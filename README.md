[[_TOC_]]

# Project Info
These codes help get figshare statistics for specified categories. They were gathered from [retrieving item ids through a search query](https://help.figshare.com/article/how-to-use-the-figshare-api) and codes provided by Jonathan Petters on gathering statistics. 

# About the scripts

- The first function `itemids_for_categories()` generates item ids associated with the given categories. 
- The second function `figshare_categorystatistics(itemList)` takes an item list and creates a JSON file for all the metadata associated with the item ids. 
- The third function `fetch_figshare_statistics(file_path)` gathers figshare statistics for the provided CSV file.
- The new script `FigStats-iType-dRange.py`:
  - Processes Figshare statistics for datasets within specific date ranges.
  - Generates 5-day intervals for a given year and retrieves metadata and statistics for items posted within those intervals.
  - Saves results as JSON and CSV files, including detailed views and downloads statistics.

# How to run the categories codes

- Go to [category numbers matching with category names figshare dataset](https://figshare.com/articles/dataset/Fields_of_Research_FoR_Classification/10305443/1?file=35317927) and download the Figshare categories as a csv file, name it Figshare_categories.csv
- Open figshare_statistics.py and change the file path of the Figshare categories csv file in 'file_path'
- Enter the category_search='main_category' or category_search='sub_category' based on the Figshare_categories.csv file on line 25. 'main_category' corresponds to column 2, and 'sub_category' corresponds to column 3 category ids.
- Enter category_to_find = '3704' on line 31 for 'main_category' or line 36 for 'sub_category'
- Run figshare_statistics.py
- This will generate a csv file with views and downloads : views_and_downloads_figshare_[current_date]
- Two other csv files are also generated:
   1. LimitedMetadataInFigshare_report_datasets[current_date].csv: limited metadata for the items related to the category picked (by the code)
   2. allMetadataInFigshare_report_datasets[current_date].csv: all the metadata for the items related to the category picked (by the code)

# How to run the FigStats-iType-dRange code

### Running `FigStats-iType-dRange.py`
1. Open `FigStats-iType-dRange.py`.
2. Set the desired year and date ranges in the script. For testing, you can use a 2-day range by uncommenting the test range:
   ```python
   date_ranges = [
       ("2022-01-01", "2022-01-02")  # Replace with any desired 2-day range
   ]

# Links

- https://help.figshare.com/article/how-to-use-advanced-search-in-figshare
- https://colab.research.google.com/drive/1bCVsSjg5Y5WsHHsxTq_W1j1U3B4TyO2x#scrollTo=415f0c3e-d599-415d-944e-6fe1aaad18dc
- https://help.figshare.com/article/search-examples
- https://help.figshare.com/article/how-to-use-the-figshare-api#metadata-search
- https://help.figshare.com/article/how-to-use-the-figshare-api#search-ids

