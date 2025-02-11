[[_TOC_]]

# Project Info
These codes help get figshare statistics for specified categories. They were gathered from [retrieving item ids through a search query](https://help.figshare.com/article/how-to-use-the-figshare-api) and codes provided by Jonathan Petters on gathering statistics. 

# About the scripts

- The first funciton itemids_for_categories() generates item ids associated with the given categories. 
- The second function figshare_categorystatistics(itemList) takes an item list and creates a json file for all the metadata associated with the item ids. 
- The third function fetch_fighsare_statistics(file_path) gathers figshare statistics for the provided csv file

# How to run the code

 -  Open figshare_statistics.py and pick the categories as a list, change the keys_to_keep if needed
 -  Run fetch_figshare_statistics_for_categories.py
 -  This will generate a csv file with views and downloads and keys to keep columns

