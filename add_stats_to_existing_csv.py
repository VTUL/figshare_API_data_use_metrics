#!/usr/bin/env python3
"""
Script to add statistics (views, downloads, stats URLs) to an existing harvested items CSV file.
This script imports and uses the gather_statistics_for_items function from harvest_institution_items.py
"""

import requests
import json
import os
import re

import pandas as pd
import datetime

# Global variable to hold the log filename for this run
LOG_FILENAME = None

def set_log_filename():
    """Set a unique log filename for this run, with date and time stamp."""
    global LOG_FILENAME
    from datetime import datetime
    log_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    LOG_FILENAME = f'add_stats_log_{log_time}.txt'

def log_to_file(*args, **kwargs):
    """Write to the log file for this run, with a date and time prefix on each line."""
    from datetime import datetime
    if LOG_FILENAME is None:
        set_log_filename()
    with open(LOG_FILENAME, 'a', encoding='utf-8') as f:
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
        print(timestamp, *args, **kwargs, file=f)
        
def get_preferred_stats_url_pattern(institution_id, views_url_1, views_url_2, item=None):
    """
    Return 'url1', 'url2', 'url3', or 'url4' if the corresponding views URL returns status 200, else None.
    url3 is based on the institution 'name' field (lowercase, removes 'university of ', spaces, and non-alphanum).
    url4 is based on the first word after the slash in the DOI.
    """
    try:
        resp1 = requests.get(views_url_1)
        print(f"DEBUG: Trying views_url_1: {views_url_1}, status_code: {resp1.status_code}, text: {resp1.text}")
        if resp1.status_code == 200:
            return 'url1'
        if views_url_2:
            resp2 = requests.get(views_url_2)
            print(f"DEBUG: Trying views_url_2: {views_url_2}, status_code: {resp2.status_code}, text: {resp2.text}")
            if resp2.status_code == 200:
                return 'url2'
        # Try url3 using institution name if available
        if item and 'name' in item and item['name']:
            name = item['name'].lower().strip()
            print(f"DEBUG: Institution name for url3: {name}")
            print(f"DEBUG: Original institution name: {item['name']}")
            # Remove all common leading patterns
            for prefix in [
                "the university of the ",
                "university of the ",
                "the university of ",
                "university of ",
                "the university ",
                "university ",
                "the "
            ]:
                if name.startswith(prefix):
                    name = name[len(prefix):]
                    print(f"DEBUG: Stripped prefix '{prefix}', new name: {name}")
                    break
            name_url = re.sub(r'[^a-z0-9]', '', name)
            print(f"DEBUG: Transformed institution name for url3: {name_url}")
            views_url_3 = f"https://stats.figshare.com/{name_url}/total/views/article/{item.get('id')}"
            print(f"DEBUG: Trying views_url_3: {views_url_3}")
            resp3 = requests.get(views_url_3)
            print(f"DEBUG: views_url_3 status_code: {resp3.status_code}, text: {resp3.text}")
            if resp3.status_code == 200:
                return ('url3', views_url_3)
        # Try url4 using first word after slash in DOI
        if item and 'doi' in item and item['doi']:
            doi = str(item['doi'])
            print(f"DEBUG: Checking DOI for url4: {doi}")
            if '/' in doi:
                suffix = doi.split('/', 1)[1]
                name_url = suffix.split('.', 1)[0]
                print(f"DEBUG: Extracted name_url from DOI for url4: {name_url}")
                views_url_4 = f"https://stats.figshare.com/{name_url}/total/views/article/{item.get('id')}"
                print(f"DEBUG: Trying views_url_4: {views_url_4}")
                resp4 = requests.get(views_url_4)
                print(f"DEBUG: views_url_4 status_code: {resp4.status_code}, text: {resp4.text}")
                if resp4.status_code == 200:
                    return ('url4', views_url_4)
    except Exception as e:
        print(f"DEBUG: Error checking preferred stats URL for institution {institution_id}: {e}")
    return None

