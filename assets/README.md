# Homesteader Unified Assets Catalog

Welcome to the master asset repository for the **Homesteader** project. This directory organizes every in-game item, building, structure, clutter object, tool, utility, and resource across the 13 core gameplay systems.

Each item subfolder contains:
- 🖼️ **`<item_id>.png`**: 128×128 32-bit transparent RGBA render (12px safe margin, 3D faceted style).
- 📦 **3D Model Files**: `.obj`, `.mtl`, `.fbx`, or `.glb` files with flat-shaded low-poly geometry.
- ⚙️ **`<item_id>.json`**: Machine-readable plugin manifest with metrics, utilities, dimensions, and 4-stage growth lifecycle.
- 📄 **`README.md`**: Human-readable overview and quick reference for the asset.

### Developer & AI Agent Specifications

- 🌐 **[`API_REFERENCE.md`](API_REFERENCE.md)**: Authoritative REST API specification for `server.py` (queue pipeline, mutations, schemas, tags).
- 📋 **[`../docs/MESHY_PIPELINE_GUIDE.md`](../docs/MESHY_PIPELINE_GUIDE.md)**: Asset generation pipeline guide (Meshy text-to-3D, low-poly, Unity target).

## Category Taxonomy Summary

Total Indexed Items: **1269**

| Category | Items Count | Description |
| :--- | :---: | :--- |
| [**Structures**](structures/) | 36 items | Placed world buildings, farmhouses, cabins, barns, silos, sheds, greenhouses, coops, shelters, and towers. |
| [**Building**](building/) | 436 items | Modular building materials, framing, doors, windows, and hardware supplies. |
| [**Farming**](farming/) | 70 items | Crops, seeds, produce, fertilizers, irrigation, and agricultural machinery. |
| [**Ranching**](ranching/) | 28 items | Livestock species, animal feed/hay, butchered meats, hides/pelts, and animal husbandry housing. |
| [**Logging**](logging/) | 43 items | Modular forest trees (large/medium/small), saplings, timber logs, firewood, woodchips, and sap spigots. |
| [**Fishing**](fishing/) | 19 items | Whole fish species, precision meat fillets, fishing rods, lures, and tackle. |
| [**Tools**](tools/) | 69 items | Hand tools, power gear, crafting implements, and surveying/measuring equipment. |
| [**Electricity**](electricity/) | 65 items | Solar photovoltaic panels, wind turbines, fuel generators, battery banks, and high-voltage wiring. |
| [**Water**](water/) | 45 items | Aquifer wells, pressure tanks, poly cisterns, rain catchment barrels, and filtration racks. |
| [**Waste**](waste/) | 19 items | Septic infrastructure, compost systems, composting toilets, and organic waste management. |
| [**Internet**](internet/) | 24 items | Starlink satellite dishes, Wi-Fi 6 mesh distribution routers, and weather-rated cabling. |
| [**Hud**](hud/) | 31 items | Player vitals, coins, energy/stamina bars, clock dials, and interface elements. |
| [**Ground**](ground/) | 18 items | Modular terrain grid tiles (1m x 1m), road pavements, and scatter clutter props. |
| [**Food**](food/) | 124 items | Edible harvested produce, pantry staples, fresh eggs, dairy, and whole foods. |
| [**Fuel**](fuel/) | 33 items | Liquid hydrocarbons, compressed gas tanks, bulk fuel storage, firewood cords, and transfer equipment. |
| [**Materials**](materials/) | 82 items | Raw construction materials, timber log piles, aggregate bulk piles, textiles, hides, and foundational crafting resources. |
| [**Ingredients**](ingredients/) | 67 items | Raw cooking and crafting inputs: butchered meats, fish fillets, eggs, dairy, harvested grains, and crop-derived ingredients. |
| [**Liquids**](liquids/) | 60 items | Fluids that fill liquid containers by volume: milk, water, fuels, oils and syrups, each with a weight per liter, a fluid colour and an opacity. |

### Shared System & World Asset Directories

| System Directory | Contents | Specification |
| :--- | :--- | :--- |
| [**Ground**](ground/) | 20 Seamless PBR Texture Sets (BaseColor, Normal, ORM), 16 Landscape Blend Masks, 20 Modular Grid Tiles (`SM_Tile_*`), and 10 Scatter Clutter Meshes. | [`ground/README.md`](ground/README.md) |
| [**Textures**](textures/) | Master 3D low-poly color palette atlas (`T_Homesteader_Palette.png`) and entity skeletal mesh base colors (`animals/`). | [`textures/README.md`](textures/README.md) |

---

### 📂 [Structures](structures/) (36 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `3_bay_truck_garage` | 3-Bay Truck Garage | — | — | [3_bay_truck_garage.json](structures/3_bay_truck_garage/3_bay_truck_garage.json) |
| `barn` | Barn | — | — | [barn.json](structures/barn/barn.json) |
| `chicken_coop` | Chicken Coop | — | — | [chicken_coop.json](structures/chicken_coop/chicken_coop.json) |
| `farmhouse` | Farmhouse | — | — | [farmhouse.json](structures/farmhouse/farmhouse.json) |
| `grain_silo_large` | Grain Silo (Large) | — | — | [grain_silo_large.json](structures/grain_silo_large/grain_silo_large.json) |
| `grain_silo_medium` | Grain Silo (Medium) | — | — | [grain_silo_medium.json](structures/grain_silo_medium/grain_silo_medium.json) |
| `grain_silo_small` | Grain Silo (Small) | — | — | [grain_silo_small.json](structures/grain_silo_small/grain_silo_small.json) |
| `greenhouse` | Greenhouse | — | — | [greenhouse.json](structures/greenhouse/greenhouse.json) |
| `house_garage` | House wtih Garage | — | — | [house_garage.json](structures/house_garage/house_garage.json) |
| `l_house` | L-Shaped House | — | — | [l_house.json](structures/l_house/l_house.json) |
| `large_log_cabin` | Large Log Cabin | — | — | [large_log_cabin.json](structures/large_log_cabin/large_log_cabin.json) |
| `large_metal_garage` | Large Metal Garage | — | — | [large_metal_garage.json](structures/large_metal_garage/large_metal_garage.json) |
| `small_cabin` | Small Cabin | — | — | [small_cabin.json](structures/small_cabin/small_cabin.json) |
| `stable` | Stable | — | — | [stable.json](structures/stable/stable.json) |
| `starter_house` | Starter House | — | — | [starter_house.json](structures/starter_house/starter_house.json) |
| `steel_truss_shelter_2` | Steel Truss Shelter (2 Vehicles) | — | — | [steel_truss_shelter_2.json](structures/steel_truss_shelter_2/steel_truss_shelter_2.json) |
| `steel_truss_shelter_3` | Steel Truss Shelter (3 Vehicles) | — | — | [steel_truss_shelter_3.json](structures/steel_truss_shelter_3/steel_truss_shelter_3.json) |
| `steel_truss_shelter_5` | Steel Truss Shelter (5 Vehicles) | — | — | [steel_truss_shelter_5.json](structures/steel_truss_shelter_5/steel_truss_shelter_5.json) |
| `struct_camper_rv` | Travel Trailer RV | ✅ Yes | — | [struct_camper_rv.json](structures/struct_camper_rv/struct_camper_rv.json) |
| `struct_camper_teardrop` | Teardrop Camper | ✅ Yes | — | [struct_camper_teardrop.json](structures/struct_camper_teardrop/struct_camper_teardrop.json) |
| `struct_light_pole_barn` | Yard Barn Light Pole | ✅ Yes | — | [struct_light_pole_barn.json](structures/struct_light_pole_barn/struct_light_pole_barn.json) |
| `struct_pump_house` | Pump House | — | — | [struct_pump_house.json](structures/struct_pump_house/struct_pump_house.json) |
| `struct_shed` | Tool Shed | — | — | [struct_shed.json](structures/struct_shed/struct_shed.json) |
| `struct_tent_canvas` | Canvas Wall Tent | ✅ Yes | — | [struct_tent_canvas.json](structures/struct_tent_canvas/struct_tent_canvas.json) |
| `struct_tent_dome` | Dome Tent | ✅ Yes | — | [struct_tent_dome.json](structures/struct_tent_dome/struct_tent_dome.json) |
| `struct_woodshed` | Woodshed | — | — | [struct_woodshed.json](structures/struct_woodshed/struct_woodshed.json) |
| `waste_leach_field_large` | Large Leach Field | — | — | [waste_leach_field_large.json](structures/waste_leach_field_large/waste_leach_field_large.json) |
| `waste_leach_field_small` | Small Leach Field | — | — | [waste_leach_field_small.json](structures/waste_leach_field_small/waste_leach_field_small.json) |
| `waste_septic_tank_concrete` | Septic Tank (Concrete) | — | — | [waste_septic_tank_concrete.json](structures/waste_septic_tank_concrete/waste_septic_tank_concrete.json) |
| `waste_septic_tank_poly` | Septic Tank (Poly) | — | — | [waste_septic_tank_poly.json](structures/waste_septic_tank_poly/waste_septic_tank_poly.json) |
| `water_well_concrete` | Drilled Well (Concrete Wellhead) | — | — | [water_well_concrete.json](structures/water_well_concrete/water_well_concrete.json) |
| `water_well_manual` | Manual Well | — | — | [water_well_manual.json](structures/water_well_manual/water_well_manual.json) |
| `water_well_wooden` | Drilled Well (Wooden Well House) | — | — | [water_well_wooden.json](structures/water_well_wooden/water_well_wooden.json) |
| `wind_turbine_100w_wood` | 100W Wooden Wind Turbine | — | — | [wind_turbine_100w_wood.json](structures/wind_turbine_100w_wood/wind_turbine_100w_wood.json) |
| `wind_turbine_200w_metal` | 200W Metal Wind Turbine | — | — | [wind_turbine_200w_metal.json](structures/wind_turbine_200w_metal/wind_turbine_200w_metal.json) |
| `wind_turbine_500w_metal` | 500W Metal Wind Turbine | — | — | [wind_turbine_500w_metal.json](structures/wind_turbine_500w_metal/wind_turbine_500w_metal.json) |

