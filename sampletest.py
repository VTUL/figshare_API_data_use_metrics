import json
import random
import requests
import pandas as pd

# Load already gathered institution items and figshare.com items
with open('harvested_items_2025-08-22_13-48-58.json') as f:
    institution_items = json.load(f)
with open('figshare_public_items_2025-08-26.json') as f:
    figshare_items = json.load(f)

# For testing: limit to first 5 institution items
test_institution_items = institution_items[:5]
n_institution = len(test_institution_items)

# Randomly select as many figshare.com items as institution items
figshare_sample = random.sample(figshare_items, min(n_institution, len(figshare_items)))

# Fetch full metadata for institution items
enriched_institution_items = []
for idx, item in enumerate(test_institution_items):
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

# Fetch full metadata for sampled figshare.com items
enriched_figshare_sample = []
for idx, item in enumerate(figshare_sample):
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

# Combine and save results
final_items = enriched_institution_items + enriched_figshare_sample
with open('test_enriched_items.json', 'w') as f:
    json.dump(final_items, f, indent=2)
pd.DataFrame(final_items).to_csv('test_enriched_items.csv', index=False)
print(f"Saved {len(final_items)} enriched items to test_enriched_items.json and test_enriched_items.csv")