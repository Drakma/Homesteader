import os, csv, hashlib
from collections import defaultdict

ITEMS_CSV = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\Data\DT_Items.csv"
HUD_ITEMS = r"C:\Users\casey\Desktop\Homesteader\HUD\assets\items"

with open(ITEMS_CSV, "r", encoding="utf-8-sig") as f:
    items = list(csv.DictReader(f))

hash_to_rows = defaultdict(list)
for idx, r in enumerate(items):
    item_id = r["ItemID"].strip()
    icon_path = os.path.join(HUD_ITEMS, f"{item_id}.png")
    if os.path.exists(icon_path):
        with open(icon_path, "rb") as fp:
            h = hashlib.sha256(fp.read()).hexdigest()
        hash_to_rows[h].append((idx+2, item_id, r["DisplayName"], r["Category"]))

print(f"=== Items in DT_Items.csv sharing the EXACT SAME icon file ===")
for h, rows in hash_to_rows.items():
    if len(rows) > 1:
        # check if it's just the exact duplicate mat_pile rows or something else
        ids = [r[1] for r in rows]
        unique_ids = set(ids)
        if len(unique_ids) > 1:
            print(f"\nDifferent ItemIDs sharing identical icon:")
            for r in rows:
                print(f"  Line {r[0]:3d}: {r[1]:<30} | {r[2]:<25} | {r[3]}")
        else:
            print(f"Duplicate row for {ids[0]} on lines {[r[0] for r in rows]}")

