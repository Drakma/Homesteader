import os
import shutil
import json
import re

BASE_DIR = r"C:\Users\casey\Desktop\Homesteader\assets"

def format_title(item_id):
    name = item_id
    prefixes = [
        "animal_fish_", "animal_", "fishing_", "seed_", "ingredient_fillet_", 
        "ingredient_", "mat_bale_", "mat_pelt_", "mat_", "food_", 
        "electricity_", "water_", "waste_", "net_", "tool_", "machinery_", "struct_"
    ]
    for p in prefixes:
        if name.startswith(p):
            name = name[len(p):]
            break
    name = name.replace("_", " ").title()
    if item_id.startswith("seed_") and not name.lower().endswith("seeds"):
        name = f"{name} Seeds"
    elif item_id.startswith("mat_bale_"):
        name = f"Bale ({name})"
    return name

def update_manifest_and_files(dst_path, new_id, new_category, new_name=None):
    if not os.path.exists(dst_path):
        return
        
    files = os.listdir(dst_path)
    
    # 1. Rename icon file to <new_id>.png
    png_files = [f for f in files if f.endswith(".png") and not f.startswith("T_") and not f.startswith("palette")]
    if png_files:
        if f"{new_id}.png" not in files:
            best_png = png_files[0]
            for f in png_files:
                if "icon" in f or "item" in f:
                    best_png = f
                    break
            old_png_path = os.path.join(dst_path, best_png)
            new_png_path = os.path.join(dst_path, f"{new_id}.png")
            if os.path.exists(old_png_path) and old_png_path != new_png_path:
                shutil.move(old_png_path, new_png_path)
                
    # 2. Rename json manifest to <new_id>.json
    json_files = [f for f in os.listdir(dst_path) if f.endswith(".json")]
    manifest_file = None
    if f"{new_id}.json" in json_files:
        manifest_file = os.path.join(dst_path, f"{new_id}.json")
    elif json_files:
        old_json_path = os.path.join(dst_path, json_files[0])
        manifest_file = os.path.join(dst_path, f"{new_id}.json")
        if old_json_path != manifest_file:
            shutil.move(old_json_path, manifest_file)
            
    # 3. Read and update manifest content
    if manifest_file and os.path.exists(manifest_file):
        try:
            with open(manifest_file, "r", encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception:
            data = {}
            
        data["id"] = new_id
        data["category"] = new_category
        data["icon"] = f"{new_id}.png"
        if new_name:
            data["name"] = new_name
        elif "name" not in data or not data["name"]:
            data["name"] = format_title(new_id)
            
        curr_files = os.listdir(dst_path)
        objs = [f for f in curr_files if f.endswith(".obj")]
        mtls = [f for f in curr_files if f.endswith(".mtl")]
        fbxs = [f for f in curr_files if f.endswith(".fbx")]
        glbs = [f for f in curr_files if f.endswith(".glb")]
        
        models_list = []
        for m in mtls:
            models_list.append({"file": m, "format": "mtl"})
        for o in objs:
            models_list.append({"file": o, "format": "obj"})
        for b in fbxs:
            models_list.append({"file": b, "format": "fbx"})
        for g in glbs:
            models_list.append({"file": g, "format": "glb"})
            
        if models_list:
            data["models"] = models_list
            
        with open(manifest_file, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)
            
    # 4. Update README.md
    readme_path = os.path.join(dst_path, "README.md")
    display_title = new_name or format_title(new_id)
    with open(readme_path, "w", encoding="utf-8") as fp:
        fp.write(f"# {display_title}\n\n")
        fp.write(f"**Item ID:** `{new_id}`  \n")
        fp.write(f"**Category:** `{new_category}`  \n")
        fp.write(f"**Icon:** ![{display_title}]({new_id}.png)\n\n")
        fp.write(f"Standardized Homesteader asset manifest for `{new_id}`.\n")

def migrate_asset(src_cat, src_id, dst_cat, dst_id, new_name=None):
    src_path = os.path.join(BASE_DIR, src_cat, src_id)
    dst_path = os.path.join(BASE_DIR, dst_cat, dst_id)
    
    if not os.path.exists(src_path):
        print(f"  [SKIP] Source not found: {src_cat}/{src_id}")
        return
        
    os.makedirs(os.path.join(BASE_DIR, dst_cat), exist_ok=True)
    
    if src_path == dst_path:
        print(f"  [IN-PLACE] Updating {dst_cat}/{dst_id}")
        update_manifest_and_files(dst_path, dst_id, dst_cat, new_name)
        return
        
    if os.path.exists(dst_path):
        print(f"  [MERGE] Merging {src_cat}/{src_id} into {dst_cat}/{dst_id}")
        for f in os.listdir(src_path):
            s_file = os.path.join(src_path, f)
            d_file = os.path.join(dst_path, f)
            if not os.path.exists(d_file) and not f.endswith(".json") and not f.endswith(".md"):
                shutil.copy2(s_file, d_file)
        shutil.rmtree(src_path)
        update_manifest_and_files(dst_path, dst_id, dst_cat, new_name)
    else:
        print(f"  [MOVE] {src_cat}/{src_id} -> {dst_cat}/{dst_id}")
        shutil.move(src_path, dst_path)
        update_manifest_and_files(dst_path, dst_id, dst_cat, new_name)

def run():
    print("=== PASS 2: HOMESTEADER ASSET NAMING STANDARDIZATION ===\n")
    
    # 1. FISH & FISHING GEAR
    print("--- 1. Fishing Category Migrations ---")
    fish_mappings = [
        ("fish_bass", "animal_fish_bass", "Largemouth Bass"),
        ("item_fish_largemouthbass", "animal_fish_bass", "Largemouth Bass"),
        ("fish_catfish", "animal_fish_catfish", "Channel Catfish"),
        ("fish_crappie", "animal_fish_crappie", "Black Crappie"),
        ("item_fish_crappie", "animal_fish_crappie", "Black Crappie"),
        ("fish_salmon", "animal_fish_salmon", "Sockeye Salmon"),
        ("item_fish_salmon", "animal_fish_salmon", "Sockeye Salmon"),
        ("fish_trout", "animal_fish_trout", "Rainbow Trout"),
        ("item_fish_rainbowtrout", "animal_fish_trout", "Rainbow Trout"),
        ("fish_walleye", "animal_fish_walleye", "Walleye"),
        ("item_fish_walleye", "animal_fish_walleye", "Walleye"),
        
        ("basket_fish_wire", "fishing_basket_wire", "Wire Fish Basket"),
        ("item_fishing_fishbasket", "fishing_basket_wire", "Wire Fish Basket"),
        ("box_lures_organizer", "fishing_box_lures_organizer", "Lures Organizer Box"),
        ("item_fishing_luretray", "fishing_box_lures_organizer", "Lures Organizer Box"),
        ("box_tackle_3tray", "fishing_box_tackle_3tray", "3-Tray Tackle Box"),
        ("item_fishing_tacklebox", "fishing_box_tackle_3tray", "3-Tray Tackle Box"),
        ("item_fishing_landingnet", "fishing_landingnet", "Fishing Landing Net"),
        ("fishing_bait", "fishing_bait", "Live Fishing Bait"),
        ("fishing_lure", "fishing_lure", "Fishing Lure"),
        ("sinkers_lead_split_shot", "fishing_sinkers_lead", "Split Shot Lead Sinkers"),
        ("spool_fishing_line_braid", "fishing_line_spool", "Braided Fishing Line Spool"),
        ("tool_fishing_rod", "fishing_rod", "Fishing Rod"),
        ("tool_rod_fly_fishing", "fishing_rod_fly", "Fly Fishing Rod"),
        
        ("ingredients_fillet_bass", "ingredient_fillet_bass", "Bass Fillet"),
        ("ingredients_fillet_catfish", "ingredient_fillet_catfish", "Catfish Fillet"),
        ("ingredients_fillet_crappie", "ingredient_fillet_crappie", "Crappie Fillet"),
        ("ingredients_fillet_salmon", "ingredient_fillet_salmon", "Salmon Fillet"),
        ("ingredients_fillet_trout", "ingredient_fillet_trout", "Trout Fillet"),
        ("ingredients_fillet_walleye", "ingredient_fillet_walleye", "Walleye Fillet"),
    ]
    for src, dst, name in fish_mappings:
        migrate_asset("fishing", src, "fishing", dst, name)
        
    migrate_asset("fishing", "tool_cant_hook_peavey", "logging", "tool_cant_hook_peavey", "Cant Hook Peavey")

    # 2. FARMING: Seeds & Ingredients
    print("\n--- 2. Farming Migrations ---")
    farming_mappings = [
        ("ingredients_cotton", "ingredient_cotton", "Cotton"),
        ("ingredients_sunflower", "ingredient_sunflower", "Sunflower Heads"),
        ("ingredients_wheat", "ingredient_wheat", "Wheat Sheaf"),
        ("item_seed_carrot", "seed_carrot", "Carrot Seeds"),
        ("item_seed_corn", "seed_corn", "Corn Seeds"),
        ("item_seed_cotton", "seed_cotton", "Cotton Seeds"),
        ("item_seed_herb", "seed_herb", "Herb Seeds"),
        ("item_seed_potato", "seed_potato", "Potato Seeds"),
        ("item_seed_pumpkin", "seed_pumpkin", "Pumpkin Seeds"),
        ("item_seed_sunflower", "seed_sunflower", "Sunflower Seeds"),
        ("item_seed_tomato", "seed_tomato", "Tomato Seeds"),
        ("item_seed_wheat", "seed_wheat", "Wheat Seeds"),
    ]
    for src, dst, name in farming_mappings:
        migrate_asset("farming", src, "farming", dst, name)
        
    migrate_asset("ranching", "item_seed_strawberry", "farming", "seed_strawberry", "Strawberry Seeds")
    migrate_asset("ranching", "seed_strawberry", "farming", "seed_strawberry", "Strawberry Seeds")
    migrate_asset("ranching", "crop_strawberry", "farming", "crop_strawberry", "Strawberry Crop")

    # 3. RANCHING: Ingredients, Truffle, Wool, Bales, Pelts
    print("\n--- 3. Ranching Migrations ---")
    ranching_mappings = [
        ("ingredients_beef", "ingredient_beef", "Raw Beef"),
        ("ingredients_chicken", "ingredient_chicken", "Raw Chicken"),
        ("ingredients_egg", "ingredient_egg", "Fresh Egg"),
        ("ingredients_milk", "ingredient_milk", "Fresh Milk"),
        ("ingredients_pork", "ingredient_pork", "Raw Pork"),
        
        ("animal_truffle", "food_truffle", "Black Truffle"),
        ("item_animal_truffle", "food_truffle", "Black Truffle"),
        
        ("wool", "mat_wool", "Raw Wool"),
        ("animal_wool", "mat_wool", "Raw Wool"),
        ("item_animal_wool_fleece", "mat_wool_fleece", "Wool Fleece"),
        
        ("bale_hay_round", "mat_bale_hay_round", "Round Hay Bale"),
        ("bale_hay_square", "mat_bale_hay_square", "Square Hay Bale"),
        ("bale_silage_round", "mat_bale_silage_round", "Round Silage Bale"),
        ("bale_straw_round", "mat_bale_straw_round", "Round Straw Bale"),
        ("bale_straw_square", "mat_bale_straw_square", "Square Straw Bale"),
        
        ("leather", "mat_leather", "Tanned Leather"),
        ("mat_leather", "mat_leather", "Tanned Leather"),
        ("mat_leather_roll", "mat_leather_roll", "Leather Roll"),
        ("pelt_cow", "mat_pelt_cow", "Cow Hide Pelt"),
        ("item_pelt_cow_hide", "mat_pelt_cow", "Cow Hide Pelt"),
        ("pelt_goat", "mat_pelt_goat", "Goat Skin Pelt"),
        ("item_pelt_goat_skin", "mat_pelt_goat", "Goat Skin Pelt"),
        ("pelt_sheep", "mat_pelt_sheep", "Sheep Fleece Pelt"),
        ("item_pelt_sheep_fleece", "mat_pelt_sheep", "Sheep Fleece Pelt"),
    ]
    for src, dst, name in ranching_mappings:
        migrate_asset("ranching", src, "ranching", dst, name)

    # 4. ELECTRICITY: Everything to electricity_
    print("\n--- 4. Electricity Migrations ---")
    elec_dir = os.path.join(BASE_DIR, "electricity")
    elec_dedupes = [
        ("item_generator", "generator"),
        ("item_solar_panel", "solar_panel"),
        ("item_tank_propane_1000gal", "tank_propane_1000gal"),
        ("item_wind_turbine", "wind_turbine"),
    ]
    for src, dst in elec_dedupes:
        migrate_asset("electricity", src, "electricity", dst)
        
    for item in sorted(os.listdir(elec_dir)):
        p = os.path.join(elec_dir, item)
        if not os.path.isdir(p): continue
        
        if item.startswith("electricity_"):
            new_id = item
        elif item.startswith("electric_"):
            new_id = "electricity_" + item[len("electric_"):]
        elif item.startswith("item_electric_"):
            new_id = "electricity_" + item[len("item_electric_"):]
        elif item.startswith("item_fuel_"):
            new_id = "electricity_fuel_" + item[len("item_fuel_"):]
        else:
            new_id = "electricity_" + item
            
        migrate_asset("electricity", item, "electricity", new_id)

    # 5. WATER: Everything to water_
    print("\n--- 5. Water Migrations ---")
    water_dir = os.path.join(BASE_DIR, "water")
    water_merges = [
        ("cistern_poly_1000gal", "water_cistern_poly_1000gal"),
        ("filter_rack_3stage", "water_filterrack_3stage"),
        ("tank_ibc_tote_275gal", "water_ibc_tote_275gal"),
        ("item_bucket_water", "water_bucket_water"),
        ("bucket_water", "water_bucket_water"),
        ("item_plumbing_filter_bigblue", "water_filter_canister_bigblue"),
        ("filter_canister_big_blue", "water_filter_canister_bigblue"),
        ("item_plumbing_waterjug_5gal", "water_jug_5gal"),
        ("item_plumbing_drainsock_roll", "water_drainsock_roll"),
        ("item_plumbing_gardenhose_reel", "water_hosereel_cart"),
        ("item_plumbing_pvc_bundle", "water_pvc_bundle"),
        ("tool_wateringcan", "water_watering_can"),
        ("tool_watering_can", "water_watering_can"),
        ("watering_can", "water_watering_can"),
        ("tool_wand_watering", "water_wand_watering_brass"),
        ("wand_watering_brass", "water_wand_watering_brass"),
        ("farm_irrigation_sprinkler_riser", "water_irrigation_sprinkler_riser"),
        ("sprinkler_micro_riser", "water_sprinkler_micro_riser"),
        ("pump_jet_shallow_well", "water_pump_jet_shallow_well"),
        ("well", "water_well"),
    ]
    for src, dst in water_merges:
        migrate_asset("water", src, "water", dst)
        
    for item in sorted(os.listdir(water_dir)):
        p = os.path.join(water_dir, item)
        if not os.path.isdir(p): continue
        if not item.startswith("water_"):
            migrate_asset("water", item, "water", f"water_{item}")
        else:
            migrate_asset("water", item, "water", item)

    # 6. WASTE: Everything to waste_
    print("\n--- 6. Waste Migrations ---")
    waste_dir = os.path.join(BASE_DIR, "waste")
    waste_merges = [
        ("mat_pile_manure_large", "waste_pile_manure_large"),
        ("pile_manure_large", "waste_pile_manure_large"),
        ("mat_pile_manure_medium", "waste_pile_manure_medium"),
        ("pile_manure_medium", "waste_pile_manure_medium"),
        ("mat_pile_manure_small", "waste_pile_manure_small"),
        ("pile_manure_small", "waste_pile_manure_small"),
        ("tool_pump_macerator_waste", "waste_pump_macerator"),
    ]
    for src, dst in waste_merges:
        migrate_asset("waste", src, "waste", dst)
        
    for item in sorted(os.listdir(waste_dir)):
        p = os.path.join(waste_dir, item)
        if not os.path.isdir(p): continue
        if not item.startswith("waste_"):
            migrate_asset("waste", item, "waste", f"waste_{item}")
        else:
            migrate_asset("waste", item, "waste", item)

    # 7. INTERNET: Everything to net_
    print("\n--- 7. Internet Migrations ---")
    net_dir = os.path.join(BASE_DIR, "internet")
    net_mappings = [
        ("internet_antenna_omni_cellular", "net_antenna_omni_mast"),
        ("antenna_omni_cellular", "net_antenna_omni_cellular"),
        ("internet_antenna_yagi_mast", "net_antenna_yagi_mast"),
        ("antenna_yagi_directional", "net_antenna_yagi_directional"),
        ("internet_dish_highperf_mast", "net_dish_highperf_mast"),
        ("dish_satellite_high_perf", "net_dish_satellite_high_perf"),
        ("internet_dish_starlink_tripod", "net_dish_starlink_tripod"),
        ("internet_satellite_dish", "net_dish_satellite"),
        ("dish_satellite_standard", "net_dish_satellite_standard"),
        ("internet_outdoor_ap_pole", "net_outdoor_ap_pole"),
        ("ap_outdoor_weatherproof", "net_ap_outdoor_weatherproof"),
        ("internet_router", "net_router"),
        ("router_mesh_wifi6", "net_router_mesh_wifi6"),
        ("internet_cable", "net_cable"),
        ("cable_ethernet_cat6_100ft", "net_cable_ethernet_cat6_100ft"),
        ("cable_ethernet_cat6_50ft", "net_cable_ethernet_cat6_50ft"),
        ("spool_cable_cat6_500ft", "net_spool_cable_cat6_500ft"),
        ("arrestor_lightning_ethernet", "net_arrestor_lightning_ethernet"),
    ]
    for src, dst in net_mappings:
        migrate_asset("internet", src, "internet", dst)
        
    for item in sorted(os.listdir(net_dir)):
        p = os.path.join(net_dir, item)
        if not os.path.isdir(p): continue
        if item.startswith("internet_"):
            new_id = "net_" + item[len("internet_"):]
            migrate_asset("internet", item, "internet", new_id)
        elif not item.startswith("net_"):
            migrate_asset("internet", item, "internet", f"net_{item}")
        else:
            migrate_asset("internet", item, "internet", item)

    print("\nMigration complete! Ready to rebuild catalogs.")

if __name__ == "__main__":
    run()

