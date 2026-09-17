#!/usr/bin/env python3
"""
Updates gallery/index.html to display all 283 models across clean dedicated gallery sections.
"""
import os
import re
import html
from html.parser import HTMLParser

# tools/ sits at the repo root, so the project root is one level up.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUD_ROOT = PROJECT_ROOT  # legacy alias - keep old joins working
INDEX_PATH = os.path.join(HUD_ROOT, "gallery", "index.html")

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
    dx = max(xs) - min(xs)
    dy = max(ys) - min(ys)
    dz = max(zs) - min(zs)
    return {
        "dx": round(dx, 1),
        "dy": round(dy, 1),
        "dz": round(dz, 1),
        "tris": face_count
    }

# 1. UTILITY ASSETS (40)
UTILITY_DEFS = [
    # Electricity (18)
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
    ('SM_Item_Spool_Romex_12_2', 'Romex 12/2 Cable Spool (250ft)', 'electricity', '250ft spool of 12/2 with ground solid copper Romex NM-B wire'),
    ('SM_Item_Spool_Cat6_500ft', 'Cat6 Outdoor Cable Spool (500ft)', 'electricity', '500ft spool of heavy-duty direct-burial shielded Cat6 cable'),
    ('SM_Item_Spool_BarbedWire', 'Barbed Wire Spool (1320ft)', 'electricity', '1/4-mile spool of 12.5-gauge high-tensile 4-point barbed wire'),
    ('SM_Item_Electric_BreakerSubpanel', '100A Breaker Subpanel', 'electricity', '100-Amp 12-space outdoor NEMA 3R rainproof electrical subpanel'),
    ('SM_Item_Electric_DisconnectSwitch', '60A Heavy-Duty Disconnect Switch', 'electricity', '60-Amp fusible AC/DC exterior knife blade disconnect switch'),
    ('SM_Item_Electric_MPPTController', '60A MPPT Solar Charge Controller', 'electricity', 'High-efficiency 150V/60A MPPT solar charge controller with heat sink'),
    ('SM_Item_Electric_NetworkSwitch_PoE', '8-Port Gigabit PoE+ Switch', 'electricity', 'Industrial hardened 8-port Gigabit PoE+ network switch'),

    # Water (13)
    ('SM_Water_RainBarrel_55gal', '55-Gal Poly Rain Barrel', 'water', '55-gallon blue poly rain barrel on cinder pedestal'),
    ('SM_Water_IBC_Tote_275gal', '275-Gal Caged IBC Tote', 'water', '275-gallon caged IBC water tote on pallet base'),
    ('SM_Water_Cistern_Poly_1000gal', '1000-Gal Poly Cistern', 'water', '1000-gallon heavy ribbed dark green poly water cistern'),
    ('SM_Water_WellPump_Manual', 'Manual Pitcher Well Pump', 'water', 'Cast-iron pitcher pump on octagonal timber well cover'),
    ('SM_Water_PressureTank_Well', 'Well Pump & Pressure Tank', 'water', 'Vertical bladder pressure tank with mounted jet pump'),
    ('SM_Water_FilterRack_3Stage', '3-Stage Water Filter Rack', 'water', '3-stage Big Blue sediment and carbon filtration rack'),
    ('SM_Water_HoseReel_Cart', 'Mobile Hose Reel Cart', 'water', 'Portable wheeled hose reel cart with 100ft green hose'),
    ('SM_Water_Trough_Stock_100gal', '100-Gal Stock Tank Trough', 'water', 'Galvanized oval livestock drinking trough with float valve'),
    ('SM_Item_Plumbing_PVC_Bundle', 'Schedule 40 PVC Pipe Bundle (10ft)', 'water', 'Bundle of five 2-inch x 10ft Schedule 40 white PVC water pipes'),
    ('SM_Item_Plumbing_Filter_BigBlue', 'Big Blue Filter Cartridge (20-Inch)', 'water', '20-inch x 4.5-inch 5-micron sediment filter cartridge'),
    ('SM_Item_Plumbing_GardenHose_Reel', 'Commercial Garden Hose (50ft)', 'water', 'Heavy-duty 5/8-inch 50-foot coiled green rubber farm hose'),
    ('SM_Item_Plumbing_WaterJug_5gal', '5-Gallon Poly Water Jug', 'water', '5-gallon food-grade BPA-free emergency drinking water jug with spigot'),
    ('SM_Item_Plumbing_DrainSock_Roll', 'Perforated Drain Sock Roll (100ft)', 'water', '100ft roll of 4-inch corrugated perforated french drain pipe'),

    # Sewage & Waste (4)
    ('SM_Sewage_SepticTank_Poly_500gal', '500-Gal Poly Septic Tank', 'sewage', '500-gallon ribbed polyethylene septic tank with dual risers'),
    ('SM_Sewage_DistributionBox', 'Septic Distribution Box', 'sewage', 'Precast concrete septic distribution box with inspection lid'),
    ('SM_Sewage_CompostBin_3Bay', '3-Bay Timber Compost Bin', 'sewage', '3-bay cedar timber homestead compost station'),
    ('SM_Sewage_Toilet_Composting', 'Rustic Composting Toilet', 'sewage', 'Self-contained rustic cedar composting toilet with agitator'),

    # Internet & Telecom (5)
    ('SM_Internet_Dish_Starlink_Tripod', 'Satellite Dish (Tripod)', 'internet', 'Rectangular phased-array satellite dish on ground tripod'),
    ('SM_Internet_Dish_HighPerf_Mast', 'Satellite Dish (J-Mast)', 'internet', 'High-performance round satellite dish on tall galvanized J-mast'),
    ('SM_Internet_Antenna_Yagi_Mast', 'Cellular Yagi Antenna (3.5m)', 'internet', 'Directional cellular Yagi antenna array on 3.5m mast'),
    ('SM_Internet_Antenna_Omni_Cellular', 'Cellular Omni Antenna Mast', 'internet', 'Vertical fiberglass high-gain cellular omni antenna'),
    ('SM_Internet_Outdoor_AP_Pole', 'Outdoor Wi-Fi AP Pole', 'internet', 'Weatherproof outdoor dual-antenna PoE Wi-Fi access point'),
]

