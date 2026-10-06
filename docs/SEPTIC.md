# Sewage: waste outlets, septic tanks and leach fields

A building drains like it gets its water and power: through a part on its wall, piped to a system in the yard. Code: `Assets/Scripts/Growth/Septic.cs`
(the flow), `Fixtures.cs` (using a fixture), `World/SepticPumpOut.cs` (the honey pot truck); the pipe is a `sewer` link in `WireNetwork` (`Wiring.cs`).
Models and manifests: `tools/make_septic.py`, `tools/make_septic_truck.py`.

## The line

    building waste outlet  >  macerator pump (optional)  >  septic tank  >  (more tanks in series)  >  distribution box  >  leach fields

- **Black waste pipe** (`pipe_abs_waste_three_inch`, `wire_kind: sewer`, 3 m a length) joins them, laid with the **pipe wrench** like a water line (right click one
  part, then the next; the same again cuts it). Outside it runs underground, inside a building along the walls.
- **Building Waste Outlet** (`waste_outlet_house`, `wire_role: sewer_outlet`): mounted on the OUTSIDE of a building, through the wall (`attach_through`), like the
  water inlet. Everything inside the building drains through it. An outlet may be piped to another building's outlet: both then drain to the same tank.
- **Macerator Pump** (`waste_pump_macerator`, `sewer_pump`, 500 W): stands inside the building between the outlet and the tank. It grinds the solids, so the tank
  gets HALF the sludge and needs pumping out half as often. It runs on the building's power; without power nothing drains through it. Once placed it is plumbed in: it is not picked up or moved by tidying (`WaterTap.IsFixed`). Standing in a building with no pipe of its own it is in that building's drain automatically: everything the building drains goes through it (`Septic.TankFor`).
- **Septic tanks** (structures, `septic_tank`, `sewage_capacity_l`): `waste_septic_tank_concrete` (3800 L) and `waste_septic_tank_poly` (1900 L). Built in three
  stages (excavate, set the tank with its two risers and lids, backfill); finished, only the two green lids show just above the ground.
- **Distribution Box** (`waste_box_distribution_septic`, `septic_dbox`): its lid sits at the ground; it shares the tank's outflow between the leach fields piped to it.
- **Leach fields** (structures, `leach_field`, `leach_lpd`, `leach_storage_l`): `waste_leach_field_small` (two trenches: 500 L a day, holds 1200 L) and
  `waste_leach_field_large` (four trenches: 1200 L a day, holds 3000 L). Three stages: trench, gravel and perforated pipe, backfill.
- Nothing can be built over a septic tank or a leach field (the structure placement check says so).

## What goes in

The **fixtures** use water (`category_fields.water_per_use_l`, appliances schema): sinks 4 L, flush toilet (`appliance_toilet_flush`) 6 L, shower 60 L, washers
50 to 120 L a load, dishwashers 12 to 20 L. A right click on one standing in a finished building uses it: the liters come from the building's water (the tanks its
inlet reaches, as the taps do) and go down the drain. A washer or dishwasher also needs the building's power. It refuses, saying why, when the building has no
water, no drain (no outlet, not piped to a tank, an unpowered macerator), or the system is backed up. Shift + right click picks a fixture up.

## What happens in the tank

- Of what drains in, 3 % settles as **sludge** (1.5 % through a powered macerator); the rest is liquid.
- The tank fills with liquid, then stays full: what comes in pushes the same amount out, into the tanks after it in series, then through the distribution box into
  the leach fields (each takes its share by the room it has).
- The leach fields **soak away** `leach_lpd` liters a game day (`Septic.Tick`, every grid tick).
- **Backed up:** when the tank, the tanks after it and the fields have no room for what a fixture would send, the fixture does not run. A tank with no leach field
  works as a holding tank: it backs up as soon as it is full.
- Sludge at a third of the tank: the look-at panel says it needs pumping soon. At half the tank it takes nothing more until it is pumped out.

## The honey pot truck

Order a **Septic Pump-Out** (`waste_service_septic_pumpout`, $325, Tank You app) for each tank. The pump truck (`vehicle_septic_pump_truck`) comes the next
morning, drives off the road as close to each tank as it gets (the fuel truck's round, `FuelDelivery.FuelTruck`), pumps out the tanks with the most sludge first
(liquid and sludge to zero) and leaves. A pump-out with no tank to do is refunded.

## Saved

`SavedSite.sewageL` / `sludgeL` (a tank's liquid and sludge, a field's liquid); the sewer links with the other wires; pending pump-outs as delivery orders with
`septic` set.