def gather_statistics_for_items(items_list, institution_abbrevs=None):
    """
    Gather statistics for harvested items using the logic from oaimphFig.py
    """
    print(f'DEBUG: Starting gather_statistics_for_items with {len(items_list)} items')
    log_to_file(f'DEBUG: Starting gather_statistics_for_items with {len(items_list)} items')
    print('Gathering statistics for harvested items...')
    log_to_file('Gathering statistics for harvested items...')
    print(f'DEBUG: items_list: {items_list}')
    log_to_file(f'DEBUG: items_list: {items_list}')

    all_stats = []
    preferred_stats_url_pattern = {}

    for i, item in enumerate(items_list):
        print(f'DEBUG: Processing item {i+1}/{len(items_list)}')
        log_to_file(f'DEBUG: Processing item {i+1}/{len(items_list)}')
        print(f'DEBUG: Item dict: {item}')
        log_to_file(f'DEBUG: Item dict: {item}')
        item_id = item.get('id')
        institution_id = item.get('harvested_institution_id')
        url_public_html = item.get('url_public_html', '')
        print(f'DEBUG: item_id={item_id}, institution_id={institution_id}, url_public_html={url_public_html}')
        log_to_file(f'DEBUG: item_id={item_id}, institution_id={institution_id}, url_public_html={url_public_html}')
        # If institution_id is None, treat as figshare.com item
        if institution_id is None or str(institution_id).lower() == 'none' or (
            url_public_html and url_public_html.startswith("https://figshare.com/")
        ):
            print(f'DEBUG: Treating as figshare.com item')
            log_to_file(f'DEBUG: Treating as figshare.com item')
            views_url = f"https://stats.figshare.com/total/views/article/{item_id}"
            downloads_url = f"https://stats.figshare.com/total/downloads/article/{item_id}"
            print(f'DEBUG: views_url={views_url}, downloads_url={downloads_url}')
            log_to_file(f'DEBUG: views_url={views_url}, downloads_url={downloads_url}')
            try:
                views_resp = requests.get(views_url)
                print(f'DEBUG: views_resp.status_code={views_resp.status_code}')
                log_to_file(f'DEBUG: views_resp.status_code={views_resp.status_code}')
                downloads_resp = requests.get(downloads_url)
                print(f'DEBUG: downloads_resp.status_code={downloads_resp.status_code}')
                log_to_file(f'DEBUG: downloads_resp.status_code={downloads_resp.status_code}')
                views = views_resp.json().get("totals") if views_resp.status_code == 200 else 'None'
                downloads = downloads_resp.json().get("totals") if downloads_resp.status_code == 200 else 'None'
                print(f'DEBUG: views={views}, downloads={downloads}')
                log_to_file(f'DEBUG: views={views}, downloads={downloads}')
            except Exception as e:
                print(f"Error fetching stats for figshare item {item_id}: {e}")
                log_to_file(f"Error fetching stats for figshare item {item_id}: {e}")
                views = 'None'
                downloads = 'None'
            stats = {
                'item_id': item_id,
                'institution_id': institution_id,
                'views_url_used': views_url,
                'views_status_code': views_resp.status_code if 'views_resp' in locals() else None,
                'views': views,
                'downloads_url_used': downloads_url,
                'downloads_status_code': downloads_resp.status_code if 'downloads_resp' in locals() else None,
                'downloads': downloads
            }
            for k, v in item.items():
                if k not in stats:
                    stats[k] = v
            print(f'DEBUG: stats dict for figshare.com item: {stats}')
            log_to_file(f'DEBUG: stats dict for figshare.com item: {stats}')
            all_stats.append(stats)
            continue

        # If institution_id is 935, treat as Virginia Tech item
        if institution_id == 935:
            print(f'DEBUG: Treating as Virginia Tech (id=935) item')
            log_to_file(f'DEBUG: Treating as Virginia Tech (id=935) item')
            views_url = f"https://stats.figshare.com/virginiatech/total/views/article/{item_id}"
            downloads_url = f"https://stats.figshare.com/virginiatech/total/downloads/article/{item_id}"
            print(f'DEBUG: views_url={views_url}, downloads_url={downloads_url}')
            log_to_file(f'DEBUG: views_url={views_url}, downloads_url={downloads_url}')
            try:
                views_resp = requests.get(views_url)
                print(f'DEBUG: views_resp.status_code={views_resp.status_code}')
                log_to_file(f'DEBUG: views_resp.status_code={views_resp.status_code}')
                downloads_resp = requests.get(downloads_url)
                print(f'DEBUG: downloads_resp.status_code={downloads_resp.status_code}')
                log_to_file(f'DEBUG: downloads_resp.status_code={downloads_resp.status_code}')
                views = views_resp.json().get("totals") if views_resp.status_code == 200 else 'None'
                downloads = downloads_resp.json().get("totals") if downloads_resp.status_code == 200 else 'None'
                print(f'DEBUG: views={views}, downloads={downloads}')
                log_to_file(f'DEBUG: views={views}, downloads={downloads}')
            except Exception as e:
                print(f"Error fetching stats for Virginia Tech item {item_id}: {e}")
                log_to_file(f"Error fetching stats for Virginia Tech item {item_id}: {e}")
                views = 'None'
                downloads = 'None'
            stats = {
                'item_id': item_id,
                'institution_id': institution_id,
                'views_url_used': views_url,
                'views_status_code': views_resp.status_code if 'views_resp' in locals() else None,
                'views': views,
                'downloads_url_used': downloads_url,
                'downloads_status_code': downloads_resp.status_code if 'downloads_resp' in locals() else None,
                'downloads': downloads
            }
            for k, v in item.items():
                if k not in stats:
                    stats[k] = v
            print(f'DEBUG: stats dict for Virginia Tech item: {stats}')
            log_to_file(f'DEBUG: stats dict for Virginia Tech item: {stats}')
            all_stats.append(stats)
            continue

        # If institution_id is 791, treat as J-STAGE item
        if institution_id == 791:
            print(f'DEBUG: Treating as J-STAGE (id=791) item')
            log_to_file(f'DEBUG: Treating as J-STAGE (id=791) item')
            views_url = f"https://stats.figshare.com/jstage/total/views/article/{item_id}"
            downloads_url = f"https://stats.figshare.com/jstage/total/downloads/article/{item_id}"
            print(f'DEBUG: views_url={views_url}, downloads_url={downloads_url}')
            log_to_file(f'DEBUG: views_url={views_url}, downloads_url={downloads_url}')
            try:
                views_resp = requests.get(views_url)
                print(f'DEBUG: views_resp.status_code={views_resp.status_code}')
                log_to_file(f'DEBUG: views_resp.status_code={views_resp.status_code}')
                downloads_resp = requests.get(downloads_url)
                print(f'DEBUG: downloads_resp.status_code={downloads_resp.status_code}')
                log_to_file(f'DEBUG: downloads_resp.status_code={downloads_resp.status_code}')
                views = views_resp.json().get("totals") if views_resp.status_code == 200 else 'None'
                downloads = downloads_resp.json().get("totals") if downloads_resp.status_code == 200 else 'None'
                print(f'DEBUG: views={views}, downloads={downloads}')
                log_to_file(f'DEBUG: views={views}, downloads={downloads}')
            except Exception as e:
                print(f"Error fetching stats for J-STAGE item {item_id}: {e}")
                log_to_file(f"Error fetching stats for J-STAGE item {item_id}: {e}")
                views = 'None'
                downloads = 'None'
            stats = {
                'item_id': item_id,
                'institution_id': institution_id,
                'views_url_used': views_url,
                'views_status_code': views_resp.status_code if 'views_resp' in locals() else None,
                'views': views,
                'downloads_url_used': downloads_url,
                'downloads_status_code': downloads_resp.status_code if 'downloads_resp' in locals() else None,
                'downloads': downloads
            }
            for k, v in item.items():
                if k not in stats:
                    stats[k] = v
            print(f'DEBUG: stats dict for J-STAGE item: {stats}')
            log_to_file(f'DEBUG: stats dict for J-STAGE item: {stats}')
            all_stats.append(stats)
            continue

        # If institution_id is 963, treat as Ryerson item
        if institution_id == 963:
            print(f'DEBUG: Treating as Ryerson (id=963) item')
            log_to_file(f'DEBUG: Treating as Ryerson (id=963) item')
            views_url = f"https://stats.figshare.com/ryerson/total/views/article/{item_id}"
            downloads_url = f"https://stats.figshare.com/ryerson/total/downloads/article/{item_id}"
            print(f'DEBUG: views_url={views_url}, downloads_url={downloads_url}')
            log_to_file(f'DEBUG: views_url={views_url}, downloads_url={downloads_url}')
            try:
                views_resp = requests.get(views_url)
                print(f'DEBUG: views_resp.status_code={views_resp.status_code}')
                log_to_file(f'DEBUG: views_resp.status_code={views_resp.status_code}')
                downloads_resp = requests.get(downloads_url)
                print(f'DEBUG: downloads_resp.status_code={downloads_resp.status_code}')
                log_to_file(f'DEBUG: downloads_resp.status_code={downloads_resp.status_code}')
                views = views_resp.json().get("totals") if views_resp.status_code == 200 else 'None'
                downloads = downloads_resp.json().get("totals") if downloads_resp.status_code == 200 else 'None'
                print(f'DEBUG: views={views}, downloads={downloads}')
                log_to_file(f'DEBUG: views={views}, downloads={downloads}')
            except Exception as e:
                print(f"Error fetching stats for Ryerson item {item_id}: {e}")
                log_to_file(f"Error fetching stats for Ryerson item {item_id}: {e}")
                views = 'None'
                downloads = 'None'
            stats = {
                'item_id': item_id,
                'institution_id': institution_id,
                'views_url_used': views_url,
                'views_status_code': views_resp.status_code if 'views_resp' in locals() else None,
                'views': views,
                'downloads_url_used': downloads_url,
                'downloads_status_code': downloads_resp.status_code if 'downloads_resp' in locals() else None,
                'downloads': downloads
            }
            for k, v in item.items():
                if k not in stats:
                    stats[k] = v
            print(f'DEBUG: stats dict for Ryerson item: {stats}')
            log_to_file(f'DEBUG: stats dict for Ryerson item: {stats}')
            all_stats.append(stats)
            continue


        print(f'DEBUG: Item {item_id}, Institution {institution_id}, URL: {url_public_html}')
        log_to_file(f'DEBUG: Item {item_id}, Institution {institution_id}, URL: {url_public_html}')
        stats_url = ''
        stats_status_code = None
        stats = {}
        views = None
        downloads = None
        downloads_url = ''
        downloads_status_code = None

        if url_public_html:
            print(f'DEBUG: URL exists, parsing parts')
            log_to_file(f'DEBUG: URL exists, parsing parts')
            url_parts = url_public_html.split('//')[1].split('.')
            print(f'DEBUG: URL parts: {url_parts}')
            log_to_file(f'DEBUG: URL parts: {url_parts}')
            views_url_1 = f"https://stats.figshare.com/{url_parts[0]}/total/views/article/{item_id}"
            views_url_2 = f"https://stats.figshare.com/{url_parts[1]}/total/views/article/{item_id}" if len(url_parts) > 1 else None
            downloads_url_1 = f"https://stats.figshare.com/{url_parts[0]}/total/downloads/article/{item_id}"
            downloads_url_2 = f"https://stats.figshare.com/{url_parts[1]}/total/downloads/article/{item_id}" if len(url_parts) > 1 else None
            print(f'DEBUG: views_url_1={views_url_1}, views_url_2={views_url_2}')
            print(f'DEBUG: downloads_url_1={downloads_url_1}, downloads_url_2={downloads_url_2}')
            log_to_file(f'DEBUG: views_url_1={views_url_1}, views_url_2={views_url_2}')
            log_to_file(f'DEBUG: downloads_url_1={downloads_url_1}, downloads_url_2={downloads_url_2}')
            pattern = preferred_stats_url_pattern.get(institution_id)
            print(f'DEBUG: preferred pattern before check: {pattern}')
            log_to_file(f'DEBUG: preferred pattern before check: {pattern}')
            if pattern is None:
                pattern = get_preferred_stats_url_pattern(institution_id, views_url_1, views_url_2, item)
                print(f'DEBUG: pattern after get_preferred_stats_url_pattern: {pattern}')
                log_to_file(f'DEBUG: pattern after get_preferred_stats_url_pattern: {pattern}')
                if pattern:
                    preferred_stats_url_pattern[institution_id] = pattern
            print(f"DEBUG: pattern for institution_id {institution_id}: {pattern}")
            print(f"DEBUG: preferred_stats_url_pattern dict: {preferred_stats_url_pattern}")
            log_to_file(f"DEBUG: pattern for institution_id {institution_id}: {pattern}")
            log_to_file(f"DEBUG: preferred_stats_url_pattern dict: {preferred_stats_url_pattern}")
            if pattern == 'url1':
                print(f'DEBUG: Using preferred views_url_1 for institution {institution_id}: {views_url_1}')
                log_to_file(f'DEBUG: Using preferred views_url_1 for institution {institution_id}: {views_url_1}')
                views_resp_1 = requests.get(views_url_1)
                print(f'DEBUG: views_resp_1.status_code={views_resp_1.status_code}')
                log_to_file(f'DEBUG: views_resp_1.status_code={views_resp_1.status_code}')
                downloads_resp_1 = requests.get(downloads_url_1)
                print(f'DEBUG: downloads_resp_1.status_code={downloads_resp_1.status_code}')
                log_to_file(f'DEBUG: downloads_resp_1.status_code={downloads_resp_1.status_code}')
                views_url = views_url_1
                downloads_url = downloads_url_1
                views_status_code = views_resp_1.status_code        
                if views_resp_1.status_code == 200:
                    stats_views = views_resp_1.json()
                    print(f'DEBUG: stats_views={stats_views}')
                    log_to_file(f'DEBUG: stats_views={stats_views}')
                    views = stats_views.get("totals")
                    stats_downloads = downloads_resp_1.json()
                    print(f'DEBUG: stats_downloads={stats_downloads}')
                    log_to_file(f'DEBUG: stats_downloads={stats_downloads}')
                    downloads = stats_downloads.get("totals")
                    print(f'DEBUG: Views response status: {views_status_code}')
                    print('downloads are ',downloads)
                    print('views are ',views)
                    log_to_file(f'DEBUG: Views response status: {views_status_code}')
                    log_to_file(f'downloads are {downloads}')
                    log_to_file(f'views are {views}')
                    downloads_status_code = downloads_resp_1.status_code
                else:
                    print(f"DEBUG: Downloads API response (not 200): {downloads_resp_1.text}")
                    log_to_file(f"DEBUG: Downloads API response (not 200): {downloads_resp_1.text}")
            elif pattern == 'url2' and views_url_2:
                print(f'DEBUG: Using preferred views_url_2 for institution {institution_id}: {views_url_2}')
                log_to_file(f'DEBUG: Using preferred views_url_2 for institution {institution_id}: {views_url_2}')
                views_resp_2 = requests.get(views_url_2)
                print(f'DEBUG: views_resp_2.status_code={views_resp_2.status_code}')
                log_to_file(f'DEBUG: views_resp_2.status_code={views_resp_2.status_code}')
                views_url = views_url_2
                views_status_code = views_resp_2.status_code
                if views_resp_2.status_code == 200:
                    stats = views_resp_2.json()
                    print(f'DEBUG: stats from views_resp_2={stats}')
                    log_to_file(f'DEBUG: stats from views_resp_2={stats}')
                    views = stats.get("totals")
                    print('views are ',views)
                    log_to_file(f'views are {views}')
                    downloads_url = downloads_url_2
                    downloads_resp = requests.get(downloads_url)
                    print(f'DEBUG: downloads_resp.status_code={downloads_resp.status_code}')
                    log_to_file(f'DEBUG: downloads_resp.status_code={downloads_resp.status_code}')
                    downloads_status_code = downloads_resp.status_code
                    if downloads_resp.status_code == 200:
                        downloads = downloads_resp.json().get("totals")
                        print('downloads are ',downloads)
                        log_to_file(f'downloads are {downloads}')
                    else:
                        print(f"DEBUG: Downloads API response (not 200): {downloads_resp.text}")
                        log_to_file(f"DEBUG: Downloads API response (not 200): {downloads_resp.text}")
            elif isinstance(pattern, tuple) and (pattern[0] == 'url3' or pattern[0] == 'url4'):
                views_url = pattern[1]
                downloads_url = views_url.replace('/views/', '/downloads/')
                print(f'DEBUG: Using preferred views_url_3 for institution {institution_id}: {views_url}')
                log_to_file(f'DEBUG: Using preferred views_url_3 for institution {institution_id}: {views_url}')
                views_resp_3 = requests.get(views_url)
                print(f'DEBUG: views_resp_3.status_code={views_resp_3.status_code}')
                log_to_file(f'DEBUG: views_resp_3.status_code={views_resp_3.status_code}')
                downloads_resp_3 = requests.get(downloads_url)
                print(f'DEBUG: downloads_resp_3.status_code={downloads_resp_3.status_code}')
                log_to_file(f'DEBUG: downloads_resp_3.status_code={downloads_resp_3.status_code}')
                views_status_code = views_resp_3.status_code
                downloads_status_code = downloads_resp_3.status_code
                views = views_resp_3.json().get("totals") if views_resp_3.status_code == 200 else 'None'
                downloads = downloads_resp_3.json().get("totals") if downloads_resp_3.status_code == 200 else 'None'
                print(f'DEBUG: views={views}, downloads={downloads}')
                log_to_file(f'DEBUG: views={views}, downloads={downloads}')
            else:
                print(f'DEBUG: No preferred pattern, using fallback')
                log_to_file(f'DEBUG: No preferred pattern, using fallback')
                views = 0
                downloads = 0
                # Print out the metadata for debugging
                print(f"DEBUG: Fallback metadata for item {item_id}: {json.dumps(item, indent=2)}")
                log_to_file(f"DEBUG: Fallback metadata for item {item_id}: {json.dumps(item, indent=2)}")
        else:
            print(f'DEBUG: No URL, using fallback')
            log_to_file(f'DEBUG: No URL, using fallback')
            views = 0
            downloads = 0
        stats['item_id'] = item_id
        stats['institution_id'] = institution_id
        stats['views_url_used'] = views_url
        stats['views_status_code'] = views_status_code
        stats['views'] = views
        stats['downloads'] = downloads
        stats['downloads_url_used'] = downloads_url
        stats['downloads_status_code'] = downloads_status_code

        # Add all columns from sheet 2 (if available in item) to stats row
        for k, v in item.items():
            if k not in stats:
                stats[k] = v
        print(f"DEBUG: Full stats dict for item {item_id}: {json.dumps(stats, indent=2)}")
        log_to_file(f"DEBUG: Full stats dict for item {item_id}: {json.dumps(stats, indent=2)}")
        all_stats.append(stats)
        print(f"DEBUG: Completed processing item {item_id} for institution {institution_id}")
        print(f"Processed item {item_id} for institution {institution_id}")
        log_to_file(f"DEBUG: Completed processing item {item_id} for institution {institution_id}")
        log_to_file(f"Processed item {item_id} for institution {institution_id}")
    print(f'DEBUG: Completed gathering statistics for {len(all_stats)} items')
    log_to_file(f'DEBUG: Completed gathering statistics for {len(all_stats)} items')
    print(f'DEBUG: all_stats: {all_stats}')
    log_to_file(f'DEBUG: all_stats: {all_stats}')
    return all_stats


