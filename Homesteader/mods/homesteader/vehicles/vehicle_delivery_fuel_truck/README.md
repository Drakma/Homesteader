# Fuel Delivery Truck (`vehicle_delivery_fuel_truck`)

A white tank truck with an orange band: the delivery van with a fuel tank in place of the box, a hose reel on the side and a ladder up the back.

Procedural model (tools/make_fuel_truck.py), 1292 triangles. Built like the delivery box van: the four wheels are separate objects named `Wheel_FL`, `Wheel_FR`, `Wheel_RL`, `Wheel_RR` with their origin on the hub, and an empty named `FrontMarker` sits at the nose, so the game can drive it the same way. The FUEL sticker on the tank is a picture (tools/case_labels.py).
