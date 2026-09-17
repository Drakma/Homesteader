# Homesteader Item & HUD Asset Organization Guide

Complete structured taxonomy of all game items and HUD assets across survival, farming, ranching, logging, fishing, building, utilities, and UI systems.

All icons are **128 × 128 px** transparent RGBA PNGs featuring cohesive **3D low-poly faceted render** styling, zero borders, and comfortable 12px margins.

## Folder Hierarchy & Item Distribution

### `farming/`
- **`seeds/`**: Seeds for planting crops in tilled farm plots
  - *Icons (11)*: `seed_corn.png`, `seed_tomato.png`, `seed_carrot.png`, `seed_wheat.png`, `seed_potato.png`, `seed_pumpkin.png`, `seed_strawberry.png`, `seed_sunflower.png`, `seed_cotton.png`, `seed_herb.png`, `icon_seeds.png`
- **`crops/`**: Raw crops freshly harvested from farm fields
  - *Icons (11)*: `crop_corn.png`, `crop_tomato.png`, `crop_carrot.png`, `crop_wheat.png`, `crop_potato.png`, `crop_pumpkin.png`, `crop_strawberry.png`, `crop_sunflower.png`, `crop_cotton.png`, `crop_herb.png`, `icon_wheat.png`
- **`produce/`**: Edible produce, fruits, vegetables, and crafted foodstuffs
  - *Icons (11)*: `crop_corn.png`, `crop_tomato.png`, `crop_carrot.png`, `crop_potato.png`, `crop_pumpkin.png`, `crop_strawberry.png`, `food_apple.png`, `food_bread.png`, `food_stew.png`, `food_cheese.png`, `icon_bread.png`
- **`fertilizer/`**: Soil amendments, organic fertilizers, and growth enhancers
  - *Icons (1)*: `mat_fertilizer.png`
- **`irrigation/`**: Irrigation pipes, sprinkler heads, and watering apparatus
  - *Icons (1)*: `water_pipe.png`

### `ranching/`
- **`animals/`**: Livestock species, breeds, and domestic animal tokens
  - *Icons*: Ready for future expansion items
- **`meats/`**: Butchered raw meats and cuts
  - *Icons (6)*: `meat_chicken.png`, `meat_beef.png`, `meat_pork.png`, `meat_mutton.png`, `meat_goat.png`, `animal_meat.png`
- **`pelts/`**: Cured hides, raw pelts, and tanned leathers
  - *Icons (4)*: `mat_leather.png`, `pelt_cow.png`, `pelt_sheep.png`, `pelt_goat.png`
- **`byproducts/`**: Animal byproducts: milk, eggs, wool fleece, cheese, truffles, feathers
  - *Icons (6)*: `animal_egg.png`, `animal_milk.png`, `animal_wool.png`, `animal_truffle.png`, `mat_feather.png`, `food_cheese.png`
- **`feed/`**: Animal fodder, grain feed, and trough rations
  - *Icons (3)*: `crop_wheat.png`, `crop_corn.png`, `icon_wheat.png`

### `logging/`
- **`wood/`**: Timber logs, milled lumber, structural beams, and heavy equipment
  - *Icons (4)*: `wood_logs_stack.png`, `mat_lumber.png`, `icon_wood_log.png`, `tool_chainsaw.png`
- **`fuel/`**: Chopped firewood, kindling, and wood briquettes
  - *Icons (1)*: `fuel_firewood.png`
- **`saplings/`**: Tree seedlings, saplings, and nursery starts
  - *Icons (1)*: `tree_sapling.png`
- **`byproducts/`**: Woodchips, sawdust, bark mulch, and tree sap taps
  - *Icons (1)*: `tree_tap.png`

### `fishing/`
- **`fish/`**: Freshwater and saltwater fish species (trout, bass, salmon)
  - *Icons (3)*: `fish_trout.png`, `fish_bass.png`, `fish_salmon.png`
- **`tackle/`**: Fishing rods, reels, hooks, lines, and lures
  - *Icons (2)*: `tool_fishing_rod.png`, `fishing_lure.png`
- **`bait/`**: Earthworms, insect larvae, dough bait, and chum
  - *Icons (1)*: `fishing_bait.png`
- **`equipment/`**: Tackle boxes, landing nets, fish baskets, and waders
  - *Icons (2)*: `tool_fishing_rod.png`, `fishing_lure.png`

### `building/`
- **`materials/`**: Primary building blocks: stone blocks, metal plates, glass panes, ropes
  - *Icons (5)*: `mat_stone.png`, `mat_metal.png`, `mat_glass.png`, `mat_rope.png`, `mat_lumber.png`
- **`structures/`**: Pre-fabricated buildings: cabins, sheds, barns, coops, greenhouses
  - *Icons*: Ready for future expansion items
