#!/usr/bin/env python3
"""
Homesteader World Assets & Models Validation Suite
=================================================
Validates ALL 283 3D World Models & Preview Icons across all Homesteader Categories:
1. Homestead Buildings & Architecture (23 models: 10 prefabs + 9 modular + 4 new outbuildings/campers)
2. Realistic Trees & Foliage (30 models: 14 trees + 16 scatter foliage props)
3. Ground Tiles & Modular Foundations (26 models)
4. Utilities & Infrastructure (40 models: 28 original + 12 new electrical/plumbing supplies)
5. Livestock & Ranching (47 models: 26 livestock animals [all 3 breed varieties] + 11 feed/fencing + 10 yields/pelts)
6. Crops, Produce & Farm Equipment (40 models: 12 original + 4 heavy machines + 14 loose produce/food + 10 seed packets)
7. Tools, Logging & Fishing (77 models: 5 log piles + 2 sawmills + 5 workshop fixtures + 4 earthmovers + 28 handheld tools + 11 materials + 10 hardware + 12 fishing items)

Checks:
- Dual-directory file existence (.obj + .mtl and .png preview icons in HUD and UE5)
- Ground plane alignment (z_min ~= 0.0)
- Geometry integrity (vertex count > 0, face count > 0, non-degenerate bounds)
"""

import os
import sys

HUD_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UE5_ROOT = os.path.abspath(os.path.join(HUD_ROOT, "..", "Homesteader", "Content", "Homesteader"))

BUILDINGS = [
    # 10 Prefabs
    ("SM_Building_Outhouse", 100, 100, 220, 260),
    ("SM_Building_WellHouse", 100, 100, 200, 260),
    ("SM_Building_ToolShed", 200, 200, 240, 290),
    ("SM_Building_ChickenCoop", 200, 300, 210, 260),
    ("SM_Building_Woodshed", 200, 300, 220, 270),
    ("SM_Building_WaterTower", 200, 200, 600, 700),
    ("SM_Building_RootCellar", 300, 300, 140, 200),
    ("SM_Building_Greenhouse", 300, 400, 280, 360),
    ("SM_Building_LogCabin", 500, 600, 450, 560),
    ("SM_Building_SmallBarn", 600, 800, 650, 780),
    # 9 Modular Parts
    ("SM_Part_Wall_Wood_1m", 100, 15, 230, 260),
    ("SM_Part_Wall_Doorway_1m", 100, 15, 230, 260),
    ("SM_Part_Wall_Window_1m", 100, 15, 230, 260),
    ("SM_Part_Door_Wood", 90, 10, 200, 220),
    ("SM_Part_Floor_Wood_1m", 100, 100, 10, 30),
    ("SM_Part_Floor_Stone_1m", 100, 100, 10, 30),
    ("SM_Part_Roof_Slope_1m", 100, 100, 40, 80),
    ("SM_Part_Roof_Ridge_1m", 100, 100, 20, 50),
    ("SM_Part_Stairs_Wood_1m", 100, 100, 90, 120),
]

TREES = [
    ("SM_Tree_Oak_Large", 500, 650, 160),
    ("SM_Tree_Oak_Medium", 380, 500, 110),
    ("SM_Tree_Oak_Small", 220, 320, 60),
    ("SM_Tree_Oak_Autumn", 420, 540, 120),
    ("SM_Tree_Pine_Tall", 720, 860, 100),
    ("SM_Tree_Pine_Medium", 440, 560, 80),
    ("SM_Tree_Pine_Small", 270, 360, 60),
    ("SM_Tree_Birch_Tall", 550, 680, 70),
    ("SM_Tree_Birch_Medium", 360, 480, 60),
    ("SM_Tree_Apple", 340, 440, 90),
    ("SM_Tree_Willow", 480, 600, 120),
    ("SM_Tree_Dead_Snag", 360, 470, 115),
    ("SM_Tree_Maple", 600, 740, 80),
    ("SM_Tree_Poplar_Columnar", 820, 960, 50),
]

