#!/usr/bin/env python3
"""
build_complete_index_html.py
Regenerates gallery/index.html with:
1. Sleek, responsive Sticky Sub-Navigation Bar for 1-click instant section jumping.
2. Complete 384-Item Icon Gallery (378 DataTable items + 6 3D UI indicators) with 12 category filters.
3. Complete 295 3D World Models Suite across 10 dedicated sections with accurate metric dimensions, tri counts, OBJ/MTL downloads, and filter buttons.
4. Clean HUD interactive simulation with 100% valid icon references (zero broken or quarantined links).
"""

import os
import csv
import json
import re

# tools/ sits at the repo root, so the project root is one level up.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUD_ROOT = PROJECT_ROOT  # legacy alias - keep old joins working
UE5_ROOT = r"c:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader"
INDEX_PATH = os.path.join(HUD_ROOT, "gallery", "index.html")
CSV_PATH = os.path.join(UE5_ROOT, "Data", "DT_Items.csv")

def parse_obj(obj_path):
    verts = []
    face_count = 0
    if not os.path.exists(obj_path):
        return None
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
        "dx": max(xs) - min(xs),
        "dy": max(ys) - min(ys),
        "dz": max(zs) - min(zs),
        "tris": face_count
    }

def get_asset_info(asset_id, name, cat, desc, model_dir_rel):
    obj_path = os.path.join(HUD_ROOT, model_dir_rel, f"{asset_id}.obj")
    stats = parse_obj(obj_path)
    if stats:
        dx, dy, dz = stats["dx"], stats["dy"], stats["dz"]
        tris = stats["tris"]
        footprint = f"{dx/100.0:.1f}×{dy/100.0:.1f}m ({dx:.0f}×{dy:.0f}cm)"
        height = f"{dz:.0f}cm"
    else:
        footprint = "1.0×1.0m (100×100cm)"
        height = "100cm"
        tris = 100
    return {
        "id": asset_id,
        "name": name,
        "cat": cat,
        "footprint": footprint,
        "height": height,
        "tris": tris,
        "desc": desc
    }

