import pandas as pd
import datetime
from datetime import datetime, timedelta
import random
import json
import csv
import os
import logging
import time
import requests
import json as json
import numpy as np
import time
# Record the start time of the script
start_time = time.time()
print(f"Script started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logging.info(f"Script started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


# Define the save directory
save_directory = r"c:\Users\padma\anaconda3\envs\figshare_statistics\figshare_statistics_categories"
json_filename = os.path.join(save_directory, 'all_results_' + str(datetime.now().strftime("%Y-%m-%d")) + '.json')
csv_filename = os.path.join(save_directory, "all_results_" + str(datetime.now().strftime("%Y-%m-%d")) + ".csv")


# Configure logging
log_filename = os.path.join(save_directory, "progress_log_" + str(datetime.now().strftime("%Y-%m-%d")) + ".txt")
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logging.info("Script started.")

BASE_URL = 'https://api.figshare.com/v2'
results = []  # create a blank list



# Function to generate 5-day intervals for a given month
def generate_date_ranges(year, month):
    start_date = datetime(year, month, 1)
    end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)  # Last day of the month
    date_ranges = []
    current_date = start_date

    while current_date <= end_date:
        next_date = current_date + timedelta(days=4)
        if next_date > end_date:
            next_date = end_date
        date_ranges.append((current_date.strftime("%Y-%m-%d"), next_date.strftime("%Y-%m-%d")))
        current_date = next_date + timedelta(days=1)

    return date_ranges

# Generate 5-day intervals for the entire year
date_ranges = []

for month in range(1, 13):  # Loop through all months (1 to 12)
    date_ranges.extend(generate_date_ranges(2022, month))

#******************Test date ranges********************
# Define a short date range for testing (2 days)
date_ranges = [
    ("2022-01-01", "2022-01-02")  # Replace with any desired 2-day range
]

# Print the test date ranges for verification
print("Testing with the following date ranges:")
#**************************
# Print the generated date ranges for verification
for start_date, end_date in date_ranges:
    print(f"Start: {start_date}, End: {end_date}")

