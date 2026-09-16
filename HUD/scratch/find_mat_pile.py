import csv

ITEMS_CSV = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\Data\DT_Items.csv"
with open(ITEMS_CSV, "r", encoding="utf-8-sig") as f:
    items = list(csv.DictReader(f))

for idx, r in enumerate(items):
    if "mat_pile_" in r["ItemID"]:
        print(f"Line {idx+2}: {r['ItemID']} | {r['DisplayName']}")

