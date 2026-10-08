# Asset Audit

Generated 2026-10-08 by `python tools/asset_audit.py` from 2632 manifests. Run it again to refresh; do not edit by hand.

A file-level check: it does not judge how a model or an icon looks.

## Needs a model (59)

No model at all, only an icon.


### tools (14)

- [ ] `tool_angle_grinder_corded`
- [ ] `tool_angle_grinder_cordless`
- [ ] `tool_basket_large`
- [ ] `tool_basket_medium`
- [ ] `tool_basket_small`
- [ ] `tool_circular_saw_corded`
- [ ] `tool_circular_saw_cordless`
- [ ] `tool_drill_corded`
- [ ] `tool_drill_cordless_basic`
- [ ] `tool_drill_cordless_pro`
- [ ] `tool_fruit_basket`
- [ ] `tool_impact_driver_cordless`
- [ ] `tool_miter_saw`
- [ ] `tool_table_saw`

### logging (10)

- [ ] `plantable_sapling_apricot`
- [ ] `plantable_sapling_cherry`
- [ ] `plantable_sapling_fig`
- [ ] `plantable_sapling_grape`
- [ ] `plantable_sapling_hazelnut`
- [ ] `plantable_sapling_peach`
- [ ] `plantable_sapling_pear`
- [ ] `plantable_sapling_pecan`
- [ ] `plantable_sapling_plum`
- [ ] `plantable_sapling_walnut`

### ingredients (8)

- [ ] `ingredient_bacon`
- [ ] `ingredient_goat_meat`
- [ ] `ingredient_ground_beef`
- [ ] `ingredient_ham`
- [ ] `ingredient_lamb_chop`
- [ ] `ingredient_pork_chop`
- [ ] `ingredient_sausage`
- [ ] `ingredient_steak`

### building (5)

- [ ] `icon_wood_log`
- [ ] `lot_asphalt`
- [ ] `lot_concrete`
- [ ] `lot_dirt`
- [ ] `lot_gravel`

### fishing (2)

- [ ] `fishing_lure`
- [ ] `fishing_rod`

### materials (2)

- [ ] `mat_feather`
- [ ] `mat_leather`

### waste (1)

- [ ] `waste_service_septic_pumpout`

### water (1)

- [ ] `water_hand_pump_wellhead`

### appliances (16)

- [ ] `appliance_dryer_budget`
- [ ] `appliance_dryer_premium`
- [ ] `appliance_fireplace_insert_standard`
- [ ] `appliance_fireplace_premium`
- [ ] `appliance_grill_charcoal`
- [ ] `appliance_grill_propane_premium`
- [ ] `appliance_grill_propane_standard`
- [ ] `appliance_oven_wood_fired`
- [ ] `appliance_smoker_budget_charcoal`
- [ ] `appliance_smoker_offset`
- [ ] `appliance_smoker_pellet_premium`
- [ ] `appliance_stove_wood_cookstove`
- [ ] `appliance_waterheater_premium_tankless`
- [ ] `appliance_waterheater_wood_fired`
- [ ] `appliance_winter_coat`
- [ ] `appliance_woodstove_budget`

## Broken model link (0)

The manifest names a model file that is not in the folder (old imperial names): a rename, not a new model.

None.


## Old OBJ / FBX only (0)

No GLB. Convert with `tools/convert_models_to_glb.py` (rigged FBX stays FBX), or remake.

None.


## Over the triangle budget (0)

None.


## Icon missing (1)

- [ ] `cursors`

## Icon not 128x128 RGBA (0)

None.


## Icon too thin to read (34)

Long thin items that cover under 5% of the icon.

