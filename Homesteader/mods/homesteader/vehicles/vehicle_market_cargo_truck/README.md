# Market Cargo Truck (`vehicle_market_cargo_truck`)

An open-bed stake truck. It comes the morning after you sell goods in the Market app, loads what you left in the pickup zone and pays you for it.

Procedural model (tools/make_cargo_truck.py), 896 triangles. Built like the fuel truck: the four wheels are separate objects named `Wheel_FL`, `Wheel_FR`, `Wheel_RL`, `Wheel_RR` with their origin on the hub, and an empty named `FrontMarker` sits at the nose, so the game drives it the same way. See docs/MARKET.md.
