import os, csv
from collections import defaultdict

ITEMS_CSV = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\Data\DT_Items.csv"
with open(ITEMS_CSV, "r", encoding="utf-8-sig") as f:
    items = list(csv.DictReader(f))

print(f"Total items in DT_Items.csv: {len(items)}")

# 1. Exact ItemID duplicates
id_to_rows = defaultdict(list)
for idx, r in enumerate(items):
    id_to_rows[r["ItemID"].strip()].append((idx, r))

exact_dups = {k: v for k, v in id_to_rows.items() if len(v) > 1}
print(f"\n--- 1. EXACT DUPLICATE ITEM IDs ({len(exact_dups)}) ---")
for k, v in exact_dups.items():
    print(f"  {k}: lines {[idx+2 for idx, _ in v]}")

# 2. Duplicate DisplayNames
name_to_rows = defaultdict(list)
for idx, r in enumerate(items):
    name_to_rows[r["DisplayName"].strip().lower()].append((idx, r))

name_dups = {k: v for k, v in name_to_rows.items() if len(v) > 1}
print(f"\n--- 2. DUPLICATE DISPLAY NAMES ({len(name_dups)}) ---")
for k, v in name_dups.items():
    print(f"  '{k}': {[r['ItemID'] for _, r in v]} (lines {[idx+2 for idx, _ in v]})")

# 3. Check for similar/redundant items (e.g. tool_axe vs axe, crop_corn vs corn, etc.)
print("\n--- 3. ALL ROWS IN DT_Items.csv ---")
for idx, r in enumerate(items):
    print(f"{idx+2:3d} | {r['ItemID']:<32} | {r['DisplayName']:<28} | {r['Category']:<14} | {r['Description']}")

