import csv
from collections import defaultdict

ITEMS_CSV = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\Data\DT_Items.csv"
with open(ITEMS_CSV, "r", encoding="utf-8-sig") as f:
    items = list(csv.DictReader(f))

by_cat = defaultdict(list)
for r in items:
    by_cat[r["Category"]].append(r)

print("=== DT_Items.csv Category Breakdown ===")
for cat, rows in sorted(by_cat.items()):
    print(f"\nCategory: {cat} ({len(rows)} items)")
    for r in rows:
        print(f"  {r['ItemID']:<32} | {r['DisplayName']:<30} | Stack:{r['MaxStackSize']:<3} | Val:{r['BaseValue']}")

