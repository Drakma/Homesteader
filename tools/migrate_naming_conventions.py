#!/usr/bin/env python3
"""
Homesteader Naming Conventions & Waste Taxonomy Migration Script
Applies standard naming conventions:
- Rename category sewage -> waste
- Consolidate all waste/compost/manure/toilet assets into waste/
- Prefix all structures with struct_
- Prefix all machinery with machinery_
- Prefix all tools with tool_
- Prefix all crop drops, meats, fish fillets, eggs, milk with ingredients_
- Prefix all edible foods dropped directly from crops/trees with food_
- Retain animal_ for live animals
- Synchronize all manifests, icons, model references, READMEs, and catalog
"""

import os
import sys
import json
import shutil
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def rename_asset(src_cat, src_id, dst_cat, dst_id, new_display_name=None):
    src_dir = os.path.join(BASE_DIR, src_cat, src_id)
    dst_dir = os.path.join(BASE_DIR, dst_cat, dst_id)

    if not os.path.exists(src_dir):
        print(f"  [SKIP] Source not found: {src_cat}/{src_id}")
        return False

    if src_dir != dst_dir and os.path.exists(dst_dir):
        # Target already exists; remove source as duplicate
        print(f"  [MERGE/DUP] Target {dst_cat}/{dst_id} exists. Removing duplicate {src_cat}/{src_id}...")
        shutil.rmtree(src_dir)
        return True

    print(f"  [RENAME] {src_cat}/{src_id} -> {dst_cat}/{dst_id}")

    # Ensure destination category directory exists
    os.makedirs(os.path.join(BASE_DIR, dst_cat), exist_ok=True)

    # Move/rename directory
    if src_dir != dst_dir:
        os.rename(src_dir, dst_dir)

    target_dir = dst_dir

    # Rename any files prefixed with src_id
    renamed_files_map = {}
    if src_id != dst_id:
        for fname in list(os.listdir(target_dir)):
            if fname.startswith(f"{src_id}."):
                ext = fname[len(src_id):]
                new_fname = f"{dst_id}{ext}"
                old_path = os.path.join(target_dir, fname)
                new_path = os.path.join(target_dir, new_fname)
                if os.path.exists(new_path) and old_path != new_path:
                    os.remove(new_path)
                os.rename(old_path, new_path)
                renamed_files_map[fname] = new_fname

    # Update manifest JSON
    manifest_file = os.path.join(target_dir, f"{dst_id}.json")
    if not os.path.exists(manifest_file):
        manifest_file = os.path.join(target_dir, f"{src_id}.json")

    if os.path.exists(manifest_file):
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            data["id"] = dst_id
            if new_display_name:
                data["name"] = new_display_name
            data["category"] = dst_cat
            data["icon"] = f"{dst_id}.png"

            # Update models list if any model file was renamed
            if "models" in data and isinstance(data["models"], list):
                for m in data["models"]:
                    if isinstance(m, dict):
                        m_file = m.get("file", "")
                        if m_file in renamed_files_map:
                            m["file"] = renamed_files_map[m_file]

            # Update stages if referencing src_id
            if "growth" in data and isinstance(data["growth"], dict):
                stages = data["growth"].get("stages", [])
                for st in stages:
                    if isinstance(st, dict) and st.get("item_id") == src_id:
                        st["item_id"] = dst_id
                curr_st = data["growth"].get("current_stage")
                if isinstance(curr_st, dict) and curr_st.get("item_id") == src_id:
                    curr_st["item_id"] = dst_id

            target_manifest = os.path.join(target_dir, f"{dst_id}.json")
            with open(target_manifest, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            if target_manifest != manifest_file and os.path.exists(manifest_file):
                os.remove(manifest_file)
        except Exception as e:
            print(f"    [ERR] Manifest update failed: {e}")

    # Update README.md
    readme_path = os.path.join(target_dir, "README.md")
    if os.path.exists(readme_path):
        try:
            with open(readme_path, "r", encoding="utf-8") as f:
                r_text = f.read()
            r_text = r_text.replace(f"{src_id}.png", f"{dst_id}.png")
            r_text = r_text.replace(f"{src_id}.json", f"{dst_id}.json")
            r_text = r_text.replace(f"#{src_id}", f"#{dst_id}")
            r_text = r_text.replace(f"`{src_id}`", f"`{dst_id}`")
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(r_text)
        except Exception as e:
            print(f"    [ERR] README update failed: {e}")

    return True

def delete_asset_if_exists(cat, item_id):
    p = os.path.join(BASE_DIR, cat, item_id)
    if os.path.exists(p) and os.path.isdir(p):
        print(f"  [PURGE DUP] Removing redundant {cat}/{item_id}")
        shutil.rmtree(p)

def main():
    print("=" * 70)
    print("  Homesteader Asset Library Naming Conventions Migration")
    print("=" * 70)

    # 1. Step 1: Rename category sewage -> waste
    sewage_dir = os.path.join(BASE_DIR, "sewage")
    waste_dir = os.path.join(BASE_DIR, "waste")
    if os.path.exists(sewage_dir):
        print("\n--- 1. Renaming category 'sewage' to 'waste' ---")
        if not os.path.exists(waste_dir):
            os.rename(sewage_dir, waste_dir)
            print("  Renamed directory assets/sewage -> assets/waste")
        else:
            # Merge sewage into waste
            for item in os.listdir(sewage_dir):
                shutil.move(os.path.join(sewage_dir, item), os.path.join(waste_dir, item))
            os.rmdir(sewage_dir)
            print("  Merged assets/sewage into existing assets/waste")

    # Update all manifests inside waste to have category: "waste"
    for item in os.listdir(waste_dir):
        item_dir = os.path.join(waste_dir, item)
        if not os.path.isdir(item_dir): continue
        m_file = os.path.join(item_dir, f"{item}.json")
        if os.path.exists(m_file):
            try:
                with open(m_file, "r", encoding="utf-8") as f:
                    d = json.load(f)
                d["category"] = "waste"
                with open(m_file, "w", encoding="utf-8") as f:
                    json.dump(d, f, indent=2)
            except Exception:
                pass

    # Clean legacy sewage_* duplicates inside waste
    delete_asset_if_exists("waste", "sewage_distributionbox")
    delete_asset_if_exists("waste", "sewage_septictank_poly_500gal")
    delete_asset_if_exists("waste", "sewage_toilet_composting")
    if os.path.exists(os.path.join(waste_dir, "sewage_compostbin_3bay")):
        rename_asset("waste", "sewage_compostbin_3bay", "waste", "compost_bin_3bay", "3-Bay Compost Bin")

    # 2. Step 2: Consolidate waste/compost/manure assets into waste
    print("\n--- 2. Moving Waste & Sanitation Assets to 'waste/' ---")
    waste_moves = [
        ("farming", "bin_compost_3bay", "waste", "compost_bin_3bay", "3-Bay Compost Bin"),
        ("tools", "pump_macerator_waste", "waste", "tool_pump_macerator_waste", "Macerator Waste Pump"),
        ("building", "tank_rv_waste_tote", "waste", "tank_rv_waste_tote", "RV Waste Holding Tote Tank"),
        ("building", "pile_manure_large", "waste", "pile_manure_large", "Large Manure Pile"),
        ("building", "pile_manure_medium", "waste", "pile_manure_medium", "Medium Manure Pile"),
        ("building", "pile_manure_small", "waste", "pile_manure_small", "Small Manure Pile"),
        ("building", "mat_pile_manure_large", "waste", "mat_pile_manure_large", "Large Manure Pile (Material)"),
        ("building", "mat_pile_manure_medium", "waste", "mat_pile_manure_medium", "Medium Manure Pile (Material)"),
        ("building", "mat_pile_manure_small", "waste", "mat_pile_manure_small", "Small Manure Pile (Material)")
    ]
    for src_cat, src_id, dst_cat, dst_id, name in waste_moves:
        rename_asset(src_cat, src_id, dst_cat, dst_id, name)

    # 3. Step 3: Structures naming (struct_*)
    print("\n--- 3. Enforcing 'struct_' Prefix on All Structures ---")
    delete_asset_if_exists("structures", "tent_canvas")
    delete_asset_if_exists("structures", "tent_dome")
    if os.path.exists(os.path.join(BASE_DIR, "ranching", "kennel")):
        rename_asset("ranching", "kennel", "structures", "struct_kennel", "Dog Kennel Structure")

    # 4. Step 4: Machinery naming (machinery_*)
    print("\n--- 4. Enforcing 'machinery_' Prefix on All Heavy Machinery ---")
    machinery_renames = [
        ("building", "machine_combine_large", "building", "machinery_combine_large", "Large Combine Harvester"),
        ("building", "machine_combine_small", "building", "machinery_combine_small", "Small Combine Harvester"),
        ("building", "machine_excavator_large", "building", "machinery_excavator_large", "Large Excavator"),
        ("building", "machine_excavator_small", "building", "machinery_excavator_small", "Small Excavator"),
        ("building", "machine_tractor_large", "building", "machinery_tractor_large", "Large Farm Tractor"),
        ("building", "machine_tractor_small", "building", "machinery_tractor_small", "Small Utility Tractor"),
        ("logging", "machine_sawmill_portable", "logging", "machinery_sawmill_portable", "Portable Sawmill"),
        ("logging", "machine_sawmill_stationary", "logging", "machinery_sawmill_stationary", "Stationary Sawmill"),
        ("ranching", "machine_skidsteer_large", "ranching", "machinery_skidsteer_large", "Large Skid Steer Loader"),
        ("ranching", "machine_skidsteer_small", "ranching", "machinery_skidsteer_small", "Compact Skid Steer Loader")
    ]
    for src_cat, src_id, dst_cat, dst_id, name in machinery_renames:
        rename_asset(src_cat, src_id, dst_cat, dst_id, name)

    # 5. Step 5: Tools naming (tool_*)
    print("\n--- 5. Enforcing 'tool_' Prefix on All Tools ---")
    # Clean duplicates in logging
    for dup in ["axe", "axe_felling", "chainsaw", "chainsaw_gas_16", "chainsaw_gas_20", "pickaxe", "icon_axe", "icon_pickaxe"]:
        delete_asset_if_exists("logging", dup)

    # Clean duplicates in farming
    for dup in ["hoe", "sickle", "sickle_grass"]:
        delete_asset_if_exists("farming", dup)

    # Clean duplicates in fishing
    for dup in ["cant_hook_peavey", "fishing_rod"]:
        delete_asset_if_exists("fishing", dup)

    # Clean duplicates in ranching
    for dup in ["hammer", "hammer_claw", "hammer_club", "shears_pruning", "shears_sheep_wool", "shovel_scoop_flat", "wrench_adjustable"]:
        delete_asset_if_exists("ranching", dup)

    # Clean icon duplicate in tools
    delete_asset_if_exists("tools", "icon_shovel")

    # Rename non-prefixed tools in tools/
    tools_renames = [
        ("tools", "drill_corded", "tools", "tool_drill_corded", "Corded Heavy Drill"),
        ("tools", "drill_cordless_20v", "tools", "tool_drill_cordless_20v", "Cordless 20V Drill"),
        ("tools", "drill_cordless_basic", "tools", "tool_drill_cordless_basic", "Basic Cordless Drill"),
        ("tools", "drill_cordless_pro", "tools", "tool_drill_cordless_pro", "Professional Cordless Drill"),
        ("tools", "hose_garden_reel", "tools", "tool_hose_garden_reel", "Garden Hose & Reel"),
        ("tools", "item_bucket_empty", "tools", "tool_bucket_empty", "Empty Utility Bucket"),
        ("tools", "net_landing_telescopic", "tools", "tool_net_landing_telescopic", "Telescopic Landing Net"),
        ("tools", "nozzle_spray_quick", "tools", "tool_nozzle_spray_quick", "Quick-Connect Spray Nozzle"),
        ("tools", "paddle_sorting_cattle", "tools", "tool_paddle_sorting_cattle", "Cattle Sorting Paddle"),
        ("tools", "pump_pitcher_manual", "tools", "tool_pump_pitcher_manual", "Manual Pitcher Well Pump"),
        ("tools", "pump_submersible_deep", "tools", "tool_pump_submersible_deep", "Deep Submersible Well Pump"),
        ("tools", "pump_sump_float", "tools", "tool_pump_sump_float", "Automatic Sump Pump"),
        ("tools", "rod_heavy_trolling", "tools", "tool_rod_heavy_trolling", "Heavy Trolling Fishing Rod"),
        ("tools", "rod_spincast_combo", "tools", "tool_rod_spincast_combo", "Spincast Rod & Reel Combo"),
        ("tools", "shovel", "tools", "tool_shovel", "Standard Shovel"),
        ("tools", "shovel_round_point", "tools", "tool_shovel_round_point", "Round Point Shovel"),
        ("tools", "shovel_trenching", "tools", "tool_shovel_trenching", "Trenching Shovel"),
        ("tools", "sprayer_backpack_4gal", "tools", "tool_sprayer_backpack_4gal", "4-Gallon Backpack Sprayer"),
        ("tools", "trowel_hand", "tools", "tool_trowel_hand", "Hand Garden Trowel"),
        ("tools", "wrench", "tools", "tool_wrench", "Standard Wrench"),
        ("tools", "wrench_pipe", "tools", "tool_wrench_pipe", "Heavy Pipe Wrench"),
        ("fishing", "rod_fly_fishing", "fishing", "tool_rod_fly_fishing", "Fly Fishing Rod"),
        ("fishing", "item_rod_flyfishing", "fishing", "tool_rod_fly_fishing", "Fly Fishing Rod")
    ]
    for src_cat, src_id, dst_cat, dst_id, name in tools_renames:
        rename_asset(src_cat, src_id, dst_cat, dst_id, name)

    # 6. Step 6: Ingredients naming (ingredients_*)
    print("\n--- 6. Enforcing 'ingredients_' Prefix on Crop Drops, Meats, Fillets, Eggs & Milk ---")
    # Clean empty placeholders first
    for dup in ["meat_beef", "meat_chicken", "meat_pork", "meat_goat", "meat_mutton", "animal_meat", "egg", "animal_egg", "milk", "animal_milk"]:
        delete_asset_if_exists("ranching", dup)

    # Ranching ingredients
    ranching_ingredients = [
        ("ranching", "item_meat_beef_steak", "ranching", "ingredients_beef", "Raw Beef Steak"),
        ("ranching", "item_meat_chicken_drumstick", "ranching", "ingredients_chicken", "Raw Chicken Drumstick"),
        ("ranching", "item_meat_pork_chop", "ranching", "ingredients_pork", "Raw Pork Chop"),
        ("ranching", "item_animal_eggs_carton", "ranching", "ingredients_egg", "Fresh Farm Eggs"),
        ("ranching", "item_animal_milk_jug", "ranching", "ingredients_milk", "Fresh Farm Milk")
    ]
    for src_cat, src_id, dst_cat, dst_id, name in ranching_ingredients:
        rename_asset(src_cat, src_id, dst_cat, dst_id, name)

    # Fishing fillets
    for dup in ["fillet_salmon", "fillet_bass", "fillet_trout", "fillet_catfish", "fillet_walleye", "fillet_crappie"]:
        delete_asset_if_exists("fishing", dup)

    fillet_renames = [
        ("fishing", "item_fishfillet_salmon", "fishing", "ingredients_fillet_salmon", "Fresh Salmon Fillet"),
        ("fishing", "item_fishfillet_bass", "fishing", "ingredients_fillet_bass", "Fresh Bass Fillet"),
        ("fishing", "item_fishfillet_trout", "fishing", "ingredients_fillet_trout", "Fresh Trout Fillet"),
        ("fishing", "item_fishfillet_catfish", "fishing", "ingredients_fillet_catfish", "Fresh Catfish Fillet"),
        ("fishing", "item_fishfillet_walleye", "fishing", "ingredients_fillet_walleye", "Fresh Walleye Fillet"),
        ("fishing", "item_fishfillet_crappie", "fishing", "ingredients_fillet_crappie", "Fresh Crappie Fillet")
    ]
    for src_cat, src_id, dst_cat, dst_id, name in fillet_renames:
        rename_asset(src_cat, src_id, dst_cat, dst_id, name)

    # Crop drop ingredients
    for dup in ["wheat", "cotton", "sunflower", "herb", "icon_wheat"]:
        delete_asset_if_exists("farming", dup)

    crop_drop_renames = [
        ("farming", "item_wheat_sheaf", "farming", "ingredients_wheat", "Harvested Wheat Sheaf"),
        ("farming", "item_cotton_boll", "farming", "ingredients_cotton", "Raw Cotton Boll"),
        ("farming", "item_sunflower_head", "farming", "ingredients_sunflower", "Harvested Sunflower Head")
    ]
    for src_cat, src_id, dst_cat, dst_id, name in crop_drop_renames:
        rename_asset(src_cat, src_id, dst_cat, dst_id, name)

    # 7. Step 7: Edible Foods (food_*)
    print("\n--- 7. Enforcing 'food_' Prefix on Edible Tree/Crop Harvests ---")
    # Clean empty crop duplicates
    for dup in ["carrot", "corn", "pumpkin", "potato", "tomato", "strawberry"]:
        delete_asset_if_exists("farming", dup)
        delete_asset_if_exists("ranching", dup)

    food_renames = [
        ("farming", "item_carrot_bunch", "farming", "food_carrot", "Fresh Garden Carrots"),
        ("farming", "item_corn_ear", "farming", "food_corn", "Sweet Corn Ear"),
        ("farming", "item_pumpkin_carved", "farming", "food_pumpkin", "Harvest Pumpkin"),
        ("farming", "item_potato_loose", "farming", "food_potato", "Fresh Russet Potato"),
        ("farming", "item_tomato_fruit", "farming", "food_tomato", "Vine-Ripe Tomato"),
        ("farming", "item_cabbage_harvested", "farming", "food_cabbage", "Fresh Green Cabbage"),
        ("ranching", "item_strawberry_basket", "farming", "food_strawberry", "Fresh Strawberry Basket")
    ]
    for src_cat, src_id, dst_cat, dst_id, name in food_renames:
        rename_asset(src_cat, src_id, dst_cat, dst_id, name)

    print("\n" + "=" * 70)
    print("  Migration completed successfully!")
    print("=" * 70)

if __name__ == "__main__":
    main()