def add_statistics_to_csv(csv_file_path, output_file_path=None):
    """
    Read an existing CSV file with harvested items and add statistics columns
    """
    print(f'========== DEBUG: Starting add_statistics_to_csv for file: {csv_file_path} =========')
    
    # Read the existing CSV file
    print(f'========== DEBUG: Reading existing CSV file: {csv_file_path} =========')
    log_to_file(f'Reading existing CSV file: {csv_file_path}')
    
    try:
        df = pd.read_csv(csv_file_path)
        #Debug: Uncomment the following lines to filter for a specific institution or limit rows during testing
        ############################################################
        # Filter for only institution id 8 (University of Melbourne)
        #df = df[df['harvested_institution_id'] == 935]
        #print(f'========== DEBUG: Filtered for institution_id=8, shape: {df.shape} =========')
        #df = df.head(1)  # Only process the first 30 rows
        ############################################################
        #df = df.fillna(0)  # Fill all NaN/empty values with 0
        print(f'========== DEBUG: CSV loaded, shape: {df.shape} =========')
        print(f'========== DEBUG: Loaded {len(df)} items from CSV =========')
        log_to_file(f'Loaded {len(df)} items from CSV')
        print(f'========== DEBUG: Original columns: {list(df.columns)} =========')
        
    except Exception as e:
        print(f'ERROR: Failed to read CSV file: {e}')
        log_to_file(f'ERROR: Failed to read CSV file: {e}')
        return None

    print(f'========== DEBUG: CSV loaded, shape: {df.shape} =========')
    print(f'========== DEBUG: Loaded {len(df)} items from CSV =========')
    log_to_file(f'Loaded {len(df)} items from CSV')
    # Display column names for verification
    print(f'========== DEBUG: Original columns: {list(df.columns)} =========')
    print(f'========== DEBUG: This may take a while - progress will be shown every 100 items =========')
    
    # Gather statistics for each item one at a time, saving progress as you go
    print('========== DEBUG: Gathering statistics for each item (no batch)... =========')
    #from harvest_institution_items import gather_statistics_for_items
    stats_list = []
    items_list = df.to_dict('records')
    try:
        for idx, item in enumerate(items_list):
            print(f'========== DEBUG: Processing item {idx+1}/{len(items_list)} =========')
            #print(f'========== DEBUG: Item dict: {item} =========')
            try:
                stat = gather_statistics_for_items([item])[0]
                print(f'========== DEBUG: Gathered stats for item {item.get("id")}: {stat} =========')
            except Exception as e:
                stat = {"item_id": item.get("id"), "error": str(e)}
                # Merge all metadata fields into stat
                for k, v in item.items():
                    if k not in stat:
                        stat[k] = v
                print(f'========== DEBUG: Error gathering stats for item {item.get("id")}: {e} =========')
            stats_list.append(stat)
            print(f'========== DEBUG: Stats list length: {len(stats_list)} =========')
            if (idx + 1) % 100 == 0 or (idx + 1) == len(items_list):
                print(f'========== DEBUG: Saving partial stats at item {idx+1} =========')
                # Print stats_list for inspection before creating DataFrame
               # print(f'========== DEBUG: stats_list preview (first 1000): {stats_list[:1000]} =========')
                print(f'========== DEBUG: stats_list length: {len(stats_list)} =========')
                df_with_stats = pd.DataFrame(stats_list)
                print(f'========== DEBUG: Created DataFrame with stats, shape: {df_with_stats.shape} =========')
                original_columns = df.columns.tolist()
                new_stats_columns = [
                    'views_url_used', 'views_status_code', 
                    'downloads_url_used', 'downloads_status_code', 'views','downloads'
                ]
                final_columns = original_columns.copy()
                for col in new_stats_columns:
                    if col not in final_columns:
                        final_columns.append(col)
                df_with_stats = df_with_stats.reindex(columns=final_columns)
                print(f'========== DEBUG: Reordered columns, final shape: {df_with_stats.shape} =========')
                print(f'========== DEBUG: Final columns: {list(df_with_stats.columns)} =========')
                if output_file_path is None:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    base_name = csv_file_path.replace('.csv', '')
                    output_file_path = f'{base_name}_with_stats_{timestamp}.csv'
                print(f'========== DEBUG: Saving updated CSV to: {output_file_path} =========')
                try:
                    df_with_stats.to_csv(output_file_path, index=False, na_rep='None')
                    print(f'✅ Progress saved to: {output_file_path}')
                    log_to_file(f'Progress saved to: {output_file_path}')
                except Exception as e:
                    print(f'❌ ERROR: Failed to save CSV file: {e}')
                    log_to_file(f'ERROR: Failed to save CSV file: {e}')
    except KeyboardInterrupt:
        print('\n⚠️ Interrupted by user! Saving partial stats...')
        log_to_file('Interrupted by user! Saving partial stats...')
        df_with_stats = pd.DataFrame(stats_list)
        print(f'DEBUG: Created DataFrame with stats, shape: {df_with_stats.shape}')
        original_columns = df.columns.tolist()
        new_stats_columns = [
            'views_url_used', 'views_status_code', 
            'downloads_url_used', 'downloads_status_code','views', 'downloads'
        ]
        final_columns = original_columns.copy()
        for col in new_stats_columns:
            if col not in final_columns:
                final_columns.append(col)
        df_with_stats = df_with_stats.reindex(columns=final_columns)
        print(f'DEBUG: Reordered columns, final shape: {df_with_stats.shape}')
        print(f'DEBUG: Final columns: {list(df_with_stats.columns)}')
        if output_file_path is None:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            base_name = csv_file_path.replace('.csv', '')
            output_file_path = f'{base_name}_with_stats_{timestamp}.csv'
        print(f'DEBUG: Saving updated CSV to: {output_file_path}')
        try:
            df_with_stats.to_csv(output_file_path, index=False)
            print(f'✅ Progress saved to: {output_file_path}')
            log_to_file(f'Progress saved to: {output_file_path}')
        except Exception as e:
            print(f'❌ ERROR: Failed to save CSV file: {e}')
            log_to_file(f'ERROR: Failed to save CSV file: {e}')
        return output_file_path
    return output_file_path

