# RETIRED: Unreal Engine 5 3D Model & Texture Integration Guide

> **THIS GUIDE IS RETIRED. DO NOT FOLLOW IT.**
>
> The project has officially switched from Unreal Engine 5 to **Unity 6 (`6000.6.0f1`)**.
> This document's import settings, material setup, and content paths all reference
> Unreal Engine 5 and are no longer accurate.
>
> **See `docs/UNITY_INTEGRATION_GUIDE.md` instead.** It covers:
> - 3D model import (GLB standard, FBX for rigged/animated only)
> - Unity 6 Model Inspector settings (Scale Factor, Convert Units, Bake Axis Conversion)
> - URP material setup
> - ScriptableObject item definitions (replacing UE5 DataTable + C++ structs)
> - The full Meshy text-to-3D pipeline
>
> Key differences from the retired UE5 guide:
>
> | Old (UE5) | New (Unity 6) |
> | :--- | :--- |
> | `.obj` static meshes | `.glb` (textures embedded, loaded at runtime by glTFast) |
> | `Content/Homesteader/Assets/Meshes/` | `Assets/Homesteader/Assets/Meshes/` |
> | `M_Homesteader_Palette` master material | URP Lit Shader / Shader Graph |
> | `T_Homesteader_Palette` color atlas | Per-model textures from Meshy (no shared palette atlas) |
> | 1 unit = 1 cm | 1 unit = 1 meter |
> | C++ `FItemData` struct + `DT_Items.csv` | C# `ItemDefinition` ScriptableObject |
>
> The metric scaling reference table below is preserved for historical reference
> only — the dimensions are still valid but are now in **meters** (Unity scale),
> not centimeters (Unreal scale).

---

## Historical Reference: Real-World Metric Scaling

All dimensions below are in centimeters (original UE5 authoring scale). In Unity 6,
divide by 100 to get meters (e.g., `66.5 cm` = `0.665 m`).

| Mesh Asset                  | Bounding Box Dimensions (cm)                | Usage                          |
| :-------------------------- | :------------------------------------------ | :----------------------------- |
| `SM_Tool_Axe`               | $4.2 \times 21.5 \times 66.5\text{ cm}$     | Handheld wood-chopping axe     |
| `SM_Tool_Pickaxe`           | $4.5 \times 46.0 \times 82.0\text{ cm}$     | Handheld mining pickaxe        |
| `SM_Tool_Hoe`               | $14.0 \times 9.3 \times 120.0\text{ cm}$    | Handheld farming hoe           |
| `SM_Tool_Shovel`            | $18.0 \times 3.5 \times 98.5\text{ cm}$     | Handheld digging spade         |
| `SM_Tool_Chainsaw`          | $19.5 \times 80.5 \times 20.5\text{ cm}$    | Motorized logging tool         |
| `SM_Tool_FishingRod`        | $6.4 \times 10.5 \times 189.0\text{ cm}$    | Handheld fishing tackle        |
| `SM_Crop_Corn`              | $6.9 \times 7.0 \times 23.5\text{ cm}$      | Ground pickup / harvest item   |
| `SM_Crop_Pumpkin`           | $36.0 \times 34.2 \times 27.0\text{ cm}$    | Large farm crop pickup         |
| `SM_Crop_Tomato`            | $9.0 \times 9.0 \times 8.9\text{ cm}$       | Handheld fruit pickup          |
| `SM_Resource_WoodLogs`      | $50.0 \times 90.0 \times 44.5\text{ cm}$    | Ground timber resource         |
| `SM_Resource_LumberPlank`   | $20.0 \times 120.0 \times 13.0\text{ cm}$   | Construction lumber bundle     |
| `SM_Resource_StoneBlock`    | $40.0 \times 40.0 \times 27.0\text{ cm}$    | Quarried masonry block         |
| `SM_Electric_SolarPanel`    | $130.0 \times 85.0 \times 68.0\text{ cm}$   | Placeable electrical generator |
| `SM_Electric_WindTurbine`   | $165.8 \times 41.0 \times 382.5\text{ cm}$  | Placeable tall wind turbine    |
| `SM_Electric_Generator`     | $56.0 \times 44.0 \times 54.0\text{ cm}$    | Placeable combustion inverter  |
| `SM_Water_WellPump`         | $30.0 \times 49.0 \times 42.0\text{ cm}$    | Placeable utility pump         |
| `SM_Water_FilterCanister`   | $34.0 \times 18.0 \times 48.2\text{ cm}$    | Wall-mounted water purifier    |
| `SM_Water_PipeValve`        | $36.0 \times 11.0 \times 18.5\text{ cm}$    | Plumbing connector             |
| `SM_Sewage_SepticTank`      | $110.0 \times 200.0 \times 116.3\text{ cm}$ | In-ground septic tank          |
| `SM_Sewage_CompostBin`      | $85.0 \times 85.0 \times 75.0\text{ cm}$    | Backyard compost converter     |
| `SM_Internet_SatelliteDish` | $69.5 \times 54.5 \times 79.0\text{ cm}$    | Ground tripod receiver         |
| `SM_Internet_Router`        | $26.0 \times 19.2 \times 26.0\text{ cm}$    | Indoor network distributor     |