### 📂 [Building](building/) (436 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `20lb_aggregate_rock_bag` | Bag of Aggregate Rock | ✅ Yes | — | [20lb_aggregate_rock_bag.json](building/20lb_aggregate_rock_bag/20lb_aggregate_rock_bag.json) |
| `20lb_aggregate_rock_bag_pallet_10` | Bag of Aggregate Rock Pallet | ✅ Yes | — | [20lb_aggregate_rock_bag_pallet_10.json](building/20lb_aggregate_rock_bag_pallet_10/20lb_aggregate_rock_bag_pallet_10.json) |
| `20lb_aggregate_rock_bag_pallet_20` | Bag of Aggregate Rock Pallet | ✅ Yes | — | [20lb_aggregate_rock_bag_pallet_20.json](building/20lb_aggregate_rock_bag_pallet_20/20lb_aggregate_rock_bag_pallet_20.json) |
| `20lb_cement_bag` | Cement Bag | ✅ Yes | — | [20lb_cement_bag.json](building/20lb_cement_bag/20lb_cement_bag.json) |
| `20lb_cement_bag_pallet_10` | Cement Bag Pallet | ✅ Yes | — | [20lb_cement_bag_pallet_10.json](building/20lb_cement_bag_pallet_10/20lb_cement_bag_pallet_10.json) |
| `20lb_cement_bag_pallet_20` | Cement Bag Pallet | ✅ Yes | — | [20lb_cement_bag_pallet_20.json](building/20lb_cement_bag_pallet_20/20lb_cement_bag_pallet_20.json) |
| `20lb_sand_bag` | Bag of Sand | ✅ Yes | — | [20lb_sand_bag.json](building/20lb_sand_bag/20lb_sand_bag.json) |
| `20lb_sand_bag_pallet_10` | Bag of Sand Pallet | ✅ Yes | — | [20lb_sand_bag_pallet_10.json](building/20lb_sand_bag_pallet_10/20lb_sand_bag_pallet_10.json) |
| `20lb_sand_bag_pallet_20` | Bag of Sand Pallet | ✅ Yes | — | [20lb_sand_bag_pallet_20.json](building/20lb_sand_bag_pallet_20/20lb_sand_bag_pallet_20.json) |
| `anchor_bolt` | Anchor Bolt | ✅ Yes | — | [anchor_bolt.json](building/anchor_bolt/anchor_bolt.json) |
| `anchor_bolts_case_10` | Anchor Bolts Case | ✅ Yes | — | [anchor_bolts_case_10.json](building/anchor_bolts_case_10/anchor_bolts_case_10.json) |
| `anchor_bolts_case_20` | Anchor Bolts Case | ✅ Yes | — | [anchor_bolts_case_20.json](building/anchor_bolts_case_20/anchor_bolts_case_20.json) |
| `box_large_brown` | Large Brown Box | ✅ Yes | — | [box_large_brown.json](building/box_large_brown/box_large_brown.json) |
| `box_large_tan` | Large Kraft Box | ✅ Yes | — | [box_large_tan.json](building/box_large_tan/box_large_tan.json) |
| `box_large_white` | Large White Box | ✅ Yes | — | [box_large_white.json](building/box_large_white/box_large_white.json) |
| `box_medium_brown` | Medium Brown Box | ✅ Yes | — | [box_medium_brown.json](building/box_medium_brown/box_medium_brown.json) |
| `box_medium_tan` | Medium Kraft Box | ✅ Yes | — | [box_medium_tan.json](building/box_medium_tan/box_medium_tan.json) |
| `box_medium_white` | Medium White Box | ✅ Yes | — | [box_medium_white.json](building/box_medium_white/box_medium_white.json) |
| `box_small_brown` | Small Brown Box | ✅ Yes | — | [box_small_brown.json](building/box_small_brown/box_small_brown.json) |
| `box_small_tan` | Small Kraft Box | ✅ Yes | — | [box_small_tan.json](building/box_small_tan/box_small_tan.json) |
| `box_small_white` | Small White Box | ✅ Yes | — | [box_small_white.json](building/box_small_white/box_small_white.json) |
| `building_beam_glulam` | Glulam Beam | ✅ Yes | — | [building_beam_glulam.json](building/building_beam_glulam/building_beam_glulam.json) |
| `building_beam_glulam_stack_10` | Glulam Beam Stack | ✅ Yes | — | [building_beam_glulam_stack_10.json](building/building_beam_glulam_stack_10/building_beam_glulam_stack_10.json) |
| `building_beam_glulam_stack_20` | Glulam Beam Stack | ✅ Yes | — | [building_beam_glulam_stack_20.json](building/building_beam_glulam_stack_20/building_beam_glulam_stack_20.json) |
| `building_bitumen_bucket` | Bitumen (Bucket) | ✅ Yes | — | [building_bitumen_bucket.json](building/building_bitumen_bucket/building_bitumen_bucket.json) |
| `building_bitumen_bucket_stack_18` | Bitumen (Bucket) Stack | ✅ Yes | — | [building_bitumen_bucket_stack_18.json](building/building_bitumen_bucket_stack_18/building_bitumen_bucket_stack_18.json) |
| `building_bitumen_bucket_stack_9` | Bitumen (Bucket) Stack | ✅ Yes | — | [building_bitumen_bucket_stack_9.json](building/building_bitumen_bucket_stack_9/building_bitumen_bucket_stack_9.json) |
| `building_bundle_rafter_2x8_large` | Large 2x8 Rafter Bundle | ✅ Yes | — | [building_bundle_rafter_2x8_large.json](building/building_bundle_rafter_2x8_large/building_bundle_rafter_2x8_large.json) |
| `building_bundle_rafter_2x8_small` | Small 2x8 Rafter Bundle | ✅ Yes | — | [building_bundle_rafter_2x8_small.json](building/building_bundle_rafter_2x8_small/building_bundle_rafter_2x8_small.json) |
| `building_chimney_kit_brick` | Brick Chimney Kit | ✅ Yes | — | [building_chimney_kit_brick.json](building/building_chimney_kit_brick/building_chimney_kit_brick.json) |
| `building_chimney_kit_stone` | Fieldstone Chimney Kit | ✅ Yes | — | [building_chimney_kit_stone.json](building/building_chimney_kit_stone/building_chimney_kit_stone.json) |
| `building_chinking` | Chinking | ✅ Yes | — | [building_chinking.json](building/building_chinking/building_chinking.json) |
| `building_concrete_block` | Concrete Block | ✅ Yes | — | [building_concrete_block.json](building/building_concrete_block/building_concrete_block.json) |
| `building_concrete_block_pallet_large` | Concrete Block Pallet | ✅ Yes | — | [building_concrete_block_pallet_large.json](building/building_concrete_block_pallet_large/building_concrete_block_pallet_large.json) |
| `building_concrete_block_pallet_small` | Concrete Block Half Pallet | ✅ Yes | — | [building_concrete_block_pallet_small.json](building/building_concrete_block_pallet_small/building_concrete_block_pallet_small.json) |
| `building_concrete_mix_bag` | Concrete Mix Bag | ✅ Yes | — | [building_concrete_mix_bag.json](building/building_concrete_mix_bag/building_concrete_mix_bag.json) |
| `building_concrete_mix_bag_pallet_10` | Concrete Mix Bag Pallet | ✅ Yes | — | [building_concrete_mix_bag_pallet_10.json](building/building_concrete_mix_bag_pallet_10/building_concrete_mix_bag_pallet_10.json) |
| `building_concrete_mix_bag_pallet_20` | Concrete Mix Bag Pallet | ✅ Yes | — | [building_concrete_mix_bag_pallet_20.json](building/building_concrete_mix_bag_pallet_20/building_concrete_mix_bag_pallet_20.json) |
| `building_concrete_mix_pallet` | Concrete Mix Bag Pallet | ✅ Yes | — | [building_concrete_mix_pallet.json](building/building_concrete_mix_pallet/building_concrete_mix_pallet.json) |
| `building_door_barn_sliding` | Barn Door | ✅ Yes | — | [building_door_barn_sliding.json](building/building_door_barn_sliding/building_door_barn_sliding.json) |
| `building_door_exterior` | Exterior Door | ✅ Yes | — | [building_door_exterior.json](building/building_door_exterior/building_door_exterior.json) |
| `building_door_exterior_craftsman` | Exterior Door (Craftsman) | ✅ Yes | — | [building_door_exterior_craftsman.json](building/building_door_exterior_craftsman/building_door_exterior_craftsman.json) |
| `building_door_exterior_half_lite` | Exterior Door (Half Lite) | ✅ Yes | — | [building_door_exterior_half_lite.json](building/building_door_exterior_half_lite/building_door_exterior_half_lite.json) |
| `building_door_exterior_plank` | Exterior Door (Plank) | ✅ Yes | — | [building_door_exterior_plank.json](building/building_door_exterior_plank/building_door_exterior_plank.json) |
| `building_door_exterior_six_panel` | Exterior Door (Six Panel) | ✅ Yes | — | [building_door_exterior_six_panel.json](building/building_door_exterior_six_panel/building_door_exterior_six_panel.json) |
| `building_door_frame_exterior` | Exterior Door Frame | ✅ Yes | — | [building_door_frame_exterior.json](building/building_door_frame_exterior/building_door_frame_exterior.json) |
| `building_door_frame_interior` | Interior Door Frame | ✅ Yes | — | [building_door_frame_interior.json](building/building_door_frame_interior/building_door_frame_interior.json) |
| `building_door_hardware_set` | Door Hardware Set | ✅ Yes | — | [building_door_hardware_set.json](building/building_door_hardware_set/building_door_hardware_set.json) |
| `building_door_interior` | Interior Door | ✅ Yes | — | [building_door_interior.json](building/building_door_interior/building_door_interior.json) |
| `building_door_interior_flush` | Interior Door (Flush) | ✅ Yes | — | [building_door_interior_flush.json](building/building_door_interior_flush/building_door_interior_flush.json) |
| `building_door_interior_french` | Interior Door (French) | ✅ Yes | — | [building_door_interior_french.json](building/building_door_interior_french/building_door_interior_french.json) |
| `building_door_interior_shaker` | Interior Door (Shaker) | ✅ Yes | — | [building_door_interior_shaker.json](building/building_door_interior_shaker/building_door_interior_shaker.json) |
| `building_door_interior_six_panel` | Interior Door (Six Panel) | ✅ Yes | — | [building_door_interior_six_panel.json](building/building_door_interior_six_panel/building_door_interior_six_panel.json) |
| `building_downspout` | Downspout | ✅ Yes | — | [building_downspout.json](building/building_downspout/building_downspout.json) |
| `building_downspout_stack_10` | Downspout Stack | ✅ Yes | — | [building_downspout_stack_10.json](building/building_downspout_stack_10/building_downspout_stack_10.json) |
| `building_downspout_stack_20` | Downspout Stack | ✅ Yes | — | [building_downspout_stack_20.json](building/building_downspout_stack_20/building_downspout_stack_20.json) |
| `building_drywall_tape_roll` | Drywall Tape | ✅ Yes | — | [building_drywall_tape_roll.json](building/building_drywall_tape_roll/building_drywall_tape_roll.json) |
| `building_drywall_tape_roll_case_12` | Drywall Tape Case | ✅ Yes | — | [building_drywall_tape_roll_case_12.json](building/building_drywall_tape_roll_case_12/building_drywall_tape_roll_case_12.json) |
| `building_drywall_tape_roll_case_6` | Drywall Tape Case | ✅ Yes | — | [building_drywall_tape_roll_case_6.json](building/building_drywall_tape_roll_case_6/building_drywall_tape_roll_case_6.json) |
| `building_fascia_board` | Fascia Board | ✅ Yes | — | [building_fascia_board.json](building/building_fascia_board/building_fascia_board.json) |
| `building_fascia_bundle` | Fascia Board Bundle | ✅ Yes | — | [building_fascia_bundle.json](building/building_fascia_bundle/building_fascia_bundle.json) |
| `building_flashing_roll` | Flashing Roll | ✅ Yes | — | [building_flashing_roll.json](building/building_flashing_roll/building_flashing_roll.json) |
| `building_floor_carpet_beige` | Beige Carpet | ✅ Yes | — | [building_floor_carpet_beige.json](building/building_floor_carpet_beige/building_floor_carpet_beige.json) |
| `building_floor_carpet_beige_stack_10` | Beige Carpet Stack | ✅ Yes | — | [building_floor_carpet_beige_stack_10.json](building/building_floor_carpet_beige_stack_10/building_floor_carpet_beige_stack_10.json) |
| `building_floor_carpet_beige_stack_20` | Beige Carpet Stack | ✅ Yes | — | [building_floor_carpet_beige_stack_20.json](building/building_floor_carpet_beige_stack_20/building_floor_carpet_beige_stack_20.json) |
| `building_floor_carpet_brown` | Brown Carpet | ✅ Yes | — | [building_floor_carpet_brown.json](building/building_floor_carpet_brown/building_floor_carpet_brown.json) |
| `building_floor_carpet_brown_stack_10` | Brown Carpet Stack | ✅ Yes | — | [building_floor_carpet_brown_stack_10.json](building/building_floor_carpet_brown_stack_10/building_floor_carpet_brown_stack_10.json) |
| `building_floor_carpet_brown_stack_20` | Brown Carpet Stack | ✅ Yes | — | [building_floor_carpet_brown_stack_20.json](building/building_floor_carpet_brown_stack_20/building_floor_carpet_brown_stack_20.json) |
| `building_floor_carpet_burgundy` | Burgundy Carpet | ✅ Yes | — | [building_floor_carpet_burgundy.json](building/building_floor_carpet_burgundy/building_floor_carpet_burgundy.json) |
| `building_floor_carpet_burgundy_stack_10` | Burgundy Carpet Stack | ✅ Yes | — | [building_floor_carpet_burgundy_stack_10.json](building/building_floor_carpet_burgundy_stack_10/building_floor_carpet_burgundy_stack_10.json) |
| `building_floor_carpet_burgundy_stack_20` | Burgundy Carpet Stack | ✅ Yes | — | [building_floor_carpet_burgundy_stack_20.json](building/building_floor_carpet_burgundy_stack_20/building_floor_carpet_burgundy_stack_20.json) |
| `building_floor_carpet_grey` | Grey Carpet | ✅ Yes | — | [building_floor_carpet_grey.json](building/building_floor_carpet_grey/building_floor_carpet_grey.json) |
| `building_floor_carpet_grey_stack_10` | Grey Carpet Stack | ✅ Yes | — | [building_floor_carpet_grey_stack_10.json](building/building_floor_carpet_grey_stack_10/building_floor_carpet_grey_stack_10.json) |
| `building_floor_carpet_grey_stack_20` | Grey Carpet Stack | ✅ Yes | — | [building_floor_carpet_grey_stack_20.json](building/building_floor_carpet_grey_stack_20/building_floor_carpet_grey_stack_20.json) |
| `building_floor_carpet_navy` | Navy Carpet | ✅ Yes | — | [building_floor_carpet_navy.json](building/building_floor_carpet_navy/building_floor_carpet_navy.json) |
| `building_floor_carpet_navy_stack_10` | Navy Carpet Stack | ✅ Yes | — | [building_floor_carpet_navy_stack_10.json](building/building_floor_carpet_navy_stack_10/building_floor_carpet_navy_stack_10.json) |
| `building_floor_carpet_navy_stack_20` | Navy Carpet Stack | ✅ Yes | — | [building_floor_carpet_navy_stack_20.json](building/building_floor_carpet_navy_stack_20/building_floor_carpet_navy_stack_20.json) |
| `building_floor_tile_slate` | Slate Tile | ✅ Yes | — | [building_floor_tile_slate.json](building/building_floor_tile_slate/building_floor_tile_slate.json) |
| `building_floor_tile_slate_stack_10` | Slate Tile Stack | ✅ Yes | — | [building_floor_tile_slate_stack_10.json](building/building_floor_tile_slate_stack_10/building_floor_tile_slate_stack_10.json) |
| `building_floor_tile_slate_stack_20` | Slate Tile Stack | ✅ Yes | — | [building_floor_tile_slate_stack_20.json](building/building_floor_tile_slate_stack_20/building_floor_tile_slate_stack_20.json) |
| `building_floor_tile_speckled` | Speckled Grey Tile | ✅ Yes | — | [building_floor_tile_speckled.json](building/building_floor_tile_speckled/building_floor_tile_speckled.json) |
| `building_floor_tile_speckled_stack_10` | Speckled Grey Tile Stack | ✅ Yes | — | [building_floor_tile_speckled_stack_10.json](building/building_floor_tile_speckled_stack_10/building_floor_tile_speckled_stack_10.json) |
| `building_floor_tile_speckled_stack_20` | Speckled Grey Tile Stack | ✅ Yes | — | [building_floor_tile_speckled_stack_20.json](building/building_floor_tile_speckled_stack_20/building_floor_tile_speckled_stack_20.json) |
| `building_floor_tile_terracotta` | Terracotta Tile | ✅ Yes | — | [building_floor_tile_terracotta.json](building/building_floor_tile_terracotta/building_floor_tile_terracotta.json) |
| `building_floor_tile_terracotta_stack_10` | Terracotta Tile Stack | ✅ Yes | — | [building_floor_tile_terracotta_stack_10.json](building/building_floor_tile_terracotta_stack_10/building_floor_tile_terracotta_stack_10.json) |
| `building_floor_tile_terracotta_stack_20` | Terracotta Tile Stack | ✅ Yes | — | [building_floor_tile_terracotta_stack_20.json](building/building_floor_tile_terracotta_stack_20/building_floor_tile_terracotta_stack_20.json) |
| `building_floor_tile_white` | White Ceramic Tile | ✅ Yes | — | [building_floor_tile_white.json](building/building_floor_tile_white/building_floor_tile_white.json) |
| `building_floor_tile_white_stack_10` | White Ceramic Tile Stack | ✅ Yes | — | [building_floor_tile_white_stack_10.json](building/building_floor_tile_white_stack_10/building_floor_tile_white_stack_10.json) |
| `building_floor_tile_white_stack_20` | White Ceramic Tile Stack | ✅ Yes | — | [building_floor_tile_white_stack_20.json](building/building_floor_tile_white_stack_20/building_floor_tile_white_stack_20.json) |
| `building_floor_vinyl_plank` | Wood-look Vinyl Plank | ✅ Yes | — | [building_floor_vinyl_plank.json](building/building_floor_vinyl_plank/building_floor_vinyl_plank.json) |
| `building_floor_vinyl_plank_stack_10` | Wood-look Vinyl Plank Stack | ✅ Yes | — | [building_floor_vinyl_plank_stack_10.json](building/building_floor_vinyl_plank_stack_10/building_floor_vinyl_plank_stack_10.json) |
| `building_floor_vinyl_plank_stack_20` | Wood-look Vinyl Plank Stack | ✅ Yes | — | [building_floor_vinyl_plank_stack_20.json](building/building_floor_vinyl_plank_stack_20/building_floor_vinyl_plank_stack_20.json) |
| `building_gate_latch` | Gate Latch | ✅ Yes | — | [building_gate_latch.json](building/building_gate_latch/building_gate_latch.json) |
| `building_glass` | Glass Pane | ✅ Yes | — | [building_glass.json](building/building_glass/building_glass.json) |
| `building_glass_stack_10` | Glass Pane Stack | ✅ Yes | — | [building_glass_stack_10.json](building/building_glass_stack_10/building_glass_stack_10.json) |
| `building_glass_stack_20` | Glass Pane Stack | ✅ Yes | — | [building_glass_stack_20.json](building/building_glass_stack_20/building_glass_stack_20.json) |
| `building_grout_bag` | Grout Bag | ✅ Yes | — | [building_grout_bag.json](building/building_grout_bag/building_grout_bag.json) |
| `building_grout_bag_pallet_10` | Grout Bag Pallet | ✅ Yes | — | [building_grout_bag_pallet_10.json](building/building_grout_bag_pallet_10/building_grout_bag_pallet_10.json) |
| `building_grout_bag_pallet_20` | Grout Bag Pallet | ✅ Yes | — | [building_grout_bag_pallet_20.json](building/building_grout_bag_pallet_20/building_grout_bag_pallet_20.json) |
| `building_gutter_bundle` | Gutter Bundle | ✅ Yes | — | [building_gutter_bundle.json](building/building_gutter_bundle/building_gutter_bundle.json) |
| `building_gutter_section` | Gutter Section | ✅ Yes | — | [building_gutter_section.json](building/building_gutter_section/building_gutter_section.json) |
| `building_house_wrap_roll` | House Wrap Roll | ✅ Yes | — | [building_house_wrap_roll.json](building/building_house_wrap_roll/building_house_wrap_roll.json) |
| `building_insulation_blown_bag` | Blown Insulation Bag | ✅ Yes | — | [building_insulation_blown_bag.json](building/building_insulation_blown_bag/building_insulation_blown_bag.json) |
| `building_insulation_blown_bag_pallet_10` | Blown Insulation Bag Pallet | ✅ Yes | — | [building_insulation_blown_bag_pallet_10.json](building/building_insulation_blown_bag_pallet_10/building_insulation_blown_bag_pallet_10.json) |
| `building_insulation_blown_bag_pallet_20` | Blown Insulation Bag Pallet | ✅ Yes | — | [building_insulation_blown_bag_pallet_20.json](building/building_insulation_blown_bag_pallet_20/building_insulation_blown_bag_pallet_20.json) |
| `building_insulation_fiberglass_batt` | Fiberglass Insulation Batt | ✅ Yes | — | [building_insulation_fiberglass_batt.json](building/building_insulation_fiberglass_batt/building_insulation_fiberglass_batt.json) |
| `building_insulation_fiberglass_batt_stack_10` | Fiberglass Insulation Batt Stack | ✅ Yes | — | [building_insulation_fiberglass_batt_stack_10.json](building/building_insulation_fiberglass_batt_stack_10/building_insulation_fiberglass_batt_stack_10.json) |
| `building_insulation_fiberglass_batt_stack_20` | Fiberglass Insulation Batt Stack | ✅ Yes | — | [building_insulation_fiberglass_batt_stack_20.json](building/building_insulation_fiberglass_batt_stack_20/building_insulation_fiberglass_batt_stack_20.json) |
| `building_insulation_foam_board` | Rigid Foam Board | ✅ Yes | — | [building_insulation_foam_board.json](building/building_insulation_foam_board/building_insulation_foam_board.json) |
| `building_insulation_foam_board_stack_large` | Large Foam Board Stack | ✅ Yes | — | [building_insulation_foam_board_stack_large.json](building/building_insulation_foam_board_stack_large/building_insulation_foam_board_stack_large.json) |
| `building_insulation_foam_board_stack_small` | Small Foam Board Stack | ✅ Yes | — | [building_insulation_foam_board_stack_small.json](building/building_insulation_foam_board_stack_small/building_insulation_foam_board_stack_small.json) |
| `building_insulation_spray_foam` | Spray Foam Can | ✅ Yes | — | [building_insulation_spray_foam.json](building/building_insulation_spray_foam/building_insulation_spray_foam.json) |
| `building_insulation_spray_foam_case_16` | Spray Foam Can Case | ✅ Yes | — | [building_insulation_spray_foam_case_16.json](building/building_insulation_spray_foam_case_16/building_insulation_spray_foam_case_16.json) |
| `building_insulation_spray_foam_case_8` | Spray Foam Can Case | ✅ Yes | — | [building_insulation_spray_foam_case_8.json](building/building_insulation_spray_foam_case_8/building_insulation_spray_foam_case_8.json) |
| `building_joint_compound_bucket` | Joint Compound (Bucket) | ✅ Yes | — | [building_joint_compound_bucket.json](building/building_joint_compound_bucket/building_joint_compound_bucket.json) |
| `building_joint_compound_bucket_stack_10` | Joint Compound (Bucket) Stack | ✅ Yes | — | [building_joint_compound_bucket_stack_10.json](building/building_joint_compound_bucket_stack_10/building_joint_compound_bucket_stack_10.json) |
| `building_joint_compound_bucket_stack_20` | Joint Compound (Bucket) Stack | ✅ Yes | — | [building_joint_compound_bucket_stack_20.json](building/building_joint_compound_bucket_stack_20/building_joint_compound_bucket_stack_20.json) |
| `building_light_ceiling_flush` | Flush Ceiling Light | ✅ Yes | — | [building_light_ceiling_flush.json](building/building_light_ceiling_flush/building_light_ceiling_flush.json) |
| `building_light_ceiling_pendant` | Pendant Ceiling Light | ✅ Yes | — | [building_light_ceiling_pendant.json](building/building_light_ceiling_pendant/building_light_ceiling_pendant.json) |
| `building_light_fluorescent_2bulb` | Fluorescent Light (2 Bulb) | ✅ Yes | — | [building_light_fluorescent_2bulb.json](building/building_light_fluorescent_2bulb/building_light_fluorescent_2bulb.json) |
| `building_light_fluorescent_4bulb` | Fluorescent Light (4 Bulb) | ✅ Yes | — | [building_light_fluorescent_4bulb.json](building/building_light_fluorescent_4bulb/building_light_fluorescent_4bulb.json) |
| `building_light_fluorescent_8bulb` | Fluorescent Light (8 Bulb) | ✅ Yes | — | [building_light_fluorescent_8bulb.json](building/building_light_fluorescent_8bulb/building_light_fluorescent_8bulb.json) |
| `building_light_grow_2bulb` | Small Grow Light | ✅ Yes | — | [building_light_grow_2bulb.json](building/building_light_grow_2bulb/building_light_grow_2bulb.json) |
| `building_light_grow_4bulb` | Grow Light | ✅ Yes | — | [building_light_grow_4bulb.json](building/building_light_grow_4bulb/building_light_grow_4bulb.json) |
| `building_light_grow_8bulb` | Large Grow Light | ✅ Yes | — | [building_light_grow_8bulb.json](building/building_light_grow_8bulb/building_light_grow_8bulb.json) |
| `building_light_sconce_exterior` | Wall Lantern | ✅ Yes | — | [building_light_sconce_exterior.json](building/building_light_sconce_exterior/building_light_sconce_exterior.json) |
| `building_light_sconce_interior` | Sconce | ✅ Yes | — | [building_light_sconce_interior.json](building/building_light_sconce_interior/building_light_sconce_interior.json) |
| `building_lumber_joist_2x10` | Joist 2x10 | ✅ Yes | — | [building_lumber_joist_2x10.json](building/building_lumber_joist_2x10/building_lumber_joist_2x10.json) |
| `building_lumber_rafter_2x8` | Rafter 2x8 | ✅ Yes | — | [building_lumber_rafter_2x8.json](building/building_lumber_rafter_2x8/building_lumber_rafter_2x8.json) |
| `building_metal` | Metal Sheet | ✅ Yes | — | [building_metal.json](building/building_metal/building_metal.json) |
| `building_metal_stack_10` | Metal Sheet Stack | ✅ Yes | — | [building_metal_stack_10.json](building/building_metal_stack_10/building_metal_stack_10.json) |
| `building_metal_stack_20` | Metal Sheet Stack | ✅ Yes | — | [building_metal_stack_20.json](building/building_metal_stack_20/building_metal_stack_20.json) |
| `building_mortar_mix_bag` | Mortar Mix Bag | ✅ Yes | — | [building_mortar_mix_bag.json](building/building_mortar_mix_bag/building_mortar_mix_bag.json) |
| `building_mortar_mix_bag_pallet_10` | Mortar Mix Bag Pallet | ✅ Yes | — | [building_mortar_mix_bag_pallet_10.json](building/building_mortar_mix_bag_pallet_10/building_mortar_mix_bag_pallet_10.json) |
| `building_mortar_mix_bag_pallet_20` | Mortar Mix Bag Pallet | ✅ Yes | — | [building_mortar_mix_bag_pallet_20.json](building/building_mortar_mix_bag_pallet_20/building_mortar_mix_bag_pallet_20.json) |
| `building_paint_barn_red` | Interior Paint: Barn Red | ✅ Yes | — | [building_paint_barn_red.json](building/building_paint_barn_red/building_paint_barn_red.json) |
| `building_paint_charcoal` | Interior Paint: Charcoal | ✅ Yes | — | [building_paint_charcoal.json](building/building_paint_charcoal/building_paint_charcoal.json) |
| `building_paint_cream` | Interior Paint: Warm Cream | ✅ Yes | — | [building_paint_cream.json](building/building_paint_cream/building_paint_cream.json) |
| `building_paint_interior_wall` | Interior Wall Paint | ✅ Yes | — | [building_paint_interior_wall.json](building/building_paint_interior_wall/building_paint_interior_wall.json) |
| `building_paint_ivory` | Interior Paint: Ivory | ✅ Yes | — | [building_paint_ivory.json](building/building_paint_ivory/building_paint_ivory.json) |
| `building_paint_lavender` | Interior Paint: Lavender | ✅ Yes | — | [building_paint_lavender.json](building/building_paint_lavender/building_paint_lavender.json) |
| `building_paint_mustard` | Interior Paint: Mustard Yellow | ✅ Yes | — | [building_paint_mustard.json](building/building_paint_mustard/building_paint_mustard.json) |
| `building_paint_navy` | Interior Paint: Deep Navy | ✅ Yes | — | [building_paint_navy.json](building/building_paint_navy/building_paint_navy.json) |
| `building_paint_sage` | Interior Paint: Sage | ✅ Yes | — | [building_paint_sage.json](building/building_paint_sage/building_paint_sage.json) |
| `building_paint_sky_blue` | Interior Paint: Sky Blue | ✅ Yes | — | [building_paint_sky_blue.json](building/building_paint_sky_blue/building_paint_sky_blue.json) |
| `building_paint_terracotta` | Interior Paint: Terracotta | ✅ Yes | — | [building_paint_terracotta.json](building/building_paint_terracotta/building_paint_terracotta.json) |
| `building_pallet_wood` | Mat Pallet Wood | ✅ Yes | — | [building_pallet_wood.json](building/building_pallet_wood/building_pallet_wood.json) |
| `building_pickup_flag` | Pickup Flag | ✅ Yes | — | [building_pickup_flag.json](building/building_pickup_flag/building_pickup_flag.json) |
| `building_pvc_cement_can` | PVC Cement | ✅ Yes | — | [building_pvc_cement_can.json](building/building_pvc_cement_can/building_pvc_cement_can.json) |
| `building_pvc_cement_can_case_12` | PVC Cement Case | ✅ Yes | — | [building_pvc_cement_can_case_12.json](building/building_pvc_cement_can_case_12/building_pvc_cement_can_case_12.json) |
| `building_pvc_cement_can_case_6` | PVC Cement Case | ✅ Yes | — | [building_pvc_cement_can_case_6.json](building/building_pvc_cement_can_case_6/building_pvc_cement_can_case_6.json) |
| `building_pvc_primer_can` | PVC Primer | ✅ Yes | — | [building_pvc_primer_can.json](building/building_pvc_primer_can/building_pvc_primer_can.json) |
| `building_pvc_primer_can_case_12` | PVC Primer Case | ✅ Yes | — | [building_pvc_primer_can_case_12.json](building/building_pvc_primer_can_case_12/building_pvc_primer_can_case_12.json) |
| `building_pvc_primer_can_case_6` | PVC Primer Case | ✅ Yes | — | [building_pvc_primer_can_case_6.json](building/building_pvc_primer_can_case_6/building_pvc_primer_can_case_6.json) |
| `building_rebar_steel_bar` | Rebar Bar | ✅ Yes | — | [building_rebar_steel_bar.json](building/building_rebar_steel_bar/building_rebar_steel_bar.json) |
| `building_rebar_steel_bundle` | Rebar Bundle | ✅ Yes | — | [building_rebar_steel_bundle.json](building/building_rebar_steel_bundle/building_rebar_steel_bundle.json) |
| `building_romex_10_3_spool` | Romex 10-3 Spool | ✅ Yes | — | [building_romex_10_3_spool.json](building/building_romex_10_3_spool/building_romex_10_3_spool.json) |
| `building_romex_10_3_spool_small` | Romex 10-3 Coil | ✅ Yes | — | [building_romex_10_3_spool_small.json](building/building_romex_10_3_spool_small/building_romex_10_3_spool_small.json) |
| `building_romex_14_2_spool` | Romex 14-2 Spool | ✅ Yes | — | [building_romex_14_2_spool.json](building/building_romex_14_2_spool/building_romex_14_2_spool.json) |
| `building_romex_14_2_spool_small` | Romex 14-2 Coil | ✅ Yes | — | [building_romex_14_2_spool_small.json](building/building_romex_14_2_spool_small/building_romex_14_2_spool_small.json) |
| `building_roofing_felt_roll` | Roofing Felt Roll | ✅ Yes | — | [building_roofing_felt_roll.json](building/building_roofing_felt_roll/building_roofing_felt_roll.json) |
| `building_roofing_nails_box` | Roofing Nails (Box) | ✅ Yes | — | [building_roofing_nails_box.json](building/building_roofing_nails_box/building_roofing_nails_box.json) |
| `building_roofing_nails_case` | Roofing Nails Case | ✅ Yes | — | [building_roofing_nails_case.json](building/building_roofing_nails_case/building_roofing_nails_case.json) |
| `building_shelf_wall_steel` | Steel Wall Shelf | ✅ Yes | — | [building_shelf_wall_steel.json](building/building_shelf_wall_steel/building_shelf_wall_steel.json) |
| `building_shelf_wall_wood` | Wall Shelf | ✅ Yes | — | [building_shelf_wall_wood.json](building/building_shelf_wall_wood/building_shelf_wall_wood.json) |
| `building_shelf_wall_wood_long` | Long Wall Shelf | ✅ Yes | — | [building_shelf_wall_wood_long.json](building/building_shelf_wall_wood_long/building_shelf_wall_wood_long.json) |
| `building_shelving_melamine_black` | Black Melamine Shelving Unit | ✅ Yes | — | [building_shelving_melamine_black.json](building/building_shelving_melamine_black/building_shelving_melamine_black.json) |
| `building_shelving_melamine_white` | White Melamine Shelving Unit | ✅ Yes | — | [building_shelving_melamine_white.json](building/building_shelving_melamine_white/building_shelving_melamine_white.json) |
| `building_shelving_steel` | Shelving | ✅ Yes | — | [building_shelving_steel.json](building/building_shelving_steel/building_shelving_steel.json) |
| `building_siding_barn_red` | Barn Red Board Siding | ✅ Yes | — | [building_siding_barn_red.json](building/building_siding_barn_red/building_siding_barn_red.json) |
| `building_siding_barn_red_stack_10` | Barn Red Board Siding Stack | ✅ Yes | — | [building_siding_barn_red_stack_10.json](building/building_siding_barn_red_stack_10/building_siding_barn_red_stack_10.json) |
| `building_siding_barn_red_stack_20` | Barn Red Board Siding Stack | ✅ Yes | — | [building_siding_barn_red_stack_20.json](building/building_siding_barn_red_stack_20/building_siding_barn_red_stack_20.json) |
| `building_siding_brick_veneer` | Red Brick Veneer | ✅ Yes | — | [building_siding_brick_veneer.json](building/building_siding_brick_veneer/building_siding_brick_veneer.json) |
| `building_siding_brick_veneer_stack_10` | Red Brick Veneer Stack | ✅ Yes | — | [building_siding_brick_veneer_stack_10.json](building/building_siding_brick_veneer_stack_10/building_siding_brick_veneer_stack_10.json) |
| `building_siding_brick_veneer_stack_20` | Red Brick Veneer Stack | ✅ Yes | — | [building_siding_brick_veneer_stack_20.json](building/building_siding_brick_veneer_stack_20/building_siding_brick_veneer_stack_20.json) |
| `building_siding_cedar_shake` | Cedar Shake Siding | ✅ Yes | — | [building_siding_cedar_shake.json](building/building_siding_cedar_shake/building_siding_cedar_shake.json) |
| `building_siding_cedar_shake_stack_10` | Cedar Shake Siding Stack | ✅ Yes | — | [building_siding_cedar_shake_stack_10.json](building/building_siding_cedar_shake_stack_10/building_siding_cedar_shake_stack_10.json) |
| `building_siding_cedar_shake_stack_20` | Cedar Shake Siding Stack | ✅ Yes | — | [building_siding_cedar_shake_stack_20.json](building/building_siding_cedar_shake_stack_20/building_siding_cedar_shake_stack_20.json) |
| `building_siding_charcoal_batten` | Charcoal Board and Batten | ✅ Yes | — | [building_siding_charcoal_batten.json](building/building_siding_charcoal_batten/building_siding_charcoal_batten.json) |
| `building_siding_charcoal_batten_stack_10` | Charcoal Board and Batten Stack | ✅ Yes | — | [building_siding_charcoal_batten_stack_10.json](building/building_siding_charcoal_batten_stack_10/building_siding_charcoal_batten_stack_10.json) |
| `building_siding_charcoal_batten_stack_20` | Charcoal Board and Batten Stack | ✅ Yes | — | [building_siding_charcoal_batten_stack_20.json](building/building_siding_charcoal_batten_stack_20/building_siding_charcoal_batten_stack_20.json) |
| `building_siding_cream` | Cream Clapboard Siding | ✅ Yes | — | [building_siding_cream.json](building/building_siding_cream/building_siding_cream.json) |
| `building_siding_cream_stack_10` | Cream Clapboard Siding Stack | ✅ Yes | — | [building_siding_cream_stack_10.json](building/building_siding_cream_stack_10/building_siding_cream_stack_10.json) |
| `building_siding_cream_stack_20` | Cream Clapboard Siding Stack | ✅ Yes | — | [building_siding_cream_stack_20.json](building/building_siding_cream_stack_20/building_siding_cream_stack_20.json) |
| `building_siding_sage` | Sage Clapboard Siding | ✅ Yes | — | [building_siding_sage.json](building/building_siding_sage/building_siding_sage.json) |
| `building_siding_sage_stack_10` | Sage Clapboard Siding Stack | ✅ Yes | — | [building_siding_sage_stack_10.json](building/building_siding_sage_stack_10/building_siding_sage_stack_10.json) |
| `building_siding_sage_stack_20` | Sage Clapboard Siding Stack | ✅ Yes | — | [building_siding_sage_stack_20.json](building/building_siding_sage_stack_20/building_siding_sage_stack_20.json) |
| `building_siding_slate_blue` | Slate Blue Clapboard Siding | ✅ Yes | — | [building_siding_slate_blue.json](building/building_siding_slate_blue/building_siding_slate_blue.json) |
| `building_siding_slate_blue_stack_10` | Slate Blue Clapboard Siding Stack | ✅ Yes | — | [building_siding_slate_blue_stack_10.json](building/building_siding_slate_blue_stack_10/building_siding_slate_blue_stack_10.json) |
| `building_siding_slate_blue_stack_20` | Slate Blue Clapboard Siding Stack | ✅ Yes | — | [building_siding_slate_blue_stack_20.json](building/building_siding_slate_blue_stack_20/building_siding_slate_blue_stack_20.json) |
| `building_siding_stucco_tan` | Tan Stucco Panels | ✅ Yes | — | [building_siding_stucco_tan.json](building/building_siding_stucco_tan/building_siding_stucco_tan.json) |
| `building_siding_stucco_tan_stack_10` | Tan Stucco Panels Stack | ✅ Yes | — | [building_siding_stucco_tan_stack_10.json](building/building_siding_stucco_tan_stack_10/building_siding_stucco_tan_stack_10.json) |
| `building_siding_stucco_tan_stack_20` | Tan Stucco Panels Stack | ✅ Yes | — | [building_siding_stucco_tan_stack_20.json](building/building_siding_stucco_tan_stack_20/building_siding_stucco_tan_stack_20.json) |
| `building_siding_weathered_grey` | Weathered Grey Shiplap | ✅ Yes | — | [building_siding_weathered_grey.json](building/building_siding_weathered_grey/building_siding_weathered_grey.json) |
| `building_siding_weathered_grey_stack_10` | Weathered Grey Shiplap Stack | ✅ Yes | — | [building_siding_weathered_grey_stack_10.json](building/building_siding_weathered_grey_stack_10/building_siding_weathered_grey_stack_10.json) |
| `building_siding_weathered_grey_stack_20` | Weathered Grey Shiplap Stack | ✅ Yes | — | [building_siding_weathered_grey_stack_20.json](building/building_siding_weathered_grey_stack_20/building_siding_weathered_grey_stack_20.json) |
| `building_siding_white` | White Clapboard Siding | ✅ Yes | — | [building_siding_white.json](building/building_siding_white/building_siding_white.json) |
| `building_siding_white_stack_10` | White Clapboard Siding Stack | ✅ Yes | — | [building_siding_white_stack_10.json](building/building_siding_white_stack_10/building_siding_white_stack_10.json) |
| `building_siding_white_stack_20` | White Clapboard Siding Stack | ✅ Yes | — | [building_siding_white_stack_20.json](building/building_siding_white_stack_20/building_siding_white_stack_20.json) |
| `building_soffit_bundle` | Soffit Panel Bundle | ✅ Yes | — | [building_soffit_bundle.json](building/building_soffit_bundle/building_soffit_bundle.json) |
| `building_soffit_panel` | Soffit Panel | ✅ Yes | — | [building_soffit_panel.json](building/building_soffit_panel/building_soffit_panel.json) |
| `building_steel_frame_beam` | Steel Rigid Frame Beam | ✅ Yes | — | [building_steel_frame_beam.json](building/building_steel_frame_beam/building_steel_frame_beam.json) |
| `building_steel_frame_beam_stack_10` | Steel Rigid Frame Beam Stack | ✅ Yes | — | [building_steel_frame_beam_stack_10.json](building/building_steel_frame_beam_stack_10/building_steel_frame_beam_stack_10.json) |
| `building_steel_frame_beam_stack_20` | Steel Rigid Frame Beam Stack | ✅ Yes | — | [building_steel_frame_beam_stack_20.json](building/building_steel_frame_beam_stack_20/building_steel_frame_beam_stack_20.json) |
| `building_steel_siding_corrugated` | Steel Siding | ✅ Yes | — | [building_steel_siding_corrugated.json](building/building_steel_siding_corrugated/building_steel_siding_corrugated.json) |
| `building_steel_siding_corrugated_black` | Black Steel Siding | ✅ Yes | — | [building_steel_siding_corrugated_black.json](building/building_steel_siding_corrugated_black/building_steel_siding_corrugated_black.json) |
| `building_steel_siding_corrugated_black_stack_10` | Black Steel Siding Stack | ✅ Yes | — | [building_steel_siding_corrugated_black_stack_10.json](building/building_steel_siding_corrugated_black_stack_10/building_steel_siding_corrugated_black_stack_10.json) |
| `building_steel_siding_corrugated_black_stack_20` | Black Steel Siding Stack | ✅ Yes | — | [building_steel_siding_corrugated_black_stack_20.json](building/building_steel_siding_corrugated_black_stack_20/building_steel_siding_corrugated_black_stack_20.json) |
| `building_steel_siding_corrugated_green` | Green Steel Siding | ✅ Yes | — | [building_steel_siding_corrugated_green.json](building/building_steel_siding_corrugated_green/building_steel_siding_corrugated_green.json) |
| `building_steel_siding_corrugated_green_stack_10` | Green Steel Siding Stack | ✅ Yes | — | [building_steel_siding_corrugated_green_stack_10.json](building/building_steel_siding_corrugated_green_stack_10/building_steel_siding_corrugated_green_stack_10.json) |
| `building_steel_siding_corrugated_green_stack_20` | Green Steel Siding Stack | ✅ Yes | — | [building_steel_siding_corrugated_green_stack_20.json](building/building_steel_siding_corrugated_green_stack_20/building_steel_siding_corrugated_green_stack_20.json) |
| `building_steel_siding_corrugated_red` | Red Steel Siding | ✅ Yes | — | [building_steel_siding_corrugated_red.json](building/building_steel_siding_corrugated_red/building_steel_siding_corrugated_red.json) |
| `building_steel_siding_corrugated_red_stack_10` | Red Steel Siding Stack | ✅ Yes | — | [building_steel_siding_corrugated_red_stack_10.json](building/building_steel_siding_corrugated_red_stack_10/building_steel_siding_corrugated_red_stack_10.json) |
| `building_steel_siding_corrugated_red_stack_20` | Red Steel Siding Stack | ✅ Yes | — | [building_steel_siding_corrugated_red_stack_20.json](building/building_steel_siding_corrugated_red_stack_20/building_steel_siding_corrugated_red_stack_20.json) |
| `building_steel_siding_corrugated_stack_10` | Steel Siding Stack | ✅ Yes | — | [building_steel_siding_corrugated_stack_10.json](building/building_steel_siding_corrugated_stack_10/building_steel_siding_corrugated_stack_10.json) |
| `building_steel_siding_corrugated_stack_20` | Steel Siding Stack | ✅ Yes | — | [building_steel_siding_corrugated_stack_20.json](building/building_steel_siding_corrugated_stack_20/building_steel_siding_corrugated_stack_20.json) |
| `building_steel_stud_framing` | Steel Stud (Metal Framing) | ✅ Yes | — | [building_steel_stud_framing.json](building/building_steel_stud_framing/building_steel_stud_framing.json) |
| `building_steel_stud_framing_stack_10` | Steel Stud (Metal Framing) Stack | ✅ Yes | — | [building_steel_stud_framing_stack_10.json](building/building_steel_stud_framing_stack_10/building_steel_stud_framing_stack_10.json) |
| `building_steel_stud_framing_stack_20` | Steel Stud (Metal Framing) Stack | ✅ Yes | — | [building_steel_stud_framing_stack_20.json](building/building_steel_stud_framing_stack_20/building_steel_stud_framing_stack_20.json) |
| `building_thinset_bucket` | Tile Adhesive (Bucket) | ✅ Yes | — | [building_thinset_bucket.json](building/building_thinset_bucket/building_thinset_bucket.json) |
| `building_thinset_bucket_stack_10` | Tile Adhesive (Bucket) Stack | ✅ Yes | — | [building_thinset_bucket_stack_10.json](building/building_thinset_bucket_stack_10/building_thinset_bucket_stack_10.json) |
| `building_thinset_bucket_stack_20` | Tile Adhesive (Bucket) Stack | ✅ Yes | — | [building_thinset_bucket_stack_20.json](building/building_thinset_bucket_stack_20/building_thinset_bucket_stack_20.json) |
| `building_trim_baseboard` | Baseboard Bundle | ✅ Yes | — | [building_trim_baseboard.json](building/building_trim_baseboard/building_trim_baseboard.json) |
| `building_trim_casing` | Door and Window Casing | ✅ Yes | — | [building_trim_casing.json](building/building_trim_casing/building_trim_casing.json) |
| `building_truss_large` | Large Roof Truss | ✅ Yes | — | [building_truss_large.json](building/building_truss_large/building_truss_large.json) |
| `building_truss_large_pack` | Large Roof Truss Pack | ✅ Yes | — | [building_truss_large_pack.json](building/building_truss_large_pack/building_truss_large_pack.json) |
| `building_truss_medium` | Medium Roof Truss | ✅ Yes | — | [building_truss_medium.json](building/building_truss_medium/building_truss_medium.json) |
| `building_truss_medium_pack` | Medium Roof Truss Pack | ✅ Yes | — | [building_truss_medium_pack.json](building/building_truss_medium_pack/building_truss_medium_pack.json) |
| `building_truss_small` | Small Roof Truss | ✅ Yes | — | [building_truss_small.json](building/building_truss_small/building_truss_small.json) |
| `building_truss_small_pack` | Small Roof Truss Pack | ✅ Yes | — | [building_truss_small_pack.json](building/building_truss_small_pack/building_truss_small_pack.json) |
| `building_valve_ball_pvc` | PVC Ball Valve | ✅ Yes | — | [building_valve_ball_pvc.json](building/building_valve_ball_pvc/building_valve_ball_pvc.json) |
| `building_valve_ball_pvc_case_10` | PVC Ball Valve Case | ✅ Yes | — | [building_valve_ball_pvc_case_10.json](building/building_valve_ball_pvc_case_10/building_valve_ball_pvc_case_10.json) |
| `building_valve_ball_pvc_case_20` | PVC Ball Valve Case | ✅ Yes | — | [building_valve_ball_pvc_case_20.json](building/building_valve_ball_pvc_case_20/building_valve_ball_pvc_case_20.json) |
| `building_weatherstripping_roll` | Weather Stripping | ✅ Yes | — | [building_weatherstripping_roll.json](building/building_weatherstripping_roll/building_weatherstripping_roll.json) |
| `building_weatherstripping_roll_case_12` | Weather Stripping Case | ✅ Yes | — | [building_weatherstripping_roll_case_12.json](building/building_weatherstripping_roll_case_12/building_weatherstripping_roll_case_12.json) |
| `building_weatherstripping_roll_case_6` | Weather Stripping Case | ✅ Yes | — | [building_weatherstripping_roll_case_6.json](building/building_weatherstripping_roll_case_6/building_weatherstripping_roll_case_6.json) |
| `building_window_double_hung` | Double-Hung Window | ✅ Yes | — | [building_window_double_hung.json](building/building_window_double_hung/building_window_double_hung.json) |
| `building_window_picture` | Picture Window | ✅ Yes | — | [building_window_picture.json](building/building_window_picture/building_window_picture.json) |
| `building_window_slider` | Sliding Window | ✅ Yes | — | [building_window_slider.json](building/building_window_slider/building_window_slider.json) |
| `camp_campfire_ring` | Camp Campfire Ring | ✅ Yes | — | [camp_campfire_ring.json](building/camp_campfire_ring/camp_campfire_ring.json) |
| `camp_picnictable_wood` | Camp Picnictable Wood | ✅ Yes | — | [camp_picnictable_wood.json](building/camp_picnictable_wood/camp_picnictable_wood.json) |
| `crate_plastic_large` | Large Plastic Crate | ✅ Yes | — | [crate_plastic_large.json](building/crate_plastic_large/crate_plastic_large.json) |
| `crate_plastic_medium` | Medium Plastic Crate | ✅ Yes | — | [crate_plastic_medium.json](building/crate_plastic_medium/crate_plastic_medium.json) |
| `crate_plastic_small` | Small Plastic Crate | ✅ Yes | — | [crate_plastic_small.json](building/crate_plastic_small/crate_plastic_small.json) |
| `crate_wood_large` | Large Wooden Crate | ✅ Yes | — | [crate_wood_large.json](building/crate_wood_large/crate_wood_large.json) |
| `crate_wood_medium` | Medium Wooden Crate | ✅ Yes | — | [crate_wood_medium.json](building/crate_wood_medium/crate_wood_medium.json) |
| `crate_wood_small` | Small Wooden Crate | ✅ Yes | — | [crate_wood_small.json](building/crate_wood_small/crate_wood_small.json) |
| `deck_screw` | Deck Screw | ✅ Yes | — | [deck_screw.json](building/deck_screw/deck_screw.json) |
| `deck_screws_case_10` | Deck Screws Case | ✅ Yes | — | [deck_screws_case_10.json](building/deck_screws_case_10/deck_screws_case_10.json) |
| `deck_screws_case_20` | Deck Screws Case | ✅ Yes | — | [deck_screws_case_20.json](building/deck_screws_case_20/deck_screws_case_20.json) |
| `dock_large_new` | Large New Dock | ✅ Yes | — | [dock_large_new.json](building/dock_large_new/dock_large_new.json) |
| `dock_large_old` | Large Old Dock | ✅ Yes | — | [dock_large_old.json](building/dock_large_old/dock_large_old.json) |
| `dock_small_new` | Small New Dock | ✅ Yes | — | [dock_small_new.json](building/dock_small_new/dock_small_new.json) |
| `dock_small_old` | Small Old Dock | ✅ Yes | — | [dock_small_old.json](building/dock_small_old/dock_small_old.json) |
| `drain_french_sock` | French Drain Pipe | ✅ Yes | — | [drain_french_sock.json](building/drain_french_sock/drain_french_sock.json) |
| `drain_french_sock_stack_10` | French Drain Pipe Stack | ✅ Yes | — | [drain_french_sock_stack_10.json](building/drain_french_sock_stack_10/drain_french_sock_stack_10.json) |
| `drain_french_sock_stack_20` | French Drain Pipe Stack | ✅ Yes | — | [drain_french_sock_stack_20.json](building/drain_french_sock_stack_20/drain_french_sock_stack_20.json) |
| `fence_wire` | Wire Fence Section | — | — | [fence_wire.json](building/fence_wire/fence_wire.json) |
| `fence_wood` | Wood Fence Section | — | — | [fence_wood.json](building/fence_wood/fence_wood.json) |
| `finishing_nail` | Finishing Nail | ✅ Yes | — | [finishing_nail.json](building/finishing_nail/finishing_nail.json) |
| `finishing_nails_case_10` | Finishing Nails Case | ✅ Yes | — | [finishing_nails_case_10.json](building/finishing_nails_case_10/finishing_nails_case_10.json) |
| `finishing_nails_case_20` | Finishing Nails Case | ✅ Yes | — | [finishing_nails_case_20.json](building/finishing_nails_case_20/finishing_nails_case_20.json) |
| `framing_nail` | Framing Nail | ✅ Yes | — | [framing_nail.json](building/framing_nail/framing_nail.json) |
| `framing_nails_case_10` | Framing Nails Case | ✅ Yes | — | [framing_nails_case_10.json](building/framing_nails_case_10/framing_nails_case_10.json) |
| `framing_nails_case_20` | Framing Nails Case | ✅ Yes | — | [framing_nails_case_20.json](building/framing_nails_case_20/framing_nails_case_20.json) |
| `gate_metal` | Metal Farm Gate | — | — | [gate_metal.json](building/gate_metal/gate_metal.json) |
| `gate_wood` | Wood Farm Gate | — | — | [gate_wood.json](building/gate_wood/gate_wood.json) |
| `gland_cable_entry_wall` | Wall Cable Entry Gland | ✅ Yes | — | [gland_cable_entry_wall.json](building/gland_cable_entry_wall/gland_cable_entry_wall.json) |
| `hardware_gate_hinges` | Gate Strap Hinge | ✅ Yes | — | [hardware_gate_hinges.json](building/hardware_gate_hinges/hardware_gate_hinges.json) |
| `hardware_hurricane_ties` | Hurricane Ties Pair | ✅ Yes | — | [hardware_hurricane_ties.json](building/hardware_hurricane_ties/hardware_hurricane_ties.json) |
| `hurricane_ties_case_10` | Hurricane Ties Case | ✅ Yes | — | [hurricane_ties_case_10.json](building/hurricane_ties_case_10/hurricane_ties_case_10.json) |
| `hurricane_ties_case_20` | Hurricane Ties Case | ✅ Yes | — | [hurricane_ties_case_20.json](building/hurricane_ties_case_20/hurricane_ties_case_20.json) |
| `icon_wood_log` | Icon Wood Log | — | — | [icon_wood_log.json](building/icon_wood_log/icon_wood_log.json) |
| `insulators_tpost_pack` | T-Post Insulators Pack | ✅ Yes | — | [insulators_tpost_pack.json](building/insulators_tpost_pack/insulators_tpost_pack.json) |
| `item_hardware_rebarbundle` | Large Rebar Bundle | ✅ Yes | — | [item_hardware_rebarbundle.json](building/item_hardware_rebarbundle/item_hardware_rebarbundle.json) |
| `item_spool_barbedwire` | Item Spool Barbedwire | ✅ Yes | — | [item_spool_barbedwire.json](building/item_spool_barbedwire/item_spool_barbedwire.json) |
| `item_spool_cat6_150m` | Cat6 Cable Spool (Building) | ✅ Yes | — | [item_spool_cat6_150m.json](building/item_spool_cat6_150m/item_spool_cat6_150m.json) |
| `item_spool_romex_12_2` | Romex 12-2 Coil | ✅ Yes | — | [item_spool_romex_12_2.json](building/item_spool_romex_12_2/item_spool_romex_12_2.json) |
| `joist_hanger` | Joist Hanger | ✅ Yes | — | [joist_hanger.json](building/joist_hanger/joist_hanger.json) |
| `joist_hangers_case_10` | Joist Hangers Case | ✅ Yes | — | [joist_hangers_case_10.json](building/joist_hangers_case_10/joist_hangers_case_10.json) |
| `joist_hangers_case_20` | Joist Hangers Case | ✅ Yes | — | [joist_hangers_case_20.json](building/joist_hangers_case_20/joist_hangers_case_20.json) |
| `lag_bolt` | Lag Bolt | ✅ Yes | — | [lag_bolt.json](building/lag_bolt/lag_bolt.json) |
| `lag_bolts_case_10` | Lag Bolts Case | ✅ Yes | — | [lag_bolts_case_10.json](building/lag_bolts_case_10/lag_bolts_case_10.json) |
| `lag_bolts_case_20` | Lag Bolts Case | ✅ Yes | — | [lag_bolts_case_20.json](building/lag_bolts_case_20/lag_bolts_case_20.json) |
| `lot_asphalt` | Asphalt Lot Blueprint | — | — | [lot_asphalt.json](building/lot_asphalt/lot_asphalt.json) |
| `lot_concrete` | Concrete Lot Blueprint | — | — | [lot_concrete.json](building/lot_concrete/lot_concrete.json) |
| `lot_dirt` | Dirt Lot Blueprint | — | — | [lot_dirt.json](building/lot_dirt/lot_dirt.json) |
| `lot_gravel` | Gravel Lot Blueprint | — | — | [lot_gravel.json](building/lot_gravel/lot_gravel.json) |
| `lumber_board_2x6` | 2x6 Lumber Board | ✅ Yes | — | [lumber_board_2x6.json](building/lumber_board_2x6/lumber_board_2x6.json) |
| `lumber_bundle_2x10_large` | Large 2x10 Bundle | ✅ Yes | — | [lumber_bundle_2x10_large.json](building/lumber_bundle_2x10_large/lumber_bundle_2x10_large.json) |
| `lumber_bundle_2x10_small` | Small 2x10 Bundle | ✅ Yes | — | [lumber_bundle_2x10_small.json](building/lumber_bundle_2x10_small/lumber_bundle_2x10_small.json) |
| `lumber_bundle_2x4_large` | Large 2x4 Bundle | ✅ Yes | — | [lumber_bundle_2x4_large.json](building/lumber_bundle_2x4_large/lumber_bundle_2x4_large.json) |
| `lumber_bundle_2x4_small` | Small 2x4 Bundle | ✅ Yes | — | [lumber_bundle_2x4_small.json](building/lumber_bundle_2x4_small/lumber_bundle_2x4_small.json) |
| `lumber_bundle_2x6_large` | Large 2x6 Bundle | ✅ Yes | — | [lumber_bundle_2x6_large.json](building/lumber_bundle_2x6_large/lumber_bundle_2x6_large.json) |
| `lumber_bundle_2x6_small` | Small 2x6 Bundle | ✅ Yes | — | [lumber_bundle_2x6_small.json](building/lumber_bundle_2x6_small/lumber_bundle_2x6_small.json) |
| `lumber_joist_2x8` | 2x8 Joist Beam | ✅ Yes | — | [lumber_joist_2x8.json](building/lumber_joist_2x8/lumber_joist_2x8.json) |
| `lumber_joist_2x8_stack_10` | 2x8 Joist Beam (Stack of 10) | ✅ Yes | — | [lumber_joist_2x8_stack_10.json](building/lumber_joist_2x8_stack_10/lumber_joist_2x8_stack_10.json) |
| `lumber_joist_2x8_stack_20` | 2x8 Joist Beam (Stack of 20) | ✅ Yes | — | [lumber_joist_2x8_stack_20.json](building/lumber_joist_2x8_stack_20/lumber_joist_2x8_stack_20.json) |
| `lumber_post_4x4` | 4x4 Treated Post | ✅ Yes | — | [lumber_post_4x4.json](building/lumber_post_4x4/lumber_post_4x4.json) |
| `lumber_post_4x4_stack_10` | 4x4 Treated Post (Stack of 10) | ✅ Yes | — | [lumber_post_4x4_stack_10.json](building/lumber_post_4x4_stack_10/lumber_post_4x4_stack_10.json) |
| `lumber_post_4x4_stack_20` | 4x4 Treated Post (Stack of 20) | ✅ Yes | — | [lumber_post_4x4_stack_20.json](building/lumber_post_4x4_stack_20/lumber_post_4x4_stack_20.json) |
| `lumber_stud_2x4` | 2x4 Lumber Stud | ✅ Yes | — | [lumber_stud_2x4.json](building/lumber_stud_2x4/lumber_stud_2x4.json) |
| `masonry_brick_brown` | Brown Brick | ✅ Yes | — | [masonry_brick_brown.json](building/masonry_brick_brown/masonry_brick_brown.json) |
| `masonry_brick_brown_stack_10` | Brown Brick Stack | ✅ Yes | — | [masonry_brick_brown_stack_10.json](building/masonry_brick_brown_stack_10/masonry_brick_brown_stack_10.json) |
| `masonry_brick_brown_stack_20` | Brown Brick Stack | ✅ Yes | — | [masonry_brick_brown_stack_20.json](building/masonry_brick_brown_stack_20/masonry_brick_brown_stack_20.json) |
| `masonry_brick_charcoal` | Charcoal Brick | ✅ Yes | — | [masonry_brick_charcoal.json](building/masonry_brick_charcoal/masonry_brick_charcoal.json) |
| `masonry_brick_charcoal_stack_10` | Charcoal Brick Stack | ✅ Yes | — | [masonry_brick_charcoal_stack_10.json](building/masonry_brick_charcoal_stack_10/masonry_brick_charcoal_stack_10.json) |
| `masonry_brick_charcoal_stack_20` | Charcoal Brick Stack | ✅ Yes | — | [masonry_brick_charcoal_stack_20.json](building/masonry_brick_charcoal_stack_20/masonry_brick_charcoal_stack_20.json) |
| `masonry_brick_dark_red` | Dark Red Brick | ✅ Yes | — | [masonry_brick_dark_red.json](building/masonry_brick_dark_red/masonry_brick_dark_red.json) |
| `masonry_brick_dark_red_stack_10` | Dark Red Brick Stack | ✅ Yes | — | [masonry_brick_dark_red_stack_10.json](building/masonry_brick_dark_red_stack_10/masonry_brick_dark_red_stack_10.json) |
| `masonry_brick_dark_red_stack_20` | Dark Red Brick Stack | ✅ Yes | — | [masonry_brick_dark_red_stack_20.json](building/masonry_brick_dark_red_stack_20/masonry_brick_dark_red_stack_20.json) |
| `masonry_brick_grey` | Grey Brick | ✅ Yes | — | [masonry_brick_grey.json](building/masonry_brick_grey/masonry_brick_grey.json) |
| `masonry_brick_grey_stack_10` | Grey Brick Stack | ✅ Yes | — | [masonry_brick_grey_stack_10.json](building/masonry_brick_grey_stack_10/masonry_brick_grey_stack_10.json) |
| `masonry_brick_grey_stack_20` | Grey Brick Stack | ✅ Yes | — | [masonry_brick_grey_stack_20.json](building/masonry_brick_grey_stack_20/masonry_brick_grey_stack_20.json) |
| `masonry_brick_old_mill` | Old Mill Red Brick | ✅ Yes | — | [masonry_brick_old_mill.json](building/masonry_brick_old_mill/masonry_brick_old_mill.json) |
| `masonry_brick_old_mill_stack_10` | Old Mill Red Brick Stack | ✅ Yes | — | [masonry_brick_old_mill_stack_10.json](building/masonry_brick_old_mill_stack_10/masonry_brick_old_mill_stack_10.json) |
| `masonry_brick_old_mill_stack_20` | Old Mill Red Brick Stack | ✅ Yes | — | [masonry_brick_old_mill_stack_20.json](building/masonry_brick_old_mill_stack_20/masonry_brick_old_mill_stack_20.json) |
| `masonry_brick_oxblood` | Oxblood Brick | ✅ Yes | — | [masonry_brick_oxblood.json](building/masonry_brick_oxblood/masonry_brick_oxblood.json) |
| `masonry_brick_oxblood_stack_10` | Oxblood Brick Stack | ✅ Yes | — | [masonry_brick_oxblood_stack_10.json](building/masonry_brick_oxblood_stack_10/masonry_brick_oxblood_stack_10.json) |
| `masonry_brick_oxblood_stack_20` | Oxblood Brick Stack | ✅ Yes | — | [masonry_brick_oxblood_stack_20.json](building/masonry_brick_oxblood_stack_20/masonry_brick_oxblood_stack_20.json) |
| `masonry_brick_pressed_red` | Pressed Red Brick | ✅ Yes | — | [masonry_brick_pressed_red.json](building/masonry_brick_pressed_red/masonry_brick_pressed_red.json) |
| `masonry_brick_pressed_red_stack_10` | Pressed Red Brick Stack | ✅ Yes | — | [masonry_brick_pressed_red_stack_10.json](building/masonry_brick_pressed_red_stack_10/masonry_brick_pressed_red_stack_10.json) |
| `masonry_brick_pressed_red_stack_20` | Pressed Red Brick Stack | ✅ Yes | — | [masonry_brick_pressed_red_stack_20.json](building/masonry_brick_pressed_red_stack_20/masonry_brick_pressed_red_stack_20.json) |
| `masonry_brick_red` | Red Clay Brick | ✅ Yes | — | [masonry_brick_red.json](building/masonry_brick_red/masonry_brick_red.json) |
| `masonry_brick_red_stack_10` | Red Clay Brick Stack | ✅ Yes | — | [masonry_brick_red_stack_10.json](building/masonry_brick_red_stack_10/masonry_brick_red_stack_10.json) |
| `masonry_brick_red_stack_20` | Red Clay Brick Stack | ✅ Yes | — | [masonry_brick_red_stack_20.json](building/masonry_brick_red_stack_20/masonry_brick_red_stack_20.json) |
| `masonry_brick_rust` | Rust Red Brick | ✅ Yes | — | [masonry_brick_rust.json](building/masonry_brick_rust/masonry_brick_rust.json) |
| `masonry_brick_rust_stack_10` | Rust Red Brick Stack | ✅ Yes | — | [masonry_brick_rust_stack_10.json](building/masonry_brick_rust_stack_10/masonry_brick_rust_stack_10.json) |
| `masonry_brick_rust_stack_20` | Rust Red Brick Stack | ✅ Yes | — | [masonry_brick_rust_stack_20.json](building/masonry_brick_rust_stack_20/masonry_brick_rust_stack_20.json) |
| `masonry_brick_salmon` | Salmon Red Brick | ✅ Yes | — | [masonry_brick_salmon.json](building/masonry_brick_salmon/masonry_brick_salmon.json) |
| `masonry_brick_salmon_stack_10` | Salmon Red Brick Stack | ✅ Yes | — | [masonry_brick_salmon_stack_10.json](building/masonry_brick_salmon_stack_10/masonry_brick_salmon_stack_10.json) |
| `masonry_brick_salmon_stack_20` | Salmon Red Brick Stack | ✅ Yes | — | [masonry_brick_salmon_stack_20.json](building/masonry_brick_salmon_stack_20/masonry_brick_salmon_stack_20.json) |
| `masonry_brick_tan` | Tan Brick | ✅ Yes | — | [masonry_brick_tan.json](building/masonry_brick_tan/masonry_brick_tan.json) |
| `masonry_brick_tan_stack_10` | Tan Brick Stack | ✅ Yes | — | [masonry_brick_tan_stack_10.json](building/masonry_brick_tan_stack_10/masonry_brick_tan_stack_10.json) |
| `masonry_brick_tan_stack_20` | Tan Brick Stack | ✅ Yes | — | [masonry_brick_tan_stack_20.json](building/masonry_brick_tan_stack_20/masonry_brick_tan_stack_20.json) |
| `masonry_brick_white` | White Washed Brick | ✅ Yes | — | [masonry_brick_white.json](building/masonry_brick_white/masonry_brick_white.json) |
| `masonry_brick_white_stack_10` | White Washed Brick Stack | ✅ Yes | — | [masonry_brick_white_stack_10.json](building/masonry_brick_white_stack_10/masonry_brick_white_stack_10.json) |
| `masonry_brick_white_stack_20` | White Washed Brick Stack | ✅ Yes | — | [masonry_brick_white_stack_20.json](building/masonry_brick_white_stack_20/masonry_brick_white_stack_20.json) |
| `masonry_fieldstone` | Field Stone | ✅ Yes | — | [masonry_fieldstone.json](building/masonry_fieldstone/masonry_fieldstone.json) |
| `masonry_fieldstone_stack_10` | Field Stone Stack | ✅ Yes | — | [masonry_fieldstone_stack_10.json](building/masonry_fieldstone_stack_10/masonry_fieldstone_stack_10.json) |
| `masonry_fieldstone_stack_20` | Field Stone Stack | ✅ Yes | — | [masonry_fieldstone_stack_20.json](building/masonry_fieldstone_stack_20/masonry_fieldstone_stack_20.json) |
| `part_floor_stone_1m` | Part Floor Stone | ✅ Yes | — | [part_floor_stone_1m.json](building/part_floor_stone_1m/part_floor_stone_1m.json) |
| `part_floor_wood_1m` | Part Floor Wood | ✅ Yes | — | [part_floor_wood_1m.json](building/part_floor_wood_1m/part_floor_wood_1m.json) |
| `path_dirt` | Dirt Path Blueprint | — | — | [path_dirt.json](building/path_dirt/path_dirt.json) |
| `path_gravel` | Gravel Path Blueprint | — | — | [path_gravel.json](building/path_gravel/path_gravel.json) |
| `path_stone` | Flagstone Path Blueprint | — | — | [path_stone.json](building/path_stone/path_stone.json) |
| `pipe_abs_waste_three_inch` | 3" Black Waste Pipe | ✅ Yes | — | [pipe_abs_waste_three_inch.json](building/pipe_abs_waste_three_inch/pipe_abs_waste_three_inch.json) |
| `pipe_leach_perforated_4inch` | 4" Perforated Leach Pipe | ✅ Yes | — | [pipe_leach_perforated_4inch.json](building/pipe_leach_perforated_4inch/pipe_leach_perforated_4inch.json) |
| `pipe_leach_perforated_4inch_stack_10` | 4" Perforated Leach Pipe (Stack of 10) | ✅ Yes | — | [pipe_leach_perforated_4inch_stack_10.json](building/pipe_leach_perforated_4inch_stack_10/pipe_leach_perforated_4inch_stack_10.json) |
| `pipe_leach_perforated_4inch_stack_20` | 4" Perforated Leach Pipe (Stack of 20) | ✅ Yes | — | [pipe_leach_perforated_4inch_stack_20.json](building/pipe_leach_perforated_4inch_stack_20/pipe_leach_perforated_4inch_stack_20.json) |
| `pipe_pvc_elbow` | PVC 90-Degree Elbow | ✅ Yes | — | [pipe_pvc_elbow.json](building/pipe_pvc_elbow/pipe_pvc_elbow.json) |
| `pipe_pvc_elbow_case_10` | PVC 90-Degree Elbow Case | ✅ Yes | — | [pipe_pvc_elbow_case_10.json](building/pipe_pvc_elbow_case_10/pipe_pvc_elbow_case_10.json) |
| `pipe_pvc_elbow_case_20` | PVC 90-Degree Elbow Case | ✅ Yes | — | [pipe_pvc_elbow_case_20.json](building/pipe_pvc_elbow_case_20/pipe_pvc_elbow_case_20.json) |
| `pipe_pvc_half_inch` | 1/2" PVC Pipe | ✅ Yes | — | [pipe_pvc_half_inch.json](building/pipe_pvc_half_inch/pipe_pvc_half_inch.json) |
| `pipe_pvc_half_inch_stack_10` | 1/2" PVC Pipe (Stack of 10) | ✅ Yes | — | [pipe_pvc_half_inch_stack_10.json](building/pipe_pvc_half_inch_stack_10/pipe_pvc_half_inch_stack_10.json) |
| `pipe_pvc_half_inch_stack_20` | 1/2" PVC Pipe (Stack of 20) | ✅ Yes | — | [pipe_pvc_half_inch_stack_20.json](building/pipe_pvc_half_inch_stack_20/pipe_pvc_half_inch_stack_20.json) |
| `pipe_pvc_one_inch` | 1" PVC Pipe | ✅ Yes | — | [pipe_pvc_one_inch.json](building/pipe_pvc_one_inch/pipe_pvc_one_inch.json) |
| `pipe_pvc_one_inch_stack_10` | 1" PVC Pipe (Stack of 10) | ✅ Yes | — | [pipe_pvc_one_inch_stack_10.json](building/pipe_pvc_one_inch_stack_10/pipe_pvc_one_inch_stack_10.json) |
| `pipe_pvc_one_inch_stack_20` | 1" PVC Pipe (Stack of 20) | ✅ Yes | — | [pipe_pvc_one_inch_stack_20.json](building/pipe_pvc_one_inch_stack_20/pipe_pvc_one_inch_stack_20.json) |
| `pipe_pvc_tee` | PVC Tee Fitting | ✅ Yes | — | [pipe_pvc_tee.json](building/pipe_pvc_tee/pipe_pvc_tee.json) |
| `pipe_pvc_tee_case_10` | PVC Tee Fitting Case | ✅ Yes | — | [pipe_pvc_tee_case_10.json](building/pipe_pvc_tee_case_10/pipe_pvc_tee_case_10.json) |
| `pipe_pvc_tee_case_20` | PVC Tee Fitting Case | ✅ Yes | — | [pipe_pvc_tee_case_20.json](building/pipe_pvc_tee_case_20/pipe_pvc_tee_case_20.json) |
| `pipe_pvc_two_inch` | 2" PVC Pipe | ✅ Yes | — | [pipe_pvc_two_inch.json](building/pipe_pvc_two_inch/pipe_pvc_two_inch.json) |
| `pipe_pvc_two_inch_stack_10` | 2" PVC Pipe (Stack of 10) | ✅ Yes | — | [pipe_pvc_two_inch_stack_10.json](building/pipe_pvc_two_inch_stack_10/pipe_pvc_two_inch_stack_10.json) |
| `pipe_pvc_two_inch_stack_20` | 2" PVC Pipe (Stack of 20) | ✅ Yes | — | [pipe_pvc_two_inch_stack_20.json](building/pipe_pvc_two_inch_stack_20/pipe_pvc_two_inch_stack_20.json) |
| `pipe_sewer_solid_4inch` | 4" Sewer Pipe | ✅ Yes | — | [pipe_sewer_solid_4inch.json](building/pipe_sewer_solid_4inch/pipe_sewer_solid_4inch.json) |
| `pipe_sewer_solid_4inch_stack_10` | 4" Sewer Pipe (Stack of 10) | ✅ Yes | — | [pipe_sewer_solid_4inch_stack_10.json](building/pipe_sewer_solid_4inch_stack_10/pipe_sewer_solid_4inch_stack_10.json) |
| `pipe_sewer_solid_4inch_stack_20` | 4" Sewer Pipe (Stack of 20) | ✅ Yes | — | [pipe_sewer_solid_4inch_stack_20.json](building/pipe_sewer_solid_4inch_stack_20/pipe_sewer_solid_4inch_stack_20.json) |
| `post_wood_round_6inch` | 6" Round Wood Post | ✅ Yes | — | [post_wood_round_6inch.json](building/post_wood_round_6inch/post_wood_round_6inch.json) |
| `post_wood_round_6inch_stack_10` | 6" Round Wood Post (Stack of 10) | ✅ Yes | — | [post_wood_round_6inch_stack_10.json](building/post_wood_round_6inch_stack_10/post_wood_round_6inch_stack_10.json) |
| `post_wood_round_6inch_stack_20` | 6" Round Wood Post (Stack of 20) | ✅ Yes | — | [post_wood_round_6inch_stack_20.json](building/post_wood_round_6inch_stack_20/post_wood_round_6inch_stack_20.json) |
| `road_asphalt` | Asphalt Road Blueprint | — | — | [road_asphalt.json](building/road_asphalt/road_asphalt.json) |
| `road_gravel` | Gravel Road Blueprint | — | — | [road_gravel.json](building/road_gravel/road_gravel.json) |
| `roofing_cedar_shakes` | Cedar Shake Roofing | ✅ Yes | — | [roofing_cedar_shakes.json](building/roofing_cedar_shakes/roofing_cedar_shakes.json) |
| `roofing_cedar_shakes_stack_10` | Cedar Shake Roofing Stack | ✅ Yes | — | [roofing_cedar_shakes_stack_10.json](building/roofing_cedar_shakes_stack_10/roofing_cedar_shakes_stack_10.json) |
| `roofing_cedar_shakes_stack_20` | Cedar Shake Roofing Stack | ✅ Yes | — | [roofing_cedar_shakes_stack_20.json](building/roofing_cedar_shakes_stack_20/roofing_cedar_shakes_stack_20.json) |
| `roofing_clay_tile` | Terracotta Clay Tile | ✅ Yes | — | [roofing_clay_tile.json](building/roofing_clay_tile/roofing_clay_tile.json) |
| `roofing_clay_tile_stack_10` | Terracotta Clay Tile Stack | ✅ Yes | — | [roofing_clay_tile_stack_10.json](building/roofing_clay_tile_stack_10/roofing_clay_tile_stack_10.json) |
| `roofing_clay_tile_stack_20` | Terracotta Clay Tile Stack | ✅ Yes | — | [roofing_clay_tile_stack_20.json](building/roofing_clay_tile_stack_20/roofing_clay_tile_stack_20.json) |
| `roofing_seam_black` | Black Seam Roofing | ✅ Yes | — | [roofing_seam_black.json](building/roofing_seam_black/roofing_seam_black.json) |
| `roofing_seam_black_stack_10` | Black Seam Roofing Stack | ✅ Yes | — | [roofing_seam_black_stack_10.json](building/roofing_seam_black_stack_10/roofing_seam_black_stack_10.json) |
| `roofing_seam_black_stack_20` | Black Seam Roofing Stack | ✅ Yes | — | [roofing_seam_black_stack_20.json](building/roofing_seam_black_stack_20/roofing_seam_black_stack_20.json) |
| `roofing_seam_green` | Green Seam Roofing | ✅ Yes | — | [roofing_seam_green.json](building/roofing_seam_green/roofing_seam_green.json) |
| `roofing_seam_green_stack_10` | Green Seam Roofing Stack | ✅ Yes | — | [roofing_seam_green_stack_10.json](building/roofing_seam_green_stack_10/roofing_seam_green_stack_10.json) |
| `roofing_seam_green_stack_20` | Green Seam Roofing Stack | ✅ Yes | — | [roofing_seam_green_stack_20.json](building/roofing_seam_green_stack_20/roofing_seam_green_stack_20.json) |
| `roofing_seam_red` | Red Seam Roofing | ✅ Yes | — | [roofing_seam_red.json](building/roofing_seam_red/roofing_seam_red.json) |
| `roofing_seam_red_stack_10` | Red Seam Roofing Stack | ✅ Yes | — | [roofing_seam_red_stack_10.json](building/roofing_seam_red_stack_10/roofing_seam_red_stack_10.json) |
| `roofing_seam_red_stack_20` | Red Seam Roofing Stack | ✅ Yes | — | [roofing_seam_red_stack_20.json](building/roofing_seam_red_stack_20/roofing_seam_red_stack_20.json) |
| `roofing_shingles_brown` | Brown Asphalt Shingles | ✅ Yes | — | [roofing_shingles_brown.json](building/roofing_shingles_brown/roofing_shingles_brown.json) |
| `roofing_shingles_brown_stack_10` | Brown Asphalt Shingles Stack | ✅ Yes | — | [roofing_shingles_brown_stack_10.json](building/roofing_shingles_brown_stack_10/roofing_shingles_brown_stack_10.json) |
| `roofing_shingles_brown_stack_20` | Brown Asphalt Shingles Stack | ✅ Yes | — | [roofing_shingles_brown_stack_20.json](building/roofing_shingles_brown_stack_20/roofing_shingles_brown_stack_20.json) |
| `roofing_shingles_bundle` | Asphalt Shingles Bundle | ✅ Yes | — | [roofing_shingles_bundle.json](building/roofing_shingles_bundle/roofing_shingles_bundle.json) |
| `roofing_shingles_green` | Green Shingles | ✅ Yes | — | [roofing_shingles_green.json](building/roofing_shingles_green/roofing_shingles_green.json) |
| `roofing_shingles_green_stack_10` | Green Shingles Stack | ✅ Yes | — | [roofing_shingles_green_stack_10.json](building/roofing_shingles_green_stack_10/roofing_shingles_green_stack_10.json) |
| `roofing_shingles_green_stack_20` | Green Shingles Stack | ✅ Yes | — | [roofing_shingles_green_stack_20.json](building/roofing_shingles_green_stack_20/roofing_shingles_green_stack_20.json) |
| `roofing_shingles_red` | Red Asphalt Shingles | ✅ Yes | — | [roofing_shingles_red.json](building/roofing_shingles_red/roofing_shingles_red.json) |
| `roofing_shingles_red_stack_10` | Red Asphalt Shingles Stack | ✅ Yes | — | [roofing_shingles_red_stack_10.json](building/roofing_shingles_red_stack_10/roofing_shingles_red_stack_10.json) |
| `roofing_shingles_red_stack_20` | Red Asphalt Shingles Stack | ✅ Yes | — | [roofing_shingles_red_stack_20.json](building/roofing_shingles_red_stack_20/roofing_shingles_red_stack_20.json) |
| `roofing_shingles_weathered` | Weathered Wood Shingles | ✅ Yes | — | [roofing_shingles_weathered.json](building/roofing_shingles_weathered/roofing_shingles_weathered.json) |
| `roofing_shingles_weathered_stack_10` | Weathered Wood Shingles Stack | ✅ Yes | — | [roofing_shingles_weathered_stack_10.json](building/roofing_shingles_weathered_stack_10/roofing_shingles_weathered_stack_10.json) |
| `roofing_shingles_weathered_stack_20` | Weathered Wood Shingles Stack | ✅ Yes | — | [roofing_shingles_weathered_stack_20.json](building/roofing_shingles_weathered_stack_20/roofing_shingles_weathered_stack_20.json) |
| `roofing_slate_tile` | Natural Slate Tile | ✅ Yes | — | [roofing_slate_tile.json](building/roofing_slate_tile/roofing_slate_tile.json) |
| `roofing_slate_tile_stack_10` | Natural Slate Tile Stack | ✅ Yes | — | [roofing_slate_tile_stack_10.json](building/roofing_slate_tile_stack_10/roofing_slate_tile_stack_10.json) |
| `roofing_slate_tile_stack_20` | Natural Slate Tile Stack | ✅ Yes | — | [roofing_slate_tile_stack_20.json](building/roofing_slate_tile_stack_20/roofing_slate_tile_stack_20.json) |
| `roofing_steel_corrugated` | Steel Roofing | ✅ Yes | — | [roofing_steel_corrugated.json](building/roofing_steel_corrugated/roofing_steel_corrugated.json) |
| `roofing_steel_corrugated_black` | Black Steel Roofing | ✅ Yes | — | [roofing_steel_corrugated_black.json](building/roofing_steel_corrugated_black/roofing_steel_corrugated_black.json) |
| `roofing_steel_corrugated_black_stack_10` | Black Steel Roofing Stack | ✅ Yes | — | [roofing_steel_corrugated_black_stack_10.json](building/roofing_steel_corrugated_black_stack_10/roofing_steel_corrugated_black_stack_10.json) |
| `roofing_steel_corrugated_black_stack_20` | Black Steel Roofing Stack | ✅ Yes | — | [roofing_steel_corrugated_black_stack_20.json](building/roofing_steel_corrugated_black_stack_20/roofing_steel_corrugated_black_stack_20.json) |
| `roofing_steel_corrugated_green` | Green Steel Roofing | ✅ Yes | — | [roofing_steel_corrugated_green.json](building/roofing_steel_corrugated_green/roofing_steel_corrugated_green.json) |
| `roofing_steel_corrugated_green_stack_10` | Green Steel Roofing Stack | ✅ Yes | — | [roofing_steel_corrugated_green_stack_10.json](building/roofing_steel_corrugated_green_stack_10/roofing_steel_corrugated_green_stack_10.json) |
| `roofing_steel_corrugated_green_stack_20` | Green Steel Roofing Stack | ✅ Yes | — | [roofing_steel_corrugated_green_stack_20.json](building/roofing_steel_corrugated_green_stack_20/roofing_steel_corrugated_green_stack_20.json) |
| `roofing_steel_corrugated_red` | Red Steel Roofing | ✅ Yes | — | [roofing_steel_corrugated_red.json](building/roofing_steel_corrugated_red/roofing_steel_corrugated_red.json) |
| `roofing_steel_corrugated_red_stack_10` | Red Steel Roofing Stack | ✅ Yes | — | [roofing_steel_corrugated_red_stack_10.json](building/roofing_steel_corrugated_red_stack_10/roofing_steel_corrugated_red_stack_10.json) |
| `roofing_steel_corrugated_red_stack_20` | Red Steel Roofing Stack | ✅ Yes | — | [roofing_steel_corrugated_red_stack_20.json](building/roofing_steel_corrugated_red_stack_20/roofing_steel_corrugated_red_stack_20.json) |
| `roofing_steel_corrugated_stack_10` | Steel Roofing Stack | ✅ Yes | — | [roofing_steel_corrugated_stack_10.json](building/roofing_steel_corrugated_stack_10/roofing_steel_corrugated_stack_10.json) |
| `roofing_steel_corrugated_stack_20` | Steel Roofing Stack | ✅ Yes | — | [roofing_steel_corrugated_stack_20.json](building/roofing_steel_corrugated_stack_20/roofing_steel_corrugated_stack_20.json) |
| `roofing_thatch` | Reed Thatch Bundle | ✅ Yes | — | [roofing_thatch.json](building/roofing_thatch/roofing_thatch.json) |
| `roofing_thatch_stack_10` | Reed Thatch Bundle Stack | ✅ Yes | — | [roofing_thatch_stack_10.json](building/roofing_thatch_stack_10/roofing_thatch_stack_10.json) |
| `roofing_thatch_stack_20` | Reed Thatch Bundle Stack | ✅ Yes | — | [roofing_thatch_stack_20.json](building/roofing_thatch_stack_20/roofing_thatch_stack_20.json) |
| `sheet_drywall` | Drywall Sheet | ✅ Yes | — | [sheet_drywall.json](building/sheet_drywall/sheet_drywall.json) |
| `sheet_drywall_stack_large` | Large Drywall Stack | ✅ Yes | — | [sheet_drywall_stack_large.json](building/sheet_drywall_stack_large/sheet_drywall_stack_large.json) |
| `sheet_drywall_stack_small` | Small Drywall Stack | ✅ Yes | — | [sheet_drywall_stack_small.json](building/sheet_drywall_stack_small/sheet_drywall_stack_small.json) |
| `sheet_osb` | OSB Sheet | ✅ Yes | — | [sheet_osb.json](building/sheet_osb/sheet_osb.json) |
| `sheet_osb_stack_large` | Large OSB Stack | ✅ Yes | — | [sheet_osb_stack_large.json](building/sheet_osb_stack_large/sheet_osb_stack_large.json) |
| `sheet_osb_stack_small` | Small OSB Stack | ✅ Yes | — | [sheet_osb_stack_small.json](building/sheet_osb_stack_small/sheet_osb_stack_small.json) |
| `sheet_plywood_cdx` | CDX Plywood Sheet | ✅ Yes | — | [sheet_plywood_cdx.json](building/sheet_plywood_cdx/sheet_plywood_cdx.json) |
| `sheet_plywood_cdx_stack_10` | CDX Plywood Sheet Stack | ✅ Yes | — | [sheet_plywood_cdx_stack_10.json](building/sheet_plywood_cdx_stack_10/sheet_plywood_cdx_stack_10.json) |
| `sheet_plywood_cdx_stack_20` | CDX Plywood Sheet Stack | ✅ Yes | — | [sheet_plywood_cdx_stack_20.json](building/sheet_plywood_cdx_stack_20/sheet_plywood_cdx_stack_20.json) |
| `spool_wire_barbed_4pt` | 4-Point Barbed Wire Spool | ✅ Yes | — | [spool_wire_barbed_4pt.json](building/spool_wire_barbed_4pt/spool_wire_barbed_4pt.json) |
| `spool_wire_romex_12_2` | Romex 12-2 Spool | ✅ Yes | — | [spool_wire_romex_12_2.json](building/spool_wire_romex_12_2/spool_wire_romex_12_2.json) |
| `spool_wire_woven_field` | Woven Field Fence Roll | ✅ Yes | — | [spool_wire_woven_field.json](building/spool_wire_woven_field/spool_wire_woven_field.json) |
| `valve_ball_brass` | Brass Ball Valve | ✅ Yes | — | [valve_ball_brass.json](building/valve_ball_brass/valve_ball_brass.json) |
| `valve_gate_brass` | Brass Gate Valve | ✅ Yes | — | [valve_gate_brass.json](building/valve_gate_brass/valve_gate_brass.json) |
| `wood_log` | Wood Log | ✅ Yes | — | [wood_log.json](building/wood_log/wood_log.json) |
| `wood_log_stack_10` | Wood Log (Stack of 10) | ✅ Yes | — | [wood_log_stack_10.json](building/wood_log_stack_10/wood_log_stack_10.json) |
| `wood_log_stack_20` | Wood Log (Stack of 20) | ✅ Yes | — | [wood_log_stack_20.json](building/wood_log_stack_20/wood_log_stack_20.json) |

