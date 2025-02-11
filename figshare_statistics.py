import pandas as pd
import datetime
from figshare_statistics_for_categories import itemids_for_categories,figshare_categorystatistics, fetch_figshare_statistics, fetch_figshare_statistics
categories=["'Earth sciences'"]
#categories=["'25756'"]
#categories=["'25720'","'25723'","'25726'","'25729'","'25732'","'25735'","'25738'","'25741'","'25744'","'25747'","'25750'","'25753'","'25756'","'25759'","'25762'","'25765'","'25768'","'25771'","'25774'","'25777'","'25780'","'25783'","'25786'","'25789'","'25792'","'25795'","'25798'","'25801'","'25804'","'25807'","'25810'","'25813'","'25816'","'25819'","'25822'","'25825'","'25828'","'25831'","'25834'","'25837'","'25840'","'25843'","'25846'","'25849'","'25852'","'25855'","'25858'","'25861'","'25864'","'25867'","'25870'","'25873'","'25876'","'25879'","'25882'","'25885'","'25888'","'25891'","'25894'","'25897'","'25900'","'25903'","'25906'","'25909'","'25912'","'25915'","'25918'","'25921'","'25924'","'25927'","'25930'","'25933'","'25936'","'25939'",25942'"
#Gather item ids for each category and write it to a csv file
item_ids_full,item_ids=itemids_for_categories(categories)

#Fetch metadata for each item id and write it to a json file
item_metadata,error_list,categories_metadata=figshare_categorystatistics(item_ids_full)

keys_to_keep = ['figshare_url','citation','categories','id','doi','handle','url', 'published_date']#, 'views','downloads']
descriptor='figshare-statistics-category'
jsonfilename=descriptor + '-full_records-'+str(datetime.datetime.now().strftime("%Y-%m-%d"))+'.json'

#Convert json file to csv file: all metadata
with open(jsonfilename, encoding='utf-8') as inputfile: 
  df = pd.read_json(inputfile)
#all metadata csv file:
df.to_csv('allMetadataInFigshare_report_datasets'+str(datetime.datetime.now().strftime("%Y-%m-%d"))+'.csv', encoding='utf-8', index=False)
#limited metadata csv file with keys to keep columns:
df.to_csv('LimitedMetadataInFigshare_report_datasets'+str(datetime.datetime.now().strftime("%Y-%m-%d"))+'.csv', columns=keys_to_keep, index=False)

#Gather figshare statistics for each item id and write it to a csv file:
fetch_figshare_statistics('LimitedMetadataInFigshare_report_datasets'+str(datetime.datetime.now().strftime("%Y-%m-%d"))+'.csv')