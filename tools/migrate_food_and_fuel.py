#!/usr/bin/env python3
"""
Migration script for Food and Fuel categories and Growable species tagging.
"""

import os
import shutil
import json

ASSETS_DIR = r"C:\Users\casey\Desktop\Homesteader\assets"
FOOD_DIR = os.path.join(ASSETS_DIR, "food")
FUEL_DIR = os.path.join(ASSETS_DIR, "fuel")

os.makedirs(FOOD_DIR, exist_ok=True)
os.makedirs(FUEL_DIR, exist_ok=True)

def update_manifest_and_files(src_dir, dst_dir, old_id, new_id, new_cat, new_name=None):
    if not os.path.exists(src_dir):
        print(f"Source not found: {src_dir}")
        return False
    
    if os.path.exists(dst_dir) and src_dir != dst_dir:
        # Avoid collisions
        counter = 2
        base_dst = dst_dir
        while os.path.exists(dst_dir):
            new_id = f"{new_id}_{counter}"
            dst_dir = f"{base_dst}_{counter}"
            counter += 1
            
    if src_dir != dst_dir:
        shutil.move(src_dir, dst_dir)
        
    # Rename files matching old_id.*
    renamed_files = {}
    if new_id != old_id:
        for f in list(os.listdir(dst_dir)):
            if f.startswith(f"{old_id}."):
                ext = f[len(old_id):]
                new_f = f"{new_id}{ext}"
                p_old = os.path.join(dst_dir, f)
                p_new = os.path.join(dst_dir, new_f)
                if os.path.exists(p_new) and p_old != p_new:
                    os.remove(p_new)
                os.rename(p_old, p_new)
                renamed_files[f] = new_f
                
    # Update manifest
    m_path = os.path.join(dst_dir, f"{new_id}.json")
    if not os.path.exists(m_path):
        m_path = os.path.join(dst_dir, f"{old_id}.json")
        
    if os.path.exists(m_path):
        try:
            with open(m_path, "r", encoding="utf-8") as jf:
                data = json.load(jf)
            data["id"] = new_id
            data["category"] = new_cat
            data["icon"] = f"{new_id}.png"
            if new_name:
                data["name"] = new_name
            elif "name" not in data:
                data["name"] = new_id.replace("_", " ").title()
                
            if "models" in data and isinstance(data["models"], list):
                for m in data["models"]:
                    if isinstance(m, dict) and m.get("file") in renamed_files:
                        m["file"] = renamed_files[m["file"]]
                        
            final_m_path = os.path.join(dst_dir, f"{new_id}.json")
            with open(final_m_path, "w", encoding="utf-8") as jf:
                json.dump(data, jf, indent=2)
            if final_m_path != m_path and os.path.exists(m_path):
                os.remove(m_path)
        except Exception as e:
            print(f"Error manifest {dst_dir}: {e}")
            
    # Update README
    r_path = os.path.join(dst_dir, "README.md")
    if os.path.exists(r_path):
        try:
            with open(r_path, "r", encoding="utf-8") as rf:
                txt = rf.read()
            txt = txt.replace(f"{old_id}.png", f"{new_id}.png")
            txt = txt.replace(f"{old_id}.json", f"{new_id}.json")
            txt = txt.replace(f"#{old_id}", f"#{new_id}")
            txt = txt.replace(f"`{old_id}`", f"`{new_id}`")
            with open(r_path, "w", encoding="utf-8") as rf:
                rf.write(txt)
        except Exception:
            pass
            
    return True