# 2. RANCHING ASSETS (47)
RANCHING_DEFS = [
    # Livestock Animals - All 3 Varieties & Young (26)
    # Cattle
    ('SM_Animal_Cow_Holstein', 'Holstein Cow', 'animals', 'Dairy cow with iconic black and white spotted coat and horns'),
    ('SM_Animal_Cow_Jersey', 'Jersey Cow', 'animals', 'Caramel tan dairy cow with dark muzzle and pale muzzle ring'),
    ('SM_Animal_Cow_Highland', 'Highland Cow', 'animals', 'Scottish Highland cow with shaggy ginger coat and 110cm horns'),
    ('SM_Animal_Cow_Calf', 'Chestnut Calf', 'animals', 'Young homestead calf with chestnut coat and white star blaze'),
    ('SM_Animal_Cow_Calf_Spotted', 'Spotted Calf', 'animals', 'Young Holstein calf with black and white spotted coat'),
    # Chickens
    ('SM_Animal_Chicken_Red', 'Rhode Island Red Chicken', 'animals', 'Egg-laying hen with rich chestnut plumage and red comb'),
    ('SM_Animal_Chicken_White', 'White Leghorn Chicken', 'animals', 'Clean white Leghorn hen with red comb and yellow legs'),
    ('SM_Animal_Chicken_Barred', 'Barred Rock Chicken', 'animals', 'Plumage with black and white zebra-striped barring'),
    ('SM_Animal_Chicken_Chick', 'Golden Baby Chick', 'animals', 'Downy golden-yellow baby chick with orange beak'),
    # Pigs
    ('SM_Animal_Pig_Pink', 'Pink Yorkshire Pig', 'animals', 'Healthy pink market pig with disc snout and curly tail'),
    ('SM_Animal_Pig_Hampshire', 'Hampshire Pig', 'animals', 'Black pig with distinct solid white shoulder belt'),
    ('SM_Animal_Pig_Duroc', 'Duroc Pig', 'animals', 'Muscular mahogany reddish-brown pig with drooping ears'),
    ('SM_Animal_Pig_Piglet', 'Young Pink Piglet', 'animals', 'Chubby pink piglet with button snout'),
    # Sheep
    ('SM_Animal_Sheep_Suffolk', 'Suffolk Sheep', 'animals', 'Thick fleece wool sheep with black face and legs'),
    ('SM_Animal_Sheep_White', 'White Fleece Sheep', 'animals', 'Full white wool sheep with pale pinkish face and legs'),
    ('SM_Animal_Sheep_Tan', 'Tan Fleece Sheep', 'animals', 'Natural warm caramel tan wool fleece sheep'),
    ('SM_Animal_Sheep_Lamb', 'Young Spring Lamb', 'animals', 'Fluffy white baby lamb with dark face mask'),
    # Goats
    ('SM_Animal_Goat_Brown', 'Brown Dairy Goat', 'animals', 'Warm brown dairy goat with white stripes, belly & beard'),
    ('SM_Animal_Goat_White', 'White Saanen Goat', 'animals', 'Pure white dairy goat with ivory horns and chin beard'),
    ('SM_Animal_Goat_BlackWhite', 'Black & White Goat', 'animals', 'Piebald black and white goat with arching horns'),
    ('SM_Animal_Goat_Kid', 'Young Goat Kid', 'animals', 'Spotted brown and white miniature goat kid'),
    # Generic Adult Aliases
    ('SM_Animal_Cow_Adult', 'Adult Cow (Holstein)', 'animals', 'Adult beef/dairy cow with spotted hide & horns'),
    ('SM_Animal_Chicken_Hen', 'Laying Hen (Red)', 'animals', 'Free-range laying hen with red comb and wattles'),
    ('SM_Animal_Pig_Adult', 'Adult Pig (Pink)', 'animals', 'Market pig with snout, flopped ears & curled tail'),
    ('SM_Animal_Sheep_Adult', 'Adult Sheep (Suffolk)', 'animals', 'Fleece wool sheep with dark face and hooves'),
    ('SM_Animal_Goat_Adult', 'Adult Goat (Brown)', 'animals', 'Homestead dairy goat with backward horns & beard'),

    # Feed & Fencing (11)
    ('SM_Ranch_HayBale_Round', 'Round Hay Bale (1.5m)', 'fencing', 'Large net-wrapped golden dried pasture grass round bale'),
    ('SM_Ranch_HayBale_Square', 'Square Hay Bale (2-String)', 'fencing', 'Two-string tied rectangular alfalfa hay bale'),
    ('SM_Ranch_SilageBale_Round', 'Wrapped Silage Round Bale', 'fencing', 'UV-stabilized white plastic-wrapped fermented forage bale'),
    ('SM_Ranch_StrawBale_Round', 'Round Straw Bedding Bale', 'fencing', 'Pale yellow wheat straw bedding bale'),
    ('SM_Ranch_StrawBale_Square', 'Square Straw Bale', 'fencing', 'Banded straw square bale for coop and stall bedding'),
    ('SM_Ranch_FeedPan_Rubber', 'Heavy Rubber Feed Pan', 'fencing', '15-gallon durable recycled tire livestock feed tub'),
    ('SM_Ranch_SaltLick_Block', 'Mineral Salt Lick on Stand', 'fencing', '50lb reddish mineral livestock salt block on timber post'),
    ('SM_Ranch_Fence_Wood_1m', 'Split-Rail Wood Fence (1m)', 'fencing', 'Cedar post with two horizontal split rails'),
    ('SM_Ranch_Fence_Wire_1m', 'Barbed Wire T-Post Fence (1m)', 'fencing', 'Steel T-post with 4 strands of barbed wire'),
    ('SM_Ranch_Gate_Metal_2m', 'Tubular Steel Farm Gate (2m)', 'fencing', '2-meter red tubular steel 6-bar farm gate with hinges'),
    ('SM_Ranch_Fence_Energizer_Solar', 'Solar Fence Energizer', 'fencing', 'Solar electric fence energizer charger on T-post'),

    # Animal Yields & Meats (10)
    ('SM_Item_Animal_Eggs_Carton', 'Farm Fresh Egg Carton (Dozen)', 'yields', '12-count molded pulp egg carton with grade-A farm eggs'),
    ('SM_Item_Animal_Milk_Jug', 'Fresh Whole Milk Jug (1 Gallon)', 'yields', '1-gallon HDPE translucent farm milk jug with blue cap'),
    ('SM_Item_Animal_Wool_Fleece', 'Raw Sheared Wool Fleece Bundle', 'yields', 'Tied bale of freshly sheared natural raw sheep wool fleece'),
    ('SM_Item_Animal_Truffle', 'Harvested Black Truffle', 'yields', 'Gourmet black Perigord foraging truffle with faceted exterior'),
    ('SM_Item_Meat_Beef_Steak', 'Thick-Cut Beef Ribeye Steak', 'yields', 'Thick butcher-cut marbled beef steak with rib bone'),
    ('SM_Item_Meat_Chicken_Drumstick', 'Fresh Chicken Drumstick', 'yields', 'Butcher poultry drumstick with ivory bone end'),
    ('SM_Item_Meat_Pork_Chop', 'Thick Bone-In Pork Chop', 'yields', 'Thick center-cut bone-in homestead pork chop'),
    ('SM_Item_Pelt_Cow_Hide', 'Cured Cowhide Leather Pelt', 'yields', 'Cured natural brown and white cowhide leather rug pelt'),
    ('SM_Item_Pelt_Sheep_Fleece', 'Natural Sheepskin Fleece Pelt', 'yields', 'Fluffy natural ivory shearling wool fleece pelt'),
    ('SM_Item_Pelt_Goat_Skin', 'Supple Goatskin Leather Hide', 'yields', 'Clean tanned amber goatskin parchment and leather hide'),
]

