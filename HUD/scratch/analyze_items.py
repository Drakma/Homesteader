import os, sys, glob, csv
from PIL import Image
from collections import Counter, defaultdict

HUD_DIR = r"C:\Users\casey\Desktop\Homesteader\HUD"
UE5_DIR = r"C:\Users\casey\Desktop\Homesteader\Homesteader"
ITEMS_CSV = os.path.join(UE5_DIR, "Content", "Homesteader", "Data", "DT_Items.csv")
ITEMS_WITH_ICONS_CSV = os.path.join(UE5_DIR, "Content", "Homesteader", "Data", "DT_Items_With_Icons.csv")

sys.path.insert(0, os.path.join(HUD_DIR, "scripts"))
import item_catalog_data
import item_catalog_data_batch2
import item_catalog_data_batch34
import item_catalog_data_batch5

# 1. Inspect Python Catalogs
cat_items = {}
cat_items.update(item_catalog_data.CATALOG)
cat_items.update(item_catalog_data_batch2.CATALOG)
cat_items.update(item_catalog_data_batch34.CATALOG)
cat_items.update(item_catalog_data_batch5.CATALOG)

print(f"Total items across Python catalogs: {len(cat_items)}")

# 2. Inspect CSVs
with open(ITEMS_CSV, "r", encoding="utf-8-sig") as f:
    csv_rows = list(csv.DictReader(f))

print(f"Total rows in DT_Items.csv: {len(csv_rows)}")
csv_ids = [r["ItemID"].strip() for r in csv_rows]
id_counter = Counter(csv_ids)
exact_dup_csv_ids = {k: v for k, v in id_counter.items() if v > 1}
print(f"Exact duplicate IDs in DT_Items.csv: {len(exact_dup_csv_ids)}")
for k, v in exact_dup_csv_ids.items():
    print(f"  {k}: {v} times")

# 3. Check icon files in HUD/assets/items
hud_items_dir = os.path.join(HUD_DIR, "assets", "items")
hud_icon_files = [f for f in os.listdir(hud_items_dir) if f.endswith(".png")]
print(f"Total icon files in HUD/assets/items: {len(hud_icon_files)}")

# 4. Check style violations across all icons in HUD/assets/items
print("\nScanning HUD/assets/items for style/formatting issues...")
style_issues = defaultdict(list)

for f in sorted(hud_icon_files):
    p = os.path.join(hud_items_dir, f)
    item_name = os.path.splitext(f)[0]
    try:
        im = Image.open(p)
        w, h = im.size
        if (w, h) != (128, 128):
            style_issues["not_128x128"].append((item_name, f"{w}x{h}"))
        if im.mode != "RGBA":
            style_issues["not_rgba"].append((item_name, im.mode))
        
        # Check outer perimeter pixels (x=0, x=127, y=0, y=127)
        px = im.load()
        perimeter_bad = 0
        for x in range(w):
            if px[x, 0][3] > 0 or px[x, h - 1][3] > 0:
                perimeter_bad += 1
        for y in range(h):
            if px[0, y][3] > 0 or px[w - 1, y][3] > 0:
                perimeter_bad += 1
        if perimeter_bad > 0:
            style_issues["perimeter_not_transparent"].append((item_name, perimeter_bad))
            
        bbox = im.getbbox()
        if bbox is None:
            style_issues["empty_image"].append(item_name)
        else:
            bx0, by0, bx1, by1 = bbox
            bw, bh = bx1 - bx0, by1 - by0
            margin = min(bx0, by0, w - bx1, h - by1)
            if margin < 12:
                style_issues["margin_less_than_12px"].append((item_name, margin, f"{bw}x{bh}"))
            if bw > 104 or bh > 104:
                style_issues["bbox_exceeds_104px"].append((item_name, f"{bw}x{bh}"))
                
        # Check for 2D flat / icon_ prefix / border patterns
        if item_name.startswith("icon_"):
            style_issues["legacy_icon_prefix"].append(item_name)

    except Exception as e:
        style_issues["corrupt_error"].append((item_name, str(e)))

for issue_type, items in style_issues.items():
    print(f"Issue: {issue_type} -> {len(items)} items")
    for it in items[:15]:
        print(f"   {it}")
    if len(items) > 15:
        print(f"   ... and {len(items) - 15} more")

# 5. Check visual appearance for 2D flat/primitive icons
print("\nChecking for flat/vector icons vs 3D low poly...")

