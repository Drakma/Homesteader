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

Total Indexed Items: **538**

| Category | Items Count | Description |
| :--- | :---: | :--- |
| [**Structures**](structures/) | 18 items | Placed world buildings, farmhouses, cabins, barns, silos, sheds, greenhouses, coops, shelters, and towers. |
| [**Building**](building/) | 85 items | Modular building materials, framing, doors, windows, and hardware supplies. |
| [**Farming**](farming/) | 15 items | Crops, seeds, produce, fertilizers, irrigation, and agricultural machinery. |
| [**Ranching**](ranching/) | 27 items | Livestock species, animal feed/hay, butchered meats, hides/pelts, and animal husbandry housing. |
| [**Logging**](logging/) | 41 items | Modular forest trees (large/medium/small), saplings, timber logs, firewood, woodchips, and sap spigots. |
| [**Fishing**](fishing/) | 19 items | Whole fish species, precision meat fillets, fishing rods, lures, and tackle. |
| [**Tools**](tools/) | 54 items | Hand tools, power gear, crafting implements, and surveying/measuring equipment. |
| [**Electricity**](electricity/) | 37 items | Solar photovoltaic panels, wind turbines, fuel generators, battery banks, and high-voltage wiring. |
| [**Water**](water/) | 31 items | Aquifer wells, pressure tanks, poly cisterns, rain catchment barrels, and filtration racks. |
| [**Waste**](waste/) | 19 items | Septic infrastructure, compost systems, composting toilets, and organic waste management. |
| [**Internet**](internet/) | 16 items | Starlink satellite dishes, Wi-Fi 6 mesh distribution routers, and weather-rated cabling. |
| [**Hud**](hud/) | 31 items | Player vitals, coins, energy/stamina bars, clock dials, and interface elements. |
| [**Ground**](ground/) | 18 items | Modular terrain grid tiles (1m x 1m), road pavements, and scatter clutter props. |
| [**Food**](food/) | 26 items | Edible harvested produce, pantry staples, fresh eggs, dairy, and whole foods. |
| [**Fuel**](fuel/) | 17 items | Liquid hydrocarbons, compressed gas tanks, bulk fuel storage, firewood cords, and transfer equipment. |
| [**Materials**](materials/) | 69 items | Raw construction materials, timber log piles, aggregate bulk piles, textiles, hides, and foundational crafting resources. |
| [**Ingredients**](ingredients/) | 15 items | Raw cooking and crafting inputs: butchered meats, fish fillets, eggs, dairy, harvested grains, and crop-derived ingredients. |

### Shared System & World Asset Directories

| System Directory | Contents | Specification |
| :--- | :--- | :--- |
| [**Ground**](ground/) | 20 Seamless PBR Texture Sets (BaseColor, Normal, ORM), 16 Landscape Blend Masks, 20 Modular Grid Tiles (`SM_Tile_*`), and 10 Scatter Clutter Meshes. | [`ground/README.md`](ground/README.md) |
| [**Textures**](textures/) | Master 3D low-poly color palette atlas (`T_Homesteader_Palette.png`) and entity skeletal mesh base colors (`animals/`). | [`textures/README.md`](textures/README.md) |

---

### 📂 [Structures](structures/) (18 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `3_bay_truck_garage` | 3 Bay Truck Garage | — | — | [3_bay_truck_garage.json](structures/3_bay_truck_garage/3_bay_truck_garage.json) |
| `barn` | Barn | — | — | [barn.json](structures/barn/barn.json) |
| `chicken_coop` | Chicken Coop | — | — | [chicken_coop.json](structures/chicken_coop/chicken_coop.json) |
| `farmhouse` | Farmhouse | — | — | [farmhouse.json](structures/farmhouse/farmhouse.json) |
| `greenhouse` | Greenhouse | — | — | [greenhouse.json](structures/greenhouse/greenhouse.json) |
| `large_log_cabin` | Large Log Cabin | — | — | [large_log_cabin.json](structures/large_log_cabin/large_log_cabin.json) |
| `large_metal_garage` | Large Metal Garage | — | — | [large_metal_garage.json](structures/large_metal_garage/large_metal_garage.json) |
| `small_cabin` | Small Cabin | — | — | [small_cabin.json](structures/small_cabin/small_cabin.json) |
| `stable` | Stable | — | — | [stable.json](structures/stable/stable.json) |
| `starter_house` | Starter House | — | — | [starter_house.json](structures/starter_house/starter_house.json) |
| `struct_camper_rv` | Travel Trailer RV | ✅ Yes | — | [struct_camper_rv.json](structures/struct_camper_rv/struct_camper_rv.json) |
| `struct_camper_teardrop` | Teardrop Camper | ✅ Yes | — | [struct_camper_teardrop.json](structures/struct_camper_teardrop/struct_camper_teardrop.json) |
| `struct_garage_truck_3bay` | 3 Bay Truck Garage | ✅ Yes | — | [struct_garage_truck_3bay.json](structures/struct_garage_truck_3bay/struct_garage_truck_3bay.json) |
| `struct_shed` | Tool Shed | ✅ Yes | — | [struct_shed.json](structures/struct_shed/struct_shed.json) |
| `struct_silo` | Grain Silo | ✅ Yes | — | [struct_silo.json](structures/struct_silo/struct_silo.json) |
| `struct_tent_canvas` | Canvas Wall Tent | ✅ Yes | — | [struct_tent_canvas.json](structures/struct_tent_canvas/struct_tent_canvas.json) |
| `struct_tent_dome` | Dome Tent | ✅ Yes | — | [struct_tent_dome.json](structures/struct_tent_dome/struct_tent_dome.json) |
| `struct_woodshed` | Woodshed | ✅ Yes | — | [struct_woodshed.json](structures/struct_woodshed/struct_woodshed.json) |

