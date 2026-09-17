#!/usr/bin/env python3
"""Catalog data for the batch-2 expansion (trees/saplings/logs, livestock,
rocks/bucket, structures, material piles). Same shape as item_catalog_data.py."""

CATALOG = {
    # TREES
    "tree_oak": ("Oak Tree", "A full-grown oak tree with a broad leafy canopy.", "Material", 1, 400.0, 0.0),
    "tree_pine": ("Pine Tree", "A tall conical evergreen pine tree.", "Material", 1, 350.0, 0.0),
    "tree_birch": ("Birch Tree", "A slender birch tree with white bark.", "Material", 1, 300.0, 0.0),
    "tree_maple": ("Maple Tree", "A maple tree with vibrant autumn-red leaves.", "Material", 1, 380.0, 0.0),

    # SAPLINGS
    "sapling_oak": ("Oak Sapling", "A young oak sapling with its roots wrapped in burlap and ready to plant.", "Material", 10, 4.0, 15.0),
    "sapling_pine": ("Pine Sapling", "A young pine sapling with its roots wrapped in burlap and ready to plant.", "Material", 10, 3.5, 15.0),
    "sapling_birch": ("Birch Sapling", "A young birch sapling with its roots wrapped in burlap and ready to plant.", "Material", 10, 3.5, 15.0),
    "sapling_maple": ("Maple Sapling", "A young maple sapling with its roots wrapped in burlap and ready to plant.", "Material", 10, 3.5, 15.0),

    # LOGS
    "log_oak": ("Oak Log", "A thick cut oak log with rough dark bark.", "Material", 20, 18.0, 6.0),
    "log_pine": ("Pine Log", "A cut pine log with pale resin-streaked bark.", "Material", 20, 14.0, 4.0),
    "log_birch": ("Birch Log", "A cut birch log with papery white bark.", "Material", 20, 12.0, 4.0),
    "log_maple": ("Maple Log", "A cut maple log with smooth gray-brown bark.", "Material", 20, 16.0, 5.0),

    # LIVESTOCK
    "livestock_cow_holstein": ("Holstein Cow", "A black and white Holstein dairy cow.", "Livestock", 1, 700.0, 800.0),
    "livestock_cow_jersey": ("Jersey Cow", "A light tan Jersey dairy cow.", "Livestock", 1, 650.0, 750.0),
    "livestock_cow_highland": ("Highland Cow", "A shaggy reddish-brown Highland cow with long horns.", "Livestock", 1, 750.0, 900.0),
    "livestock_chicken_white": ("White Leghorn Chicken", "A white Leghorn egg-laying chicken.", "Livestock", 1, 2.0, 25.0),
    "livestock_chicken_red": ("Rhode Island Red Chicken", "A reddish-brown Rhode Island Red chicken.", "Livestock", 1, 2.2, 25.0),
    "livestock_chicken_barred": ("Barred Rock Chicken", "A black and white barred-feather chicken.", "Livestock", 1, 2.2, 25.0),
    "livestock_pig_pink": ("Pink Pig", "A pink domestic pig with a curly tail.", "Livestock", 1, 90.0, 200.0),
    "livestock_pig_hampshire": ("Hampshire Pig", "A black pig with a white belt stripe.", "Livestock", 1, 95.0, 220.0),
    "livestock_pig_duroc": ("Duroc Pig", "A reddish-brown Duroc pig.", "Livestock", 1, 95.0, 220.0),
    "livestock_sheep_white": ("White Sheep", "A sheep with white wool fleece.", "Livestock", 1, 65.0, 180.0),
    "livestock_sheep_suffolk": ("Suffolk Sheep", "A sheep with white wool and a black face and legs.", "Livestock", 1, 68.0, 190.0),
    "livestock_sheep_tan": ("Tan Sheep", "A sheep with tan-brown wool fleece.", "Livestock", 1, 65.0, 180.0),
    "livestock_goat_white": ("White Goat", "A solid white goat with short horns.", "Livestock", 1, 55.0, 150.0),
    "livestock_goat_brown": ("Brown Goat", "A brown and tan goat with short horns.", "Livestock", 1, 55.0, 150.0),
    "livestock_goat_blackwhite": ("Black & White Goat", "A black and white patched goat with short horns.", "Livestock", 1, 55.0, 150.0),

    # ROCKS
    "mat_rock_small": ("Small Rock", "A small fist-sized stone.", "Material", 30, 2.0, 1.0),
    "mat_rock_medium": ("Medium Rock", "A medium-sized cracked granite rock.", "Material", 15, 8.0, 3.0),
    "mat_rock_large": ("Large Rock", "A large moss-flecked rock.", "Material", 5, 25.0, 8.0),
    "mat_boulder": ("Boulder", "A huge rough boulder.", "Material", 1, 90.0, 25.0),

    # BUCKET
    "item_bucket_empty": ("Steel Bucket", "An empty galvanized steel bucket.", "Tool", 1, 1.5, 10.0),
    "item_bucket_water": ("Bucket of Water", "A galvanized steel bucket filled with water.", "Tool", 1, 6.0, 10.0),

    # STRUCTURES
    "struct_tent_dome": ("Dome Tent", "A small two-person dome camping tent.", "Structure", 1, 8.0, 60.0),
    "struct_tent_canvas": ("Canvas Wall Tent", "A canvas A-frame wall tent with wood support poles.", "Structure", 1, 35.0, 220.0),
    "struct_camper_teardrop": ("Teardrop Camper", "A small teardrop travel trailer.", "Structure", 1, 550.0, 4500.0),
    "struct_camper_rv": ("Travel Trailer RV", "A larger travel trailer with an awning.", "Structure", 1, 1800.0, 12000.0),
    "struct_cabin_small": ("Small Log Cabin", "A one-room log cabin with a peaked roof.", "Structure", 1, 5000.0, 8000.0),
    "struct_cabin_large": ("Large Log Cabin", "A two-story log cabin with a porch and stone chimney.", "Structure", 1, 9000.0, 18000.0),
    "struct_house_starter": ("Starter House", "A small single-story starter homestead house.", "Structure", 1, 12000.0, 25000.0),
    "struct_house_farmhouse": ("Farmhouse", "A two-story farmhouse with a wraparound porch.", "Structure", 1, 22000.0, 55000.0),

    # PILES
    "mat_pile_gravel_small": ("Small Gravel Pile", "A small pile of crushed gravel.", "Material", 10, 40.0, 5.0),
    "mat_pile_dirt_small": ("Small Dirt Pile", "A small pile of loose dirt.", "Material", 10, 35.0, 3.0),
    "mat_pile_sand_small": ("Small Sand Pile", "A small pile of sand.", "Material", 10, 35.0, 4.0),
    "mat_pile_mulch_small": ("Small Mulch Pile", "A small pile of wood mulch chips.", "Material", 10, 20.0, 6.0),
    "mat_pile_manure_small": ("Small Manure Pile", "A small pile of composted manure.", "Material", 10, 30.0, 4.0),
    "mat_pile_gravel_medium": ("Medium Gravel Pile", "A medium mound of crushed gravel.", "Material", 3, 120.0, 15.0),
    "mat_pile_dirt_medium": ("Medium Dirt Pile", "A medium mound of loose dirt.", "Material", 3, 105.0, 9.0),
    "mat_pile_sand_medium": ("Medium Sand Pile", "A medium mound of sand.", "Material", 3, 105.0, 12.0),
    "mat_pile_mulch_medium": ("Medium Mulch Pile", "A medium mound of wood mulch chips.", "Material", 3, 60.0, 18.0),
    "mat_pile_manure_medium": ("Medium Manure Pile", "A medium mound of composted manure.", "Material", 3, 90.0, 12.0),
    "mat_pile_gravel_large": ("Large Gravel Pile", "A large mound of crushed gravel.", "Material", 1, 300.0, 35.0),
    "mat_pile_dirt_large": ("Large Dirt Pile", "A large mound of loose dirt.", "Material", 1, 260.0, 20.0),
    "mat_pile_sand_large": ("Large Sand Pile", "A large mound of sand.", "Material", 1, 260.0, 28.0),
    "mat_pile_mulch_large": ("Large Mulch Pile", "A large mound of wood mulch chips.", "Material", 1, 150.0, 40.0),
    "mat_pile_manure_large": ("Large Manure Pile", "A large mound of composted manure.", "Material", 1, 220.0, 28.0),
}