### 📂 [Farming](farming/) (70 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `alfalfa` | Alfalfa Plant | — | — | [alfalfa.json](farming/alfalfa/alfalfa.json) |
| `barley` | Barley Plant | — | — | [barley.json](farming/barley/barley.json) |
| `beet` | Beet Plant | — | — | [beet.json](farming/beet/beet.json) |
| `broccoli` | Broccoli Plant | — | — | [broccoli.json](farming/broccoli/broccoli.json) |
| `cabbage` | Cabbage Plant | — | — | [cabbage.json](farming/cabbage/cabbage.json) |
| `canola` | Canola Plant | — | — | [canola.json](farming/canola/canola.json) |
| `cantaloupe` | Cantaloupe Plant | — | — | [cantaloupe.json](farming/cantaloupe/cantaloupe.json) |
| `carrot` | Carrot Plant | — | — | [carrot.json](farming/carrot/carrot.json) |
| `corn` | Corn Plant | — | — | [corn.json](farming/corn/corn.json) |
| `cotton` | Cotton Plant | — | — | [cotton.json](farming/cotton/cotton.json) |
| `cucumber` | Cucumber Plant | — | — | [cucumber.json](farming/cucumber/cucumber.json) |
| `flax` | Flax Plant | — | — | [flax.json](farming/flax/flax.json) |
| `garlic` | Garlic Plant | — | — | [garlic.json](farming/garlic/garlic.json) |
| `green_beans` | Green Bean Plant | — | — | [green_beans.json](farming/green_beans/green_beans.json) |
| `herb` | Herb Plant | — | — | [herb.json](farming/herb/herb.json) |
| `hops` | Hops Plant | — | — | [hops.json](farming/hops/hops.json) |
| `lettuce` | Lettuce Plant | — | — | [lettuce.json](farming/lettuce/lettuce.json) |
| `oats` | Oat Plant | — | — | [oats.json](farming/oats/oats.json) |
| `onion` | Onion Plant | — | — | [onion.json](farming/onion/onion.json) |
| `peanuts` | Peanut Plant | — | — | [peanuts.json](farming/peanuts/peanuts.json) |
| `peas` | Peas Plant | — | — | [peas.json](farming/peas/peas.json) |
| `peppers` | Pepper Plant | — | — | [peppers.json](farming/peppers/peppers.json) |
| `potato` | Potato Plant | — | — | [potato.json](farming/potato/potato.json) |
| `pumpkin` | Pumpkin Plant | — | — | [pumpkin.json](farming/pumpkin/pumpkin.json) |
| `radish` | Radish Plant | — | — | [radish.json](farming/radish/radish.json) |
| `rhubarb` | Rhubarb Plant | — | — | [rhubarb.json](farming/rhubarb/rhubarb.json) |
| `seed_alfalfa` | Alfalfa Seeds | — | — | [seed_alfalfa.json](farming/seed_alfalfa/seed_alfalfa.json) |
| `seed_barley` | Barley Seeds | — | — | [seed_barley.json](farming/seed_barley/seed_barley.json) |
| `seed_beet` | Beet Seeds | — | — | [seed_beet.json](farming/seed_beet/seed_beet.json) |
| `seed_broccoli` | Broccoli Seeds | — | — | [seed_broccoli.json](farming/seed_broccoli/seed_broccoli.json) |
| `seed_cabbage` | Cabbage Seeds | — | — | [seed_cabbage.json](farming/seed_cabbage/seed_cabbage.json) |
| `seed_canola` | Canola Seeds | — | — | [seed_canola.json](farming/seed_canola/seed_canola.json) |
| `seed_cantaloupe` | Cantaloupe Seeds | — | — | [seed_cantaloupe.json](farming/seed_cantaloupe/seed_cantaloupe.json) |
| `seed_carrot` | Carrot Seeds | ✅ Yes | — | [seed_carrot.json](farming/seed_carrot/seed_carrot.json) |
| `seed_corn` | Corn Seeds | ✅ Yes | — | [seed_corn.json](farming/seed_corn/seed_corn.json) |
| `seed_cotton` | Cotton Seeds | ✅ Yes | — | [seed_cotton.json](farming/seed_cotton/seed_cotton.json) |
| `seed_cucumber` | Cucumber Seeds | — | — | [seed_cucumber.json](farming/seed_cucumber/seed_cucumber.json) |
| `seed_flax` | Flax Seeds | — | — | [seed_flax.json](farming/seed_flax/seed_flax.json) |
| `seed_garlic` | Garlic Seeds | — | — | [seed_garlic.json](farming/seed_garlic/seed_garlic.json) |
| `seed_green_beans` | Green Bean Seeds | — | — | [seed_green_beans.json](farming/seed_green_beans/seed_green_beans.json) |
| `seed_herb` | Herb Seeds | ✅ Yes | — | [seed_herb.json](farming/seed_herb/seed_herb.json) |
| `seed_hops` | Hops Seeds | — | — | [seed_hops.json](farming/seed_hops/seed_hops.json) |
| `seed_lettuce` | Lettuce Seeds | — | — | [seed_lettuce.json](farming/seed_lettuce/seed_lettuce.json) |
| `seed_oats` | Oat Seeds | — | — | [seed_oats.json](farming/seed_oats/seed_oats.json) |
| `seed_onion` | Onion Seeds | — | — | [seed_onion.json](farming/seed_onion/seed_onion.json) |
| `seed_peanuts` | Peanut Seeds | — | — | [seed_peanuts.json](farming/seed_peanuts/seed_peanuts.json) |
| `seed_peas` | Pea Seeds | — | — | [seed_peas.json](farming/seed_peas/seed_peas.json) |
| `seed_peppers` | Pepper Seeds | — | — | [seed_peppers.json](farming/seed_peppers/seed_peppers.json) |
| `seed_potato` | Potato Seeds | ✅ Yes | — | [seed_potato.json](farming/seed_potato/seed_potato.json) |
| `seed_pumpkin` | Pumpkin Seeds | ✅ Yes | — | [seed_pumpkin.json](farming/seed_pumpkin/seed_pumpkin.json) |
| `seed_radish` | Radish Seeds | — | — | [seed_radish.json](farming/seed_radish/seed_radish.json) |
| `seed_rhubarb` | Rhubarb Seeds | — | — | [seed_rhubarb.json](farming/seed_rhubarb/seed_rhubarb.json) |
| `seed_soybeans` | Soybean Seeds | — | — | [seed_soybeans.json](farming/seed_soybeans/seed_soybeans.json) |
| `seed_spinach` | Spinach Seeds | — | — | [seed_spinach.json](farming/seed_spinach/seed_spinach.json) |
| `seed_strawberry` | Strawberry Seeds | ✅ Yes | — | [seed_strawberry.json](farming/seed_strawberry/seed_strawberry.json) |
| `seed_sunflower` | Sunflower Seeds | ✅ Yes | — | [seed_sunflower.json](farming/seed_sunflower/seed_sunflower.json) |
| `seed_tobacco` | Tobacco Seeds | — | — | [seed_tobacco.json](farming/seed_tobacco/seed_tobacco.json) |
| `seed_tomato` | Tomato Seeds | ✅ Yes | — | [seed_tomato.json](farming/seed_tomato/seed_tomato.json) |
| `seed_watermelon` | Watermelon Seeds | — | — | [seed_watermelon.json](farming/seed_watermelon/seed_watermelon.json) |
| `seed_wheat` | Wheat Seeds | ✅ Yes | — | [seed_wheat.json](farming/seed_wheat/seed_wheat.json) |
| `seed_zucchini` | Zucchini Seeds | — | — | [seed_zucchini.json](farming/seed_zucchini/seed_zucchini.json) |
| `soybeans` | Soybean Plant | — | — | [soybeans.json](farming/soybeans/soybeans.json) |
| `spinach` | Spinach Plant | — | — | [spinach.json](farming/spinach/spinach.json) |
| `strawberry` | Strawberry Plant | — | — | [strawberry.json](farming/strawberry/strawberry.json) |
| `sunflower` | Sunflower Plant | — | — | [sunflower.json](farming/sunflower/sunflower.json) |
| `tobacco` | Tobacco Plant | — | — | [tobacco.json](farming/tobacco/tobacco.json) |
| `tomato` | Tomato Plant | — | — | [tomato.json](farming/tomato/tomato.json) |
| `watermelon` | Watermelon Plant | — | — | [watermelon.json](farming/watermelon/watermelon.json) |
| `wheat` | Wheat Plant | — | — | [wheat.json](farming/wheat/wheat.json) |
| `zucchini` | Zucchini Plant | — | — | [zucchini.json](farming/zucchini/zucchini.json) |