- [ ] building_downspout (4% of the icon)
- [ ] building_lumber_rafter_2x8 (4% of the icon)
- [ ] building_rebar_steel_bar (4% of the icon)
- [ ] building_truss_large (4% of the icon)
- [ ] drain_french_sock (4% of the icon)
- [ ] finishing_nail (4% of the icon)
- [ ] lumber_stud_2x4 (4% of the icon)
- [ ] pipe_abs_waste_three_inch (3% of the icon)
- [ ] pipe_leach_perforated_4inch (4% of the icon)
- [ ] pipe_pvc_half_inch (1% of the icon)
- [ ] pipe_pvc_half_inch_stack_10 (3% of the icon)
- [ ] pipe_pvc_one_inch (2% of the icon)
- [ ] pipe_pvc_two_inch (2% of the icon)
- [ ] pipe_sewer_solid_4inch (4% of the icon)
- [ ] electricity_power_pole_metal (2% of the icon)
- [ ] electricity_power_pole_wood (3% of the icon)
- [ ] electricity_powerpole_wood (4% of the icon)
- [ ] electricity_wind_kit_200w_metal (4% of the icon)
- [ ] electricity_wind_kit_500w_metal (3% of the icon)
- [ ] electricity_wooden_utility_pole (3% of the icon)
- [ ] garlic (3% of the icon)
- [ ] onion (4% of the icon)
- [ ] fuel_pipe_line (2% of the icon)
- [ ] fuel_pipe_propane (2% of the icon)
- [ ] lighting_pole_light_classic_black (4% of the icon)
- [ ] lighting_pole_light_classic_brass (4% of the icon)
- [ ] lighting_pole_light_classic_bronze (4% of the icon)
- [ ] lighting_pole_light_classic_white (4% of the icon)
- [ ] lighting_pole_light_modern_black (3% of the icon)
- [ ] lighting_pole_light_modern_chrome (3% of the icon)
- [ ] lighting_pole_light_modern_nickel (3% of the icon)
- [ ] lighting_pole_light_modern_white (3% of the icon)
- [ ] water_irrigation_sprinkler_riser (4% of the icon)
- [ ] water_pipe (2% of the icon)

## Same icon on two items (32)

Usually a duplicate item.

- [ ] bathroom_hamper_classic_burgundy = bathroom_hamper_classic_camel = bathroom_hamper_classic_forest = bathroom_hamper_classic_navy
- [ ] bathroom_soap_set_classic_chrome = bathroom_soap_set_modern_chrome
- [ ] bathroom_towel_bar_classic_chrome = bathroom_towel_bar_modern_chrome
- [ ] item_spool_barbedwire = spool_wire_barbed_4pt
- [ ] dining_wine_rack_classic_walnut = dining_wine_rack_modern_walnut
- [ ] electricity_wind_kit_100w_wood = wind_turbine_100w_wood
- [ ] electricity_wind_kit_200w_metal = wind_turbine_200w_metal
- [ ] electricity_wind_kit_500w_metal = wind_turbine_500w_metal
- [ ] fuel_bulk_diesel = liquid_diesel
- [ ] fuel_bulk_gasoline = liquid_gasoline
- [ ] fuel_bulk_propane = liquid_propane
- [ ] fuel_service_tank_pickup = vehicle_delivery_fuel_truck
- [ ] garage_bench_grinder_classic_black = garage_bench_grinder_modern_black
- [ ] garage_lumber_rack_classic_black = garage_lumber_rack_modern_black
- [ ] garage_pegboard_classic_walnut = garage_pegboard_modern_walnut
- [ ] garage_sawhorse_modern_birch = garage_sawhorse_modern_black = garage_sawhorse_modern_walnut
- [ ] kitchen_bowl = kitchen_bowl_meal
- [ ] kitchen_cutting_board_oak = kitchen_cutting_board_white
- [ ] kitchen_plate = kitchen_plated_meal
- [ ] laundry_drying_rack_classic_walnut = laundry_drying_rack_modern_walnut
- [ ] living_tv_modern_walnut = living_tv_modern_white
- [ ] living_wall_clock_modern_birch = living_wall_clock_modern_walnut
- [ ] living_wall_mirror_modern_birch = living_wall_mirror_modern_black = living_wall_mirror_modern_walnut = living_wall_mirror_modern_white
- [ ] plantable_sapling_apple = plantable_sapling_apricot = plantable_sapling_cherry = plantable_sapling_fig = plantable_sapling_grape = plantable_sapling_hazelnut = plantable_sapling_peach = plantable_sapling_pear = plantable_sapling_pecan = plantable_sapling_plum = plantable_sapling_walnut
- [ ] mat_pile_bedding_stone_small = mat_scoop_bedding_stone
- [ ] mat_pile_dirt_small = mat_scoop_dirt
- [ ] mat_pile_gravel_small = mat_scoop_gravel
- [ ] mat_pile_mulch_small = mat_scoop_mulch
- [ ] mat_pile_sand_small = mat_scoop_sand
- [ ] mat_scoop_manure = waste_pile_manure_small
- [ ] office_whiteboard_classic_walnut = office_whiteboard_modern_walnut
- [ ] vehicle_septic_pump_truck = waste_service_septic_pumpout

