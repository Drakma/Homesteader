# Overload

Every piece of electric equipment has a RATED CURRENT (manifest `category_fields.max_current_a`, in amps). The grid works out the current through each part every grid tick; a part carrying
more than its rating HEATS, and a part that heats all the way TRIPS: it opens like a thrown disconnect and what is past it gets nothing until it is reset by hand.
Code: `Growth/WireOverload.cs` (a partial of `WireNetwork`), hooks in `Growth/Wiring.cs`. Data: `tools/set_electric_ratings.py`. A part under its rating cools.

## Units

- AC amps = watts / 240 V (`WireNetwork.AcV`, a split-phase service). DC amps = watts / 48 V (`WireNetwork.DcV`, the battery bus).
- A load (light, appliance, pump) has no rating of its own: its watts (`power_draw_w`) are what flows. The parts in the supply chain carry the sum.

## How fast it trips

Game seconds to a trip at r times the rating (r above 1): `360 / (r - 1)`, kept between 5 seconds and an hour. 10 % over takes an hour, double takes 6 minutes, ten times takes 40 seconds.
A part at or under its rating cools at 1 / 600 a second. Heat shows in WAILA as a share of a trip. A reset part comes back at half heat (0.5), so a circuit that is still over trips it again soon.

## What is measured, and what it is rated at

| Part | Current through it | Rating | Tolerance |
|---|---|---|---|
| AC breaker box (and sub panel) | its building's watts plus every sub panel it feeds, / 240 | 50, 100, 200 A; sub panel 150 A; well panel 20 A | none |
| Inverter | the AC demand it must give (load less direct wind), shared by rating, / 240 | rated watts / 240 (3 kW 12.5 A) | none |
| DC breaker box | the array's current into the controllers (solar watts / 48) | 32, 64, 128 A | none |
| Bus bar | the largest of the array, battery and inverter DC currents | 100, 250, 500 A | none |
| Wall entry, safety disconnect, lockout box | AC: the AC demand / 240; DC: the array current | 64 A; 50 A; 50 A | none |
| Charge controller (MPPT) | the array's current, shared by rating | 32, 64, 128 A | 25 % (it clips first) |
| Battery | the DISCHARGE (charge is limited by the controller) / 48, shared by capacity | continuous watts / 48 | none |
| Standby generator | its share of the building's load / 240 | rated watts / 240 | 10 % |
| Portable generator | demand / 240 | 31.3 A | 10 %; resets itself when it has cooled |
| Wire | the larger of the currents at its two ends | the coil's `max_current_a` (DC 55 A) | none; heats the parts at BOTH ends |
| Solar panels, wind turbines | the current of their rated output | info only: a source cannot be overloaded | n/a |

## What a trip does

- The part is `Open` (`WireNode.Open`): `Neighbours`, `Cut`, `IsEnergized` and the solar traversal all treat it like a disconnect thrown off. A tripped breaker box leaves its building dark.
- A tripped inverter leaves the AC side with no source; a tripped DC breaker, bus bar, wall entry or controller cuts the array from the batteries; a tripped battery drops out of the bank; a tripped standby generator is out of its lockout box.
- A toast says which part tripped and the current. The existing power alerts (Power lost, Low power) follow from the building losing power.

## Resetting

Right click a tripped part (not with wire cutters in hand). Reset it only after the load is down. A portable generator has no handle: it resets itself when it has cooled.

## Saving

`GameSave.trips` (`SavedTrip`: the part's placed or attached index, `tripped`, `off`, `heat`) keeps which parts are tripped and how hot, and which safety disconnects are thrown off.

## Changing a rating

Edit `RATINGS` in `tools/set_electric_ratings.py` (or the item's Category Fields in the asset kit), run it, then `tools/generate_unity_asset_catalog.py` and `tools/package_catalog_as_mods.py`.
A new kind of part goes into `WireNetwork.ApplyOverload` with the current it carries.
