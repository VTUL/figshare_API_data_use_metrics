"""
Compare the corrected September re-harvest against the September slice of the
original (paper) harvest, to show whether the off-by-one fix recovered the
missing Fridays. Reads local files only - no API calls.
"""
import json
import datetime
from collections import Counter

NEW_POOL = "figshare_public_items_2026-07-28.json"      # September-only re-harvest (fixed)
OLD_POOL = "figshare_public_items_2025-09-16.json"      # original full-year harvest (paper)

def load_unique(path):
    data = json.load(open(path))
    seen, uniq = set(), []
    for x in data:
        i = x.get("id")
        if i not in seen:
            seen.add(i)
            uniq.append(x)
    return uniq

def sept_2022(items):
    out = []
    for x in items:
        d = (x.get("published_date") or "")[:10]
        if d.startswith("2022-09"):
            out.append((x.get("id"), d))
    return out

def weekday_counts(rows):
    c = Counter()
    for _id, d in rows:
        wd = datetime.date.fromisoformat(d).strftime("%A")
        c[wd] += 1
    return c

new_sept = sept_2022(load_unique(NEW_POOL))
old_sept = sept_2022(load_unique(OLD_POOL))

print(f"CORRECTED re-harvest (Sept 2022 public): {len(new_sept)} unique items")
print(f"ORIGINAL paper harvest (Sept 2022 public): {len(old_sept)} unique items")
print()

order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
nw, ow = weekday_counts(new_sept), weekday_counts(old_sept)
print(f"{'weekday':10s} {'ORIGINAL (paper)':>18s} {'CORRECTED (re-run)':>20s}")
for wd in order:
    flag = "   <-- recovered" if (wd == "Friday" and ow.get(wd, 0) == 0 and nw.get(wd, 0) > 0) else ""
    print(f"{wd:10s} {ow.get(wd,0):>18d} {nw.get(wd,0):>20d}{flag}")

new_ids = {i for i, _ in new_sept}
old_ids = {i for i, _ in old_sept}
recovered = new_ids - old_ids
print()
print(f"items in the corrected re-run but NOT in the paper's September: {len(recovered)}")
fri_recovered = sum(1 for i, d in new_sept
                    if i in recovered and datetime.date.fromisoformat(d).strftime("%A") == "Friday")
print(f"  ...of which posted on a Friday: {fri_recovered}")
