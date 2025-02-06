import json
import requests
import csv
import os
import json as json
import datetime
import pandas as pd
import numpy as np


df = pd.read_csv("c:/Users/padma/anaconda3/envs/curation/LimitedMetadataInEarthSciencesCategory.csv")
print(df)

df['idstr']=df['id'].astype(str)
df['institute'] = df['figshare_url'].str.split('.', n=2).str[1]
print('https://stats.figshare.com/'+df['institute']+'/total/views/article/' + df['idstr'])
df['inst_views'] = np.nan
df['inst_downloads'] = np.nan
df['stats_views_url'] = 'np.nan'
df['stats_downloads_url'] ='np.nan'
#df['inst']='np.nan'
instviews=[]
instdownloads=[]
for i in range(len(df['id'])):
    if df['institute'][i]=='figshare':
      views = json.loads(requests.get('https://stats.figshare.com/total/views/article/' + df['idstr'][i]).content) #this gives 41
      downs = json.loads(requests.get('https://stats.figshare.com/total/downloads/article/' + df['idstr'][i]).content) #this gives 5
      print(' is figshare, url: ','https://stats.figshare.com/total/views/article/' + df['idstr'][i],views.get('totals'))
      df['stats_views_url'][i]='https://stats.figshare.com/total/views/article/' + df['idstr'][i]
      df['stats_downloads_url'][i]='https://stats.figshare.com/total/downloads/article/' +df['idstr'][i]
    else:
      views = json.loads(requests.get('https://stats.figshare.com/'+df['institute'][i]+'/total/views/article/' + df['idstr'][i]).content) #this gives 41
      downs = json.loads(requests.get('https://stats.figshare.com/'+df['institute'][i]+'/total/downloads/article/' + df['idstr'][i]).content) #this gives 5
      df['stats_views_url'][i]='https://stats.figshare.com/'+df['institute'][i]+'/total/views/article/' + df['idstr'][i]
      df['stats_downloads_url'][i]='https://stats.figshare.com/'+df['institute'][i]+'/total/downloads/article/' +df['idstr'][i]
    instviews.append(views)
    instdownloads.append(downs)
    print(views,views.get('totals'))
    print(downs,downs.get('totals'))
    df['inst_views'][i] = views.get('totals')
    df['inst_downloads'][i] = downs.get('totals')

    print('len is',len(df['id']), 'i is ',i)

def closeFile():

    try:
        os.system('TASKKILL /F /IM excel.exe')

    except Exception:
        print("All closed")

closeFile()
df.to_csv('views_and_downloads_earthscience_figshare_'+str(datetime.datetime.now().strftime("%Y-%m-%d"))+'.csv', encoding='utf-8', index=False)
print('done')