print("Loading DataTable items from CSV...")
items_list = []
with open(CSV_PATH, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    for r in reader:
        item_id = r[0]
        disp_name = r[2]
        desc = r[3]
        dt_cat = r[4]
        
        # Classify into UI filter categories
        cat = "building"
        lid = item_id.lower()
        if any(w in lid for w in ["seed", "crop", "fertilizer", "soil", "plant", "garden"]):
            cat = "farming"
        elif any(w in lid for w in ["cow", "chicken", "pig", "sheep", "goat", "animal", "egg", "milk", "feed", "wool", "truffle"]):
            cat = "ranching"
        elif any(w in lid for w in ["bread", "cheese", "stew", "apple", "meat", "fillet", "food", "pork", "beef"]):
            cat = "food"
        elif any(w in lid for w in ["fish", "rod", "lure", "bait", "hook", "tackle", "boat", "dock"]):
            cat = "fishing"
        elif any(w in lid for w in ["log", "firewood", "lumber", "saw", "chainsaw", "cant", "maul", "timber"]):
            cat = "logging"
        elif any(w in lid for w in ["tool", "hoe", "shovel", "pickaxe", "hammer", "wrench", "drill", "shears", "trowel", "tap"]):
            cat = "tools"
        elif any(w in lid for w in ["solar", "generator", "battery", "electric", "power", "turbine", "inverter", "romex"]):
            cat = "electricity"
        elif any(w in lid for w in ["water", "pump", "tank", "filter", "hose", "cistern", "barrel", "pipe"]):
            cat = "water"
        elif any(w in lid for w in ["septic", "sewage", "toilet", "compost"]):
            cat = "sewage"
        elif any(w in lid for w in ["dish", "antenna", "internet", "cat6", "wifi", "router", "starlink"]):
            cat = "internet"
        elif any(w in lid for w in ["clutter", "branch", "clump", "tuft", "pebble"]):
            cat = "clutter"
        elif any(w in lid for w in ["pelt", "hide", "feather", "mat_", "brick", "hardware", "nail", "screw", "bolt"]):
            cat = "building"
            
        items_list.append({
            "id": item_id,
            "name": disp_name,
            "cat": cat,
            "desc": desc,
            "dtCat": dt_cat
        })

# Append 3D HUD Indicators
hud_indicators = [
    {"id": "icon_coin", "name": "Gold Coin ($)", "cat": "hud", "desc": "Embossed 3D faceted gold currency coin", "dtCat": "HUD"},
    {"id": "icon_heart", "name": "Health Indicator", "cat": "hud", "desc": "Ruby red 3D faceted health heart", "dtCat": "HUD"},
    {"id": "icon_stamina", "name": "Stamina Bolt", "cat": "hud", "desc": "Emerald green 3D faceted energy lightning bolt", "dtCat": "HUD"},
    {"id": "icon_water", "name": "Hydration Droplet", "cat": "hud", "desc": "Cyan crystal 3D faceted water droplet", "dtCat": "HUD"},
    {"id": "icon_battery", "name": "Energy Battery", "cat": "hud", "desc": "Industrial 3D faceted battery cell with brass cap", "dtCat": "HUD"},
    {"id": "icon_solar", "name": "Sundial Solar Medallion", "cat": "hud", "desc": "Amber 3D faceted sun medallion with pointer", "dtCat": "HUD"},
]
items_list.extend(hud_indicators)
print(f"Total icon items cataloged: {len(items_list)}")

print("Compiling 3D World Model definitions...")

# 1. GROUND TILES (29)
ground_names = [
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
ground_items = []
for name in ground_names:
    cat = "clutter" if "Clutter" in name else "tiles"
    clean_name = name.replace("SM_Tile_", "").replace("SM_Clutter_", "").replace("_", " ").title()
    ground_items.append(get_asset_info(name, clean_name, cat, f"Modular {clean_name} terrain asset", "assets/ground/models"))

# 2. BUILDINGS (19)
building_defs = [
    ("SM_Building_Outhouse", "Homestead Outhouse", "prefabs", "Rustic timber outhouse with crescent vent door"),
    ("SM_Building_WellHouse", "Covered Well House", "prefabs", "Stone well base with timber gable roof & winch"),
    ("SM_Building_ToolShed", "Storage Tool Shed", "prefabs", "Slanted roof weatherboard garden storage shed"),
    ("SM_Building_ChickenCoop", "Homestead Chicken Coop", "prefabs", "Raised timber chicken coop with ramp and roost doors"),
    ("SM_Building_Woodshed", "Seasoned Woodshed", "prefabs", "3-sided timber firewood seasoning woodshed"),
    ("SM_Building_WaterTower", "Timber Water Tower (7m)", "prefabs", "Heavy timber trestle tower with cedar stave water tank"),
    ("SM_Building_RootCellar", "Bunkered Root Cellar", "prefabs", "Earth-sheltered earthen mound root cellar with cellar doors"),
    ("SM_Building_Greenhouse", "Glazed Greenhouse (6m)", "prefabs", "Timber frame gable greenhouse with glass window panes"),
    ("SM_Building_LogCabin", "Homestead Log Cabin (7m)", "prefabs", "Hand-hewn log cabin with stone chimney & covered porch"),
    ("SM_Building_SmallBarn", "Gambrel Timber Barn (10m)", "prefabs", "Classic 2-story red gambrel livestock & hay barn"),
    ("SM_Part_Wall_Wood_1m", "Wood Wall Section (1m)", "modular", "Interlocking chinked timber wall segment (1x2.4m)"),
    ("SM_Part_Wall_Doorway_1m", "Wall with Doorway (1m)", "modular", "Timber wall section with framed doorway cutout"),
    ("SM_Part_Wall_Window_1m", "Wall with Window (1m)", "modular", "Chinked timber wall segment with framed glass window"),
    ("SM_Part_Door_Wood", "Rough-Sawn Wood Door", "modular", "Hinged rough-sawn timber plank door with cross-buck"),
    ("SM_Part_Floor_Wood_1m", "Wood Plank Floor (1m)", "modular", "Tongue-and-groove timber floor foundation tile"),
    ("SM_Part_Floor_Stone_1m", "Stone Slab Floor (1m)", "modular", "Heavy hewn masonry fieldstone floor tile"),
    ("SM_Part_Roof_Slope_1m", "Sloped Cedar Roof (1m)", "modular", "45-degree angled cedar shake roof segment"),
    ("SM_Part_Roof_Ridge_1m", "Roof Ridge Cap (1m)", "modular", "Interlocking cedar shingle roof ridge cap piece"),
    ("SM_Part_Stairs_Wood_1m", "Timber Steps (1m)", "modular", "Heavy notched timber stringer stairs (1m rise)")
]
building_items = [get_asset_info(d[0], d[1], d[2], d[3], "assets/building/structures") for d in building_defs]

# 3. FOLIAGE & VEGETATION (30)
foliage_defs = [
    ("SM_Tree_Oak_Large", "Large White Oak Tree (6.5m)", "trees", "Sprawling hardwood deciduous oak canopy"),
    ("SM_Tree_Oak_Medium", "Medium Field Oak (5.0m)", "trees", "Medium canopy deciduous oak tree"),
    ("SM_Tree_Oak_Small", "Young Oak Sapling (3.2m)", "trees", "Young juvenile oak sapling with green foliage"),
    ("SM_Tree_Oak_Autumn", "Autumn Golden Oak (5.4m)", "trees", "Vibrant amber autumn foliage oak shade tree"),
    ("SM_Tree_Pine_Tall", "Towering Pine (8.6m)", "trees", "Evergreen conifer with tiered boughs"),
    ("SM_Tree_Pine_Medium", "Medium Evergreen Pine (5.6m)", "trees", "Dense evergreen conifer tree"),
    ("SM_Tree_Pine_Small", "Young Pine Tree (3.6m)", "trees", "Young homestead evergreen conifer pine"),
    ("SM_Tree_Birch_Tall", "Paper Birch Tall (6.8m)", "trees", "Slender white paper birch tree with fluttering leaves"),
    ("SM_Tree_Birch_Medium", "Paper Birch Medium (4.8m)", "trees", "Medium white paper birch tree"),
    ("SM_Tree_Apple", "Fruiting Apple Tree (4.4m)", "trees", "Low-branching orchard apple tree with red fruit"),
    ("SM_Tree_Willow", "Weeping Willow (6.0m)", "trees", "Cascading drooping willow branch canopy"),
    ("SM_Tree_Dead_Snag", "Weathered Dead Snag (4.7m)", "trees", "Barkless lightning-struck forest wildlife snag"),
    ("SM_Tree_Maple", "Sugar Maple Tree (7.4m)", "trees", "Vibrant autumn red sugar maple shade tree"),
    ("SM_Tree_Poplar_Columnar", "Columnar Poplar (9.6m)", "trees", "Narrow windbreak columnar poplar tree"),
    ("SM_Bush_Round_Large", "Large Round Shrub (1.5m)", "bushes", "Dense spherical green landscape bush"),
    ("SM_Bush_Round_Medium", "Medium Round Shrub (1.0m)", "bushes", "Medium rounded mounding foliage shrub"),
    ("SM_Bush_Berry", "Wild Berry Bramble Bush", "bushes", "Thorny berry thicket with ripe homestead fruit"),
    ("SM_Bush_Flowering", "Flowering Garden Shrub", "bushes", "Rounded mounding ornamental flowering shrub"),
    ("SM_Bush_DryScrub", "Arid Scrub Bush", "bushes", "Hardy desert scrub brush cluster"),
    ("SM_Bramble_Patch_Large", "Dense Thorny Bramble (3m)", "brambles", "Impenetrable homestead perimeter thorn hedge"),
    ("SM_Bramble_Patch_Small", "Low Bramble Thick (1.5m)", "brambles", "Understory forest briar bramble cluster"),
    ("SM_Bramble_Arch", "Arched Wild Briar Canopy", "brambles", "Natural arched overhanging trail briar runner"),
    ("SM_Grass_Tuft_Meadow", "Flowering Meadow Grass", "grasses", "Tuft of lush pasture grass with yellow wildflowers"),
    ("SM_Grass_Tall_Wild", "Tall Prairie Switchgrass", "grasses", "Waist-high feathering wind pasture grass"),
    ("SM_Grass_Short_Lawn", "Trimmed Turf Grass Tuft", "grasses", "Dense manicured homestead yard lawn tuft"),
    ("SM_Flora_Reeds_Cattail", "Freshwater Pond Cattails", "features", "Stand of wetland cattail reeds with brown seed heads"),
    ("SM_Flora_Fern_Forest", "Woodland Ostrich Fern", "features", "Erect arching fiddlehead forest fern crown"),
    ("SM_Flora_Mushroom_Cluster", "Forest Chanterelle Cluster", "features", "Cluster of golden wild forest chanterelle mushrooms"),
    ("SM_Flora_Tree_Stump", "Axe-Cut Tree Stump", "features", "Freshly axe-notched timber felling stump"),
    ("SM_Flora_Fallen_Log", "Mossy Fallen Log (3.5m)", "features", "Fallen forest nurse log with bracket fungi")
]
foliage_items = [get_asset_info(d[0], d[1], d[2], d[3], "assets/foliage/models") for d in foliage_defs]

# 4. UTILITIES (40)
utility_defs = [
    ('SM_Electric_SolarPanel_Ground_1m', 'Ground Solar Panel (1m)', 'electricity', '100W ground-mount tilted solar panel on galvanized frame'),
    ('SM_Electric_SolarArray_3m', 'Commercial Solar Array (3m)', 'electricity', 'Commercial 3-panel off-grid solar array on concrete piers'),
    ('SM_Electric_WindTurbine_Small', '400W Wind Turbine', 'electricity', '400W 3-blade wind turbine with tail vane on 4.5m guyed mast'),
    ('SM_Electric_WindTurbine_Large', '3kW Wind Turbine', 'electricity', '3kW heavy-duty wind turbine on 8m lattice steel tower'),
    ('SM_Electric_Generator_Portable', 'Portable Gas Generator', 'electricity', 'Gas portable inverter generator with steel roll cage'),
    ('SM_Electric_Generator_Standby', 'Standby Diesel Genset', 'electricity', 'Commercial diesel backup genset on concrete pad'),
    ('SM_Electric_Battery_Powerwall', 'Home Battery Powerwall', 'electricity', 'Wall-mounted 10kWh home energy storage battery'),
    ('SM_Electric_Battery_Rack_48V', '48V Battery Server Rack', 'electricity', '4-module 48V server rack lithium battery bank'),
    ('SM_Electric_Inverter_Wall', 'Hybrid Solar Inverter', 'electricity', 'Pure sine wave off-grid hybrid inverter charger'),
    ('SM_Electric_PowerPole_Wood', 'Utility Power Pole (6.5m)', 'electricity', 'Creosote utility power pole with crossarm & insulators'),
    ('SM_Electric_WireSpool_Wood', 'Heavy Wire Spool Reel', 'electricity', 'Heavy wooden electrical cable reel with copper wiring'),
    ('SM_Item_Spool_Romex_12_2', 'Romex 12/2 Cable Spool (250ft)', 'electricity', '250ft spool of 12/2 solid copper Romex NM-B wire'),
    ('SM_Item_Spool_Cat6_500ft', 'Cat6 Cable Spool (500ft)', 'electricity', '500ft spool of direct-burial shielded Cat6 cable'),
    ('SM_Item_Spool_BarbedWire', 'Barbed Wire Spool (1320ft)', 'electricity', '1/4-mile spool of high-tensile 4-point barbed wire'),
    ('SM_Item_Electric_BreakerSubpanel', '100A Breaker Subpanel', 'electricity', '100-Amp outdoor rainproof electrical subpanel'),
    ('SM_Item_Electric_DisconnectSwitch', '60A Disconnect Switch', 'electricity', '60-Amp exterior knife blade disconnect switch'),
    ('SM_Item_Electric_MPPTController', '60A MPPT Charge Controller', 'electricity', 'High-efficiency MPPT solar charge controller with LCD'),
    ('SM_Item_Electric_NetworkSwitch_PoE', '8-Port Gigabit PoE+ Switch', 'electricity', 'Hardened 8-port Gigabit PoE+ network switch'),
    ('SM_Water_RainBarrel_55gal', '55-Gal Poly Rain Barrel', 'water', '55-gallon blue poly rain barrel on pedestal'),
    ('SM_Water_IBC_Tote_275gal', '275-Gal Caged IBC Tote', 'water', '275-gallon caged IBC water tote on pallet base'),
    ('SM_Water_Cistern_Poly_1000gal', '1000-Gal Poly Cistern', 'water', '1000-gallon heavy ribbed dark green water cistern'),
    ('SM_Water_WellPump_Manual', 'Manual Pitcher Well Pump', 'water', 'Cast-iron pitcher pump on timber well cover'),
    ('SM_Water_PressureTank_Well', 'Well Pump & Pressure Tank', 'water', 'Vertical bladder pressure tank with mounted jet pump'),
    ('SM_Water_FilterRack_3Stage', '3-Stage Water Filter Rack', 'water', '3-stage Big Blue sediment and carbon filtration rack'),
    ('SM_Water_HoseReel_Cart', 'Mobile Hose Reel Cart', 'water', 'Portable wheeled hose reel cart with green hose'),
    ('SM_Water_Trough_Stock_100gal', '100-Gal Stock Tank Trough', 'water', 'Galvanized oval livestock drinking trough with float valve'),
    ('SM_Item_Plumbing_PVC_Bundle', 'PVC Pipe Bundle (10ft)', 'water', 'Bundle of five Schedule 40 white PVC pipes'),
    ('SM_Item_Plumbing_Filter_BigBlue', 'Big Blue Filter Cartridge', 'water', '20-inch sediment filter replacement cartridge'),
    ('SM_Item_Plumbing_GardenHose_Reel', 'Garden Hose (50ft)', 'water', 'Heavy-duty 50-foot coiled green farm hose'),
    ('SM_Item_Plumbing_WaterJug_5gal', '5-Gallon Poly Water Jug', 'water', 'Food-grade emergency drinking water jug with spigot'),
    ('SM_Item_Plumbing_DrainSock_Roll', 'Perforated Drain Sock (100ft)', 'water', '100ft roll of perforated french drain pipe'),
    ('SM_Sewage_SepticTank_Poly_500gal', '500-Gal Poly Septic Tank', 'sewage', '500-gallon ribbed septic tank with dual risers'),
    ('SM_Sewage_DistributionBox', 'Septic Distribution Box', 'sewage', 'Precast concrete septic distribution box with lid'),
    ('SM_Sewage_CompostBin_3Bay', '3-Bay Timber Compost Bin', 'sewage', '3-bay cedar timber homestead compost station'),
    ('SM_Sewage_Toilet_Composting', 'Rustic Composting Toilet', 'sewage', 'Self-contained rustic cedar composting toilet'),
    ('SM_Internet_Dish_Starlink_Tripod', 'Satellite Dish (Tripod)', 'internet', 'Rectangular phased-array satellite dish on tripod'),
    ('SM_Internet_Dish_HighPerf_Mast', 'Satellite Dish (J-Mast)', 'internet', 'High-performance round satellite dish on tall mast'),
    ('SM_Internet_Antenna_Yagi_Mast', 'Cellular Yagi Antenna (3.5m)', 'internet', 'Directional cellular Yagi antenna on 3.5m mast'),
    ('SM_Internet_Antenna_Omni_Cellular', 'Cellular Omni Antenna', 'internet', 'Vertical high-gain cellular omni antenna'),
    ('SM_Internet_Outdoor_AP_Pole', 'Outdoor Wi-Fi AP Pole', 'internet', 'Weatherproof outdoor dual-antenna Wi-Fi access point')
]
utility_items = [get_asset_info(d[0], d[1], d[2], d[3], "assets/utilities/models") for d in utility_defs]

# 5. LIVESTOCK & RANCHING (47)
ranching_defs = [
    ('SM_Animal_Cow_Holstein', 'Holstein Cow', 'animals', 'Dairy cow with iconic black and white spotted coat and horns'),
    ('SM_Animal_Cow_Jersey', 'Jersey Cow', 'animals', 'Caramel tan dairy cow with dark muzzle and pale muzzle ring'),
    ('SM_Animal_Cow_Highland', 'Highland Cow', 'animals', 'Scottish Highland cow with shaggy ginger coat and 110cm horns'),
    ('SM_Animal_Cow_Calf', 'Chestnut Calf', 'animals', 'Young homestead calf with chestnut coat and white star blaze'),
    ('SM_Animal_Cow_Calf_Spotted', 'Spotted Calf', 'animals', 'Young Holstein calf with black and white spotted coat'),
    ('SM_Animal_Chicken_Red', 'Rhode Island Red Hen', 'animals', 'Classic reddish-brown egg-laying hen with bright red comb'),
    ('SM_Animal_Chicken_White', 'White Leghorn Hen', 'animals', 'Pure white homestead hen with tall red comb and yellow beak'),
    ('SM_Animal_Chicken_Barred', 'Barred Rock Hen', 'animals', 'Heritage barred Plymouth Rock hen with zebra-striped plumage'),
    ('SM_Animal_Chicken_Chick', 'Golden Baby Chick', 'animals', 'Fluffy golden-yellow baby down chick with orange feet'),
    ('SM_Animal_Pig_Pink', 'Yorkshire Pig', 'animals', 'Classic pink homestead swine with floppy ears and curly tail'),
    ('SM_Animal_Pig_Hampshire', 'Hampshire Belted Pig', 'animals', 'Black swine featuring a striking solid white shoulder belt'),
    ('SM_Animal_Pig_Duroc', 'Duroc Red Pig', 'animals', 'Muscular deep mahogany-red pig with drooping ears'),
    ('SM_Animal_Pig_Piglet', 'Pink Baby Piglet', 'animals', 'Chubby miniature pink piglet with tiny corkscrew tail'),
    ('SM_Animal_Sheep_Suffolk', 'Suffolk Sheep', 'animals', 'Plush white wool fleece sheep with distinctive jet-black face and legs'),
    ('SM_Animal_Sheep_White', 'White Fleece Sheep', 'animals', 'Solid white wool homestead sheep with pale pinkish face'),
    ('SM_Animal_Sheep_Tan', 'Caramel Tan Sheep', 'animals', 'Natural warm caramel tan wool sheep with brown markings'),
    ('SM_Animal_Sheep_Lamb', 'White Baby Lamb', 'animals', 'Playful young lamb with fluffy white fleece and black mask'),
    ('SM_Animal_Goat_Brown', 'Brown Dairy Goat', 'animals', 'Two-tone brown and cream goat with curved horns and chin beard'),
    ('SM_Animal_Goat_White', 'Saanen White Goat', 'animals', 'All-white Saanen dairy goat with ivory horns and perky ears'),
    ('SM_Animal_Goat_BlackWhite', 'Piebald Goat', 'animals', 'Striking black and white piebald patterned dairy goat'),
    ('SM_Animal_Goat_Kid', 'Spotted Baby Kid', 'animals', 'Spotted baby goat kid with tiny horn buds and perky ears'),
    ('SM_Animal_Cow_Adult', 'Homestead Cow (Default)', 'animals', 'Standard dairy cow world model'),
    ('SM_Animal_Chicken_Hen', 'Homestead Hen (Default)', 'animals', 'Standard egg-laying hen model'),
    ('SM_Animal_Pig_Adult', 'Homestead Pig (Default)', 'animals', 'Standard swine world model'),
    ('SM_Animal_Sheep_Adult', 'Homestead Sheep (Default)', 'animals', 'Standard wool sheep model'),
    ('SM_Animal_Goat_Adult', 'Homestead Goat (Default)', 'animals', 'Standard dairy goat model'),
    ('SM_Ranch_HayBale_Round', 'Round Hay Bale (1.5m)', 'fencing', 'Large net-wrapped golden meadow grass hay bale'),
    ('SM_Ranch_HayBale_Square', 'Square Hay Bale', 'fencing', 'Two-string wire-tied rectangular alfalfa hay bale'),
    ('SM_Ranch_SilageBale_Round', 'Wrapped Silage Round Bale', 'fencing', 'White UV-film wrapped fermented green silage round bale'),
    ('SM_Ranch_StrawBale_Round', 'Round Straw Bedding Bale', 'fencing', 'Clean golden round oat straw bedding bale'),
    ('SM_Ranch_StrawBale_Square', 'Square Straw Bale', 'fencing', 'Clean golden oat straw bedding bale with green twine'),
    ('SM_Ranch_FeedPan_Rubber', 'Rubber Livestock Feed Pan', 'fencing', '15-gallon heavy-duty molded rubber feed pan'),
    ('SM_Ranch_SaltLick_Block', 'Mineral Salt Lick Block', 'fencing', '50lb reddish-brown mineral salt block on timber stand'),
    ('SM_Ranch_Fence_Wood_1m', 'Timber Post & Rail Fence (1m)', 'fencing', 'Rustic 2-rail cedar homestead boundary fence segment'),
    ('SM_Ranch_Fence_Wire_1m', 'T-Post Woven Wire Fence (1m)', 'fencing', 'T-post and woven steel wire livestock barrier fence'),
    ('SM_Ranch_Gate_Metal_2m', 'Tubular Steel Farm Gate (2m)', 'fencing', 'Galvanized 6-bar tubular steel farm gate with latch'),
    ('SM_Ranch_Fence_Energizer_Solar', 'Solar Fence Energizer Unit', 'fencing', 'Solar-powered electric fence charger unit on T-post'),
    ('SM_Item_Meat_Beef_Steak', 'Choice Beef T-Bone Steak', 'yields', 'Raw thick-cut bone-in beef steak with fat marbling'),
    ('SM_Item_Meat_Chicken_Drumstick', 'Poultry Chicken Drumstick', 'yields', 'Raw fresh poultry drumstick with dual bone knuckle'),
    ('SM_Item_Meat_Pork_Chop', 'Heritage Pork Loin Chop', 'yields', 'Raw bone-in center cut pork loin chop with fat cap'),
    ('SM_Item_Pelt_Cow_Hide', 'Cured Spotted Cowhide', 'yields', 'Folded spotted cow pelt with raw edges'),
    ('SM_Item_Pelt_Sheep_Fleece', 'Sheared Sheep Wool Fleece', 'yields', 'Folded dense plush sheep wool fleece pelt'),
    ('SM_Item_Pelt_Goat_Skin', 'Supple Goat Skin Pelt', 'yields', 'Rolled brown goat fur pelt with suede backing'),
    ('SM_Item_Animal_Eggs_Carton', 'Farm Fresh Egg Carton (12ct)', 'yields', 'Molded pulp carton with one dozen fresh farm eggs'),
    ('SM_Item_Animal_Milk_Jug', 'Fresh Whole Milk Jug (1-Gal)', 'yields', 'Glass 1-gallon dairy jug with red foil seal and cap'),
    ('SM_Item_Animal_Wool_Fleece', 'Raw Wool Fleece Bundle', 'yields', 'Dense cloud bundle of raw sheared sheep wool tied with twine'),
    ('SM_Item_Animal_Truffle', 'Black Foraged Truffle', 'yields', 'Rare prized knobby black forest truffle')
]
ranching_items = [get_asset_info(d[0], d[1], d[2], d[3], "assets/ranching/models") for d in ranching_defs]

# 6. FARMING, CROPS, PRODUCE & MACHINERY (40)
farming_defs = [
    ('SM_Crop_Corn_Stalk', 'Sweet Corn Stalk (2.3m)', 'crops', 'Tall mature sweet corn stalk with ripe ears and silk tassels'),
    ('SM_Crop_Tomato_Vine', 'Caged Tomato Vine', 'crops', 'Galvanized wire tomato cage supporting lush vine with red fruit'),
    ('SM_Crop_Wheat_Bundle', 'Ripe Wheat Clump', 'crops', 'Dense cluster of golden mature wheat heads'),
    ('SM_Crop_Potato_Plant', 'Hilled Potato Plant', 'crops', 'Mounded soil hill with dark green leafy potato vine'),
    ('SM_Crop_Carrot_Patch', 'Garden Carrot Patch', 'crops', 'Feathery green carrot tops with orange crowns visible'),
    ('SM_Crop_Pumpkin_Patch', 'Mound Pumpkin Patch', 'crops', 'Trailing vine with broad leaves and ribbed orange field pumpkin'),
    ('SM_Crop_Cabbage_Head', 'Homestead Cabbage Head', 'crops', 'Dense crinkled green cabbage head surrounded by fan leaves'),
    ('SM_Crop_Sunflower_Stalk', 'Giant Sunflower (2.3m)', 'crops', 'Towering mammoth sunflower stalk with massive seed disc'),
    ('SM_Machine_Tractor_Large', 'Heavy Field Tractor (4.1m)', 'machinery', 'Heavy 250HP utility farm tractor with dual rear ag tires & cab'),
    ('SM_Machine_Tractor_Small', 'Compact Farm Tractor (3.1m)', 'machinery', 'Compact 40HP homestead diesel tractor with 4-post ROPS'),
    ('SM_Machine_Combine_Large', 'Heavy Grain Combine Harvester (7.5m)', 'machinery', 'Commercial combine harvester with front reel header & auger'),
    ('SM_Machine_Combine_Small', 'Compact Combine Harvester (5.5m)', 'machinery', 'Compact homestead grain combine with 2.8m grain platform'),
    ('SM_Farm_Wheelbarrow', 'Steel Garden Wheelbarrow', 'equipment', 'Single-wheel steel hopper wheelbarrow with wood handles'),
    ('SM_Farm_SeedBag_Burlap', 'Burlap Grain Seed Bag', 'equipment', 'Tied burlap seed sack with stitched vintage seal'),
    ('SM_Farm_ProduceCrate_Wood', 'Cedar Apple Harvest Crate', 'equipment', 'Slotted bushel crate heaped with ripe red apples'),
    ('SM_Farm_Irrigation_Sprinkler_Riser', 'Impact Sprinkler Riser', 'equipment', 'PVC riser pipe with brass pulsating impact sprinkler head'),
    ('SM_Item_Corn_Ear', 'Sweet Golden Corn Ear', 'produce', 'Freshly picked sweet corn ear with peeled husk leaves'),
    ('SM_Item_Tomato_Fruit', 'Heirloom Vine Tomato', 'produce', 'Ripe plump heirloom beefsteak tomato with green calyx'),
    ('SM_Item_Potato_Loose', 'Russet Baking Potato', 'produce', 'Freshly dug earthy russet baking potato'),
    ('SM_Item_Carrot_Bunch', 'Tied Crisp Carrot Bunch', 'produce', 'Tied bunch of three crisp garden carrots with fresh green tops'),
    ('SM_Item_Pumpkin_Carved', 'Field Harvest Pumpkin', 'produce', 'Heavy ribbed autumn harvest pumpkin with angled stem'),
    ('SM_Item_Cabbage_Harvested', 'Crisp Green Cabbage', 'produce', 'Solid round head of green garden cabbage'),
    ('SM_Item_Sunflower_Head', 'Sunflower Seed Head', 'produce', 'Mature clipped sunflower head packed with black oil seeds'),
    ('SM_Item_Strawberry_Basket', 'Fresh Strawberry Quart Basket', 'produce', 'Veneer wood market basket filled with ripe red strawberries'),
    ('SM_Item_Cotton_Boll', 'Fluffy Cotton Boll', 'produce', 'Natural cotton stem with open 4-lobe fluffy white cotton bolls'),
    ('SM_Item_Wheat_Sheaf', 'Tied Wheat Harvest Sheaf', 'produce', 'Traditional tied shock bundle of ripe golden wheat stalks'),
    ('SM_Item_Food_Bread', 'Artisan Hearth Bread Loaf', 'produce', 'Golden-crusted scored sourdough bakery bread loaf'),
    ('SM_Item_Food_Cheese_Wheel', 'Aged Cheddar Cheese Wheel', 'produce', 'Traditional yellow waxed artisan farmhouse cheddar cheese wheel'),
    ('SM_Item_Food_Stew_Bowl', 'Homestead Vegetable Stew Bowl', 'produce', 'Handmade ceramic bowl filled with hearty hot vegetable stew'),
    ('SM_Item_Food_Apple', 'Crisp Red Honeycrisp Apple', 'produce', 'Freshly picked crisp red eating apple with stem and leaf'),
    ('SM_Item_Seed_Corn', 'Sweet Corn Seed Packet', 'seeds', 'Heirloom seed packet for Golden Bantam sweet corn'),
    ('SM_Item_Seed_Tomato', 'Beefsteak Tomato Seed Packet', 'seeds', 'Seed envelope for Cherokee Purple beefsteak tomatoes'),
    ('SM_Item_Seed_Wheat', 'Winter Wheat Grain Seed Packet', 'seeds', 'Hard red winter wheat seed planting packet'),
    ('SM_Item_Seed_Potato', 'Seed Potato Eyes Packet', 'seeds', 'Certified organic seed potato planting pouch'),
    ('SM_Item_Seed_Carrot', 'Danvers Carrot Seed Packet', 'seeds', 'Danvers half-long heirloom carrot seed packet'),
    ('SM_Item_Seed_Pumpkin', 'Sugar Pie Pumpkin Seed Packet', 'seeds', 'Traditional New England sugar pie pumpkin seeds'),
    ('SM_Item_Seed_Sunflower', 'Mammoth Sunflower Seed Packet', 'seeds', 'Mammoth Russian giant sunflower seed packet'),
    ('SM_Item_Seed_Strawberry', 'Ever-Bearing Strawberry Seed Packet', 'seeds', 'Ever-bearing alpine sweet strawberry seeds'),
    ('SM_Item_Seed_Cotton', 'Upland Cotton Seed Packet', 'seeds', 'Delta upland heirloom white cotton seed packet'),
    ('SM_Item_Seed_Herb', 'Culinary Herb Blend Seed Packet', 'seeds', 'Homestead kitchen garden basil, thyme & oregano seeds')
]
farming_items = [get_asset_info(d[0], d[1], d[2], d[3], "assets/farming/models") for d in farming_defs]

# 7. TOOLS & MACHINERY (37)
tools_defs = [
    ('SM_Machine_Excavator_Large', 'Heavy Hydraulic Excavator (6.5m)', 'earthmoving', 'Commercial 20-ton tracked excavator with boom, arm and bucket'),
    ('SM_Machine_Excavator_Small', 'Compact Mini Excavator (3.3m)', 'earthmoving', 'Rubber-tracked mini excavator with front dozer blade and cab'),
    ('SM_Machine_Skidsteer_Large', 'Heavy Skid Steer Loader (2.8m)', 'earthmoving', 'Tracked heavy skid steer loader with dirt bucket and ROPS canopy'),
    ('SM_Machine_Skidsteer_Small', 'Compact Wheeled Skid Steer (2.2m)', 'earthmoving', '4-wheel compact skid steer loader with standard material bucket'),
    ('SM_Tool_Workbench_Timber', 'Timber Woodworking Workbench', 'fixtures', 'Heavy-duty timber workbench with cast iron vise and tool shelf'),
    ('SM_Tool_Anvil_Stump', 'Blacksmith Anvil on Stump', 'fixtures', 'Cast steel blacksmith anvil strapped to solid hardwood stump'),
    ('SM_Tool_CementMixer_Electric', 'Wheeled Electric Cement Mixer', 'fixtures', 'Orange electric rotating drum cement mixer on wheeled A-frame'),
    ('SM_Tool_ToolChest_Rolling', 'Rolling Mechanic Tool Chest', 'fixtures', 'Red 6-drawer mechanic rolling tool chest with worktop mat'),
    ('SM_Tool_Sawhorse_Pair', 'Pair of Timber Sawhorses', 'fixtures', 'Pair of sturdy timber carpenters\' A-frame sawhorses'),
    ('SM_Tool_Axe_Felling', 'Felling Axe (3.5lb, 36-Inch)', 'handheld', 'Hickory-handled professional felling axe with forged carbon steel head'),
    ('SM_Tool_Hatchet_Camp', 'Camp Hatchet (16-Inch)', 'handheld', 'Compact backpacking and kindling hatchet with carved ash grip'),
    ('SM_Tool_Chainsaw_Gas_16', '16-Inch Gas Chainsaw', 'handheld', '45cc 2-stroke gas chainsaw with 16-inch bar, chain & wrap handle'),
    ('SM_Tool_Chainsaw_Gas_20', '20-Inch Heavy Timber Chainsaw', 'handheld', '60cc heavy timber professional chainsaw with 20-inch guide bar'),
    ('SM_Tool_CantHook_Peavey', 'Logging Peavey Cant Hook', 'handheld', 'Heavy-duty log rolling peavey with forged steel duckbill hook & spike'),
    ('SM_Tool_Maul_Splitting', 'Splitting Maul (8lb, 36-Inch)', 'handheld', '8-pound sledge splitting maul with wedged cheeks for cordwood'),
    ('SM_Tool_Shovel_RoundPoint', 'Round Point Digging Shovel', 'handheld', 'Heavy 14-gauge round point shovel with ash handle'),
    ('SM_Tool_Shovel_ScoopFlat', 'Aluminum Grain & Snow Scoop', 'handheld', 'Large #10 aluminum ribbed grain scoop shovel with D-handle grip'),
    ('SM_Tool_Shovel_Trenching', 'Trenching Shovel (4-Inch)', 'handheld', 'Narrow trenching shovel with V-shaped blade for utility trenches'),
    ('SM_Tool_Hoe', 'Draw Cultivator Garden Hoe', 'handheld', 'Forged swan-neck garden draw hoe for weeding and furrows'),
    ('SM_Tool_Pickaxe', 'Clay Pick & Mattock (5lb)', 'handheld', 'Combination pointed pick and chisel mattock for hardpack and roots'),
    ('SM_Tool_Sickle', 'Harvest Forage Sickle', 'handheld', 'Curved serrated high-carbon steel harvesting sickle with walnut grip'),
    ('SM_Tool_Trowel_Hand', 'Cast Aluminum Hand Trowel', 'handheld', 'Graduated garden hand trowel with depth markings and rubber handle'),
    ('SM_Tool_Drill_Cordless_20V', '20V Brushless Cordless Drill', 'powertools', '20V compact cordless drill driver with lithium battery'),
    ('SM_Tool_ImpactDriver_Cordless', '20V Hex Impact Driver', 'powertools', 'High-torque 1/4-inch hex shank cordless impact driver'),
    ('SM_Tool_CircularSaw_Cordless', '7-1/4-Inch Cordless Circular Saw', 'powertools', 'Brushless framing circular saw with carbide blade and shoe'),
    ('SM_Tool_AngleGrinder_Cordless', '4-1/2-Inch Cordless Angle Grinder', 'powertools', 'Heavy-duty angle grinder with abrasive cutoff wheel & guard'),
    ('SM_Tool_MiterSaw', '10-Inch Sliding Compound Miter Saw', 'powertools', 'Benchtop 10-inch sliding compound miter saw on turntable'),
    ('SM_Tool_TableSaw', 'Jobsite Portable Table Saw', 'powertools', '10-inch jobsite contractor table saw on folding stand with fence'),
    ('SM_Tool_WateringCan', 'Galvanized Steel Watering Can', 'care', 'Classic 2-gallon galvanized sheet steel watering can with brass rose'),
    ('SM_Tool_Shears_Pruning', 'Bypass Garden Pruning Shears', 'care', 'Forged steel bypass pruning secateurs with spring and lock'),
    ('SM_Tool_Loppers_Heavy', 'Heavy Bypass Branch Loppers', 'care', 'Compound action 30-inch bypass tree branch loppers'),
    ('SM_Tool_Sprayer_Backpack', '4-Gallon Backpack Crop Sprayer', 'care', 'Ergonomic 4-gallon chemical crop sprayer with brass wand'),
    ('SM_Tool_Wand_Watering', 'Long-Reach Watering Wand', 'care', '30-inch anodized aluminum watering wand with shutoff valve'),
    ('SM_Tool_Pail_Milk_Stainless', 'Seamless Stainless Steel Milk Pail', 'care', '13-quart seamless 304 stainless steel milking pail with bail'),
    ('SM_Tool_Shears_SheepWool', 'Single-Bow Sheep Wool Shears', 'care', 'Traditional high-carbon spring steel sheep wool shears'),
    ('SM_Tool_Paddle_Sorting', 'Livestock Sorting Rattle Paddle', 'care', 'Vinyl livestock sorting paddle with internal noise shaker beads'),
    ('SM_Tool_Helmet_LoggingSafety', 'Logging Safety Helmet & Mesh Shield', 'care', 'Hi-vis orange arborist hard hat with muffs and face shield'),
    ('SM_Tool_TreeTap', 'Tree Tap & Maple Spile', 'handheld', 'Cast aluminum spile with sap bucket hook for tapping sugar maples')
]
tools_items = [get_asset_info(d[0], d[1], d[2], d[3], "assets/tools/models") for d in tools_defs]

# 8. BUILDING MATERIALS & CAMP (26)
materials_defs = [
    ('SM_Mat_Lumber_Stack_2x4', 'Banded 2x4 Lumber Stack', 'lumber', 'Steel-banded bundle of dimensional 2x4 framing studs on skids'),
    ('SM_Mat_Plywood_Stack', 'CDX Plywood Sheathing Stack', 'lumber', 'Stack of 4x8 CDX plywood sheathing boards on timber runners'),
    ('SM_Mat_Pallet_Wood', 'Standard GMA Shipping Pallet', 'lumber', 'Standard GMA/Euro heavy wooden warehouse shipping pallet'),
    ('SM_Mat_CinderBlocks_Stack', 'Pallet of Concrete Blocks', 'masonry', 'Tiered stack of 2-core hollow concrete cinder blocks on pallet'),
    ('SM_Mat_Brick_Pallet', 'Pallet of Red Clay Bricks', 'masonry', 'Banded pallet of red clay masonry construction bricks'),
    ('SM_Mat_Steel_Drum_55gal', '55-Gallon Steel Oil Drum', 'tanks', 'Blue 55-gallon steel fuel and chemical storage drum with bungs'),
    ('SM_Mat_PropaneTank_500gal', '500-Gallon Propane Torpedo Tank', 'tanks', '500-gallon horizontal torpedo LP gas propane tank on saddles'),
    ('SM_Struct_Camper_RV', 'Vintage Off-Grid Travel Trailer RV (5.9m)', 'structures', 'Tandem-axle vintage camper trailer with hitch and awning'),
    ('SM_Struct_Camper_Teardrop', 'Compact Teardrop Camper (3.0m)', 'structures', 'Lightweight off-road teardrop sleeper trailer with side door'),
    ('SM_Struct_Silo', 'Galvanized Corrugated Grain Silo (9.0m)', 'structures', 'Galvanized corrugated sheet metal farm grain storage silo with ladder'),
    ('SM_Struct_Stable', 'Homestead Livestock Stable Shed (6.0m)', 'structures', '2-stall timber homestead barn stable with dual open Dutch animal pens'),
    ('SM_Item_Fuel_GasCan_5gal', '5-Gallon Poly Gasoline Can', 'fuel', 'OSHA red 5-gallon CARB-compliant plastic gas can with flame arrestor'),
    ('SM_Item_Fuel_DieselCan_5gal', '5-Gallon Poly Diesel Can', 'fuel', 'Yellow 5-gallon polyethylene diesel fuel jerry can with pour spout'),
    ('SM_Item_Fuel_PropaneTank_20lb', '20lb Propane BBQ Cylinder', 'fuel', 'Standard white 20lb refillable LP propane cylinder with OPD valve'),
    ('SM_Item_Tank_Propane_1000gal', '1000-Gallon LP Propane Bullet Tank', 'fuel', 'Heavy 1000-gallon ASME LP gas bullet tank with brass service valves'),
    ('SM_Item_Tank_FuelBulk_Elevated', '300-Gallon Gravity Farm Fuel Tank', 'fuel', 'Elevated 300-gallon diesel storage skid tank with gravity hose'),
    ('SM_Item_Hardware_FramingNails_Box', '16D Framing Nails Box (50lb)', 'hardware', '50lb cardboard carton of 3-1/2-inch smooth shank framing nails'),
    ('SM_Item_Hardware_DeckScrews_Box', '3-Inch Ceramic Deck Screws Tub (5lb)', 'hardware', '5lb plastic contractor tub of Torx T-25 outdoor deck screws'),
    ('SM_Item_Hardware_LagBolts_Box', 'Hex Lag Screws Box (1/2" x 6")', 'hardware', 'Heavy contractor box of 1/2-inch x 6-inch zinc-plated hex lag bolts'),
    ('SM_Item_Hardware_GateHinges_Pair', 'Heavy Heavy-Strap Farm Gate Hinges', 'hardware', 'Pair of forged 12-inch heavy-duty strap hinges with hinge pins'),
    ('SM_Item_Hardware_RebarBundle', '#4 Steel Rebar Bundle (10ft)', 'hardware', 'Bundle of 1/2-inch deformed reinforcing steel rebar rods'),
    ('SM_Mat_Leather_Roll', 'Cured Homestead Leather Roll', 'lumber', 'Roll of vegetable-tanned homestead leather for clothing and tool crafting'),
    ('SM_Camp_Tent_Canvas_Wall', 'Outfitter Wall Tent (2.4×3m)', 'camp', 'Heavy canvas outfitter wall tent with stovepipe flashing elbow'),
    ('SM_Camp_Tent_Dome', 'Geodesic Dome Tent (2×2m)', 'camp', 'Modern 2-person geodesic dome camping tent with crossed poles'),
    ('SM_Camp_Campfire_Ring', 'Natural Stone Campfire Ring', 'camp', 'Circular stone campfire ring with glowing coals and charred logs'),
    ('SM_Camp_PicnicTable_Wood', 'Timber A-Frame Picnic Table', 'camp', 'Heavy timber A-frame park picnic table with attached bench seats')
]
materials_items = [get_asset_info(d[0], d[1], d[2], d[3], "assets/building/models") for d in materials_defs]

# 9. LOGGING, FIREWOOD & SAWMILLS (7)
logging_defs = [
    ('SM_Log_Pile_Large', 'Large Timber Log Pile', 'logging', 'Pyramid stack of 10 large cut timber logs with support chocks'),
    ('SM_Log_Pile_Medium', 'Medium Log Stack', 'logging', 'Stack of 6 cut firewood logs secured between side stakes'),
    ('SM_Firewood_Rack_Cord', 'Full Cord Firewood Rack', 'logging', 'Tubular steel rack stacked full of split seasoned cordwood'),
    ('SM_Firewood_Bundle_Wrapped', 'Wrapped Firewood Bundle', 'logging', 'Shrink-wrapped bundle of kiln-dried firewood with handle strap'),
    ('SM_Chopping_Block_Maul', 'Stump Chopping Block & Maul', 'logging', 'Oak stump chopping block with heavy splitting maul embedded'),
    ('SM_Machine_Sawmill_Portable', 'Towable Trailer Bandsaw Mill (6.5m)', 'sawmills', 'Gas-powered portable bandsaw sawmill mounted on trailer chassis'),
    ('SM_Machine_Sawmill_Stationary', 'Heavy Commercial Timber Sawmill (7.0m)', 'sawmills', 'Heavy stationary timber saw shed mill with structural steel track bed')
]
logging_items = [get_asset_info(d[0], d[1], d[2], d[3], "assets/logging/models") for d in logging_defs]

# 10. WATERFRONT, FISHING, FISH & FILLETS (21)
fishing_defs = [
    ('SM_Water_Dock_Section_1x2m', 'Cedar Dock Section (1×2m)', 'waterfront', 'Modular cedar plank dock section with pilings and mooring cleats'),
    ('SM_Water_Rowboat_Wood', '10ft Wooden Rowing Skiff', 'waterfront', '10-foot cedar lapstrake wooden rowing skiff with oars'),
    ('SM_Item_Rod_FlyFishing', '9ft 5-Weight Fly Fishing Rod & Reel', 'tackle', 'Graphite 9ft fly rod with cork grip and aluminum arbor reel'),
    ('SM_Item_Rod_Spincast', '6ft Medium Spincast Fishing Combo', 'tackle', 'Push-button closed-face spincast reel combo with EVA foam grip'),
    ('SM_Item_Rod_Trolling', '7ft Heavy Lake Trolling Rod', 'tackle', 'Heavy-power conventional trolling rod with level-wind reel'),
    ('SM_Item_Fishing_TackleBox', '3-Tray Cantilever Tackle Box', 'tackle', 'Classic blue 3-tier cantilever plastic tackle box with brass latch'),
    ('SM_Item_Fishing_LandingNet', 'Rubber Mesh Trout Landing Net', 'tackle', 'Teardrop hardwood landing net with knotless rubber mesh'),
    ('SM_Item_Fishing_FishBasket', 'Floating Wire Mesh Fish Basket', 'tackle', 'Galvanized spring-loaded floating wire mesh live fish keeper basket'),
    ('SM_Item_Fishing_LureTray', '18-Compartment Utility Lure Tray', 'tackle', 'Clear polymer tackle organizer tray filled with lures'),
    ('SM_Item_Fish_LargemouthBass', 'Trophy Largemouth Bass (44cm)', 'fish', 'Fresh caught 44cm largemouth bass with green lateral stripe & fins'),
    ('SM_Item_Fish_ChinookSalmon', 'King Chinook Salmon (64cm)', 'fish', 'Chrome silver 64cm trophy king salmon with spotted adipose fin'),
    ('SM_Item_Fish_RainbowTrout', 'Native Rainbow Trout (39cm)', 'fish', 'Stream-caught 39cm rainbow trout with vivid pink side band and black spots'),
    ('SM_Item_Fish_Catfish', 'Channel Catfish (56cm)', 'fish', 'Freshwater channel catfish with whiskers, blue-gray body and white belly'),
    ('SM_Item_Fish_Walleye', 'Trophy Walleye (50cm)', 'fish', 'Predatory golden-olive walleye with glassy eyes and spiny dorsal fin'),
    ('SM_Item_Fish_Crappie', 'Black Crappie (30cm)', 'fish', 'Deep-bodied speckled black crappie panfish from homestead pond'),
    ('SM_Item_FishFillet_Bass', 'Fresh Bass Fillet', 'fillets', 'Clean boneless white meat largemouth bass fillet with skin'),
    ('SM_Item_FishFillet_Salmon', 'Wild Salmon Steak Fillet', 'fillets', 'Thick cut wild Chinook salmon steak with rich orange-pink meat'),
    ('SM_Item_FishFillet_Trout', 'Fresh Trout Fillet', 'fillets', 'Delicate blush pink freshwater rainbow trout fillet'),
    ('SM_Item_FishFillet_Catfish', 'Fresh Catfish Fillet', 'fillets', 'Firm white catfish cutlet fillet, ideal for skillet fry'),
    ('SM_Item_FishFillet_Walleye', 'Prized Walleye Fillet', 'fillets', 'Tender flaky white meat walleye fillet with sweet delicate flavor'),
    ('SM_Item_FishFillet_Crappie', 'Sweet Crappie Panfish Fillet', 'fillets', 'Sweet flaky panfish fillet harvested from fresh catch')
]
fishing_items = [get_asset_info(d[0], d[1], d[2], d[3], "assets/fishing/models") for d in fishing_defs]

print(f"Total 3D models compiled: Ground={len(ground_items)}, Bld={len(building_items)}, Fol={len(foliage_items)}, Utl={len(utility_items)}, Ranch={len(ranching_items)}, Farm={len(farming_items)}, Tools={len(tools_items)}, Mat={len(materials_items)}, Log={len(logging_items)}, Fish={len(fishing_items)}")
total_models = len(ground_items) + len(building_items) + len(foliage_items) + len(utility_items) + len(ranching_items) + len(farming_items) + len(tools_items) + len(materials_items) + len(logging_items) + len(fishing_items)
print(f"TOTAL SUITE 3D MODELS: {total_models}")

# Read existing index.html up to the tabGallery section:
with open(INDEX_PATH, "r", encoding="utf-8") as f:
    full_text = f.read()

# Locate top toolbar and TAB 2 gallery view
# Insert the Sticky Sub-Navigation Bar inside tabGallery right at the top
subnav_html = f"""
    <!-- Sticky Gallery Sub-Navigation Toolbar -->
    <nav class="gallery-subnav" id="gallerySubNav">
      <div class="subnav-container">
        <span class="subnav-title">JUMP TO:</span>
        <div class="subnav-pills">
          <button class="subnav-pill" onclick="jumpToSection('secIcons')">📦 Item Icons <span class="pill-badge">{len(items_list)}</span></button>
          <button class="subnav-pill" onclick="jumpToSection('secGround')">🧱 Ground & Terrain <span class="pill-badge">{len(ground_items)}</span></button>
          <button class="subnav-pill" onclick="jumpToSection('secBuildings')">🏡 Buildings & Architecture <span class="pill-badge">{len(building_items)}</span></button>
          <button class="subnav-pill" onclick="jumpToSection('secFoliage')">🌲 Foliage & Flora <span class="pill-badge">{len(foliage_items)}</span></button>
          <button class="subnav-pill" onclick="jumpToSection('secUtilities')">⚡ Utilities & Grid <span class="pill-badge">{len(utility_items)}</span></button>
          <button class="subnav-pill" onclick="jumpToSection('secRanching')">🐄 Livestock & Ranching <span class="pill-badge">{len(ranching_items)}</span></button>
          <button class="subnav-pill" onclick="jumpToSection('secFarming')">🌾 Farming & Produce <span class="pill-badge">{len(farming_items)}</span></button>
          <button class="subnav-pill" onclick="jumpToSection('secTools')">🛠️ Tools & Excavators <span class="pill-badge">{len(tools_items)}</span></button>
          <button class="subnav-pill" onclick="jumpToSection('secMaterials')">🏕️ Materials & Camp <span class="pill-badge">{len(materials_items)}</span></button>
          <button class="subnav-pill" onclick="jumpToSection('secLogging')">🪓 Logging & Sawmills <span class="pill-badge">{len(logging_items)}</span></button>
          <button class="subnav-pill" onclick="jumpToSection('secFishing')">🎣 Waterfront & Fish <span class="pill-badge">{len(fishing_items)}</span></button>
        </div>
      </div>
    </nav>
"""

# Build all gallery HTML sections
gallery_sections_html = f"""
    {subnav_html}

    <!-- SECTION: Item Icons (384) -->
    <div class="gallery-section" id="secIcons">
      <div class="gallery-title">
        <span>📦 Homesteader Item Icons ({len(items_list)} Items in 3D Low-Poly Faceted Style)</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="res-btn active" id="btnFilterAll" onclick="filterIcons('all')">All ({len(items_list)})</button>
          <button class="res-btn" id="btnFilterFarming" onclick="filterIcons('farming')">Farming</button>
          <button class="res-btn" id="btnFilterRanching" onclick="filterIcons('ranching')">Ranching</button>
          <button class="res-btn" id="btnFilterFood" onclick="filterIcons('food')">Food & Fillets</button>
          <button class="res-btn" id="btnFilterFishing" onclick="filterIcons('fishing')">Fishing</button>
          <button class="res-btn" id="btnFilterBuilding" onclick="filterIcons('building')">Building</button>
          <button class="res-btn" id="btnFilterTools" onclick="filterIcons('tools')">Tools</button>
          <button class="res-btn" id="btnFilterElectricity" onclick="filterIcons('electricity')">Electricity</button>
          <button class="res-btn" id="btnFilterWater" onclick="filterIcons('water')">Water</button>
          <button class="res-btn" id="btnFilterSewage" onclick="filterIcons('sewage')">Sewage</button>
          <button class="res-btn" id="btnFilterInternet" onclick="filterIcons('internet')">Internet</button>
          <button class="res-btn" id="btnFilterClutter" onclick="filterIcons('clutter')">Clutter</button>
          <button class="res-btn" id="btnFilterHud" onclick="filterIcons('hud')">HUD UI</button>
        </div>
      </div>
      <div class="gallery-grid" id="iconGalleryGrid"></div>
    </div>

    <!-- SECTION: Ground Tiles & Clutter (29) -->
    <div class="gallery-section" id="secGround">
      <div class="gallery-title">
        <span>🧱 Modular Ground Tiles, Terrain & Natural Clutter (29 Models & PBR Textures)</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="res-btn active" id="btnFilterGroundAll" onclick="filterGround('all')">All (29)</button>
          <button class="res-btn" id="btnFilterGroundTiles" onclick="filterGround('tiles')">Terrain Tiles (23)</button>
          <button class="res-btn" id="btnFilterGroundClutter" onclick="filterGround('clutter')">Natural Clutter (6)</button>
        </div>
      </div>
      <div class="gallery-grid" id="groundTileGalleryGrid"></div>
    </div>

    <!-- SECTION: Homestead Buildings (19) -->
    <div class="gallery-section" id="secBuildings">
      <div class="gallery-title">
        <span>🏡 Homestead Buildings & Architecture (19 Models & Matching 128×128 Icons)</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="res-btn active" id="btnFilterBuildingAll" onclick="filterBuildings('all')">All (19)</button>
          <button class="res-btn" id="btnFilterBuildingPrefabs" onclick="filterBuildings('prefabs')">Prefabs (10)</button>
          <button class="res-btn" id="btnFilterBuildingModular" onclick="filterBuildings('modular')">Modular Pieces (9)</button>
        </div>
      </div>
      <div class="gallery-grid" id="buildingGalleryGrid"></div>
    </div>

    <!-- SECTION: Foliage & Vegetation (30) -->
    <div class="gallery-section" id="secFoliage">
      <div class="gallery-title">
        <span>🌲 Foliage, Trees & Wild Vegetation (30 Models & Matching 128×128 Icons)</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="res-btn active" id="btnFilterFoliageAll" onclick="filterFoliage('all')">All (30)</button>
          <button class="res-btn" id="btnFilterFoliageTrees" onclick="filterFoliage('trees')">Trees (14)</button>
          <button class="res-btn" id="btnFilterFoliageBushes" onclick="filterFoliage('bushes')">Bushes & Shrubs (6)</button>
          <button class="res-btn" id="btnFilterFoliageBrambles" onclick="filterFoliage('brambles')">Bramble Patches (3)</button>
          <button class="res-btn" id="btnFilterFoliageGrasses" onclick="filterFoliage('grasses')">Grasses (3)</button>
          <button class="res-btn" id="btnFilterFoliageFeatures" onclick="filterFoliage('features')">Forest Floor (4)</button>
        </div>
      </div>
      <div class="gallery-grid" id="foliageGalleryGrid"></div>
    </div>

    <!-- SECTION: Utilities & Infrastructure (40) -->
    <div class="gallery-section" id="secUtilities">
      <div class="gallery-title">
        <span>⚡ Off-Grid Utilities & Infrastructure (40 Models & Matching 128×128 Icons)</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="res-btn active" id="btnFilterUtilityAll" onclick="filterUtilities('all')">All (40)</button>
          <button class="res-btn" id="btnFilterUtilityElectric" onclick="filterUtilities('electricity')">Electricity (18)</button>
          <button class="res-btn" id="btnFilterUtilityWater" onclick="filterUtilities('water')">Water Supply (13)</button>
          <button class="res-btn" id="btnFilterUtilitySewage" onclick="filterUtilities('sewage')">Septic & Compost (4)</button>
          <button class="res-btn" id="btnFilterUtilityNet" onclick="filterUtilities('internet')">Internet & Telecom (5)</button>
        </div>
      </div>
      <div class="gallery-grid" id="utilityGalleryGrid"></div>
    </div>

    <!-- SECTION: Livestock & Ranching (47) -->
    <div class="gallery-section" id="secRanching">
      <div class="gallery-title">
        <span>🐄 3-Variety Livestock & Ranching (47 Models & Matching 128×128 Icons)</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="res-btn active" id="btnFilterRanchAll" onclick="filterRanching('all')">All (47)</button>
          <button class="res-btn" id="btnFilterRanchAnimals" onclick="filterRanching('animals')">Livestock Breeds (26)</button>
          <button class="res-btn" id="btnFilterRanchFencing" onclick="filterRanching('fencing')">Bales & Fencing (11)</button>
          <button class="res-btn" id="btnFilterRanchYields" onclick="filterRanching('yields')">Animal Yields (10)</button>
        </div>
      </div>
      <div class="gallery-grid" id="ranchingGalleryGrid"></div>
    </div>

    <!-- SECTION: Farming, Crops, Produce & Machinery (40) -->
    <div class="gallery-section" id="secFarming">
      <div class="gallery-title">
        <span>🌾 Crops, Heavy Machinery & Harvested Produce (40 Models & Matching 128×128 Icons)</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="res-btn active" id="btnFilterFarmAll" onclick="filterFarming('all')">All (40)</button>
          <button class="res-btn" id="btnFilterFarmCrops" onclick="filterFarming('crops')">Garden Crops (8)</button>
          <button class="res-btn" id="btnFilterFarmMachinery" onclick="filterFarming('machinery')">Tractors & Combines (4)</button>
          <button class="res-btn" id="btnFilterFarmEquip" onclick="filterFarming('equipment')">Farm Tools (4)</button>
          <button class="res-btn" id="btnFilterFarmProduce" onclick="filterFarming('produce')">Harvested Food (14)</button>
          <button class="res-btn" id="btnFilterFarmSeeds" onclick="filterFarming('seeds')">Seed Packets (10)</button>
        </div>
      </div>
      <div class="gallery-grid" id="farmingGalleryGrid"></div>
    </div>

    <!-- SECTION: Workshop Tools & Earthmovers (38) -->
    <div class="gallery-section" id="secTools">
      <div class="gallery-title">
        <span>🛠️ Workshop Fixtures, Excavators & Handheld Tools (38 Models & Matching 128×128 Icons)</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="res-btn active" id="btnFilterToolsAll" onclick="filterTools('all')">All (38)</button>
          <button class="res-btn" id="btnFilterToolsEarthmoving" onclick="filterTools('earthmoving')">Earthmovers (4)</button>
          <button class="res-btn" id="btnFilterToolsFixtures" onclick="filterTools('fixtures')">Shop Fixtures (5)</button>
          <button class="res-btn" id="btnFilterToolsHandheld" onclick="filterTools('handheld')">Forestry & Digging (14)</button>
          <button class="res-btn" id="btnFilterToolsPower" onclick="filterTools('powertools')">Power Tools (6)</button>
          <button class="res-btn" id="btnFilterToolsCare" onclick="filterTools('care')">Care & Safety (9)</button>
        </div>
      </div>
      <div class="gallery-grid" id="toolsGalleryGrid"></div>
    </div>

    <!-- SECTION: Building Materials & Camp (26) -->
    <div class="gallery-section" id="secMaterials">
      <div class="gallery-title">
        <span>🏕️ Building Materials, Hardware & Camp (26 Models & Matching 128×128 Icons)</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="res-btn active" id="btnFilterMatAll" onclick="filterMaterials('all')">All (26)</button>
          <button class="res-btn" id="btnFilterMatLumber" onclick="filterMaterials('lumber')">Lumber & Masonry (8)</button>
          <button class="res-btn" id="btnFilterMatStructures" onclick="filterMaterials('structures')">Campers & Silos (4)</button>
          <button class="res-btn" id="btnFilterMatFuel" onclick="filterMaterials('fuel')">Fuel & Bulk Tanks (5)</button>
          <button class="res-btn" id="btnFilterMatHardware" onclick="filterMaterials('hardware')">Fasteners (5)</button>
          <button class="res-btn" id="btnFilterMatCamp" onclick="filterMaterials('camp')">Camp & Outfitter (4)</button>
        </div>
      </div>
      <div class="gallery-grid" id="materialsGalleryGrid"></div>
    </div>

    <!-- SECTION: Logging, Firewood & Sawmills (7) -->
    <div class="gallery-section" id="secLogging">
      <div class="gallery-title">
        <span>🪓 Logging, Firewood & Sawmills (7 Models & Matching 128×128 Icons)</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="res-btn active" id="btnFilterLogAll" onclick="filterLogging('all')">All (7)</button>
          <button class="res-btn" id="btnFilterLogPiles" onclick="filterLogging('logging')">Log Piles & Cordwood (5)</button>
          <button class="res-btn" id="btnFilterLogSawmills" onclick="filterLogging('sawmills')">Sawmills (2)</button>
        </div>
      </div>
      <div class="gallery-grid" id="loggingGalleryGrid"></div>
    </div>

    <!-- SECTION: Waterfront, Fishing Tackle, Fish & Fillets (21) -->
    <div class="gallery-section" id="secFishing">
      <div class="gallery-title">
        <span>🎣 Waterfront, Fishing Tackle, Trophy Fish & Fillets (21 Models & Matching 128×128 Icons)</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="res-btn active" id="btnFilterFishAll" onclick="filterFishing('all')">All (21)</button>
          <button class="res-btn" id="btnFilterFishWaterfront" onclick="filterFishing('waterfront')">Dock & Boat (2)</button>
          <button class="res-btn" id="btnFilterFishTackle" onclick="filterFishing('tackle')">Rods & Tackle (7)</button>
          <button class="res-btn" id="btnFilterFishTrophy" onclick="filterFishing('fish')">Trophy Fish (6)</button>
          <button class="res-btn" id="btnFilterFishFillets" onclick="filterFishing('fillets')">Fresh Fillets (6)</button>
        </div>
      </div>
      <div class="gallery-grid" id="fishingGalleryGrid"></div>
    </div>
"""

# Style for Sticky Sub-Navigation Bar
subnav_css = """
    /* Sticky Gallery Sub-Navigation Bar */
    .gallery-subnav {
      position: sticky;
      top: 0;
      z-index: 95;
      background: rgba(26, 33, 43, 0.95);
      backdrop-filter: blur(8px);
      border-bottom: 1px solid var(--panel-border);
      padding: 10px 20px;
      margin: -20px -20px 24px -20px;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
    }

    .subnav-container {
      display: flex;
      align-items: center;
      gap: 14px;
      overflow-x: auto;
      white-space: nowrap;
      scrollbar-width: thin;
    }

    .subnav-title {
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 1.5px;
      color: var(--accent-gold);
      font-family: 'Sora', sans-serif;
      text-transform: uppercase;
      flex-shrink: 0;
    }

    .subnav-pills {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .subnav-pill {
      background: var(--panel-bg);
      border: 1px solid var(--panel-border);
      color: var(--text-main);
      padding: 6px 12px;
      font-size: 12px;
      font-weight: 700;
      font-family: 'Manrope', sans-serif;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
      flex-shrink: 0;
    }

    .subnav-pill:hover {
      background: rgba(224, 138, 60, 0.15);
      border-color: var(--accent-gold);
      color: #fff;
    }

    .pill-badge {
      background: var(--panel-bg-deep);
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: var(--accent-cyan);
      font-size: 10px;
      padding: 1px 6px;
      border-radius: 4px;
      font-weight: 800;
    }
"""

# Extract top part of HTML up to <section class="asset-gallery-view" id="tabGallery">
idx_tab_gallery = full_text.find('<section class="asset-gallery-view" id="tabGallery">')
if idx_tab_gallery == -1:
    print("ERROR: Could not find tabGallery in index.html")
    exit(1)

# Fix crafting modal and hotbar slots in head/main
pre_gallery = full_text[:idx_tab_gallery + len('<section class="asset-gallery-view" id="tabGallery">')]

# Inject subnav CSS into <style> if not present
if ".gallery-subnav" not in pre_gallery:
    idx_style_end = pre_gallery.find("</style>")
    pre_gallery = pre_gallery[:idx_style_end] + subnav_css + "\n" + pre_gallery[idx_style_end:]

# Replace outdated crafting icons in pre_gallery
pre_gallery = pre_gallery.replace('src="assets/items/icon_axe.png"', 'src="assets/items/tool_axe.png"')
pre_gallery = pre_gallery.replace('src="assets/items/icon_pickaxe.png"', 'src="assets/items/tool_pickaxe.png"')
pre_gallery = pre_gallery.replace('src="assets/items/icon_watering_can.png"', 'src="assets/items/tool_watering_can.png"')
pre_gallery = pre_gallery.replace('src="assets/items/meat_beef.png"', 'src="assets/items/meat_beef.png"')

# Build comprehensive JavaScript block
js_functions = f"""
    // Client-side smooth scroll to category section
    function jumpToSection(sectionId) {{
      playClickSound(650, 0.02);
      const el = document.getElementById(sectionId);
      if (el) {{
        el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      }}
    }}

    // =========================================================================
    // ITEM ICONS GALLERY (384 ASSETS)
    // =========================================================================
    const ALL_ITEM_ICONS = {json.dumps(items_list, indent=2)};
    let currentIconCategory = 'all';

    function renderIconGallery() {{
      const grid = document.getElementById('iconGalleryGrid');
      if (!grid) return;
      grid.innerHTML = '';
      const filtered = currentIconCategory === 'all'
        ? ALL_ITEM_ICONS
        : ALL_ITEM_ICONS.filter(it => it.cat === currentIconCategory);

      filtered.forEach(item => {{
        const card = document.createElement('div');
        card.className = 'asset-card';
        card.innerHTML = `
          <div class="asset-thumb" style="background: radial-gradient(circle, #1a2332 0%, #0d121a 100%);">
            <img src="assets/items/${{item.id}}.png" alt="${{item.name}}" loading="lazy" style="width:100%;height:100%;object-fit:contain;">
          </div>
          <div class="asset-name" style="color:#f8fafc;font-size:12px;font-weight:700;">${{item.name}}</div>
          <div class="asset-dims" style="color:#e08a3c;font-size:10px;font-family:monospace;">${{item.id}}</div>
          <div class="asset-dims" style="color:#94a3b8;font-size:9.5px;margin-top:2px;">${{item.desc}}</div>
          <button class="btn-export" onclick="downloadRaster('assets/items/${{item.id}}.png', '${{item.id}}.png', 128, 128)" style="margin-top:6px;font-size:9.5px;padding:3px 8px;">Export PNG</button>
        `;
        grid.appendChild(card);
      }});
    }}

    function filterIcons(cat) {{
      playClickSound(580, 0.03);
      currentIconCategory = cat;
      const buttons = document.querySelectorAll('#secIcons .res-btn');
      buttons.forEach(b => b.classList.remove('active'));
      const activeBtn = Array.from(buttons).find(b => b.getAttribute('onclick') && b.getAttribute('onclick').includes(`'${{cat}}'`));
      if (activeBtn) activeBtn.classList.add('active');
      renderIconGallery();
    }}

    // =========================================================================
    // 3D MODELS GALLERIES (295 WORLD MODELS)
    // =========================================================================
    const GROUND_ASSETS = {json.dumps(ground_items, indent=2)};
    let currentGroundCategory = 'all';
    function renderGroundTilesGallery() {{
      const grid = document.getElementById('groundTileGalleryGrid');
      if (!grid) return;
      grid.innerHTML = '';
      const filtered = currentGroundCategory === 'all' ? GROUND_ASSETS : GROUND_ASSETS.filter(it => it.cat === currentGroundCategory);
      filtered.forEach(item => {{
        const card = document.createElement('div');
        card.className = 'asset-card';
        card.innerHTML = `
          <div class="asset-thumb" style="background: radial-gradient(circle, #1a2332 0%, #0d121a 100%);">
            <img src="assets/ground/icons/${{item.id}}.png" alt="${{item.name}}" loading="lazy" style="width:100%;height:100%;object-fit:contain;" onerror="this.src='assets/items/${{item.id.toLowerCase().replace('sm_clutter_','clutter_')}}.png'">
          </div>
          <div class="asset-name" style="color:#f8fafc;font-size:13px;font-weight:700;">${{item.name}}</div>
          <div class="asset-dims" style="color:#94a3b8;font-size:10px;margin-top:2px;">${{item.desc}}</div>
          <div class="asset-dims" style="color:#45d1c0;font-size:9.5px;margin-top:4px;">📐 ${{item.footprint}} · H: ${{item.height}} · ${{item.tris}} Tris</div>
          <div style="display:flex;gap:4px;margin-top:6px;justify-content:center;flex-wrap:wrap;">
            <a class="btn-export" href="assets/ground/models/${{item.id}}.obj" download="${{item.id}}.obj" style="text-decoration:none;font-size:9px;padding:3px 6px;">OBJ</a>
            <a class="btn-export" href="assets/ground/models/${{item.id}}.mtl" download="${{item.id}}.mtl" style="text-decoration:none;font-size:9px;padding:3px 6px;">MTL</a>
          </div>
        `;
        grid.appendChild(card);
      }});
    }}
    function filterGround(cat) {{
      playClickSound(580, 0.03);
      currentGroundCategory = cat;
      document.querySelectorAll('#secGround .res-btn').forEach(b => b.classList.remove('active'));
      const activeBtn = document.getElementById(cat === 'all' ? 'btnFilterGroundAll' : (cat === 'tiles' ? 'btnFilterGroundTiles' : 'btnFilterGroundClutter'));
      if (activeBtn) activeBtn.classList.add('active');
      renderGroundTilesGallery();
    }}

    const BUILDING_ASSETS = {json.dumps(building_items, indent=2)};
    let currentBuildingCategory = 'all';
    function renderBuildingGallery() {{
      const grid = document.getElementById('buildingGalleryGrid');
      if (!grid) return;
      grid.innerHTML = '';
      const filtered = currentBuildingCategory === 'all' ? BUILDING_ASSETS : BUILDING_ASSETS.filter(it => it.cat === currentBuildingCategory);
      filtered.forEach(item => {{
        const card = document.createElement('div');
        card.className = 'asset-card';
        card.innerHTML = `
          <div class="asset-thumb" style="background: radial-gradient(circle, #1a2332 0%, #0d121a 100%);">
            <img src="assets/building/icons/${{item.id}}.png" alt="${{item.name}}" loading="lazy" style="width:100%;height:100%;object-fit:contain;">
          </div>
          <div class="asset-name" style="color:#f8fafc;font-size:13px;font-weight:700;">${{item.name}}</div>
          <div class="asset-dims" style="color:#94a3b8;font-size:10px;margin-top:2px;">${{item.desc}}</div>
          <div class="asset-dims" style="color:#45d1c0;font-size:9.5px;margin-top:4px;">📐 ${{item.footprint}} · H: ${{item.height}} · ${{item.tris}} Tris</div>
          <div style="display:flex;gap:4px;margin-top:6px;justify-content:center;flex-wrap:wrap;">
            <a class="btn-export" href="assets/building/structures/${{item.id}}.obj" download="${{item.id}}.obj" style="text-decoration:none;font-size:9px;padding:3px 6px;">OBJ</a>
            <a class="btn-export" href="assets/building/structures/${{item.id}}.mtl" download="${{item.id}}.mtl" style="text-decoration:none;font-size:9px;padding:3px 6px;">MTL</a>
            <a class="btn-export" href="assets/building/icons/${{item.id}}.png" download="${{item.id}}.png" style="text-decoration:none;font-size:9px;padding:3px 6px;">128px PNG</a>
          </div>
        `;
        grid.appendChild(card);
      }});
    }}
    function filterBuildings(cat) {{
      playClickSound(580, 0.03);
      currentBuildingCategory = cat;
      document.querySelectorAll('#secBuildings .res-btn').forEach(b => b.classList.remove('active'));
      const activeBtn = document.getElementById(cat === 'all' ? 'btnFilterBuildingAll' : (cat === 'prefabs' ? 'btnFilterBuildingPrefabs' : 'btnFilterBuildingModular'));
      if (activeBtn) activeBtn.classList.add('active');
      renderBuildingGallery();
    }}

    const FOLIAGE_ASSETS = {json.dumps(foliage_items, indent=2)};
    let currentFoliageCategory = 'all';
    function renderFoliageGallery() {{
      const grid = document.getElementById('foliageGalleryGrid');
      if (!grid) return;
      grid.innerHTML = '';
      const filtered = currentFoliageCategory === 'all' ? FOLIAGE_ASSETS : FOLIAGE_ASSETS.filter(it => it.cat === currentFoliageCategory);
      filtered.forEach(item => {{
        const card = document.createElement('div');
        card.className = 'asset-card';
        card.innerHTML = `
          <div class="asset-thumb" style="background: radial-gradient(circle, #1a2332 0%, #0d121a 100%);">
            <img src="assets/foliage/icons/${{item.id}}.png" alt="${{item.name}}" loading="lazy" style="width:100%;height:100%;object-fit:contain;">
          </div>
          <div class="asset-name" style="color:#f8fafc;font-size:13px;font-weight:700;">${{item.name}}</div>
          <div class="asset-dims" style="color:#94a3b8;font-size:10px;margin-top:2px;">${{item.desc}}</div>
          <div class="asset-dims" style="color:#45d1c0;font-size:9.5px;margin-top:4px;">📐 ${{item.footprint}} · H: ${{item.height}} · ${{item.tris}} Tris</div>
          <div style="display:flex;gap:4px;margin-top:6px;justify-content:center;flex-wrap:wrap;">
            <a class="btn-export" href="assets/foliage/models/${{item.id}}.obj" download="${{item.id}}.obj" style="text-decoration:none;font-size:9px;padding:3px 6px;">OBJ</a>
            <a class="btn-export" href="assets/foliage/models/${{item.id}}.mtl" download="${{item.id}}.mtl" style="text-decoration:none;font-size:9px;padding:3px 6px;">MTL</a>
            <a class="btn-export" href="assets/foliage/icons/${{item.id}}.png" download="${{item.id}}.png" style="text-decoration:none;font-size:9px;padding:3px 6px;">128px PNG</a>
          </div>
        `;
        grid.appendChild(card);
      }});
    }}
    function filterFoliage(cat) {{
      playClickSound(580, 0.03);
      currentFoliageCategory = cat;
      document.querySelectorAll('#secFoliage .res-btn').forEach(b => b.classList.remove('active'));
      const btnMap = {{ all:'btnFilterFoliageAll', trees:'btnFilterFoliageTrees', bushes:'btnFilterFoliageBushes', brambles:'btnFilterFoliageBrambles', grasses:'btnFilterFoliageGrasses', features:'btnFilterFoliageFeatures' }};
      if (btnMap[cat] && document.getElementById(btnMap[cat])) document.getElementById(btnMap[cat]).classList.add('active');
      renderFoliageGallery();
    }}

    const UTILITY_ASSETS = {json.dumps(utility_items, indent=2)};
    let currentUtilityCategory = 'all';
    function renderUtilityGallery() {{
      const grid = document.getElementById('utilityGalleryGrid');
      if (!grid) return;
      grid.innerHTML = '';
      const filtered = currentUtilityCategory === 'all' ? UTILITY_ASSETS : UTILITY_ASSETS.filter(it => it.cat === currentUtilityCategory);
      filtered.forEach(item => {{
        const card = document.createElement('div');
        card.className = 'asset-card';
        card.innerHTML = `
          <div class="asset-thumb" style="background: radial-gradient(circle, #1a2332 0%, #0d121a 100%);">
            <img src="assets/utilities/icons/${{item.id}}.png" alt="${{item.name}}" loading="lazy" style="width:100%;height:100%;object-fit:contain;">
          </div>
          <div class="asset-name" style="color:#f8fafc;font-size:13px;font-weight:700;">${{item.name}}</div>
          <div class="asset-dims" style="color:#94a3b8;font-size:10px;margin-top:2px;">${{item.desc}}</div>
          <div class="asset-dims" style="color:#45d1c0;font-size:9.5px;margin-top:4px;">📐 ${{item.footprint}} · H: ${{item.height}} · ${{item.tris}} Tris</div>
          <div style="display:flex;gap:4px;margin-top:6px;justify-content:center;flex-wrap:wrap;">
            <a class="btn-export" href="assets/utilities/models/${{item.id}}.obj" download="${{item.id}}.obj" style="text-decoration:none;font-size:9px;padding:3px 6px;">OBJ</a>
            <a class="btn-export" href="assets/utilities/models/${{item.id}}.mtl" download="${{item.id}}.mtl" style="text-decoration:none;font-size:9px;padding:3px 6px;">MTL</a>
            <a class="btn-export" href="assets/utilities/icons/${{item.id}}.png" download="${{item.id}}.png" style="text-decoration:none;font-size:9px;padding:3px 6px;">128px PNG</a>
          </div>
        `;
        grid.appendChild(card);
      }});
    }}
    function filterUtilities(cat) {{
      playClickSound(580, 0.03);
      currentUtilityCategory = cat;
      document.querySelectorAll('#secUtilities .res-btn').forEach(b => b.classList.remove('active'));
      const btnMap = {{ all:'btnFilterUtilityAll', electricity:'btnFilterUtilityElectric', water:'btnFilterUtilityWater', sewage:'btnFilterUtilitySewage', internet:'btnFilterUtilityNet' }};
      if (btnMap[cat] && document.getElementById(btnMap[cat])) document.getElementById(btnMap[cat]).classList.add('active');
      renderUtilityGallery();
    }}

    const RANCHING_ASSETS = {json.dumps(ranching_items, indent=2)};
    let currentRanchCategory = 'all';
    function renderRanchingGallery() {{
      const grid = document.getElementById('ranchingGalleryGrid');
      if (!grid) return;
      grid.innerHTML = '';
      const filtered = currentRanchCategory === 'all' ? RANCHING_ASSETS : RANCHING_ASSETS.filter(it => it.cat === currentRanchCategory);
      filtered.forEach(item => {{
        const card = document.createElement('div');
        card.className = 'asset-card';
        card.innerHTML = `
          <div class="asset-thumb" style="background: radial-gradient(circle, #1a2332 0%, #0d121a 100%);">
            <img src="assets/ranching/icons/${{item.id}}.png" alt="${{item.name}}" loading="lazy" style="width:100%;height:100%;object-fit:contain;">
          </div>
          <div class="asset-name" style="color:#f8fafc;font-size:13px;font-weight:700;">${{item.name}}</div>
          <div class="asset-dims" style="color:#94a3b8;font-size:10px;margin-top:2px;">${{item.desc}}</div>
          <div class="asset-dims" style="color:#45d1c0;font-size:9.5px;margin-top:4px;">📐 ${{item.footprint}} · H: ${{item.height}} · ${{item.tris}} Tris</div>
          <div style="display:flex;gap:4px;margin-top:6px;justify-content:center;flex-wrap:wrap;">
            <a class="btn-export" href="assets/ranching/models/${{item.id}}.obj" download="${{item.id}}.obj" style="text-decoration:none;font-size:9px;padding:3px 6px;">OBJ</a>
            <a class="btn-export" href="assets/ranching/models/${{item.id}}.mtl" download="${{item.id}}.mtl" style="text-decoration:none;font-size:9px;padding:3px 6px;">MTL</a>
            <a class="btn-export" href="assets/ranching/icons/${{item.id}}.png" download="${{item.id}}.png" style="text-decoration:none;font-size:9px;padding:3px 6px;">128px PNG</a>
          </div>
        `;
        grid.appendChild(card);
      }});
    }}
    function filterRanching(cat) {{
      playClickSound(580, 0.03);
      currentRanchCategory = cat;
      document.querySelectorAll('#secRanching .res-btn').forEach(b => b.classList.remove('active'));
      const btnMap = {{ all:'btnFilterRanchAll', animals:'btnFilterRanchAnimals', fencing:'btnFilterRanchFencing', yields:'btnFilterRanchYields' }};
      if (btnMap[cat] && document.getElementById(btnMap[cat])) document.getElementById(btnMap[cat]).classList.add('active');
      renderRanchingGallery();
    }}

    const FARMING_ASSETS = {json.dumps(farming_items, indent=2)};
    let currentFarmCategory = 'all';
    function renderFarmingGallery() {{
      const grid = document.getElementById('farmingGalleryGrid');
      if (!grid) return;
      grid.innerHTML = '';
      const filtered = currentFarmCategory === 'all' ? FARMING_ASSETS : FARMING_ASSETS.filter(it => it.cat === currentFarmCategory);
      filtered.forEach(item => {{
        const card = document.createElement('div');
        card.className = 'asset-card';
        card.innerHTML = `
          <div class="asset-thumb" style="background: radial-gradient(circle, #1a2332 0%, #0d121a 100%);">
            <img src="assets/farming/icons/${{item.id}}.png" alt="${{item.name}}" loading="lazy" style="width:100%;height:100%;object-fit:contain;">
          </div>
          <div class="asset-name" style="color:#f8fafc;font-size:13px;font-weight:700;">${{item.name}}</div>
          <div class="asset-dims" style="color:#94a3b8;font-size:10px;margin-top:2px;">${{item.desc}}</div>
          <div class="asset-dims" style="color:#45d1c0;font-size:9.5px;margin-top:4px;">📐 ${{item.footprint}} · H: ${{item.height}} · ${{item.tris}} Tris</div>
          <div style="display:flex;gap:4px;margin-top:6px;justify-content:center;flex-wrap:wrap;">
            <a class="btn-export" href="assets/farming/models/${{item.id}}.obj" download="${{item.id}}.obj" style="text-decoration:none;font-size:9px;padding:3px 6px;">OBJ</a>
            <a class="btn-export" href="assets/farming/models/${{item.id}}.mtl" download="${{item.id}}.mtl" style="text-decoration:none;font-size:9px;padding:3px 6px;">MTL</a>
            <a class="btn-export" href="assets/farming/icons/${{item.id}}.png" download="${{item.id}}.png" style="text-decoration:none;font-size:9px;padding:3px 6px;">128px PNG</a>
          </div>
        `;
        grid.appendChild(card);
      }});
    }}
    function filterFarming(cat) {{
      playClickSound(580, 0.03);
      currentFarmCategory = cat;
      document.querySelectorAll('#secFarming .res-btn').forEach(b => b.classList.remove('active'));
      const btnMap = {{ all:'btnFilterFarmAll', crops:'btnFilterFarmCrops', machinery:'btnFilterFarmMachinery', equipment:'btnFilterFarmEquip', produce:'btnFilterFarmProduce', seeds:'btnFilterFarmSeeds' }};
      if (btnMap[cat] && document.getElementById(btnMap[cat])) document.getElementById(btnMap[cat]).classList.add('active');
      renderFarmingGallery();
    }}

    const TOOLS_ASSETS = {json.dumps(tools_items, indent=2)};
    let currentToolsCategory = 'all';
    function renderToolsGallery() {{
      const grid = document.getElementById('toolsGalleryGrid');
      if (!grid) return;
      grid.innerHTML = '';
      const filtered = currentToolsCategory === 'all' ? TOOLS_ASSETS : TOOLS_ASSETS.filter(it => it.cat === currentToolsCategory);
      filtered.forEach(item => {{
        const card = document.createElement('div');
        card.className = 'asset-card';
        card.innerHTML = `
          <div class="asset-thumb" style="background: radial-gradient(circle, #1a2332 0%, #0d121a 100%);">
            <img src="assets/tools/icons/${{item.id}}.png" alt="${{item.name}}" loading="lazy" style="width:100%;height:100%;object-fit:contain;">
          </div>
          <div class="asset-name" style="color:#f8fafc;font-size:13px;font-weight:700;">${{item.name}}</div>
          <div class="asset-dims" style="color:#94a3b8;font-size:10px;margin-top:2px;">${{item.desc}}</div>
          <div class="asset-dims" style="color:#45d1c0;font-size:9.5px;margin-top:4px;">📐 ${{item.footprint}} · H: ${{item.height}} · ${{item.tris}} Tris</div>
          <div style="display:flex;gap:4px;margin-top:6px;justify-content:center;flex-wrap:wrap;">
            <a class="btn-export" href="assets/tools/models/${{item.id}}.obj" download="${{item.id}}.obj" style="text-decoration:none;font-size:9px;padding:3px 6px;">OBJ</a>
            <a class="btn-export" href="assets/tools/models/${{item.id}}.mtl" download="${{item.id}}.mtl" style="text-decoration:none;font-size:9px;padding:3px 6px;">MTL</a>
            <a class="btn-export" href="assets/tools/icons/${{item.id}}.png" download="${{item.id}}.png" style="text-decoration:none;font-size:9px;padding:3px 6px;">128px PNG</a>
          </div>
        `;
        grid.appendChild(card);
      }});
    }}
    function filterTools(cat) {{
      playClickSound(580, 0.03);
      currentToolsCategory = cat;
      document.querySelectorAll('#secTools .res-btn').forEach(b => b.classList.remove('active'));
      const btnMap = {{ all:'btnFilterToolsAll', earthmoving:'btnFilterToolsEarthmoving', fixtures:'btnFilterToolsFixtures', handheld:'btnFilterToolsHandheld', powertools:'btnFilterToolsPower', care:'btnFilterToolsCare' }};
      if (btnMap[cat] && document.getElementById(btnMap[cat])) document.getElementById(btnMap[cat]).classList.add('active');
      renderToolsGallery();
    }}

    const MATERIALS_ASSETS = {json.dumps(materials_items, indent=2)};
    let currentMaterialsCategory = 'all';
    function renderMaterialsGallery() {{
      const grid = document.getElementById('materialsGalleryGrid');
      if (!grid) return;
      grid.innerHTML = '';
      const filtered = currentMaterialsCategory === 'all' ? MATERIALS_ASSETS : MATERIALS_ASSETS.filter(it => it.cat === currentMaterialsCategory);
      filtered.forEach(item => {{
        const card = document.createElement('div');
        card.className = 'asset-card';
        card.innerHTML = `
          <div class="asset-thumb" style="background: radial-gradient(circle, #1a2332 0%, #0d121a 100%);">
            <img src="assets/building/icons/${{item.id}}.png" alt="${{item.name}}" loading="lazy" style="width:100%;height:100%;object-fit:contain;">
          </div>
          <div class="asset-name" style="color:#f8fafc;font-size:13px;font-weight:700;">${{item.name}}</div>
          <div class="asset-dims" style="color:#94a3b8;font-size:10px;margin-top:2px;">${{item.desc}}</div>
          <div class="asset-dims" style="color:#45d1c0;font-size:9.5px;margin-top:4px;">📐 ${{item.footprint}} · H: ${{item.height}} · ${{item.tris}} Tris</div>
          <div style="display:flex;gap:4px;margin-top:6px;justify-content:center;flex-wrap:wrap;">
            <a class="btn-export" href="assets/building/models/${{item.id}}.obj" download="${{item.id}}.obj" style="text-decoration:none;font-size:9px;padding:3px 6px;">OBJ</a>
            <a class="btn-export" href="assets/building/models/${{item.id}}.mtl" download="${{item.id}}.mtl" style="text-decoration:none;font-size:9px;padding:3px 6px;">MTL</a>
            <a class="btn-export" href="assets/building/icons/${{item.id}}.png" download="${{item.id}}.png" style="text-decoration:none;font-size:9px;padding:3px 6px;">128px PNG</a>
          </div>
        `;
        grid.appendChild(card);
      }});
    }}
    function filterMaterials(cat) {{
      playClickSound(580, 0.03);
      currentMaterialsCategory = cat;
      document.querySelectorAll('#secMaterials .res-btn').forEach(b => b.classList.remove('active'));
      const btnMap = {{ all:'btnFilterMatAll', lumber:'btnFilterMatLumber', structures:'btnFilterMatStructures', fuel:'btnFilterMatFuel', hardware:'btnFilterMatHardware', camp:'btnFilterMatCamp' }};
      if (btnMap[cat] && document.getElementById(btnMap[cat])) document.getElementById(btnMap[cat]).classList.add('active');
      renderMaterialsGallery();
    }}

    const LOGGING_ASSETS = {json.dumps(logging_items, indent=2)};
    let currentLoggingCategory = 'all';
    function renderLoggingGallery() {{
      const grid = document.getElementById('loggingGalleryGrid');
      if (!grid) return;
      grid.innerHTML = '';
      const filtered = currentLoggingCategory === 'all' ? LOGGING_ASSETS : LOGGING_ASSETS.filter(it => it.cat === currentLoggingCategory);
      filtered.forEach(item => {{
        const card = document.createElement('div');
        card.className = 'asset-card';
        card.innerHTML = `
          <div class="asset-thumb" style="background: radial-gradient(circle, #1a2332 0%, #0d121a 100%);">
            <img src="assets/logging/icons/${{item.id}}.png" alt="${{item.name}}" loading="lazy" style="width:100%;height:100%;object-fit:contain;">
          </div>
          <div class="asset-name" style="color:#f8fafc;font-size:13px;font-weight:700;">${{item.name}}</div>
          <div class="asset-dims" style="color:#94a3b8;font-size:10px;margin-top:2px;">${{item.desc}}</div>
          <div class="asset-dims" style="color:#45d1c0;font-size:9.5px;margin-top:4px;">📐 ${{item.footprint}} · H: ${{item.height}} · ${{item.tris}} Tris</div>
          <div style="display:flex;gap:4px;margin-top:6px;justify-content:center;flex-wrap:wrap;">
            <a class="btn-export" href="assets/logging/models/${{item.id}}.obj" download="${{item.id}}.obj" style="text-decoration:none;font-size:9px;padding:3px 6px;">OBJ</a>
            <a class="btn-export" href="assets/logging/models/${{item.id}}.mtl" download="${{item.id}}.mtl" style="text-decoration:none;font-size:9px;padding:3px 6px;">MTL</a>
            <a class="btn-export" href="assets/logging/icons/${{item.id}}.png" download="${{item.id}}.png" style="text-decoration:none;font-size:9px;padding:3px 6px;">128px PNG</a>
          </div>
        `;
        grid.appendChild(card);
      }});
    }}
    function filterLogging(cat) {{
      playClickSound(580, 0.03);
      currentLoggingCategory = cat;
      document.querySelectorAll('#secLogging .res-btn').forEach(b => b.classList.remove('active'));
      const btnMap = {{ all:'btnFilterLogAll', logging:'btnFilterLogPiles', sawmills:'btnFilterLogSawmills' }};
      if (btnMap[cat] && document.getElementById(btnMap[cat])) document.getElementById(btnMap[cat]).classList.add('active');
      renderLoggingGallery();
    }}

    const FISHING_ASSETS = {json.dumps(fishing_items, indent=2)};
    let currentFishingCategory = 'all';
    function renderFishingGallery() {{
      const grid = document.getElementById('fishingGalleryGrid');
      if (!grid) return;
      grid.innerHTML = '';
      const filtered = currentFishingCategory === 'all' ? FISHING_ASSETS : FISHING_ASSETS.filter(it => it.cat === currentFishingCategory);
      filtered.forEach(item => {{
        const card = document.createElement('div');
        card.className = 'asset-card';
        card.innerHTML = `
          <div class="asset-thumb" style="background: radial-gradient(circle, #1a2332 0%, #0d121a 100%);">
            <img src="assets/fishing/icons/${{item.id}}.png" alt="${{item.name}}" loading="lazy" style="width:100%;height:100%;object-fit:contain;">
          </div>
          <div class="asset-name" style="color:#f8fafc;font-size:13px;font-weight:700;">${{item.name}}</div>
          <div class="asset-dims" style="color:#94a3b8;font-size:10px;margin-top:2px;">${{item.desc}}</div>
          <div class="asset-dims" style="color:#45d1c0;font-size:9.5px;margin-top:4px;">📐 ${{item.footprint}} · H: ${{item.height}} · ${{item.tris}} Tris</div>
          <div style="display:flex;gap:4px;margin-top:6px;justify-content:center;flex-wrap:wrap;">
            <a class="btn-export" href="assets/fishing/models/${{item.id}}.obj" download="${{item.id}}.obj" style="text-decoration:none;font-size:9px;padding:3px 6px;">OBJ</a>
            <a class="btn-export" href="assets/fishing/models/${{item.id}}.mtl" download="${{item.id}}.mtl" style="text-decoration:none;font-size:9px;padding:3px 6px;">MTL</a>
            <a class="btn-export" href="assets/fishing/icons/${{item.id}}.png" download="${{item.id}}.png" style="text-decoration:none;font-size:9px;padding:3px 6px;">128px PNG</a>
          </div>
        `;
        grid.appendChild(card);
      }});
    }}
    function filterFishing(cat) {{
      playClickSound(580, 0.03);
      currentFishingCategory = cat;
      document.querySelectorAll('#secFishing .res-btn').forEach(b => b.classList.remove('active'));
      const btnMap = {{ all:'btnFilterFishAll', waterfront:'btnFilterFishWaterfront', tackle:'btnFilterFishTackle', fish:'btnFilterFishTrophy', fillets:'btnFilterFishFillets' }};
      if (btnMap[cat] && document.getElementById(btnMap[cat])) document.getElementById(btnMap[cat]).classList.add('active');
      renderFishingGallery();
    }}
"""

# Assemble new HTML:
# Find where `<canvas id="exportCanvas"` is in full_text
idx_canvas = full_text.find('<canvas id="exportCanvas"')
if idx_canvas == -1:
    print("ERROR: Could not find exportCanvas in index.html")
    exit(1)

# Find where rasterizer starts
idx_raster = full_text.find("// Client-side instant SVG-to-PNG rasterizer")
if idx_raster == -1:
    idx_raster = full_text.find("function downloadRaster")

# Locate closing </section> of tabGallery
new_body = (
    pre_gallery + "\n" +
    gallery_sections_html + "\n  </section>\n\n  " +
    full_text[idx_canvas:full_text.find("<script>", idx_canvas) + len("<script>")] + "\n" +
    full_text[full_text.find("<script>", idx_canvas) + len("<script>"):full_text.find("// Tab Navigation")] +
    """// Tab Navigation
    function switchTab(tabId) {
      playClickSound(600, 0.03);
      const isSim = tabId === 'simulation';
      document.getElementById('tabSimulation').style.display = isSim ? 'flex' : 'none';
      document.getElementById('tabGallery').classList.toggle('active', !isSim);
      document.getElementById('resControls').style.display = isSim ? 'flex' : 'none';
      document.querySelectorAll('.tab-btn').forEach((b, i) => {
        b.classList.toggle('active', (isSim && i === 0) || (!isSim && i === 1));
      });
    }

    """ +
    js_functions + "\n\n    // Initial render\n" +
    """    renderIconGallery();
    renderGroundTilesGallery();
    renderBuildingGallery();
    renderFoliageGallery();
    renderUtilityGallery();
    renderRanchingGallery();
    renderFarmingGallery();
    renderToolsGallery();
    renderMaterialsGallery();
    renderLoggingGallery();
    renderFishingGallery();\n\n    """ +
    full_text[idx_raster:]
)

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(new_body)

print(f"Successfully generated new index.html ({len(new_body)} bytes)!")

