"""
Compare September views/downloads: corrected re-harvest vs the paper's September
slice. Answers: (1) do public Friday items have lower engagement (direct test),
and (2) does correcting the off-by-one change the institution-vs-public gap.
Reads local files only - no API calls.
"""
import pandas as pd
import datetime

NEW = "harvested_items_2026-07-28_14-19-19_fullmeta_with_stats_2026-07-29_07-05-31.csv"
OLD = "harvested_items_2025-09-16_deduplicated.csv"   # the paper's data (deduplicated)

def prep(path, sept_only):
    df = pd.read_csv(path, low_memory=False)
    for c in ["views", "downloads"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["pub_dt"] = pd.to_datetime(df["published_date"].astype(str).str[:10], errors="coerce")
    if sept_only:
        df = df[df["pub_dt"].dt.strftime("%Y-%m") == "2022-09"]
    df["is_inst"] = df["harvested_institution_id"].notna()
    df["weekday"] = df["pub_dt"].dt.day_name()
    return df

new = prep(NEW, sept_only=False)   # already September-only
old = prep(OLD, sept_only=True)    # filter the full-year paper file to September

def summ(df, label):
    inst = df[df["is_inst"]]
    pub = df[~df["is_inst"]]
    print(f"\n=== {label} ===")
    for name, g in [("institution", inst), ("public", pub)]:
        v, d = g["views"].dropna(), g["downloads"].dropna()
        print(f"  {name:11s} n={len(g):4d} | views  mean={v.mean():8.1f} median={v.median():7.1f}"
              f" | downloads mean={d.mean():8.1f} median={d.median():7.1f}")

summ(old, "PAPER September (Fridays missing)")
summ(new, "CORRECTED September (Fridays included)")

# Direct Friday test on the corrected PUBLIC sample
pub_new = new[~new["is_inst"]]
fri = pub_new[pub_new["weekday"] == "Friday"]
non = pub_new[pub_new["weekday"] != "Friday"]
print("\n=== DIRECT test: corrected PUBLIC items, Friday vs non-Friday ===")
for name, g in [("Friday", fri), ("non-Friday", non)]:
    v, d = g["views"].dropna(), g["downloads"].dropna()
    if len(v):
        print(f"  {name:11s} n={len(g):4d} | views  mean={v.mean():8.1f} median={v.median():7.1f}"
              f" | downloads mean={d.mean():8.1f} median={d.median():7.1f}")

# The institution-vs-public gap, both datasets (using medians - robust to outliers)
def gap(df):
    im = df[df["is_inst"]]["views"].median()
    pm = df[~df["is_inst"]]["views"].median()
    idl = df[df["is_inst"]]["downloads"].median()
    pdl = df[~df["is_inst"]]["downloads"].median()
    return im, pm, idl, pdl

print("\n=== institution-vs-public GAP (median) ===")
for label, df in [("PAPER", old), ("CORRECTED", new)]:
    im, pm, idl, pdl = gap(df)
    print(f"  {label:10s} views: inst {im:.0f} vs public {pm:.0f}  (ratio {im/pm:.2f}x) |"
          f" downloads: inst {idl:.0f} vs public {pdl:.0f}  (ratio {idl/pdl:.2f}x)")
