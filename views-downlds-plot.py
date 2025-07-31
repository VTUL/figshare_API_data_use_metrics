import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV file
file_path = "c:/Users/padma/anaconda3/envs/figshare_statistics/figshare_statistics_categories/views_and_downloads_figshare_2025-04-27.csv"
df = pd.read_csv(
    file_path,
    dtype={
        "institute": str,
        "inst_views": float,
        "inst_downloads": float,
        "published_date": str,
    }
)

# Ensure the CSV contains the required columns
if "institute" not in df.columns or "inst_views" not in df.columns or "inst_downloads" not in df.columns or "published_date" not in df.columns:
    raise ValueError("The CSV file must contain 'institute', 'inst_views', 'inst_downloads', and 'published_date' columns.")

# Convert the published_date column to datetime
df["published_date"] = pd.to_datetime(df["published_date"], errors="coerce")

# Filter for the year 2022
df_2022 = df[(df["published_date"] >= "2022-01-01") & (df["published_date"] <= "2022-12-31")]

# Group by institute and sum inst_views and inst_downloads
grouped_df = df_2022.groupby("institute")[["inst_views", "inst_downloads"]].sum().reset_index()

# Plot the data
plt.figure(figsize=(12, 6))
bar_width = 0.4
x = range(len(grouped_df["institute"]))

# Create bars for inst_views and inst_downloads
plt.bar(x, grouped_df["inst_views"], width=bar_width, label="Views", color="skyblue")
plt.bar([i + bar_width for i in x], grouped_df["inst_downloads"], width=bar_width, label="Downloads", color="orange")

# Add labels and title
plt.xlabel("Institute", fontsize=12)
plt.ylabel("Count (Log Scale)", fontsize=12)
plt.title("Views and Downloads by Institute (2022)", fontsize=14)
plt.xticks([i + bar_width / 2 for i in x], grouped_df["institute"], rotation=45, ha="right")
plt.yscale("log")  # Set y-axis to logarithmic scale
plt.legend()

# Save the plot
output_file = "figStats-institutes-vs-year.png"
plt.tight_layout()
#
# Created on Sun Apr 27 2025
#
# Copyright (c) 2025 Your Company
#
plt.savefig(output_file, dpi=300)
print(f"Plot saved as {output_file}")

# Show the plot
plt.show()