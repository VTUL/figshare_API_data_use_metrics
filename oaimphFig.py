import json
import requests
import pandas as pd
import datetime
import xml.etree.ElementTree as ET
import xmltodict

# Helper function to also write to a log file
def log_to_file(*args, **kwargs):
    with open('harvest_log.txt', 'a', encoding='utf-8') as f:
        print(*args, **kwargs, file=f)

#Set the base URLs
BASE_URL = 'https://api.figshare.com/v2'
#Set up lists to collect information and reports
errorList = []
newRecords = []

#There are two functions here, one to start collecting and one to get any additional pages of results

def initialHarvest():
    global token # set a global variable to hold the token
    global portalSet # set a global variable that tells us when portals have been harvested
    portalSet = False

    oai_url = BASE_URL + '/oai?verb=ListSets'
    print('Retrieving OAI sets from:', oai_url)
    log_to_file('Retrieving OAI sets from:', oai_url)
    r = requests.get(oai_url)
    print('HTTP status code:', r.status_code)
    log_to_file('HTTP status code:', r.status_code)
    dict_data = xmltodict.parse(r.content)

    #If there is an error (i.e. there are no records), note that in the errorList
    if 'error' in dict_data['OAI-PMH']:
        desc = 'Some type of error occurred during initial harvest.'
        print(desc)
        log_to_file(desc)
        errorList.append(desc)
    else:
        # Set the resumption token if present
        if "resumptionToken" in dict_data['OAI-PMH']['ListSets']:
            token = dict_data['OAI-PMH']['ListSets']['resumptionToken']['#text']
            print('Resumption token found:', token)
            log_to_file('Resumption token found:', token)
        else:
            token = ""
            print('No resumption token found, harvesting will stop after this page.')
            log_to_file('No resumption token found, harvesting will stop after this page.')

        # Iterate through each set in the response
        recs = dict_data['OAI-PMH']['ListSets']['set'] # this is a list of sets
        print('Number of sets found in this page:', len(recs))
        log_to_file('Number of sets found in this page:', len(recs))
        for r in recs:
            # Only collect sets where 'portal' is in setSpec
            if 'portal' in r['setSpec']:
                portalSet = True
                newRecords.append(r)
                print('Collected portal set:', r['setSpec'])
                log_to_file('Collected portal set:', r['setSpec'])
            elif portalSet == True:  # If we've already collected portal sets and now see a non-portal, stop collecting
                print('Reached non-portal set after collecting portals, stopping.')
                log_to_file('Reached non-portal set after collecting portals, stopping.')
                token = ""

def additionalHarvest():
    global token
    global portalSet # set a global variable that tells us when portals have been harvested
    print('Requesting next page with resumptionToken:', token)
    log_to_file('Requesting next page with resumptionToken:', token)
    s = requests.get(BASE_URL + '/oai?verb=ListSets&resumptionToken=' + str(token))
    print('HTTP status code:', s.status_code)
    log_to_file('HTTP status code:', s.status_code)
    dict_data = xmltodict.parse(s.content)

    # Check for error in response
    if 'error' in dict_data['OAI-PMH']:
        desc = 'Some type of error occurred during additional harvest.'
        print(desc)
        log_to_file(desc)
        errorList.append(desc)
    else:
        # Set the resumption token if present
        if "resumptionToken" in dict_data['OAI-PMH']['ListSets']:
            token = dict_data['OAI-PMH']['ListSets']['resumptionToken']['#text']
            print('Resumption token found:', token)
            log_to_file('Resumption token found:', token)
        else:
            token = ""
            print('No resumption token found, harvesting will stop after this page.')
            log_to_file('No resumption token found, harvesting will stop after this page.')

        # Iterate through each set in the response
        recs = dict_data['OAI-PMH']['ListSets']['set'] # this is a list of sets
        print('Number of sets found in this page:', len(recs))
        log_to_file('Number of sets found in this page:', len(recs))
        for r in recs:
            if 'portal' in r['setSpec']:
                portalSet = True
                newRecords.append(r)
                print('Collected portal set:', r['setSpec'])
                log_to_file('Collected portal set:', r['setSpec'])
            elif portalSet == True:
                print('Reached non-portal set after collecting portals, stopping.')
                log_to_file('Reached non-portal set after collecting portals, stopping.')
                token = ""


#df.to_csv('institutionListOAI.csv', encoding='utf-8', index=False) # Save CSV locally
# ------------------------- The following collects the records -------------------

#Loop through the list of repository ids

# Set the token to zero (empty string)
token = ""

# Perform the initial harvest
initialHarvest()
print('Initial harvest complete. Current ResumptionToken:', token)
log_to_file('Initial harvest complete. Current ResumptionToken:', token)

# Check the resumption token. If exists, harvest until it is back to an empty string
while token != "":
    print('Continuing harvest with ResumptionToken:', token)
    log_to_file('Continuing harvest with ResumptionToken:', token)
    additionalHarvest()