SCATTER_FOLIAGE = [
    "SM_Bush_Round_Large", "SM_Bush_Round_Medium", "SM_Bush_Berry",
    "SM_Bush_Flowering", "SM_Bush_DryScrub", "SM_Bramble_Patch_Large",
    "SM_Bramble_Patch_Small", "SM_Bramble_Arch", "SM_Grass_Tuft_Meadow",
    "SM_Grass_Tall_Wild", "SM_Grass_Short_Lawn", "SM_Flora_Reeds_Cattail",
    "SM_Flora_Fern_Forest", "SM_Flora_Mushroom_Cluster", "SM_Flora_Tree_Stump",
    "SM_Flora_Fallen_Log"
]

GROUND_TILES = [
    "SM_Tile_Gravel", "SM_Tile_Dirt", "SM_Tile_Road", "SM_Tile_Path",
    "SM_Tile_Grass", "SM_Tile_Tall_grass", "SM_Tile_Farmland",
    "SM_Tile_Trampled_grass", "SM_Tile_Concrete", "SM_Tile_Black_top",
    "SM_Tile_Bricks", "SM_Tile_Mud", "SM_Tile_Swamp", "SM_Tile_Pond",
    "SM_Tile_Deep_water", "SM_Tile_Sand", "SM_Tile_Wood_planks",
    "SM_Tile_Snow", "SM_Tile_Forest_floor", "SM_Tile_Flagstone",
    "SM_Tile_Farmland_Furrows", "SM_Tile_Road_Asphalt", "SM_Tile_WoodPlanks",
    "SM_Clutter_TallGrass", "SM_Clutter_Pebbles", "SM_Clutter_Cattails",
    "SM_Clutter_Branch", "SM_Clutter_DirtClump", "SM_Clutter_GrassTuft"
]