### 📂 [Building](building/) (85 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `box_large_brown` | Large Brown Box | — | — | [box_large_brown.json](building/box_large_brown/box_large_brown.json) |
| `box_large_tan` | Large Kraft Box | — | — | [box_large_tan.json](building/box_large_tan/box_large_tan.json) |
| `box_large_white` | Large White Box | — | — | [box_large_white.json](building/box_large_white/box_large_white.json) |
| `box_medium_brown` | Medium Brown Box | — | — | [box_medium_brown.json](building/box_medium_brown/box_medium_brown.json) |
| `box_medium_tan` | Medium Kraft Box | — | — | [box_medium_tan.json](building/box_medium_tan/box_medium_tan.json) |
| `box_medium_white` | Medium White Box | — | — | [box_medium_white.json](building/box_medium_white/box_medium_white.json) |
| `box_small_brown` | Small Brown Box | — | — | [box_small_brown.json](building/box_small_brown/box_small_brown.json) |
| `box_small_tan` | Small Kraft Box | — | — | [box_small_tan.json](building/box_small_tan/box_small_tan.json) |
| `box_small_white` | Small White Box | — | — | [box_small_white.json](building/box_small_white/box_small_white.json) |
| `building_chinking` | Chinking | ✅ Yes | — | [building_chinking.json](building/building_chinking/building_chinking.json) |
| `building_glass` | Glass Pane | — | — | [building_glass.json](building/building_glass/building_glass.json) |
| `building_insulation_fiberglass_batt` | Fiberglass Insulation Batt | — | — | [building_insulation_fiberglass_batt.json](building/building_insulation_fiberglass_batt/building_insulation_fiberglass_batt.json) |
| `building_metal` | Metal Sheet | — | — | [building_metal.json](building/building_metal/building_metal.json) |
| `building_paint_interior_wall` | Interior Wall Paint | — | — | [building_paint_interior_wall.json](building/building_paint_interior_wall/building_paint_interior_wall.json) |
| `building_pallet_wood` | Mat Pallet Wood | ✅ Yes | — | [building_pallet_wood.json](building/building_pallet_wood/building_pallet_wood.json) |
| `building_rebar_steel_bundle` | Rebar Bundle | ✅ Yes | — | [building_rebar_steel_bundle.json](building/building_rebar_steel_bundle/building_rebar_steel_bundle.json) |
| `building_steel_frame_beam` | Steel Rigid Frame Beam | ✅ Yes | — | [building_steel_frame_beam.json](building/building_steel_frame_beam/building_steel_frame_beam.json) |
| `building_steel_siding_corrugated` | Corrugated Steel Wall Siding | ✅ Yes | — | [building_steel_siding_corrugated.json](building/building_steel_siding_corrugated/building_steel_siding_corrugated.json) |
| `building_steel_stud_framing` | Steel Stud (Metal Framing) | ✅ Yes | — | [building_steel_stud_framing.json](building/building_steel_stud_framing/building_steel_stud_framing.json) |
| `camp_campfire_ring` | Camp Campfire Ring | ✅ Yes | — | [camp_campfire_ring.json](building/camp_campfire_ring/camp_campfire_ring.json) |
| `camp_picnictable_wood` | Camp Picnictable Wood | ✅ Yes | — | [camp_picnictable_wood.json](building/camp_picnictable_wood/camp_picnictable_wood.json) |
| `dock_large_new` | Large New Dock | — | — | [dock_large_new.json](building/dock_large_new/dock_large_new.json) |
| `dock_large_old` | Large Old Dock | — | — | [dock_large_old.json](building/dock_large_old/dock_large_old.json) |
| `dock_small_new` | Small New Dock | — | — | [dock_small_new.json](building/dock_small_new/dock_small_new.json) |
| `dock_small_old` | Small Old Dock | — | — | [dock_small_old.json](building/dock_small_old/dock_small_old.json) |
| `drain_french_sock` | French Drain Pipe | ✅ Yes | — | [drain_french_sock.json](building/drain_french_sock/drain_french_sock.json) |
| `fence_wire` | Wire Fence Section | — | — | [fence_wire.json](building/fence_wire/fence_wire.json) |
| `fence_wood` | Wood Fence Section | — | — | [fence_wood.json](building/fence_wood/fence_wood.json) |
| `gate_metal` | Metal Farm Gate | — | — | [gate_metal.json](building/gate_metal/gate_metal.json) |
| `gate_wood` | Wood Farm Gate | — | — | [gate_wood.json](building/gate_wood/gate_wood.json) |
| `gland_cable_entry_wall` | Wall Cable Entry Gland | ✅ Yes | — | [gland_cable_entry_wall.json](building/gland_cable_entry_wall/gland_cable_entry_wall.json) |
| `hardware_gate_hinges` | Gate Strap Hinge | ✅ Yes | — | [hardware_gate_hinges.json](building/hardware_gate_hinges/hardware_gate_hinges.json) |
| `hardware_hurricane_ties` | Hurricane Ties Pair | ✅ Yes | — | [hardware_hurricane_ties.json](building/hardware_hurricane_ties/hardware_hurricane_ties.json) |
| `hardware_nails` | Hardware Nails | — | — | [hardware_nails.json](building/hardware_nails/hardware_nails.json) |
| `icon_wood_log` | Icon Wood Log | — | — | [icon_wood_log.json](building/icon_wood_log/icon_wood_log.json) |
| `insulators_tpost_pack` | T-Post Insulators Pack | ✅ Yes | — | [insulators_tpost_pack.json](building/insulators_tpost_pack/insulators_tpost_pack.json) |
| `item_hardware_deckscrews_box` | Item Hardware Deckscrews Box | ✅ Yes | — | [item_hardware_deckscrews_box.json](building/item_hardware_deckscrews_box/item_hardware_deckscrews_box.json) |
| `item_hardware_framingnails_box` | Item Hardware Framingnails Box | ✅ Yes | — | [item_hardware_framingnails_box.json](building/item_hardware_framingnails_box/item_hardware_framingnails_box.json) |
| `item_hardware_gatehinges_pair` | Item Hardware Gatehinges Pair | ✅ Yes | — | [item_hardware_gatehinges_pair.json](building/item_hardware_gatehinges_pair/item_hardware_gatehinges_pair.json) |
| `item_hardware_lagbolts_box` | Item Hardware Lagbolts Box | ✅ Yes | — | [item_hardware_lagbolts_box.json](building/item_hardware_lagbolts_box/item_hardware_lagbolts_box.json) |
| `item_hardware_rebarbundle` | Item Hardware Rebarbundle | ✅ Yes | — | [item_hardware_rebarbundle.json](building/item_hardware_rebarbundle/item_hardware_rebarbundle.json) |
| `item_spool_barbedwire` | Item Spool Barbedwire | ✅ Yes | — | [item_spool_barbedwire.json](building/item_spool_barbedwire/item_spool_barbedwire.json) |
| `item_spool_cat6_150m` | Cat6 Cable Spool (150m) | ✅ Yes | — | [item_spool_cat6_150m.json](building/item_spool_cat6_150m/item_spool_cat6_150m.json) |
| `item_spool_romex_12_2` | Item Spool Romex 12 2 | ✅ Yes | — | [item_spool_romex_12_2.json](building/item_spool_romex_12_2/item_spool_romex_12_2.json) |
| `lumber_bundle_2x10_large` | Large 2x10 Bundle | — | — | [lumber_bundle_2x10_large.json](building/lumber_bundle_2x10_large/lumber_bundle_2x10_large.json) |
| `lumber_bundle_2x10_small` | Small 2x10 Bundle | — | — | [lumber_bundle_2x10_small.json](building/lumber_bundle_2x10_small/lumber_bundle_2x10_small.json) |
| `lumber_bundle_2x4_large` | Large 2x4 Bundle | — | — | [lumber_bundle_2x4_large.json](building/lumber_bundle_2x4_large/lumber_bundle_2x4_large.json) |
| `lumber_bundle_2x4_small` | Small 2x4 Bundle | — | — | [lumber_bundle_2x4_small.json](building/lumber_bundle_2x4_small/lumber_bundle_2x4_small.json) |
| `lumber_bundle_2x6_large` | Large 2x6 Bundle | — | — | [lumber_bundle_2x6_large.json](building/lumber_bundle_2x6_large/lumber_bundle_2x6_large.json) |
| `lumber_bundle_2x6_small` | Small 2x6 Bundle | — | — | [lumber_bundle_2x6_small.json](building/lumber_bundle_2x6_small/lumber_bundle_2x6_small.json) |
| `lumber_joist_2x8` | 2x8 Joist Beam | ✅ Yes | — | [lumber_joist_2x8.json](building/lumber_joist_2x8/lumber_joist_2x8.json) |
| `lumber_post_4x4` | 4x4 Treated Post | ✅ Yes | — | [lumber_post_4x4.json](building/lumber_post_4x4/lumber_post_4x4.json) |
| `lumber_stud_2x4` | 2x4 Lumber Stud | ✅ Yes | — | [lumber_stud_2x4.json](building/lumber_stud_2x4/lumber_stud_2x4.json) |
| `masonry_brick_red` | Red Clay Brick | ✅ Yes | — | [masonry_brick_red.json](building/masonry_brick_red/masonry_brick_red.json) |
| `masonry_cinder_block` | Cinder Block | ✅ Yes | — | [masonry_cinder_block.json](building/masonry_cinder_block/masonry_cinder_block.json) |
| `masonry_concrete_bag` | 80lb Concrete Mix Bag | ✅ Yes | — | [masonry_concrete_bag.json](building/masonry_concrete_bag/masonry_concrete_bag.json) |
| `part_floor_stone_1m` | Part Floor Stone 1M | ✅ Yes | — | [part_floor_stone_1m.json](building/part_floor_stone_1m/part_floor_stone_1m.json) |
| `part_floor_wood_1m` | Part Floor Wood 1M | ✅ Yes | — | [part_floor_wood_1m.json](building/part_floor_wood_1m/part_floor_wood_1m.json) |
| `pipe_leach_perforated_4inch` | 4" Perforated Leach Pipe | ✅ Yes | — | [pipe_leach_perforated_4inch.json](building/pipe_leach_perforated_4inch/pipe_leach_perforated_4inch.json) |
| `pipe_pvc_elbow` | PVC 90-Degree Elbow | ✅ Yes | — | [pipe_pvc_elbow.json](building/pipe_pvc_elbow/pipe_pvc_elbow.json) |
| `pipe_pvc_half_inch` | 1/2" PVC Pipe | ✅ Yes | — | [pipe_pvc_half_inch.json](building/pipe_pvc_half_inch/pipe_pvc_half_inch.json) |
| `pipe_pvc_one_inch` | 1" PVC Pipe | ✅ Yes | — | [pipe_pvc_one_inch.json](building/pipe_pvc_one_inch/pipe_pvc_one_inch.json) |
| `pipe_pvc_tee` | PVC Tee Fitting | ✅ Yes | — | [pipe_pvc_tee.json](building/pipe_pvc_tee/pipe_pvc_tee.json) |
| `pipe_pvc_two_inch` | 2" PVC Pipe | ✅ Yes | — | [pipe_pvc_two_inch.json](building/pipe_pvc_two_inch/pipe_pvc_two_inch.json) |
| `pipe_sewer_solid_4inch` | 4" Sewer Pipe | ✅ Yes | — | [pipe_sewer_solid_4inch.json](building/pipe_sewer_solid_4inch/pipe_sewer_solid_4inch.json) |
| `post_wood_round_6inch` | 6" Round Wood Post | ✅ Yes | — | [post_wood_round_6inch.json](building/post_wood_round_6inch/post_wood_round_6inch.json) |
| `roofing_shingles_bundle` | Asphalt Shingles Bundle | ✅ Yes | — | [roofing_shingles_bundle.json](building/roofing_shingles_bundle/roofing_shingles_bundle.json) |
| `roofing_steel_corrugated` | Corrugated Steel Roofing | ✅ Yes | — | [roofing_steel_corrugated.json](building/roofing_steel_corrugated/roofing_steel_corrugated.json) |
| `sheet_drywall_stack_large` | Large Drywall Stack | — | — | [sheet_drywall_stack_large.json](building/sheet_drywall_stack_large/sheet_drywall_stack_large.json) |
| `sheet_drywall_stack_small` | Small Drywall Stack | — | — | [sheet_drywall_stack_small.json](building/sheet_drywall_stack_small/sheet_drywall_stack_small.json) |
| `sheet_osb_stack_large` | Large OSB Stack | — | — | [sheet_osb_stack_large.json](building/sheet_osb_stack_large/sheet_osb_stack_large.json) |
| `sheet_osb_stack_small` | Small OSB Stack | — | — | [sheet_osb_stack_small.json](building/sheet_osb_stack_small/sheet_osb_stack_small.json) |
| `sheet_plywood_cdx` | CDX Plywood Sheet | ✅ Yes | — | [sheet_plywood_cdx.json](building/sheet_plywood_cdx/sheet_plywood_cdx.json) |
| `spool_wire_barbed_4pt` | 4-Point Barbed Wire Spool | ✅ Yes | — | [spool_wire_barbed_4pt.json](building/spool_wire_barbed_4pt/spool_wire_barbed_4pt.json) |
| `spool_wire_romex_12_2` | Romex 12/2 Wire Spool | ✅ Yes | — | [spool_wire_romex_12_2.json](building/spool_wire_romex_12_2/spool_wire_romex_12_2.json) |
| `spool_wire_woven_field` | Woven Field Fence Roll | ✅ Yes | — | [spool_wire_woven_field.json](building/spool_wire_woven_field/spool_wire_woven_field.json) |
| `tape_drip_roll_300m` | 300m Drip Tape Roll | ✅ Yes | — | [tape_drip_roll_300m.json](building/tape_drip_roll_300m/tape_drip_roll_300m.json) |
| `timer_hose_digital` | Digital Hose Timer | ✅ Yes | — | [timer_hose_digital.json](building/timer_hose_digital/timer_hose_digital.json) |
| `tubing_drip_irrigation` | Drip Irrigation Tubing | ✅ Yes | — | [tubing_drip_irrigation.json](building/tubing_drip_irrigation/tubing_drip_irrigation.json) |
| `turbine_wind_3kw` | 3kW Wind Turbine | ✅ Yes | — | [turbine_wind_3kw.json](building/turbine_wind_3kw/turbine_wind_3kw.json) |
| `turbine_wind_400w` | 400W Wind Turbine | ✅ Yes | — | [turbine_wind_400w.json](building/turbine_wind_400w/turbine_wind_400w.json) |
| `valve_ball_brass` | Brass Ball Valve | ✅ Yes | — | [valve_ball_brass.json](building/valve_ball_brass/valve_ball_brass.json) |
| `valve_gate_brass` | Brass Gate Valve | ✅ Yes | — | [valve_gate_brass.json](building/valve_gate_brass/valve_gate_brass.json) |
| `valve_stock_float` | Stock Tank Float Valve | ✅ Yes | — | [valve_stock_float.json](building/valve_stock_float/valve_stock_float.json) |
| `wood_log` | Wood Log | — | — | [wood_log.json](building/wood_log/wood_log.json) |