## No case, pallet or stack (301)

Buyable singles with no pack item (paint, piles, logs, tanks and placed parts left out).


### building (82)

- [ ] `building_chimney_kit_brick`
- [ ] `building_chimney_kit_stone`
- [ ] `building_chinking`
- [ ] `building_door_barn_sliding`
- [ ] `building_door_exterior`
- [ ] `building_door_exterior_craftsman`
- [ ] `building_door_exterior_half_lite`
- [ ] `building_door_exterior_plank`
- [ ] `building_door_exterior_six_panel`
- [ ] `building_door_frame_exterior`
- [ ] `building_door_frame_interior`
- [ ] `building_door_hardware_set`
- [ ] `building_door_interior`
- [ ] `building_door_interior_flush`
- [ ] `building_door_interior_french`
- [ ] `building_door_interior_shaker`
- [ ] `building_door_interior_six_panel`
- [ ] `building_fascia_board`
- [ ] `building_flashing_roll`
- [ ] `building_gate_latch`
- [ ] `building_gutter_section`
- [ ] `building_house_wrap_roll`
- [ ] `building_light_ceiling_flush`
- [ ] `building_light_ceiling_pendant`
- [ ] `building_light_fluorescent_2bulb`
- [ ] `building_light_fluorescent_4bulb`
- [ ] `building_light_fluorescent_8bulb`
- [ ] `building_light_grow_2bulb`
- [ ] `building_light_grow_4bulb`
- [ ] `building_light_grow_8bulb`
- [ ] `building_light_sconce_exterior`
- [ ] `building_light_sconce_interior`
- [ ] `building_lumber_joist_2x10`
- [ ] `building_lumber_rafter_2x8`
- [ ] `building_pallet_wood`
- [ ] `building_pickup_flag`
- [ ] `building_rebar_steel_bar`
- [ ] `building_roofing_felt_roll`
- [ ] `building_shelf_wall_steel`
- [ ] `building_shelf_wall_wood`
- [ ] `building_shelf_wall_wood_long`
- [ ] `building_shelving_melamine_black`
- [ ] `building_shelving_melamine_white`
- [ ] `building_shelving_steel`
- [ ] `building_soffit_panel`
- [ ] `building_trim_baseboard`
- [ ] `building_trim_casing`
- [ ] `building_window_double_hung`
- [ ] `building_window_double_hung_panes2`
- [ ] `building_window_double_hung_panes6`
- [ ] `building_window_double_hung_panes8`
- [ ] `building_window_double_hung_plain`
- [ ] `building_window_picture`
- [ ] `building_window_picture_panes2`
- [ ] `building_window_picture_panes6`
- [ ] `building_window_picture_panes8`
- [ ] `building_window_picture_plain`
- [ ] `building_window_shutters`
- [ ] `building_window_slider`
- [ ] `building_window_slider_panes2`
- [ ] `building_window_slider_panes6`
- [ ] `building_window_slider_panes8`
- [ ] `building_window_slider_plain`
- [ ] `gland_cable_entry_wall`
- [ ] `hardware_gate_hinges`
- [ ] `hardware_hurricane_ties`
- [ ] `item_hardware_rebarbundle`
- [ ] `item_spool_barbedwire`
- [ ] `item_spool_cat6_150m`
- [ ] `item_spool_romex_12_2`
- [ ] `lot_asphalt`
- [ ] `lot_concrete`
- [ ] `lot_dirt`
- [ ] `lot_gravel`
- [ ] `lumber_board_2x6`
- [ ] `lumber_stud_2x4`
- [ ] `pipe_abs_waste_three_inch`
- [ ] `spool_wire_barbed_4pt`
- [ ] `spool_wire_romex_12_2`
- [ ] `spool_wire_woven_field`
- [ ] `valve_ball_brass`
- [ ] `valve_gate_brass`

### ingredients (71)