- **`fencing/`**: Boundary fencing: split rail wood, barbed wire, electric fence
  - *Icons*: Ready for future expansion items
- **`hardware/`**: Fasteners: construction nails, metal brackets, hinges, screws
  - *Icons (1)*: `hardware_nails.png`
- **`roads/`**: Ground surfaces: dirt path paving, gravel road gravel
  - *Icons*: Ready for future expansion items

### `tools/`
- **`hand_tools/`**: Manual hand tools: hoes, axes, pickaxes, shovels, sickles, hammers, wrenches
  - *Icons (10)*: `tool_hoe.png`, `tool_axe.png`, `tool_pickaxe.png`, `tool_shovel.png`, `tool_sickle.png`, `tool_hammer.png`, `tool_wrench.png`, `icon_axe.png`, `icon_pickaxe.png`, `icon_shovel.png`
- **`equipment/`**: Power gear & utility: chainsaws, watering cans, planter seedbags
  - *Icons (4)*: `tool_chainsaw.png`, `tool_watering_can.png`, `tool_seedbag.png`, `icon_watering_can.png`
- **`measuring/`**: Survey stakes, tape measures, plumb bobs, soil pH meters
  - *Icons*: Ready for future expansion items

### `electricity/`
- **`generation/`**: Power generation: solar PV panels, wind turbines, fuel generators
  - *Icons (4)*: `item_solar_panel.png`, `item_wind_turbine.png`, `item_generator.png`, `icon_solar.png`
- **`storage/`**: Energy storage: deep-cycle battery banks, rechargeable cells
  - *Icons (1)*: `icon_battery.png`
- **`fuel/`**: Combustion fuels: gasoline canisters, propane tanks
  - *Icons (2)*: `fuel_gasoline.png`, `fuel_propane.png`
- **`wiring/`**: Transmission: high-voltage cables, conduits, transformers
  - *Icons (1)*: `internet_cable.png`

### `water/`
- **`sources/`**: Water procurement: deep wells, rainwater catchment, electric pumps
  - *Icons (2)*: `water_pump.png`, `icon_water.png`
- **`storage/`**: Water reserves: cistern tanks, 55-gal drums, jugs
  - *Icons*: Ready for future expansion items
- **`piping/`**: Plumbing: PVC pipes, shutoff valves, brass fittings
  - *Icons (1)*: `water_pipe.png`
- **`treatment/`**: Purification: sediment filters, reverse osmosis, UV sterilizers
  - *Icons (1)*: `water_filter.png`

### `sewage/`
- **`waste/`**: Sanitation: outhouses, blackwater holding tanks, waste drums
  - *Icons (1)*: `sewage_septic_tank.png`
- **`treatment/`**: Bioconversion: wooden compost bins, aerators, microbial digesters
  - *Icons (1)*: `sewage_compost_bin.png`
- **`drainage/`**: Drainage: septic leach fields, perforated pipes, septic tanks
  - *Icons (1)*: `sewage_septic_tank.png`

### `internet/`
- **`satellite_antennas/`**: Off-grid telemetry: phased-array satellite dishes, parabolic receivers
  - *Icons (1)*: `internet_satellite_dish.png`
- **`routers_networking/`**: Distribution: Wi-Fi mesh routers, access point antennas, switches
  - *Icons (1)*: `internet_router.png`
- **`cabling/`**: Connectivity: weather-rated Cat6 Ethernet cables, fiber optic drops
  - *Icons (1)*: `internet_cable.png`

### `hud/`
- **`status/`**: Player vitals: health heart, stamina lightning bolt, hunger, hydration
  - *Icons (2)*: `icon_heart.png`, `icon_stamina.png`
- **`resources/`**: Homestead metrics: currency gold coin, water volume, solar flux, battery kWh
  - *Icons (4)*: `icon_coin.png`, `icon_water.png`, `icon_solar.png`, `icon_battery.png`
- **`hotbar/`**: Item selector trays, active highlight frames, slot wells
  - *Icons (3)*: `compact_hotbar_10slots.png`, `compact_hotbar_slot.png`, `compact_selector_active.png`
- **`bars/`**: Compound status pills, sundial clock capsules, resource bars
  - *Icons (3)*: `compact_player_status.png`, `compact_time_season.png`, `compact_resources.png`
- **`buttons/`**: UI interaction buttons: normal, hover, active, disabled
  - *Icons (4)*: `compact_btn_slate_normal.png`, `compact_btn_slate_hover.png`, `compact_btn_green_normal.png`, `compact_btn_amber_normal.png`
- **`windows/`**: Dialog frames, inventory backdrops, modal windows
  - *Icons (1)*: `compact_window_dialog.png`