### 📂 [Farming](farming/) (15 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `corn` | Corn Plant | — | — | [corn.json](farming/corn/corn.json) |
| `crop_dead` | Dead Crop | ✅ Yes | — | [crop_dead.json](farming/crop_dead/crop_dead.json) |
| `crop_withered` | Withered Crop | ✅ Yes | — | [crop_withered.json](farming/crop_withered/crop_withered.json) |
| `seed_carrot` | Carrot Seeds | ✅ Yes | — | [seed_carrot.json](farming/seed_carrot/seed_carrot.json) |
| `seed_corn` | Corn Seeds | ✅ Yes | — | [seed_corn.json](farming/seed_corn/seed_corn.json) |
| `seed_cotton` | Cotton Seeds | ✅ Yes | — | [seed_cotton.json](farming/seed_cotton/seed_cotton.json) |
| `seed_herb` | Herb Seeds | ✅ Yes | — | [seed_herb.json](farming/seed_herb/seed_herb.json) |
| `seed_potato` | Potato Seeds | ✅ Yes | — | [seed_potato.json](farming/seed_potato/seed_potato.json) |
| `seed_pumpkin` | Pumpkin Seeds | ✅ Yes | — | [seed_pumpkin.json](farming/seed_pumpkin/seed_pumpkin.json) |
| `seed_strawberry` | Strawberry Seeds | ✅ Yes | — | [seed_strawberry.json](farming/seed_strawberry/seed_strawberry.json) |
| `seed_sunflower` | Sunflower Seeds | ✅ Yes | — | [seed_sunflower.json](farming/seed_sunflower/seed_sunflower.json) |
| `seed_tomato` | Tomato Seeds | ✅ Yes | — | [seed_tomato.json](farming/seed_tomato/seed_tomato.json) |
| `seed_wheat` | Wheat Seeds | ✅ Yes | — | [seed_wheat.json](farming/seed_wheat/seed_wheat.json) |
| `sunflower` | Sunflower Plant | — | — | [sunflower.json](farming/sunflower/sunflower.json) |
| `wheat` | Wheat Plant | — | — | [wheat.json](farming/wheat/wheat.json) |

### 📂 [Ranching](ranching/) (27 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `animal_bull_holstein` | Holstein Bull | ✅ Yes | — | [animal_bull_holstein.json](ranching/animal_bull_holstein/animal_bull_holstein.json) |
| `animal_cat_calico` | Calico Cat | ✅ Yes | — | [animal_cat_calico.json](ranching/animal_cat_calico/animal_cat_calico.json) |
| `animal_dog_labrador` | Labrador Retriever | ✅ Yes | — | [animal_dog_labrador.json](ranching/animal_dog_labrador/animal_dog_labrador.json) |
| `animal_halter_lead_rope` | Halter & Lead Rope | ✅ Yes | — | [animal_halter_lead_rope.json](ranching/animal_halter_lead_rope/animal_halter_lead_rope.json) |
| `animal_pan_feed_rubber_55l` | Rubber Feed Pan (55L) | ✅ Yes | — | [animal_pan_feed_rubber_55l.json](ranching/animal_pan_feed_rubber_55l/animal_pan_feed_rubber_55l.json) |
| `animal_salt_lick_mineral_23kg` | 23kg Mineral Salt Lick | ✅ Yes | — | [animal_salt_lick_mineral_23kg.json](ranching/animal_salt_lick_mineral_23kg/animal_salt_lick_mineral_23kg.json) |
| `barred_chicken` | Barred Chicken | — | — | [barred_chicken.json](ranching/barred_chicken/barred_chicken.json) |
| `black_white_billy_goat` | Black White Billy Goat | — | — | [black_white_billy_goat.json](ranching/black_white_billy_goat/black_white_billy_goat.json) |
| `black_white_goat` | Black White Goat | — | — | [black_white_goat.json](ranching/black_white_goat/black_white_goat.json) |
| `brown_goat` | Brown Goat | — | — | [brown_goat.json](ranching/brown_goat/brown_goat.json) |
| `duroc_pig` | Duroc Pig | — | — | [duroc_pig.json](ranching/duroc_pig/duroc_pig.json) |
| `hampshire_pig` | Hampshire Pig | — | — | [hampshire_pig.json](ranching/hampshire_pig/hampshire_pig.json) |
| `highland_cow` | Highland Cow | — | — | [highland_cow.json](ranching/highland_cow/highland_cow.json) |
| `holstein_cow` | Holstein Cow | — | — | [holstein_cow.json](ranching/holstein_cow/holstein_cow.json) |
| `jersey_cow` | Jersey Cow | — | — | [jersey_cow.json](ranching/jersey_cow/jersey_cow.json) |
| `mat_bale_silage_round` | Round Silage Bale | — | — | [mat_bale_silage_round.json](ranching/mat_bale_silage_round/mat_bale_silage_round.json) |
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

### 📂 [Logging](logging/) (41 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `apple` | Apple Tree | — | — | [apple.json](logging/apple/apple.json) |
| `birch` | Birch Tree | — | — | [birch.json](logging/birch/birch.json) |
| `lemon` | Lemon | — | — | [lemon.json](logging/lemon/lemon.json) |
| `maple` | Maple Tree | — | — | [maple.json](logging/maple/maple.json) |
| `oak` | Oak Tree | — | — | [oak.json](logging/oak/oak.json) |
| `orange` | Orange | — | — | [orange.json](logging/orange/orange.json) |
| `pine` | Pine Tree | — | — | [pine.json](logging/pine/pine.json) |
| `plantable_birch_sapling` | Plantable Birch Sapling | ✅ Yes | — | [plantable_birch_sapling.json](logging/plantable_birch_sapling/plantable_birch_sapling.json) |
| `plantable_maple_sapling` | Plantable Maple Sapling | ✅ Yes | — | [plantable_maple_sapling.json](logging/plantable_maple_sapling/plantable_maple_sapling.json) |
| `plantable_oak_sapling` | Plantable Oak Sapling | ✅ Yes | — | [plantable_oak_sapling.json](logging/plantable_oak_sapling/plantable_oak_sapling.json) |
| `plantable_pine_sapling` | Plantable Pine Sapling | ✅ Yes | — | [plantable_pine_sapling.json](logging/plantable_pine_sapling/plantable_pine_sapling.json) |
| `plantable_poplar_sapling` | Plantable Poplar Sapling | ✅ Yes | — | [plantable_poplar_sapling.json](logging/plantable_poplar_sapling/plantable_poplar_sapling.json) |
| `plantable_sapling_apple` | Plantable Sapling Apple | ✅ Yes | — | [plantable_sapling_apple.json](logging/plantable_sapling_apple/plantable_sapling_apple.json) |
| `plantable_sapling_lemon` | Plantable Sapling Lemon | ✅ Yes | — | [plantable_sapling_lemon.json](logging/plantable_sapling_lemon/plantable_sapling_lemon.json) |
| `plantable_sapling_orange` | Plantable Sapling Orange | ✅ Yes | — | [plantable_sapling_orange.json](logging/plantable_sapling_orange/plantable_sapling_orange.json) |
| `plantable_willow_sapling` | Plantable Willow Sapling | ✅ Yes | — | [plantable_willow_sapling.json](logging/plantable_willow_sapling/plantable_willow_sapling.json) |
| `poplar` | Poplar Tree | — | — | [poplar.json](logging/poplar/poplar.json) |
| `stump_apple_large` | Stump Apple Large | ✅ Yes | — | [stump_apple_large.json](logging/stump_apple_large/stump_apple_large.json) |
| `stump_apple_medium` | Stump Apple Medium | ✅ Yes | — | [stump_apple_medium.json](logging/stump_apple_medium/stump_apple_medium.json) |
| `stump_apple_small` | Stump Apple Small | ✅ Yes | — | [stump_apple_small.json](logging/stump_apple_small/stump_apple_small.json) |
| `stump_birch_large` | Stump Birch Large | ✅ Yes | — | [stump_birch_large.json](logging/stump_birch_large/stump_birch_large.json) |
| `stump_birch_medium` | Stump Birch Medium | ✅ Yes | — | [stump_birch_medium.json](logging/stump_birch_medium/stump_birch_medium.json) |
| `stump_birch_small` | Stump Birch Small | ✅ Yes | — | [stump_birch_small.json](logging/stump_birch_small/stump_birch_small.json) |
| `stump_maple_large` | Stump Maple Large | ✅ Yes | — | [stump_maple_large.json](logging/stump_maple_large/stump_maple_large.json) |
| `stump_maple_medium` | Stump Maple Medium | ✅ Yes | — | [stump_maple_medium.json](logging/stump_maple_medium/stump_maple_medium.json) |
| `stump_maple_small` | Stump Maple Small | ✅ Yes | — | [stump_maple_small.json](logging/stump_maple_small/stump_maple_small.json) |
| `stump_oak_large` | Stump Oak Large | ✅ Yes | — | [stump_oak_large.json](logging/stump_oak_large/stump_oak_large.json) |
| `stump_oak_medium` | Stump Oak Medium | ✅ Yes | — | [stump_oak_medium.json](logging/stump_oak_medium/stump_oak_medium.json) |
| `stump_oak_small` | Stump Oak Small | ✅ Yes | — | [stump_oak_small.json](logging/stump_oak_small/stump_oak_small.json) |
| `stump_pine_large` | Stump Pine Large | ✅ Yes | — | [stump_pine_large.json](logging/stump_pine_large/stump_pine_large.json) |
| `stump_pine_medium` | Stump Pine Medium | ✅ Yes | — | [stump_pine_medium.json](logging/stump_pine_medium/stump_pine_medium.json) |
| `stump_pine_small` | Stump Pine Small | ✅ Yes | — | [stump_pine_small.json](logging/stump_pine_small/stump_pine_small.json) |
| `stump_poplar_large` | Stump Poplar Large | ✅ Yes | — | [stump_poplar_large.json](logging/stump_poplar_large/stump_poplar_large.json) |
| `stump_poplar_medium` | Stump Poplar Medium | ✅ Yes | — | [stump_poplar_medium.json](logging/stump_poplar_medium/stump_poplar_medium.json) |
| `stump_poplar_small` | Stump Poplar Small | ✅ Yes | — | [stump_poplar_small.json](logging/stump_poplar_small/stump_poplar_small.json) |
| `stump_willow_large` | Stump Willow Large | ✅ Yes | — | [stump_willow_large.json](logging/stump_willow_large/stump_willow_large.json) |
| `stump_willow_medium` | Stump Willow Medium | ✅ Yes | — | [stump_willow_medium.json](logging/stump_willow_medium/stump_willow_medium.json) |
| `stump_willow_small` | Stump Willow Small | ✅ Yes | — | [stump_willow_small.json](logging/stump_willow_small/stump_willow_small.json) |
| `tree_dead_snag` | Tree Dead Snag | ✅ Yes | — | [tree_dead_snag.json](logging/tree_dead_snag/tree_dead_snag.json) |
| `tree_sapling` | Tree Sapling | ✅ Yes | — | [tree_sapling.json](logging/tree_sapling/tree_sapling.json) |
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
| `fishing_bait` | Live Fishing Bait | — | — | [fishing_bait.json](fishing/fishing_bait/fishing_bait.json) |
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

