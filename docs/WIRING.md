# Wiring the off-grid solar system

`Assets/Scripts/Growth/Wiring.cs` (`WireNode`, `WireNetwork`, `WireTool`). Data: `tools/set_wiring_data.py` (idempotent), schema fields `wire_role`, `wire_kind`, `wire_length_m` (asset kit "Wiring Role", "Wire Kind", "Wire Length").

## The chain

Solar Panel > Wall Entry > DC Breaker Box > MPPT Charge Controller > Battery > Inverter, and an inverter feeds an AC panel (the outdoor breaker box on a building) with AC wire, directly or through a wall entry (inverter > wall entry > AC panel, AC wire both legs).
A DC bus bar joins any DC devices (panel, wall entry, DC breaker box, MPPT, battery, inverter, another bus bar). It does nothing but carry the current: every device wired to a bar (and to bars wired to it) counts as wired to every other, so for example MPPT > bus bar > battery is the same as MPPT > battery.

| `wire_role` | Items |
|---|---|
| `solar_panel` | a solar mount (`electricity_solar_mount_*`, roof and ground); it makes power only once a panel is fitted |
| `wall_entry` | `electricity_wall_entry_wire` |
| `dc_breaker` | `electricity_breaker_box_dc_32a / 64a / 128a` |
| `mppt` | `electricity_controller_mppt_32a / 64a / 128a` |
| `battery` | the 12 V batteries, the wall power batteries and the battery rack |
| `inverter` | `electricity_inverter_hybrid_3kw / 5kw / 10kw` |
| `ac_panel` | the outdoor breaker boxes (`electricity_panel_breaker_outdoor_*`, `electricity_panel_breaker_subpanel`) |
| `busbar` | `electricity_busbar_dc_*` |

## Making a connection

- Wire cutters (`tool_wire_cutters`) in the ACTIVE slot. Over a device the cursor becomes the cutters.
- Right click one device (a line follows the cursor), then right click another. Either order works: panel then entry is entry then panel. Right click anything else to let go.
- The two devices' CONNECTION POINTS are at most **4 m** apart (**40 m** for AC runs and for the outdoor DC run to a solar panel: a run longer than 4 m is buried, coming up in conduit at each end). A connection point is where the wire meets the device, not the middle of its model: along the bottom edge of a wall device (charge controller, inverter, breaker boxes, wall batteries, panels), on top of a battery standing on the floor, the nearer plate of a wall entry, anywhere on a bus bar.
- A coil or spool of the right wire within **4 m of the player** (in the toolbar, or standing on the ground): `dc_indoor` or `dc_outdoor` for DC links, `ac` for inverter to AC panel. A run outside (to a panel) is in conduit, so either DC wire works.
- The run uses the distance between the two connection points plus 0.5 m of slack, counted in metres per coil or spool (`ToolbarSlotData.WireUsed`, `PlacedObject.WireUsed`); an empty spool is used up. The metres used stay with the spool: a partly used one picked up from the ground goes into a slot of its own, and placing or dropping it (the drop key puts it down as a spool) puts the same metres back. Loose items are not used as wire sources, only a spool standing on the ground.
- Right clicking two devices that are already wired cuts the wire (the metres are lost). **Shift + right click** a device with the cutters cuts EVERY wire off it.
- Wire items: DC `electricity_wire_dc_*` (10 m coils, 25 m spools), AC the Romex coils and spools (15 m, 75 m).

## How a wire is drawn (`WireRouting.cs`)

