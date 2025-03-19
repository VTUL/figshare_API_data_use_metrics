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
  #categories=["'Earth sciences'"]
  #categories=["'25756'"]
#Gather basic metadata for items (articles) that meet your search criteria
  results = [] #create a blank list
  for i in categories:
    query = '{"search_for":":category: ' + i + '"}'
    print('query is',query)
    y = json.loads(query) #Figshare API requires json paramaters
    #The number of results is unknown but you can collect up to 9,000 results. This sets the page size to 1000 results and calls the API 
    #to retrieve results
    #for j in range(1,10000): #Collect 5 pages of results
    for j in range(1,10): #Collect 5 pages of results
        r = json.loads(requests.post(BASE_URL + '/articles/search?page_size=1000&page={}'.format(j), params=y).content)
        print('page',j,'for term',i,'collected successfully')
        results.extend(r) #add the retrieved records to the list of records
#See the number of items
  print(len(results),'items retrieved total')
  print('result is ',results)
#Create a list of all the item ids
  item_ids_full = [item['id'] for item in results]  

#Remove duplicates by converting to a dictionary and back to a list
  item_ids = list( dict.fromkeys(item_ids_full) ) 
  print(len(item_ids_full)-len(item_ids),'duplicate records removed,',len(item_ids),'unique records remain')
  print('List of item ids created, called item_ids', item_ids_full)
  outfile = open('item_ids'+str(datetime.datetime.now().strftime("%Y-%m-%d"))+'.csv','w')
  out = csv.writer(outfile)
  out.writerows(map(lambda x: [x], item_ids_full))
  outfile.close()
  return item_ids_full,item_ids

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
    df['institute'] = df['figshare_url'].str.split('.', n=2).str[1]
    print('https://stats.figshare.com/' + df['institute'] + '/total/views/article/' + df['idstr'])
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
