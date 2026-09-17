#!/usr/bin/env python3
"""Catalog data for batch 3 (tree growth stages, baby animals, log piles,
farm buildings, fencing, power poles, ground clutter, docks, fixed material
piles) and batch 4 (lumber/sheet bundles, hay/straw/silage bales, boxes)."""

CATALOG = {
    # TREE GROWTH STAGES
    "tree_oak_small": ("Young Oak Tree", "A young oak tree that is already past the sapling stage.", "Material", 1, 120.0, 0.0),
    "tree_oak_medium": ("Half-Grown Oak Tree", "A half-grown oak tree that is nearing maturity.", "Material", 1, 260.0, 0.0),
    "tree_pine_small": ("Young Pine Tree", "A young pine tree that is already past the sapling stage.", "Material", 1, 100.0, 0.0),
    "tree_pine_medium": ("Half-Grown Pine Tree", "A half-grown pine tree that is nearing maturity.", "Material", 1, 230.0, 0.0),
    "tree_birch_small": ("Young Birch Tree", "A young birch tree that is already past the sapling stage.", "Material", 1, 90.0, 0.0),
    "tree_birch_medium": ("Half-Grown Birch Tree", "A half-grown birch tree that is nearing maturity.", "Material", 1, 200.0, 0.0),
    "tree_maple_small": ("Young Maple Tree", "A young maple tree that is already past the sapling stage.", "Material", 1, 110.0, 0.0),
    "tree_maple_medium": ("Half-Grown Maple Tree", "A half-grown maple tree that is nearing maturity.", "Material", 1, 250.0, 0.0),

    # BABY ANIMALS
    "baby_calf": ("Calf", "A baby cow calf.", "Livestock", 1, 60.0, 150.0),
    "baby_calf_spotted": ("Spotted Calf", "A baby cow calf with a spotted coat.", "Livestock", 1, 60.0, 150.0),
    "baby_chick": ("Chick", "A fluffy baby chick.", "Livestock", 1, 0.5, 8.0),
    "baby_piglet": ("Piglet", "A baby pig.", "Livestock", 1, 8.0, 40.0),
    "baby_lamb": ("Lamb", "A baby sheep.", "Livestock", 1, 6.0, 35.0),
    "baby_kid": ("Kid", "A baby goat.", "Livestock", 1, 5.0, 30.0),

    # LOG PILES
    "pile_logs_oak_small": ("Small Oak Log Pile", "A small stack of cut oak logs.", "Material", 5, 40.0, 15.0),
    "pile_logs_oak_medium": ("Medium Oak Log Pile", "A medium stack of cut oak logs.", "Material", 2, 90.0, 32.0),
    "pile_logs_oak_large": ("Large Oak Log Pile", "A large stack of cut oak logs.", "Material", 1, 190.0, 65.0),
    "pile_logs_pine_small": ("Small Pine Log Pile", "A small stack of cut pine logs.", "Material", 5, 32.0, 10.0),
    "pile_logs_pine_medium": ("Medium Pine Log Pile", "A medium stack of cut pine logs.", "Material", 2, 72.0, 22.0),
    "pile_logs_pine_large": ("Large Pine Log Pile", "A large stack of cut pine logs.", "Material", 1, 150.0, 45.0),
    "pile_logs_birch_small": ("Small Birch Log Pile", "A small stack of cut birch logs.", "Material", 5, 28.0, 9.0),
    "pile_logs_birch_medium": ("Medium Birch Log Pile", "A medium stack of cut birch logs.", "Material", 2, 64.0, 20.0),
    "pile_logs_birch_large": ("Large Birch Log Pile", "A large stack of cut birch logs.", "Material", 1, 135.0, 40.0),
    "pile_logs_maple_small": ("Small Maple Log Pile", "A small stack of cut maple logs.", "Material", 5, 36.0, 12.0),
    "pile_logs_maple_medium": ("Medium Maple Log Pile", "A medium stack of cut maple logs.", "Material", 2, 82.0, 26.0),
    "pile_logs_maple_large": ("Large Maple Log Pile", "A large stack of cut maple logs.", "Material", 1, 170.0, 52.0),

    # FARM BUILDINGS
    "struct_barn": ("Barn", "A classic red barn with a gambrel roof.", "Structure", 1, 15000.0, 30000.0),
    "struct_silo": ("Grain Silo", "A tall cylindrical metal grain silo.", "Structure", 1, 8000.0, 20000.0),
    "struct_coop_chicken": ("Chicken Coop", "A small chicken coop with a fenced run.", "Structure", 1, 600.0, 900.0),
    "struct_greenhouse": ("Greenhouse", "A greenhouse with glass panels.", "Structure", 1, 2500.0, 4000.0),
    "struct_shed": ("Tool Shed", "A small wooden tool shed.", "Structure", 1, 450.0, 700.0),
    "struct_stable": ("Horse Stable", "A stable with multiple stall doors.", "Structure", 1, 9000.0, 15000.0),

    # FENCING
    "fence_wood": ("Wood Fence Section", "A section of wooden picket fence.", "Material", 20, 12.0, 8.0),
    "fence_wire": ("Wire Fence Section", "A section of woven wire livestock fence.", "Material", 20, 9.0, 10.0),
    "gate_wood": ("Wood Farm Gate", "A wooden farm gate with diagonal bracing.", "Material", 5, 25.0, 40.0),
    "gate_metal": ("Metal Farm Gate", "A galvanized metal tube farm gate.", "Material", 5, 35.0, 65.0),

    # POWER POLES
    "item_power_pole_wood": ("Wood Power Pole", "A wooden utility pole with a crossarm and insulators.", "Material", 3, 180.0, 200.0),
    "item_power_pole_metal": ("Transmission Tower", "A metal lattice electrical transmission tower.", "Material", 1, 900.0, 1500.0),

    # GROUND CLUTTER
    "clutter_leaves": ("Fallen Leaves", "A scattered pile of fallen autumn leaves.", "Material", 20, 0.2, 0.0),
    "clutter_pebbles": ("Pebbles", "A scattered cluster of small pebbles.", "Material", 20, 0.5, 0.0),
    "clutter_twigs": ("Twigs", "A scattered cluster of dry twigs.", "Material", 20, 0.3, 0.0),
    "clutter_pinecones": ("Pinecones", "A pair of fallen pinecones.", "Material", 20, 0.2, 0.0),
    "clutter_acorns": ("Acorns", "A few scattered acorns.", "Material", 20, 0.1, 0.0),
    "clutter_grass_tuft": ("Grass Tuft", "A tuft of green grass.", "Material", 20, 0.1, 0.0),
    "clutter_dirt_clump": ("Dirt Clump", "A small clump of dirt.", "Material", 20, 0.4, 0.0),
    "clutter_branch": ("Fallen Branch", "A fallen tree branch.", "Material", 10, 1.5, 0.0),

    # DOCKS
    "dock_small_new": ("Small New Dock", "A small new wooden dock section.", "Structure", 1, 300.0, 800.0),
    "dock_small_old": ("Small Old Dock", "A small weathered wooden dock section.", "Structure", 1, 280.0, 300.0),
    "dock_large_new": ("Large New Dock", "A large new wooden dock section with a railing.", "Structure", 1, 700.0, 1800.0),
    "dock_large_old": ("Large Old Dock", "A large weathered wooden dock section with a broken railing.", "Structure", 1, 650.0, 600.0),

    # MATERIAL PILES (redo — replaces earlier undersized medium tier)
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

    # LUMBER / SHEET BUNDLES
    "lumber_bundle_2x4_small": ("Small 2x4 Bundle", "A small bundle of 2x4 framing lumber.", "Material", 5, 60.0, 20.0),
    "lumber_bundle_2x6_small": ("Small 2x6 Bundle", "A small bundle of 2x6 framing lumber.", "Material", 5, 80.0, 28.0),
    "lumber_bundle_2x10_small": ("Small 2x10 Bundle", "A small bundle of 2x10 framing lumber.", "Material", 5, 110.0, 40.0),
    "sheet_osb_stack_small": ("Small OSB Stack", "A small stack of OSB sheathing sheets.", "Material", 5, 90.0, 30.0),
    "sheet_drywall_stack_small": ("Small Drywall Stack", "A small stack of drywall sheets.", "Material", 5, 100.0, 25.0),
    "lumber_bundle_2x4_large": ("Large 2x4 Bundle", "A large bundle of 2x4 framing lumber.", "Material", 2, 150.0, 45.0),
    "lumber_bundle_2x6_large": ("Large 2x6 Bundle", "A large bundle of 2x6 framing lumber.", "Material", 2, 200.0, 62.0),
    "lumber_bundle_2x10_large": ("Large 2x10 Bundle", "A large bundle of 2x10 framing lumber.", "Material", 2, 270.0, 90.0),
    "sheet_osb_stack_large": ("Large OSB Stack", "A large stack of OSB sheathing sheets.", "Material", 2, 220.0, 68.0),
    "sheet_drywall_stack_large": ("Large Drywall Stack", "A large stack of drywall sheets.", "Material", 2, 240.0, 55.0),

    # BALES
    "bale_hay_square": ("Square Hay Bale", "A rectangular twine-bound hay bale.", "Fuel", 10, 25.0, 6.0),
    "bale_hay_round": ("Round Hay Bale", "A round rolled hay bale.", "Fuel", 5, 450.0, 40.0),
    "bale_straw_square": ("Square Straw Bale", "A rectangular twine-bound straw bale.", "Fuel", 10, 18.0, 4.0),
    "bale_straw_round": ("Round Straw Bale", "A round rolled straw bale.", "Fuel", 5, 350.0, 30.0),
    "bale_silage_round": ("Round Silage Bale", "A round silage bale wrapped in plastic.", "Fuel", 5, 500.0, 45.0),

    # BOXES
    "box_small_white": ("Small White Box", "A small white cardboard shipping box.", "Material", 20, 1.0, 2.0),
    "box_small_tan": ("Small Kraft Box", "A small tan cardboard shipping box.", "Material", 20, 1.0, 2.0),
    "box_small_brown": ("Small Brown Box", "A small dark brown cardboard shipping box.", "Material", 20, 1.0, 2.0),
    "box_medium_white": ("Medium White Box", "A medium white cardboard shipping box.", "Material", 10, 3.0, 4.0),
    "box_medium_tan": ("Medium Kraft Box", "A medium tan cardboard shipping box.", "Material", 10, 3.0, 4.0),
    "box_medium_brown": ("Medium Brown Box", "A medium dark brown cardboard shipping box.", "Material", 10, 3.0, 4.0),
    "box_large_white": ("Large White Box", "A large white cardboard shipping box.", "Material", 5, 7.0, 7.0),
    "box_large_tan": ("Large Kraft Box", "A large tan cardboard shipping box.", "Material", 5, 7.0, 7.0),
    "box_large_brown": ("Large Brown Box", "A large dark brown cardboard shipping box.", "Material", 5, 7.0, 7.0),
}