print(f"Date ranges generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logging.info(f"Date ranges generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

for start_date, end_date in date_ranges:
    range_start_time = time.time()  # Record the start time for this date range
    logging.info(f"Processing date range: {start_date} to {end_date}")
    print(f"Processing date range: {start_date} to {end_date}")
    query = {
        "search_for": f":item_type: dataset AND :posted_before: {end_date} AND :posted_after: {start_date}"
    }
    for j in range(1, 1000):  # Limit to 10 pages per date range
        logging.info(f"Fetching page {j} for date range {start_date} to {end_date}")
        print(f"Fetching page {j} for date range {start_date} to {end_date}")
        response = requests.post(
            BASE_URL + '/articles/search?page_size=1000&page={}'.format(j),
            json=query
        )
        #print(len)
        if response.status_code != 200:
            logging.error(f"Error fetching page {j}: {response.status_code} - {response.text}")
            print(f"Error fetching page {j}: {response.status_code} - {response.text}")
            break
        r = json.loads(response.content)
        if not r:  # Break if no results are returned
            logging.info(f"No more results for page {j}. Moving to the next date range.")
            print(f"No more results for page {j}. Moving to the next date range.")
            break
        if len(r) < 1000:  # Stop if fewer than 1,000 results are returned
            logging.info(f"Fewer than 1,000 results on page {j}. ")
            print(f"Fewer than 1,000 results on page {j}. ")
          #  break
        results.extend(r)
        logging.info(f"Page {j} fetched successfully. Total results so far: {len(results)}")
        print(f"Page {j} fetched successfully. Total results so far: {len(results)}")
        time.sleep(10)  # Add a delay to avoid hitting rate limits
        range_end_time = time.time()
        print(f"Finished processing date range {start_date} to {end_date} in {range_end_time - range_start_time:.2f} seconds")
        logging.info(f"Finished processing date range {start_date} to {end_date} in {range_end_time - range_start_time:.2f} seconds")

# Filter results to remove any strings or non-dictionary elements
results = [item for item in results if isinstance(item, dict)]
logging.info(f"Filtered results. Total valid items: {len(results)}")
print(f"Filtered results. Total valid items: {len(results)}")



# Save all results to a JSON file
with open(json_filename, 'w') as f:
    json.dump(results, f)
logging.info(f"Results saved to JSON file: {json_filename}")
print(f"Results saved to JSON file: {json_filename}")
json_save_time = time.time()
print(f"Results saved to JSON file at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logging.info(f"Results saved to JSON file at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Time taken to save JSON: {json_save_time - range_end_time:.2f} seconds")
# Convert JSON file to CSV file
try:
    df = pd.read_json(json_filename)  # Read the JSON file into a pandas DataFrame
    df.to_csv(csv_filename, index=False, encoding="utf-8")  # Save the DataFrame as a CSV file
    logging.info(f"Results converted to CSV file: {csv_filename}")
    print(f"Results converted to CSV file: {csv_filename}")
except Exception as e:
    logging.error(f"Error converting JSON to CSV: {e}")
    print(f"Error converting JSON to CSV: {e}")




logging.info(f"Starting to fetch statistics and save to CSV: {csv_filename}")
print(f"Starting to fetch statistics and save to CSV: {csv_filename}")




#&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
# Read the CSV file
df = pd.read_csv(csv_filename)
print(df)

# Convert 'id' column to string
df['idstr'] = df['id'].astype(str)

# Extract the institute name from the 'url_public_html' column
df['institute'] = df['url_public_html'].str.extract(
    r'https://(?:www\.)?([a-zA-Z0-9\-]+)\.figshare|https://(?:www\.)?([a-zA-Z0-9\-]+)\.ac\.uk'
).bfill(axis=1).iloc[:, 0]

# Fill NaN values in 'institute' with 'figshare' for URLs like 'https://figshare.com'
df['institute'] = df['institute'].fillna('figshare')

# Print the DataFrame to verify the extracted institute names
print(df[['url_public_html', 'institute']])

# Save the DataFrame to a CSV file
output_file = os.path.join(save_directory, 'extracted_figshare_statistics_' + str(datetime.now().strftime("%Y-%m-%d")) + '.csv')
df.to_csv(output_file, index=False, encoding='utf-8')
print(f"Data saved to {output_file}")

# Initialize new columns for statistics
df['inst_views'] = np.nan
df['inst_downloads'] = np.nan
df['stats_views_url'] = np.nan
df['stats_downloads_url'] = np.nan

# Lists to store views and downloads
instviews = []
instdownloads = []
stats_start_time = time.time()
# Fetch statistics for each item
for i in range(len(df['id'])):
    if df['institute'][i] == 'figshare':
        # Fetch views and downloads for 'figshare'
        views = json.loads(requests.get(
            'https://stats.figshare.com/total/views/article/' + df['idstr'][i]
        ).content)
        downs = json.loads(requests.get(
            'https://stats.figshare.com/total/downloads/article/' + df['idstr'][i]
        ).content)
        print('is figshare, url:', 'https://stats.figshare.com/total/views/article/' + df['idstr'][i], views.get('totals'))
        df.loc[i, 'stats_views_url'] = 'https://stats.figshare.com/total/views/article/' + df['idstr'][i]
        df.loc[i, 'stats_downloads_url'] = 'https://stats.figshare.com/total/downloads/article/' + df['idstr'][i]
    else:
        # Fetch views and downloads for other institutes
        views = json.loads(requests.get(
            'https://stats.figshare.com/' + df['institute'][i] + '/total/views/article/' + df['idstr'][i]
        ).content)
        downs = json.loads(requests.get(
            'https://stats.figshare.com/' + df['institute'][i] + '/total/downloads/article/' + df['idstr'][i]
        ).content)
        df.loc[i, 'stats_views_url'] = 'https://stats.figshare.com/' + df['institute'][i] + '/total/views/article/' + df['idstr'][i]
        df.loc[i, 'stats_downloads_url'] = 'https://stats.figshare.com/' + df['institute'][i] + '/total/downloads/article/' + df['idstr'][i]

    # Append views and downloads to lists
    instviews.append(views)
    instdownloads.append(downs)

    # Update DataFrame with totals
    print(views, views.get('totals'))
    print(downs, downs.get('totals'))
    df.loc[i, 'inst_views'] = views.get('totals')
    df.loc[i, 'inst_downloads'] = downs.get('totals')

    print('len is', len(df['id']), 'i is', i)
stats_end_time = time.time()
print(f"Statistics fetching completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logging.info(f"Statistics fetching completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Time taken to fetch statistics: {stats_end_time - stats_start_time:.2f} seconds")

# Save the updated DataFrame to a new CSV file
output_file = os.path.join(save_directory, 'views_and_downloads_figshare_' + str(datetime.now().strftime("%Y-%m-%d")) + '.csv')
df.to_csv(output_file, encoding='utf-8', index=False)
print('Data saved to', output_file)
print('done')
logging.info("Statistics fetching completed.")
print("Statistics fetching completed.")
# Record the end time of the script
end_time = time.time()
print(f"Script completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logging.info(f"Script completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Total time taken: {end_time - start_time:.2f} seconds")
