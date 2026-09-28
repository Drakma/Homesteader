import os
import json

root = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Mods"

# Sample 1 item manifest from each category to see exact JSON keys
sample_cats = ["fuel", "logging", "materials", "building", "tools", "ranching", "food", "ingredients", "vehicles", "structures", "appliances"]

for cat in sample_cats:
    mod_cat_dir = os.path.join(root, f"mod_{cat}", "assets", cat)
    if os.path.exists(mod_cat_dir):
        items = [d for d in os.listdir(mod_cat_dir) if os.path.isdir(os.path.join(mod_cat_dir, d))]
        if items:
            sample_item = items[0]
            mf = os.path.join(mod_cat_dir, sample_item, f"{sample_item}.json")
            if os.path.exists(mf):
                with open(mf, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    print(f"\n--- [{cat}] {sample_item} ---")
                    print(json.dumps(d, indent=2))