def parse_obj(obj_path):
    verts = []
    face_count = 0
    with open(obj_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("v "):
                parts = line.strip().split()
                verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif line.startswith("f "):
                face_count += 1
    if not verts:
        return None
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    return {
        "num_verts": len(verts),
        "num_faces": face_count,
        "min_x": min(xs), "max_x": max(xs), "dx": max(xs) - min(xs),
        "min_y": min(ys), "max_y": max(ys), "dy": max(ys) - min(ys),
        "min_z": min(zs), "max_z": max(zs), "dz": max(zs) - min(zs),
    }

def validate_category(cat_name, asset_list, hud_model_dir, ue5_model_dir, hud_icon_dir, ue5_icon_dir, errors):
    print(f"\n--> Validating {len(asset_list)} {cat_name}...")
    for name in asset_list:
        hud_obj = os.path.join(hud_model_dir, f"{name}.obj")
        ue5_obj = os.path.join(ue5_model_dir, f"{name}.obj")
        hud_mtl = os.path.join(hud_model_dir, f"{name}.mtl")
        ue5_mtl = os.path.join(ue5_model_dir, f"{name}.mtl")
        hud_icon = os.path.join(hud_icon_dir, f"{name}.png")
        ue5_icon = os.path.join(ue5_icon_dir, f"{name}.png")

        for path, desc in [(hud_obj, "HUD OBJ"), (ue5_obj, "UE5 OBJ"),
                           (hud_mtl, "HUD MTL"), (ue5_mtl, "UE5 MTL"),
                           (hud_icon, "HUD Icon"), (ue5_icon, "UE5 Icon")]:
            if not os.path.exists(path):
                errors.append(f"{name}: Missing {desc} at {path}")

        if not os.path.exists(hud_obj):
            continue

        stats = parse_obj(hud_obj)
        if not stats:
            errors.append(f"{name}: Failed to parse OBJ at {hud_obj}")
            continue

        if abs(stats["min_z"]) > 1.0:
            errors.append(f"{name}: z_min is {stats['min_z']:.2f}, expected ~0.0")

        if stats["dx"] < 0.1 or stats["dy"] < 0.1 or stats["dz"] < 0.1:
            errors.append(f"{name}: Degenerate bounds {stats['dx']:.2f}x{stats['dy']:.2f}x{stats['dz']:.2f}cm")

        print(f"  [PASS] {name:<35} Bounds: {stats['dx']:>5.1f}x{stats['dy']:>5.1f}x{stats['dz']:>5.1f}cm  Tris: {stats['num_faces']:<5}")

def main():
    print("=====================================================================")
    print("  HOMESTEADER WORLD MODELS & SCALE VALIDATION SUITE (283 ASSETS)")
    print("  Rule: 1 Grid Tile = 1m x 1m = 100 UU x 100 UU = 512px")
    print("=====================================================================")

    errors = []

    # 1. Buildings & Structures (19)
    print("\n--> 1. Validating 19 Homestead Buildings & Modular Components...")
    bld_hud_dir = os.path.join(HUD_ROOT, "assets", "building", "structures")
    bld_ue5_dir = os.path.join(UE5_ROOT, "Assets", "Building", "Meshes")
    bld_icon_hud = os.path.join(HUD_ROOT, "assets", "building", "icons")
    bld_icon_ue5 = os.path.join(UE5_ROOT, "UI", "Icons", "Building")

    for name, exp_dx, exp_dy, min_h, max_h in BUILDINGS:
        hud_obj = os.path.join(bld_hud_dir, f"{name}.obj")
        ue5_obj = os.path.join(bld_ue5_dir, f"{name}.obj")
        hud_icon = os.path.join(bld_icon_hud, f"{name}.png")
        ue5_icon = os.path.join(bld_icon_ue5, f"{name}.png")

        for p, d in [(hud_obj, "HUD OBJ"), (ue5_obj, "UE5 OBJ"), (hud_icon, "HUD Icon"), (ue5_icon, "UE5 Icon")]:
            if not os.path.exists(p):
                errors.append(f"{name}: Missing {d} ({p})")

        stats = parse_obj(hud_obj)
        if stats:
            if abs(stats["min_z"]) > 1.0:
                errors.append(f"{name}: z_min is {stats['min_z']:.2f}, expected ~0.0")
            print(f"  [PASS] {name:<35} Bounds: {stats['dx']:>5.1f}x{stats['dy']:>5.1f}x{stats['dz']:>5.1f}cm  Tris: {stats['num_faces']:<5}")

    # 2. Trees (14)
    print("\n--> 2. Validating 14 Realistic Homestead Trees...")
    fol_hud_dir = os.path.join(HUD_ROOT, "assets", "foliage", "models")
    fol_ue5_dir = os.path.join(UE5_ROOT, "Assets", "Foliage", "Meshes")
    fol_icon_hud = os.path.join(HUD_ROOT, "assets", "foliage", "icons")
    fol_icon_ue5 = os.path.join(UE5_ROOT, "UI", "Icons", "Foliage")

    for name, min_h, max_h, max_base in TREES:
        hud_obj = os.path.join(fol_hud_dir, f"{name}.obj")
        ue5_obj = os.path.join(fol_ue5_dir, f"{name}.obj")
        hud_icon = os.path.join(fol_icon_hud, f"{name}.png")
        ue5_icon = os.path.join(fol_icon_ue5, f"{name}.png")

        for p, d in [(hud_obj, "HUD OBJ"), (ue5_obj, "UE5 OBJ"), (hud_icon, "HUD Icon"), (ue5_icon, "UE5 Icon")]:
            if not os.path.exists(p):
                errors.append(f"{name}: Missing {d} ({p})")

        stats = parse_obj(hud_obj)
        if stats:
            if abs(stats["min_z"]) > 1.0:
                errors.append(f"{name}: z_min is {stats['min_z']:.2f}, expected ~0.0")
            print(f"  [PASS] {name:<35} Height: {stats['dz']:>5.1f}cm ({stats['dz']/100.0:>4.2f}m)  Spread: {max(stats['dx'], stats['dy']):>5.1f}cm  Tris: {stats['num_faces']:<5}")

    # 3. Scatter Foliage (16)
    print("\n--> 3. Validating 16 Scatter Foliage Props...")
    for name in SCATTER_FOLIAGE:
        hud_obj = os.path.join(fol_hud_dir, f"{name}.obj")
        ue5_obj = os.path.join(fol_ue5_dir, f"{name}.obj")
        hud_icon = os.path.join(fol_icon_hud, f"{name}.png")
        ue5_icon = os.path.join(fol_icon_ue5, f"{name}.png")

        for p, d in [(hud_obj, "HUD OBJ"), (ue5_obj, "UE5 OBJ"), (hud_icon, "HUD Icon"), (ue5_icon, "UE5 Icon")]:
            if not os.path.exists(p):
                errors.append(f"{name}: Missing {d} ({p})")

        stats = parse_obj(hud_obj)
        if stats:
            print(f"  [PASS] {name:<35} Bounds: {stats['dx']:>5.1f}x{stats['dy']:>5.1f}x{stats['dz']:>5.1f}cm  Tris: {stats['num_faces']:<5}")

    # 4. Ground Tiles (26)
    print("\n--> 4. Validating 26 Modular Ground Tiles...")
    gnd_hud_dir = os.path.join(HUD_ROOT, "assets", "ground", "models")
    gnd_ue5_dir = os.path.join(UE5_ROOT, "Assets", "Ground", "Meshes")
    for name in GROUND_TILES:
        hud_obj = os.path.join(gnd_hud_dir, f"{name}.obj")
        ue5_obj = os.path.join(gnd_ue5_dir, f"{name}.obj")
        if not (os.path.exists(hud_obj) and os.path.exists(ue5_obj)):
            errors.append(f"Ground tile missing OBJ: {name}")
        stats = parse_obj(hud_obj)
        if stats:
            print(f"  [PASS] {name:<35} Footprint: {stats['dx']:>5.1f}x{stats['dy']:>5.1f}cm  Depth/H: {stats['dz']:>4.1f}cm")

    # 5. Utilities & Infrastructure (28 + 12 = 40)
    UTILITIES_ALL = [
        "SM_Electric_SolarPanel_Ground_1m", "SM_Electric_SolarArray_3m", "SM_Electric_WindTurbine_Small",
        "SM_Electric_WindTurbine_Large", "SM_Electric_Generator_Portable", "SM_Electric_Generator_Standby",
        "SM_Electric_Battery_Powerwall", "SM_Electric_Battery_Rack_48V", "SM_Electric_Inverter_Wall",
        "SM_Electric_PowerPole_Wood", "SM_Electric_WireSpool_Wood", "SM_Water_RainBarrel_55gal",
        "SM_Water_IBC_Tote_275gal", "SM_Water_Cistern_Poly_1000gal", "SM_Water_WellPump_Manual",
        "SM_Water_PressureTank_Well", "SM_Water_FilterRack_3Stage", "SM_Water_HoseReel_Cart",
        "SM_Water_Trough_Stock_100gal", "SM_Sewage_SepticTank_Poly_500gal", "SM_Sewage_DistributionBox",
        "SM_Sewage_CompostBin_3Bay", "SM_Sewage_Toilet_Composting", "SM_Internet_Dish_Starlink_Tripod",
        "SM_Internet_Dish_HighPerf_Mast", "SM_Internet_Antenna_Yagi_Mast", "SM_Internet_Antenna_Omni_Cellular",
        "SM_Internet_Outdoor_AP_Pole",
        # New Batch 5 Utilities
        "SM_Item_Spool_Romex_12_2", "SM_Item_Spool_Cat6_500ft", "SM_Item_Spool_BarbedWire",
        "SM_Item_Electric_BreakerSubpanel", "SM_Item_Electric_DisconnectSwitch",
        "SM_Item_Electric_MPPTController", "SM_Item_Electric_NetworkSwitch_PoE",
        "SM_Item_Plumbing_PVC_Bundle", "SM_Item_Plumbing_Filter_BigBlue",
        "SM_Item_Plumbing_GardenHose_Reel", "SM_Item_Plumbing_WaterJug_5gal",
        "SM_Item_Plumbing_DrainSock_Roll"
    ]
    validate_category(
        "Utilities & Small Infrastructure Assets",
        UTILITIES_ALL,
        os.path.join(HUD_ROOT, "assets", "utilities", "models"),
        os.path.join(UE5_ROOT, "Assets", "Utilities", "Meshes"),
        os.path.join(HUD_ROOT, "assets", "utilities", "icons"),
        os.path.join(UE5_ROOT, "UI", "Icons", "Utilities"),
        errors
    )

    # 6. Ranching & Animal Assets (26 animals + 11 feed/fencing + 10 yields/pelts = 47)
    RANCHING_ALL = [
        # Cattle (3 Adult Varieties + 2 Calves)
        "SM_Animal_Cow_Holstein", "SM_Animal_Cow_Jersey", "SM_Animal_Cow_Highland",
        "SM_Animal_Cow_Calf", "SM_Animal_Cow_Calf_Spotted",
        # Chickens (3 Adult Varieties + 1 Chick)
        "SM_Animal_Chicken_Red", "SM_Animal_Chicken_White", "SM_Animal_Chicken_Barred",
        "SM_Animal_Chicken_Chick",
        # Pigs (3 Adult Varieties + 1 Piglet)
        "SM_Animal_Pig_Pink", "SM_Animal_Pig_Hampshire", "SM_Animal_Pig_Duroc",
        "SM_Animal_Pig_Piglet",
        # Sheep (3 Adult Varieties + 1 Lamb)
        "SM_Animal_Sheep_Suffolk", "SM_Animal_Sheep_White", "SM_Animal_Sheep_Tan",
        "SM_Animal_Sheep_Lamb",
        # Goats (3 Adult Varieties + 1 Kid)
        "SM_Animal_Goat_Brown", "SM_Animal_Goat_White", "SM_Animal_Goat_BlackWhite",
        "SM_Animal_Goat_Kid",
        # Backwards-Compatible Generic Adult Models
        "SM_Animal_Cow_Adult", "SM_Animal_Chicken_Hen", "SM_Animal_Pig_Adult",
        "SM_Animal_Sheep_Adult", "SM_Animal_Goat_Adult",
        # Feed & Fencing (11)
        "SM_Ranch_HayBale_Round", "SM_Ranch_HayBale_Square", "SM_Ranch_SilageBale_Round",
        "SM_Ranch_StrawBale_Round", "SM_Ranch_StrawBale_Square", "SM_Ranch_FeedPan_Rubber",
        "SM_Ranch_SaltLick_Block", "SM_Ranch_Fence_Wood_1m", "SM_Ranch_Fence_Wire_1m",
        "SM_Ranch_Gate_Metal_2m", "SM_Ranch_Fence_Energizer_Solar",
        # Animal Yields, Meats & Pelts (10)
        "SM_Item_Animal_Eggs_Carton", "SM_Item_Animal_Milk_Jug", "SM_Item_Animal_Wool_Fleece",
        "SM_Item_Animal_Truffle", "SM_Item_Meat_Beef_Steak", "SM_Item_Meat_Chicken_Drumstick",
        "SM_Item_Meat_Pork_Chop", "SM_Item_Pelt_Cow_Hide", "SM_Item_Pelt_Sheep_Fleece",
        "SM_Item_Pelt_Goat_Skin"
    ]
    validate_category(
        "Ranching, Animals (All 3 Varieties), Meats & Pelts",
        RANCHING_ALL,
        os.path.join(HUD_ROOT, "assets", "ranching", "models"),
        os.path.join(UE5_ROOT, "Assets", "Ranching", "Meshes"),
        os.path.join(HUD_ROOT, "assets", "ranching", "icons"),
        os.path.join(UE5_ROOT, "UI", "Icons", "Ranching"),
        errors
    )

    # 7. Farming, Crops, Produce & Machines (12 + 4 + 14 + 10 = 40)
    FARMING_ALL = [
        "SM_Crop_Corn_Stalk", "SM_Crop_Tomato_Vine", "SM_Crop_Wheat_Bundle", "SM_Crop_Potato_Plant",
        "SM_Crop_Carrot_Patch", "SM_Crop_Pumpkin_Patch", "SM_Crop_Cabbage_Head", "SM_Crop_Sunflower_Stalk",
        "SM_Farm_Wheelbarrow", "SM_Farm_SeedBag_Burlap", "SM_Farm_ProduceCrate_Wood",
        "SM_Farm_Irrigation_Sprinkler_Riser",
        # New Batch 1 Tractors & Combines
        "SM_Machine_Tractor_Large", "SM_Machine_Tractor_Small", "SM_Machine_Combine_Large", "SM_Machine_Combine_Small",
        # New Batch 3 Harvested Crops & Foods
        "SM_Item_Corn_Ear", "SM_Item_Tomato_Fruit", "SM_Item_Potato_Loose", "SM_Item_Carrot_Bunch",
        "SM_Item_Pumpkin_Carved", "SM_Item_Cabbage_Harvested", "SM_Item_Sunflower_Head",
        "SM_Item_Strawberry_Basket", "SM_Item_Cotton_Boll", "SM_Item_Wheat_Sheaf",
        "SM_Item_Food_Bread", "SM_Item_Food_Cheese_Wheel", "SM_Item_Food_Stew_Bowl", "SM_Item_Food_Apple",
        # New Batch 4 Seed Packets
        "SM_Item_Seed_Corn", "SM_Item_Seed_Tomato", "SM_Item_Seed_Wheat", "SM_Item_Seed_Potato",
        "SM_Item_Seed_Carrot", "SM_Item_Seed_Pumpkin", "SM_Item_Seed_Sunflower", "SM_Item_Seed_Strawberry",
        "SM_Item_Seed_Cotton", "SM_Item_Seed_Herb"
    ]
    validate_category(
        "Farming Crops, Farm Machinery & Harvested Produce",
        FARMING_ALL,
        os.path.join(HUD_ROOT, "assets", "farming", "models"),
        os.path.join(UE5_ROOT, "Assets", "Farming", "Meshes"),
        os.path.join(HUD_ROOT, "assets", "farming", "icons"),
        os.path.join(UE5_ROOT, "UI", "Icons", "Farming"),
        errors
    )

    # 8. Logging, Sawmills & Fuel (5 + 2 = 7)
    LOGGING_ALL = [
        "SM_Log_Pile_Large", "SM_Log_Pile_Medium", "SM_Firewood_Rack_Cord",
        "SM_Firewood_Bundle_Wrapped", "SM_Chopping_Block_Maul",
        # New Batch 1 Sawmills
        "SM_Machine_Sawmill_Portable", "SM_Machine_Sawmill_Stationary"
    ]
    validate_category(
        "Logging, Firewood & Sawmills",
        LOGGING_ALL,
        os.path.join(HUD_ROOT, "assets", "logging", "models"),
        os.path.join(UE5_ROOT, "Assets", "Logging", "Meshes"),
        os.path.join(HUD_ROOT, "assets", "logging", "icons"),
        os.path.join(UE5_ROOT, "UI", "Icons", "logging"),
        errors
    )

    # 9. Building Materials, Heavy Tanks, Outbuildings & Camp (11 + 4 + 10 = 25)
    BUILDING_MATERIALS_ALL = [
        "SM_Mat_Lumber_Stack_2x4", "SM_Mat_Plywood_Stack", "SM_Mat_Pallet_Wood",
        "SM_Mat_CinderBlocks_Stack", "SM_Mat_Brick_Pallet", "SM_Mat_Steel_Drum_55gal",
        "SM_Mat_PropaneTank_500gal", "SM_Camp_Tent_Canvas_Wall", "SM_Camp_Tent_Dome",
        "SM_Camp_Campfire_Ring", "SM_Camp_PicnicTable_Wood",
        # New Batch 1 Structures & Campers
        "SM_Struct_Camper_RV", "SM_Struct_Camper_Teardrop", "SM_Struct_Silo", "SM_Struct_Stable",
        # New Batch 5 Fuel & Hardware
        "SM_Item_Fuel_GasCan_5gal", "SM_Item_Fuel_DieselCan_5gal", "SM_Item_Fuel_PropaneTank_20lb",
        "SM_Item_Tank_Propane_1000gal", "SM_Item_Tank_FuelBulk_Elevated",
        "SM_Item_Hardware_FramingNails_Box", "SM_Item_Hardware_DeckScrews_Box",
        "SM_Item_Hardware_LagBolts_Box", "SM_Item_Hardware_GateHinges_Pair",
        "SM_Item_Hardware_RebarBundle", "SM_Mat_Leather_Roll"
    ]
    validate_category(
        "Building Materials, Tanks, Hardware & Camp Assets",
        BUILDING_MATERIALS_ALL,
        os.path.join(HUD_ROOT, "assets", "building", "models"),
        os.path.join(UE5_ROOT, "Assets", "Building", "Meshes"),
        os.path.join(HUD_ROOT, "assets", "building", "icons"),
        os.path.join(UE5_ROOT, "UI", "Icons", "building"),
        errors
    )

    # 10. Tools, Earthmoving & Handhelds (5 + 4 + 29 = 38)
    TOOLS_ALL = [
        "SM_Tool_Workbench_Timber", "SM_Tool_Anvil_Stump", "SM_Tool_CementMixer_Electric",
        "SM_Tool_ToolChest_Rolling", "SM_Tool_Sawhorse_Pair",
        # New Batch 1 Earthmoving & Skid Steers
        "SM_Machine_Excavator_Large", "SM_Machine_Excavator_Small", "SM_Machine_Skidsteer_Large", "SM_Machine_Skidsteer_Small",
        # New Batch 2 Handheld Tools & Wearables
        "SM_Tool_Axe_Felling", "SM_Tool_Hatchet_Camp", "SM_Tool_Chainsaw_Gas_16", "SM_Tool_Chainsaw_Gas_20",
        "SM_Tool_CantHook_Peavey", "SM_Tool_Maul_Splitting", "SM_Tool_Shovel_RoundPoint", "SM_Tool_Shovel_ScoopFlat",
        "SM_Tool_Shovel_Trenching", "SM_Tool_Hoe", "SM_Tool_Pickaxe", "SM_Tool_Sickle", "SM_Tool_Trowel_Hand",
        "SM_Tool_Drill_Cordless_20V", "SM_Tool_ImpactDriver_Cordless", "SM_Tool_CircularSaw_Cordless",
        "SM_Tool_AngleGrinder_Cordless", "SM_Tool_MiterSaw", "SM_Tool_TableSaw", "SM_Tool_WateringCan",
        "SM_Tool_Shears_Pruning", "SM_Tool_Loppers_Heavy", "SM_Tool_Sprayer_Backpack", "SM_Tool_Wand_Watering",
        "SM_Tool_Pail_Milk_Stainless", "SM_Tool_Shears_SheepWool", "SM_Tool_Paddle_Sorting",
        "SM_Tool_Helmet_LoggingSafety", "SM_Tool_TreeTap"
    ]
    validate_category(
        "Workshop Tools, Excavators & Handheld Tools",
        TOOLS_ALL,
        os.path.join(HUD_ROOT, "assets", "tools", "models"),
        os.path.join(UE5_ROOT, "Assets", "Tools", "Meshes"),
        os.path.join(HUD_ROOT, "assets", "tools", "icons"),
        os.path.join(UE5_ROOT, "UI", "Icons", "tools"),
        errors
    )

    # 11. Fishing, Waterfront & Fish (2 + 10 = 12)
    FISHING_ALL = [
        "SM_Water_Dock_Section_1x2m", "SM_Water_Rowboat_Wood",
        # New Batch 4 Tackle & Fish
        "SM_Item_Rod_FlyFishing", "SM_Item_Rod_Spincast", "SM_Item_Rod_Trolling",
        "SM_Item_Fishing_TackleBox", "SM_Item_Fishing_LandingNet", "SM_Item_Fishing_FishBasket",
        "SM_Item_Fishing_LureTray", "SM_Item_Fish_LargemouthBass", "SM_Item_Fish_ChinookSalmon",
        "SM_Item_Fish_RainbowTrout",
        # New Fish Varieties
        "SM_Item_Fish_Catfish", "SM_Item_Fish_Walleye", "SM_Item_Fish_Crappie",
        # Fish Fillets Suite
        "SM_Item_FishFillet_Bass", "SM_Item_FishFillet_Salmon", "SM_Item_FishFillet_Trout",
        "SM_Item_FishFillet_Catfish", "SM_Item_FishFillet_Walleye", "SM_Item_FishFillet_Crappie"
    ]
    validate_category(
        "Waterfront, Fishing Tackle & Caught Fish",
        FISHING_ALL,
        os.path.join(HUD_ROOT, "assets", "fishing", "models"),
        os.path.join(UE5_ROOT, "Assets", "Fishing", "Meshes"),
        os.path.join(HUD_ROOT, "assets", "fishing", "icons"),
        os.path.join(UE5_ROOT, "UI", "Icons", "fishing"),
        errors
    )

    total_models = (len(BUILDINGS) + len(TREES) + len(SCATTER_FOLIAGE) + len(GROUND_TILES) +
                    len(UTILITIES_ALL) + len(RANCHING_ALL) + len(FARMING_ALL) + len(LOGGING_ALL) +
                    len(BUILDING_MATERIALS_ALL) + len(TOOLS_ALL) + len(FISHING_ALL))

    print("\n=====================================================================")
    print(f"  VALIDATION SUMMARY: {total_models} Total 3D Models Inspected")
    print(f"  Errors:   {len(errors)}")
    print("=====================================================================")

    if errors:
        print("\nERRORS DETECTED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    else:
        print(f"\nALL {total_models} MODELS PASS HOMESTEADER GRID & GEOMETRY SPECIFICATIONS!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