### 📂 [Tools](tools/) (54 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `tool_angle_grinder_corded` | Corded Angle Grinder | — | — | [tool_angle_grinder_corded.json](tools/tool_angle_grinder_corded/tool_angle_grinder_corded.json) |
| `tool_angle_grinder_cordless` | Cordless Angle Grinder | — | — | [tool_angle_grinder_cordless.json](tools/tool_angle_grinder_cordless/tool_angle_grinder_cordless.json) |
| `tool_animal_paddle_sorting_cattle` | Cattle Sorting Paddle | ✅ Yes | — | [tool_animal_paddle_sorting_cattle.json](tools/tool_animal_paddle_sorting_cattle/tool_animal_paddle_sorting_cattle.json) |
| `tool_anvil_stump` | Tool Anvil Stump | ✅ Yes | — | [tool_anvil_stump.json](tools/tool_anvil_stump/tool_anvil_stump.json) |
| `tool_axe` | Axe | ✅ Yes | — | [tool_axe.json](tools/tool_axe/tool_axe.json) |
| `tool_axe_felling` | Felling Axe | ✅ Yes | — | [tool_axe_felling.json](tools/tool_axe_felling/tool_axe_felling.json) |
| `tool_bucket_empty` | Empty Utility Bucket | — | — | [tool_bucket_empty.json](tools/tool_bucket_empty/tool_bucket_empty.json) |
| `tool_cant_hook_peavey` | Cant Hook Peavey | ✅ Yes | — | [tool_cant_hook_peavey.json](tools/tool_cant_hook_peavey/tool_cant_hook_peavey.json) |
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
| `tool_hammer` | Hammer | ✅ Yes | — | [tool_hammer.json](tools/tool_hammer/tool_hammer.json) |
| `tool_hammer_claw` | Claw Hammer | ✅ Yes | — | [tool_hammer_claw.json](tools/tool_hammer_claw/tool_hammer_claw.json) |
| `tool_hammer_club` | Club Hammer | ✅ Yes | — | [tool_hammer_club.json](tools/tool_hammer_club/tool_hammer_club.json) |
| `tool_hatchet_camp` | Camp Hatchet | ✅ Yes | — | [tool_hatchet_camp.json](tools/tool_hatchet_camp/tool_hatchet_camp.json) |
| `tool_helmet_logging_safety` | Logging Safety Helmet | ✅ Yes | — | [tool_helmet_logging_safety.json](tools/tool_helmet_logging_safety/tool_helmet_logging_safety.json) |
| `tool_hoe` | Hoe | ✅ Yes | — | [tool_hoe.json](tools/tool_hoe/tool_hoe.json) |
| `tool_hose_garden_reel` | Garden Hose & Reel | ✅ Yes | — | [tool_hose_garden_reel.json](tools/tool_hose_garden_reel/tool_hose_garden_reel.json) |
| `tool_impact_driver_cordless` | Cordless Impact Driver | — | — | [tool_impact_driver_cordless.json](tools/tool_impact_driver_cordless/tool_impact_driver_cordless.json) |
| `tool_kit_chainsaw_file_pouch` | Chainsaw File Kit | ✅ Yes | — | [tool_kit_chainsaw_file_pouch.json](tools/tool_kit_chainsaw_file_pouch/tool_kit_chainsaw_file_pouch.json) |
| `tool_loppers_heavy` | Heavy Loppers | ✅ Yes | — | [tool_loppers_heavy.json](tools/tool_loppers_heavy/tool_loppers_heavy.json) |
| `tool_maul_splitting` | Splitting Maul | ✅ Yes | — | [tool_maul_splitting.json](tools/tool_maul_splitting/tool_maul_splitting.json) |
| `tool_miter_saw` | Miter Saw | — | — | [tool_miter_saw.json](tools/tool_miter_saw/tool_miter_saw.json) |
| `tool_pail_milk_stainless` | Tool Pail Milk Stainless | ✅ Yes | — | [tool_pail_milk_stainless.json](tools/tool_pail_milk_stainless/tool_pail_milk_stainless.json) |
| `tool_pickaxe` | Pickaxe | ✅ Yes | — | [tool_pickaxe.json](tools/tool_pickaxe/tool_pickaxe.json) |
| `tool_plastic_wheelbarrow` | Plastic Wheelbarrow | ✅ Yes | — | [tool_plastic_wheelbarrow.json](tools/tool_plastic_wheelbarrow/tool_plastic_wheelbarrow.json) |
| `tool_pump_sprayer` | Pump Sprayer | ✅ Yes | — | [tool_pump_sprayer.json](tools/tool_pump_sprayer/tool_pump_sprayer.json) |
| `tool_seedbag` | Seed Bag | — | — | [tool_seedbag.json](tools/tool_seedbag/tool_seedbag.json) |
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
| `tool_tap` | Tree Tap & Spile | — | — | [tool_tap.json](tools/tool_tap/tool_tap.json) |
| `tool_tongs_skidding_logging` | Skidding Tongs | ✅ Yes | — | [tool_tongs_skidding_logging.json](tools/tool_tongs_skidding_logging/tool_tongs_skidding_logging.json) |
| `tool_trowel_hand` | Hand Trowel | ✅ Yes | — | [tool_trowel_hand.json](tools/tool_trowel_hand/tool_trowel_hand.json) |
| `tool_walking_plow_own` | Walking Plow (Meshy text-to-3D, own icon) | ✅ Yes | — | [tool_walking_plow_own.json](tools/tool_walking_plow_own/tool_walking_plow_own.json) |
| `tool_wedge_felling_abs_pack` | Felling Wedges Pack | ✅ Yes | — | [tool_wedge_felling_abs_pack.json](tools/tool_wedge_felling_abs_pack/tool_wedge_felling_abs_pack.json) |
| `tool_wedge_splitting_diamond` | Diamond Splitting Wedge | ✅ Yes | — | [tool_wedge_splitting_diamond.json](tools/tool_wedge_splitting_diamond/tool_wedge_splitting_diamond.json) |
| `tool_wheelbarrow` | Wheelbarrow | ✅ Yes | — | [tool_wheelbarrow.json](tools/tool_wheelbarrow/tool_wheelbarrow.json) |
| `tool_wrench_adjustable` | Adjustable Wrench | ✅ Yes | — | [tool_wrench_adjustable.json](tools/tool_wrench_adjustable/tool_wrench_adjustable.json) |
| `tool_wrench_pipe` | Pipe Wrench | ✅ Yes | — | [tool_wrench_pipe.json](tools/tool_wrench_pipe/tool_wrench_pipe.json) |

