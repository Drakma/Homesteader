# Septic Pump Truck (`vehicle_septic_pump_truck`)

The honey pot truck: a vacuum tank on a truck chassis, with its pump, racks of black suction hose and a dump valve at the back. It comes to pump out septic tanks (a Septic Pump-Out in the Tank You app).

Procedural model (tools/make_septic_truck.py), 1218 triangles. Built on the fuel truck: the four wheels are separate objects named `Wheel_FL`, `Wheel_FR`, `Wheel_RL`, `Wheel_RR` with their origin on the hub, and an empty named `FrontMarker` sits at the nose, so the game drives it the same way. See docs/SEPTIC.md.