### 📂 [Ranching](ranching/) (28 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `animal_bull_holstein` | Holstein Bull | ✅ Yes | — | [animal_bull_holstein.json](ranching/animal_bull_holstein/animal_bull_holstein.json) |
| `animal_cat_calico` | Calico Cat | ✅ Yes | — | [animal_cat_calico.json](ranching/animal_cat_calico/animal_cat_calico.json) |
| `animal_dog_labrador` | Labrador Retriever | ✅ Yes | — | [animal_dog_labrador.json](ranching/animal_dog_labrador/animal_dog_labrador.json) |
| `animal_halter_lead_rope` | Halter & Lead Rope | ✅ Yes | — | [animal_halter_lead_rope.json](ranching/animal_halter_lead_rope/animal_halter_lead_rope.json) |
| `animal_pan_feed_rubber_55l` | Rubber Feed Pan (55L) | ✅ Yes | — | [animal_pan_feed_rubber_55l.json](ranching/animal_pan_feed_rubber_55l/animal_pan_feed_rubber_55l.json) |
| `animal_salt_lick_mineral_23kg` | Mineral Salt Lick | ✅ Yes | — | [animal_salt_lick_mineral_23kg.json](ranching/animal_salt_lick_mineral_23kg/animal_salt_lick_mineral_23kg.json) |
| `barred_chicken` | Barred Chicken | — | — | [barred_chicken.json](ranching/barred_chicken/barred_chicken.json) |
| `black_goat` | Black Goat | — | — | [black_goat.json](ranching/black_goat/black_goat.json) |
| `black_white_billy_goat` | Black White Billy Goat | — | — | [black_white_billy_goat.json](ranching/black_white_billy_goat/black_white_billy_goat.json) |
| `black_white_goat` | Black White Goat | — | — | [black_white_goat.json](ranching/black_white_goat/black_white_goat.json) |
| `brown_goat` | Brown Goat | — | — | [brown_goat.json](ranching/brown_goat/brown_goat.json) |
| `duroc_pig` | Duroc Pig | — | — | [duroc_pig.json](ranching/duroc_pig/duroc_pig.json) |
| `hampshire_pig` | Hampshire Pig | — | — | [hampshire_pig.json](ranching/hampshire_pig/hampshire_pig.json) |
| `highland_cow` | Highland Cow | — | — | [highland_cow.json](ranching/highland_cow/highland_cow.json) |
| `holstein_cow` | Holstein Cow | — | — | [holstein_cow.json](ranching/holstein_cow/holstein_cow.json) |
| `jersey_cow` | Jersey Cow | — | — | [jersey_cow.json](ranching/jersey_cow/jersey_cow.json) |
| `mat_bale_silage_round` | Round Silage Bale | ✅ Yes | — | [mat_bale_silage_round.json](ranching/mat_bale_silage_round/mat_bale_silage_round.json) |
| `pink_pig` | Pink Pig | — | — | [pink_pig.json](ranching/pink_pig/pink_pig.json) |
| `quarter_horse` | Quarter Horse | — | — | [quarter_horse.json](ranching/quarter_horse/quarter_horse.json) |
| `red_chicken` | Red Chicken | — | — | [red_chicken.json](ranching/red_chicken/red_chicken.json) |
| `suffolk_sheep` | Suffolk Sheep | — | — | [suffolk_sheep.json](ranching/suffolk_sheep/suffolk_sheep.json) |
| `tan_sheep` | Tan Sheep | — | — | [tan_sheep.json](ranching/tan_sheep/tan_sheep.json) |
| `trough_stock_tank_380l` | 380L Stock Tank | ✅ Yes | — | [trough_stock_tank_380l.json](ranching/trough_stock_tank_380l/trough_stock_tank_380l.json) |
| `trough_stock_tank_380l_empty` | 380 Liter Stock Tank - Empty | ✅ Yes | — | [trough_stock_tank_380l_empty.json](ranching/trough_stock_tank_380l_empty/trough_stock_tank_380l_empty.json) |
| `welsummer_rooter` | Welsummer Rooter | — | — | [welsummer_rooter.json](ranching/welsummer_rooter/welsummer_rooter.json) |
| `white_chicken` | White Chicken | — | — | [white_chicken.json](ranching/white_chicken/white_chicken.json) |
| `white_goat` | White Goat | — | — | [white_goat.json](ranching/white_goat/white_goat.json) |
| `white_sheep` | White Sheep | — | — | [white_sheep.json](ranching/white_sheep/white_sheep.json) |

### 📂 [Logging](logging/) (43 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `apple` | Apple Tree | — | — | [apple.json](logging/apple/apple.json) |
| `apricot` | Apricot | — | — | [apricot.json](logging/apricot/apricot.json) |
| `birch` | Birch Tree | — | — | [birch.json](logging/birch/birch.json) |
| `bush_blueberry` | Blueberry Bush | — | — | [bush_blueberry.json](logging/bush_blueberry/bush_blueberry.json) |
| `bush_elderberry` | Elderberry Bush | — | — | [bush_elderberry.json](logging/bush_elderberry/bush_elderberry.json) |
| `bush_haskap` | Haskap Bush | — | — | [bush_haskap.json](logging/bush_haskap/bush_haskap.json) |
| `bush_huckleberry` | Huckleberry Bush | — | — | [bush_huckleberry.json](logging/bush_huckleberry/bush_huckleberry.json) |
| `bush_raspberry` | Raspberry Bush | — | — | [bush_raspberry.json](logging/bush_raspberry/bush_raspberry.json) |
| `cherry` | Cherry | — | — | [cherry.json](logging/cherry/cherry.json) |
| `fig` | Fig | — | — | [fig.json](logging/fig/fig.json) |
| `grape` | Grape | — | — | [grape.json](logging/grape/grape.json) |
| `hazelnut` | Hazelnut | — | — | [hazelnut.json](logging/hazelnut/hazelnut.json) |
| `lemon` | Lemon | — | — | [lemon.json](logging/lemon/lemon.json) |
| `maple` | Maple Tree | — | — | [maple.json](logging/maple/maple.json) |
| `oak` | Oak Tree | — | — | [oak.json](logging/oak/oak.json) |
| `orange` | Orange | — | — | [orange.json](logging/orange/orange.json) |
| `peach` | Peach | — | — | [peach.json](logging/peach/peach.json) |
| `pear` | Pear | — | — | [pear.json](logging/pear/pear.json) |
| `pecan` | Pecan | — | — | [pecan.json](logging/pecan/pecan.json) |
| `pine` | Pine Tree | — | — | [pine.json](logging/pine/pine.json) |
| `plantable_birch_sapling` | Plantable Birch Sapling | ✅ Yes | — | [plantable_birch_sapling.json](logging/plantable_birch_sapling/plantable_birch_sapling.json) |
| `plantable_maple_sapling` | Plantable Maple Sapling | ✅ Yes | — | [plantable_maple_sapling.json](logging/plantable_maple_sapling/plantable_maple_sapling.json) |
| `plantable_oak_sapling` | Plantable Oak Sapling | ✅ Yes | — | [plantable_oak_sapling.json](logging/plantable_oak_sapling/plantable_oak_sapling.json) |
| `plantable_pine_sapling` | Plantable Pine Sapling | ✅ Yes | — | [plantable_pine_sapling.json](logging/plantable_pine_sapling/plantable_pine_sapling.json) |
| `plantable_poplar_sapling` | Plantable Poplar Sapling | ✅ Yes | — | [plantable_poplar_sapling.json](logging/plantable_poplar_sapling/plantable_poplar_sapling.json) |
| `plantable_sapling_apple` | Plantable Sapling Apple | ✅ Yes | — | [plantable_sapling_apple.json](logging/plantable_sapling_apple/plantable_sapling_apple.json) |
| `plantable_sapling_apricot` | Plantable Sapling Apricot | — | — | [plantable_sapling_apricot.json](logging/plantable_sapling_apricot/plantable_sapling_apricot.json) |
| `plantable_sapling_cherry` | Plantable Sapling Cherry | — | — | [plantable_sapling_cherry.json](logging/plantable_sapling_cherry/plantable_sapling_cherry.json) |
| `plantable_sapling_fig` | Plantable Sapling Fig | — | — | [plantable_sapling_fig.json](logging/plantable_sapling_fig/plantable_sapling_fig.json) |
| `plantable_sapling_grape` | Plantable Grapevine | — | — | [plantable_sapling_grape.json](logging/plantable_sapling_grape/plantable_sapling_grape.json) |
| `plantable_sapling_hazelnut` | Plantable Sapling Hazelnut | — | — | [plantable_sapling_hazelnut.json](logging/plantable_sapling_hazelnut/plantable_sapling_hazelnut.json) |
| `plantable_sapling_lemon` | Plantable Sapling Lemon | ✅ Yes | — | [plantable_sapling_lemon.json](logging/plantable_sapling_lemon/plantable_sapling_lemon.json) |
| `plantable_sapling_orange` | Plantable Sapling Orange | ✅ Yes | — | [plantable_sapling_orange.json](logging/plantable_sapling_orange/plantable_sapling_orange.json) |
| `plantable_sapling_peach` | Plantable Sapling Peach | — | — | [plantable_sapling_peach.json](logging/plantable_sapling_peach/plantable_sapling_peach.json) |
| `plantable_sapling_pear` | Plantable Sapling Pear | — | — | [plantable_sapling_pear.json](logging/plantable_sapling_pear/plantable_sapling_pear.json) |
| `plantable_sapling_pecan` | Plantable Sapling Pecan | — | — | [plantable_sapling_pecan.json](logging/plantable_sapling_pecan/plantable_sapling_pecan.json) |
| `plantable_sapling_plum` | Plantable Sapling Plum | — | — | [plantable_sapling_plum.json](logging/plantable_sapling_plum/plantable_sapling_plum.json) |
| `plantable_sapling_walnut` | Plantable Sapling Walnut | — | — | [plantable_sapling_walnut.json](logging/plantable_sapling_walnut/plantable_sapling_walnut.json) |
| `plantable_willow_sapling` | Plantable Willow Sapling | ✅ Yes | — | [plantable_willow_sapling.json](logging/plantable_willow_sapling/plantable_willow_sapling.json) |
| `plum` | Plum | — | — | [plum.json](logging/plum/plum.json) |
| `poplar` | Poplar Tree | — | — | [poplar.json](logging/poplar/poplar.json) |
| `walnut` | Walnut | — | — | [walnut.json](logging/walnut/walnut.json) |
| `willow` | Willow Tree | — | — | [willow.json](logging/willow/willow.json) |