# 3. FARMING ASSETS (40)
FARMING_DEFS = [
    # Crops (8)
    ('SM_Crop_Corn_Stalk', 'Sweet Corn Stalk (2.3m)', 'crops', 'Tall mature sweet corn stalk with ripe ears and silk tassels'),
    ('SM_Crop_Tomato_Vine', 'Caged Tomato Vine', 'crops', 'Galvanized wire tomato cage supporting lush vine with red fruit'),
    ('SM_Crop_Wheat_Bundle', 'Ripe Wheat Clump', 'crops', 'Dense cluster of golden mature wheat heads'),
    ('SM_Crop_Potato_Plant', 'Hilled Potato Plant', 'crops', 'Mounded soil hill with dark green leafy potato vine'),
    ('SM_Crop_Carrot_Patch', 'Garden Carrot Patch', 'crops', 'Feathery green carrot tops with orange crowns visible'),
    ('SM_Crop_Pumpkin_Patch', 'Mound Pumpkin Patch', 'crops', 'Trailing vine with broad leaves and ribbed orange field pumpkin'),
    ('SM_Crop_Cabbage_Head', 'Homestead Cabbage Head', 'crops', 'Dense crinkled green cabbage head surrounded by fan leaves'),
    ('SM_Crop_Sunflower_Stalk', 'Giant Sunflower (2.3m)', 'crops', 'Towering mammoth sunflower stalk with massive seed disc'),

    # Farm Machinery & Equipment (8)
    ('SM_Machine_Tractor_Large', 'Heavy Field Tractor (4.1m)', 'machinery', 'Heavy 250HP utility farm tractor with dual rear lug tires and cab'),
    ('SM_Machine_Tractor_Small', 'Compact Farm Tractor (3.1m)', 'machinery', 'Compact 40HP homestead diesel tractor with rear 3-point hitch'),
    ('SM_Machine_Combine_Large', 'Heavy Grain Combine Harvester (7.5m)', 'machinery', 'Commercial grain combine harvester with front reel header & grain auger'),
    ('SM_Machine_Combine_Small', 'Compact Combine Harvester (5.5m)', 'machinery', 'Compact homestead grain combine with 2.8m grain platform'),
    ('SM_Farm_Wheelbarrow', 'Steel Garden Wheelbarrow', 'equipment', 'Single-wheel steel hopper wheelbarrow with wood handles'),
    ('SM_Farm_SeedBag_Burlap', 'Burlap Grain Seed Bag', 'equipment', 'Tied burlap seed sack with stitched vintage seal'),
    ('SM_Farm_ProduceCrate_Wood', 'Cedar Apple Harvest Crate', 'equipment', 'Slotted bushel crate heaped with ripe red apples'),
    ('SM_Farm_Irrigation_Sprinkler_Riser', 'Impact Sprinkler Riser', 'equipment', 'PVC riser pipe with brass pulsating impact sprinkler head'),

    # Harvested Produce & Foods (14)
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

    # Seed Packets (10)
    ('SM_Item_Seed_Corn', 'Sweet Corn Seed Packet', 'seeds', 'Heirloom seed packet for Golden Bantam sweet corn'),
    ('SM_Item_Seed_Tomato', 'Beefsteak Tomato Seed Packet', 'seeds', 'Seed envelope for Cherokee Purple beefsteak tomatoes'),
    ('SM_Item_Seed_Wheat', 'Winter Wheat Grain Seed Packet', 'seeds', 'Hard red winter wheat seed planting packet'),
    ('SM_Item_Seed_Potato', 'Seed Potato Eyes Packet', 'seeds', 'Certified organic seed potato planting pouch'),
    ('SM_Item_Seed_Carrot', 'Danvers Carrot Seed Packet', 'seeds', 'Danvers half-long heirloom carrot seed packet'),
    ('SM_Item_Seed_Pumpkin', 'Sugar Pie Pumpkin Seed Packet', 'seeds', 'Traditional New England sugar pie pumpkin seeds'),
    ('SM_Item_Seed_Sunflower', 'Mammoth Sunflower Seed Packet', 'seeds', 'Mammoth Russian giant sunflower seed packet'),
    ('SM_Item_Seed_Strawberry', 'Ever-Bearing Strawberry Seed Packet', 'seeds', 'Ever-bearing alpine sweet strawberry seeds'),
    ('SM_Item_Seed_Cotton', 'Upland Cotton Seed Packet', 'seeds', 'Delta upland heirloom white cotton seed packet'),
    ('SM_Item_Seed_Herb', 'Culinary Herb Blend Seed Packet', 'seeds', 'Homestead kitchen garden basil, thyme & oregano seeds'),
]