### 📂 [Electricity](electricity/) (37 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `electricity_battery_12v_agm_1200wh` | 12V AGM 1200Wh Battery | ✅ Yes | — | [electricity_battery_12v_agm_1200wh.json](electricity/electricity_battery_12v_agm_1200wh/electricity_battery_12v_agm_1200wh.json) |
| `electricity_battery_12v_lifepo4_1200wh` | 12V LiFePO4 1200Wh Battery | ✅ Yes | — | [electricity_battery_12v_lifepo4_1200wh.json](electricity/electricity_battery_12v_lifepo4_1200wh/electricity_battery_12v_lifepo4_1200wh.json) |
| `electricity_battery_bank` | Battery Bank | ✅ Yes | — | [electricity_battery_bank.json](electricity/electricity_battery_bank/electricity_battery_bank.json) |
| `electricity_battery_rack_48v_5kwh` | 48V Rack Battery (5kWh) | ✅ Yes | — | [electricity_battery_rack_48v_5kwh.json](electricity/electricity_battery_rack_48v_5kwh/electricity_battery_rack_48v_5kwh.json) |
| `electricity_battery_wall_power_10kwh` | Wall Power Battery (10kWh) | ✅ Yes | — | [electricity_battery_wall_power_10kwh.json](electricity/electricity_battery_wall_power_10kwh/electricity_battery_wall_power_10kwh.json) |
| `electricity_breakersubpanel` | Item Electric Breakersubpanel | ✅ Yes | — | [electricity_breakersubpanel.json](electricity/electricity_breakersubpanel/electricity_breakersubpanel.json) |
| `electricity_cable_solar_mc4_pair` | Solar MC4 Cable Pair | ✅ Yes | — | [electricity_cable_solar_mc4_pair.json](electricity/electricity_cable_solar_mc4_pair/electricity_cable_solar_mc4_pair.json) |
| `electricity_cables_battery_interconnect` | Battery Jumper Cables | ✅ Yes | — | [electricity_cables_battery_interconnect.json](electricity/electricity_cables_battery_interconnect/electricity_cables_battery_interconnect.json) |
| `electricity_conduit_pipe_emt` | EMT Conduit Pipe | ✅ Yes | — | [electricity_conduit_pipe_emt.json](electricity/electricity_conduit_pipe_emt/electricity_conduit_pipe_emt.json) |
| `electricity_controller_mppt_60a` | 60A MPPT Charge Controller | ✅ Yes | — | [electricity_controller_mppt_60a.json](electricity/electricity_controller_mppt_60a/electricity_controller_mppt_60a.json) |
| `electricity_cord_generator_30a` | 30A Generator Cord | ✅ Yes | — | [electricity_cord_generator_30a.json](electricity/electricity_cord_generator_30a/electricity_cord_generator_30a.json) |
| `electricity_disconnectswitch` | Item Electric Disconnectswitch | ✅ Yes | — | [electricity_disconnectswitch.json](electricity/electricity_disconnectswitch/electricity_disconnectswitch.json) |
| `electricity_energizer_fence_solar` | Solar Fence Energizer | ✅ Yes | — | [electricity_energizer_fence_solar.json](electricity/electricity_energizer_fence_solar/electricity_energizer_fence_solar.json) |
| `electricity_generator` | Generator | ✅ Yes | — | [electricity_generator.json](electricity/electricity_generator/electricity_generator.json) |
| `electricity_generator_frame_7500w` | 7500W Frame Generator | ✅ Yes | — | [electricity_generator_frame_7500w.json](electricity/electricity_generator_frame_7500w/electricity_generator_frame_7500w.json) |
| `electricity_generator_inverter_2000w` | 2000W Inverter Generator | ✅ Yes | — | [electricity_generator_inverter_2000w.json](electricity/electricity_generator_inverter_2000w/electricity_generator_inverter_2000w.json) |
| `electricity_generator_portable` | Portable Generator | — | — | [electricity_generator_portable.json](electricity/electricity_generator_portable/electricity_generator_portable.json) |
| `electricity_generator_standby` | Standby Generator | — | — | [electricity_generator_standby.json](electricity/electricity_generator_standby/electricity_generator_standby.json) |
| `electricity_generator_standby_15kw` | 15kW Standby Generator | ✅ Yes | — | [electricity_generator_standby_15kw.json](electricity/electricity_generator_standby_15kw/electricity_generator_standby_15kw.json) |
| `electricity_inverter_hybrid_3000w` | 3000W Hybrid Inverter | ✅ Yes | — | [electricity_inverter_hybrid_3000w.json](electricity/electricity_inverter_hybrid_3000w/electricity_inverter_hybrid_3000w.json) |
| `electricity_inverter_wall` | Electric Inverter Wall | ✅ Yes | — | [electricity_inverter_wall.json](electricity/electricity_inverter_wall/electricity_inverter_wall.json) |
| `electricity_mpptcontroller` | MPPT Solar Charge Controller | — | — | [electricity_mpptcontroller.json](electricity/electricity_mpptcontroller/electricity_mpptcontroller.json) |
| `electricity_networkswitch_poe` | Item Electric Networkswitch Poe | ✅ Yes | — | [electricity_networkswitch_poe.json](electricity/electricity_networkswitch_poe/electricity_networkswitch_poe.json) |
| `electricity_panel_breaker_subpanel` | Outdoor Breaker Subpanel | ✅ Yes | — | [electricity_panel_breaker_subpanel.json](electricity/electricity_panel_breaker_subpanel/electricity_panel_breaker_subpanel.json) |
| `electricity_power_pole_metal` | Power Pole Metal | — | — | [electricity_power_pole_metal.json](electricity/electricity_power_pole_metal/electricity_power_pole_metal.json) |
| `electricity_power_pole_wood` | Power Pole Wood | — | — | [electricity_power_pole_wood.json](electricity/electricity_power_pole_wood/electricity_power_pole_wood.json) |
| `electricity_powerpole_wood` | Electric Powerpole Wood | ✅ Yes | — | [electricity_powerpole_wood.json](electricity/electricity_powerpole_wood/electricity_powerpole_wood.json) |
| `electricity_rod_grounding_copper` | Copper Grounding Rod | ✅ Yes | — | [electricity_rod_grounding_copper.json](electricity/electricity_rod_grounding_copper/electricity_rod_grounding_copper.json) |
| `electricity_solar_blanket_200w_folding` | 200W Folding Solar Blanket | ✅ Yes | — | [electricity_solar_blanket_200w_folding.json](electricity/electricity_solar_blanket_200w_folding/electricity_solar_blanket_200w_folding.json) |
| `electricity_solar_panel` | Solar Panel | ✅ Yes | — | [electricity_solar_panel.json](electricity/electricity_solar_panel/electricity_solar_panel.json) |
| `electricity_solar_panel_100w_rigid` | 100W Rigid Solar Panel | ✅ Yes | — | [electricity_solar_panel_100w_rigid.json](electricity/electricity_solar_panel_100w_rigid/electricity_solar_panel_100w_rigid.json) |
| `electricity_solar_panel_400w_commercial` | 400W Commercial Solar Panel | ✅ Yes | — | [electricity_solar_panel_400w_commercial.json](electricity/electricity_solar_panel_400w_commercial/electricity_solar_panel_400w_commercial.json) |
| `electricity_spool_electric_polywire` | Electric Polywire Spool | ✅ Yes | — | [electricity_spool_electric_polywire.json](electricity/electricity_spool_electric_polywire/electricity_spool_electric_polywire.json) |
| `electricity_sterilizer_uv_chamber` | UV Sterilizer Chamber | ✅ Yes | — | [electricity_sterilizer_uv_chamber.json](electricity/electricity_sterilizer_uv_chamber/electricity_sterilizer_uv_chamber.json) |
| `electricity_switch_disconnect_safety` | Safety Disconnect Switch | ✅ Yes | — | [electricity_switch_disconnect_safety.json](electricity/electricity_switch_disconnect_safety/electricity_switch_disconnect_safety.json) |
| `electricity_wind_turbine` | Wind Turbine | ✅ Yes | — | [electricity_wind_turbine.json](electricity/electricity_wind_turbine/electricity_wind_turbine.json) |
| `electricity_wooden_utility_pole` | Wooden Utility Pole | — | — | [electricity_wooden_utility_pole.json](electricity/electricity_wooden_utility_pole/electricity_wooden_utility_pole.json) |

### 📂 [Water](water/) (31 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `water_barrel_rain_200l` | 200L Rain Barrel | ✅ Yes | — | [water_barrel_rain_200l.json](water/water_barrel_rain_200l/water_barrel_rain_200l.json) |
| `water_bucket_water` | Bucket of Water | — | — | [water_bucket_water.json](water/water_bucket_water/water_bucket_water.json) |
| `water_cistern_poly_3800l` | 3800L Water Cistern | ✅ Yes | — | [water_cistern_poly_3800l.json](water/water_cistern_poly_3800l/water_cistern_poly_3800l.json) |
| `water_dock_section_1x2m` | Water Dock Section 1X2M | ✅ Yes | — | [water_dock_section_1x2m.json](water/water_dock_section_1x2m/water_dock_section_1x2m.json) |
| `water_drainsock_roll` | Item Plumbing Drainsock Roll | ✅ Yes | — | [water_drainsock_roll.json](water/water_drainsock_roll/water_drainsock_roll.json) |
| `water_filter` | Water Filter | — | — | [water_filter.json](water/water_filter/water_filter.json) |
| `water_filter_canister_bigblue` | Item Plumbing Filter Bigblue | ✅ Yes | — | [water_filter_canister_bigblue.json](water/water_filter_canister_bigblue/water_filter_canister_bigblue.json) |
| `water_filter_reverse_osmosis` | Reverse Osmosis Filter | ✅ Yes | — | [water_filter_reverse_osmosis.json](water/water_filter_reverse_osmosis/water_filter_reverse_osmosis.json) |
| `water_filter_spin_down_sediment` | Spin-Down Sediment Filter | ✅ Yes | — | [water_filter_spin_down_sediment.json](water/water_filter_spin_down_sediment/water_filter_spin_down_sediment.json) |
| `water_fitting_camlock_coupler` | Camlock Coupler | ✅ Yes | — | [water_fitting_camlock_coupler.json](water/water_fitting_camlock_coupler/water_fitting_camlock_coupler.json) |
| `water_hand_pump_wellhead` | Hand Pump Well Head | — | — | [water_hand_pump_wellhead.json](water/water_hand_pump_wellhead/water_hand_pump_wellhead.json) |
| `water_hose_contractor_heavy` | Heavy Contractor Hose | ✅ Yes | — | [water_hose_contractor_heavy.json](water/water_hose_contractor_heavy/water_hose_contractor_heavy.json) |
| `water_hose_soaker_flat` | Soaker Hose | ✅ Yes | — | [water_hose_soaker_flat.json](water/water_hose_soaker_flat/water_hose_soaker_flat.json) |
| `water_ibc_tote_1000l` | 1000L IBC Tote | ✅ Yes | — | [water_ibc_tote_1000l.json](water/water_ibc_tote_1000l/water_ibc_tote_1000l.json) |
| `water_irrigation_sprinkler_riser` | Farm Irrigation Sprinkler Riser | ✅ Yes | — | [water_irrigation_sprinkler_riser.json](water/water_irrigation_sprinkler_riser/water_irrigation_sprinkler_riser.json) |
| `water_jug_20l` | 20L Water Jug | ✅ Yes | — | [water_jug_20l.json](water/water_jug_20l/water_jug_20l.json) |
| `water_pipe` | Water Pipe | — | — | [water_pipe.json](water/water_pipe/water_pipe.json) |
| `water_pressuretank_well` | Water Pressuretank Well | ✅ Yes | — | [water_pressuretank_well.json](water/water_pressuretank_well/water_pressuretank_well.json) |
| `water_pump` | Electric Water Pump | ✅ Yes | — | [water_pump.json](water/water_pump/water_pump.json) |
| `water_pump_high_capacity` | High Capacity Water Well Pump | — | — | [water_pump_high_capacity.json](water/water_pump_high_capacity/water_pump_high_capacity.json) |
| `water_pump_jet_shallow_well` | Shallow Well Jet Pump | ✅ Yes | — | [water_pump_jet_shallow_well.json](water/water_pump_jet_shallow_well/water_pump_jet_shallow_well.json) |
| `water_pump_low_capacity` | Low Capacity Water Well Pump | — | — | [water_pump_low_capacity.json](water/water_pump_low_capacity/water_pump_low_capacity.json) |
| `water_pump_submersible_1hp` | Small Submersible Well Pump | ✅ Yes | — | [water_pump_submersible_1hp.json](water/water_pump_submersible_1hp/water_pump_submersible_1hp.json) |
| `water_pump_submersible_3hp` | Large Submersible Well Pump | ✅ Yes | — | [water_pump_submersible_3hp.json](water/water_pump_submersible_3hp/water_pump_submersible_3hp.json) |
| `water_pvc_bundle` | Item Plumbing Pvc Bundle | ✅ Yes | — | [water_pvc_bundle.json](water/water_pvc_bundle/water_pvc_bundle.json) |
| `water_sprinkler` | Sprinkler Head | ✅ Yes | — | [water_sprinkler.json](water/water_sprinkler/water_sprinkler.json) |
| `water_wand_watering_brass` | Tool Wand Watering | ✅ Yes | — | [water_wand_watering_brass.json](water/water_wand_watering_brass/water_wand_watering_brass.json) |
| `water_watering_can` | Tool Wateringcan | ✅ Yes | — | [water_watering_can.json](water/water_watering_can/water_watering_can.json) |
| `water_well_head_concrete` | Concrete Well Head | ✅ Yes | — | [water_well_head_concrete.json](water/water_well_head_concrete/water_well_head_concrete.json) |
| `water_well_head_wooden` | Wooden Well Head | ✅ Yes | — | [water_well_head_wooden.json](water/water_well_head_wooden/water_well_head_wooden.json) |
| `water_well_manual` | Manual Well | — | — | [water_well_manual.json](water/water_well_manual/water_well_manual.json) |