### 📂 [Fishing](fishing/) (19 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `animal_fish_bass` | Largemouth Bass | ✅ Yes | — | [animal_fish_bass.json](fishing/animal_fish_bass/animal_fish_bass.json) |
| `animal_fish_catfish` | Channel Catfish | ✅ Yes | — | [animal_fish_catfish.json](fishing/animal_fish_catfish/animal_fish_catfish.json) |
| `animal_fish_crappie` | Black Crappie | ✅ Yes | — | [animal_fish_crappie.json](fishing/animal_fish_crappie/animal_fish_crappie.json) |
| `animal_fish_salmon` | Sockeye Salmon | ✅ Yes | — | [animal_fish_salmon.json](fishing/animal_fish_salmon/animal_fish_salmon.json) |
| `animal_fish_trout` | Rainbow Trout | ✅ Yes | — | [animal_fish_trout.json](fishing/animal_fish_trout/animal_fish_trout.json) |
| `animal_fish_walleye` | Walleye | ✅ Yes | — | [animal_fish_walleye.json](fishing/animal_fish_walleye/animal_fish_walleye.json) |
| `fishing_bait` | Live Fishing Bait | ✅ Yes | — | [fishing_bait.json](fishing/fishing_bait/fishing_bait.json) |
| `fishing_basket_wire` | Wire Fish Basket | ✅ Yes | — | [fishing_basket_wire.json](fishing/fishing_basket_wire/fishing_basket_wire.json) |
| `fishing_bobbers_clip_pack` | Clip-On Bobbers Pack | ✅ Yes | — | [fishing_bobbers_clip_pack.json](fishing/fishing_bobbers_clip_pack/fishing_bobbers_clip_pack.json) |
| `fishing_box_lures_organizer` | Lures Organizer Box | ✅ Yes | — | [fishing_box_lures_organizer.json](fishing/fishing_box_lures_organizer/fishing_box_lures_organizer.json) |
| `fishing_box_tackle_3tray` | 3-Tray Tackle Box | ✅ Yes | — | [fishing_box_tackle_3tray.json](fishing/fishing_box_tackle_3tray/fishing_box_tackle_3tray.json) |
| `fishing_line_spool` | Braided Fishing Line Spool | ✅ Yes | — | [fishing_line_spool.json](fishing/fishing_line_spool/fishing_line_spool.json) |
| `fishing_lure` | Fishing Lure | — | — | [fishing_lure.json](fishing/fishing_lure/fishing_lure.json) |
| `fishing_net_landing_telescopic` | Telescopic Landing Net | ✅ Yes | — | [fishing_net_landing_telescopic.json](fishing/fishing_net_landing_telescopic/fishing_net_landing_telescopic.json) |
| `fishing_rod` | Fishing Rod | — | — | [fishing_rod.json](fishing/fishing_rod/fishing_rod.json) |
| `fishing_rod_fly` | Fly Fishing Rod | ✅ Yes | — | [fishing_rod_fly.json](fishing/fishing_rod_fly/fishing_rod_fly.json) |
| `fishing_rod_heavy_trolling` | Heavy Trolling Fishing Rod | ✅ Yes | — | [fishing_rod_heavy_trolling.json](fishing/fishing_rod_heavy_trolling/fishing_rod_heavy_trolling.json) |
| `fishing_rod_spincast_combo` | Spincast Rod & Reel Combo | ✅ Yes | — | [fishing_rod_spincast_combo.json](fishing/fishing_rod_spincast_combo/fishing_rod_spincast_combo.json) |
| `fishing_sinkers_lead` | Split Shot Lead Sinkers | ✅ Yes | — | [fishing_sinkers_lead.json](fishing/fishing_sinkers_lead/fishing_sinkers_lead.json) |

### 📂 [Tools](tools/) (69 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `tool_angle_grinder_corded` | Corded Angle Grinder | — | — | [tool_angle_grinder_corded.json](tools/tool_angle_grinder_corded/tool_angle_grinder_corded.json) |
| `tool_angle_grinder_cordless` | Cordless Angle Grinder | — | — | [tool_angle_grinder_cordless.json](tools/tool_angle_grinder_cordless/tool_angle_grinder_cordless.json) |
| `tool_animal_paddle_sorting_cattle` | Cattle Sorting Paddle | ✅ Yes | — | [tool_animal_paddle_sorting_cattle.json](tools/tool_animal_paddle_sorting_cattle/tool_animal_paddle_sorting_cattle.json) |
| `tool_anvil_stump` | Tool Anvil Stump | ✅ Yes | — | [tool_anvil_stump.json](tools/tool_anvil_stump/tool_anvil_stump.json) |
| `tool_axe` | Axe | ✅ Yes | — | [tool_axe.json](tools/tool_axe/tool_axe.json) |
| `tool_axe_felling` | Felling Axe | ✅ Yes | — | [tool_axe_felling.json](tools/tool_axe_felling/tool_axe_felling.json) |
| `tool_basket_large` | Large Basket | — | — | [tool_basket_large.json](tools/tool_basket_large/tool_basket_large.json) |
| `tool_basket_medium` | Medium Basket | — | — | [tool_basket_medium.json](tools/tool_basket_medium/tool_basket_medium.json) |
| `tool_basket_small` | Small Basket | — | — | [tool_basket_small.json](tools/tool_basket_small/tool_basket_small.json) |
| `tool_bucket_empty` | Empty Utility Bucket | ✅ Yes | — | [tool_bucket_empty.json](tools/tool_bucket_empty/tool_bucket_empty.json) |
| `tool_cant_hook_peavey` | Cant Hook Peavey | ✅ Yes | — | [tool_cant_hook_peavey.json](tools/tool_cant_hook_peavey/tool_cant_hook_peavey.json) |
| `tool_cement_mixer` | Cement Mixer | ✅ Yes | — | [tool_cement_mixer.json](tools/tool_cement_mixer/tool_cement_mixer.json) |
| `tool_chain_choker_logging` | Logging Choker Chain | ✅ Yes | — | [tool_chain_choker_logging.json](tools/tool_chain_choker_logging/tool_chain_choker_logging.json) |
| `tool_chainsaw_gas_16` | 16" Gas Chainsaw | ✅ Yes | — | [tool_chainsaw_gas_16.json](tools/tool_chainsaw_gas_16/tool_chainsaw_gas_16.json) |
| `tool_chainsaw_gas_20` | 20" Gas Chainsaw | ✅ Yes | — | [tool_chainsaw_gas_20.json](tools/tool_chainsaw_gas_20/tool_chainsaw_gas_20.json) |
| `tool_circular_saw_corded` | Corded Circular Saw | — | — | [tool_circular_saw_corded.json](tools/tool_circular_saw_corded/tool_circular_saw_corded.json) |
| `tool_circular_saw_cordless` | Cordless Circular Saw | — | — | [tool_circular_saw_cordless.json](tools/tool_circular_saw_cordless/tool_circular_saw_cordless.json) |
| `tool_cord_shore_power_50a` | 50A Shore Power Cord | ✅ Yes | — | [tool_cord_shore_power_50a.json](tools/tool_cord_shore_power_50a/tool_cord_shore_power_50a.json) |
| `tool_cordless_chainsaw_16` | 16" Cordless Chainsaw | ✅ Yes | — | [tool_cordless_chainsaw_16.json](tools/tool_cordless_chainsaw_16/tool_cordless_chainsaw_16.json) |
| `tool_drill_corded` | Corded Power Drill | — | — | [tool_drill_corded.json](tools/tool_drill_corded/tool_drill_corded.json) |
| `tool_drill_cordless_basic` | Basic Cordless Drill | — | — | [tool_drill_cordless_basic.json](tools/tool_drill_cordless_basic/tool_drill_cordless_basic.json) |
| `tool_drill_cordless_pro` | Pro Cordless Drill | — | — | [tool_drill_cordless_pro.json](tools/tool_drill_cordless_pro/tool_drill_cordless_pro.json) |
| `tool_fruit_basket` | Fruit Basket | — | — | [tool_fruit_basket.json](tools/tool_fruit_basket/tool_fruit_basket.json) |
| `tool_hammer` | Hammer | ✅ Yes | — | [tool_hammer.json](tools/tool_hammer/tool_hammer.json) |
| `tool_hammer_claw` | Claw Hammer | ✅ Yes | — | [tool_hammer_claw.json](tools/tool_hammer_claw/tool_hammer_claw.json) |
| `tool_hammer_club` | Club Hammer | ✅ Yes | — | [tool_hammer_club.json](tools/tool_hammer_club/tool_hammer_club.json) |
| `tool_harvest_sack_large` | Large Harvest Sack | ✅ Yes | — | [tool_harvest_sack_large.json](tools/tool_harvest_sack_large/tool_harvest_sack_large.json) |
| `tool_hatchet_camp` | Camp Hatchet | ✅ Yes | — | [tool_hatchet_camp.json](tools/tool_hatchet_camp/tool_hatchet_camp.json) |
| `tool_helmet_logging_safety` | Logging Safety Helmet | ✅ Yes | — | [tool_helmet_logging_safety.json](tools/tool_helmet_logging_safety/tool_helmet_logging_safety.json) |
| `tool_hoe` | Hoe | ✅ Yes | — | [tool_hoe.json](tools/tool_hoe/tool_hoe.json) |
| `tool_hose_garden_reel` | Garden Hose & Reel | ✅ Yes | — | [tool_hose_garden_reel.json](tools/tool_hose_garden_reel/tool_hose_garden_reel.json) |
| `tool_impact_driver_cordless` | Cordless Impact Driver | — | — | [tool_impact_driver_cordless.json](tools/tool_impact_driver_cordless/tool_impact_driver_cordless.json) |
| `tool_kit_chainsaw_file_pouch` | Chainsaw File Kit | ✅ Yes | — | [tool_kit_chainsaw_file_pouch.json](tools/tool_kit_chainsaw_file_pouch/tool_kit_chainsaw_file_pouch.json) |
| `tool_lighter` | Lighter | ✅ Yes | — | [tool_lighter.json](tools/tool_lighter/tool_lighter.json) |
| `tool_loppers_heavy` | Heavy Loppers | ✅ Yes | — | [tool_loppers_heavy.json](tools/tool_loppers_heavy/tool_loppers_heavy.json) |
| `tool_maul_splitting` | Splitting Maul | ✅ Yes | — | [tool_maul_splitting.json](tools/tool_maul_splitting/tool_maul_splitting.json) |
| `tool_miter_saw` | Miter Saw | — | — | [tool_miter_saw.json](tools/tool_miter_saw/tool_miter_saw.json) |
| `tool_pail_milk_stainless` | Tool Pail Milk Stainless | ✅ Yes | — | [tool_pail_milk_stainless.json](tools/tool_pail_milk_stainless/tool_pail_milk_stainless.json) |
| `tool_pickaxe` | Pickaxe | ✅ Yes | — | [tool_pickaxe.json](tools/tool_pickaxe/tool_pickaxe.json) |
| `tool_plastic_wheelbarrow` | Plastic Wheelbarrow | ✅ Yes | — | [tool_plastic_wheelbarrow.json](tools/tool_plastic_wheelbarrow/tool_plastic_wheelbarrow.json) |
| `tool_pump_sprayer` | Pump Sprayer | ✅ Yes | — | [tool_pump_sprayer.json](tools/tool_pump_sprayer/tool_pump_sprayer.json) |
| `tool_saw_hand` | Hand Saw | ✅ Yes | — | [tool_saw_hand.json](tools/tool_saw_hand/tool_saw_hand.json) |
| `tool_sawhorse_metal` | Metal Sawhorse | ✅ Yes | — | [tool_sawhorse_metal.json](tools/tool_sawhorse_metal/tool_sawhorse_metal.json) |
| `tool_sawhorse_plastic` | Plastic Sawhorse | ✅ Yes | — | [tool_sawhorse_plastic.json](tools/tool_sawhorse_plastic/tool_sawhorse_plastic.json) |
| `tool_sawhorse_wood` | Wooden Sawhorse | ✅ Yes | — | [tool_sawhorse_wood.json](tools/tool_sawhorse_wood/tool_sawhorse_wood.json) |
| `tool_seedbag` | Seed Bag | ✅ Yes | — | [tool_seedbag.json](tools/tool_seedbag/tool_seedbag.json) |
| `tool_shears_pruning` | Pruning Shears | ✅ Yes | — | [tool_shears_pruning.json](tools/tool_shears_pruning/tool_shears_pruning.json) |
| `tool_shears_sheepwool` | Tool Shears Sheepwool | ✅ Yes | — | [tool_shears_sheepwool.json](tools/tool_shears_sheepwool/tool_shears_sheepwool.json) |
| `tool_shovel` | Shovel | ✅ Yes | — | [tool_shovel.json](tools/tool_shovel/tool_shovel.json) |
| `tool_shovel_round_point` | Round-Point Shovel | ✅ Yes | — | [tool_shovel_round_point.json](tools/tool_shovel_round_point/tool_shovel_round_point.json) |
| `tool_shovel_scoop_flat` | Grain Scoop Shovel | ✅ Yes | — | [tool_shovel_scoop_flat.json](tools/tool_shovel_scoop_flat/tool_shovel_scoop_flat.json) |
| `tool_shovel_trenching` | Trenching Shovel | ✅ Yes | — | [tool_shovel_trenching.json](tools/tool_shovel_trenching/tool_shovel_trenching.json) |
| `tool_sickle` | Sickle | ✅ Yes | — | [tool_sickle.json](tools/tool_sickle/tool_sickle.json) |
| `tool_sickle_grass` | Grass Sickle | ✅ Yes | — | [tool_sickle_grass.json](tools/tool_sickle_grass/tool_sickle_grass.json) |
| `tool_steel_wheelbarrow` | Steel Wheelbarrow | ✅ Yes | — | [tool_steel_wheelbarrow.json](tools/tool_steel_wheelbarrow/tool_steel_wheelbarrow.json) |
| `tool_table_saw` | Table Saw | — | — | [tool_table_saw.json](tools/tool_table_saw/tool_table_saw.json) |
| `tool_tap` | Tree Tap & Spile | ✅ Yes | — | [tool_tap.json](tools/tool_tap/tool_tap.json) |
| `tool_tongs_skidding_logging` | Skidding Tongs | ✅ Yes | — | [tool_tongs_skidding_logging.json](tools/tool_tongs_skidding_logging/tool_tongs_skidding_logging.json) |
| `tool_toolbox_large` | Large Tool Chest | ✅ Yes | — | [tool_toolbox_large.json](tools/tool_toolbox_large/tool_toolbox_large.json) |
| `tool_toolbox_medium` | Medium Toolbox | ✅ Yes | — | [tool_toolbox_medium.json](tools/tool_toolbox_medium/tool_toolbox_medium.json) |
| `tool_toolbox_small` | Small Toolbox | ✅ Yes | — | [tool_toolbox_small.json](tools/tool_toolbox_small/tool_toolbox_small.json) |
| `tool_trowel_hand` | Hand Trowel | ✅ Yes | — | [tool_trowel_hand.json](tools/tool_trowel_hand/tool_trowel_hand.json) |
| `tool_walking_plow_own` | Walking Plow | ✅ Yes | — | [tool_walking_plow_own.json](tools/tool_walking_plow_own/tool_walking_plow_own.json) |
| `tool_wedge_felling_abs_pack` | Felling Wedges Pack | ✅ Yes | — | [tool_wedge_felling_abs_pack.json](tools/tool_wedge_felling_abs_pack/tool_wedge_felling_abs_pack.json) |
| `tool_wedge_splitting_diamond` | Diamond Splitting Wedge | ✅ Yes | — | [tool_wedge_splitting_diamond.json](tools/tool_wedge_splitting_diamond/tool_wedge_splitting_diamond.json) |
| `tool_wheelbarrow` | Wheelbarrow | ✅ Yes | — | [tool_wheelbarrow.json](tools/tool_wheelbarrow/tool_wheelbarrow.json) |
| `tool_wire_cutters` | Wire Cutters | ✅ Yes | — | [tool_wire_cutters.json](tools/tool_wire_cutters/tool_wire_cutters.json) |
| `tool_wrench_adjustable` | Adjustable Wrench | ✅ Yes | — | [tool_wrench_adjustable.json](tools/tool_wrench_adjustable/tool_wrench_adjustable.json) |
| `tool_wrench_pipe` | Pipe Wrench | ✅ Yes | — | [tool_wrench_pipe.json](tools/tool_wrench_pipe/tool_wrench_pipe.json) |

### 📂 [Electricity](electricity/) (65 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `electricity_battery_12v_agm_1200wh` | 12V AGM 1200Wh Battery | ✅ Yes | — | [electricity_battery_12v_agm_1200wh.json](electricity/electricity_battery_12v_agm_1200wh/electricity_battery_12v_agm_1200wh.json) |
| `electricity_battery_12v_lifepo4_1200wh` | 12V LiFePO4 1200Wh Battery | ✅ Yes | — | [electricity_battery_12v_lifepo4_1200wh.json](electricity/electricity_battery_12v_lifepo4_1200wh/electricity_battery_12v_lifepo4_1200wh.json) |
| `electricity_battery_12v_nmc_1200wh` | 12V NMC 1200Wh Battery | ✅ Yes | — | [electricity_battery_12v_nmc_1200wh.json](electricity/electricity_battery_12v_nmc_1200wh/electricity_battery_12v_nmc_1200wh.json) |
| `electricity_battery_rack_agm_48v` | 48V AGM Rack Battery | ✅ Yes | — | [electricity_battery_rack_agm_48v.json](electricity/electricity_battery_rack_agm_48v/electricity_battery_rack_agm_48v.json) |
| `electricity_battery_rack_empty` | Battery Rack | ✅ Yes | — | [electricity_battery_rack_empty.json](electricity/electricity_battery_rack_empty/electricity_battery_rack_empty.json) |
| `electricity_battery_rack_lifepo4_48v` | 48V LiFePO4 Rack Battery | ✅ Yes | — | [electricity_battery_rack_lifepo4_48v.json](electricity/electricity_battery_rack_lifepo4_48v/electricity_battery_rack_lifepo4_48v.json) |
| `electricity_battery_rack_nmc_48v` | 48V NMC Rack Battery | ✅ Yes | — | [electricity_battery_rack_nmc_48v.json](electricity/electricity_battery_rack_nmc_48v/electricity_battery_rack_nmc_48v.json) |
| `electricity_battery_wall_power_10kwh` | Wall Power Battery, Medium | ✅ Yes | — | [electricity_battery_wall_power_10kwh.json](electricity/electricity_battery_wall_power_10kwh/electricity_battery_wall_power_10kwh.json) |
| `electricity_battery_wall_power_20kwh` | Wall Power Battery, Large | ✅ Yes | — | [electricity_battery_wall_power_20kwh.json](electricity/electricity_battery_wall_power_20kwh/electricity_battery_wall_power_20kwh.json) |
| `electricity_battery_wall_power_5kwh` | Wall Power Battery, Small | ✅ Yes | — | [electricity_battery_wall_power_5kwh.json](electricity/electricity_battery_wall_power_5kwh/electricity_battery_wall_power_5kwh.json) |
| `electricity_breaker_box_dc_128a` | DC Breaker Box | ✅ Yes | — | [electricity_breaker_box_dc_128a.json](electricity/electricity_breaker_box_dc_128a/electricity_breaker_box_dc_128a.json) |
| `electricity_breaker_box_dc_32a` | DC Breaker Box | ✅ Yes | — | [electricity_breaker_box_dc_32a.json](electricity/electricity_breaker_box_dc_32a/electricity_breaker_box_dc_32a.json) |
| `electricity_breaker_box_dc_64a` | DC Breaker Box | ✅ Yes | — | [electricity_breaker_box_dc_64a.json](electricity/electricity_breaker_box_dc_64a/electricity_breaker_box_dc_64a.json) |
| `electricity_busbar_dc_100a` | DC Bus Bar, Small | ✅ Yes | — | [electricity_busbar_dc_100a.json](electricity/electricity_busbar_dc_100a/electricity_busbar_dc_100a.json) |
| `electricity_busbar_dc_250a` | DC Bus Bar, Medium | ✅ Yes | — | [electricity_busbar_dc_250a.json](electricity/electricity_busbar_dc_250a/electricity_busbar_dc_250a.json) |
| `electricity_busbar_dc_500a` | DC Bus Bar, Large | ✅ Yes | — | [electricity_busbar_dc_500a.json](electricity/electricity_busbar_dc_500a/electricity_busbar_dc_500a.json) |
| `electricity_controller_mppt_128a` | MPPT Charge Controller, Large | ✅ Yes | — | [electricity_controller_mppt_128a.json](electricity/electricity_controller_mppt_128a/electricity_controller_mppt_128a.json) |
| `electricity_controller_mppt_32a` | MPPT Charge Controller, Small | ✅ Yes | — | [electricity_controller_mppt_32a.json](electricity/electricity_controller_mppt_32a/electricity_controller_mppt_32a.json) |
| `electricity_controller_mppt_64a` | MPPT Charge Controller, Medium | ✅ Yes | — | [electricity_controller_mppt_64a.json](electricity/electricity_controller_mppt_64a/electricity_controller_mppt_64a.json) |
| `electricity_energizer_fence_solar` | Solar Fence Energizer | ✅ Yes | — | [electricity_energizer_fence_solar.json](electricity/electricity_energizer_fence_solar/electricity_energizer_fence_solar.json) |
| `electricity_generator` | Portable Generator | ✅ Yes | — | [electricity_generator.json](electricity/electricity_generator/electricity_generator.json) |
| `electricity_generator_lockout_box` | Generator Lockout Box | ✅ Yes | — | [electricity_generator_lockout_box.json](electricity/electricity_generator_lockout_box/electricity_generator_lockout_box.json) |
| `electricity_generator_standby_10kw` | Standby Generator | ✅ Yes | — | [electricity_generator_standby_10kw.json](electricity/electricity_generator_standby_10kw/electricity_generator_standby_10kw.json) |
| `electricity_generator_standby_14kw` | Standby Generator | ✅ Yes | — | [electricity_generator_standby_14kw.json](electricity/electricity_generator_standby_14kw/electricity_generator_standby_14kw.json) |
| `electricity_generator_standby_28kw` | Standby Generator | ✅ Yes | — | [electricity_generator_standby_28kw.json](electricity/electricity_generator_standby_28kw/electricity_generator_standby_28kw.json) |
| `electricity_inverter_hybrid_10kw` | Hybrid Inverter, Large | ✅ Yes | — | [electricity_inverter_hybrid_10kw.json](electricity/electricity_inverter_hybrid_10kw/electricity_inverter_hybrid_10kw.json) |
| `electricity_inverter_hybrid_3kw` | Hybrid Inverter, Small | ✅ Yes | — | [electricity_inverter_hybrid_3kw.json](electricity/electricity_inverter_hybrid_3kw/electricity_inverter_hybrid_3kw.json) |
| `electricity_inverter_hybrid_5kw` | Hybrid Inverter, Medium | ✅ Yes | — | [electricity_inverter_hybrid_5kw.json](electricity/electricity_inverter_hybrid_5kw/electricity_inverter_hybrid_5kw.json) |
| `electricity_panel_breaker_outdoor_100a` | Outdoor Breaker Box 100A | ✅ Yes | — | [electricity_panel_breaker_outdoor_100a.json](electricity/electricity_panel_breaker_outdoor_100a/electricity_panel_breaker_outdoor_100a.json) |
| `electricity_panel_breaker_outdoor_200a` | Outdoor Breaker Box 200A | ✅ Yes | — | [electricity_panel_breaker_outdoor_200a.json](electricity/electricity_panel_breaker_outdoor_200a/electricity_panel_breaker_outdoor_200a.json) |
| `electricity_panel_breaker_outdoor_50a` | Outdoor Breaker Box 50A | ✅ Yes | — | [electricity_panel_breaker_outdoor_50a.json](electricity/electricity_panel_breaker_outdoor_50a/electricity_panel_breaker_outdoor_50a.json) |
| `electricity_panel_breaker_subpanel` | Outdoor Breaker Subpanel | ✅ Yes | — | [electricity_panel_breaker_subpanel.json](electricity/electricity_panel_breaker_subpanel/electricity_panel_breaker_subpanel.json) |
| `electricity_panel_well_sub` | Well Pump Sub Panel | ✅ Yes | — | [electricity_panel_well_sub.json](electricity/electricity_panel_well_sub/electricity_panel_well_sub.json) |
| `electricity_power_pole_metal` | Power Pole Metal | ✅ Yes | — | [electricity_power_pole_metal.json](electricity/electricity_power_pole_metal/electricity_power_pole_metal.json) |
| `electricity_power_pole_wood` | Power Pole Wood | ✅ Yes | — | [electricity_power_pole_wood.json](electricity/electricity_power_pole_wood/electricity_power_pole_wood.json) |
| `electricity_powerpole_wood` | Electric Powerpole Wood | ✅ Yes | — | [electricity_powerpole_wood.json](electricity/electricity_powerpole_wood/electricity_powerpole_wood.json) |
| `electricity_solar_mount_100w_ground` | 100W Solar Ground Mount | ✅ Yes | — | [electricity_solar_mount_100w_ground.json](electricity/electricity_solar_mount_100w_ground/electricity_solar_mount_100w_ground.json) |
| `electricity_solar_mount_100w_roof` | 100W Solar Roof Mount | ✅ Yes | — | [electricity_solar_mount_100w_roof.json](electricity/electricity_solar_mount_100w_roof/electricity_solar_mount_100w_roof.json) |
| `electricity_solar_mount_200w_ground` | 200W Solar Ground Mount | ✅ Yes | — | [electricity_solar_mount_200w_ground.json](electricity/electricity_solar_mount_200w_ground/electricity_solar_mount_200w_ground.json) |
| `electricity_solar_mount_200w_roof` | 200W Solar Roof Mount | ✅ Yes | — | [electricity_solar_mount_200w_roof.json](electricity/electricity_solar_mount_200w_roof/electricity_solar_mount_200w_roof.json) |
| `electricity_solar_mount_400w_ground` | 400W Solar Ground Mount | ✅ Yes | — | [electricity_solar_mount_400w_ground.json](electricity/electricity_solar_mount_400w_ground/electricity_solar_mount_400w_ground.json) |
| `electricity_solar_mount_400w_roof` | 400W Solar Roof Mount | ✅ Yes | — | [electricity_solar_mount_400w_roof.json](electricity/electricity_solar_mount_400w_roof/electricity_solar_mount_400w_roof.json) |
| `electricity_solar_panel_100w_rigid` | Rigid Solar Panel | ✅ Yes | — | [electricity_solar_panel_100w_rigid.json](electricity/electricity_solar_panel_100w_rigid/electricity_solar_panel_100w_rigid.json) |
| `electricity_solar_panel_100w_rigid_stack_4` | Rigid Solar Panel Stack | ✅ Yes | — | [electricity_solar_panel_100w_rigid_stack_4.json](electricity/electricity_solar_panel_100w_rigid_stack_4/electricity_solar_panel_100w_rigid_stack_4.json) |
| `electricity_solar_panel_100w_rigid_stack_8` | Rigid Solar Panel Stack | ✅ Yes | — | [electricity_solar_panel_100w_rigid_stack_8.json](electricity/electricity_solar_panel_100w_rigid_stack_8/electricity_solar_panel_100w_rigid_stack_8.json) |
| `electricity_solar_panel_200w` | Solar Panel | ✅ Yes | — | [electricity_solar_panel_200w.json](electricity/electricity_solar_panel_200w/electricity_solar_panel_200w.json) |
| `electricity_solar_panel_200w_stack_4` | Solar Panel Stack | ✅ Yes | — | [electricity_solar_panel_200w_stack_4.json](electricity/electricity_solar_panel_200w_stack_4/electricity_solar_panel_200w_stack_4.json) |
| `electricity_solar_panel_200w_stack_8` | Solar Panel Stack | ✅ Yes | — | [electricity_solar_panel_200w_stack_8.json](electricity/electricity_solar_panel_200w_stack_8/electricity_solar_panel_200w_stack_8.json) |
| `electricity_solar_panel_400w_commercial` | Commercial Solar Panel | ✅ Yes | — | [electricity_solar_panel_400w_commercial.json](electricity/electricity_solar_panel_400w_commercial/electricity_solar_panel_400w_commercial.json) |
| `electricity_solar_panel_400w_commercial_stack_4` | Commercial Solar Panel Stack | ✅ Yes | — | [electricity_solar_panel_400w_commercial_stack_4.json](electricity/electricity_solar_panel_400w_commercial_stack_4/electricity_solar_panel_400w_commercial_stack_4.json) |
| `electricity_solar_panel_400w_commercial_stack_8` | Commercial Solar Panel Stack | ✅ Yes | — | [electricity_solar_panel_400w_commercial_stack_8.json](electricity/electricity_solar_panel_400w_commercial_stack_8/electricity_solar_panel_400w_commercial_stack_8.json) |
| `electricity_switch_disconnect_safety` | Safety Disconnect Switch | ✅ Yes | — | [electricity_switch_disconnect_safety.json](electricity/electricity_switch_disconnect_safety/electricity_switch_disconnect_safety.json) |
| `electricity_turbine_wind_3kw` | Wind Turbine | ✅ Yes | — | [electricity_turbine_wind_3kw.json](electricity/electricity_turbine_wind_3kw/electricity_turbine_wind_3kw.json) |
| `electricity_turbine_wind_400w` | Wind Turbine | ✅ Yes | — | [electricity_turbine_wind_400w.json](electricity/electricity_turbine_wind_400w/electricity_turbine_wind_400w.json) |
| `electricity_wall_entry_wire` | Wall Wire Entry | ✅ Yes | — | [electricity_wall_entry_wire.json](electricity/electricity_wall_entry_wire/electricity_wall_entry_wire.json) |
| `electricity_wind_kit_100w_wood` | 100W Wooden Wind Turbine Kit | ✅ Yes | — | [electricity_wind_kit_100w_wood.json](electricity/electricity_wind_kit_100w_wood/electricity_wind_kit_100w_wood.json) |
| `electricity_wind_kit_200w_metal` | 200W Metal Wind Turbine Kit | ✅ Yes | — | [electricity_wind_kit_200w_metal.json](electricity/electricity_wind_kit_200w_metal/electricity_wind_kit_200w_metal.json) |
| `electricity_wind_kit_500w_metal` | 500W Metal Wind Turbine Kit | ✅ Yes | — | [electricity_wind_kit_500w_metal.json](electricity/electricity_wind_kit_500w_metal/electricity_wind_kit_500w_metal.json) |
| `electricity_wind_turbine` | Wind Turbine | ✅ Yes | — | [electricity_wind_turbine.json](electricity/electricity_wind_turbine/electricity_wind_turbine.json) |
| `electricity_wire_dc_indoor_10m` | Indoor DC Wire Coil | ✅ Yes | — | [electricity_wire_dc_indoor_10m.json](electricity/electricity_wire_dc_indoor_10m/electricity_wire_dc_indoor_10m.json) |
| `electricity_wire_dc_indoor_25m` | Indoor DC Wire Spool | ✅ Yes | — | [electricity_wire_dc_indoor_25m.json](electricity/electricity_wire_dc_indoor_25m/electricity_wire_dc_indoor_25m.json) |
| `electricity_wire_dc_outdoor_10m` | Weatherproof DC Wire Coil | ✅ Yes | — | [electricity_wire_dc_outdoor_10m.json](electricity/electricity_wire_dc_outdoor_10m/electricity_wire_dc_outdoor_10m.json) |
| `electricity_wire_dc_outdoor_25m` | Weatherproof DC Wire Spool | ✅ Yes | — | [electricity_wire_dc_outdoor_25m.json](electricity/electricity_wire_dc_outdoor_25m/electricity_wire_dc_outdoor_25m.json) |
| `electricity_wooden_utility_pole` | Wooden Utility Pole | ✅ Yes | — | [electricity_wooden_utility_pole.json](electricity/electricity_wooden_utility_pole/electricity_wooden_utility_pole.json) |
| `portable_generator` | Portable Generator | ✅ Yes | — | [portable_generator.json](electricity/portable_generator/portable_generator.json) |

