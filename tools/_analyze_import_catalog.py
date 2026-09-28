import os
import json

root = r"C:\Users\casey\Desktop\Homesteader"
assets_dir = os.path.join(root, "assets")

excluded_cats = {"ground", "hud", "hud_kit", "peds"}

# List categories
categories = [d for d in os.listdir(assets_dir) 
              if os.path.isdir(os.path.join(assets_dir, d)) 
              and not d.startswith("_") 
              and d not in excluded_cats
              and d != "models_legacy"
              and d != "textures"]

print("Categories to import:", categories)

total_items = 0
group_items = 0
regular_items = 0

category_breakdown = {}

for cat in sorted(categories):
    cat_dir = os.path.join(assets_dir, cat)
    items = [d for d in os.listdir(cat_dir) if os.path.isdir(os.path.join(cat_dir, d))]
    cat_regs = []
    cat_groups = []
    for item in items:
        item_dir = os.path.join(cat_dir, item)
        manifest_file = os.path.join(item_dir, f"{item}.json")
        is_group = False
        if os.path.exists(manifest_file):
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "stages" in data or "growth_group" in data or data.get("type") == "growth_group" or data.get("type") == "structure_group":
                        is_group = True
            except Exception:
                pass
        if os.path.exists(os.path.join(item_dir, "stages")):
            is_group = True

        if is_group:
            cat_groups.append(item)
        else:
            cat_regs.append(item)

    category_breakdown[cat] = {
        "regular": len(cat_regs),
        "groups": len(cat_groups),
        "items": cat_regs
    }
    regular_items += len(cat_regs)
    group_items += len(cat_groups)

print(f"\nTotal Regular Items to import: {regular_items}")
print(f"Skipped Group Items: {group_items}")
for cat, info in category_breakdown.items():
    print(f"  {cat}: {info['regular']} items (skipped {info['groups']} groups)")
