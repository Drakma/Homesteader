# Water flow

Every part of a water line has a FLOW RATING (manifest `properties.flow_lph`, liters an hour): the most it can pass. Nothing trips. A part that is too small only SLOWS the water, and WAILA
names the part that limits it. Code: `Growth/WaterFlow.cs` (a partial of `WireNetwork`), hooks in `Growth/Wiring.cs` and `Growth/WaterTap.cs`. Data: `tools/set_water_ratings.py`.

## The rule

The water that can get from one part to another is the NARROWEST pipe or part on the way (`WireNetwork.FlowCaps`); of several ways the best counts. What moves is held to it.

## Ratings (L/h)

| Part | Flow | Notes |
|---|---|---|
| PVC pipe | half inch 900, one inch 2400, two inch 9000 | by diameter (the item's `flow_lph`) |
| Water pump | 1200, 2000, 2400, 3600 | submersible well pumps 1400 to 2900 |
| Filters | sediment 240, reverse osmosis 120, spin-down 3000, UV chamber 1800 | = the older `max_filter_throughput_lpm` x 60 |
| Large filters | whole-house reverse osmosis 470 (about 3,000 gallons a day), large 2 inch spin-down 9000 | floor-standing, sold at the water treatment store |
| Spigot, outdoor and post | 900 | |
| Faucet, indoor | 480 | |
| House water inlet | 3000 | |
| Tank fittings | rain barrel 600, IBC tote 1800, cisterns 1800 to 3600, pressure tank 3600, water heater 900 | |
| Hand pump | 480 | |

## Reverse osmosis waste

A reverse osmosis filter rejects part of the water it takes in to the drain: only its RECOVERY (manifest `properties.filter_recovery_pct`) comes out as clean product. Its flow rating is the PRODUCT flow.
Under-sink unit: 33 % (about 2 L rejected for every liter made). Whole-house unit: 50 % (1 L rejected for every liter made). The rest is lost down the drain: there is no sewer connection for it yet.

- The flow that gets past a reverse osmosis filter is `min(what comes in x recovery, its rating)` (`FlowCap.Rec` carries the share along the path).
- **A tap drawing through one** (`DrawWaterAt`, `DrawWater`): the tank loses `delivered / recovery`: 10 L from a 33 % unit takes 30 L from the tank.
- **A water pump moving water through one** (`TickWaterPumps`): it drains `moved / recovery` from the cistern and the tanks on the other side get `moved`; `WireNode.WastedLph` is the rest (WAILA "Wasting").
- **A well filling tanks through one**: only the recovery share arrives (the aquifer is not drawn down, so nothing else is lost).
- WAILA on the filter shows `Recovery` and the waste per liter made.

## What it limits

- **A well filling a tank** (`PumpInto`, `PipedFlowLph`): the pump's flow (or the aquifer's), held to the best path to a tank with room.
- **A water pump moving stored water** (`TickWaterPumps`, `PumpLimitLph`): its flow, held to the narrowest way between the cistern it pulls from and the tanks it fills. `WireNode.FlowLimitedBy` names the part.
- **A tap filling a container** (`WaterTap`): at most its flow for one fill (`TapFillHours`, 72 game seconds): a spigot post gives 18 L a fill, a faucet 9.6 L. A bigger container takes several fills, and a toast says what limits the tap.
  A tap on a building is held to the building's supply line (`SiteSupplyFlowLph`, the best inlet) as well as its own rating.
- **The supply that keeps a plumbed tank full** (`TickPlumbed`): 1500 L/h at most, held to the supply line.
- **The flow map** (WAILA "Flow" on a part): what reaches a part from a well is held to the way to it.

## WAILA

A part of a water line shows `Rated flow` and, when the water reaching it is held back, `Limited by` the part that does it (a pipe, a filter, an inlet...). A pump shows what it moves and what limits it.

## Changing a rating

Edit `RATINGS` in `tools/set_water_ratings.py` (or the item's Flow field in the asset kit), run it, then `tools/generate_unity_asset_catalog.py` and `tools/package_catalog_as_mods.py`.
A new kind of part that should limit the flow goes into `WireNetwork.NodeFlowLph`.
