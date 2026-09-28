import os
import json

ROOT = r"C:\Users\casey\Desktop\Homesteader"
MODS_DIR = os.path.join(ROOT, "assets")   # source of truth (same <category>/<asset folder> layout as mods/homesteader)
OUT_FILE = os.path.join(ROOT, "Homesteader", "Assets", "Resources", "StoreCatalogs.json")

# Mapping categories for the stores:
# 1. Board Meeting: logging
# 2. Nail It: materials, building, tools
# 3. Lettuce Shop: food, ingredients
# 4. Hay There: ranching
# 5. Tank You: fuel
# 6. Shift Happens: personal vehicles (cars, trucks, motorcycles)
# 7. Drafting Behind You: structures
# 8. Tractor Beam: farming equipment & tractors
# 9. Sofa So Good: appliances (furniture & home appliances)

personal_veh_types = {"car", "truck", "pickup", "van", "suv", "motorcycle", "bike", "wagon", "atv", "quad", "sedan"}

def load_cat_items(cat, flag="is_buyable"):
    """Items of one category whose manifest has properties[flag] == true.
    Stores stock is_buyable items (a vendor sells them TO the player); the Market's Sell tab lists is_sellable."""
    cat_dir = os.path.join(MODS_DIR, cat)
    if not os.path.exists(cat_dir):
        return []
    res = []
    for it in sorted(os.listdir(cat_dir)):
        it_dir = os.path.join(cat_dir, it)
        if not os.path.isdir(it_dir):
            continue
        mf = os.path.join(it_dir, f"{it}.json")
        if not os.path.exists(mf):
            continue
        try:
            with open(mf, "r", encoding="utf-8") as f:
                d = json.load(f)
            
            # Skip if group
            if "stages" in d or "growth_group" in d or d.get("type") in ("growth_group", "structure_group"):
                continue

            name = d.get("name", it.replace("_", " ").title())
            desc = d.get("description", "")
            props = d.get("properties", {})
            if props.get(flag) is not True:
                continue
            price = props.get("base_value", 10.0)
            if price <= 0:
                price = 15.0 # baseline nominal price
            
            # Unit estimation
            unit = "ea"
            if "seed" in it or "packet" in name.lower():
                unit = "packet"
            elif "box" in name.lower() or "case" in name.lower():
                unit = "box"
            elif "bale" in name.lower():
                unit = "bale"
            elif "gal" in name.lower() or "tank" in name.lower() or "cistern" in name.lower():
                unit = "tank"
            elif "can" in name.lower():
                unit = "can"
            elif "cord" in name.lower():
                unit = "cord"
            elif "vehicle" in cat or "tractor" in name.lower():
                unit = "unit"
            elif "building" in cat or "structure" in cat:
                unit = "kit"

            cat_fields = d.get("category_fields", {})
            v_type = cat_fields.get("vehicle_type", "").lower()

            res.append({
                "id": it,
                "name": name,
                "category": cat.title(),
                "price": round(float(price), 2),
                "unit": unit,
                "description": desc,
                "icon": d.get("icon", f"{it}.png"),
                "v_type": v_type
            })
        except Exception as e:
            pass
    return res

# Compile catalogs
catalogs = {}

# 1. Board Meeting (Logging)
catalogs["lumber"] = load_cat_items("logging")

# 2. Nail It (Materials, Building, Tools)
nail_it_items = []
for c in ["building", "materials", "tools"]:
    nail_it_items.extend(load_cat_items(c))
catalogs["depot"] = nail_it_items

# 3. Lettuce Shop (Food, Ingredients)
lettuce_items = []
for c in ["food", "ingredients"]:
    lettuce_items.extend(load_cat_items(c))
catalogs["grocer"] = lettuce_items

# 4. Hay There (Ranching & Farming: seeds, manure, fertilizer, forage, feed)
hay_there_items = []
hay_there_items.extend(load_cat_items("ranching"))
hay_there_items.extend(load_cat_items("farming"))
catalogs["feed"] = hay_there_items

# 5. Tank You (Fuel)
catalogs["water"] = load_cat_items("fuel") # "water" was the tile name for Tank You

# 6 & 7. Vehicles split: Shift Happens vs Tractor Beam
all_veh = load_cat_items("vehicles")
personal_veh = []
farm_veh = []

for v in all_veh:
    vt = v.get("v_type", "")
    vid = v["id"].lower()
    vname = v["name"].lower()
    if any(k in vid or k in vname or k in vt for k in ["car", "truck", "pickup", "van", "suv", "motorcycle", "bike", "wagon", "atv", "quad", "sedan"]):
        personal_veh.append(v)
    else:
        farm_veh.append(v)

# If personal or farm has few, ensure good items in both
catalogs["vehicles"] = personal_veh if personal_veh else all_veh[:10]
catalogs["equipment"] = farm_veh if farm_veh else all_veh[10:]

# 8. Drafting Behind You (Structures)
catalogs["livestock"] = load_cat_items("structures") # "livestock" was the tile name for Drafting Behind You

# 9. Sofa So Good (Appliances & Furniture)
catalogs["furniture"] = load_cat_items("appliances")

# Market > Sell Produce: everything the player can sell (is_sellable), across all categories
sellables = []
for c in sorted(os.listdir(MODS_DIR)):
    if os.path.isdir(os.path.join(MODS_DIR, c)) and not c.endswith(".disabled") and c != "gamerules":
        sellables.extend(load_cat_items(c, "is_sellable"))
catalogs["sellables"] = sellables

# Print summary
total = 0
for k, v in catalogs.items():
    print(f"Store [{k}]: {len(v)} real catalog items")
    total += len(v)

print(f"\nTotal real catalog items wired: {total}")

# Write StoreCatalogs.json
with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(catalogs, f, indent=2)

print(f"Wrote real catalog JSON to {OUT_FILE}")