- [ ] `ingredient_alfalfa`
- [ ] `ingredient_alfredo_sauce`
- [ ] `ingredient_bacon`
- [ ] `ingredient_baking_powder`
- [ ] `ingredient_baking_powder_5kg`
- [ ] `ingredient_barley`
- [ ] `ingredient_barley_flour`
- [ ] `ingredient_barley_flour_5kg`
- [ ] `ingredient_beef`
- [ ] `ingredient_bread_crumbs`
- [ ] `ingredient_butter`
- [ ] `ingredient_canola`
- [ ] `ingredient_chicken`
- [ ] `ingredient_cocoa`
- [ ] `ingredient_corn`
- [ ] `ingredient_corn_flour`
- [ ] `ingredient_corn_flour_5kg`
- [ ] `ingredient_cornmeal`
- [ ] `ingredient_cornmeal_5kg`
- [ ] `ingredient_cotton`
- [ ] `ingredient_cracked_wheat`
- [ ] `ingredient_cracked_wheat_5kg`
- [ ] `ingredient_egg`
- [ ] `ingredient_fillet_bass`
- [ ] `ingredient_fillet_catfish`
- [ ] `ingredient_fillet_crappie`
- [ ] `ingredient_fillet_salmon`
- [ ] `ingredient_fillet_trout`
- [ ] `ingredient_fillet_walleye`
- [ ] `ingredient_flax`
- [ ] `ingredient_flax_meal`
- [ ] `ingredient_flax_meal_5kg`
- [ ] `ingredient_flour`
- [ ] `ingredient_flour_5kg`
- [ ] `ingredient_gelatin`
- [ ] `ingredient_gelatin_5kg`
- [ ] `ingredient_goat_meat`
- [ ] `ingredient_grits`
- [ ] `ingredient_grits_5kg`
- [ ] `ingredient_ground_beef`
- [ ] `ingredient_ham`
- [ ] `ingredient_herbs`
- [ ] `ingredient_hops`
- [ ] `ingredient_lamb_chop`
- [ ] `ingredient_oat_flour`
- [ ] `ingredient_oat_flour_5kg`
- [ ] `ingredient_oats`
- [ ] `ingredient_pasta`
- [ ] `ingredient_pasta_5kg`
- [ ] `ingredient_pasta_sauce`
- [ ] `ingredient_pearl_barley`
- [ ] `ingredient_pearl_barley_5kg`
- [ ] `ingredient_pepper_ground`
- [ ] `ingredient_pork`
- [ ] `ingredient_pork_chop`
- [ ] `ingredient_rolled_oats`
- [ ] `ingredient_rolled_oats_5kg`
- [ ] `ingredient_salt`
- [ ] `ingredient_salt_5kg`
- [ ] `ingredient_sausage`
- [ ] `ingredient_soy_flour`
- [ ] `ingredient_soy_flour_5kg`
- [ ] `ingredient_soybeans`
- [ ] `ingredient_steak`
- [ ] `ingredient_sugar`
- [ ] `ingredient_sugar_5kg`
- [ ] `ingredient_sunflower`
- [ ] `ingredient_tobacco`
- [ ] `ingredient_wheat`
- [ ] `ingredient_yeast`
- [ ] `ingredient_yeast_5kg`

### fuel (16)

- [ ] `fuel_bulk_diesel`
- [ ] `fuel_bulk_gasoline`
- [ ] `fuel_bulk_propane`
- [ ] `fuel_charcoal`
- [ ] `fuel_firewood_bundle_birch`
- [ ] `fuel_firewood_bundle_maple`
- [ ] `fuel_firewood_bundle_oak`
- [ ] `fuel_firewood_bundle_pine`
- [ ] `fuel_firewood_bundle_poplar`
- [ ] `fuel_firewood_bundle_willow`
- [ ] `fuel_propane_18l`
- [ ] `fuel_propane_1_5l`
- [ ] `fuel_propane_36l`
- [ ] `fuel_propane_fill_post`
- [ ] `fuel_propane_house_connector`
- [ ] `fuel_service_tank_pickup`

### materials (13)

- [ ] `mat_bale_hay_round`
- [ ] `mat_bale_hay_square`
- [ ] `mat_bale_straw_round`
- [ ] `mat_bale_straw_square`
- [ ] `mat_feather`
- [ ] `mat_fertilizer`
- [ ] `mat_leather`
- [ ] `mat_pelt_cow`
- [ ] `mat_pelt_goat`
- [ ] `mat_pelt_sheep`
- [ ] `mat_rope`
- [ ] `mat_stone`
- [ ] `mat_wool_fleece`

### farming (35)

