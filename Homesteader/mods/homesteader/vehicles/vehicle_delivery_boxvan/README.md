# Delivery Box Van (`vehicle_delivery_boxvan`)

![Icon](vehicle_delivery_boxvan.png)

## Overview
- **Category**: `vehicles`
- **Item Identifier**: `vehicle_delivery_boxvan`
- **Placeable**: no (it drives itself: see `Assets/Scripts/World/DeliveryService.cs`)

## Description
A plain white cargo van with an orange stripe. It brings your orders down the road to the homestead the day after you place them.

The model's four wheels are separate objects named `Wheel_FL`, `Wheel_FR`, `Wheel_RL`, `Wheel_RR` with their origin on the hub, so the game
spins them while it drives; an empty named `FrontMarker` sits at the nose so the game knows which way the model faces.

## Asset Files & Links
- **Plugin Manifest (JSON)**: [vehicle_delivery_boxvan.json](vehicle_delivery_boxvan.json)
- **Model (GLB, 484 triangles)**: [vehicle_delivery_boxvan.glb](vehicle_delivery_boxvan.glb)
- **Icon (PNG)**: [vehicle_delivery_boxvan.png](vehicle_delivery_boxvan.png)