print("=== MIGRATING FOOD ITEMS ===")
FOOD_MOVES = [
    # (source_cat, old_id, new_id, new_name)
    ("farming", "food_apple", "food_apple", "Fresh Red Apple"),
    ("farming", "food_carrot", "food_carrot", "Fresh Garden Carrot"),
    ("farming", "food_cheese", "food_cheese", "Aged Farmhouse Cheese"),
    ("farming", "food_corn", "food_corn", "Sweet Yellow Corn"),
    ("farming", "food_potato", "food_potato", "Russet Potato"),
    ("farming", "food_pumpkin", "food_pumpkin", "Autumn Pumpkin"),
    ("farming", "food_strawberry", "food_strawberry", "Fresh Strawberry"),
    ("farming", "food_tomato", "food_tomato", "Vine Ripe Tomato"),
    ("farming", "ingredient_herbs", "ingredient_herbs", "Fresh Culinary Herbs"),
    ("farming", "ingredient_wheat", "ingredient_wheat", "Milled Wheat Grain"),
    ("ranching", "food_truffle", "food_truffle", "Black Foraged Truffle"),
    ("ranching", "ingredient_beef", "ingredient_beef", "Raw Beef Cut"),
    ("ranching", "ingredient_chicken", "ingredient_chicken", "Raw Chicken Breast"),
    ("ranching", "ingredient_egg", "ingredient_egg", "Fresh Farm Egg"),
    ("ranching", "ingredient_milk", "ingredient_milk", "Fresh Whole Milk"),
    ("ranching", "ingredient_pork", "ingredient_pork", "Raw Pork Chop"),
    ("fishing", "ingredient_fillet_bass", "ingredient_fillet_bass", "Bass Fillet"),
    ("fishing", "ingredient_fillet_catfish", "ingredient_fillet_catfish", "Catfish Fillet"),
    ("fishing", "ingredient_fillet_crappie", "ingredient_fillet_crappie", "Crappie Fillet"),
    ("fishing", "ingredient_fillet_salmon", "ingredient_fillet_salmon", "Salmon Fillet"),
    ("fishing", "ingredient_fillet_trout", "ingredient_fillet_trout", "Trout Fillet"),
    ("fishing", "ingredient_fillet_walleye", "ingredient_fillet_walleye", "Walleye Fillet"),
]

for src_cat, old_id, new_id, new_name in FOOD_MOVES:
    src_dir = os.path.join(ASSETS_DIR, src_cat, old_id)
    dst_dir = os.path.join(FOOD_DIR, new_id)
    if os.path.exists(src_dir):
        update_manifest_and_files(src_dir, dst_dir, old_id, new_id, "food", new_name)
        print(f"Moved {src_cat}/{old_id} -> food/{new_id}")

print("\n=== MIGRATING FUEL ITEMS ===")
FUEL_MOVES = [
    # (source_cat, old_id, new_id, new_name)
    ("electricity", "electricity_fuel_diesel_large", "fuel_diesel_large", "Large Diesel Fuel Drum"),
    ("electricity", "electricity_fuel_diesel_small", "fuel_diesel_small", "Small Diesel Canister"),
    ("electricity", "electricity_fuel_gasoline", "fuel_gasoline", "Gasoline Can"),
    ("electricity", "electricity_fuel_propane", "fuel_propane", "Standard Propane Tank"),
    ("electricity", "electricity_fuel_propane_large", "fuel_propane_large", "Large Propane Tank"),
    ("electricity", "electricity_fuel_propane_small", "fuel_propane_small", "Small Propane Tank"),
    ("electricity", "electricity_fuel_propanetank_20lb", "fuel_tank_propane_20lb", "20lb Propane Tank"),
    ("electricity", "electricity_fuel_pump_diesel", "fuel_pump_diesel_commercial", "Commercial Diesel Dispenser"),
    ("electricity", "electricity_fuel_pump_gas", "fuel_pump_gas_commercial", "Commercial Gas Dispenser"),
    ("electricity", "electricity_mat_propanetank_500gal", "fuel_tank_propane_500gal_steel", "500-Gallon Steel Propane Tank"),
    ("electricity", "electricity_tank_fuel_bulk_large", "fuel_tank_bulk_large", "Large Bulk Fuel Storage Tank"),
    ("electricity", "electricity_tank_fuel_bulk_small", "fuel_tank_bulk_small", "Small Bulk Fuel Storage Tank"),
    ("electricity", "electricity_tank_propane_1000gal", "fuel_tank_propane_1000gal", "1000-Gallon Propane Tank"),
    ("electricity", "electricity_tank_propane_500gal", "fuel_tank_propane_500gal", "500-Gallon Propane Tank"),
    ("building", "fuel_pump_diesel", "fuel_pump_diesel", "Diesel Fuel Pump"),
    ("building", "fuel_pump_gas", "fuel_pump_gas", "Gasoline Fuel Pump"),
    ("building", "item_fuel_dieselcan_5gal", "fuel_can_diesel_5gal", "5-Gallon Diesel Jerry Can"),
    ("building", "item_tank_fuelbulk_elevated", "fuel_tank_bulk_elevated", "Elevated Gravity Fuel Tank"),
    ("logging", "fuel_firewood", "fuel_firewood", "Seasoned Firewood Stack"),
    ("logging", "firewood_bundle_wrapped", "fuel_firewood_bundle_wrapped", "Wrapped Firewood Bundle"),
    ("logging", "firewood_rack_cord", "fuel_firewood_rack_cord", "Cord Firewood Storage Rack"),
    ("logging", "bundle_firewood_wrapped", "fuel_firewood_bundle_tied", "Tied Firewood Bundle"),
]