- Between two devices MOUNTED ON WALLS of the same building and on the same side of the walls (both inside, or both outside) the wire is **tacked to the walls**: it leaves the first device and runs at that device's height along the walls with square corners, with a small clip every half metre and at each corner. Wall to wall works: it goes round the corners of the room (or of the building, outside) the shorter way, around the outline of the walls (`ConstructionSite.WallRect`, inset by the wall's thickness inside).
- Where it meets a **window** it dips UNDER it, where it meets a **door** it goes OVER it, with right-angle jogs (found from the model's `Door*` and `Window*` parts).
- It is worked out once (the building's model may still be loading after a load: it tries a few times) and is then just a fixed line and a few clips: no per-frame cost. The wire used is still the straight distance between the connection points plus the slack.
- **Conduit**: every run outside the walls is in conduit, thicker than a bare wire and held by straps: **galvanized steel for AC**, **beige PVC for DC**.
- **Panel to wall entry**: a solar panel on a roof or on the ground runs to the wall entry's outside plate across to the nearest point of the building's outline at the panel's own height (along the eave, or over the ground), straight down or up the wall to the entry's height, then tacked along the walls like any other run (under windows, over doors). All of it in PVC conduit.
- **Anything on a roof, buried**: any buried run (DC, AC, Cat6, water, sewer, propane, fuel) with an end up on a ROOF (a panel, a dish, a yagi) first runs across to the nearest outer wall at that height, down the outside of the wall (clear of windows and doors) to the ground, and only then goes underground (`WireRouter.RoofDescent`, `RouteBuried(a, b, ...)`). Either end, or both.
- Anything else (one end inside and one outside) hangs as a plain sagging wire.

## What it does

A building has electricity only while its AC panel (the outdoor breaker box mounted outside it) is wired to an inverter whose DC chain runs all the way back to a solar panel
(`WireNetwork.IsEnergized`, used by `AttachedObject.HasPower`): without it the lights stay dark. Hover a device (the look-at panel) to see what it is wired to and what the chain still lacks.

## Saving

`GameSave.wires` stores each wire as two references (an entry of `placed[]` or of `attached[]`), its kind, its length and its wire item; `GameSave.SavedSlot.wireUsed` and `SavedPlaced.wireUsed` keep the metres used.

## Sun and the look-at panel

`Growth/SolarSun.cs`: a panel makes its rated watts (`max_power_w`) times the sun. The sun is 0 at sunrise, sunset and all night, a half sine between them with the peak at solar noon, times a weather share (sunny 100%, partly cloudy 75%, cloudy 30%, fog 35%, snow 25%, rain 20%, thunderstorm 12%, blizzard 10%). Day length follows the season. Looking at any wired part shows its ratings (power, current, voltage, capacity from `capacity_wh` / `voltage_v`) and the live numbers: panel output, what reaches a controller, battery or inverter, the inverter's output (held to the controller and inverter ratings, only when its chain is complete) and what an AC panel is fed. Batteries store charge: the panels' output (only through a charge controller, held to its rating) fills every battery wired on the same DC side, in game time, and the look-at panel shows the level; nothing draws them down yet (no building load exists). The level is saved (`chargeWh` on placed and attached entries).

## HUD and Grid OS

The HUD electricity value is the energy stored in every battery (`WireNetwork.TotalStoredWh`, shown as MJ or kWh by the unit setting). The Grid OS phone app lists one section per separate wired system (`WireNetwork.Systems`): devices that share a wire are one system, however many buildings it spans (farmhouse + tool shed on one wire is one section, a garage with its own is another), named after the buildings its devices are mounted on. Each section shows solar generation, the battery bank (percent and stored energy) and the inverter output.

Tap a system's group in Grid OS for its detail page: the power flow (sun, batteries, inverter, AC), three graphs of the last 24 game hours (solar output, battery charge, inverter output; one sample every 15 game minutes, `WireNetwork.GridSeries`, drawn by `UI/Phone/GridGraph.cs`), the stats, and every component by kind with its icon and its own stat line (batteries with a charge bar).

## Wind turbines

A finished wind turbine (the work site of `wind_turbine_*`, manifest `wire_role: wind_turbine`) can be wired to an AC panel (an outdoor breaker box or the subpanel) with AC wire: it has its own inverter, so it makes AC. Right click the turbine with the cutters, then the panel. The cable is BURIED (it may run up to 40 m); only a larger galvanized steel conduit shows, rising out of the ground (or the floor, for a panel indoors) to the bottom of the panel. The panel is live while a finished turbine is wired to it and is fed the turbine's output (`WindWatts`). The wire is saved against the turbine's work site (kind 2 in `SavedWire`).

Solar panels can be wired to each other (DC wire): a run of panels wired in a chain, with the last one wired to the wall entry, adds their output (`SolarSun.InputWatts` walks on past a panel).

**Panel groups**: solar panels standing side by side (their edges within 0.45 m) are joined by themselves into a group, with no wire: an unseen DC link of no length (`WireLink.Auto`, `WireNetwork.TickSolarGroups`, scanned about once a second; not drawn, not saved, not cut: Shift + right click with the cutters leaves them). ONE wire from any panel of a group to a wall entry (or a DC breaker box, bus bar ...) carries the whole group's output, and one wire from a panel of one group to a panel of another joins the two groups. Moving a panel away drops it from the group.

## House load and brownouts

The lights are the first load. A light that `requires_power` draws its `power_w` while it wants to be on (its schedule), and each system serves the lights of the buildings that have one of its AC panels (`WireNetwork.BalanceOf`): first the wind (AC, direct), then solar through the inverter (held to the inverter rating), then the batteries (also through the inverter, as far as they hold energy). Whatever solar the lights do not use charges the batteries; what the batteries cannot take is wasted. The result is a ratio served / load, the share of the 115 V the lights get.

- Ratio 0 (no power at all): the lights go out AT ONCE.
- Ratio below 1 (not enough to serve every light): a brownout. The voltage reads lower (115 V times the ratio), the lights dim and cut in and out, the worse the lower it is (`LightEmitter`).
- WAILA on an AC panel shows the load and the voltage; Grid OS shows load and voltage on the tile, the stats and a 24 h load graph.

An AC panel (breaker box) can be wired to another AC panel with AC wire: the second is fed through the first (a subpanel off the outdoor panel), so it is live whenever the first is, and its building's lights are served by the same system.

## Portable generators

A portable generator (`portable_generator`, `electricity_generator`: manifest `pushable`, `power_radius_tiles` 6, `max_power_w`) is pushed like a wheelbarrow (right click to grab, right click to put down). It powers everything that needs electricity within 6 tiles of it (nothing battery powered needs it), and ALL of a build site it stands in or reaches within that radius (the corded tools building it: a tool with `power_draw_w` counts at a site only while a generator powers it, the hover card says "No power" otherwise, and its draw is the generator's load), but it is NOT connected to finished structures: a building's lights run on the building's own system only (`Growth/PortableGenerator.cs`, `PortableGenerator.RatioAt(position)` for anything outside a building that needs power). Asked for more than its rated power, what it reaches gets that share of its voltage. It runs while it exists: fuel is not modeled yet. WAILA shows its output and range.

## Propane lines

A propane line uses the same machinery as a wire (`WireNode`, `WireLink`, `WireNetwork`, `WireRouter`), with a kind of its own, `propane`.

| | |
|---|---|
| Ends | `wire_role: propane_tank` (`fuel_tank_propane_1900l`, `fuel_tank_propane_3800l`, placed on the ground) and `wire_role: propane_connector` (`fuel_propane_house_connector`, mounted on the OUTSIDE of a building). Tank to connector, tank to tank and connector to connector all join; nothing electrical joins a propane device. |
| Tool | The pipe wrench (`tool_wrench_pipe`) in the active slot, not the cutters: right click one end, then the other. The same again cuts the line; Shift + right click takes every line off a device. |
| Material | Propane pipe (`wire_kind: propane`): `fuel_pipe_propane` (3 m), `fuel_pipe_propane_stack_10` (30 m), `fuel_pipe_propane_stack_20` (60 m), in the toolbar or standing within reach. A run uses the distance plus 0.5 m. |
| Reach | Up to 40 m, like a buried AC run. |
| Route | Both ends on the same side of one building's walls: along the walls, like a wire in conduit. Otherwise underground: down from one end, 0.4 m under the surface, up at the other. Drawn as a charcoal grey pipe, with no conduit round it. |
| Effect | `WireNetwork.HasPropane(site)`: a building has propane while a house connector mounted on it is piped (through any number of connectors and tanks) to a tank. The look-at panel says so on the connector. Nothing consumes propane yet, and a tank's contents are not tracked. |
| Saved | With the wires (`GameSave.SavedWire`, kind `propane`). |

Data: `tools/set_wiring_data.py`. Models: `tools/make_propane_line.py` (the connector), `tools/make_material_stacks.py` (the pipe and its stacks).

### The fill post

`fuel_propane_fill_post` (`wire_role: propane_filler`) is a third end of a propane line: a post set in the ground with a fill valve and a yellow hose, piped to a tank like a house
connector. A right click on it with a portable propane tank in the active slot (a liquid container that accepts `liquid_propane`: `fuel_propane_1_5l`, `fuel_propane_18l`,
`fuel_propane_36l`) fills that tank (`PropaneFill.cs`). The post must be piped to a tank and within 4 m; one tank at a time.

How full a portable tank is: `LiquidRules.Held(item, stored)`, where `stored` is the slot's (or the placed object's) `WireUsed` number: the change from what the item holds by
default (nothing for a propane tank, its `filled_l` for an item sold full). So portable propane tanks start EMPTY. Nothing uses propane up yet.

### Bulk fuel delivery and what a tank holds

Propane, diesel and gasoline are bought in the Tank You phone store as 100 L lots (`fuel_bulk_propane`, `fuel_bulk_diesel`, `fuel_bulk_gasoline`, written by
`tools/make_bulk_fuel.py`: no model, a liquid container sold full). At checkout they become an order of their own (`DeliveryService.Order.fuel`); the next morning the fuel truck
(`vehicle_delivery_fuel_truck`) drives in like the van and `FuelDelivery.FillRoutine` pumps each liquid into the tanks standing in the world, one tank every 1.5 s, the biggest
first: every placed liquid container that accepts the liquid and is empty or already holds it. Liters that fit in no tank are refunded.

The truck's round (`FuelDelivery.FuelTruck`): down the road to the point nearest each tank, off the road and straight for the tank as close as it gets (it stops short of the tank and of a building in the way), 1.5 s of work there, backing out to the road, on to the next tank; after the last it turns round and leaves. With no road or no truck model the work is simply done.

The big fuel tanks (`fuel_tank_*`, `FuelDelivery.IsFixedTank`) cannot be picked up by hand. A Tank Pickup (`fuel_service_tank_pickup`, also in Tank You) sends the truck to take one away per pickup ordered, the emptiest first. The player is paid back at a discount (`FuelDelivery.TankBuyBack`, `FuelBuyBack`, both 0.5): half the tank's price, and the fuel still in it at half what a liter costs in the store. A pickup with no tank to take is refunded.

A placed tank's contents are its `LiquidId` (saved as `SavedPlaced.liquidId`) and its liters, `LiquidRules.Held(item, WireUsed)`. The look-at panel shows them ("Holds"), and a
tank with a sticker names the liquid on it (`TankSticker`). A propane tank supplies its line only while it has propane in it, so a new tank must be filled before a house connector
or a fill post works. Picking a tank up keeps its liters but forgets which liquid a multi-fuel tank held.

## Safety disconnect

`electricity_switch_disconnect_safety` (`wire_role: disconnect`, `Growth/Disconnect.cs`) mounts on a wall and is wired INTO a run: AC beside a breaker box, an inverter, a wind turbine or a standby generator; DC beside the rest (panels, wall entry, DC breaker box, MPPT, battery, bus bar). On (handle up) it carries the current like a bus bar; a right click throws it off (handle down) and the run is cut there: the chain past it is broken (`WireNetwork.Cut`, `Neighbours`, `IsEnergized`, `SolarSun.InputWatts`). Saved with the mounted item.

## Standby generators and the lockout box

`electricity_generator_standby_*` (`wire_role: standby_generator`) stand on the ground and stay there once placed. Pipe one to a propane tank (pipe wrench, propane
pipe) and wire it with AC wire to a **Generator Lockout Box** (`electricity_generator_lockout_box`, `wire_role: generator_lockout`) mounted on the OUTSIDE wall of
the building. A generator connects to nothing else.

The lockout box runs the building on ONE side, never both (`WireNetwork.TickLockouts`): on its breaker box while that system can carry the building (its
breaker box live, the load carried, the batteries over 15 %); otherwise it switches the building over to its generators, which start by themselves: a generator takes a few seconds to fire up (`GenStartSeconds`, 3 s) and the building stays dark or dim until it takes the load. On the
generator the building is no longer that system's load, so its batteries recharge; once the system could carry the building again with its batteries at half,
the box switches back. A generator gives up to its rating and burns propane from its tanks (`fuel_consumption_l_per_min` at full load, 30 % of that idling);
with no propane it does not start. The box's handle shows the side: up the breaker box, down the generator.

## Power alerts

Emergency toasts for each building with a breaker box or lockout box outside (`WireNetwork.TickPowerAlerts`), only when its state changes: **Power lost** (severe: it had power and has none), **Low power** (a brownout, or the batteries feeding it under 15 %; it clears at 95 % supply and 20 % charge), **On the generator** (its lockout box switched over), and **Power restored** (back on its breaker box after a loss or the generator). Loading a game or wiring a building says nothing.

## Fuel pumps

The gasoline and diesel pumps (`fuel_pump_gas`, `fuel_pump_diesel`, `wire_role: fuel_pump`) stand on the ground. Pipe one to bulk fuel tanks (`fuel_tank_bulk_*`, `wire_role: fuel_tank`, filled by the fuel truck) with a **Fuel Line** (`fuel_pipe_line`, `wire_kind: fuel`, pipe wrench; underground outside; tank to tank too), and wire it to a breaker box with AC wire: it pumps while that box is live and not browning out. A right click on the pump takes its nozzle (the fuel nozzle cursor, a hose to the player, 5 m long); a right click on a fuel container on the ground that takes that fuel starts filling it from the tanks at 4 L a game minute until it is full (again stops it); while it pumps, its motor (`power_draw_w`, 750 W) is load on the breaker box's system, and a brownout stops it; a right click on the pump, or walking out of the hose's reach, hangs it up (`Growth/FuelNozzle.cs`; vehicles will use `FuelNozzle.Dispense`).
