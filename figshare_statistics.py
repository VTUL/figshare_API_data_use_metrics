import pandas as pd
import datetime
import random
from figshare_statistics_for_categories import itemids_for_categories,figshare_categorystatistics, fetch_figshare_statistics, fetch_figshare_statistics

#Gather item ids for each category and write it to a csv file

#read the categories numbers and match it with the names provided in Figshare_categories.csv:
file_path = 'C:/Users/padma/anaconda3/envs/figshare_statistics/figshare_statistics_categories/Figshare_categories.csv'
# Define the column names
column_names = ['categoryItemNumber', 'MainCategoryNumber', 'MainCategoryName-Number', 'SubCategoryName','x','y']  # Replace with actual column names

df = pd.read_csv(file_path,names=column_names)

# Fill empty fields in 'categoryItemNumber' with the value above
df['categoryItemNumber'].fillna(method='ffill', inplace=True)

# Fill empty fields in 'MainCategoryNumber' with the value above
df['MainCategoryNumber'].fillna(method='ffill', inplace=True)

# Save the updated DataFrame to a CSV file
df.to_csv('Updated_Figshare_categories.csv', index=False)

#categories=['25777']
#categories=[25720,25723,25726,25729,25732,25735,25738,25741,25744,25747,25750,25753,25756,25759,25762,25765,25768,25771,25774,25777]
category_search='main_category'
#category_search='sub_category'
#####################
##Match with the main category number:
## Define the main category to find
if category_search=='main_category':
  category_to_find = '3704'
## Filter the DataFrame to find the rows that match the main category
  filtered_df = df[df['MainCategoryNumber'] == category_to_find]

##Match with the sub category number:
## Define the sub category to find
if category_search=='sub_category':
  category_to_find = '300101'
## Filter the DataFrame to find the rows that match the subcategory
  filtered_df = df[df['categoryItemNumber'] == category_to_find]
#####################
# Print the filtered DataFrame
print(filtered_df)

# If you need to use the filtered DataFrame for further processing
#categories = filtered_df['categoryItemNumber'].tolist()
categories = filtered_df['SubCategoryName'].tolist()

# Remove NaN values from the 'categories' list
categories = [category for category in categories if pd.notna(category)]

#####################
item_ids_full,item_ids=itemids_for_categories(categories)
#print("**********json is*******************",)
#Fetch metadata for each item id and write it to a json file
#Commenting this out because this takes forever to run:
#item_metadata,error_list,categories_metadata=figshare_categorystatistics(item_ids_full)

# Pick 100 random items from item_ids_full
random_item_ids = random.sample(item_ids_full, min(100, len(item_ids_full)))

print(f"Randomly selected 100 item IDs: {random_item_ids}")
item_metadata,error_list,categories_metadata=figshare_categorystatistics(random_item_ids)
keys_to_keep = ['figshare_url','citation','categories','id','doi','handle','url', 'published_date','defined_type_name']#, 'views','downloads']
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