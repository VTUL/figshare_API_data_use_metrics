import json
import requests
import pandas as pd
import datetime
import time

# Helper function to also write to a log file
import os

def load_figshare_token():
    """
    Load a Figshare API personal token from figshare_api_token.txt, if present.
    The file should contain only the token (whitespace is stripped). Returns
    None if the file is missing or empty, in which case requests are sent
    unauthenticated as before.
    """
    token_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'figshare_api_token.txt')
    try:
        with open(token_path, 'r', encoding='utf-8') as f:
            token = f.read().strip()
        return token if token else None
    except FileNotFoundError:
        return None

FIGSHARE_TOKEN = load_figshare_token()
FIGSHARE_HEADERS = {'Authorization': f'token {FIGSHARE_TOKEN}'} if FIGSHARE_TOKEN else {}
print(f"DEBUG: Figshare API token {'loaded (authenticated requests)' if FIGSHARE_TOKEN else 'NOT found (using anonymous requests)'}")

# Function to harvest all public items from figshare.com
#def harvest_figshare_public_items(item_type="dataset", start_date="2022-01-01", end_date="2022-12-31", max_pages=1000):
def harvest_figshare_public_items(start_date, end_date, item_type, max_pages, batch_type='week'):
    BASE_URL = 'https://api.figshare.com/v2'
    results = []
    # Split the date range into weekly/monthly batches to avoid large result sets
    start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    batch_ranges = []
    current = start_dt
    while current < end_dt:
        batch_start = current
        if batch_type == 'week':
            batch_end = min(batch_start + datetime.timedelta(days=6), end_dt)
        else:  # fallback to monthly
            next_month = (batch_start.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
            batch_end = min(next_month - datetime.timedelta(days=1), end_dt)
        batch_ranges.append((batch_start.strftime("%Y-%m-%d"), batch_end.strftime("%Y-%m-%d")))
        current = batch_end + datetime.timedelta(days=1)
    print(f"DEBUG: Batching into {len(batch_ranges)} {batch_type}ly ranges: {batch_ranges}")

    # Process batches from a work queue instead of a fixed list, so a batch
    # that turns out to have too many matches (approaching Figshare's ~10,000
    # result depth limit) can be split into smaller date ranges and re-queued,
    # instead of silently truncating.
    SPLIT_TRIGGER_PAGE = 9  # if page 9 (9000 items) is STILL a full page, split now rather than push closer to the ~10,000 cap
    work_queue = list(batch_ranges)
    while work_queue:
        batch_start, batch_end = work_queue.pop(0)
        print(f"DEBUG: Harvesting batch {batch_start} to {batch_end}")
        # NOTE: :posted_before: is EXCLUSIVE (the range is [after, before)), so to
        # include batch_end itself we query up to the day AFTER batch_end. Without
        # this, every batch silently drops its last day.
        batch_before = (datetime.datetime.strptime(batch_end, "%Y-%m-%d") + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        query = {
            "search_for": f":item_type: {item_type} AND :posted_before: {batch_before} AND :posted_after: {batch_start}"
        }
        seen_page_ids = set()
        batch_items = []
        needs_split = False
        for page in range(1, max_pages + 1):
            # page_size/page/order must be in the POST body - the API ignores
            # them in the URL query string and falls back to a small default
            # page size, which silently truncates every batch.
            url = f"{BASE_URL}/articles/search"
            body = dict(query)
            body['page_size'] = 1000
            body['page'] = page
            body['order'] = 'published_date'
            body['order_direction'] = 'asc'
            response = requests.post(url, json=body, headers=FIGSHARE_HEADERS)
            print(f"Batch {batch_start} to {batch_end}, Page {page} status: {response.status_code}")
            if response.status_code != 200:
                print(f"Error on batch {batch_start} to {batch_end}, page {page}: {response.status_code}")
                print("Request URL:", url)
                print("Request payload:", body)
                print("Response content:", response.text)
                break
            items = response.json()
            if not items:
                print(f"No more items found in batch {batch_start} to {batch_end}.")
                break
            # Guard: if this page has no ids we haven't already seen, the API is
            # repeating a page (e.g. ignoring the page param) or we have reached
            # the end without an empty page - stop instead of looping forever.
            current_ids = {it.get('id') for it in items}
            if not (current_ids - seen_page_ids):
                print(f"Batch {batch_start} to {batch_end}, Page {page}: no new items, stopping to avoid a loop.")
                break
            seen_page_ids |= current_ids
            # Only keep items where 'url_public_html' starts with 'https://figshare.com'
            filtered_items = [item for item in items if str(item.get('url_public_html', '')).startswith('https://figshare.com')]
            batch_items.extend(filtered_items)
            print(f"Batch {batch_start} to {batch_end}, Page {page}: {len(filtered_items)} figshare.com items retrieved, total so far: {len(batch_items)}")
            # Keep paging until an empty page or a repeated page (guard above).
            # Do NOT stop just because a page has < 1000 items - a short page is
            # not a reliable end-of-results signal.
            if page >= SPLIT_TRIGGER_PAGE and len(items) == 1000:
                needs_split = True
                print(f"WARNING: Batch {batch_start} to {batch_end} is still returning full pages at page {page} "
                      f"(approaching Figshare's ~10,000 result depth limit). Splitting into smaller date ranges "
                      f"instead of continuing.")
                break

        if needs_split:
            bs_dt = datetime.datetime.strptime(batch_start, "%Y-%m-%d")
            be_dt = datetime.datetime.strptime(batch_end, "%Y-%m-%d")
            if bs_dt >= be_dt:
                # Already a single day - cannot split further. Keep what we
                # got and log loudly rather than looping forever.
                msg = (f"WARNING: batch {batch_start} to {batch_end} cannot be split further (single day) "
                       f"but is approaching the results limit - this day's data may be incomplete.")
                print(msg)
                log_to_file(msg)
                results.extend(batch_items)
                continue
            mid_dt = bs_dt + (be_dt - bs_dt) // 2
            first_half = (batch_start, mid_dt.strftime("%Y-%m-%d"))
            second_half = ((mid_dt + datetime.timedelta(days=1)).strftime("%Y-%m-%d"), batch_end)
            print(f"DEBUG: Splitting {batch_start} to {batch_end} into {first_half} and {second_half}")
            # Discard the partial items collected before the split - they will
            # be fully re-collected via the smaller, safe sub-ranges instead.
            work_queue.insert(0, second_half)
            work_queue.insert(0, first_half)
        else:
            results.extend(batch_items)
    # Save results to JSON
    filename = f"figshare_public_items_{datetime.datetime.now().strftime('%Y-%m-%d')}.json"
    with open(filename, "w") as f:
        json.dump(results, f)
    print(f"Harvest complete. Total figshare.com items: {len(results)}. Saved to {filename}")
    return results
def log_to_file(*args, **kwargs):
    with open('harvest_institution_log.txt', 'a', encoding='utf-8') as f:
        print(*args, **kwargs, file=f)

# Set the base URLs
BASE_URL = 'https://api.figshare.com/v2'

# Set up lists to collect information and reports
errorList = []
newRecords = []

#def harvest_institution_items(institution_id, item_type="dataset", start_date="2022-01-01", end_date="2022-12-31"):
def harvest_institution_items(institution_id, start_date, end_date, item_type):
    """
    Harvest items for a specific institution
    """
    global newRecords, errorList
    
    print(f'DEBUG: Starting harvest_institution_items for institution_id={institution_id}')
    print(f'DEBUG: Parameters - item_type={item_type}, start_date={start_date}, end_date={end_date}')
    print(f'Harvesting items for institution ID: {institution_id}')
    log_to_file(f'Harvesting items for institution ID: {institution_id}')
    
    # Build the search query
   # query = {
   #     "institution": int(institution_id),
   #     "search_for": f":defined_type_name:{item_type} AND :posted_before:#{end_date} AND :posted_after:{start_date}"
   # }
    #query = {
    #    "institution": int(institution_id)}
    #start_date='2022-01-01'
    #end_date='2022-12-31'
    print(f'DEBUG: Built query with institution_id={institution_id}, start_date={start_date}, end_date={end_date}')
    # :posted_before: is EXCLUSIVE, so query up to the day AFTER end_date to
    # include end_date itself (otherwise the final day is silently dropped).
    end_before = (datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    query = {
        "institution": int(institution_id),
        "search_for": f":item_type: dataset AND :posted_before: {end_before} AND :posted_after: {start_date}"
        }
    
    print(f'DEBUG: Built query={query}')
    print(f'Search query: {query}')
    log_to_file(f'Search query: {query}')
   # query is {"institution":153, "page_size":1}
   # *********Search request URL: https://api.figshare.com/v2/articles/search with params: {'institution': 153, 'page_size': 1}
    page = 1
    total_items_for_institution = 0
    seen_ids_this_institution = set()
    MAX_PAGES_PER_INSTITUTION = 2000  # backstop only; largest real institution seen so far is ~700 items (~70 pages)
    while True:
        if page > MAX_PAGES_PER_INSTITUTION:
            print(f'WARNING: institution {institution_id} hit the {MAX_PAGES_PER_INSTITUTION}-page backstop; stopping. This should not happen for real data - investigate.')
            log_to_file(f'WARNING: institution {institution_id} hit the {MAX_PAGES_PER_INSTITUTION}-page backstop; stopping.')
            errorList.append({'page': page, 'error': 'hit MAX_PAGES_PER_INSTITUTION backstop', 'institution_id': institution_id})
            break
        try:
            print(f'DEBUG: Starting page {page} request')
            print(f'Requesting page {page}...')
            log_to_file(f'Requesting page {page}...')
            
            # Make the API request with proper pagination.
            # page_size/page/order must be in the POST body - the API ignores
            # them in the URL query string and falls back to a small default
            # page size, which silently truncates every institution's results.
            url = f"{BASE_URL}/articles/search"
            body = dict(query)
            body['page_size'] = 1000
            body['page'] = page
            body['order'] = 'published_date'
            body['order_direction'] = 'asc'
            print(f'DEBUG: Making POST request to {url}')
            response = requests.post(url, json=body, headers=FIGSHARE_HEADERS)  # Use json=body, not params
            print('*********Search request URL:', url, 'with json:', body)
            print('Search request status:', response.status_code)
            print(f'DEBUG: Response received, status_code={response.status_code}')
            print(f'HTTP status code: {response.status_code}')
            log_to_file(f'HTTP status code: {response.status_code}')
            
            if response.status_code != 200:
                print(f'DEBUG: Non-200 status code, adding to error list')
                error_desc = f'Error on page {page}: HTTP {response.status_code}'
                print(error_desc)
                log_to_file(error_desc)
                errorList.append({'page': page, 'status_code': response.status_code, 'institution_id': institution_id})
                break
            
            # Parse the response
            print(f'DEBUG: Parsing JSON response')
            items = response.json()
            print(f'DEBUG: JSON parsed, type={type(items)}, length={len(items) if isinstance(items, list) else "not a list"}')
            
            if not items:
                print(f'DEBUG: No items found, breaking loop')
                print(f'No more items found. Harvesting complete for institution {institution_id}.')
                log_to_file(f'No more items found. Harvesting complete for institution {institution_id}.')
                break

            # Guard: if this page has no ids we haven't already seen, the API is
            # repeating a page (e.g. ignoring the page param) - stop instead of
            # looping forever. This is the normal way this loop ends now.
            current_ids = {it.get('id') for it in items}
            if not (current_ids - seen_ids_this_institution):
                print(f'DEBUG: Page {page} had no new items (API repeated a page). Harvesting complete for institution {institution_id}.')
                log_to_file(f'Page {page} had no new items. Harvesting complete for institution {institution_id}.')
                break
            seen_ids_this_institution |= current_ids

            print(f'DEBUG: Processing {len(items)} items')
            print(f'Page {page}: {len(items)} items retrieved')
            log_to_file(f'Page {page}: {len(items)} items retrieved')
            
            # Add institution_id to each item for tracking
            items_processed = 0
            for item in items:
                item['harvested_institution_id'] = institution_id
                item['harvested_datetime'] = datetime.datetime.now().isoformat()
                item['harvest_start_date'] = start_date
                item['harvest_end_date'] = end_date
                item['harvest_item_type'] = item_type
                items_processed += 1
            
            print(f'DEBUG: Added metadata to {items_processed} items')
            print(f'DEBUG: Adding {len(items)} items to newRecords')
            newRecords.extend(items)
            total_items_for_institution += len(items)
            print(f'DEBUG: Total items for institution {institution_id} so far: {total_items_for_institution}')
            page += 1
            
        except Exception as e:
            print(f'DEBUG: Exception occurred: {type(e).__name__}: {str(e)}')
            error_desc = f'Exception on page {page}: {str(e)}'
            print(error_desc)
            log_to_file(error_desc)
            errorList.append({'page': page, 'error': str(e), 'institution_id': institution_id})
            break
    
    print(f'DEBUG: Harvest complete for institution {institution_id}')
    print(f'Institution {institution_id}: Total items harvested: {len([r for r in newRecords if r.get("harvested_institution_id") == institution_id])}')
    log_to_file(f'Institution {institution_id}: Total items harvested: {len([r for r in newRecords if r.get("harvested_institution_id") == institution_id])}')

#def harvest_multiple_institutions(institution_ids, item_type="dataset", start_date="2022-01-01", end_date="2022-12-31"):
def harvest_multiple_institutions(institution_ids, start_date, end_date, item_type):
    """
    Harvest items for multiple institutions
    """
    print(f'DEBUG: Starting harvest_multiple_institutions with {len(institution_ids)} institutions')
    print(f'DEBUG: Institution IDs: {institution_ids}')
    for i, inst_id in enumerate(institution_ids):
        print(f'DEBUG: Processing institution {i+1}/{len(institution_ids)}: {inst_id}')
        harvest_institution_items(inst_id,  start_date, end_date,item_type)
        print(f'DEBUG: Completed institution {i+1}/{len(institution_ids)}: {inst_id}')


def fetch_article_metadata(item_id, max_retries=3, retry_wait=5, request_delay=0.3):
    """
    Fetch full metadata for one article. Waits request_delay seconds before
    every attempt (to avoid triggering throttling), and on a non-200 response
    retries with backoff (honoring a Retry-After header if the server sends
    one) instead of giving up immediately. Returns the metadata dict on
    success, or None if every attempt fails.
    """
    url = f"https://api.figshare.com/v2/articles/{item_id}"
    for attempt in range(1, max_retries + 1):
        time.sleep(request_delay)
        try:
            resp = requests.get(url, timeout=30, headers=FIGSHARE_HEADERS)
        except Exception as e:
            print(f"Error fetching metadata for item {item_id} (attempt {attempt}/{max_retries}): {e}")
            time.sleep(retry_wait * attempt)
            continue
        if resp.status_code == 200:
            return resp.json()
        if attempt < max_retries:
            wait = retry_wait * attempt
            retry_after = resp.headers.get('Retry-After')
            if retry_after:
                try:
                    wait = max(wait, float(retry_after))
                except ValueError:
                    pass
            print(f"Warning: item {item_id} status {resp.status_code} (attempt {attempt}/{max_retries}), retrying in {wait:.0f}s")
            time.sleep(wait)
        else:
            print(f"Warning: Could not fetch full metadata for item {item_id}, status {resp.status_code} (gave up after {max_retries} attempts)")
    return None


# Example usage
if __name__ == "__main__":
    print('DEBUG: Starting main execution')
    # Fix the random seed once, up front, so the random control-group sample
    # below is reproducible. NOTE: this only reproduces the SELECTION; to let
    # someone reproduce the exact sample you must also archive the harvested
    # pool file (figshare_public_items_*.json), since the live API changes.
    import random
    random.seed(42)
    # Read institution IDs from Excel file (adjust sheet and column names as needed)
    try:
        #excel_file = 'institutionListOAI_20250730.xlsx'
        excel_file = 'institutionListOAI.xlsx'
        print(f'DEBUG: Reading Excel file: {excel_file}')
        inst_df = pd.read_excel(excel_file, sheet_name=2)
        df0 = pd.read_excel(excel_file, sheet_name=0)
        print(f'DEBUG: Excel file read successfully, shape: {inst_df.shape}')
        print(f'DEBUG: Column names: {inst_df.columns.tolist()}')
        
        # Debug: Print first few rows
        print('DEBUG: First 5 rows of data:')
        print(inst_df.head())
        
        #institution_ids = inst_df['institution_id'].dropna().astype(int).astype(str).tolist()[:5]  # Test with first 5
        #institution_ids = inst_df['institution_id'].dropna().astype(int).astype(str).tolist()[:1]  # Test with first 5
        #institution_ids = inst_df['institution_id'].dropna().astype(int).astype(str).tolist()[:1]  # Test with first 5
        institution_ids = inst_df['institution_id'].dropna().astype(int).astype(str).tolist()[:3]  # SMALL TEST: first 3 institutions only
        print(f'DEBUG: Extracted institution IDs: {institution_ids}')
        print(f"Extracted institution IDs: {institution_ids}")
        print(f"Number of institution IDs: {len(institution_ids)}")

        print(f"DEBUG: Starting harvest for {len(institution_ids)} institutions...")
        print(f"Starting harvest for {len(institution_ids)} institutions...")
        log_to_file(f"Starting harvest for {len(institution_ids)} institutions...")
        
        # Harvest items for institutions
        print('DEBUG: Calling harvest_multiple_institutions')
        start_date = "2022-06-04"   # SMALL TEST: 2-week window incl. the high-volume June 4-10 week (full run uses 2022-01-01)
        end_date = "2022-06-17"     # SMALL TEST: (full run uses 2022-12-31)
        item_type = "dataset"
        harvest_multiple_institutions(institution_ids, start_date, end_date, item_type)
        print('DEBUG: harvest_multiple_institutions completed')
        print(f'DEBUG: Final counts - newRecords: {len(newRecords)}, errorList: {len(errorList)}')
        print(f'Harvesting complete. Total items collected: {len(newRecords)}')
        print(f'There were {len(errorList)} errors.')
        log_to_file(f'Harvesting complete. Total items collected: {len(newRecords)}')
        log_to_file(f'There were {len(errorList)} errors.')
        # Merge in columns from sheet 0 to newRecords before saving
        key_col = 'institution_id' if 'institution_id' in df0.columns else 'instution_id'
        # Build a mapping from institution_id to all columns in df0 (except the key)
        df0_map = df0.set_index(key_col).to_dict(orient='index')
        for rec in newRecords:
            inst_id = int(rec['harvested_institution_id'])
            if inst_id in df0_map:
                for k, v in df0_map[inst_id].items():
                    if k not in rec:
                        rec[k] = v
        # Harvest figshare.com public items and append to results
        print('DEBUG: Harvesting figshare.com public items')
        #figshare_items = harvest_figshare_public_items()
        #figshare_items = harvest_figshare_public_items(start_date=start_date, end_date=end_date)
        max_pages = 1000  # Adjust as needed
        print(f'DEBUG: Calling harvest_figshare_public_items with start_date={start_date}, end_date={end_date}, item_type={item_type}, max_pages={max_pages}')
        figshare_items = harvest_figshare_public_items(start_date, end_date,item_type,max_pages, batch_type='week')

        print(f'DEBUG: Appending {len(figshare_items)} figshare.com items to harvested items')

        # Randomly select as many figshare.com items as institution items
        n_institution = len(newRecords)
        print(f"DEBUG: Number of institution items: {n_institution}")
        figshare_sample = []
        if len(figshare_items) >= n_institution:
            import random
            figshare_sample = random.sample(figshare_items, n_institution)
        else:
            figshare_sample = figshare_items.copy()
        print(f"DEBUG: Randomly selected {len(figshare_sample)} figshare.com items for full metadata fetch")

        # Fetch full metadata for institution items
        print('DEBUG: Fetching full metadata for institution items')
        enriched_institution_items = []
        for idx, item in enumerate(newRecords):
        #for idx, item in enumerate(newRecords[:5]): #for testing 1
            item_id = item.get('id')
            if item_id:
                full_meta = fetch_article_metadata(item_id)
                if full_meta:
                    item.update(full_meta)
            enriched_institution_items.append(item)
            if (idx+1) % 100 == 0:
                print(f"Fetched metadata for {idx+1} institution items...")

        # Fetch full metadata for the sampled figshare.com items
        print('DEBUG: Fetching full metadata for sampled figshare.com items')
        enriched_figshare_sample = []
        for idx, item in enumerate(figshare_sample):
        #for idx, item in enumerate(figshare_sample[:5]):
            item_id = item.get('id')
            if item_id:
                full_meta = fetch_article_metadata(item_id)
                if full_meta:
                    item.update(full_meta)
            enriched_figshare_sample.append(item)
            if (idx+1) % 100 == 0:
                print(f"Fetched metadata for {idx+1} figshare.com items...")

        # Combine enriched institution items and enriched sampled figshare.com items
        final_items = enriched_institution_items + enriched_figshare_sample

        # Remove duplicate items by 'id' (the API can return the same item more
        # than once), keeping the first occurrence of each id.
        seen_ids = set()
        deduped_items = []
        for item in final_items:
            item_id = item.get('id')
            if item_id not in seen_ids:
                seen_ids.add(item_id)
                deduped_items.append(item)
        if len(deduped_items) < len(final_items):
            print(f'DEBUG: Removed {len(final_items) - len(deduped_items)} duplicate items by id')
        final_items = deduped_items

        # REMOVE 'files' key from all items to avoid CSV line break issues
        for item in final_items:
            if 'files' in item:
                del item['files']
    
        # REMOVE 'custom_fields' key from all items to avoid CSV line break issues
        for item in final_items:
            if 'custom_fields' in item:
                del item['custom_fields']
                
        # Save all enriched items to JSON and CSV
        today = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        print(f'DEBUG: Saving files with date-time suffix: {today}')
        json_file = f'harvested_items_{today}_fullmeta.json'
        print(f'DEBUG: Saving JSON file: {json_file}')
        with open(json_file, 'w') as f:
            json.dump(final_items, f, indent=2)
        csv_file = f'harvested_items_{today}_fullmeta.csv'
        print(f'DEBUG: Saving CSV file: {csv_file}')
        df_items = pd.DataFrame(final_items)
        df_items.to_csv(csv_file, index=False)
        print(f'DEBUG: CSV file saved, shape: {df_items.shape}')
        print('DEBUG: All operations completed successfully')
        print('All data saved to files.')
        log_to_file('All data saved to files.')
        
    except Exception as e:
        print(f'DEBUG: Exception in main: {type(e).__name__}: {str(e)}')
        print(f'Error reading institution file: {e}')
        log_to_file(f'Error reading institution file: {e}')
        
        # Example with single institution ID for testing
        #test_institution_id = "123"  # Replace with actual institution ID
        #print(f'DEBUG: Running test with institution ID: {test_institution_id}')
        #harvest_institution_items(test_institution_id)
        #print(f'Test harvest complete. Items collected: {len(newRecords)}')
        #print(f'DEBUG: Running test with institution ID: {test_institution_id}')
        #harvest_institution_items(test_institution_id)
        #print(f'Test harvest complete. Items collected: {len(newRecords)}')
        #print(f'DEBUG: Running test with institution ID: {test_institution_id}')
        #harvest_institution_items(test_institution_id)
        #print(f'Test harvest complete. Items collected: {len(newRecords)}')
