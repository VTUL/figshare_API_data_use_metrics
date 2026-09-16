"""
Does the day-of-week an item was posted affect its views/downloads?

The September public pool is missing every FRIDAY (the off-by-one bug). Whether
that biases the analysis depends on whether Friday-posted datasets differ from
others in views/downloads. The public sample has no Fridays to test, but the
INSTITUTION group was NOT weekly-batched, so it still contains all weekdays -
we use it as the test population.

If Friday-posted institution items look like the rest, that is evidence the
missing public Fridays do not bias the views/downloads comparison.

Reads the deduplicated September file only - no API calls.
"""
import pandas as pd

FILE = "harvested_items_2025-09-16_deduplicated.csv"
df = pd.read_csv(FILE, low_memory=False)

# institution items only (these include all weekdays, incl. Fridays)
inst = df[df["harvested_institution_id"].notna()].copy()

# parse the published date and get the weekday name
inst["pub_dt"] = pd.to_datetime(inst["published_date"].astype(str).str[:10], errors="coerce")
inst = inst[inst["pub_dt"].notna()].copy()
inst["weekday"] = inst["pub_dt"].dt.day_name()
inst["is_friday"] = inst["weekday"] == "Friday"

# make views/downloads numeric (blanks / 'None' -> NaN)
for c in ["views", "downloads"]:
    inst[c] = pd.to_numeric(inst[c], errors="coerce")

print(f"institution items with a valid published date: {len(inst)}")
print("\nitems by weekday posted:")
print(inst["weekday"].value_counts().to_string())

fri = inst[inst["is_friday"]]
non = inst[~inst["is_friday"]]
print(f"\nFriday-posted: {len(fri)}    non-Friday: {len(non)}")

print("\n=== views / downloads: Friday vs non-Friday ===")
for c in ["views", "downloads"]:
    print(f"\n{c}:")
    print(f"  Friday      mean={fri[c].mean():8.1f}  median={fri[c].median():7.1f}")
    print(f"  non-Friday  mean={non[c].mean():8.1f}  median={non[c].median():7.1f}")

# non-parametric test (data is very skewed, so compare distributions, not means)
try:
    from scipy.stats import mannwhitneyu
    print("\n=== statistical test (Mann-Whitney U, two-sided) ===")
    for c in ["views", "downloads"]:
        a = fri[c].dropna()
        b = non[c].dropna()
        if len(a) > 0 and len(b) > 0:
            u, p = mannwhitneyu(a, b, alternative="two-sided")
            verdict = "SIGNIFICANT difference (p<0.05)" if p < 0.05 else "no significant difference"
            print(f"  {c:10s}: p = {p:.3f}  ->  {verdict}")
except ImportError:
    print("\n(scipy not available - relying on the mean/median comparison above)")