- [ ] `seed_alfalfa`
- [ ] `seed_barley`
- [ ] `seed_beet`
- [ ] `seed_broccoli`
- [ ] `seed_cabbage`
- [ ] `seed_canola`
- [ ] `seed_cantaloupe`
- [ ] `seed_carrot`
- [ ] `seed_corn`
- [ ] `seed_cotton`
- [ ] `seed_cucumber`
- [ ] `seed_flax`
- [ ] `seed_garlic`
- [ ] `seed_green_beans`
- [ ] `seed_herb`
- [ ] `seed_hops`
- [ ] `seed_lettuce`
- [ ] `seed_oats`
- [ ] `seed_onion`
- [ ] `seed_peanuts`
- [ ] `seed_peas`
- [ ] `seed_peppers`
- [ ] `seed_potato`
- [ ] `seed_pumpkin`
- [ ] `seed_radish`
- [ ] `seed_rhubarb`
- [ ] `seed_soybeans`
- [ ] `seed_spinach`
- [ ] `seed_strawberry`
- [ ] `seed_sunflower`
- [ ] `seed_tobacco`
- [ ] `seed_tomato`
- [ ] `seed_watermelon`
- [ ] `seed_wheat`
- [ ] `seed_zucchini`

### food (84)

- [ ] `food_apple`
- [ ] `food_apple_muffin`
- [ ] `food_apricot`
- [ ] `food_apricot_muffin`
- [ ] `food_bacon_cooked`
- [ ] `food_bass_deepfried`
- [ ] `food_bass_grilled`
- [ ] `food_beet`
- [ ] `food_blueberry_muffin`
- [ ] `food_bread`
- [ ] `food_broccoli`
- [ ] `food_burger`
- [ ] `food_burger_bun`
- [ ] `food_cabbage`
- [ ] `food_cantaloupe`
- [ ] `food_carrot`
- [ ] `food_catfish_deepfried`
- [ ] `food_catfish_grilled`
- [ ] `food_cheese`
- [ ] `food_cherry`
- [ ] `food_cherry_muffin`
- [ ] `food_corn_muffin`
- [ ] `food_cornbread`
- [ ] `food_crappie_deepfried`
- [ ] `food_crappie_grilled`
- [ ] `food_cucumber`
- [ ] `food_elderberry_muffin`
- [ ] `food_fig`
- [ ] `food_fig_muffin`
- [ ] `food_garlic`
- [ ] `food_goat_meat_baked`
- [ ] `food_grapes`
- [ ] `food_green_beans`
- [ ] `food_ground_beef_grilled`
- [ ] `food_ham_baked`
- [ ] `food_haskap_muffin`
- [ ] `food_hazelnut`
- [ ] `food_hot_dog`
- [ ] `food_hot_dog_bun`
- [ ] `food_huckleberry_muffin`
- [ ] `food_lamb_chop_grilled`
- [ ] `food_lemon`
- [ ] `food_lemon_muffin`
- [ ] `food_lettuce`
- [ ] `food_muffin`
- [ ] `food_onion`
- [ ] `food_orange`
- [ ] `food_orange_muffin`
- [ ] `food_peach`
- [ ] `food_peach_muffin`
- [ ] `food_peanuts`
- [ ] `food_pear`
- [ ] `food_pear_muffin`
- [ ] `food_peas`
- [ ] `food_pecan`
- [ ] `food_pepper`
- [ ] `food_plum`
- [ ] `food_plum_muffin`
- [ ] `food_pork_chop_grilled`
- [ ] `food_potato`
- [ ] `food_pumpkin`
- [ ] `food_radish`
- [ ] `food_raspberry_muffin`
- [ ] `food_rhubarb`
- [ ] `food_rhubarb_muffin`
- [ ] `food_salmon_grilled`
- [ ] `food_sausage_grilled`
- [ ] `food_spinach`
- [ ] `food_steak_grilled`
- [ ] `food_strawberry`
- [ ] `food_strawberry_muffin`
- [ ] `food_tomato`
- [ ] `food_trout_deepfried`
- [ ] `food_trout_grilled`
- [ ] `food_truffle`
- [ ] `food_walleye_deepfried`
- [ ] `food_walleye_grilled`
- [ ] `food_walnut`
- [ ] `food_watermelon`
- [ ] `food_zucchini`
- [ ] `ingredient_beef_grilled`
- [ ] `ingredient_chicken_grilled`
- [ ] `ingredient_milk`
- [ ] `ingredient_pork_grilled`

## Old pack naming (0)

Packs named `_large` / `_small` beside the newer counted packs (`_10` / `_20`).

None.


## Bad manifest JSON (0)

None.


## Not checked

104 grown things (crops, trees, animals) have no model of their own by design, and structures, HUD, liquids, fences, paths, roads, scoops and ground clutter are built in code or staged.