# 4. TOOLS, WORKSHOP & EARTHMOVERS (37)
TOOLS_DEFS = [
    # Earthmovers & Machinery (4)
    ('SM_Machine_Excavator_Large', 'Heavy Hydraulic Excavator (6.5m)', 'earthmoving', 'Commercial 20-ton tracked excavator with boom, arm and bucket'),
    ('SM_Machine_Excavator_Small', 'Compact Mini Excavator (3.3m)', 'earthmoving', 'Rubber-tracked mini excavator with front dozer blade and cab'),
    ('SM_Machine_Skidsteer_Large', 'Heavy Skid Steer Loader (2.8m)', 'earthmoving', 'Tracked heavy skid steer loader with dirt bucket and ROPS canopy'),
    ('SM_Machine_Skidsteer_Small', 'Compact Wheeled Skid Steer (2.2m)', 'earthmoving', '4-wheel compact skid steer loader with standard material bucket'),

    # Workshop Fixtures (5)
    ('SM_Tool_Workbench_Timber', 'Timber Woodworking Workbench', 'fixtures', 'Heavy-duty timber workbench with cast iron vise and tool shelf'),
    ('SM_Tool_Anvil_Stump', 'Blacksmith Anvil on Stump', 'fixtures', 'Cast steel blacksmith anvil strapped to solid hardwood stump'),
    ('SM_Tool_CementMixer_Electric', 'Wheeled Electric Cement Mixer', 'fixtures', 'Orange electric rotating drum cement mixer on wheeled A-frame'),
    ('SM_Tool_ToolChest_Rolling', 'Rolling Mechanic Tool Chest', 'fixtures', 'Red 6-drawer mechanic rolling tool chest with worktop mat'),
    ('SM_Tool_Sawhorse_Pair', 'Pair of Timber Sawhorses', 'fixtures', 'Pair of sturdy timber carpenters\' A-frame sawhorses'),

    # Forestry Handheld Tools (6)
    ('SM_Tool_Axe_Felling', 'Felling Axe (3.5lb, 36-Inch)', 'handheld', 'Hickory-handled professional felling axe with forged carbon steel head'),
    ('SM_Tool_Hatchet_Camp', 'Camp Hatchet (16-Inch)', 'handheld', 'Compact backpacking and kindling hatchet with carved ash grip'),
    ('SM_Tool_Chainsaw_Gas_16', '16-Inch Gas Chainsaw', 'handheld', '45cc 2-stroke gas chainsaw with 16-inch bar, chain & wrap handle'),
    ('SM_Tool_Chainsaw_Gas_20', '20-Inch Heavy Timber Chainsaw', 'handheld', '60cc heavy timber professional chainsaw with 20-inch guide bar'),
    ('SM_Tool_CantHook_Peavey', 'Logging Peavey Cant Hook', 'handheld', 'Heavy-duty log rolling peavey with forged steel duckbill hook & spike'),
    ('SM_Tool_Maul_Splitting', 'Splitting Maul (8lb, 36-Inch)', 'handheld', '8-pound sledge splitting maul with wedged cheeks for cordwood'),

    # Digging & Garden Hand Tools (7)
    ('SM_Tool_Shovel_RoundPoint', 'Round Point Digging Shovel', 'handheld', 'Heavy 14-gauge round point shovel with ash handle and forward-turned step'),
    ('SM_Tool_Shovel_ScoopFlat', 'Aluminum Grain & Snow Scoop', 'handheld', 'Large #10 aluminum ribbed grain scoop shovel with D-handle grip'),
    ('SM_Tool_Shovel_Trenching', 'Trenching / Clean-Out Shovel', 'handheld', '4-inch narrow trenching shovel with V-shaped blade for utility trenches'),
    ('SM_Tool_Hoe', 'Draw Cultivator Garden Hoe', 'handheld', 'Forged swan-neck garden draw hoe for weeding and furrow creation'),
    ('SM_Tool_Pickaxe', 'Clay Pick & Mattock (5lb)', 'handheld', 'Combination pointed pick and chisel mattock for hardpack and roots'),
    ('SM_Tool_Sickle', 'Harvest Forage Sickle', 'handheld', 'Curved serrated high-carbon steel harvesting sickle with walnut grip'),
    ('SM_Tool_Trowel_Hand', 'Cast Aluminum Hand Trowel', 'handheld', 'Graduated garden hand trowel with depth markings and rubber handle'),

    # Power Tools (6)
    ('SM_Tool_Drill_Cordless_20V', '20V Brushless Cordless Drill', 'powertools', '20V compact cordless drill driver with keyless chuck and lithium battery'),
    ('SM_Tool_ImpactDriver_Cordless', '20V Hex Impact Driver', 'powertools', 'High-torque 1/4-inch hex shank cordless impact driver'),
    ('SM_Tool_CircularSaw_Cordless', '7-1/4-Inch Cordless Circular Saw', 'powertools', 'Brushless 7-1/4-inch framing circular saw with carbide blade and shoe'),
    ('SM_Tool_AngleGrinder_Cordless', '4-1/2-Inch Cordless Angle Grinder', 'powertools', 'Heavy-duty 4-1/2-inch angle grinder with abrasive cutoff wheel & guard'),
    ('SM_Tool_MiterSaw', '10-Inch Sliding Compound Miter Saw', 'powertools', 'Benchtop 10-inch sliding compound miter saw with rotating turntable table'),
    ('SM_Tool_TableSaw', 'Jobsite Portable Table Saw', 'powertools', '10-inch jobsite contractor table saw on folding stand with rip fence'),

    # Homestead Care, Livestock & Safety (9)
    ('SM_Tool_WateringCan', 'Galvanized Steel Watering Can (2-Gal)', 'care', 'Classic 2-gallon galvanized sheet steel watering can with brass rose head'),
    ('SM_Tool_Shears_Pruning', 'Bypass Garden Pruning Shears', 'care', 'Forged steel bypass pruning secateurs with spring and safety lock'),
    ('SM_Tool_Loppers_Heavy', 'Heavy Bypass Branch Loppers (30-Inch)', 'care', 'Compound action 30-inch bypass tree branch loppers with cushioned grips'),
    ('SM_Tool_Sprayer_Backpack', '4-Gallon Backpack Crop Sprayer', 'care', 'Ergonomic 4-gallon chemical crop sprayer with brass spray wand and pump lever'),
    ('SM_Tool_Wand_Watering', 'Long-Reach Greenhouse Watering Wand', 'care', '30-inch anodized aluminum watering wand with thumb shutoff valve'),
    ('SM_Tool_Pail_Milk_Stainless', 'Seamless Stainless Steel Milk Pail', 'care', '13-quart seamless 304 stainless steel milking pail with heavy wire bail'),
    ('SM_Tool_Shears_SheepWool', 'Single-Bow Sheep Shearing Shears', 'care', 'Traditional high-carbon spring steel single-bow sheep wool shears'),
    ('SM_Tool_Paddle_Sorting', 'Livestock Sorting Rattle Paddle', 'care', 'Vinyl livestock sorting paddle with internal noise shaker beads'),
    ('SM_Tool_Helmet_LoggingSafety', 'Logging Safety Helmet & Mesh Shield', 'care', 'Hi-vis orange arborist hard hat with hearing muffs and steel mesh face shield'),
]

# 5. BUILDING MATERIALS, HARDWARE & TANKS (25)
MATERIALS_DEFS = [
    # Dimensional Materials (7)
    ('SM_Mat_Lumber_Stack_2x4', 'Banded 2x4 Lumber Stack', 'lumber', 'Steel-banded bundle of dimensional 2x4 framing studs on skids'),
    ('SM_Mat_Plywood_Stack', 'CDX Plywood Sheathing Stack', 'lumber', 'Stack of 4x8 CDX plywood sheathing boards on timber runners'),
    ('SM_Mat_Pallet_Wood', 'Standard GMA Shipping Pallet', 'lumber', 'Standard GMA/Euro heavy wooden warehouse shipping pallet'),
    ('SM_Mat_CinderBlocks_Stack', 'Pallet of Concrete Blocks', 'masonry', 'Tiered stack of 2-core hollow concrete cinder blocks on pallet'),
    ('SM_Mat_Brick_Pallet', 'Pallet of Red Clay Bricks', 'masonry', 'Banded pallet of red clay masonry construction bricks'),
    ('SM_Mat_Steel_Drum_55gal', '55-Gallon Steel Oil Drum', 'tanks', 'Blue 55-gallon steel fuel and chemical storage drum with bungs'),
    ('SM_Mat_PropaneTank_500gal', '500-Gallon Propane Torpedo Tank', 'tanks', '500-gallon horizontal torpedo LP gas propane tank on saddles'),

    # Campers & Farm Structures (4)
    ('SM_Struct_Camper_RV', 'Vintage Off-Grid Travel Trailer RV (5.9m)', 'structures', 'Tandem-axle vintage camper trailer with hitch, windows and entry door'),
    ('SM_Struct_Camper_Teardrop', 'Compact Teardrop Camper (3.0m)', 'structures', 'Lightweight off-road teardrop sleeper trailer with side door and rear galley'),
    ('SM_Struct_Silo', 'Galvanized Corrugated Grain Silo (9.0m)', 'structures', 'Galvanized corrugated sheet metal farm grain storage silo with access ladder'),
    ('SM_Struct_Stable', 'Homestead Livestock Stable Shed (6.0m)', 'structures', '2-stall timber homestead barn stable with dual open Dutch animal pens'),

    # Portable Fuel & Bulk Tanks (5)
    ('SM_Item_Fuel_GasCan_5gal', '5-Gallon Poly Gasoline Can', 'fuel', 'OSHA red 5-gallon CARB-compliant plastic gas can with flame arrestor'),
    ('SM_Item_Fuel_DieselCan_5gal', '5-Gallon Poly Diesel Can', 'fuel', 'Yellow 5-gallon polyethylene diesel fuel jerry can with pour spout'),
    ('SM_Item_Fuel_PropaneTank_20lb', '20lb Propane BBQ Cylinder', 'fuel', 'Standard white 20lb refillable LP propane cylinder with OPD valve'),
    ('SM_Item_Tank_Propane_1000gal', '1000-Gallon LP Propane Bullet Tank', 'fuel', 'Heavy 1000-gallon ASME LP gas bullet tank with brass service valves'),
    ('SM_Item_Tank_FuelBulk_Elevated', '300-Gallon Gravity Farm Fuel Tank', 'fuel', 'Elevated 300-gallon diesel storage skid tank with gravity hose and nozzle'),

    # Hardware & Fasteners (5)
    ('SM_Item_Hardware_FramingNails_Box', '16D Framing Nails Box (50lb)', 'hardware', '50lb cardboard carton of 3-1/2-inch smooth shank framing nails'),
    ('SM_Item_Hardware_DeckScrews_Box', '3-Inch Ceramic Deck Screws Tub (5lb)', 'hardware', '5lb plastic contractor tub of Torx T-25 coated outdoor deck screws'),
    ('SM_Item_Hardware_LagBolts_Box', 'Hex Lag Screws Box (1/2" x 6")', 'hardware', 'Heavy contractor box of 1/2-inch x 6-inch zinc-plated hex lag bolts'),
    ('SM_Item_Hardware_GateHinges_Pair', 'Heavy Heavy-Strap Farm Gate Hinges', 'hardware', 'Pair of forged 12-inch heavy-duty strap hinges with hinge pins'),
    ('SM_Item_Hardware_RebarBundle', '#4 Steel Rebar Bundle (10ft)', 'hardware', 'Bundle of 1/2-inch (#4) deformed reinforcing steel rebar rods tied with wire'),

    # Camp & Outdoor Living (4)
    ('SM_Camp_Tent_Canvas_Wall', 'Outfitter Wall Tent (2.4×3m)', 'camp', 'Heavy canvas outfitter wall tent with stovepipe flashing elbow'),
    ('SM_Camp_Tent_Dome', 'Geodesic Dome Tent (2×2m)', 'camp', 'Modern 2-person geodesic dome camping tent with crossed poles'),
    ('SM_Camp_Campfire_Ring', 'Natural Stone Campfire Ring', 'camp', 'Circular stone campfire ring with glowing coals and charred logs'),
    ('SM_Camp_PicnicTable_Wood', 'Timber A-Frame Picnic Table', 'camp', 'Heavy timber A-frame park picnic table with attached bench seats'),
]

