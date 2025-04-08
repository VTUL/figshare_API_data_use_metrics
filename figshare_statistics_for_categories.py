import json
import requests
import csv
import json as json
import datetime
import pandas as pd
import numpy as np
import os

def itemids_for_categories(categories):
    BASE_URL = 'https://api.figshare.com/v2'
    results = []  # create a blank list
    # search string taken from https://help.figshare.com/article/search-examples for multiple fields
    for i in categories:
        query = '{"search_for":":category: ' + i + '"}'
       # query = {"search_for": ":category_name: \"{i}\""}
        #query = '{"search_for":":category: f'"{i}"'}'
        print('category is', i)
        print('query is', query)
        y = json.loads(query)  # Figshare API requires JSON parameters
        # Get the total number of pages
        for j in range(1, 50):
           # r = json.loads(requests.post(BASE_URL + '/articles/search?page_size=1000&page={}'.format(j), params=y).content)
            r = json.loads(requests.post(BASE_URL + '/articles/search?page_size=1000&page={}'.format(j), json=y).content)
            results.extend(r)  # Add the retrieved records to the list of records
    # Filter results to remove any strings or non-dictionary elements
    results = [item for item in results if isinstance(item, dict)]
    # Save all results to a JSON file
    with open('all_results_' + str(datetime.datetime.now().strftime("%Y-%m-%d")) + '.json', 'w') as f:
        json.dump(results, f)
    
    # See the number of items
    print('items retrieved total', len(results))
    # Filter and pick the 'id', 'defined_type_name', and 'published_date' where 'defined_type_name' is 'dataset' and 'published_date' is in range
    filtered_items = [
        (item['id'], item.get('defined_type_name', ''), item.get('published_date', ''))
        for item in results
        if item.get('defined_type_name') == 'dataset' and '2022-01-01' <= item.get('published_date', '') <= '2022-12-31'
    ]
    print('Filtered items for defined_type_name "dataset" and published_date in range:', filtered_items)
    # Remove duplicates by converting to a dictionary and back to a list
    item_ids = list(dict.fromkeys([item[0] for item in filtered_items]))
    print(len(filtered_items) - len(item_ids), 'duplicate records removed,', len(item_ids), 'unique records remain')
    print('List of item IDs created, called item_ids', item_ids)

    # Ensure the file is closed before overwriting
    output_file = 'item_ids_with_type_and_date_' + str(datetime.datetime.now().strftime("%Y-%m-%d")) + '.csv'
    try:
        # Attempt to close the file if it is open
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
                print(f"Closed and removed existing file: {output_file}")
            except PermissionError:
                print(f"PermissionError: Unable to remove {output_file}. Ensure the file is not open elsewhere.")
                return [], []
        # Write to the file
        with open(output_file, 'w', newline='') as outfile:
            out = csv.writer(outfile)
            out.writerow(['id', 'defined_type_name', 'published_date'])  # Add headers
            out.writerows(filtered_items)
    except PermissionError:
        print(f"PermissionError: Unable to write to {output_file}. Ensure the file is not open elsewhere.")
        return [], []

    return [item[0] for item in filtered_items], item_ids

def figshare_categorystatistics(itemList):
    item_metadata = []
    error_list = []
    categories_metadata = []

    for id in itemList:
        m = requests.get('https://api.figshare.com/v2/articles/' + str(id))
        metadata=json.loads(m.text)

        if m.status_code == 200: #if successful

            #Add counts:
            metadata['count_categories'] = len(metadata['categories']) 
            metadata['count_references'] = len(metadata['related_materials'])
            metadata['count_tags'] = len(metadata['tags'])
            metadata['size_GB'] = metadata['size']/1000000000 
            try:
                metadata['posted_year'] = metadata['timeline']['posted'].split("-")[0] #gives 2022
            except:
                metadata['posted_year'] = ''

            item_metadata.append(metadata)

            cats = metadata['categories'] 
            for c in cats:
              c['item_id'] = id 
              categories_metadata.append(c)          

        else:  
          e = {}
          e['item_id'] = id
          e['code'] = m.status_code
          error_list.append(e)

        if len(item_metadata)%100 == 0:
          print(len(item_metadata),'records done and counting')



        #descriptor='figshare-statistics-earth-sciences-category'
        descriptor='figshare-statistics-category'
        #jsonfilename=descriptor + '-full_records-'+str(datetime.datetime.now().strftime("%Y-%m-%d"))
        with open(descriptor + '-full_records-'+str(datetime.datetime.now().strftime("%Y-%m-%d"))+'.json', 'w') as f:
           json.dump(item_metadata, f)