for src_cat, old_id, new_id, new_name in FUEL_MOVES:
    src_dir = os.path.join(ASSETS_DIR, src_cat, old_id)
    dst_dir = os.path.join(FUEL_DIR, new_id)
    if os.path.exists(src_dir):
        update_manifest_and_files(src_dir, dst_dir, old_id, new_id, "fuel", new_name)
        print(f"Moved {src_cat}/{old_id} -> fuel/{new_id}")

print("\n=== TAGGING GROWABLE SPECIES ===")
SPECIES_MAP = {
    # Trees
    "apple": ["planted_sapling_apple", "sapling_apple", "tree_apple", "tree_apple_large", "tree_apple_medium", "tree_apple_small"],
    "birch": ["planted_sapling_birch", "sapling_birch", "tree_birch", "tree_birch_medium", "tree_birch_small", "tree_birch_tall"],
    "maple": ["planted_sapling_maple", "sapling_maple", "tree_maple", "tree_maple_medium", "tree_maple_small"],
    "oak": ["planted_sapling_oak", "sapling_oak", "tree_oak", "tree_oak_autumn", "tree_oak_large", "tree_oak_medium", "tree_oak_small", "tree_sapling"],
    "pine": ["planted_sapling_pine", "sapling_pine", "tree_pine", "tree_pine_medium", "tree_pine_small", "tree_pine_tall"],
    "poplar": ["planted_sapling_poplar", "sapling_poplar", "tree_poplar_columnar", "tree_poplar_medium", "tree_poplar_small"],
    "willow": ["planted_sapling_willow", "sapling_willow", "tree_willow", "tree_willow_large", "tree_willow_medium", "tree_willow_small"],
    # Crops
    "carrot": ["crop_carrot", "seed_carrot"],
    "corn": ["crop_corn", "seed_corn"],
    "cotton": ["crop_cotton", "seed_cotton"],
    "herb": ["crop_herb", "seed_herb"],
    "potato": ["crop_potato", "seed_potato"],
    "pumpkin": ["crop_pumpkin", "seed_pumpkin"],
    "strawberry": ["crop_strawberry", "seed_strawberry"],
    "sunflower": ["crop_sunflower", "seed_sunflower"],
    "tomato": ["crop_tomato", "seed_tomato"],
    "wheat": ["crop_wheat", "seed_wheat"],
    # Animals
    "chicken": ["animal_chicken_barred", "animal_chicken_chick", "animal_chicken_hen", "animal_chicken_red", "animal_chicken_white"],
    "cattle": ["animal_cow_adult", "animal_cow_calf", "animal_cow_calf_spotted", "animal_cow_highland", "animal_cow_holstein", "animal_cow_jersey"],
    "goat": ["animal_goat_adult", "animal_goat_blackwhite", "animal_goat_brown", "animal_goat_kid", "animal_goat_white"],
    "pig": ["animal_pig_adult", "animal_pig_duroc", "animal_pig_hampshire", "animal_pig_piglet", "animal_pig_pink"],
    "sheep": ["animal_sheep_adult", "animal_sheep_lamb", "animal_sheep_suffolk", "animal_sheep_tan", "animal_sheep_white"]
}

# Scan and update species across all categories
for root, dirs, files in os.walk(ASSETS_DIR):
    for f in files:
        if f.endswith(".json") and f != "tsconfig.json" and f != "package.json":
            fpath = os.path.join(root, f)
            try:
                with open(fpath, "r", encoding="utf-8") as jf:
                    manifest = json.load(jf)
                item_id = manifest.get("id", "")
                
                matched_species = None
                for sp, ids in SPECIES_MAP.items():
                    if item_id in ids or item_id.startswith(f"{sp}_") or f"_{sp}_" in item_id or item_id.endswith(f"_{sp}"):
                        matched_species = sp
                        break
                        
                if matched_species and manifest.get("growth", {}).get("is_growable"):
                    manifest["growth"]["species"] = matched_species
                    with open(fpath, "w", encoding="utf-8") as jf:
                        json.dump(manifest, jf, indent=2)
            except Exception:
                pass

print("Species tagging complete.")