# 6. LOGGING, FIREWOOD & SAWMILLS (7)
LOGGING_DEFS = [
    ('SM_Log_Pile_Large', 'Large Timber Log Pile', 'logging', 'Pyramid stack of 10 large cut timber logs with support chocks'),
    ('SM_Log_Pile_Medium', 'Medium Log Stack', 'logging', 'Stack of 6 cut firewood logs secured between side stakes'),
    ('SM_Firewood_Rack_Cord', 'Full Cord Firewood Rack', 'logging', 'Tubular steel rack stacked full of split seasoned cordwood'),
    ('SM_Firewood_Bundle_Wrapped', 'Wrapped Firewood Bundle', 'logging', 'Shrink-wrapped bundle of kiln-dried firewood with handle strap'),
    ('SM_Chopping_Block_Maul', 'Stump Chopping Block & Maul', 'logging', 'Oak stump chopping block with heavy splitting maul embedded'),
    ('SM_Machine_Sawmill_Portable', 'Towable Trailer Bandsaw Mill (6.5m)', 'sawmills', 'Gas-powered portable bandsaw sawmill mounted on highway trailer chassis'),
    ('SM_Machine_Sawmill_Stationary', 'Heavy Commercial Timber Sawmill (7.0m)', 'sawmills', 'Heavy stationary timber saw shed mill with structural steel track bed'),
]

# 7. WATERFRONT, FISHING & FISH (12)
FISHING_DEFS = [
    # Waterfront (2)
    ('SM_Water_Dock_Section_1x2m', 'Cedar Dock Section (1×2m)', 'waterfront', 'Modular cedar plank dock section with pilings and mooring cleats'),
    ('SM_Water_Rowboat_Wood', '10ft Wooden Rowing Skiff', 'waterfront', '10-foot cedar lapstrake wooden rowing skiff with oars'),

    # Tackle & Rods (7)
    ('SM_Item_Rod_FlyFishing', '9ft 5-Weight Fly Fishing Rod & Reel', 'tackle', 'Graphite 9ft fly rod with cork grip, aluminum arbor reel & fly line'),
    ('SM_Item_Rod_Spincast', '6ft Medium Spincast Fishing Combo', 'tackle', 'Push-button closed-face spincast reel combo with EVA foam grip'),
    ('SM_Item_Rod_Trolling', '7ft Heavy Lake Trolling Rod', 'tackle', 'Heavy-power conventional trolling rod with level-wind baitcaster reel'),
    ('SM_Item_Fishing_TackleBox', '3-Tray Cantilever Tackle Box', 'tackle', 'Classic blue 3-tier cantilever plastic tackle box with brass latch'),
    ('SM_Item_Fishing_LandingNet', 'Rubber Mesh Trout Landing Net', 'tackle', 'Teardrop hardwood landing net with knotless catch-and-release mesh'),
    ('SM_Item_Fishing_FishBasket', 'Floating Wire Mesh Fish Basket', 'tackle', 'Galvanized spring-loaded floating wire mesh live fish keeper basket'),
    ('SM_Item_Fishing_LureTray', '18-Compartment Utility Lure Tray', 'tackle', 'Clear polymer tackle organizer tray filled with spoons and crankbaits'),

    # Caught Fish (3)
    ('SM_Item_Fish_LargemouthBass', 'Trophy Largemouth Bass (44cm)', 'fish', 'Fresh caught 44cm largemouth bass with green lateral stripe & fins'),
    ('SM_Item_Fish_ChinookSalmon', 'King Chinook Salmon (64cm)', 'fish', 'Chrome silver 64cm trophy king salmon with spotted adipose fin'),
    ('SM_Item_Fish_RainbowTrout', 'Native Rainbow Trout (39cm)', 'fish', 'Stream-caught 39cm rainbow trout with vivid pink side band and black spots'),
]

def build_js_items(item_defs, obj_dir_rel):
    items = []
    for item_id, name, cat, desc in item_defs:
        obj_path = os.path.join(HUD_ROOT, obj_dir_rel, f"{item_id}.obj")
        stats = parse_obj(obj_path)
        if not stats:
            print(f"WARNING: Could not parse {obj_path}")
            dx = dy = dz = 0.0
            tris = 0
        else:
            dx, dy, dz = stats["dx"], stats["dy"], stats["dz"]
            tris = stats["tris"]
        
        footprint = f"{dx/100.0:.1f}×{dy/100.0:.1f}m ({dx:.0f}×{dy:.0f}cm)"
        height = f"{dz:.0f}cm"
        items.append({
            "id": item_id,
            "name": name,
            "cat": cat,
            "footprint": footprint,
            "height": height,
            "tris": tris,
            "desc": desc
        })
    return items

def format_js_array(items):
    lines = ["[\n"]
    for it in items:
        # escape single quotes
        name_esc = it['name'].replace("'", "\\'")
        desc_esc = it['desc'].replace("'", "\\'")
        lines.append(f"      {{ id: '{it['id']}', name: '{name_esc}', cat: '{it['cat']}', footprint: '{it['footprint']}', height: '{it['height']}', tris: {it['tris']}, desc: '{desc_esc}' }},\n")
    lines.append("    ];\n")
    return "".join(lines)

print("Building asset metadata from OBJ files...")
utl_items = build_js_items(UTILITY_DEFS, os.path.join("assets", "utilities", "models"))
ran_items = build_js_items(RANCHING_DEFS, os.path.join("assets", "ranching", "models"))
far_items = build_js_items(FARMING_DEFS, os.path.join("assets", "farming", "models"))
tls_items = build_js_items(TOOLS_DEFS, os.path.join("assets", "tools", "models"))
mat_items = build_js_items(MATERIALS_DEFS, os.path.join("assets", "building", "models"))
log_items = build_js_items(LOGGING_DEFS, os.path.join("assets", "logging", "models"))
fsh_items = build_js_items(FISHING_DEFS, os.path.join("assets", "fishing", "models"))