### 📂 [Water](water/) (45 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `water_barrel_rain_200l` | Rain Barrel | ✅ Yes | — | [water_barrel_rain_200l.json](water/water_barrel_rain_200l/water_barrel_rain_200l.json) |
| `water_bucket_water` | Bucket of Water | ✅ Yes | — | [water_bucket_water.json](water/water_bucket_water/water_bucket_water.json) |
| `water_cistern_poly_1200l` | Water Cistern | ✅ Yes | — | [water_cistern_poly_1200l.json](water/water_cistern_poly_1200l/water_cistern_poly_1200l.json) |
| `water_cistern_poly_2400l` | Water Cistern | ✅ Yes | — | [water_cistern_poly_2400l.json](water/water_cistern_poly_2400l/water_cistern_poly_2400l.json) |
| `water_cistern_poly_3800l` | Water Cistern | ✅ Yes | — | [water_cistern_poly_3800l.json](water/water_cistern_poly_3800l/water_cistern_poly_3800l.json) |
| `water_dock_section_1x2m` | Water Dock Section | ✅ Yes | — | [water_dock_section_1x2m.json](water/water_dock_section_1x2m/water_dock_section_1x2m.json) |
| `water_drainsock_roll` | Item Plumbing Drainsock Roll | ✅ Yes | — | [water_drainsock_roll.json](water/water_drainsock_roll/water_drainsock_roll.json) |
| `water_faucet_indoor` | Utility Faucet | ✅ Yes | — | [water_faucet_indoor.json](water/water_faucet_indoor/water_faucet_indoor.json) |
| `water_filter` | Water Filter | ✅ Yes | — | [water_filter.json](water/water_filter/water_filter.json) |
| `water_filter_reverse_osmosis` | Reverse Osmosis Filter | ✅ Yes | — | [water_filter_reverse_osmosis.json](water/water_filter_reverse_osmosis/water_filter_reverse_osmosis.json) |
| `water_filter_spin_down_sediment` | Spin-Down Sediment Filter | ✅ Yes | — | [water_filter_spin_down_sediment.json](water/water_filter_spin_down_sediment/water_filter_spin_down_sediment.json) |
| `water_fitting_camlock_coupler` | Camlock Coupler | ✅ Yes | — | [water_fitting_camlock_coupler.json](water/water_fitting_camlock_coupler/water_fitting_camlock_coupler.json) |
| `water_hand_pump_wellhead` | Hand Pump Well Head | — | — | [water_hand_pump_wellhead.json](water/water_hand_pump_wellhead/water_hand_pump_wellhead.json) |
| `water_heater_electric_190l` | Electric Water Heater | ✅ Yes | — | [water_heater_electric_190l.json](water/water_heater_electric_190l/water_heater_electric_190l.json) |
| `water_hose_contractor_heavy` | Heavy Contractor Hose | ✅ Yes | — | [water_hose_contractor_heavy.json](water/water_hose_contractor_heavy/water_hose_contractor_heavy.json) |
| `water_hose_soaker_flat` | Soaker Hose | ✅ Yes | — | [water_hose_soaker_flat.json](water/water_hose_soaker_flat/water_hose_soaker_flat.json) |
| `water_ibc_tote_1000l` | IBC Tote | ✅ Yes | — | [water_ibc_tote_1000l.json](water/water_ibc_tote_1000l/water_ibc_tote_1000l.json) |
| `water_inlet_house` | Building Water Inlet | ✅ Yes | — | [water_inlet_house.json](water/water_inlet_house/water_inlet_house.json) |
| `water_irrigation_sprinkler_riser` | Farm Irrigation Sprinkler Riser | ✅ Yes | — | [water_irrigation_sprinkler_riser.json](water/water_irrigation_sprinkler_riser/water_irrigation_sprinkler_riser.json) |
| `water_jug_1l` | Full Water Jug | ✅ Yes | — | [water_jug_1l.json](water/water_jug_1l/water_jug_1l.json) |
| `water_jug_1l_pallet_10` | Full Water Jug Pallet | ✅ Yes | — | [water_jug_1l_pallet_10.json](water/water_jug_1l_pallet_10/water_jug_1l_pallet_10.json) |
| `water_jug_1l_pallet_5` | Full Water Jug Pallet | ✅ Yes | — | [water_jug_1l_pallet_5.json](water/water_jug_1l_pallet_5/water_jug_1l_pallet_5.json) |
| `water_jug_20l` | Water Jug | ✅ Yes | — | [water_jug_20l.json](water/water_jug_20l/water_jug_20l.json) |
| `water_jug_5l` | Full Water Jug | ✅ Yes | — | [water_jug_5l.json](water/water_jug_5l/water_jug_5l.json) |
| `water_jug_5l_pallet_10` | Full Water Jug Pallet | ✅ Yes | — | [water_jug_5l_pallet_10.json](water/water_jug_5l_pallet_10/water_jug_5l_pallet_10.json) |
| `water_jug_5l_pallet_5` | Full Water Jug Pallet | ✅ Yes | — | [water_jug_5l_pallet_5.json](water/water_jug_5l_pallet_5/water_jug_5l_pallet_5.json) |
| `water_pipe` | Water Pipe | ✅ Yes | — | [water_pipe.json](water/water_pipe/water_pipe.json) |
| `water_pressuretank_well` | Water Pressuretank Well | ✅ Yes | — | [water_pressuretank_well.json](water/water_pressuretank_well/water_pressuretank_well.json) |
| `water_pump` | Electric Water Pump | ✅ Yes | — | [water_pump.json](water/water_pump/water_pump.json) |
| `water_pump_high_capacity` | High Capacity Water Well Pump | ✅ Yes | — | [water_pump_high_capacity.json](water/water_pump_high_capacity/water_pump_high_capacity.json) |
| `water_pump_jet_shallow_well` | Shallow Well Jet Pump | ✅ Yes | — | [water_pump_jet_shallow_well.json](water/water_pump_jet_shallow_well/water_pump_jet_shallow_well.json) |
| `water_pump_low_capacity` | Low Capacity Water Well Pump | ✅ Yes | — | [water_pump_low_capacity.json](water/water_pump_low_capacity/water_pump_low_capacity.json) |
| `water_pump_submersible_1hp` | 1 HP Submersible Well Pump | ✅ Yes | — | [water_pump_submersible_1hp.json](water/water_pump_submersible_1hp/water_pump_submersible_1hp.json) |
| `water_pump_submersible_half_hp` | 1/2 HP Submersible Well Pump | ✅ Yes | — | [water_pump_submersible_half_hp.json](water/water_pump_submersible_half_hp/water_pump_submersible_half_hp.json) |
| `water_pump_submersible_three_quarter_hp` | 3/4 HP Submersible Well Pump | ✅ Yes | — | [water_pump_submersible_three_quarter_hp.json](water/water_pump_submersible_three_quarter_hp/water_pump_submersible_three_quarter_hp.json) |
| `water_pvc_bundle` | Item Plumbing Pvc Bundle | ✅ Yes | — | [water_pvc_bundle.json](water/water_pvc_bundle/water_pvc_bundle.json) |
| `water_spigot_outdoor` | Outdoor Spigot | ✅ Yes | — | [water_spigot_outdoor.json](water/water_spigot_outdoor/water_spigot_outdoor.json) |
| `water_spigot_post` | Spigot Post | ✅ Yes | — | [water_spigot_post.json](water/water_spigot_post/water_spigot_post.json) |
| `water_sprinkler` | Sprinkler Head | ✅ Yes | — | [water_sprinkler.json](water/water_sprinkler/water_sprinkler.json) |
| `water_sterilizer_uv_chamber` | UV Sterilizer Chamber | ✅ Yes | — | [water_sterilizer_uv_chamber.json](water/water_sterilizer_uv_chamber/water_sterilizer_uv_chamber.json) |
| `water_tape_drip_roll_300m` | Drip Tape Roll | ✅ Yes | — | [water_tape_drip_roll_300m.json](water/water_tape_drip_roll_300m/water_tape_drip_roll_300m.json) |
| `water_timer_hose_digital` | Digital Hose Timer | ✅ Yes | — | [water_timer_hose_digital.json](water/water_timer_hose_digital/water_timer_hose_digital.json) |
| `water_tubing_drip_irrigation` | Drip Irrigation Tubing | ✅ Yes | — | [water_tubing_drip_irrigation.json](water/water_tubing_drip_irrigation/water_tubing_drip_irrigation.json) |
| `water_wand_watering_brass` | Tool Wand Watering | ✅ Yes | — | [water_wand_watering_brass.json](water/water_wand_watering_brass/water_wand_watering_brass.json) |
| `water_watering_can` | Tool Wateringcan | ✅ Yes | — | [water_watering_can.json](water/water_watering_can/water_watering_can.json) |

### 📂 [Waste](waste/) (19 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `waste_aerator_septic_air_pump` | Septic Aerator Pump | ✅ Yes | — | [waste_aerator_septic_air_pump.json](waste/waste_aerator_septic_air_pump/waste_aerator_septic_air_pump.json) |
| `waste_box_distribution_septic` | Septic Distribution Box | ✅ Yes | — | [waste_box_distribution_septic.json](waste/waste_box_distribution_septic/waste_box_distribution_septic.json) |
| `waste_compost_bin_3bay` | 3-Bay Compost Bin | ✅ Yes | — | [waste_compost_bin_3bay.json](waste/waste_compost_bin_3bay/waste_compost_bin_3bay.json) |
| `waste_hose_sewer_rv_3m` | Short RV Sewer Hose | ✅ Yes | — | [waste_hose_sewer_rv_3m.json](waste/waste_hose_sewer_rv_3m/waste_hose_sewer_rv_3m.json) |
| `waste_hose_sewer_rv_6m` | Long RV Sewer Hose | ✅ Yes | — | [waste_hose_sewer_rv_6m.json](waste/waste_hose_sewer_rv_6m/waste_hose_sewer_rv_6m.json) |
| `waste_nozzle_spray_quick` | Quick-Connect Spray Nozzle | ✅ Yes | — | [waste_nozzle_spray_quick.json](waste/waste_nozzle_spray_quick/waste_nozzle_spray_quick.json) |
| `waste_outlet_house` | Building Waste Outlet | ✅ Yes | — | [waste_outlet_house.json](waste/waste_outlet_house/waste_outlet_house.json) |
| `waste_pile_manure_large` | Large Manure Pile (Material) | ✅ Yes | — | [waste_pile_manure_large.json](waste/waste_pile_manure_large/waste_pile_manure_large.json) |
| `waste_pile_manure_medium` | Medium Manure Pile (Material) | ✅ Yes | — | [waste_pile_manure_medium.json](waste/waste_pile_manure_medium/waste_pile_manure_medium.json) |
| `waste_pile_manure_small` | Small Manure Pile (Material) | ✅ Yes | — | [waste_pile_manure_small.json](waste/waste_pile_manure_small/waste_pile_manure_small.json) |
| `waste_pile_manure_tiny` | Tiny Manure Pile | ✅ Yes | — | [waste_pile_manure_tiny.json](waste/waste_pile_manure_tiny/waste_pile_manure_tiny.json) |
| `waste_pump_macerator` | Macerator Waste Pump | ✅ Yes | — | [waste_pump_macerator.json](waste/waste_pump_macerator/waste_pump_macerator.json) |
| `waste_pump_sump_float` | Automatic Sump Pump | ✅ Yes | — | [waste_pump_sump_float.json](waste/waste_pump_sump_float/waste_pump_sump_float.json) |
| `waste_riser_septic_lid` | Septic Riser & Lid | ✅ Yes | — | [waste_riser_septic_lid.json](waste/waste_riser_septic_lid/waste_riser_septic_lid.json) |
| `waste_service_septic_pumpout` | Septic Pump-Out | — | — | [waste_service_septic_pumpout.json](waste/waste_service_septic_pumpout/waste_service_septic_pumpout.json) |
| `waste_tank_manure_slurry` | Manure Slurry Tank | ✅ Yes | — | [waste_tank_manure_slurry.json](waste/waste_tank_manure_slurry/waste_tank_manure_slurry.json) |
| `waste_tank_rv_waste_tote` | RV Waste Holding Tote Tank | ✅ Yes | — | [waste_tank_rv_waste_tote.json](waste/waste_tank_rv_waste_tote/waste_tank_rv_waste_tote.json) |
| `waste_toilet_composting_rustic` | Composting Toilet | ✅ Yes | — | [waste_toilet_composting_rustic.json](waste/waste_toilet_composting_rustic/waste_toilet_composting_rustic.json) |
| `waste_treatment_septic_packets` | Septic Treatment Packets | ✅ Yes | — | [waste_treatment_septic_packets.json](waste/waste_treatment_septic_packets/waste_treatment_septic_packets.json) |

### 📂 [Internet](internet/) (24 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `net_antenna_omni_cellular` | Omni Cellular Antenna | ✅ Yes | — | [net_antenna_omni_cellular.json](internet/net_antenna_omni_cellular/net_antenna_omni_cellular.json) |
| `net_antenna_yagi_directional` | Yagi Directional Antenna | ✅ Yes | — | [net_antenna_yagi_directional.json](internet/net_antenna_yagi_directional/net_antenna_yagi_directional.json) |
| `net_ap_indoor_ceiling` | Indoor Access Point | ✅ Yes | — | [net_ap_indoor_ceiling.json](internet/net_ap_indoor_ceiling/net_ap_indoor_ceiling.json) |
| `net_ap_outdoor_weatherproof` | Outdoor Access Point | ✅ Yes | — | [net_ap_outdoor_weatherproof.json](internet/net_ap_outdoor_weatherproof/net_ap_outdoor_weatherproof.json) |
| `net_arrestor_lightning_ethernet` | Ethernet Surge Arrestor | ✅ Yes | — | [net_arrestor_lightning_ethernet.json](internet/net_arrestor_lightning_ethernet/net_arrestor_lightning_ethernet.json) |
| `net_cable_ethernet_cat6_15m` | Cat6 Cable (Short) | ✅ Yes | — | [net_cable_ethernet_cat6_15m.json](internet/net_cable_ethernet_cat6_15m/net_cable_ethernet_cat6_15m.json) |
| `net_cable_ethernet_cat6_30m` | Cat6 Cable (Long) | ✅ Yes | — | [net_cable_ethernet_cat6_30m.json](internet/net_cable_ethernet_cat6_30m/net_cable_ethernet_cat6_30m.json) |
| `net_camera_poe` | PoE Camera | ✅ Yes | — | [net_camera_poe.json](internet/net_camera_poe/net_camera_poe.json) |
| `net_dish_satellite` | Satellite Dish | ✅ Yes | — | [net_dish_satellite.json](internet/net_dish_satellite/net_dish_satellite.json) |
| `net_dish_satellite_high_perf` | High-Performance Satellite Dish | ✅ Yes | — | [net_dish_satellite_high_perf.json](internet/net_dish_satellite_high_perf/net_dish_satellite_high_perf.json) |
| `net_injector_poe_adapter` | PoE Injector | ✅ Yes | — | [net_injector_poe_adapter.json](internet/net_injector_poe_adapter/net_injector_poe_adapter.json) |
| `net_jack_wall` | Ethernet Wall Jack | ✅ Yes | — | [net_jack_wall.json](internet/net_jack_wall/net_jack_wall.json) |
| `net_mount_j_mast_bracket` | J-Mast Mounting Bracket | ✅ Yes | — | [net_mount_j_mast_bracket.json](internet/net_mount_j_mast_bracket/net_mount_j_mast_bracket.json) |
| `net_networkswitch_poe` | Compact PoE Switch | ✅ Yes | — | [net_networkswitch_poe.json](internet/net_networkswitch_poe/net_networkswitch_poe.json) |
| `net_rack_wall_8u` | Wall Rack | ✅ Yes | — | [net_rack_wall_8u.json](internet/net_rack_wall_8u/net_rack_wall_8u.json) |
| `net_router` | Internet Router | ✅ Yes | — | [net_router.json](internet/net_router/net_router.json) |
| `net_router_mesh_wifi6` | Wi-Fi 6 Mesh Router | ✅ Yes | — | [net_router_mesh_wifi6.json](internet/net_router_mesh_wifi6/net_router_mesh_wifi6.json) |
| `net_router_rackmount` | Rackmount Router | ✅ Yes | — | [net_router_rackmount.json](internet/net_router_rackmount/net_router_rackmount.json) |
| `net_spool_cable_cat6_150m` | Cat6 Cable Spool | ✅ Yes | — | [net_spool_cable_cat6_150m.json](internet/net_spool_cable_cat6_150m/net_spool_cable_cat6_150m.json) |
| `net_switch_poe_16port` | 16-Port PoE Switch | ✅ Yes | — | [net_switch_poe_16port.json](internet/net_switch_poe_16port/net_switch_poe_16port.json) |
| `net_switch_poe_8port` | 8-Port PoE Switch | ✅ Yes | — | [net_switch_poe_8port.json](internet/net_switch_poe_8port/net_switch_poe_8port.json) |
| `net_switch_rackmount_16port` | 16-Port Rackmount Switch | ✅ Yes | — | [net_switch_rackmount_16port.json](internet/net_switch_rackmount_16port/net_switch_rackmount_16port.json) |
| `net_switch_rackmount_32port` | 32-Port Rackmount Switch | ✅ Yes | — | [net_switch_rackmount_32port.json](internet/net_switch_rackmount_32port/net_switch_rackmount_32port.json) |
| `net_ups_rackmount` | Rackmount UPS | ✅ Yes | — | [net_ups_rackmount.json](internet/net_ups_rackmount/net_ups_rackmount.json) |

### 📂 [Hud](hud/) (31 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `coin` | Coin | — | — | [coin.json](hud/coin/coin.json) |
| `compact_hotbar_10slots` | Compact Hotbar 10Slots | — | — | [compact_hotbar_10slots.json](hud/compact_hotbar_10slots/compact_hotbar_10slots.json) |
| `compact_hotbar_slot` | Compact Hotbar Slot | — | — | [compact_hotbar_slot.json](hud/compact_hotbar_slot/compact_hotbar_slot.json) |
| `compact_hotbar_tray_kit` | Compact Hotbar Tray Kit | — | — | [compact_hotbar_tray_kit.json](hud/compact_hotbar_tray_kit/compact_hotbar_tray_kit.json) |
| `compact_window_crafting_kit` | Compact Window Crafting Kit | — | — | [compact_window_crafting_kit.json](hud/compact_window_crafting_kit/compact_window_crafting_kit.json) |
| `compact_window_dialog` | Compact Window Dialog | — | — | [compact_window_dialog.json](hud/compact_window_dialog/compact_window_dialog.json) |
| `hud_badge_3d` | Badge 3D | — | — | [hud_badge_3d.json](hud/hud_badge_3d/hud_badge_3d.json) |
| `hud_compact_btn_amber_normal` | Compact Btn Amber Normal | — | — | [hud_compact_btn_amber_normal.json](hud/hud_compact_btn_amber_normal/hud_compact_btn_amber_normal.json) |
| `hud_compact_btn_green_normal` | Compact Btn Green Normal | — | — | [hud_compact_btn_green_normal.json](hud/hud_compact_btn_green_normal/hud_compact_btn_green_normal.json) |
| `hud_compact_btn_slate_hover` | Compact Btn Slate Hover | — | — | [hud_compact_btn_slate_hover.json](hud/hud_compact_btn_slate_hover/hud_compact_btn_slate_hover.json) |
| `hud_compact_btn_slate_normal` | Compact Btn Slate Normal | — | — | [hud_compact_btn_slate_normal.json](hud/hud_compact_btn_slate_normal/hud_compact_btn_slate_normal.json) |
| `hud_compact_player_status` | Compact Player Status | — | — | [hud_compact_player_status.json](hud/hud_compact_player_status/hud_compact_player_status.json) |
| `hud_compact_player_status_kit` | Compact Player Status Kit | — | — | [hud_compact_player_status_kit.json](hud/hud_compact_player_status_kit/hud_compact_player_status_kit.json) |
| `hud_compact_resources` | Compact Resources | — | — | [hud_compact_resources.json](hud/hud_compact_resources/hud_compact_resources.json) |
| `hud_compact_resources_kit` | Compact Resources Kit | — | — | [hud_compact_resources_kit.json](hud/hud_compact_resources_kit/hud_compact_resources_kit.json) |
| `hud_compact_selector_active` | Compact Selector Active | — | — | [hud_compact_selector_active.json](hud/hud_compact_selector_active/hud_compact_selector_active.json) |
| `hud_compact_selector_active_kit` | Compact Selector Active Kit | — | — | [hud_compact_selector_active_kit.json](hud/hud_compact_selector_active_kit/hud_compact_selector_active_kit.json) |
| `hud_compact_time_season` | Compact Time Season | — | — | [hud_compact_time_season.json](hud/hud_compact_time_season/hud_compact_time_season.json) |
| `hud_compact_time_season_kit` | Compact Time Season Kit | — | — | [hud_compact_time_season_kit.json](hud/hud_compact_time_season_kit/hud_compact_time_season_kit.json) |
| `hud_emblem_square` | Emblem Square | — | — | [hud_emblem_square.json](hud/hud_emblem_square/hud_emblem_square.json) |
| `hud_heart` | Heart | — | — | [hud_heart.json](hud/hud_heart/hud_heart.json) |
| `hud_icon_battery` | Icon Battery | — | — | [hud_icon_battery.json](hud/hud_icon_battery/hud_icon_battery.json) |
| `hud_icon_water` | Icon Water | — | — | [hud_icon_water.json](hud/hud_icon_water/hud_icon_water.json) |
| `hud_logo_diagonal` | Logo Diagonal | — | — | [hud_logo_diagonal.json](hud/hud_logo_diagonal/hud_logo_diagonal.json) |
| `hud_logo_horizontal` | Logo Horizontal | — | — | [hud_logo_horizontal.json](hud/hud_logo_horizontal/hud_logo_horizontal.json) |
| `hud_solar` | Solar | — | — | [hud_solar.json](hud/hud_solar/hud_solar.json) |
| `hud_stamina` | Stamina | — | — | [hud_stamina.json](hud/hud_stamina/hud_stamina.json) |
| `hud_water` | Water HUD Icon | — | — | [hud_water.json](hud/hud_water/hud_water.json) |
| `icon_coin` | Icon Coin | — | — | [icon_coin.json](hud/icon_coin/icon_coin.json) |
| `icon_heart` | Icon Heart | — | — | [icon_heart.json](hud/icon_heart/icon_heart.json) |
| `icon_stamina` | Icon Stamina | — | — | [icon_stamina.json](hud/icon_stamina/icon_stamina.json) |

### 📂 [Ground](ground/) (18 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `blend_masks` | Blend Masks | — | — | [blend_masks.json](ground/blend_masks/blend_masks.json) |
| `clutter_acorns` | Acorns | ✅ Yes | — | [clutter_acorns.json](ground/clutter_acorns/clutter_acorns.json) |
| `clutter_boulder` | Boulder | — | — | [clutter_boulder.json](ground/clutter_boulder/clutter_boulder.json) |
| `clutter_branch` | Fallen Tree Branch | ✅ Yes | — | [clutter_branch.json](ground/clutter_branch/clutter_branch.json) |
| `clutter_cattails` | Cattails | ✅ Yes | — | [clutter_cattails.json](ground/clutter_cattails/clutter_cattails.json) |
| `clutter_dirt_clump` | Dirt Clump | ✅ Yes | — | [clutter_dirt_clump.json](ground/clutter_dirt_clump/clutter_dirt_clump.json) |
| `clutter_grass_tuft` | Wild Grass Tuft | ✅ Yes | — | [clutter_grass_tuft.json](ground/clutter_grass_tuft/clutter_grass_tuft.json) |
| `clutter_leaves` | Fallen Leaves | ✅ Yes | — | [clutter_leaves.json](ground/clutter_leaves/clutter_leaves.json) |
| `clutter_pebbles` | Pebbles | ✅ Yes | — | [clutter_pebbles.json](ground/clutter_pebbles/clutter_pebbles.json) |
| `clutter_pinecones` | Pinecones | ✅ Yes | — | [clutter_pinecones.json](ground/clutter_pinecones/clutter_pinecones.json) |
| `clutter_rock_large` | Large Rock | — | — | [clutter_rock_large.json](ground/clutter_rock_large/clutter_rock_large.json) |
| `clutter_rock_medium` | Medium Rock | — | — | [clutter_rock_medium.json](ground/clutter_rock_medium/clutter_rock_medium.json) |
| `clutter_rock_small` | Small Rock | — | — | [clutter_rock_small.json](ground/clutter_rock_small/clutter_rock_small.json) |
| `clutter_tall_grass` | Clutter Tall Grass | ✅ Yes | — | [clutter_tall_grass.json](ground/clutter_tall_grass/clutter_tall_grass.json) |
| `clutter_twigs` | Twigs | ✅ Yes | — | [clutter_twigs.json](ground/clutter_twigs/clutter_twigs.json) |
| `ground_medium_grass` | Medium Grass | — | — | [ground_medium_grass.json](ground/ground_medium_grass/ground_medium_grass.json) |
| `textures` | Textures | — | — | [textures.json](ground/textures/textures.json) |
| `tile_grass_tuft_meadow` | Grass Tuft Meadow | ✅ Yes | — | [tile_grass_tuft_meadow.json](ground/tile_grass_tuft_meadow/tile_grass_tuft_meadow.json) |

