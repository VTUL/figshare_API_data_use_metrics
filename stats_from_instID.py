import requests
import json
import pandas as pd
import datetime

BASE_URL = 'https://api.figshare.com/v2'

# Read institution abbreviations from the third sheet of the Excel file
excel_file = 'institutionListOAI_20250730.xlsx'
inst_df = pd.read_excel(excel_file, sheet_name=2)  # 0-based index, so 2 is the third sheet
# Assume the abbreviation column is named 'inst_abbrev' (adjust if needed)
institution_abbrevs = inst_df['inst_abbrev'].dropna().unique().tolist()

all_stats = []

for inst_abbrev in institution_abbrevs:
    print(f"Processing institution: {inst_abbrev}")
    # Query for datasets posted in 2022
    query = {
        "search_for": ":defined_type_name:dataset AND :posted_before:2022-12-31 AND :posted_after:2022-01-01"
    }
    results = []
    for page in range(1, 1000):
        resp = requests.post(
            f"{BASE_URL}/articles/search?page_size=1000&page={page}",
            json=query
        )
        items = json.loads(resp.content)
        if not items:
            break
        results.extend(items)
        print(f"Institution {inst_abbrev} - Page {page}: {len(items)} items retrieved")
    print(f"Institution {inst_abbrev}: Total items harvested: {len(results)}")

    # For each item, gather statistics using the abbreviation logic from oaimphFig.py
    for item in results:
        item_id = item.get('id')
        url_public_html = item.get('url_public_html', '')
        stats_url = ''
        stats = {}
        if url_public_html:
            url_parts = url_public_html.split('//')[1].split('.')
            # Try first part
            stats_url_1 = f"https://stats.figshare.com/{inst_abbrev}/total/views/article/{item_id}"
            stats_resp_1 = requests.get(stats_url_1)
            if stats_resp_1.status_code == 200:
                stats = stats_resp_1.json()
                stats_url = stats_url_1
                if stats.get('totals', 0) > 0:
                    pass  # Use this stats_url
                else:
                    # Try the second part if available
                    if len(url_parts) > 1:
                        stats_url_2 = f"https://stats.figshare.com/{url_parts[1]}/total/views/article/{item_id}"
                        stats_resp_2 = requests.get(stats_url_2)
                        if stats_resp_2.status_code == 200:
                            stats2 = stats_resp_2.json()
                            if stats2.get('totals', 0) > 0:
                                stats = stats2
                                stats_url = stats_url_2
            else:
                # Fallback to old style if public_html fails
                stats_url = f"https://stats.figshare.com/item/total/views/article/{item_id}"
                stats_resp = requests.get(stats_url)
                if stats_resp.status_code == 200:
                    stats = stats_resp.json()
        else:
            # Fallback if no public_html
            stats_url = f"https://stats.figshare.com/item/total/views/article/{item_id}"
            stats_resp = requests.get(stats_url)
            if stats_resp.status_code == 200:
                stats = stats_resp.json()
        stats['item_id'] = item_id
        stats['inst_abbrev'] = inst_abbrev
        stats['stats_url'] = stats_url
        all_stats.append(stats)
        print(f"Processed item {item_id} for institution {inst_abbrev}")

# Save statistics to CSV
stats_df = pd.DataFrame(all_stats)
today = datetime.datetime.now().strftime("%Y-%m-%d")
stats_df.to_csv(f"figshare_stats_by_inst_abbrev_{today}.csv", index=False)
print("All statistics saved to CSV file.")