### 📂 [Waste](waste/) (19 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `waste_aerator_septic_air_pump` | Septic Aerator Pump | ✅ Yes | — | [waste_aerator_septic_air_pump.json](waste/waste_aerator_septic_air_pump/waste_aerator_septic_air_pump.json) |
| `waste_box_distribution_septic` | Septic Distribution Box | ✅ Yes | — | [waste_box_distribution_septic.json](waste/waste_box_distribution_septic/waste_box_distribution_septic.json) |
| `waste_compost_bin_3bay` | 3-Bay Compost Bin | ✅ Yes | — | [waste_compost_bin_3bay.json](waste/waste_compost_bin_3bay/waste_compost_bin_3bay.json) |
| `waste_hose_sewer_rv_3m` | 3m RV Sewer Hose | ✅ Yes | — | [waste_hose_sewer_rv_3m.json](waste/waste_hose_sewer_rv_3m/waste_hose_sewer_rv_3m.json) |
| `waste_hose_sewer_rv_6m` | 6m RV Sewer Hose | ✅ Yes | — | [waste_hose_sewer_rv_6m.json](waste/waste_hose_sewer_rv_6m/waste_hose_sewer_rv_6m.json) |
| `waste_nozzle_spray_quick` | Quick-Connect Spray Nozzle | ✅ Yes | — | [waste_nozzle_spray_quick.json](waste/waste_nozzle_spray_quick/waste_nozzle_spray_quick.json) |
| `waste_pile_manure_large` | Large Manure Pile (Material) | — | — | [waste_pile_manure_large.json](waste/waste_pile_manure_large/waste_pile_manure_large.json) |
| `waste_pile_manure_medium` | Medium Manure Pile (Material) | — | — | [waste_pile_manure_medium.json](waste/waste_pile_manure_medium/waste_pile_manure_medium.json) |
| `waste_pile_manure_small` | Small Manure Pile (Material) | — | — | [waste_pile_manure_small.json](waste/waste_pile_manure_small/waste_pile_manure_small.json) |
| `waste_pump_macerator` | Macerator Waste Pump | ✅ Yes | — | [waste_pump_macerator.json](waste/waste_pump_macerator/waste_pump_macerator.json) |
| `waste_pump_pitcher_manual` | Manual Pitcher Well Pump | ✅ Yes | — | [waste_pump_pitcher_manual.json](waste/waste_pump_pitcher_manual/waste_pump_pitcher_manual.json) |
| `waste_pump_submersible_deep` | Deep Submersible Well Pump | ✅ Yes | — | [waste_pump_submersible_deep.json](waste/waste_pump_submersible_deep/waste_pump_submersible_deep.json) |
| `waste_pump_sump_float` | Automatic Sump Pump | ✅ Yes | — | [waste_pump_sump_float.json](waste/waste_pump_sump_float/waste_pump_sump_float.json) |
| `waste_riser_septic_lid` | Septic Riser & Lid | ✅ Yes | — | [waste_riser_septic_lid.json](waste/waste_riser_septic_lid/waste_riser_septic_lid.json) |
| `waste_tank_rv_waste_tote` | RV Waste Holding Tote Tank | ✅ Yes | — | [waste_tank_rv_waste_tote.json](waste/waste_tank_rv_waste_tote/waste_tank_rv_waste_tote.json) |
| `waste_tank_septic_concrete_3800l` | 3800L Concrete Septic Vault | ✅ Yes | — | [waste_tank_septic_concrete_3800l.json](waste/waste_tank_septic_concrete_3800l/waste_tank_septic_concrete_3800l.json) |
| `waste_tank_septic_poly_1900l` | 1900L Poly Septic Tank | ✅ Yes | — | [waste_tank_septic_poly_1900l.json](waste/waste_tank_septic_poly_1900l/waste_tank_septic_poly_1900l.json) |
| `waste_toilet_composting_rustic` | Composting Toilet | ✅ Yes | — | [waste_toilet_composting_rustic.json](waste/waste_toilet_composting_rustic/waste_toilet_composting_rustic.json) |
| `waste_treatment_septic_packets` | Septic Treatment Packets | ✅ Yes | — | [waste_treatment_septic_packets.json](waste/waste_treatment_septic_packets/waste_treatment_septic_packets.json) |

### 📂 [Internet](internet/) (16 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `net_antenna_omni_cellular` | Omni Cellular Antenna | ✅ Yes | — | [net_antenna_omni_cellular.json](internet/net_antenna_omni_cellular/net_antenna_omni_cellular.json) |
| `net_antenna_yagi_directional` | Yagi Directional Antenna | ✅ Yes | — | [net_antenna_yagi_directional.json](internet/net_antenna_yagi_directional/net_antenna_yagi_directional.json) |
| `net_ap_outdoor_weatherproof` | Outdoor Access Point | ✅ Yes | — | [net_ap_outdoor_weatherproof.json](internet/net_ap_outdoor_weatherproof/net_ap_outdoor_weatherproof.json) |
| `net_arrestor_lightning_ethernet` | Ethernet Surge Arrestor | ✅ Yes | — | [net_arrestor_lightning_ethernet.json](internet/net_arrestor_lightning_ethernet/net_arrestor_lightning_ethernet.json) |
| `net_cable` | Internet Cable | — | — | [net_cable.json](internet/net_cable/net_cable.json) |
| `net_cable_ethernet_cat6_15m` | 15m Cat6 Cable | ✅ Yes | — | [net_cable_ethernet_cat6_15m.json](internet/net_cable_ethernet_cat6_15m/net_cable_ethernet_cat6_15m.json) |
| `net_cable_ethernet_cat6_30m` | 30m Cat6 Cable | ✅ Yes | — | [net_cable_ethernet_cat6_30m.json](internet/net_cable_ethernet_cat6_30m/net_cable_ethernet_cat6_30m.json) |
| `net_dish_satellite` | Internet Satellite Dish | — | — | [net_dish_satellite.json](internet/net_dish_satellite/net_dish_satellite.json) |
| `net_dish_satellite_high_perf` | High-Performance Satellite Dish | ✅ Yes | — | [net_dish_satellite_high_perf.json](internet/net_dish_satellite_high_perf/net_dish_satellite_high_perf.json) |
| `net_injector_poe_adapter` | PoE Injector | ✅ Yes | — | [net_injector_poe_adapter.json](internet/net_injector_poe_adapter/net_injector_poe_adapter.json) |
| `net_mount_j_mast_bracket` | J-Mast Mounting Bracket | ✅ Yes | — | [net_mount_j_mast_bracket.json](internet/net_mount_j_mast_bracket/net_mount_j_mast_bracket.json) |
| `net_router` | Internet Router | ✅ Yes | — | [net_router.json](internet/net_router/net_router.json) |
| `net_router_mesh_wifi6` | Wi-Fi 6 Mesh Router | ✅ Yes | — | [net_router_mesh_wifi6.json](internet/net_router_mesh_wifi6/net_router_mesh_wifi6.json) |
| `net_spool_cable_cat6_150m` | 150m Cat6 Cable Spool | ✅ Yes | — | [net_spool_cable_cat6_150m.json](internet/net_spool_cable_cat6_150m/net_spool_cable_cat6_150m.json) |
| `net_switch_poe_8port` | 8-Port PoE Switch | ✅ Yes | — | [net_switch_poe_8port.json](internet/net_switch_poe_8port/net_switch_poe_8port.json) |
| `net_switch_rackmount_16port` | 16-Port Rackmount Switch | ✅ Yes | — | [net_switch_rackmount_16port.json](internet/net_switch_rackmount_16port/net_switch_rackmount_16port.json) |

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
| `hud_water` | Water | — | — | [hud_water.json](hud/hud_water/hud_water.json) |
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

### 📂 [Food](food/) (26 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `food_apple` | Fresh Red Apple | ✅ Yes | — | [food_apple.json](food/food_apple/food_apple.json) |
| `food_bass_deepfried` | Bass Fillet Deep Fried | — | — | [food_bass_deepfried.json](food/food_bass_deepfried/food_bass_deepfried.json) |
| `food_bass_grilled` | Bass Grilled Fillet | — | — | [food_bass_grilled.json](food/food_bass_grilled/food_bass_grilled.json) |
| `food_bread` | Bread | — | — | [food_bread.json](food/food_bread/food_bread.json) |
| `food_carrot` | Fresh Garden Carrot | ✅ Yes | — | [food_carrot.json](food/food_carrot/food_carrot.json) |
| `food_catfish_deepfried` | Catfish Fillet Deep Fried | — | — | [food_catfish_deepfried.json](food/food_catfish_deepfried/food_catfish_deepfried.json) |
| `food_catfish_grilled` | Catfish Grilled Fillet | — | — | [food_catfish_grilled.json](food/food_catfish_grilled/food_catfish_grilled.json) |
| `food_cheese` | Aged Farmhouse Cheese | — | — | [food_cheese.json](food/food_cheese/food_cheese.json) |
| `food_crappie_deepfried` | Crappie Fillet Deep Fried | — | — | [food_crappie_deepfried.json](food/food_crappie_deepfried/food_crappie_deepfried.json) |
| `food_crappie_grilled` | Crappie Grilled Fillet | — | — | [food_crappie_grilled.json](food/food_crappie_grilled/food_crappie_grilled.json) |
| `food_lemon` | Fresh Lemon | ✅ Yes | — | [food_lemon.json](food/food_lemon/food_lemon.json) |
| `food_orange` | Fresh Navel Orange | ✅ Yes | — | [food_orange.json](food/food_orange/food_orange.json) |
| `food_potato` | Russet Potato | ✅ Yes | — | [food_potato.json](food/food_potato/food_potato.json) |
| `food_pumpkin` | Autumn Pumpkin | ✅ Yes | — | [food_pumpkin.json](food/food_pumpkin/food_pumpkin.json) |
| `food_salmon_grilled` | Salmon Grilled Fillet | — | — | [food_salmon_grilled.json](food/food_salmon_grilled/food_salmon_grilled.json) |
| `food_strawberry` | Fresh Strawberry | ✅ Yes | — | [food_strawberry.json](food/food_strawberry/food_strawberry.json) |
| `food_tomato` | Vine Ripe Tomato | ✅ Yes | — | [food_tomato.json](food/food_tomato/food_tomato.json) |
| `food_trout_deepfried` | Trout Fillet Deep Fried | — | — | [food_trout_deepfried.json](food/food_trout_deepfried/food_trout_deepfried.json) |
| `food_trout_grilled` | Trout Grilled Fillet | — | — | [food_trout_grilled.json](food/food_trout_grilled/food_trout_grilled.json) |
| `food_truffle` | Black Foraged Truffle | ✅ Yes | — | [food_truffle.json](food/food_truffle/food_truffle.json) |
| `food_walleye_deepfried` | Walleye Fillet Deep Fried | — | — | [food_walleye_deepfried.json](food/food_walleye_deepfried/food_walleye_deepfried.json) |
| `food_walleye_grilled` | Walleye Grilled Fillet | — | — | [food_walleye_grilled.json](food/food_walleye_grilled/food_walleye_grilled.json) |
| `ingredient_beef_grilled` | Grilled Beef Cut | — | — | [ingredient_beef_grilled.json](food/ingredient_beef_grilled/ingredient_beef_grilled.json) |
| `ingredient_chicken_grilled` | Grilled Chicken Drumstick | — | — | [ingredient_chicken_grilled.json](food/ingredient_chicken_grilled/ingredient_chicken_grilled.json) |
| `ingredient_milk` | Fresh Whole Milk | ✅ Yes | — | [ingredient_milk.json](food/ingredient_milk/ingredient_milk.json) |
| `ingredient_pork_grilled` | Grilled Pork Chop | — | — | [ingredient_pork_grilled.json](food/ingredient_pork_grilled/ingredient_pork_grilled.json) |

