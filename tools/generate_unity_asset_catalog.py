import os
import sys
import json

ROOT = r"C:\Users\casey\Desktop\Homesteader"
ASSETS_DIR = os.path.join(ROOT, "assets")
OUTPUT_PATH = os.path.join(ROOT, "Homesteader", "Assets", "Resources", "AssetCatalog.json")

EXCLUDED_CATEGORIES = {"ground", "hud", "hud_kit", "peds", "models_legacy", "textures", "biomes"}

def main():
    print("Indexing asset catalog from:", ASSETS_DIR)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    categories = sorted([
        d for d in os.listdir(ASSETS_DIR)
        if os.path.isdir(os.path.join(ASSETS_DIR, d))
        and not d.startswith("_")
        and d not in EXCLUDED_CATEGORIES
    ])

    all_items = []
    cat_counts = {}

    for cat in categories:
        cat_dir = os.path.join(ASSETS_DIR, cat)
        items = sorted([
            d for d in os.listdir(cat_dir)
            if os.path.isdir(os.path.join(cat_dir, d))
            and not d.startswith("_")
        ])
        cat_counts[cat] = 0

        for item_folder in items:
            manifest_path = os.path.join(cat_dir, item_folder, f"{item_folder}.json")
            if not os.path.exists(manifest_path):
                # Fallback manifest if named item.json
                for fn in os.listdir(os.path.join(cat_dir, item_folder)):
                    if fn.endswith(".json") and not fn.startswith("_"):
                        manifest_path = os.path.join(cat_dir, item_folder, fn)
                        break

            item_data = {
                "id": item_folder,
                "name": item_folder.replace("_", " ").title(),
                "category": cat,
                "description": "",
                "icon": f"{item_folder}.png",
                "max_stack": 64
            }

            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        m = json.load(f)
                    item_data["id"] = m.get("id", item_folder)
                    item_data["name"] = m.get("name", item_folder.replace("_", " ").title())
                    item_data["category"] = m.get("category", cat)
                    item_data["description"] = m.get("description", "")
                    item_data["icon"] = m.get("icon", f"{item_folder}.png")
                    props = m.get("properties", {})
                    if props and isinstance(props, dict):
                        ms = props.get("max_stack_size")
                        if ms and isinstance(ms, int) and ms > 0:
                            item_data["max_stack"] = ms
                except Exception as ex:
                    print(f"Warning reading {manifest_path}: {ex}")

            all_items.append(item_data)
            cat_counts[cat] += 1

    catalog_dict = {
        "items": all_items
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog_dict, f, indent=2)

    print(f"Successfully generated {OUTPUT_PATH}")
    print(f"Total items: {len(all_items)} across {len(categories)} categories:")
    for c, cnt in cat_counts.items():
        print(f"  {c}: {cnt}")

if __name__ == "__main__":
    main()

