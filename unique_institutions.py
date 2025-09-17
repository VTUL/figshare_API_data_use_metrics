import pandas as pd

# Read the CSV
df = pd.read_csv('unique_institutions.csv')

# Drop duplicate rows based on the first column
first_col = df.columns[0]
df_unique = df.drop_duplicates(subset=[first_col])

# Remove article id from the end of stats URLs
def remove_article_id(url):
    if isinstance(url, str) and url.rstrip('/').count('/') > 0:
        return url.rsplit('/', 1)[0]
    return url

df_unique['views_url'] = df_unique['views_url'].apply(remove_article_id)
df_unique['downloads_url'] = df_unique['downloads_url'].apply(remove_article_id)

# Save back to CSV
df_unique.to_csv('unique_institutions_unique.csv', index=False)

print("Saved unique institutions to unique_institutions_unique.csv")