### 📂 [Food](food/) (124 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `food_apple` | Fresh Red Apple | ✅ Yes | — | [food_apple.json](food/food_apple/food_apple.json) |
| `food_apple_muffin` | Apple Muffin | — | — | [food_apple_muffin.json](food/food_apple_muffin/food_apple_muffin.json) |
| `food_apple_pie` | Apple Pie | — | — | [food_apple_pie.json](food/food_apple_pie/food_apple_pie.json) |
| `food_apricot` | Fresh Apricot | — | — | [food_apricot.json](food/food_apricot/food_apricot.json) |
| `food_apricot_muffin` | Apricot Muffin | — | — | [food_apricot_muffin.json](food/food_apricot_muffin/food_apricot_muffin.json) |
| `food_bacon_and_eggs` | Bacon and Eggs | — | — | [food_bacon_and_eggs.json](food/food_bacon_and_eggs/food_bacon_and_eggs.json) |
| `food_bacon_cooked` | Crispy Bacon | — | — | [food_bacon_cooked.json](food/food_bacon_cooked/food_bacon_cooked.json) |
| `food_baked_potato` | Baked Potato | — | — | [food_baked_potato.json](food/food_baked_potato/food_baked_potato.json) |
| `food_bass_deepfried` | Bass Fillet Deep Fried | — | — | [food_bass_deepfried.json](food/food_bass_deepfried/food_bass_deepfried.json) |
| `food_bass_grilled` | Bass Grilled Fillet | — | — | [food_bass_grilled.json](food/food_bass_grilled/food_bass_grilled.json) |
| `food_beef_barley_soup` | Beef Barley Soup | — | — | [food_beef_barley_soup.json](food/food_beef_barley_soup/food_beef_barley_soup.json) |
| `food_beef_stew` | Beef Stew | — | — | [food_beef_stew.json](food/food_beef_stew/food_beef_stew.json) |
| `food_beet` | Fresh Beet | — | — | [food_beet.json](food/food_beet/food_beet.json) |
| `food_blueberry` | Blueberry | — | — | [food_blueberry.json](food/food_blueberry/food_blueberry.json) |
| `food_blueberry_muffin` | Blueberry Muffin | — | — | [food_blueberry_muffin.json](food/food_blueberry_muffin/food_blueberry_muffin.json) |
| `food_blueberry_pie` | Blueberry Pie | — | — | [food_blueberry_pie.json](food/food_blueberry_pie/food_blueberry_pie.json) |
| `food_bread` | Bread | — | — | [food_bread.json](food/food_bread/food_bread.json) |
| `food_broccoli` | Broccoli Crown | — | — | [food_broccoli.json](food/food_broccoli/food_broccoli.json) |
| `food_burger` | Hamburger | — | — | [food_burger.json](food/food_burger/food_burger.json) |
| `food_burger_bun` | Burger Bun | — | — | [food_burger_bun.json](food/food_burger_bun/food_burger_bun.json) |
| `food_buttered_noodles` | Buttered Noodles | — | — | [food_buttered_noodles.json](food/food_buttered_noodles/food_buttered_noodles.json) |
| `food_cabbage` | Head of Cabbage | — | — | [food_cabbage.json](food/food_cabbage/food_cabbage.json) |
| `food_cake` | Yellow Cake | — | — | [food_cake.json](food/food_cake/food_cake.json) |
| `food_cantaloupe` | Cantaloupe | — | — | [food_cantaloupe.json](food/food_cantaloupe/food_cantaloupe.json) |
| `food_carrot` | Fresh Garden Carrot | ✅ Yes | — | [food_carrot.json](food/food_carrot/food_carrot.json) |
| `food_catfish_deepfried` | Catfish Fillet Deep Fried | — | — | [food_catfish_deepfried.json](food/food_catfish_deepfried/food_catfish_deepfried.json) |
| `food_catfish_grilled` | Catfish Grilled Fillet | — | — | [food_catfish_grilled.json](food/food_catfish_grilled/food_catfish_grilled.json) |
| `food_cheese` | Aged Farmhouse Cheese | — | — | [food_cheese.json](food/food_cheese/food_cheese.json) |
| `food_cherry` | Fresh Cherries | — | — | [food_cherry.json](food/food_cherry/food_cherry.json) |
| `food_cherry_muffin` | Cherry Muffin | — | — | [food_cherry_muffin.json](food/food_cherry_muffin/food_cherry_muffin.json) |
| `food_cherry_pie` | Cherry Pie | — | — | [food_cherry_pie.json](food/food_cherry_pie/food_cherry_pie.json) |
| `food_chicken_noodle_soup` | Chicken Noodle Soup | — | — | [food_chicken_noodle_soup.json](food/food_chicken_noodle_soup/food_chicken_noodle_soup.json) |
| `food_chicken_stew` | Chicken Stew | — | — | [food_chicken_stew.json](food/food_chicken_stew/food_chicken_stew.json) |
| `food_coleslaw` | Coleslaw | — | — | [food_coleslaw.json](food/food_coleslaw/food_coleslaw.json) |
| `food_corn_muffin` | Corn Muffin | — | — | [food_corn_muffin.json](food/food_corn_muffin/food_corn_muffin.json) |
| `food_cornbread` | Cornbread | — | — | [food_cornbread.json](food/food_cornbread/food_cornbread.json) |
| `food_crappie_deepfried` | Crappie Fillet Deep Fried | — | — | [food_crappie_deepfried.json](food/food_crappie_deepfried/food_crappie_deepfried.json) |
| `food_crappie_grilled` | Crappie Grilled Fillet | — | — | [food_crappie_grilled.json](food/food_crappie_grilled/food_crappie_grilled.json) |
| `food_cucumber` | Fresh Cucumber | — | — | [food_cucumber.json](food/food_cucumber/food_cucumber.json) |
| `food_elderberry` | Elderberry | — | — | [food_elderberry.json](food/food_elderberry/food_elderberry.json) |
| `food_elderberry_muffin` | Elderberry Muffin | — | — | [food_elderberry_muffin.json](food/food_elderberry_muffin/food_elderberry_muffin.json) |
| `food_fig` | Fresh Fig | — | — | [food_fig.json](food/food_fig/food_fig.json) |
| `food_fig_muffin` | Fig Muffin | — | — | [food_fig_muffin.json](food/food_fig_muffin/food_fig_muffin.json) |
| `food_french_toast` | French Toast | — | — | [food_french_toast.json](food/food_french_toast/food_french_toast.json) |
| `food_garden_salad` | Garden Salad | — | — | [food_garden_salad.json](food/food_garden_salad/food_garden_salad.json) |
| `food_garlic` | Garlic Bulb | — | — | [food_garlic.json](food/food_garlic/food_garlic.json) |
| `food_goat_meat_baked` | Roast Goat Leg | — | — | [food_goat_meat_baked.json](food/food_goat_meat_baked/food_goat_meat_baked.json) |
| `food_grapes` | Grapes | — | — | [food_grapes.json](food/food_grapes/food_grapes.json) |
| `food_green_beans` | Green Beans | — | — | [food_green_beans.json](food/food_green_beans/food_green_beans.json) |
| `food_grits` | Grits | — | — | [food_grits.json](food/food_grits/food_grits.json) |
| `food_ground_beef_grilled` | Grilled Burger Patty | — | — | [food_ground_beef_grilled.json](food/food_ground_beef_grilled/food_ground_beef_grilled.json) |
| `food_ham_baked` | Baked Ham | — | — | [food_ham_baked.json](food/food_ham_baked/food_ham_baked.json) |
| `food_haskap` | Haskap | — | — | [food_haskap.json](food/food_haskap/food_haskap.json) |
| `food_haskap_muffin` | Haskap Muffin | — | — | [food_haskap_muffin.json](food/food_haskap_muffin/food_haskap_muffin.json) |
| `food_hazelnut` | Hazelnuts | — | — | [food_hazelnut.json](food/food_hazelnut/food_hazelnut.json) |
| `food_hot_dog` | Hot Dog | — | — | [food_hot_dog.json](food/food_hot_dog/food_hot_dog.json) |
| `food_hot_dog_bun` | Hot Dog Bun | — | — | [food_hot_dog_bun.json](food/food_hot_dog_bun/food_hot_dog_bun.json) |
| `food_huckleberry` | Huckleberry | — | — | [food_huckleberry.json](food/food_huckleberry/food_huckleberry.json) |
| `food_huckleberry_muffin` | Huckleberry Muffin | — | — | [food_huckleberry_muffin.json](food/food_huckleberry_muffin/food_huckleberry_muffin.json) |
| `food_lamb_chop_grilled` | Grilled Lamb Chop | — | — | [food_lamb_chop_grilled.json](food/food_lamb_chop_grilled/food_lamb_chop_grilled.json) |
| `food_lemon` | Fresh Lemon | ✅ Yes | — | [food_lemon.json](food/food_lemon/food_lemon.json) |
| `food_lemon_muffin` | Lemon Muffin | — | — | [food_lemon_muffin.json](food/food_lemon_muffin/food_lemon_muffin.json) |
| `food_lettuce` | Head of Lettuce | — | — | [food_lettuce.json](food/food_lettuce/food_lettuce.json) |
| `food_mac_and_cheese` | Macaroni and Cheese | — | — | [food_mac_and_cheese.json](food/food_mac_and_cheese/food_mac_and_cheese.json) |
| `food_mashed_potatoes` | Mashed Potatoes | — | — | [food_mashed_potatoes.json](food/food_mashed_potatoes/food_mashed_potatoes.json) |
| `food_meatloaf` | Meatloaf | — | — | [food_meatloaf.json](food/food_meatloaf/food_meatloaf.json) |
| `food_muffin` | Muffin | — | — | [food_muffin.json](food/food_muffin/food_muffin.json) |
| `food_oatmeal` | Oatmeal | — | — | [food_oatmeal.json](food/food_oatmeal/food_oatmeal.json) |
| `food_onion` | Fresh Onion | — | — | [food_onion.json](food/food_onion/food_onion.json) |
| `food_orange` | Fresh Navel Orange | ✅ Yes | — | [food_orange.json](food/food_orange/food_orange.json) |
| `food_orange_muffin` | Orange Muffin | — | — | [food_orange_muffin.json](food/food_orange_muffin/food_orange_muffin.json) |
| `food_pancakes` | Pancakes | — | — | [food_pancakes.json](food/food_pancakes/food_pancakes.json) |
| `food_peach` | Fresh Peach | — | — | [food_peach.json](food/food_peach/food_peach.json) |
| `food_peach_muffin` | Peach Muffin | — | — | [food_peach_muffin.json](food/food_peach_muffin/food_peach_muffin.json) |
| `food_peanuts` | Raw Peanuts | — | — | [food_peanuts.json](food/food_peanuts/food_peanuts.json) |
| `food_pear` | Fresh Pear | — | — | [food_pear.json](food/food_pear/food_pear.json) |
| `food_pear_muffin` | Pear Muffin | — | — | [food_pear_muffin.json](food/food_pear_muffin/food_pear_muffin.json) |
| `food_peas` | Fresh Peas | — | — | [food_peas.json](food/food_peas/food_peas.json) |
| `food_pecan` | Pecans | — | — | [food_pecan.json](food/food_pecan/food_pecan.json) |
| `food_pepper` | Bell Pepper | — | — | [food_pepper.json](food/food_pepper/food_pepper.json) |
| `food_plum` | Fresh Plum | — | — | [food_plum.json](food/food_plum/food_plum.json) |
| `food_plum_muffin` | Plum Muffin | — | — | [food_plum_muffin.json](food/food_plum_muffin/food_plum_muffin.json) |
| `food_pork_chop_grilled` | Grilled Bone-In Pork Chop | — | — | [food_pork_chop_grilled.json](food/food_pork_chop_grilled/food_pork_chop_grilled.json) |
| `food_pot_roast` | Pot Roast | — | — | [food_pot_roast.json](food/food_pot_roast/food_pot_roast.json) |
| `food_potato` | Russet Potato | ✅ Yes | — | [food_potato.json](food/food_potato/food_potato.json) |
| `food_potato_soup` | Potato Soup | — | — | [food_potato_soup.json](food/food_potato_soup/food_potato_soup.json) |
| `food_pumpkin` | Autumn Pumpkin | ✅ Yes | — | [food_pumpkin.json](food/food_pumpkin/food_pumpkin.json) |
| `food_pumpkin_pie` | Pumpkin Pie | — | — | [food_pumpkin_pie.json](food/food_pumpkin_pie/food_pumpkin_pie.json) |
| `food_pumpkin_soup` | Pumpkin Soup | — | — | [food_pumpkin_soup.json](food/food_pumpkin_soup/food_pumpkin_soup.json) |
| `food_radish` | Fresh Radish | — | — | [food_radish.json](food/food_radish/food_radish.json) |
| `food_raspberry` | Raspberry | — | — | [food_raspberry.json](food/food_raspberry/food_raspberry.json) |
| `food_raspberry_muffin` | Raspberry Muffin | — | — | [food_raspberry_muffin.json](food/food_raspberry_muffin/food_raspberry_muffin.json) |
| `food_rhubarb` | Rhubarb Stalks | — | — | [food_rhubarb.json](food/food_rhubarb/food_rhubarb.json) |
| `food_rhubarb_muffin` | Rhubarb Muffin | — | — | [food_rhubarb_muffin.json](food/food_rhubarb_muffin/food_rhubarb_muffin.json) |
| `food_roast_chicken` | Roast Chicken | — | — | [food_roast_chicken.json](food/food_roast_chicken/food_roast_chicken.json) |
| `food_roasted_vegetables` | Roasted Vegetables | — | — | [food_roasted_vegetables.json](food/food_roasted_vegetables/food_roasted_vegetables.json) |
| `food_salmon_grilled` | Salmon Grilled Fillet | — | — | [food_salmon_grilled.json](food/food_salmon_grilled/food_salmon_grilled.json) |
| `food_sausage_grilled` | Grilled Sausage | — | — | [food_sausage_grilled.json](food/food_sausage_grilled/food_sausage_grilled.json) |
| `food_sausage_pasta` | Sausage Pasta | — | — | [food_sausage_pasta.json](food/food_sausage_pasta/food_sausage_pasta.json) |
| `food_scrambled_eggs` | Scrambled Eggs | — | — | [food_scrambled_eggs.json](food/food_scrambled_eggs/food_scrambled_eggs.json) |
| `food_shepherds_pie` | Shepherd's Pie | — | — | [food_shepherds_pie.json](food/food_shepherds_pie/food_shepherds_pie.json) |
| `food_spaghetti` | Spaghetti with Sauce | — | — | [food_spaghetti.json](food/food_spaghetti/food_spaghetti.json) |
| `food_spaghetti_meatballs` | Spaghetti and Meatballs | — | — | [food_spaghetti_meatballs.json](food/food_spaghetti_meatballs/food_spaghetti_meatballs.json) |
| `food_spinach` | Fresh Spinach | — | — | [food_spinach.json](food/food_spinach/food_spinach.json) |
| `food_spinach_salad` | Spinach Salad | — | — | [food_spinach_salad.json](food/food_spinach_salad/food_spinach_salad.json) |
| `food_steak_grilled` | Grilled Ribeye Steak | — | — | [food_steak_grilled.json](food/food_steak_grilled/food_steak_grilled.json) |
| `food_strawberry` | Fresh Strawberry | ✅ Yes | — | [food_strawberry.json](food/food_strawberry/food_strawberry.json) |
| `food_strawberry_muffin` | Strawberry Muffin | — | — | [food_strawberry_muffin.json](food/food_strawberry_muffin/food_strawberry_muffin.json) |
| `food_sugar_cookies` | Sugar Cookies | — | — | [food_sugar_cookies.json](food/food_sugar_cookies/food_sugar_cookies.json) |
| `food_tomato` | Vine Ripe Tomato | ✅ Yes | — | [food_tomato.json](food/food_tomato/food_tomato.json) |
| `food_tomato_soup` | Tomato Soup | — | — | [food_tomato_soup.json](food/food_tomato_soup/food_tomato_soup.json) |
| `food_trout_deepfried` | Trout Fillet Deep Fried | — | — | [food_trout_deepfried.json](food/food_trout_deepfried/food_trout_deepfried.json) |
| `food_trout_grilled` | Trout Grilled Fillet | — | — | [food_trout_grilled.json](food/food_trout_grilled/food_trout_grilled.json) |
| `food_truffle` | Black Foraged Truffle | ✅ Yes | — | [food_truffle.json](food/food_truffle/food_truffle.json) |
| `food_vegetable_soup` | Vegetable Soup | — | — | [food_vegetable_soup.json](food/food_vegetable_soup/food_vegetable_soup.json) |
| `food_walleye_deepfried` | Walleye Fillet Deep Fried | — | — | [food_walleye_deepfried.json](food/food_walleye_deepfried/food_walleye_deepfried.json) |
| `food_walleye_grilled` | Walleye Grilled Fillet | — | — | [food_walleye_grilled.json](food/food_walleye_grilled/food_walleye_grilled.json) |
| `food_walnut` | Walnuts | — | — | [food_walnut.json](food/food_walnut/food_walnut.json) |
| `food_watermelon` | Watermelon | — | — | [food_watermelon.json](food/food_watermelon/food_watermelon.json) |
| `food_zucchini` | Zucchini | — | — | [food_zucchini.json](food/food_zucchini/food_zucchini.json) |
| `ingredient_beef_grilled` | Grilled Beef Cut | — | — | [ingredient_beef_grilled.json](food/ingredient_beef_grilled/ingredient_beef_grilled.json) |
| `ingredient_chicken_grilled` | Grilled Chicken Drumstick | — | — | [ingredient_chicken_grilled.json](food/ingredient_chicken_grilled/ingredient_chicken_grilled.json) |
| `ingredient_milk` | Fresh Whole Milk | ✅ Yes | — | [ingredient_milk.json](food/ingredient_milk/ingredient_milk.json) |
| `ingredient_pork_grilled` | Grilled Pork Chop | — | — | [ingredient_pork_grilled.json](food/ingredient_pork_grilled/ingredient_pork_grilled.json) |

### 📂 [Fuel](fuel/) (33 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `fuel_bulk_diesel` | Bulk Diesel | — | — | [fuel_bulk_diesel.json](fuel/fuel_bulk_diesel/fuel_bulk_diesel.json) |
| `fuel_bulk_gasoline` | Bulk Gasoline | — | — | [fuel_bulk_gasoline.json](fuel/fuel_bulk_gasoline/fuel_bulk_gasoline.json) |
| `fuel_bulk_propane` | Bulk Propane | — | — | [fuel_bulk_propane.json](fuel/fuel_bulk_propane/fuel_bulk_propane.json) |
| `fuel_charcoal` | Charcoal | ✅ Yes | — | [fuel_charcoal.json](fuel/fuel_charcoal/fuel_charcoal.json) |
| `fuel_firewood_bundle_birch` | Birch Firewood Bundle | ✅ Yes | — | [fuel_firewood_bundle_birch.json](fuel/fuel_firewood_bundle_birch/fuel_firewood_bundle_birch.json) |
| `fuel_firewood_bundle_maple` | Maple Firewood Bundle | ✅ Yes | — | [fuel_firewood_bundle_maple.json](fuel/fuel_firewood_bundle_maple/fuel_firewood_bundle_maple.json) |
| `fuel_firewood_bundle_oak` | Oak Firewood Bundle | ✅ Yes | — | [fuel_firewood_bundle_oak.json](fuel/fuel_firewood_bundle_oak/fuel_firewood_bundle_oak.json) |
| `fuel_firewood_bundle_pine` | Pine Firewood Bundle | ✅ Yes | — | [fuel_firewood_bundle_pine.json](fuel/fuel_firewood_bundle_pine/fuel_firewood_bundle_pine.json) |
| `fuel_firewood_bundle_poplar` | Poplar Firewood Bundle | ✅ Yes | — | [fuel_firewood_bundle_poplar.json](fuel/fuel_firewood_bundle_poplar/fuel_firewood_bundle_poplar.json) |
| `fuel_firewood_bundle_willow` | Willow Firewood Bundle | ✅ Yes | — | [fuel_firewood_bundle_willow.json](fuel/fuel_firewood_bundle_willow/fuel_firewood_bundle_willow.json) |
| `fuel_large_diesel_container` | Large Diesel Fuel Container | ✅ Yes | — | [fuel_large_diesel_container.json](fuel/fuel_large_diesel_container/fuel_large_diesel_container.json) |
| `fuel_pipe_line` | Fuel Line | ✅ Yes | — | [fuel_pipe_line.json](fuel/fuel_pipe_line/fuel_pipe_line.json) |
| `fuel_pipe_line_stack_10` | Fuel Line Stack | ✅ Yes | — | [fuel_pipe_line_stack_10.json](fuel/fuel_pipe_line_stack_10/fuel_pipe_line_stack_10.json) |
| `fuel_pipe_line_stack_20` | Fuel Line Stack | ✅ Yes | — | [fuel_pipe_line_stack_20.json](fuel/fuel_pipe_line_stack_20/fuel_pipe_line_stack_20.json) |
| `fuel_pipe_propane` | Propane Pipe | ✅ Yes | — | [fuel_pipe_propane.json](fuel/fuel_pipe_propane/fuel_pipe_propane.json) |
| `fuel_pipe_propane_stack_10` | Propane Pipe Stack | ✅ Yes | — | [fuel_pipe_propane_stack_10.json](fuel/fuel_pipe_propane_stack_10/fuel_pipe_propane_stack_10.json) |
| `fuel_pipe_propane_stack_20` | Propane Pipe Stack | ✅ Yes | — | [fuel_pipe_propane_stack_20.json](fuel/fuel_pipe_propane_stack_20/fuel_pipe_propane_stack_20.json) |
| `fuel_propane_18l` | Propane Tank | ✅ Yes | — | [fuel_propane_18l.json](fuel/fuel_propane_18l/fuel_propane_18l.json) |
| `fuel_propane_1_5l` | Small Propane Tank | ✅ Yes | — | [fuel_propane_1_5l.json](fuel/fuel_propane_1_5l/fuel_propane_1_5l.json) |
| `fuel_propane_36l` | Large Propane Tank | ✅ Yes | — | [fuel_propane_36l.json](fuel/fuel_propane_36l/fuel_propane_36l.json) |
| `fuel_propane_fill_post` | Propane Fill Post | ✅ Yes | — | [fuel_propane_fill_post.json](fuel/fuel_propane_fill_post/fuel_propane_fill_post.json) |
| `fuel_propane_house_connector` | Propane House Connector | ✅ Yes | — | [fuel_propane_house_connector.json](fuel/fuel_propane_house_connector/fuel_propane_house_connector.json) |
| `fuel_pump_diesel` | Diesel Fuel Pump | ✅ Yes | — | [fuel_pump_diesel.json](fuel/fuel_pump_diesel/fuel_pump_diesel.json) |
| `fuel_pump_gas` | Gasoline Fuel Pump | ✅ Yes | — | [fuel_pump_gas.json](fuel/fuel_pump_gas/fuel_pump_gas.json) |
| `fuel_service_tank_pickup` | Tank Pickup | — | — | [fuel_service_tank_pickup.json](fuel/fuel_service_tank_pickup/fuel_service_tank_pickup.json) |
| `fuel_small_diesel_container` | Small Diesel Fuel Container | ✅ Yes | — | [fuel_small_diesel_container.json](fuel/fuel_small_diesel_container/fuel_small_diesel_container.json) |
| `fuel_steel_drum_200l` | Steel Drum | ✅ Yes | — | [fuel_steel_drum_200l.json](fuel/fuel_steel_drum_200l/fuel_steel_drum_200l.json) |
| `fuel_tank_bulk_large` | Large Bulk Fuel Storage Tank | ✅ Yes | — | [fuel_tank_bulk_large.json](fuel/fuel_tank_bulk_large/fuel_tank_bulk_large.json) |
| `fuel_tank_bulk_small` | Small Bulk Fuel Storage Tank | ✅ Yes | — | [fuel_tank_bulk_small.json](fuel/fuel_tank_bulk_small/fuel_tank_bulk_small.json) |
| `fuel_tank_propane_1900l` | Propane Tank | ✅ Yes | — | [fuel_tank_propane_1900l.json](fuel/fuel_tank_propane_1900l/fuel_tank_propane_1900l.json) |
| `fuel_tank_propane_3800l` | Large Propane Tank | ✅ Yes | — | [fuel_tank_propane_3800l.json](fuel/fuel_tank_propane_3800l/fuel_tank_propane_3800l.json) |
| `large_gas_fuel_container` | Large Gas Fuel Container | ✅ Yes | — | [large_gas_fuel_container.json](fuel/large_gas_fuel_container/large_gas_fuel_container.json) |
| `small_gas_fuel_container` | Small Gas Fuel Container | ✅ Yes | — | [small_gas_fuel_container.json](fuel/small_gas_fuel_container/small_gas_fuel_container.json) |

### 📂 [Materials](materials/) (82 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `mat_bale_hay_round` | Round Hay Bale | ✅ Yes | — | [mat_bale_hay_round.json](materials/mat_bale_hay_round/mat_bale_hay_round.json) |
| `mat_bale_hay_square` | Square Hay Bale | ✅ Yes | — | [mat_bale_hay_square.json](materials/mat_bale_hay_square/mat_bale_hay_square.json) |
| `mat_bale_straw_round` | Round Straw Bale | ✅ Yes | — | [mat_bale_straw_round.json](materials/mat_bale_straw_round/mat_bale_straw_round.json) |
| `mat_bale_straw_square` | Square Straw Bale | ✅ Yes | — | [mat_bale_straw_square.json](materials/mat_bale_straw_square/mat_bale_straw_square.json) |
| `mat_bedding_straw` | Straw Bedding | ✅ Yes | — | [mat_bedding_straw.json](materials/mat_bedding_straw/mat_bedding_straw.json) |
| `mat_feather` | Poultry Down Feather | — | — | [mat_feather.json](materials/mat_feather/mat_feather.json) |
| `mat_fertilizer` | Fertilizer | ✅ Yes | — | [mat_fertilizer.json](materials/mat_fertilizer/mat_fertilizer.json) |
| `mat_leather` | Tanned Leather | — | — | [mat_leather.json](materials/mat_leather/mat_leather.json) |
| `mat_log_birch` | Birch Log | ✅ Yes | — | [mat_log_birch.json](materials/mat_log_birch/mat_log_birch.json) |
| `mat_log_birch_uncut_long` | Long Birch Uncut Log | ✅ Yes | — | [mat_log_birch_uncut_long.json](materials/mat_log_birch_uncut_long/mat_log_birch_uncut_long.json) |
| `mat_log_birch_uncut_medium` | Medium Birch Uncut Log | ✅ Yes | — | [mat_log_birch_uncut_medium.json](materials/mat_log_birch_uncut_medium/mat_log_birch_uncut_medium.json) |
| `mat_log_birch_uncut_small` | Small Birch Uncut Log | ✅ Yes | — | [mat_log_birch_uncut_small.json](materials/mat_log_birch_uncut_small/mat_log_birch_uncut_small.json) |
| `mat_log_maple` | Maple Log | ✅ Yes | — | [mat_log_maple.json](materials/mat_log_maple/mat_log_maple.json) |
| `mat_log_maple_uncut_long` | Long Maple Uncut Log | ✅ Yes | — | [mat_log_maple_uncut_long.json](materials/mat_log_maple_uncut_long/mat_log_maple_uncut_long.json) |
| `mat_log_maple_uncut_medium` | Medium Maple Uncut Log | ✅ Yes | — | [mat_log_maple_uncut_medium.json](materials/mat_log_maple_uncut_medium/mat_log_maple_uncut_medium.json) |
| `mat_log_maple_uncut_small` | Small Maple Uncut Log | ✅ Yes | — | [mat_log_maple_uncut_small.json](materials/mat_log_maple_uncut_small/mat_log_maple_uncut_small.json) |
| `mat_log_oak` | Oak Log | ✅ Yes | — | [mat_log_oak.json](materials/mat_log_oak/mat_log_oak.json) |
| `mat_log_oak_uncut_long` | Long Oak Uncut Log | ✅ Yes | — | [mat_log_oak_uncut_long.json](materials/mat_log_oak_uncut_long/mat_log_oak_uncut_long.json) |
| `mat_log_oak_uncut_medium` | Medium Oak Uncut Log | ✅ Yes | — | [mat_log_oak_uncut_medium.json](materials/mat_log_oak_uncut_medium/mat_log_oak_uncut_medium.json) |
| `mat_log_oak_uncut_small` | Small Oak Uncut Log | ✅ Yes | — | [mat_log_oak_uncut_small.json](materials/mat_log_oak_uncut_small/mat_log_oak_uncut_small.json) |
| `mat_log_pine` | Pine Log | ✅ Yes | — | [mat_log_pine.json](materials/mat_log_pine/mat_log_pine.json) |
| `mat_log_pine_uncut_long` | Long Pine Uncut Log | ✅ Yes | — | [mat_log_pine_uncut_long.json](materials/mat_log_pine_uncut_long/mat_log_pine_uncut_long.json) |
| `mat_log_pine_uncut_medium` | Medium Pine Uncut Log | ✅ Yes | — | [mat_log_pine_uncut_medium.json](materials/mat_log_pine_uncut_medium/mat_log_pine_uncut_medium.json) |
| `mat_log_pine_uncut_small` | Small Pine Uncut Log | ✅ Yes | — | [mat_log_pine_uncut_small.json](materials/mat_log_pine_uncut_small/mat_log_pine_uncut_small.json) |
| `mat_log_poplar_uncut_long` | Long Poplar Uncut Log | ✅ Yes | — | [mat_log_poplar_uncut_long.json](materials/mat_log_poplar_uncut_long/mat_log_poplar_uncut_long.json) |
| `mat_log_poplar_uncut_medium` | Medium Poplar Uncut Log | ✅ Yes | — | [mat_log_poplar_uncut_medium.json](materials/mat_log_poplar_uncut_medium/mat_log_poplar_uncut_medium.json) |
| `mat_log_poplar_uncut_small` | Small Poplar Uncut Log | ✅ Yes | — | [mat_log_poplar_uncut_small.json](materials/mat_log_poplar_uncut_small/mat_log_poplar_uncut_small.json) |
| `mat_log_willow` | Willow Log | ✅ Yes | — | [mat_log_willow.json](materials/mat_log_willow/mat_log_willow.json) |
| `mat_log_willowood_uncut_long` | Long Willowood Uncut Log | ✅ Yes | — | [mat_log_willowood_uncut_long.json](materials/mat_log_willowood_uncut_long/mat_log_willowood_uncut_long.json) |
| `mat_log_willowood_uncut_medium` | Medium Willowood Uncut Log | ✅ Yes | — | [mat_log_willowood_uncut_medium.json](materials/mat_log_willowood_uncut_medium/mat_log_willowood_uncut_medium.json) |
| `mat_log_willowood_uncut_small` | Small Willowood Uncut Log | ✅ Yes | — | [mat_log_willowood_uncut_small.json](materials/mat_log_willowood_uncut_small/mat_log_willowood_uncut_small.json) |
| `mat_pelt_cow` | Cow Hide Pelt | ✅ Yes | — | [mat_pelt_cow.json](materials/mat_pelt_cow/mat_pelt_cow.json) |
| `mat_pelt_goat` | Goat Skin Pelt | ✅ Yes | — | [mat_pelt_goat.json](materials/mat_pelt_goat/mat_pelt_goat.json) |
| `mat_pelt_sheep` | Sheep Fleece Pelt | ✅ Yes | — | [mat_pelt_sheep.json](materials/mat_pelt_sheep/mat_pelt_sheep.json) |
| `mat_pile_bedding_stone_large` | Large Bedding Stone Pile | ✅ Yes | — | [mat_pile_bedding_stone_large.json](materials/mat_pile_bedding_stone_large/mat_pile_bedding_stone_large.json) |
| `mat_pile_bedding_stone_medium` | Medium Bedding Stone Pile | ✅ Yes | — | [mat_pile_bedding_stone_medium.json](materials/mat_pile_bedding_stone_medium/mat_pile_bedding_stone_medium.json) |
| `mat_pile_bedding_stone_small` | Small Bedding Stone Pile | ✅ Yes | — | [mat_pile_bedding_stone_small.json](materials/mat_pile_bedding_stone_small/mat_pile_bedding_stone_small.json) |
| `mat_pile_bedding_stone_tiny` | Tiny Bedding Stone Pile | ✅ Yes | — | [mat_pile_bedding_stone_tiny.json](materials/mat_pile_bedding_stone_tiny/mat_pile_bedding_stone_tiny.json) |
| `mat_pile_dirt_large` | Large Dirt Pile | ✅ Yes | — | [mat_pile_dirt_large.json](materials/mat_pile_dirt_large/mat_pile_dirt_large.json) |
| `mat_pile_dirt_medium` | Medium Dirt Pile | ✅ Yes | — | [mat_pile_dirt_medium.json](materials/mat_pile_dirt_medium/mat_pile_dirt_medium.json) |
| `mat_pile_dirt_small` | Small Dirt Pile | ✅ Yes | — | [mat_pile_dirt_small.json](materials/mat_pile_dirt_small/mat_pile_dirt_small.json) |
| `mat_pile_dirt_tiny` | Tiny Dirt Pile | ✅ Yes | — | [mat_pile_dirt_tiny.json](materials/mat_pile_dirt_tiny/mat_pile_dirt_tiny.json) |
| `mat_pile_gravel_large` | Large Gravel Pile | ✅ Yes | — | [mat_pile_gravel_large.json](materials/mat_pile_gravel_large/mat_pile_gravel_large.json) |
| `mat_pile_gravel_medium` | Medium Gravel Pile | ✅ Yes | — | [mat_pile_gravel_medium.json](materials/mat_pile_gravel_medium/mat_pile_gravel_medium.json) |
| `mat_pile_gravel_small` | Small Gravel Pile | ✅ Yes | — | [mat_pile_gravel_small.json](materials/mat_pile_gravel_small/mat_pile_gravel_small.json) |
| `mat_pile_gravel_tiny` | Tiny Gravel Pile | ✅ Yes | — | [mat_pile_gravel_tiny.json](materials/mat_pile_gravel_tiny/mat_pile_gravel_tiny.json) |
| `mat_pile_logs_birch_large` | Large Birch Log Pile | ✅ Yes | — | [mat_pile_logs_birch_large.json](materials/mat_pile_logs_birch_large/mat_pile_logs_birch_large.json) |
| `mat_pile_logs_birch_medium` | Medium Birch Log Pile | ✅ Yes | — | [mat_pile_logs_birch_medium.json](materials/mat_pile_logs_birch_medium/mat_pile_logs_birch_medium.json) |
| `mat_pile_logs_birch_small` | Small Birch Log Pile | ✅ Yes | — | [mat_pile_logs_birch_small.json](materials/mat_pile_logs_birch_small/mat_pile_logs_birch_small.json) |
| `mat_pile_logs_maple_large` | Large Maple Log Pile | ✅ Yes | — | [mat_pile_logs_maple_large.json](materials/mat_pile_logs_maple_large/mat_pile_logs_maple_large.json) |
| `mat_pile_logs_maple_medium` | Medium Maple Log Pile | ✅ Yes | — | [mat_pile_logs_maple_medium.json](materials/mat_pile_logs_maple_medium/mat_pile_logs_maple_medium.json) |
| `mat_pile_logs_maple_small` | Small Maple Log Pile | ✅ Yes | — | [mat_pile_logs_maple_small.json](materials/mat_pile_logs_maple_small/mat_pile_logs_maple_small.json) |
| `mat_pile_logs_oak_large` | Large Oak Log Pile | ✅ Yes | — | [mat_pile_logs_oak_large.json](materials/mat_pile_logs_oak_large/mat_pile_logs_oak_large.json) |
| `mat_pile_logs_oak_medium` | Medium Oak Log Pile | ✅ Yes | — | [mat_pile_logs_oak_medium.json](materials/mat_pile_logs_oak_medium/mat_pile_logs_oak_medium.json) |
| `mat_pile_logs_oak_small` | Small Oak Log Pile | ✅ Yes | — | [mat_pile_logs_oak_small.json](materials/mat_pile_logs_oak_small/mat_pile_logs_oak_small.json) |
| `mat_pile_logs_pine_large` | Large Pine Log Pile | ✅ Yes | — | [mat_pile_logs_pine_large.json](materials/mat_pile_logs_pine_large/mat_pile_logs_pine_large.json) |
| `mat_pile_logs_pine_medium` | Medium Pine Log Pile | ✅ Yes | — | [mat_pile_logs_pine_medium.json](materials/mat_pile_logs_pine_medium/mat_pile_logs_pine_medium.json) |
| `mat_pile_logs_pine_small` | Small Pine Log Pile | ✅ Yes | — | [mat_pile_logs_pine_small.json](materials/mat_pile_logs_pine_small/mat_pile_logs_pine_small.json) |
| `mat_pile_logs_poplar_large` | Large Poplar Log Pile | ✅ Yes | — | [mat_pile_logs_poplar_large.json](materials/mat_pile_logs_poplar_large/mat_pile_logs_poplar_large.json) |
| `mat_pile_logs_poplar_medium` | Medium Poplar Log Pile | ✅ Yes | — | [mat_pile_logs_poplar_medium.json](materials/mat_pile_logs_poplar_medium/mat_pile_logs_poplar_medium.json) |
| `mat_pile_logs_poplar_small` | Small Poplar Log Pile | ✅ Yes | — | [mat_pile_logs_poplar_small.json](materials/mat_pile_logs_poplar_small/mat_pile_logs_poplar_small.json) |
| `mat_pile_logs_willow_large` | Large Willowood Log Pile | ✅ Yes | — | [mat_pile_logs_willow_large.json](materials/mat_pile_logs_willow_large/mat_pile_logs_willow_large.json) |
| `mat_pile_logs_willow_medium` | Medium Willowood Log Pile | ✅ Yes | — | [mat_pile_logs_willow_medium.json](materials/mat_pile_logs_willow_medium/mat_pile_logs_willow_medium.json) |
| `mat_pile_logs_willow_small` | Small Willowood Log Pile | ✅ Yes | — | [mat_pile_logs_willow_small.json](materials/mat_pile_logs_willow_small/mat_pile_logs_willow_small.json) |
| `mat_pile_mulch_large` | Large Mulch Pile | ✅ Yes | — | [mat_pile_mulch_large.json](materials/mat_pile_mulch_large/mat_pile_mulch_large.json) |
| `mat_pile_mulch_medium` | Medium Mulch Pile | ✅ Yes | — | [mat_pile_mulch_medium.json](materials/mat_pile_mulch_medium/mat_pile_mulch_medium.json) |
| `mat_pile_mulch_small` | Small Mulch Pile | ✅ Yes | — | [mat_pile_mulch_small.json](materials/mat_pile_mulch_small/mat_pile_mulch_small.json) |
| `mat_pile_mulch_tiny` | Tiny Mulch Pile | ✅ Yes | — | [mat_pile_mulch_tiny.json](materials/mat_pile_mulch_tiny/mat_pile_mulch_tiny.json) |
| `mat_pile_sand_large` | Large Sand Pile | ✅ Yes | — | [mat_pile_sand_large.json](materials/mat_pile_sand_large/mat_pile_sand_large.json) |
| `mat_pile_sand_medium` | Medium Sand Pile | ✅ Yes | — | [mat_pile_sand_medium.json](materials/mat_pile_sand_medium/mat_pile_sand_medium.json) |
| `mat_pile_sand_small` | Small Sand Pile | ✅ Yes | — | [mat_pile_sand_small.json](materials/mat_pile_sand_small/mat_pile_sand_small.json) |
| `mat_pile_sand_tiny` | Tiny Sand Pile | ✅ Yes | — | [mat_pile_sand_tiny.json](materials/mat_pile_sand_tiny/mat_pile_sand_tiny.json) |
| `mat_rope` | Rope | ✅ Yes | — | [mat_rope.json](materials/mat_rope/mat_rope.json) |
| `mat_scoop_bedding_stone` | Shovelful of Bedding Stone | — | — | [mat_scoop_bedding_stone.json](materials/mat_scoop_bedding_stone/mat_scoop_bedding_stone.json) |
| `mat_scoop_dirt` | Shovelful of Dirt | — | — | [mat_scoop_dirt.json](materials/mat_scoop_dirt/mat_scoop_dirt.json) |
| `mat_scoop_gravel` | Shovelful of Gravel | — | — | [mat_scoop_gravel.json](materials/mat_scoop_gravel/mat_scoop_gravel.json) |
| `mat_scoop_manure` | Shovelful of Manure | — | — | [mat_scoop_manure.json](materials/mat_scoop_manure/mat_scoop_manure.json) |
| `mat_scoop_mulch` | Shovelful of Mulch | — | — | [mat_scoop_mulch.json](materials/mat_scoop_mulch/mat_scoop_mulch.json) |
| `mat_scoop_sand` | Shovelful of Sand | — | — | [mat_scoop_sand.json](materials/mat_scoop_sand/mat_scoop_sand.json) |
| `mat_stone` | Stone | ✅ Yes | — | [mat_stone.json](materials/mat_stone/mat_stone.json) |
| `mat_wood_logs_stack` | Wood Logs Stack | ✅ Yes | — | [mat_wood_logs_stack.json](materials/mat_wood_logs_stack/mat_wood_logs_stack.json) |
| `mat_wool_fleece` | Wool Fleece | ✅ Yes | — | [mat_wool_fleece.json](materials/mat_wool_fleece/mat_wool_fleece.json) |

