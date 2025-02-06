import json
import csv
import pandas as pd
from sys import path
import os,sys
from os.path import join, split, dirname, realpath
#path.append(join(split(dirname(realpath(__file__)))[0], 'curation'))
import sys
import os
import datetime
# Get the current script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Get the parent directory
parent_dir = os.path.dirname(current_dir)

# Get the parent parent directory
parent_parent_dir = os.path.dirname(parent_dir)

# Append the parent parent directory to the Python path
sys.path.append(parent_dir)
print(parent_dir)
def filter_and_save_json(json_file, csv_file, keys_to_keep):
    with open(json_file, 'r',encoding="utf8") as f:
        data = json.load(f)

    filtered_data = []
    for item in data:
        filtered_item = {key: item[key] for key in keys_to_keep if key in item}
        filtered_data.append(filtered_item)

    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys_to_keep)
        writer.writeheader()
        writer.writerows(filtered_data)

# Example Usage
json_file = 'c:/Users/padma/anaconda3/envs/curation/figshare-statistics-earth-sciences-category-full_records-2025-01-31.json'
#keys_to_keep = ['figshare_url','citation','categories','id','doi','handle','url', 'published_date', 'views','downloads']
keys_to_keep = ['figshare_url','citation','categories','id','doi','handle','url', 'published_date']#, 'views','downloads']
with open(json_file, encoding='utf-8') as inputfile: 
  df = pd.read_json(inputfile)
#filter_and_save_json(json_file, csv_file, keys_to_keep)
#all metadata csv:
df.to_csv('allMetadataInEarthSciencesCategory.csv', encoding='utf-8', index=False)
# Save the DataFrame to a CSV file with only the specified columns
df.to_csv('LimitedMetadataInEarthSciencesCategory.csv', columns=keys_to_keep, index=False)
#all metadata for test itmes
df.to_csv('allMetadataInFigshare_report_datasets'+str(datetime.datetime.now().strftime("%Y-%m-%d"))+'.csv', encoding='utf-8', index=False)
# Save the DataFrame to a CSV file with only the specified columns
df.to_csv('LimitedMetadataInFigshare_report_datasets'+str(datetime.datetime.now().strftime("%Y-%m-%d"))+'.csv', columns=keys_to_keep, index=False)
# Load JSON data
data = json.loads(json_data)