def main():
    set_log_filename()
    """Main function to run the statistics addition process"""
    
    # Specify the CSV file to process
    #input_csv = 'harvested_items_2025-08-05_12-51-48.csv'
    #input_csv='harvested_items_2025-08-07_11-29-01.csv'
    #input_csv='harvested_items_2025-09-01_17-23-30_fullmeta.csv'
    #input_csv='harvested_items_2025-09-09_15-46-06_fullmeta.csv'
    #input_csv='harvested_items_2025-09-09_17-45-43_fullmeta.csv'
    input_csv='harvested_items_2025-09-11_23-14-18_fullmeta.csv'
    #input_csv= "harvested-items.csv"
    print(f'🚀 Starting statistics addition for: {input_csv}')
    #quit()
    print(f'📅 Started at: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    log_to_file(f'Starting statistics addition for: {input_csv}')
    log_to_file(f'Started at: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    try:
        # Add statistics to the CSV
        output_file = add_statistics_to_csv(input_csv)
        
        if output_file:
            print(f'\n🎉 PROCESS COMPLETED SUCCESSFULLY!')
            print(f'📄 Input file: {input_csv}')
            print(f'📄 Output file: {output_file}')
            print(f'\n📋 The new file includes all original columns plus:')
            print(f'   • views_url_used: The URL used to fetch views statistics')
            print(f'   • views_status_code: HTTP status code from views API')
            print(f'   • views: Total view count')
            print(f'   • downloads_url_used: The URL used to fetch downloads statistics')
            print(f'   • downloads_status_code: HTTP status code from downloads API')
            print(f'   • downloads: Download count (if available)')
            print(f'\n⏰ Completed at: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        else:
            print(f'\n❌ PROCESS FAILED!')
            
    except FileNotFoundError:
        print(f'❌ ERROR: File not found: {input_csv}')
        print(f'Please make sure the file exists in the current directory.')
        log_to_file(f'ERROR: File not found: {input_csv}')
        
    except Exception as e:
        print(f'❌ ERROR: Unexpected error occurred: {e}')
        log_to_file(f'ERROR: Unexpected error occurred: {e}')

if __name__ == "__main__":
    main()