print(f"Parsed: Utilities={len(utl_items)}, Ranching={len(ran_items)}, Farming={len(far_items)}, Tools={len(tls_items)}, Materials={len(mat_items)}, Logging={len(log_items)}, Fishing={len(fsh_items)}")

# Now generate the HTML replacement chunk for index.html
# Let's inspect the target block in index.html: from line ~1224 to 1287:
with open(INDEX_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Replace HTML gallery sections:
# Search for:
# <!-- 3D Low-Poly Utilities & Infrastructure Section -->
# down to the end of props section before </section>
html_old_pattern = re.compile(r"<!-- 3D Low-Poly Utilities & Infrastructure Section -->.*?</div>\s*</div>\s*</div>\s*(?=</section>)", re.DOTALL)

new_html_sections = """<!-- 3D Low-Poly Utilities & Infrastructure Section -->
    <div class="gallery-section">
      <div class="gallery-title">
        <span>Homesteader Utilities & Infrastructure (40 Models & Matching 128×128 Icons)</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="res-btn active" id="btnFilterUtilityAll" onclick="filterUtilities('all')">All (40)</button>
          <button class="res-btn" id="btnFilterUtilityElectric" onclick="filterUtilities('electricity')">Electricity (18)</button>
          <button class="res-btn" id="btnFilterUtilityWater" onclick="filterUtilities('water')">Water (13)</button>
          <button class="res-btn" id="btnFilterUtilitySewage" onclick="filterUtilities('sewage')">Sewage (4)</button>
          <button class="res-btn" id="btnFilterUtilityNet" onclick="filterUtilities('internet')">Internet & Telecom (5)</button>
        </div>
      </div>
      <div class="gallery-grid" id="utilityGalleryGrid">
        <!-- Dynamically injected utility assets -->
      </div>
    </div>

    <!-- 3D Low-Poly Livestock & Ranching Section -->
    <div class="gallery-section">
      <div class="gallery-title">
        <span>Livestock, Ranching & Animal Yields (31 Models & Matching 128×128 Icons)</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="res-btn active" id="btnFilterRanchAll" onclick="filterRanching('all')">All (31)</button>
          <button class="res-btn" id="btnFilterRanchAnimals" onclick="filterRanching('animals')">Livestock Animals (10)</button>
          <button class="res-btn" id="btnFilterRanchFencing" onclick="filterRanching('fencing')">Feed & Fencing (11)</button>
          <button class="res-btn" id="btnFilterRanchYields" onclick="filterRanching('yields')">Animal Yields, Meats & Pelts (10)</button>
        </div>
      </div>
      <div class="gallery-grid" id="ranchingGalleryGrid">
        <!-- Dynamically injected ranching assets -->
      </div>
    </div>

    <!-- 3D Low-Poly Crops & Farm Equipment Section -->
    <div class="gallery-section">
      <div class="gallery-title">
        <span>Crops, Farm Tractors, Harvest Produce & Seeds (40 Models & Matching 128×128 Icons)</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="res-btn active" id="btnFilterFarmAll" onclick="filterFarming('all')">All (40)</button>
          <button class="res-btn" id="btnFilterFarmCrops" onclick="filterFarming('crops')">Field Crops (8)</button>
          <button class="res-btn" id="btnFilterFarmMachinery" onclick="filterFarming('machinery')">Tractors & Combines (4)</button>
          <button class="res-btn" id="btnFilterFarmEquip" onclick="filterFarming('equipment')">Farm Tools (4)</button>
          <button class="res-btn" id="btnFilterFarmProduce" onclick="filterFarming('produce')">Harvested Produce & Food (14)</button>
          <button class="res-btn" id="btnFilterFarmSeeds" onclick="filterFarming('seeds')">Seed Packets (10)</button>
        </div>
      </div>
      <div class="gallery-grid" id="farmingGalleryGrid">
        <!-- Dynamically injected farming assets -->
      </div>
    </div>

    <!-- 3D Low-Poly Workshop & Handheld Tools Section -->
    <div class="gallery-section">
      <div class="gallery-title">
        <span>Workshop Fixtures, Excavators & Handheld Tools (37 Models & Matching 128×128 Icons)</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="res-btn active" id="btnFilterToolsAll" onclick="filterTools('all')">All (37)</button>
          <button class="res-btn" id="btnFilterToolsEarthmoving" onclick="filterTools('earthmoving')">Earthmovers (4)</button>
          <button class="res-btn" id="btnFilterToolsFixtures" onclick="filterTools('fixtures')">Shop Fixtures (5)</button>
          <button class="res-btn" id="btnFilterToolsHandheld" onclick="filterTools('handheld')">Forestry & Digging (13)</button>
          <button class="res-btn" id="btnFilterToolsPower" onclick="filterTools('powertools')">Power Tools (6)</button>
          <button class="res-btn" id="btnFilterToolsCare" onclick="filterTools('care')">Homestead Care & Safety (9)</button>
        </div>
      </div>
      <div class="gallery-grid" id="toolsGalleryGrid">
        <!-- Dynamically injected tools assets -->
      </div>
    </div>

    <!-- 3D Low-Poly Building Materials, Tanks, Campers & Hardware Section -->
    <div class="gallery-section">
      <div class="gallery-title">
        <span>Building Materials, Tanks, Hardware & Camp (25 Models & Matching 128×128 Icons)</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="res-btn active" id="btnFilterMatAll" onclick="filterMaterials('all')">All (25)</button>
          <button class="res-btn" id="btnFilterMatLumber" onclick="filterMaterials('lumber')">Lumber & Masonry (7)</button>
          <button class="res-btn" id="btnFilterMatStructures" onclick="filterMaterials('structures')">Campers & Silos (4)</button>
          <button class="res-btn" id="btnFilterMatFuel" onclick="filterMaterials('fuel')">Fuel & Tanks (5)</button>
          <button class="res-btn" id="btnFilterMatHardware" onclick="filterMaterials('hardware')">Hardware (5)</button>
          <button class="res-btn" id="btnFilterMatCamp" onclick="filterMaterials('camp')">Camp (4)</button>
        </div>
      </div>
      <div class="gallery-grid" id="materialsGalleryGrid">
        <!-- Dynamically injected building materials assets -->
      </div>
    </div>

    <!-- 3D Low-Poly Logging, Firewood & Sawmills Section -->
    <div class="gallery-section">
      <div class="gallery-title">
        <span>Logging, Firewood & Sawmills (7 Models & Matching 128×128 Icons)</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="res-btn active" id="btnFilterLogAll" onclick="filterLogging('all')">All (7)</button>
          <button class="res-btn" id="btnFilterLogPiles" onclick="filterLogging('logging')">Log Piles & Cordwood (5)</button>
          <button class="res-btn" id="btnFilterLogSawmills" onclick="filterLogging('sawmills')">Sawmills (2)</button>
        </div>
      </div>
      <div class="gallery-grid" id="loggingGalleryGrid">
        <!-- Dynamically injected logging assets -->
      </div>
    </div>

    <!-- 3D Low-Poly Waterfront, Fishing Gear & Trophy Fish Section -->
    <div class="gallery-section">
      <div class="gallery-title">
        <span>Waterfront, Fishing Gear & Caught Fish (12 Models & Matching 128×128 Icons)</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="res-btn active" id="btnFilterFishAll" onclick="filterFishing('all')">All (12)</button>
          <button class="res-btn" id="btnFilterFishWaterfront" onclick="filterFishing('waterfront')">Dock & Boat (2)</button>
          <button class="res-btn" id="btnFilterFishTackle" onclick="filterFishing('tackle')">Rods & Tackle (7)</button>
          <button class="res-btn" id="btnFilterFishTrophy" onclick="filterFishing('fish')">Trophy Fish (3)</button>
        </div>
      </div>
      <div class="gallery-grid" id="fishingGalleryGrid">
        <!-- Dynamically injected fishing assets -->
      </div>
    </div>
"""

if not html_old_pattern.search(content):
    print("ERROR: Could not find old HTML gallery sections pattern!")
else:
    content = html_old_pattern.sub(new_html_sections, content)
    print("Replaced HTML gallery sections successfully!")

# Now replace the JS script block for UTILITY_ASSETS, RANCHING_ASSETS, FARMING_ASSETS, PROPS_ASSETS:
js_old_pattern = re.compile(r"// =========================================================================\s*// 3D ASSETS: UTILITIES, RANCHING, FARMING, PROPS.*?renderPropsGallery\(\);\s*renderPropsGallery\(\);?", re.DOTALL)

# Let's check how the render calls at the bottom are placed:
render_calls_pattern = re.compile(r"renderIconGallery\(\);\s*renderGroundTilesGallery\(\);\s*renderBuildingGallery\(\);\s*renderFoliageGallery\(\);\s*renderUtilityGallery\(\);\s*renderRanchingGallery\(\);\s*renderFarmingGallery\(\);\s*renderPropsGallery\(\);", re.DOTALL)

new_render_calls = """renderIconGallery();
    renderGroundTilesGallery();
    renderBuildingGallery();
    renderFoliageGallery();
    renderUtilityGallery();
    renderRanchingGallery();
    renderFarmingGallery();
    renderToolsGallery();
    renderMaterialsGallery();
    renderLoggingGallery();
    renderFishingGallery();"""

# Build complete JS block:
new_js_block = f"""// =========================================================================
    // 3D ASSETS: UTILITIES, RANCHING, FARMING, TOOLS, MATERIALS, LOGGING, FISHING (192 MODELS)
    // =========================================================================

    const UTILITY_ASSETS = {format_js_array(utl_items)}
    let currentUtilityCategory = 'all';

    function renderUtilityGallery() {{
      const grid = document.getElementById('utilityGalleryGrid');
      if (!grid) return;
      grid.innerHTML = '';
      const filtered = currentUtilityCategory === 'all'
        ? UTILITY_ASSETS
        : UTILITY_ASSETS.filter(it => it.cat === currentUtilityCategory);

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
      const btnMap = {{
        all: 'btnFilterUtilityAll',
        electricity: 'btnFilterUtilityElectric',
        water: 'btnFilterUtilityWater',
        sewage: 'btnFilterUtilitySewage',
        internet: 'btnFilterUtilityNet'
      }};
      Object.values(btnMap).forEach(btnId => {{
        const btn = document.getElementById(btnId);
        if (btn) btn.classList.remove('active');
      }});
      const activeBtn = document.getElementById(btnMap[cat]);
      if (activeBtn) activeBtn.classList.add('active');
      renderUtilityGallery();
    }}

    const RANCHING_ASSETS = {format_js_array(ran_items)}
    let currentRanchCategory = 'all';

    function renderRanchingGallery() {{
      const grid = document.getElementById('ranchingGalleryGrid');
      if (!grid) return;
      grid.innerHTML = '';
      const filtered = currentRanchCategory === 'all'
        ? RANCHING_ASSETS
        : RANCHING_ASSETS.filter(it => it.cat === currentRanchCategory);

      filtered.forEach(item => {{
        const card = document.createElement('div');
        card.className = 'asset-card';
        card.innerHTML = `
          <div class="asset-thumb" style="background: radial-gradient(circle, #1a2332 0%, #0d121a 100%);">
            <img src="assets/ranching/icons/${{item.id}}.png" alt="${{item.name}}" loading="lazy" style="width:100%;height:100%;object-fit:contain;">
          </div>
          <div class="asset-name" style="color:#f8fafc;font-size:13px;font-weight:700;">${{item.name}}</div>
          <div class="asset-dims" style="color:#94a3b8;font-size:10px;margin-top:2px;">${{item.desc}}</div>
          <div class="asset-dims" style="color:#e08a3c;font-size:9.5px;margin-top:4px;">📐 ${{item.footprint}} · H: ${{item.height}} · ${{item.tris}} Tris</div>
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
      const btnMap = {{
        all: 'btnFilterRanchAll',
        animals: 'btnFilterRanchAnimals',
        fencing: 'btnFilterRanchFencing',
        yields: 'btnFilterRanchYields'
      }};
      Object.values(btnMap).forEach(btnId => {{
        const btn = document.getElementById(btnId);
        if (btn) btn.classList.remove('active');
      }});
      const activeBtn = document.getElementById(btnMap[cat]);
      if (activeBtn) activeBtn.classList.add('active');
      renderRanchingGallery();
    }}

    const FARMING_ASSETS = {format_js_array(far_items)}
    let currentFarmCategory = 'all';

    function renderFarmingGallery() {{
      const grid = document.getElementById('farmingGalleryGrid');
      if (!grid) return;
      grid.innerHTML = '';
      const filtered = currentFarmCategory === 'all'
        ? FARMING_ASSETS
        : FARMING_ASSETS.filter(it => it.cat === currentFarmCategory);

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
      const btnMap = {{
        all: 'btnFilterFarmAll',
        crops: 'btnFilterFarmCrops',
        machinery: 'btnFilterFarmMachinery',
        equipment: 'btnFilterFarmEquip',
        produce: 'btnFilterFarmProduce',
        seeds: 'btnFilterFarmSeeds'
      }};
      Object.values(btnMap).forEach(btnId => {{
        const btn = document.getElementById(btnId);
        if (btn) btn.classList.remove('active');
      }});
      const activeBtn = document.getElementById(btnMap[cat]);
      if (activeBtn) activeBtn.classList.add('active');
      renderFarmingGallery();
    }}

    const TOOLS_ASSETS = {format_js_array(tls_items)}
    let currentToolsCategory = 'all';

    function renderToolsGallery() {{
      const grid = document.getElementById('toolsGalleryGrid');
      if (!grid) return;
      grid.innerHTML = '';
      const filtered = currentToolsCategory === 'all'
        ? TOOLS_ASSETS
        : TOOLS_ASSETS.filter(it => it.cat === currentToolsCategory);

      filtered.forEach(item => {{
        const card = document.createElement('div');
        card.className = 'asset-card';
        card.innerHTML = `
          <div class="asset-thumb" style="background: radial-gradient(circle, #1a2332 0%, #0d121a 100%);">
            <img src="assets/tools/icons/${{item.id}}.png" alt="${{item.name}}" loading="lazy" style="width:100%;height:100%;object-fit:contain;">
          </div>
          <div class="asset-name" style="color:#f8fafc;font-size:13px;font-weight:700;">${{item.name}}</div>
          <div class="asset-dims" style="color:#94a3b8;font-size:10px;margin-top:2px;">${{item.desc}}</div>
          <div class="asset-dims" style="color:#e08a3c;font-size:9.5px;margin-top:4px;">📐 ${{item.footprint}} · H: ${{item.height}} · ${{item.tris}} Tris</div>
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
      const btnMap = {{
        all: 'btnFilterToolsAll',
        earthmoving: 'btnFilterToolsEarthmoving',
        fixtures: 'btnFilterToolsFixtures',
        handheld: 'btnFilterToolsHandheld',
        powertools: 'btnFilterToolsPower',
        care: 'btnFilterToolsCare'
      }};
      Object.values(btnMap).forEach(btnId => {{
        const btn = document.getElementById(btnId);
        if (btn) btn.classList.remove('active');
      }});
      const activeBtn = document.getElementById(btnMap[cat]);
      if (activeBtn) activeBtn.classList.add('active');
      renderToolsGallery();
    }}

    const MATERIALS_ASSETS = {format_js_array(mat_items)}
    let currentMaterialsCategory = 'all';

    function renderMaterialsGallery() {{
      const grid = document.getElementById('materialsGalleryGrid');
      if (!grid) return;
      grid.innerHTML = '';
      const filtered = currentMaterialsCategory === 'all'
        ? MATERIALS_ASSETS
        : MATERIALS_ASSETS.filter(it => it.cat === currentMaterialsCategory);

      filtered.forEach(item => {{
        const card = document.createElement('div');
        card.className = 'asset-card';
        card.innerHTML = `
          <div class="asset-thumb" style="background: radial-gradient(circle, #1a2332 0%, #0d121a 100%);">
            <img src="assets/building/icons/${{item.id}}.png" alt="${{item.name}}" loading="lazy" style="width:100%;height:100%;object-fit:contain;">
          </div>
          <div class="asset-name" style="color:#f8fafc;font-size:13px;font-weight:700;">${{item.name}}</div>
          <div class="asset-dims" style="color:#94a3b8;font-size:10px;margin-top:2px;">${{item.desc}}</div>
          <div class="asset-dims" style="color:#e08a3c;font-size:9.5px;margin-top:4px;">📐 ${{item.footprint}} · H: ${{item.height}} · ${{item.tris}} Tris</div>
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
      const btnMap = {{
        all: 'btnFilterMatAll',
        lumber: 'btnFilterMatLumber',
        structures: 'btnFilterMatStructures',
        fuel: 'btnFilterMatFuel',
        hardware: 'btnFilterMatHardware',
        camp: 'btnFilterMatCamp'
      }};
      Object.values(btnMap).forEach(btnId => {{
        const btn = document.getElementById(btnId);
        if (btn) btn.classList.remove('active');
      }});
      const activeBtn = document.getElementById(btnMap[cat]);
      if (activeBtn) activeBtn.classList.add('active');
      renderMaterialsGallery();
    }}

    const LOGGING_ASSETS = {format_js_array(log_items)}
    let currentLoggingCategory = 'all';

    function renderLoggingGallery() {{
      const grid = document.getElementById('loggingGalleryGrid');
      if (!grid) return;
      grid.innerHTML = '';
      const filtered = currentLoggingCategory === 'all'
        ? LOGGING_ASSETS
        : LOGGING_ASSETS.filter(it => it.cat === currentLoggingCategory);

      filtered.forEach(item => {{
        const card = document.createElement('div');
        card.className = 'asset-card';
        card.innerHTML = `
          <div class="asset-thumb" style="background: radial-gradient(circle, #1a2332 0%, #0d121a 100%);">
            <img src="assets/logging/icons/${{item.id}}.png" alt="${{item.name}}" loading="lazy" style="width:100%;height:100%;object-fit:contain;">
          </div>
          <div class="asset-name" style="color:#f8fafc;font-size:13px;font-weight:700;">${{item.name}}</div>
          <div class="asset-dims" style="color:#94a3b8;font-size:10px;margin-top:2px;">${{item.desc}}</div>
          <div class="asset-dims" style="color:#e08a3c;font-size:9.5px;margin-top:4px;">📐 ${{item.footprint}} · H: ${{item.height}} · ${{item.tris}} Tris</div>
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
      const btnMap = {{
        all: 'btnFilterLogAll',
        logging: 'btnFilterLogPiles',
        sawmills: 'btnFilterLogSawmills'
      }};
      Object.values(btnMap).forEach(btnId => {{
        const btn = document.getElementById(btnId);
        if (btn) btn.classList.remove('active');
      }});
      const activeBtn = document.getElementById(btnMap[cat]);
      if (activeBtn) activeBtn.classList.add('active');
      renderLoggingGallery();
    }}

    const FISHING_ASSETS = {format_js_array(fsh_items)}
    let currentFishingCategory = 'all';

    function renderFishingGallery() {{
      const grid = document.getElementById('fishingGalleryGrid');
      if (!grid) return;
      grid.innerHTML = '';
      const filtered = currentFishingCategory === 'all'
        ? FISHING_ASSETS
        : FISHING_ASSETS.filter(it => it.cat === currentFishingCategory);

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
      const btnMap = {{
        all: 'btnFilterFishAll',
        waterfront: 'btnFilterFishWaterfront',
        tackle: 'btnFilterFishTackle',
        fish: 'btnFilterFishTrophy'
      }};
      Object.values(btnMap).forEach(btnId => {{
        const btn = document.getElementById(btnId);
        if (btn) btn.classList.remove('active');
      }});
      const activeBtn = document.getElementById(btnMap[cat]);
      if (activeBtn) activeBtn.classList.add('active');
      renderFishingGallery();
    }}
"""

# Now replace the old JS block and render calls in content:
# First search where UTILITY_ASSETS starts:
idx_utl_start = content.find("const UTILITY_ASSETS =")
if idx_utl_start == -1:
    print("ERROR: Could not find const UTILITY_ASSETS in index.html")
else:
    # Find where renderIconGallery() begins:
    idx_render_start = content.find("renderIconGallery();", idx_utl_start)
    if idx_render_start == -1:
        print("ERROR: Could not find renderIconGallery() in index.html")
    else:
        # Find where downloadRaster starts:
        idx_raster_start = content.find("// Client-side instant SVG-to-PNG rasterizer", idx_render_start)
        if idx_raster_start == -1:
            print("ERROR: Could not find downloadRaster in index.html")
        else:
            # Replace the JS data/functions and render calls:
            content = content[:idx_utl_start] + new_js_block.lstrip() + "\n    // Initial render\n    " + new_render_calls + "\n\n    " + content[idx_raster_start:]
            print("Replaced JS blocks and initial render calls successfully!")

# Write updated index.html
with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Updated index.html ({len(content)} bytes). Validating HTML syntax...")

class SimpleHTMLValidator(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.void_tags = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
        self.errors = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() not in self.void_tags:
            self.tags.append(tag.lower())
    def handle_endtag(self, tag):
        tag_l = tag.lower()
        if tag_l in self.void_tags:
            return
        if not self.tags:
            self.errors.append(f"Unexpected closing tag </{tag}>")
            return
        last = self.tags.pop()
        if last != tag_l:
            self.errors.append(f"Mismatched tag: expected </{last}>, found </{tag}>")

val = SimpleHTMLValidator()
val.feed(content)
if val.errors:
    print("HTML validation warnings/errors:")
    for err in val.errors[:10]:
        print("  -", err)
else:
    print(f"HTML VALIDATION PASSED! All tags balanced. Remaining open: {val.tags}")
