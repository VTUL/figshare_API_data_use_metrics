import pandas as pd
import datetime
import random
from figshare_statistics_for_categories import (
    itemids_for_categories,
    figshare_categorystatistics,
    fetch_figshare_statistics,
)

# Gather item IDs for each category and write it to a CSV file

# Read the category numbers and match them with the names provided in Figshare_categories.csv
file_path = (
    "C:/Users/padma/anaconda3/envs/figshare_statistics/"
    "figshare_statistics_categories/Figshare_categories.csv"
)
# Define the column names
column_names = [
    "categoryItemNumber",
    "MainCategoryNumber",
    "MainCategoryName-Number",
    "SubCategoryName",
    "x",
    "y",
]  # Replace with actual column names

df = pd.read_csv(file_path, names=column_names)

# Fill empty fields in 'categoryItemNumber' with the value above
df["categoryItemNumber"].fillna(method="ffill", inplace=True)

# Fill empty fields in 'MainCategoryNumber' with the value above
df["MainCategoryNumber"].fillna(method="ffill", inplace=True)

# Save the updated DataFrame to a CSV file
df.to_csv("Updated_Figshare_categories.csv", index=False)

# Define the category search type
category_search = "main_category"
#category_search = 'sub_category'

#####################
# Match with the main category number
if category_search == "main_category":
    category_to_find = "3704"
    # Filter the DataFrame to find the rows that match the main category
    filtered_df = df[df["MainCategoryNumber"].astype(str) == category_to_find]

# Match with the subcategory number
if category_search == "sub_category":
    category_to_find = "300101"
    # Filter the DataFrame to find the rows that match the subcategory
    filtered_df = df[df["categoryItemNumber"] == category_to_find]

#####################
# Print the filtered DataFrame
print(filtered_df)

# Save the filtered DataFrame to a CSV file for cross-checking
filtered_df.to_csv(
    "Filtered_Figshare_categories_" + str(datetime.datetime.now().strftime("%Y-%m-%d")) + ".csv",
    index=False,
    encoding="utf-8"
)

# If you need to use the filtered DataFrame for further processing
categories = filtered_df["SubCategoryName"].tolist()

# Remove NaN values from the 'categories' list
categories = [category for category in categories if pd.notna(category)]


# Save the categories list to a CSV file for cross-checking
with open(
    "Selected_Categories_" + str(datetime.datetime.now().strftime("%Y-%m-%d")) + ".csv",
    "w",
    encoding="utf-8"
) as f:
    f.write("SubCategoryName\n")  # Add a header
    f.writelines([category + "\n" for category in categories])
print('********************',categories,'*********************')
#quit()
#categories=['Computational modelling and simulation in earth sciences', 'Earth and space science informatics', 'Geoscience data visualisation', 'Geoinformatics not elsewhere classified']
#categories=['Computational modelling and simulation in earth sciences', 'Earth and space science informatics', 'Geoscience data visualisation', 'Geoinformatics not elsewhere classified']
#####################
item_ids_full, item_ids = itemids_for_categories(categories)

# Pick 100 random items from item_ids_full
random_item_ids = random.sample(item_ids_full, min(100, len(item_ids_full)))

#print(f"Randomly selected 100 item IDs: {random_item_ids}")
#item_metadata, error_list, categories_metadata = figshare_categorystatistics(
 ##   random_item_ids
#)
#print(f"Randomly selected 100 item IDs: {random_item_ids}")
item_metadata, error_list, categories_metadata = figshare_categorystatistics(item_ids_full)

keys_to_keep = [
    "figshare_url",
    "citation",
    "categories",
    "id",
    "doi",
    "handle",
    "url",
    "published_date",
    "defined_type_name",
]  # Add more keys if needed
descriptor = "figshare-statistics-category"
jsonfilename = (
    descriptor
    + "-full_records-"
    + str(datetime.datetime.now().strftime("%Y-%m-%d"))
    + ".json"
)

# Convert JSON file to CSV file: all metadata
with open(jsonfilename, encoding="utf-8") as inputfile:
    df = pd.read_json(inputfile)

# Save all metadata to a CSV file
df.to_csv(
    "allMetadataInFigshare_report_datasets"
    + str(datetime.datetime.now().strftime("%Y-%m-%d"))
    + ".csv",
    encoding="utf-8",
    index=False,
)

# Save limited metadata to a CSV file with selected columns
df.to_csv(
    "LimitedMetadataInFigshare_report_datasets"
    + str(datetime.datetime.now().strftime("%Y-%m-%d"))
    + ".csv",
    columns=keys_to_keep,
    index=False,
)

# Gather Figshare statistics for each item ID and write it to a CSV file
fetch_figshare_statistics(
    "LimitedMetadataInFigshare_report_datasets"
    + str(datetime.datetime.now().strftime("%Y-%m-%d"))
    + ".csv"
)