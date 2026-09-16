"""
Check whether the off-by-one date-filter bug affected the SEPTEMBER 2025 harvest.

The bug: :posted_before: is EXCLUSIVE, so each weekly batch (batch_start, batch_end)
silently drops batch_end itself. If the September harvest used this batching, then
the LAST day of every week (Jan 7, Jan 14, Jan 21, ...) would be missing entirely
from the harvested pool.

This script looks at the actual September pool file and checks whether those
batch-boundary days are empty. It reads a local file only - no API calls.
"""
import json
import datetime
from collections import Counter
import statistics

POOL_FILE = "figshare_public_items_2025-09-16.json"

# --- load the September pool and dedupe by id ------------------------------
data = json.load(open(POOL_FILE))
seen = set()
unique = []
for x in data:
    i = x.get("id")
    if i not in seen:
        seen.add(i)
        unique.append(x)
print(f"September pool: {len(data)} rows, {len(unique)} unique items")

def pub_date(x):
    s = x.get("published_date") or ""
    return s[:10]

date_counts = Counter(pub_date(x) for x in unique if pub_date(x))
all_days = sorted(date_counts)
print(f"published-date range in pool: {all_days[0]} to {all_days[-1]}")

# --- reconstruct the weekly batch boundaries the code would have used ------
start = datetime.date(2022, 1, 1)
end = datetime.date(2022, 12, 31)
batch_end_days = set()      # the last day of each weekly batch (dropped if bug present)
cur = start
while cur < end:
    be = min(cur + datetime.timedelta(days=6), end)
    batch_end_days.add(be.isoformat())
    cur = be + datetime.timedelta(days=1)

# --- how many items sit on batch-boundary days vs normal days -------------
boundary = [(d, date_counts.get(d, 0)) for d in sorted(batch_end_days)]
boundary_vals = [c for _, c in boundary]
normal_vals = [c for d, c in date_counts.items() if d not in batch_end_days]

print()
print("=== batch-boundary days (would be EMPTY if the bug was active) ===")
print(f"number of batch-boundary days checked: {len(boundary)}")
print(f"  ...of which have ZERO items: {sum(1 for c in boundary_vals if c == 0)}")
print(f"  avg items on boundary days : {statistics.mean(boundary_vals):.1f}")
print(f"  avg items on normal days   : {statistics.mean(normal_vals):.1f}")
print()
print("first 12 boundary days and their item counts:")
for d, c in boundary[:12]:
    flag = "  <-- EMPTY" if c == 0 else ""
    print(f"    {d}: {c} items{flag}")

# --- overall: which calendar days in 2022 are completely empty? ------------
all_2022 = []
cur = start
while cur <= end:
    all_2022.append(cur.isoformat())
    cur += datetime.timedelta(days=1)
zero_days = [d for d in all_2022 if date_counts.get(d, 0) == 0]
zero_on_boundary = [d for d in zero_days if d in batch_end_days]
print()
print("=== overall empty-day pattern ===")
print(f"total calendar days in 2022 with ZERO items: {len(zero_days)}")
print(f"  ...of those, how many are batch-boundary days: {zero_on_boundary and len(zero_on_boundary) or 0}")
if zero_days:
    print(f"  first 15 empty days: {zero_days[:15]}")

print()
print("=== verdict ===")
frac_boundary_empty = sum(1 for c in boundary_vals if c == 0) / len(boundary_vals)
if frac_boundary_empty > 0.5:
    print("The batch-boundary days are mostly EMPTY -> the off-by-one bug WAS active in September.")
else:
    print("The batch-boundary days are populated normally -> the off-by-one bug did NOT affect September.")
