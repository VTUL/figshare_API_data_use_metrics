"""
De-duplicate the September 2025 harvested-items-with-stats file by article id.

The Figshare search API returned some public records more than once within a
single response, so the harvested dataset contains exact-duplicate rows (same
article id, byte-for-byte identical). This script removes those duplicates,
keeping the first occurrence of each id, and writes a new clean file. The
original file is left untouched.
"""
import pandas as pd

# --- the file the paper's analysis is based on -----------------------------
INPUT_FILE = "harvested_items_2025-09-16_09-32-27_fullmeta_with_stats_2025-09-16_11-18-48.csv"
OUTPUT_FILE = "harvested_items_2025-09-16_deduplicated.csv"

# 1. Read the original file
df = pd.read_csv(INPUT_FILE, low_memory=False)
print(f"Original file: {INPUT_FILE}")
print(f"  rows: {len(df)}, columns: {df.shape[1]}")

# 2. Report the duplicates BEFORE removing them
dup_rows = df.duplicated(subset="id", keep=False).sum()   # every row that is part of a duplicate group
dup_ids = df[df.duplicated(subset="id", keep=False)]["id"].nunique()  # how many distinct ids are duplicated
print(f"  duplicate rows (by id): {dup_rows}  (covering {dup_ids} distinct article ids)")

# 3. Remove duplicates, keeping the first occurrence of each id
df_clean = df.drop_duplicates(subset="id", keep="first").reset_index(drop=True)

# 4. Report the result and a breakdown by group (institution vs public)
removed = len(df) - len(df_clean)
print(f"\nAfter de-duplication:")
print(f"  rows: {len(df_clean)}  (removed {removed} duplicate rows)")
print(f"  duplicate rows remaining (should be 0): {df_clean.duplicated(subset='id').sum()}")

if "harvested_institution_id" in df_clean.columns:
    institution_rows = df_clean["harvested_institution_id"].notna().sum()
    public_rows = df_clean["harvested_institution_id"].isna().sum()
    print(f"  institution items: {institution_rows}")
    print(f"  public (control) items: {public_rows}")

# 5. Save the clean file (original is not modified)
df_clean.to_csv(OUTPUT_FILE, index=False)
print(f"\nSaved clean file to: {OUTPUT_FILE}")