#save the json for errors
        with open(descriptor + '-error-list.json', 'w') as f:
          json.dump(error_list, f)

    print('Done.',len(item_metadata),"items detailed")
    return item_metadata,error_list,categories_metadata#,jsonfilename

def fetch_figshare_statistics(file_path):
    df = pd.read_csv(file_path)
    print(df)

    df['idstr'] = df['id'].astype(str)
    #df['institute'] = df['figshare_url'].str.split('.', n=2).str[1]
    #print('https://stats.figshare.com/' + df['institute'] + '/total/views/article/' + df['idstr'])
    #df['institute'] = df['figshare_url'].str.split('.', n=2).str[1]
   # df['inst_abbr'] = df['figshare_url'].str.split('.', n=2).str[1]
# Extract the institute name from the 'figshare_url' column
    df['institute'] = df['figshare_url'].str.extract(r'https://(?:www\.)?([a-zA-Z0-9\-]+)\.figshare|https://(?:www\.)?([a-zA-Z0-9\-]+)\.ac\.uk').bfill(axis=1).iloc[:, 0]
# Fill NaN values in 'institute' with 'figshare' for URLs like 'https://figshare.com'
    df['institute'] = df['institute'].fillna('figshare')

# Print the DataFrame to verify the extracted institute names
    print(df[['figshare_url', 'institute']])
    #print('https://stats.figshare.com/' + df['inst_abbr'] + '/total/views/article/' + df['idstr'])
    # Save the DataFrame to a CSV file
    output_file = 'extracted_figshare_statistics_' + str(datetime.datetime.now().strftime("%Y-%m-%d")) + '.csv'
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Data saved to {output_file}")
    df['inst_views'] = np.nan
    df['inst_downloads'] = np.nan
    df['stats_views_url'] = 'np.nan'
    df['stats_downloads_url'] = 'np.nan'
    instviews = []
    instdownloads = []

    for i in range(len(df['id'])):
        if df['institute'][i] == 'figshare':
            views = json.loads(requests.get('https://stats.figshare.com/total/views/article/' + df['idstr'][i]).content)
            downs = json.loads(requests.get('https://stats.figshare.com/total/downloads/article/' + df['idstr'][i]).content)
            print(' is figshare, url: ', 'https://stats.figshare.com/total/views/article/' + df['idstr'][i], views.get('totals'))
            df['stats_views_url'][i] = 'https://stats.figshare.com/total/views/article/' + df['idstr'][i]
            df['stats_downloads_url'][i] = 'https://stats.figshare.com/total/downloads/article/' + df['idstr'][i]
        else:
            views = json.loads(requests.get('https://stats.figshare.com/' + df['institute'][i] + '/total/views/article/' + df['idstr'][i]).content)
            downs = json.loads(requests.get('https://stats.figshare.com/' + df['institute'][i] + '/total/downloads/article/' + df['idstr'][i]).content)
            df['stats_views_url'][i] = 'https://stats.figshare.com/' + df['institute'][i] + '/total/views/article/' + df['idstr'][i]
            df['stats_downloads_url'][i] = 'https://stats.figshare.com/' + df['institute'][i] + '/total/downloads/article/' + df['idstr'][i]
        instviews.append(views)
        instdownloads.append(downs)
        print(views, views.get('totals'))
        print(downs, downs.get('totals'))
        df['inst_views'][i] = views.get('totals')
        df['inst_downloads'][i] = downs.get('totals')

        print('len is', len(df['id']), 'i is ', i)

    df.to_csv('views_and_downloads_figshare_' + str(datetime.datetime.now().strftime("%Y-%m-%d")) + '.csv', encoding='utf-8', index=False)
    print('done')

def closeFile(file_path):
    try:
        os.system('TASKKILL /F /IM '+ file_path)
    except Exception:
        print("All closed")

#closeFile()
#fetch_figshare_statistics("c:/Users/padma/anaconda3/envs/curation/LimitedMetadataInEarthSciencesCategory.csv")
