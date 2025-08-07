#!/usr/bin/env python3
"""
Script to add statistics (views, downloads, stats URLs) to an existing harvested items CSV file.
This script imports and uses the gather_statistics_for_items function from harvest_institution_items.py
"""

import requests
import json

import pandas as pd
import datetime

def log_to_file(*args, **kwargs):
    """Helper function to also write to a log file"""
    with open('add_stats_log.txt', 'a', encoding='utf-8') as f:
        print(*args, **kwargs, file=f)
        
def get_preferred_stats_url_pattern(institution_id, views_url_1, views_url_2):
    """Return 'url1' or 'url2' if the corresponding views URL returns status 200, else None."""
    try:
        resp1 = requests.get(views_url_1)
        if resp1.status_code == 200:
            return 'url1'
        if views_url_2:
            resp2 = requests.get(views_url_2)
            if resp2.status_code == 200:
                return 'url2'
    except Exception as e:
        print(f"DEBUG: Error checking preferred stats URL for institution {institution_id}: {e}")
    return None

def gather_statistics_for_items(items_list, institution_abbrevs=None):
    """
    Gather statistics for harvested items using the logic from oaimphFig.py
    """
    print(f'DEBUG: Starting gather_statistics_for_items with {len(items_list)} items')
    print('Gathering statistics for harvested items...')
    log_to_file('Gathering statistics for harvested items...')
    

    all_stats = []
    # Track preferred stats URL pattern for each institution
    preferred_stats_url_pattern = {}  # institution_id -> 'url1' or 'url2' or None

    for i, item in enumerate(items_list):
        print(f'DEBUG: Processing item {i+1}/{len(items_list)}')
        item_id = item.get('id')
        institution_id = item.get('harvested_institution_id')
        url_public_html = item.get('url_public_html', '')

        print(f'DEBUG: Item {item_id}, Institution {institution_id}, URL: {url_public_html}')

        stats_url = ''
        stats_status_code = None
        stats = {}
        views = None
        downloads = None
        downloads_url = ''
        downloads_status_code = None

        if url_public_html:
            print(f'DEBUG: URL exists, parsing parts')
            url_parts = url_public_html.split('//')[1].split('.')
            print(f'DEBUG: URL parts: {url_parts}')
            # Try first part (institution abbreviation)
            views_url_1 = f"https://stats.figshare.com/{url_parts[0]}/total/views/article/{item_id}"
            views_url_2 = f"https://stats.figshare.com/{url_parts[1]}/total/views/article/{item_id}" if len(url_parts) > 1 else None
            downloads_url_1 = f"https://stats.figshare.com/{url_parts[0]}/total/downloads/article/{item_id}"
            downloads_url_2 = f"https://stats.figshare.com/{url_parts[1]}/total/downloads/article/{item_id}" if len(url_parts) > 1 else None

            # Use preferred pattern if known, else check which views URL works
            pattern = preferred_stats_url_pattern.get(institution_id)
            if pattern is None:
                pattern = get_preferred_stats_url_pattern(institution_id, views_url_1, views_url_2)
                if pattern:
                    preferred_stats_url_pattern[institution_id] = pattern
            print(f"DEBUG: pattern for institution_id {institution_id}: {pattern}")
            print(f"DEBUG: preferred_stats_url_pattern dict: {preferred_stats_url_pattern}")

            # Views
            if pattern == 'url1':
                print(f'DEBUG: Using preferred views_url_1 for institution {institution_id}: {views_url_1}')
                views_resp_1 = requests.get(views_url_1)
                downloads_resp_1 = requests.get(downloads_url_1)
                views_url = views_url_1
                downloads_url = downloads_url_1
                views_status_code = views_resp_1.status_code        
                if views_resp_1.status_code == 200:
                    stats_views = views_resp_1.json()
                    views = stats_views.get("totals")
                    stats_downloads=downloads_resp_1.json()
                    downloads=stats_downloads.get("totals")
                    print(f'DEBUG: Views response status: {views_status_code}')
                    print('downloads are ',downloads)
                    print('views are ',views)
                    downloads_status_code = downloads_resp_1.status_code
                else:
                    print(f"DEBUG: Downloads API response (not 200): {downloads_resp_1.text}")
            elif pattern == 'url2' and views_url_2:
                print(f'DEBUG: Using preferred views_url_2 for institution {institution_id}: {views_url_2}')
                views_resp_2 = requests.get(views_url_2)
                views_url = views_url_2
                views_status_code = views_resp_2.status_code
                if views_resp_2.status_code == 200:
                    stats = views_resp_2.json()
                    views = stats.get("totals")
                    print('views are ',views)
                    # Dedicated downloads stats URL (url2)
                    downloads_url = downloads_url_2
                    downloads_resp = requests.get(downloads_url)
                    print(f'DEBUG: Downloads response status: {downloads_resp.status_code}')
                    downloads_status_code = downloads_resp.status_code
                    if downloads_resp.status_code == 200:
                        downloads = downloads_resp.json().get("totals")
                        print('downloads are ',downloads)
                    else:
                        print(f"DEBUG: Downloads API response (not 200): {downloads_resp.text}")
            else:
                print(f'DEBUG: No preferred pattern, using fallback')
                views='None'
                downloads='None'
        else:
            print(f'DEBUG: No URL, using fallback')
            views='None'
            downloads='None'
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
        all_stats.append(stats)
        
        print(f"DEBUG: Completed processing item {item_id} for institution {institution_id}")
        print(f"Processed item {item_id} for institution {institution_id}")
        log_to_file(f"Processed item {item_id} for institution {institution_id}")
    
    print(f'DEBUG: Completed gathering statistics for {len(all_stats)} items')
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
        print(f'========== DEBUG: CSV loaded, shape: {df.shape} =========')
        print(f'========== DEBUG: Loaded {len(df)} items from CSV =========')
        log_to_file(f'Loaded {len(df)} items from CSV')
        
        # Display column names for verification
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
            print(f'========== DEBUG: Item dict: {item} =========')
            try:
                stat = gather_statistics_for_items([item])[0]
                print(f'========== DEBUG: Gathered stats for item {item.get("id")}: {stat} =========')
            except Exception as e:
                stat = {"item_id": item.get("id"), "error": str(e)}
                print(f'========== DEBUG: Error gathering stats for item {item.get("id")}: {e} =========')
            stats_list.append(stat)
            print(f'========== DEBUG: Stats list length: {len(stats_list)} =========')
            if (idx + 1) % 100 == 0 or (idx + 1) == len(items_list):
                print(f'========== DEBUG: Saving partial stats at item {idx+1} =========')
                df_with_stats = pd.DataFrame(stats_list)
                print(f'========== DEBUG: Created DataFrame with stats, shape: {df_with_stats.shape} =========')
                original_columns = df.columns.tolist()
                new_stats_columns = ['stats_url_used', 'stats_status_code', 'views', 'downloads']
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
                    df_with_stats.to_csv(output_file_path, index=False)
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
        new_stats_columns = ['stats_url_used', 'stats_status_code', 'views', 'downloads']
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
    """Main function to run the statistics addition process"""
    
    # Specify the CSV file to process
    #input_csv = 'harvested_items_2025-08-05_12-51-48.csv'
    input_csv='harvested_items_2025-08-07_11-29-01.csv'
    #input_csv= "harvested-items.csv"
    print(f'🚀 Starting statistics addition for: {input_csv}')
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
            print(f'   • stats_url_used: The URL used to fetch statistics')
            print(f'   • stats_status_code: HTTP status code from stats API')
            print(f'   • views: Total view count')
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
