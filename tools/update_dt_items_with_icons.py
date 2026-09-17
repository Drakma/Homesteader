import os
import csv

CSV_PATH = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\Data\DT_Items.csv"
OUT_CSV_PATH = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\Data\DT_Items_With_Icons.csv"
ICONS_DIR = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\UI\Icons"

if os.path.exists(CSV_PATH):
    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        if "Icon" not in fieldnames:
            fieldnames.append("Icon")
            
        rows = []
        for r in reader:
            item_id = r.get("ItemID", "").strip()
            if item_id:
                # Unreal Engine SoftObjectPath format
                r["Icon"] = f"/Game/Homesteader/UI/Icons/{item_id}.{item_id}"
            rows.append(r)
            
    with open(OUT_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"Generated {OUT_CSV_PATH} with {len(rows)} items linked to their icon assets!")
else:
    print(f"CSV not found at {CSV_PATH}")