### 📂 [Fuel](fuel/) (17 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `fuel_charcoal` | Charcoal | — | — | [fuel_charcoal.json](fuel/fuel_charcoal/fuel_charcoal.json) |
| `fuel_firewood` | Seasoned Firewood Stack | — | — | [fuel_firewood.json](fuel/fuel_firewood/fuel_firewood.json) |
| `fuel_firewood_bundle_tied` | Tied Firewood Bundle | ✅ Yes | — | [fuel_firewood_bundle_tied.json](fuel/fuel_firewood_bundle_tied/fuel_firewood_bundle_tied.json) |
| `fuel_large_diesel_container` | Large Diesel Fuel Container | ✅ Yes | — | [fuel_large_diesel_container.json](fuel/fuel_large_diesel_container/fuel_large_diesel_container.json) |
| `fuel_propane_18l` | Propane Tank (18L) | — | — | [fuel_propane_18l.json](fuel/fuel_propane_18l/fuel_propane_18l.json) |
| `fuel_propane_1_5l` | Small Propane Tank (1.5L) | — | — | [fuel_propane_1_5l.json](fuel/fuel_propane_1_5l/fuel_propane_1_5l.json) |
| `fuel_propane_36l` | Large Propane Tank (36L) | — | — | [fuel_propane_36l.json](fuel/fuel_propane_36l/fuel_propane_36l.json) |
| `fuel_pump_diesel` | Diesel Fuel Pump | — | — | [fuel_pump_diesel.json](fuel/fuel_pump_diesel/fuel_pump_diesel.json) |
| `fuel_pump_gas` | Gasoline Fuel Pump | — | — | [fuel_pump_gas.json](fuel/fuel_pump_gas/fuel_pump_gas.json) |
| `fuel_small_diesel_container` | Small Diesel Fuel Container | ✅ Yes | — | [fuel_small_diesel_container.json](fuel/fuel_small_diesel_container/fuel_small_diesel_container.json) |
| `fuel_steel_drum_200l` | Steel Drum (200L) | ✅ Yes | — | [fuel_steel_drum_200l.json](fuel/fuel_steel_drum_200l/fuel_steel_drum_200l.json) |
| `fuel_tank_bulk_large` | Large Bulk Fuel Storage Tank | — | — | [fuel_tank_bulk_large.json](fuel/fuel_tank_bulk_large/fuel_tank_bulk_large.json) |
| `fuel_tank_bulk_small` | Small Bulk Fuel Storage Tank | — | — | [fuel_tank_bulk_small.json](fuel/fuel_tank_bulk_small/fuel_tank_bulk_small.json) |
| `fuel_tank_propane_1900l` | 1900L Propane Tank | — | — | [fuel_tank_propane_1900l.json](fuel/fuel_tank_propane_1900l/fuel_tank_propane_1900l.json) |
| `fuel_tank_propane_3800l` | 3800L Propane Tank | ✅ Yes | — | [fuel_tank_propane_3800l.json](fuel/fuel_tank_propane_3800l/fuel_tank_propane_3800l.json) |
| `large_gas_fuel_container` | Large Gas Fuel Container | — | — | [large_gas_fuel_container.json](fuel/large_gas_fuel_container/large_gas_fuel_container.json) |
| `small_gas_fuel_container` | Small Gas Fuel Container | — | — | [small_gas_fuel_container.json](fuel/small_gas_fuel_container/small_gas_fuel_container.json) |

