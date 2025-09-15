import json
import requests
import pandas as pd
import datetime

# Helper function to also write to a log file
import os
# Function to harvest all public items from figshare.com
#def harvest_figshare_public_items(item_type="dataset", start_date="2022-01-01", end_date="2022-12-31", max_pages=1000):
def harvest_figshare_public_items(start_date, end_date, item_type, max_pages):
    BASE_URL = 'https://api.figshare.com/v2'
    results = []
    # Split the date range into monthly batches
    start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    batch_ranges = []
    current = start_dt
    while current < end_dt:
        batch_start = current
        # Get last day of month
        next_month = (batch_start.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
        batch_end = min(next_month - datetime.timedelta(days=1), end_dt)
        batch_ranges.append((batch_start.strftime("%Y-%m-%d"), batch_end.strftime("%Y-%m-%d")))
        current = batch_end + datetime.timedelta(days=1)
    print(f"DEBUG: Batching into {len(batch_ranges)} monthly ranges: {batch_ranges}")
    for batch_start, batch_end in batch_ranges:
        print(f"DEBUG: Harvesting batch {batch_start} to {batch_end}")
        query = {
            "search_for": f":item_type: {item_type} AND :posted_before: {batch_end} AND :posted_after: {batch_start}"
        }
        for page in range(1, max_pages + 1):
            url = f"{BASE_URL}/articles/search?page_size=1000&page={page}"
            response = requests.post(url, json=query)
            print(f"Batch {batch_start} to {batch_end}, Page {page} status: {response.status_code}")
            if response.status_code != 200:
                print(f"Error on batch {batch_start} to {batch_end}, page {page}: {response.status_code}")
                print("Request URL:", url)
                print("Request payload:", query)
                print("Response content:", response.text)
                break
            items = response.json()
            if not items:
                print(f"No more items found in batch {batch_start} to {batch_end}.")
                break
            # Only keep items where 'url_public_html' starts with 'https://figshare.com'
            filtered_items = [item for item in items if str(item.get('url_public_html', '')).startswith('https://figshare.com')]
            results.extend(filtered_items)
            print(f"Batch {batch_start} to {batch_end}, Page {page}: {len(filtered_items)} figshare.com items retrieved, total so far: {len(results)}")
            if len(items) < 1000:
                break
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
    query = {
        "institution": int(institution_id),
        "search_for": f":item_type: dataset AND :posted_before: {end_date} AND :posted_after: {start_date}"
        }
    
    print(f'DEBUG: Built query={query}')
    print(f'Search query: {query}')
    log_to_file(f'Search query: {query}')
   # query is {"institution":153, "page_size":1}
   # *********Search request URL: https://api.figshare.com/v2/articles/search with params: {'institution': 153, 'page_size': 1}
    page = 1
    total_items_for_institution = 0
    while True:
        try:
            print(f'DEBUG: Starting page {page} request')
            print(f'Requesting page {page}...')
            log_to_file(f'Requesting page {page}...')
            
            # Make the API request with proper pagination
            url = f"{BASE_URL}/articles/search?page_size=1000&page={page}"
            print(f'DEBUG: Making POST request to {url}')
            response = requests.post(url, json=query)  # Use json=query, not params
            print('*********Search request URL:', url, 'with json:', query)
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


# Example usage
if __name__ == "__main__":
    print('DEBUG: Starting main execution')
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
        institution_ids = inst_df['institution_id'].dropna().astype(int).astype(str).tolist()  # All institutions
        print(f'DEBUG: Extracted institution IDs: {institution_ids}')
        print(f"Extracted institution IDs: {institution_ids}")
        print(f"Number of institution IDs: {len(institution_ids)}")

        print(f"DEBUG: Starting harvest for {len(institution_ids)} institutions...")
        print(f"Starting harvest for {len(institution_ids)} institutions...")
        log_to_file(f"Starting harvest for {len(institution_ids)} institutions...")
        
        # Harvest items for institutions
        print('DEBUG: Calling harvest_multiple_institutions')
        start_date = "2022-01-01"
        end_date = "2022-12-31"
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
        figshare_items = harvest_figshare_public_items(start_date, end_date,item_type,max_pages)
        
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
                try:
                    url = f"https://api.figshare.com/v2/articles/{item_id}"
                    resp = requests.get(url)
                    if resp.status_code == 200:
                        full_meta = resp.json()
                        item.update(full_meta)
                    else:
                        print(f"Warning: Could not fetch full metadata for item {item_id}, status {resp.status_code}")
                except Exception as e:
                    print(f"Error fetching metadata for item {item_id}: {e}")
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
                try:
                    url = f"https://api.figshare.com/v2/articles/{item_id}"
                    resp = requests.get(url)
                    if resp.status_code == 200:
                        full_meta = resp.json()
                        item.update(full_meta)
                    else:
                        print(f"Warning: Could not fetch full metadata for figshare item {item_id}, status {resp.status_code}")
                except Exception as e:
                    print(f"Error fetching metadata for figshare item {item_id}: {e}")
            enriched_figshare_sample.append(item)
            if (idx+1) % 100 == 0:
                print(f"Fetched metadata for {idx+1} figshare.com items...")

        # Combine enriched institution items and enriched sampled figshare.com items
        final_items = enriched_institution_items + enriched_figshare_sample

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