print('Harvesting complete.')
log_to_file('Harvesting complete.')
print(len(newRecords), 'portal sets collected. There were', len(errorList), 'errors.')
log_to_file(len(newRecords), 'portal sets collected. There were', len(errorList), 'errors.')
print(len(newRecords),'sets collected.','There were',len(errorList),'errors.')
log_to_file(len(newRecords),'sets collected.','There were',len(errorList),'errors.')

#Get one item from each portal to try to match the inst ids

dataset = []

print('Collecting sample articles for each portal set...')
log_to_file('Collecting sample articles for each portal set...')
for i in newRecords:
    # Extract institution id from setSpec (format: 'portal_xxx')
    id = i['setSpec'].split('_')[1]
    print('Processing institution id:', id)
    log_to_file('Processing institution id:', id)
    # Build query for searching articles for this institution
    query = '{"institution":' + str(id) + ', "page_size":1}'
    y = json.loads(query) # Convert the string to a dictionary (JSON)
    r = requests.post(BASE_URL + "/articles/search", params=y)
    print('Search request status:', r.status_code)
    log_to_file('Search request status:', r.status_code)
    if r.status_code == 200:
        article = json.loads(r.text)
        if len(article) > 0:
            entry = {}
            entry['instution_id'] = id
            entry['url'] = article[0]['url_public_html']
            entry['name'] = i['setName']
            print('Found article for institution:', entry['url'])
            log_to_file('Found article for institution:', entry['url'])
            # Try to get view statistics for the article
            stats_url_1 = 'https://stats.figshare.com/' + str(article[0]['url_public_html'].split('//')[1].split('.')[0]) + '/total/views/article/' + str(article[0]['id'])
            entry['stats_url'] = stats_url_1  # Add stats_url_1 as the default stats URL
            r_stats = requests.get(stats_url_1)
            print('Stats request 1 URL:', stats_url_1, 'Status:', r_stats.status_code)
            log_to_file('Stats request 1 URL:', stats_url_1, 'Status:', r_stats.status_code)
            print('article ********', article[0])
            print('article public html ********', article[0]['url_public_html'])
            print('******inst abbr******', article[0]['url_public_html'].split('//')[1].split('.')[0])
            if r_stats.status_code == 200:
                testing = json.loads(r_stats.text)
                if testing['totals'] > 0:
                    entry['inst_abbrev'] = article[0]['url_public_html'].split('//')[1].split('.')[0]
                    print('article ********', article[0])
                    print('article public html ********', article[0]['url_public_html'])
                    print('******inst abbr******', article[0]['url_public_html'].split('//')[1].split('.')[0])
                    entry['Notes'] = 'Seems to work. View count is ' + str(testing['totals'])
                    print('View count found:', testing['totals'])
                    log_to_file('View count found:', testing['totals'])
                else:
                    # Try the second part of the URL if first part fails
                    stats_url_2 = 'https://stats.figshare.com/' + str(article[0]['url_public_html'].split('//')[1].split('.')[1]) + '/total/views/article/' + str(article[0]['id'])
                    entry['stats_url'] = stats_url_2  # Overwrite with second stats URL if used
                    r_stats2 = requests.get(stats_url_2)
                    print('article ********', article[0])
                    print('article public html ********', article[0]['url_public_html'])
                    print(article[0]['url_public_html'].split('//')[1].split('.')[1])
                    print('Stats request 2 URL:', stats_url_2, 'Status:', r_stats2.status_code)
                    log_to_file('Stats request 2 URL:', stats_url_2, 'Status:', r_stats2.status_code)
                    if r_stats2.status_code == 200:
                        testing2 = json.loads(r_stats2.text)
                        if testing2['totals'] > 0:
                            entry['inst_abbrev'] = article[0]['url_public_html'].split('//')[1].split('.')[1]
                            entry['Notes'] = 'Seems to work. View count is ' + str(testing2['totals'])
                            print('View count found (second try):', testing2['totals'])
                            log_to_file('View count found (second try):', testing2['totals'])
            else:
                entry['inst_abbrev'] = 'unknown'
                entry['Notes'] = 'Needs testing (stats request failed)'
                print('Stats request failed for institution:', id)
                log_to_file('Stats request failed for institution:', id)
            dataset.append(entry.copy())
        else:
            # No articles found for this institution
            entry = {}
            entry['instution_id'] = id
            entry['url'] = 'No items'
            entry['name'] = i['setName']
            entry['stats_url'] = ''  # No stats URL if no article
            print('No articles found for institution:', id)
            log_to_file('No articles found for institution:', id)
            dataset.append(entry.copy())
    else:
        print('Search request failed for institution:', id)
        log_to_file('Search request failed for institution:', id)
        continue

print('All done collecting articles and stats.')
log_to_file('All done collecting articles and stats.')

# Convert dataset to DataFrame
df = pd.DataFrame(dataset)
print('Preview of collected data:')
log_to_file('Preview of collected data:')
print(df.head())
log_to_file(df.head())

# Save DataFrame to CSV locally
df.to_csv('institutionListOAI.csv', encoding='utf-8', index=False)
print('CSV file "institutionListOAI.csv" has been saved in the current directory.')
log_to_file('CSV file "institutionListOAI.csv" has been saved in the current directory.')