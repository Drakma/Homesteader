# Drilled wells

Electric drilled wells: a submersible pump down the bore, a PVC drop pipe bringing the water up, a wellhead on top, a sub panel on its post wired to a breaker box, and a buried water line to the tanks it fills.

## The water table

`Growth/WaterTable.cs`: every spot has a depth to water (8 to 85 m) and an aquifer yield (600 to 4200 L/h, the most any pump can draw there). Both are smooth noise fixed by the world seed (nothing saved); within a few metres of the water level the water is nearer. Hold a well blueprint over the ground and the look-at panel shows the depth, the max flow and what the pump stage will need there (pipe and cable).

## The structures

`water_well_concrete` (a concrete wellhead) and `water_well_wooden` (a small wooden well house), built in three stages (models and manifests: `tools/make_wells.py`):

1. Drill: the bore and its casing (shovels, pickaxe).
2. Pump: `~well_pump` (any of the three pumps), `~pipe_pvc_one_inch` and `~romex_12_2` BY DEPTH, PVC cement (pipe wrench, a saw, wire cutters).
3. Wellhead: concrete (bagged mix or cement, sand, aggregate, with water and a wheelbarrow or mixer) or lumber and screws; and the post the sub panel mounts on.

A depth-scaled recipe line has `per_depth_m`: it needs `quantity + per_depth_m x depth` (whole units). The kit's recipe editor has the field ("+/m deep") beside the quantity; `tools/recipe_format.py` keeps it; the site works it out from where it stands (`ConstructionSite.NeedOf`). The pump that goes down is remembered (`PumpId`, saved).

## Pumps

They replace every earlier submersible pump (`water_pump_submersible_3hp` and `waste_pump_submersible_deep` are gone): `water_pump_submersible_half_hp` 1/2 HP, 1400 L/h, 900 W; `water_pump_submersible_three_quarter_hp` 3/4 HP, 2300 L/h, 1200 W; `water_pump_submersible_1hp` 1 HP, 2900 L/h, 1500 W (manifest `flow_lph`, `power_draw_w`; equivalency `~well_pump`).

## Power