### 📂 [Materials](materials/) (69 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `mat_bale_hay_round` | Round Hay Bale | — | — | [mat_bale_hay_round.json](materials/mat_bale_hay_round/mat_bale_hay_round.json) |
| `mat_bale_hay_square` | Square Hay Bale | — | — | [mat_bale_hay_square.json](materials/mat_bale_hay_square/mat_bale_hay_square.json) |
| `mat_bale_straw_round` | Round Straw Bale | — | — | [mat_bale_straw_round.json](materials/mat_bale_straw_round/mat_bale_straw_round.json) |
| `mat_bale_straw_square` | Square Straw Bale | — | — | [mat_bale_straw_square.json](materials/mat_bale_straw_square/mat_bale_straw_square.json) |
| `mat_feather` | Poultry Down Feather | — | — | [mat_feather.json](materials/mat_feather/mat_feather.json) |
| `mat_fertilizer` | Fertilizer | — | — | [mat_fertilizer.json](materials/mat_fertilizer/mat_fertilizer.json) |
| `mat_leather` | Tanned Leather | — | — | [mat_leather.json](materials/mat_leather/mat_leather.json) |
| `mat_log_birch` | Birch Log | — | — | [mat_log_birch.json](materials/mat_log_birch/mat_log_birch.json) |
| `mat_log_birch_uncut_long` | Long Birch Uncut Log | ✅ Yes | — | [mat_log_birch_uncut_long.json](materials/mat_log_birch_uncut_long/mat_log_birch_uncut_long.json) |
| `mat_log_birch_uncut_medium` | Medium Birch Uncut Log | ✅ Yes | — | [mat_log_birch_uncut_medium.json](materials/mat_log_birch_uncut_medium/mat_log_birch_uncut_medium.json) |
| `mat_log_birch_uncut_small` | Small Birch Uncut Log | ✅ Yes | — | [mat_log_birch_uncut_small.json](materials/mat_log_birch_uncut_small/mat_log_birch_uncut_small.json) |
| `mat_log_maple` | Maple Log | — | — | [mat_log_maple.json](materials/mat_log_maple/mat_log_maple.json) |
| `mat_log_maple_uncut_long` | Long Maple Uncut Log | — | — | [mat_log_maple_uncut_long.json](materials/mat_log_maple_uncut_long/mat_log_maple_uncut_long.json) |
| `mat_log_maple_uncut_medium` | Medium Maple Uncut Log | — | — | [mat_log_maple_uncut_medium.json](materials/mat_log_maple_uncut_medium/mat_log_maple_uncut_medium.json) |
| `mat_log_maple_uncut_small` | Small Maple Uncut Log | — | — | [mat_log_maple_uncut_small.json](materials/mat_log_maple_uncut_small/mat_log_maple_uncut_small.json) |
| `mat_log_oak` | Oak Log | — | — | [mat_log_oak.json](materials/mat_log_oak/mat_log_oak.json) |
| `mat_log_oak_uncut_long` | Long Oak Uncut Log | — | — | [mat_log_oak_uncut_long.json](materials/mat_log_oak_uncut_long/mat_log_oak_uncut_long.json) |
| `mat_log_oak_uncut_medium` | Medium Oak Uncut Log | — | — | [mat_log_oak_uncut_medium.json](materials/mat_log_oak_uncut_medium/mat_log_oak_uncut_medium.json) |
| `mat_log_oak_uncut_small` | Small Oak Uncut Log | — | — | [mat_log_oak_uncut_small.json](materials/mat_log_oak_uncut_small/mat_log_oak_uncut_small.json) |
| `mat_log_pine` | Pine Log | — | — | [mat_log_pine.json](materials/mat_log_pine/mat_log_pine.json) |
| `mat_log_pine_uncut_long` | Long Pine Uncut Log | — | — | [mat_log_pine_uncut_long.json](materials/mat_log_pine_uncut_long/mat_log_pine_uncut_long.json) |
| `mat_log_pine_uncut_medium` | Medium Pine Uncut Log | — | — | [mat_log_pine_uncut_medium.json](materials/mat_log_pine_uncut_medium/mat_log_pine_uncut_medium.json) |
| `mat_log_pine_uncut_small` | Small Pine Uncut Log | — | — | [mat_log_pine_uncut_small.json](materials/mat_log_pine_uncut_small/mat_log_pine_uncut_small.json) |
| `mat_log_poplar_uncut_long` | Long Poplar Uncut Log | — | — | [mat_log_poplar_uncut_long.json](materials/mat_log_poplar_uncut_long/mat_log_poplar_uncut_long.json) |
| `mat_log_poplar_uncut_medium` | Medium Poplar Uncut Log | — | — | [mat_log_poplar_uncut_medium.json](materials/mat_log_poplar_uncut_medium/mat_log_poplar_uncut_medium.json) |
| `mat_log_poplar_uncut_small` | Small Poplar Uncut Log | — | — | [mat_log_poplar_uncut_small.json](materials/mat_log_poplar_uncut_small/mat_log_poplar_uncut_small.json) |
| `mat_log_willowood_uncut_long` | Long Willowood Uncut Log | — | — | [mat_log_willowood_uncut_long.json](materials/mat_log_willowood_uncut_long/mat_log_willowood_uncut_long.json) |
| `mat_log_willowood_uncut_medium` | Medium Willowood Uncut Log | — | — | [mat_log_willowood_uncut_medium.json](materials/mat_log_willowood_uncut_medium/mat_log_willowood_uncut_medium.json) |
| `mat_log_willowood_uncut_small` | Small Willowood Uncut Log | — | — | [mat_log_willowood_uncut_small.json](materials/mat_log_willowood_uncut_small/mat_log_willowood_uncut_small.json) |
| `mat_pelt_cow` | Cow Hide Pelt | ✅ Yes | — | [mat_pelt_cow.json](materials/mat_pelt_cow/mat_pelt_cow.json) |
| `mat_pelt_goat` | Goat Skin Pelt | ✅ Yes | — | [mat_pelt_goat.json](materials/mat_pelt_goat/mat_pelt_goat.json) |
| `mat_pelt_sheep` | Sheep Fleece Pelt | ✅ Yes | — | [mat_pelt_sheep.json](materials/mat_pelt_sheep/mat_pelt_sheep.json) |
| `mat_pile_bedding_stone_large` | Large Bedding Stone Pile | — | — | [mat_pile_bedding_stone_large.json](materials/mat_pile_bedding_stone_large/mat_pile_bedding_stone_large.json) |
| `mat_pile_bedding_stone_medium` | Medium Bedding Stone Pile | — | — | [mat_pile_bedding_stone_medium.json](materials/mat_pile_bedding_stone_medium/mat_pile_bedding_stone_medium.json) |
| `mat_pile_bedding_stone_small` | Small Bedding Stone Pile | — | — | [mat_pile_bedding_stone_small.json](materials/mat_pile_bedding_stone_small/mat_pile_bedding_stone_small.json) |
| `mat_pile_dirt_large` | Large Dirt Pile | — | — | [mat_pile_dirt_large.json](materials/mat_pile_dirt_large/mat_pile_dirt_large.json) |
| `mat_pile_dirt_medium` | Medium Dirt Pile | — | — | [mat_pile_dirt_medium.json](materials/mat_pile_dirt_medium/mat_pile_dirt_medium.json) |
| `mat_pile_dirt_small` | Small Dirt Pile | — | — | [mat_pile_dirt_small.json](materials/mat_pile_dirt_small/mat_pile_dirt_small.json) |
| `mat_pile_gravel_large` | Large Gravel Pile | — | — | [mat_pile_gravel_large.json](materials/mat_pile_gravel_large/mat_pile_gravel_large.json) |
| `mat_pile_gravel_medium` | Medium Gravel Pile | — | — | [mat_pile_gravel_medium.json](materials/mat_pile_gravel_medium/mat_pile_gravel_medium.json) |
| `mat_pile_gravel_small` | Small Gravel Pile | — | — | [mat_pile_gravel_small.json](materials/mat_pile_gravel_small/mat_pile_gravel_small.json) |
| `mat_pile_logs_birch_large` | Large Birch Log Pile | — | — | [mat_pile_logs_birch_large.json](materials/mat_pile_logs_birch_large/mat_pile_logs_birch_large.json) |
| `mat_pile_logs_birch_medium` | Medium Birch Log Pile | — | — | [mat_pile_logs_birch_medium.json](materials/mat_pile_logs_birch_medium/mat_pile_logs_birch_medium.json) |
| `mat_pile_logs_birch_small` | Small Birch Log Pile | — | — | [mat_pile_logs_birch_small.json](materials/mat_pile_logs_birch_small/mat_pile_logs_birch_small.json) |
| `mat_pile_logs_maple_large` | Large Maple Log Pile | — | — | [mat_pile_logs_maple_large.json](materials/mat_pile_logs_maple_large/mat_pile_logs_maple_large.json) |
| `mat_pile_logs_maple_medium` | Medium Maple Log Pile | — | — | [mat_pile_logs_maple_medium.json](materials/mat_pile_logs_maple_medium/mat_pile_logs_maple_medium.json) |
| `mat_pile_logs_maple_small` | Small Maple Log Pile | — | — | [mat_pile_logs_maple_small.json](materials/mat_pile_logs_maple_small/mat_pile_logs_maple_small.json) |
| `mat_pile_logs_oak_large` | Large Oak Log Pile | — | — | [mat_pile_logs_oak_large.json](materials/mat_pile_logs_oak_large/mat_pile_logs_oak_large.json) |
| `mat_pile_logs_oak_medium` | Medium Oak Log Pile | — | — | [mat_pile_logs_oak_medium.json](materials/mat_pile_logs_oak_medium/mat_pile_logs_oak_medium.json) |
| `mat_pile_logs_oak_small` | Small Oak Log Pile | — | — | [mat_pile_logs_oak_small.json](materials/mat_pile_logs_oak_small/mat_pile_logs_oak_small.json) |
| `mat_pile_logs_pine_large` | Large Pine Log Pile | — | — | [mat_pile_logs_pine_large.json](materials/mat_pile_logs_pine_large/mat_pile_logs_pine_large.json) |
| `mat_pile_logs_pine_medium` | Medium Pine Log Pile | — | — | [mat_pile_logs_pine_medium.json](materials/mat_pile_logs_pine_medium/mat_pile_logs_pine_medium.json) |
| `mat_pile_logs_pine_small` | Small Pine Log Pile | — | — | [mat_pile_logs_pine_small.json](materials/mat_pile_logs_pine_small/mat_pile_logs_pine_small.json) |
| `mat_pile_logs_poplar_large` | Large Poplar Log Pile | ✅ Yes | — | [mat_pile_logs_poplar_large.json](materials/mat_pile_logs_poplar_large/mat_pile_logs_poplar_large.json) |
| `mat_pile_logs_poplar_medium` | Medium Poplar Log Pile | ✅ Yes | — | [mat_pile_logs_poplar_medium.json](materials/mat_pile_logs_poplar_medium/mat_pile_logs_poplar_medium.json) |
| `mat_pile_logs_poplar_small` | Small Poplar Log Pile | ✅ Yes | — | [mat_pile_logs_poplar_small.json](materials/mat_pile_logs_poplar_small/mat_pile_logs_poplar_small.json) |
| `mat_pile_logs_willow_large` | Large Willowood Log Pile | ✅ Yes | — | [mat_pile_logs_willow_large.json](materials/mat_pile_logs_willow_large/mat_pile_logs_willow_large.json) |
| `mat_pile_logs_willow_medium` | Medium Willowood Log Pile | ✅ Yes | — | [mat_pile_logs_willow_medium.json](materials/mat_pile_logs_willow_medium/mat_pile_logs_willow_medium.json) |
| `mat_pile_logs_willow_small` | Small Willowood Log Pile | ✅ Yes | — | [mat_pile_logs_willow_small.json](materials/mat_pile_logs_willow_small/mat_pile_logs_willow_small.json) |
| `mat_pile_mulch_large` | Large Mulch Pile | — | — | [mat_pile_mulch_large.json](materials/mat_pile_mulch_large/mat_pile_mulch_large.json) |
| `mat_pile_mulch_medium` | Medium Mulch Pile | — | — | [mat_pile_mulch_medium.json](materials/mat_pile_mulch_medium/mat_pile_mulch_medium.json) |
| `mat_pile_mulch_small` | Small Mulch Pile | — | — | [mat_pile_mulch_small.json](materials/mat_pile_mulch_small/mat_pile_mulch_small.json) |
| `mat_pile_sand_large` | Large Sand Pile | — | — | [mat_pile_sand_large.json](materials/mat_pile_sand_large/mat_pile_sand_large.json) |
| `mat_pile_sand_medium` | Medium Sand Pile | — | — | [mat_pile_sand_medium.json](materials/mat_pile_sand_medium/mat_pile_sand_medium.json) |
| `mat_pile_sand_small` | Small Sand Pile | — | — | [mat_pile_sand_small.json](materials/mat_pile_sand_small/mat_pile_sand_small.json) |
| `mat_rope` | Rope | — | — | [mat_rope.json](materials/mat_rope/mat_rope.json) |
| `mat_stone` | Stone | — | — | [mat_stone.json](materials/mat_stone/mat_stone.json) |
| `mat_wood_logs_stack` | Wood Logs Stack | — | — | [mat_wood_logs_stack.json](materials/mat_wood_logs_stack/mat_wood_logs_stack.json) |
| `mat_wool_fleece` | Wool Fleece | ✅ Yes | — | [mat_wool_fleece.json](materials/mat_wool_fleece/mat_wool_fleece.json) |

### 📂 [Ingredients](ingredients/) (15 items)

| Item ID | Display Name | 3D Model | Growth | Plugin Manifest |
| :--- | :--- | :---: | :---: | :--- |
| `ingredient_beef` | Raw Beef Cut | ✅ Yes | — | [ingredient_beef.json](ingredients/ingredient_beef/ingredient_beef.json) |
| `ingredient_chicken` | Raw Chicken Breast | ✅ Yes | — | [ingredient_chicken.json](ingredients/ingredient_chicken/ingredient_chicken.json) |
| `ingredient_corn` | Sweet Yellow Corn | ✅ Yes | — | [ingredient_corn.json](ingredients/ingredient_corn/ingredient_corn.json) |
| `ingredient_cotton` | Cotton | ✅ Yes | — | [ingredient_cotton.json](ingredients/ingredient_cotton/ingredient_cotton.json) |
| `ingredient_egg` | Fresh Farm Egg | ✅ Yes | — | [ingredient_egg.json](ingredients/ingredient_egg/ingredient_egg.json) |
| `ingredient_fillet_bass` | Bass Fillet | ✅ Yes | — | [ingredient_fillet_bass.json](ingredients/ingredient_fillet_bass/ingredient_fillet_bass.json) |
| `ingredient_fillet_catfish` | Catfish Fillet | ✅ Yes | — | [ingredient_fillet_catfish.json](ingredients/ingredient_fillet_catfish/ingredient_fillet_catfish.json) |
| `ingredient_fillet_crappie` | Crappie Fillet | ✅ Yes | — | [ingredient_fillet_crappie.json](ingredients/ingredient_fillet_crappie/ingredient_fillet_crappie.json) |
| `ingredient_fillet_salmon` | Salmon Fillet | ✅ Yes | — | [ingredient_fillet_salmon.json](ingredients/ingredient_fillet_salmon/ingredient_fillet_salmon.json) |
| `ingredient_fillet_trout` | Trout Fillet | ✅ Yes | — | [ingredient_fillet_trout.json](ingredients/ingredient_fillet_trout/ingredient_fillet_trout.json) |
| `ingredient_fillet_walleye` | Walleye Fillet | ✅ Yes | — | [ingredient_fillet_walleye.json](ingredients/ingredient_fillet_walleye/ingredient_fillet_walleye.json) |
| `ingredient_herbs` | Fresh Culinary Herbs | ✅ Yes | — | [ingredient_herbs.json](ingredients/ingredient_herbs/ingredient_herbs.json) |
| `ingredient_pork` | Raw Pork Chop | ✅ Yes | — | [ingredient_pork.json](ingredients/ingredient_pork/ingredient_pork.json) |
| `ingredient_sunflower` | Sunflower Heads | ✅ Yes | — | [ingredient_sunflower.json](ingredients/ingredient_sunflower/ingredient_sunflower.json) |
| `ingredient_wheat` | Milled Wheat Grain | ✅ Yes | — | [ingredient_wheat.json](ingredients/ingredient_wheat/ingredient_wheat.json) |