### 📂 [Ingredients](ingredients/) (67 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `ingredient_alfalfa` | Alfalfa Hay | ✅ Yes | — | [ingredient_alfalfa.json](ingredients/ingredient_alfalfa/ingredient_alfalfa.json) |
| `ingredient_bacon` | Bacon | — | — | [ingredient_bacon.json](ingredients/ingredient_bacon/ingredient_bacon.json) |
| `ingredient_baking_powder` | Baking Powder | ✅ Yes | — | [ingredient_baking_powder.json](ingredients/ingredient_baking_powder/ingredient_baking_powder.json) |
| `ingredient_baking_powder_5kg` | Bulk Baking Powder | ✅ Yes | — | [ingredient_baking_powder_5kg.json](ingredients/ingredient_baking_powder_5kg/ingredient_baking_powder_5kg.json) |
| `ingredient_barley` | Barley Grain | ✅ Yes | — | [ingredient_barley.json](ingredients/ingredient_barley/ingredient_barley.json) |
| `ingredient_barley_flour` | Barley Flour | ✅ Yes | — | [ingredient_barley_flour.json](ingredients/ingredient_barley_flour/ingredient_barley_flour.json) |
| `ingredient_barley_flour_5kg` | Bulk Barley Flour | ✅ Yes | — | [ingredient_barley_flour_5kg.json](ingredients/ingredient_barley_flour_5kg/ingredient_barley_flour_5kg.json) |
| `ingredient_beef` | Raw Beef Cut | ✅ Yes | — | [ingredient_beef.json](ingredients/ingredient_beef/ingredient_beef.json) |
| `ingredient_butter` | Butter | ✅ Yes | — | [ingredient_butter.json](ingredients/ingredient_butter/ingredient_butter.json) |
| `ingredient_canola` | Canola Seed | ✅ Yes | — | [ingredient_canola.json](ingredients/ingredient_canola/ingredient_canola.json) |
| `ingredient_chicken` | Raw Chicken Breast | ✅ Yes | — | [ingredient_chicken.json](ingredients/ingredient_chicken/ingredient_chicken.json) |
| `ingredient_corn` | Sweet Yellow Corn | ✅ Yes | — | [ingredient_corn.json](ingredients/ingredient_corn/ingredient_corn.json) |
| `ingredient_corn_flour` | Corn Flour | ✅ Yes | — | [ingredient_corn_flour.json](ingredients/ingredient_corn_flour/ingredient_corn_flour.json) |
| `ingredient_corn_flour_5kg` | Bulk Corn Flour | ✅ Yes | — | [ingredient_corn_flour_5kg.json](ingredients/ingredient_corn_flour_5kg/ingredient_corn_flour_5kg.json) |
| `ingredient_cornmeal` | Cornmeal | ✅ Yes | — | [ingredient_cornmeal.json](ingredients/ingredient_cornmeal/ingredient_cornmeal.json) |
| `ingredient_cornmeal_5kg` | Bulk Cornmeal | ✅ Yes | — | [ingredient_cornmeal_5kg.json](ingredients/ingredient_cornmeal_5kg/ingredient_cornmeal_5kg.json) |
| `ingredient_cotton` | Cotton | ✅ Yes | — | [ingredient_cotton.json](ingredients/ingredient_cotton/ingredient_cotton.json) |
| `ingredient_cracked_wheat` | Cracked Wheat | ✅ Yes | — | [ingredient_cracked_wheat.json](ingredients/ingredient_cracked_wheat/ingredient_cracked_wheat.json) |
| `ingredient_cracked_wheat_5kg` | Bulk Cracked Wheat | ✅ Yes | — | [ingredient_cracked_wheat_5kg.json](ingredients/ingredient_cracked_wheat_5kg/ingredient_cracked_wheat_5kg.json) |
| `ingredient_egg` | Fresh Farm Egg | ✅ Yes | — | [ingredient_egg.json](ingredients/ingredient_egg/ingredient_egg.json) |
| `ingredient_fillet_bass` | Bass Fillet | ✅ Yes | — | [ingredient_fillet_bass.json](ingredients/ingredient_fillet_bass/ingredient_fillet_bass.json) |
| `ingredient_fillet_catfish` | Catfish Fillet | ✅ Yes | — | [ingredient_fillet_catfish.json](ingredients/ingredient_fillet_catfish/ingredient_fillet_catfish.json) |
| `ingredient_fillet_crappie` | Crappie Fillet | ✅ Yes | — | [ingredient_fillet_crappie.json](ingredients/ingredient_fillet_crappie/ingredient_fillet_crappie.json) |
| `ingredient_fillet_salmon` | Salmon Fillet | ✅ Yes | — | [ingredient_fillet_salmon.json](ingredients/ingredient_fillet_salmon/ingredient_fillet_salmon.json) |
| `ingredient_fillet_trout` | Trout Fillet | ✅ Yes | — | [ingredient_fillet_trout.json](ingredients/ingredient_fillet_trout/ingredient_fillet_trout.json) |
| `ingredient_fillet_walleye` | Walleye Fillet | ✅ Yes | — | [ingredient_fillet_walleye.json](ingredients/ingredient_fillet_walleye/ingredient_fillet_walleye.json) |
| `ingredient_flax` | Flax Stems | ✅ Yes | — | [ingredient_flax.json](ingredients/ingredient_flax/ingredient_flax.json) |
| `ingredient_flax_meal` | Flax Meal | ✅ Yes | — | [ingredient_flax_meal.json](ingredients/ingredient_flax_meal/ingredient_flax_meal.json) |
| `ingredient_flax_meal_5kg` | Bulk Flax Meal | ✅ Yes | — | [ingredient_flax_meal_5kg.json](ingredients/ingredient_flax_meal_5kg/ingredient_flax_meal_5kg.json) |
| `ingredient_flour` | All-Purpose Flour | ✅ Yes | — | [ingredient_flour.json](ingredients/ingredient_flour/ingredient_flour.json) |
| `ingredient_flour_5kg` | Bulk All-Purpose Flour | ✅ Yes | — | [ingredient_flour_5kg.json](ingredients/ingredient_flour_5kg/ingredient_flour_5kg.json) |
| `ingredient_gelatin` | Unflavored Gelatin | ✅ Yes | — | [ingredient_gelatin.json](ingredients/ingredient_gelatin/ingredient_gelatin.json) |
| `ingredient_gelatin_5kg` | Bulk Unflavored Gelatin | ✅ Yes | — | [ingredient_gelatin_5kg.json](ingredients/ingredient_gelatin_5kg/ingredient_gelatin_5kg.json) |
| `ingredient_goat_meat` | Goat Leg | — | — | [ingredient_goat_meat.json](ingredients/ingredient_goat_meat/ingredient_goat_meat.json) |
| `ingredient_grits` | Grits | ✅ Yes | — | [ingredient_grits.json](ingredients/ingredient_grits/ingredient_grits.json) |
| `ingredient_grits_5kg` | Bulk Grits | ✅ Yes | — | [ingredient_grits_5kg.json](ingredients/ingredient_grits_5kg/ingredient_grits_5kg.json) |
| `ingredient_ground_beef` | Ground Beef | — | — | [ingredient_ground_beef.json](ingredients/ingredient_ground_beef/ingredient_ground_beef.json) |
| `ingredient_ham` | Whole Ham | — | — | [ingredient_ham.json](ingredients/ingredient_ham/ingredient_ham.json) |
| `ingredient_herbs` | Fresh Culinary Herbs | ✅ Yes | — | [ingredient_herbs.json](ingredients/ingredient_herbs/ingredient_herbs.json) |
| `ingredient_hops` | Hops Cones | ✅ Yes | — | [ingredient_hops.json](ingredients/ingredient_hops/ingredient_hops.json) |
| `ingredient_lamb_chop` | Lamb Rib Chop | — | — | [ingredient_lamb_chop.json](ingredients/ingredient_lamb_chop/ingredient_lamb_chop.json) |
| `ingredient_oat_flour` | Oat Flour | ✅ Yes | — | [ingredient_oat_flour.json](ingredients/ingredient_oat_flour/ingredient_oat_flour.json) |
| `ingredient_oat_flour_5kg` | Bulk Oat Flour | ✅ Yes | — | [ingredient_oat_flour_5kg.json](ingredients/ingredient_oat_flour_5kg/ingredient_oat_flour_5kg.json) |
| `ingredient_oats` | Oat Grain | ✅ Yes | — | [ingredient_oats.json](ingredients/ingredient_oats/ingredient_oats.json) |
| `ingredient_pasta` | Dry Pasta | ✅ Yes | — | [ingredient_pasta.json](ingredients/ingredient_pasta/ingredient_pasta.json) |
| `ingredient_pasta_5kg` | Bulk Dry Pasta | ✅ Yes | — | [ingredient_pasta_5kg.json](ingredients/ingredient_pasta_5kg/ingredient_pasta_5kg.json) |
| `ingredient_pasta_sauce` | Pasta Sauce | ✅ Yes | — | [ingredient_pasta_sauce.json](ingredients/ingredient_pasta_sauce/ingredient_pasta_sauce.json) |
| `ingredient_pearl_barley` | Pearl Barley | ✅ Yes | — | [ingredient_pearl_barley.json](ingredients/ingredient_pearl_barley/ingredient_pearl_barley.json) |
| `ingredient_pearl_barley_5kg` | Bulk Pearl Barley | ✅ Yes | — | [ingredient_pearl_barley_5kg.json](ingredients/ingredient_pearl_barley_5kg/ingredient_pearl_barley_5kg.json) |
| `ingredient_pork` | Raw Pork Chop | ✅ Yes | — | [ingredient_pork.json](ingredients/ingredient_pork/ingredient_pork.json) |
| `ingredient_pork_chop` | Bone-In Pork Chop | — | — | [ingredient_pork_chop.json](ingredients/ingredient_pork_chop/ingredient_pork_chop.json) |
| `ingredient_rolled_oats` | Rolled Oats | ✅ Yes | — | [ingredient_rolled_oats.json](ingredients/ingredient_rolled_oats/ingredient_rolled_oats.json) |
| `ingredient_rolled_oats_5kg` | Bulk Rolled Oats | ✅ Yes | — | [ingredient_rolled_oats_5kg.json](ingredients/ingredient_rolled_oats_5kg/ingredient_rolled_oats_5kg.json) |
| `ingredient_salt` | Table Salt | ✅ Yes | — | [ingredient_salt.json](ingredients/ingredient_salt/ingredient_salt.json) |
| `ingredient_salt_5kg` | Bulk Table Salt | ✅ Yes | — | [ingredient_salt_5kg.json](ingredients/ingredient_salt_5kg/ingredient_salt_5kg.json) |
| `ingredient_sausage` | Pork Sausage | — | — | [ingredient_sausage.json](ingredients/ingredient_sausage/ingredient_sausage.json) |
| `ingredient_soy_flour` | Soy Flour | ✅ Yes | — | [ingredient_soy_flour.json](ingredients/ingredient_soy_flour/ingredient_soy_flour.json) |
| `ingredient_soy_flour_5kg` | Bulk Soy Flour | ✅ Yes | — | [ingredient_soy_flour_5kg.json](ingredients/ingredient_soy_flour_5kg/ingredient_soy_flour_5kg.json) |
| `ingredient_soybeans` | Soybeans | ✅ Yes | — | [ingredient_soybeans.json](ingredients/ingredient_soybeans/ingredient_soybeans.json) |
| `ingredient_steak` | Ribeye Steak | — | — | [ingredient_steak.json](ingredients/ingredient_steak/ingredient_steak.json) |
| `ingredient_sugar` | Granulated Sugar | ✅ Yes | — | [ingredient_sugar.json](ingredients/ingredient_sugar/ingredient_sugar.json) |
| `ingredient_sugar_5kg` | Bulk Granulated Sugar | ✅ Yes | — | [ingredient_sugar_5kg.json](ingredients/ingredient_sugar_5kg/ingredient_sugar_5kg.json) |
| `ingredient_sunflower` | Sunflower Heads | ✅ Yes | — | [ingredient_sunflower.json](ingredients/ingredient_sunflower/ingredient_sunflower.json) |
| `ingredient_tobacco` | Tobacco Leaf | ✅ Yes | — | [ingredient_tobacco.json](ingredients/ingredient_tobacco/ingredient_tobacco.json) |
| `ingredient_wheat` | Milled Wheat Grain | ✅ Yes | — | [ingredient_wheat.json](ingredients/ingredient_wheat/ingredient_wheat.json) |
| `ingredient_yeast` | Active Dry Yeast | ✅ Yes | — | [ingredient_yeast.json](ingredients/ingredient_yeast/ingredient_yeast.json) |
| `ingredient_yeast_5kg` | Bulk Active Dry Yeast | ✅ Yes | — | [ingredient_yeast_5kg.json](ingredients/ingredient_yeast_5kg/ingredient_yeast_5kg.json) |

### 📂 [Liquids](liquids/) (60 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `liquid_antifreeze` | Antifreeze | — | — | [liquid_antifreeze.json](liquids/liquid_antifreeze/liquid_antifreeze.json) |
| `liquid_apple_cider` | Apple Cider | — | — | [liquid_apple_cider.json](liquids/liquid_apple_cider/liquid_apple_cider.json) |
| `liquid_bar_chain_oil` | Bar and Chain Oil | — | — | [liquid_bar_chain_oil.json](liquids/liquid_bar_chain_oil/liquid_bar_chain_oil.json) |
| `liquid_canola_oil` | Canola Oil | — | — | [liquid_canola_oil.json](liquids/liquid_canola_oil/liquid_canola_oil.json) |
| `liquid_corn_oil` | Corn Oil | — | — | [liquid_corn_oil.json](liquids/liquid_corn_oil/liquid_corn_oil.json) |
| `liquid_cottonseed_oil` | Cottonseed Oil | — | — | [liquid_cottonseed_oil.json](liquids/liquid_cottonseed_oil/liquid_cottonseed_oil.json) |
| `liquid_cream` | Cream | — | — | [liquid_cream.json](liquids/liquid_cream/liquid_cream.json) |
| `liquid_diesel` | Diesel Fuel | — | — | [liquid_diesel.json](liquids/liquid_diesel/liquid_diesel.json) |
| `liquid_flax_oil` | Flaxseed Oil | — | — | [liquid_flax_oil.json](liquids/liquid_flax_oil/liquid_flax_oil.json) |
| `liquid_gasoline` | Gasoline | — | — | [liquid_gasoline.json](liquids/liquid_gasoline/liquid_gasoline.json) |
| `liquid_gear_oil` | Gear Oil | — | — | [liquid_gear_oil.json](liquids/liquid_gear_oil/liquid_gear_oil.json) |
| `liquid_goat_milk` | Goat Milk | — | — | [liquid_goat_milk.json](liquids/liquid_goat_milk/liquid_goat_milk.json) |
| `liquid_greywater` | Greywater | — | — | [liquid_greywater.json](liquids/liquid_greywater/liquid_greywater.json) |
| `liquid_hazelnut_butter` | Hazelnut Butter | — | — | [liquid_hazelnut_butter.json](liquids/liquid_hazelnut_butter/liquid_hazelnut_butter.json) |
| `liquid_honey` | Honey | — | — | [liquid_honey.json](liquids/liquid_honey/liquid_honey.json) |
| `liquid_hydraulic_fluid` | Hydraulic Fluid | — | — | [liquid_hydraulic_fluid.json](liquids/liquid_hydraulic_fluid/liquid_hydraulic_fluid.json) |
| `liquid_jam_apricot` | Apricot Jam | — | — | [liquid_jam_apricot.json](liquids/liquid_jam_apricot/liquid_jam_apricot.json) |
| `liquid_jam_blueberry` | Blueberry Jam | — | — | [liquid_jam_blueberry.json](liquids/liquid_jam_blueberry/liquid_jam_blueberry.json) |
| `liquid_jam_cherry` | Cherry Jam | — | — | [liquid_jam_cherry.json](liquids/liquid_jam_cherry/liquid_jam_cherry.json) |
| `liquid_jam_elderberry` | Elderberry Jam | — | — | [liquid_jam_elderberry.json](liquids/liquid_jam_elderberry/liquid_jam_elderberry.json) |
| `liquid_jam_fig` | Fig Jam | — | — | [liquid_jam_fig.json](liquids/liquid_jam_fig/liquid_jam_fig.json) |
| `liquid_jam_grape` | Grape Jam | — | — | [liquid_jam_grape.json](liquids/liquid_jam_grape/liquid_jam_grape.json) |
| `liquid_jam_haskap` | Haskap Jam | — | — | [liquid_jam_haskap.json](liquids/liquid_jam_haskap/liquid_jam_haskap.json) |
| `liquid_jam_huckleberry` | Huckleberry Jam | — | — | [liquid_jam_huckleberry.json](liquids/liquid_jam_huckleberry/liquid_jam_huckleberry.json) |
| `liquid_jam_peach` | Peach Jam | — | — | [liquid_jam_peach.json](liquids/liquid_jam_peach/liquid_jam_peach.json) |
| `liquid_jam_pear` | Pear Jam | — | — | [liquid_jam_pear.json](liquids/liquid_jam_pear/liquid_jam_pear.json) |
| `liquid_jam_plum` | Plum Jam | — | — | [liquid_jam_plum.json](liquids/liquid_jam_plum/liquid_jam_plum.json) |
| `liquid_jam_raspberry` | Raspberry Jam | — | — | [liquid_jam_raspberry.json](liquids/liquid_jam_raspberry/liquid_jam_raspberry.json) |
| `liquid_jam_strawberry` | Strawberry Jam | — | — | [liquid_jam_strawberry.json](liquids/liquid_jam_strawberry/liquid_jam_strawberry.json) |
| `liquid_juice_apple` | Apple Juice | — | — | [liquid_juice_apple.json](liquids/liquid_juice_apple/liquid_juice_apple.json) |
| `liquid_juice_apricot` | Apricot Juice | — | — | [liquid_juice_apricot.json](liquids/liquid_juice_apricot/liquid_juice_apricot.json) |
| `liquid_juice_cherry` | Cherry Juice | — | — | [liquid_juice_cherry.json](liquids/liquid_juice_cherry/liquid_juice_cherry.json) |
| `liquid_juice_grape` | Grape Juice | — | — | [liquid_juice_grape.json](liquids/liquid_juice_grape/liquid_juice_grape.json) |
| `liquid_juice_lemon` | Lemon Juice | — | — | [liquid_juice_lemon.json](liquids/liquid_juice_lemon/liquid_juice_lemon.json) |
| `liquid_juice_orange` | Orange Juice | — | — | [liquid_juice_orange.json](liquids/liquid_juice_orange/liquid_juice_orange.json) |
| `liquid_juice_peach` | Peach Juice | — | — | [liquid_juice_peach.json](liquids/liquid_juice_peach/liquid_juice_peach.json) |
| `liquid_juice_pear` | Pear Juice | — | — | [liquid_juice_pear.json](liquids/liquid_juice_pear/liquid_juice_pear.json) |
| `liquid_juice_plum` | Plum Juice | — | — | [liquid_juice_plum.json](liquids/liquid_juice_plum/liquid_juice_plum.json) |
| `liquid_juice_strawberry` | Strawberry Juice | — | — | [liquid_juice_strawberry.json](liquids/liquid_juice_strawberry/liquid_juice_strawberry.json) |
| `liquid_juice_tomato` | Tomato Juice | — | — | [liquid_juice_tomato.json](liquids/liquid_juice_tomato/liquid_juice_tomato.json) |
| `liquid_juice_watermelon` | Watermelon Juice | — | — | [liquid_juice_watermelon.json](liquids/liquid_juice_watermelon/liquid_juice_watermelon.json) |
| `liquid_kerosene` | Kerosene | — | — | [liquid_kerosene.json](liquids/liquid_kerosene/liquid_kerosene.json) |
| `liquid_manure_slurry` | Manure Slurry | — | — | [liquid_manure_slurry.json](liquids/liquid_manure_slurry/liquid_manure_slurry.json) |
| `liquid_maple_sap` | Maple Sap | — | — | [liquid_maple_sap.json](liquids/liquid_maple_sap/liquid_maple_sap.json) |
| `liquid_maple_syrup` | Maple Syrup | — | — | [liquid_maple_syrup.json](liquids/liquid_maple_syrup/liquid_maple_syrup.json) |
| `liquid_milk` | Cow Milk | — | — | [liquid_milk.json](liquids/liquid_milk/liquid_milk.json) |
| `liquid_motor_oil` | Motor Oil | — | — | [liquid_motor_oil.json](liquids/liquid_motor_oil/liquid_motor_oil.json) |
| `liquid_olive_oil` | Olive Oil | — | — | [liquid_olive_oil.json](liquids/liquid_olive_oil/liquid_olive_oil.json) |
| `liquid_peanut_butter` | Peanut Butter | — | — | [liquid_peanut_butter.json](liquids/liquid_peanut_butter/liquid_peanut_butter.json) |
| `liquid_peanut_oil` | Peanut Oil | — | — | [liquid_peanut_oil.json](liquids/liquid_peanut_oil/liquid_peanut_oil.json) |
| `liquid_pecan_butter` | Pecan Butter | — | — | [liquid_pecan_butter.json](liquids/liquid_pecan_butter/liquid_pecan_butter.json) |
| `liquid_propane` | Liquid Propane | — | — | [liquid_propane.json](liquids/liquid_propane/liquid_propane.json) |
| `liquid_sewage` | Sewage | — | — | [liquid_sewage.json](liquids/liquid_sewage/liquid_sewage.json) |
| `liquid_soybean_oil` | Soybean Oil | — | — | [liquid_soybean_oil.json](liquids/liquid_soybean_oil/liquid_soybean_oil.json) |
| `liquid_sunflower_oil` | Sunflower Oil | — | — | [liquid_sunflower_oil.json](liquids/liquid_sunflower_oil/liquid_sunflower_oil.json) |
| `liquid_two_stroke_mix` | Two-Stroke Fuel Mix | — | — | [liquid_two_stroke_mix.json](liquids/liquid_two_stroke_mix/liquid_two_stroke_mix.json) |
| `liquid_vegetable_oil` | Vegetable Oil | — | — | [liquid_vegetable_oil.json](liquids/liquid_vegetable_oil/liquid_vegetable_oil.json) |
| `liquid_walnut_butter` | Walnut Butter | — | — | [liquid_walnut_butter.json](liquids/liquid_walnut_butter/liquid_walnut_butter.json) |
| `liquid_water` | Water | — | — | [liquid_water.json](liquids/liquid_water/liquid_water.json) |
| `liquid_water_raw` | Raw Water | — | — | [liquid_water_raw.json](liquids/liquid_water_raw/liquid_water_raw.json) |