The well sub panel (`electricity_panel_well_sub`, wire_role ac_panel) is fitted on a finished well by left clicking the well with it in hand (the structure's `attach_item`); the well then IS that AC panel for the wiring: wire it to a breaker box with AC wire (long runs are buried). While the panel is energized and a tank it is piped to has room, the pump runs: its `power_draw_w` is load on that system (Grid OS shows it), and in a brownout below 85% the pump stalls.

## Water

With a pipe wrench in hand, right click the well, then a tank (`water_cistern_poly_3800l`, `water_ibc_tote_1000l`, `water_barrel_rain_200l`, `water_pressuretank_well`: wire_role water_tank, capacity from `capacity_l`), or tank to tank: a buried water line made of PVC pipe within reach (`pipe_pvc_one_inch` 3 m a length, its stacks 30 and 60 m). The pump fills the tanks at its flow or the aquifer's yield, whichever is less, first tank first. A tank's water is saved; WAILA shows it, and on the well its depth, max flow, pump and whether it is pumping.

## Treatment and the pump house

Well water comes up RAW. Pipe it through the filter stages before the tanks: a sediment filter (`water_filter_spin_down_sediment`, `water_filter`), a carbon filter (`water_filter_canister_bigblue`, `water_filter_reverse_osmosis`) and a UV sterilizer (`water_sterilizer_uv_chamber`) (manifest `filter_stage`, wire_role water_filter). Water that reaches a tank through all three stages, in any order, is clean (drinkable); anything that missed one is raw (`WireNode.RawL`, saved). WAILA on a tank shows its quality.

The **Pump House** (`struct_pump_house`, 2.4 x 2.4 m, a small tool shed: `tools/make_building_stages.py`) is the place for the filters, the pressure tank and the water heater. Like the tool shed, its stages ask for no materials.

The **Electric Water Heater** (`water_heater_electric_190l`, 190 L, `heater_w` 4500: `tools/make_water_heater.py`) is a tank on the water line that heats what it holds to 55 C while the building it stands in has power (the pump house wired to a breaker box); its element is load on that system while it heats, cold well water mixes in as it fills, and it cools slowly when unpowered. Its temperature is saved.

Within 3 m a water line is a short straight pipe (filter to filter in the pump house); longer runs are buried.

## Into the building

A **Building Water Inlet** (`water_inlet_house`, mounted on the outside of a building and going THROUGH the wall like the wire entry, `attach_through`: a valve plate on each side, the riser out of the ground outside; wire_role water_inlet: `tools/make_water_fixtures.py`) piped with the pipe wrench to a tank, a filter or a well gives the building water: the water in the tanks it reaches. Its **taps** draw from those tanks, nearest first:

- **Outdoor Spigot** (`water_spigot_outdoor`, outside) and **Utility Faucet** (`water_faucet_indoor`, inside): both give whatever water the building is supplied with, raw or filtered (raw water will make the player sick: not yet done).

Right click a tap with a bucket, jug or watering can (a liquid container that takes `liquid_water`) to fill it (`Growth/WaterTap.cs`, `WireNetwork.DrawWater`). WAILA on the inlet and the taps shows the water the building has and how much of it is clean.

### The spigot post

`water_spigot_post` (`tools/make_spigot_post.py`) is a spigot that stands in the yard on a wooden post. It has the same role as the wall spigots (`wire_role: water_spigot`) but is
not mounted on a building, so it is PIPED: pipe wrench and PVC pipe, to a water tank, a filter or a well (`WireNetwork.KindFor`; a spigot on a building refuses a pipe). A right click
with a bucket, jug or watering can in hand fills it from the tanks its pipe reaches (`WaterTap` > `WireNetwork.DrawWaterAt`), raw or filtered as they hold it.

**Raw Water** (`liquid_water_raw`, a liquids item): what a container holds when the water it was filled with was raw. Every water container (jugs, cisterns, barrels, the watering can, the pressure tank, the water heater) takes it as well as clean water. A toolbar slot remembers the liquid in its container (`ToolbarSlotData.LiquidId`, saved); any raw water in it makes the whole container raw.

### Pipe size and flow

A water line is laid with PVC pipe of any of three sizes, and the size limits how much water it carries (`properties.flow_lph` on the pipe, set by `tools/set_wiring_data.py`):

| Pipe | Carries | Against the pumps (1,400 / 2,300 / 2,900 L/h) |
|---|---|---|
| `pipe_pvc_half_inch` | 900 L/h | throttles every pump |
| `pipe_pvc_one_inch` | 2,400 L/h | throttles only the biggest pump |
| `pipe_pvc_two_inch` | 9,000 L/h | never the limit |

A way from the well to a tank is as good as its NARROWEST pipe (`WireNetwork.PipeCaps`), and where there are several ways the best counts. What leaves the well each hour is the
least of the pump's flow, the aquifer's yield and what the pipes carry to the best-piped tank that still has room (`PipedFlowLph`); each tank then gets no more than its own way
carries. The look-at panel's Pump row shows what gets through and says when the pipe is the limit. A line uses the pipe within reach that is long enough, taking the shortest
stock first, so hold only the size you mean to lay. Filling a bucket at a tap is not slowed by pipe size, and a propane line has one size.

Simplification: two tanks behind one narrow pipe can each be given that pipe's full flow in the same hour when the pump has more to give; a chain (well, pipe, tank, pipe, tank)
is exact.

## Pumps between tanks

Stored water only moves with a pump. A **water pump** (`water_pump_low_capacity` 1200 L/h, `water_pump` 2000, `water_pump_jet_shallow_well` 2400, `water_pump_high_capacity` 3600: wire_role water_pump, `flow_lph`, `power_draw_w`) piped between a cistern and what it feeds pulls from the side of it whose tanks hold the most and pushes to the tanks on its other sides that have room, while the building it stands in has power (its watts are load while it runs). Water that passes every filter stage on the way out arrives clean. A building's water inlet is just a pipe through the wall: a pump inside pulls through it from a cistern outside. Inlets pipe to each other too (one building's water on to the next), and to spigot posts and pumps. The look-at panel shows a running pump's flow on every part it moves water through (`WireNetwork.FlowMap`). **Plumbed in:** a water tank standing in a finished building with no pipe of its own (a water heater, a pressure tank) is part of that building's water: the building's supply keeps it full (up to 1500 L/h, `WireNetwork.TickPlumbed`) and the building's taps and fixtures draw from it first. Pipe it yourself and it is a tank on the line like any other.

Inside a building a pipe between two parts that stand apart runs out to the nearest wall, along the inner face of the walls (round corners, under windows, over doors) at the higher end's height, and back out (`WireRouter.RouteInside`); parts side by side get a short straight pipe.

A building's taps draw from a **pressurized** tank (`pressurized`: the pressure tank, the water heater) directly, and from a plain cistern only through a powered water pump on the way (`WireNetwork.TapSources`). The well's own pump still pushes fresh water to every tank it reaches.

Water takes the SHORTEST way through the lines: the filter stages a part shows are those on the shortest way from the well (a filter further round a loop does not count).

Every part of a water line, not only the pipes, has a flow rating that limits the water (filters, taps, the house inlet, pumps): see `docs/WATER_FLOW.md`.
