# Clutter Tall Grass (`clutter_tall_grass`)

![Clutter Tall Grass Icon](clutter_tall_grass.png)

## Overview
- **Category**: `ground`
- **Item Identifier**: `clutter_tall_grass`
- **Max Stack Size**: 99
- **Weight**: 1.0 kg
- **Base Economic Value**: $10.0
- **Consumable**: False

## Description
Standard ground asset used in the Homesteader simulation.

## 3D Model & Mesh Specifications
- **Physical Dimensions (X × Y × Z)**: `100.0 cm × 100.0 cm × 20.0 cm` (`1.0m × 1.0m × 0.2m`)
- **Mesh Complexity**: 8 vertices, 6 polygon faces
- **Bounding Box**: $X_{min}=-50.0$, $X_{max}=50.0$, $Y_{min}=-50.0$, $Y_{max}=50.0$, $Z_{min}=-20.0$, $Z_{max}=0.0$
- **Shading Aesthetic**: 3D Low-Poly Faceted, Metric Scale (cm), Ground-Aligned Pivot ($Z_{min} = 0$).
- **Texture / Materials**: Flat-shaded UV mapped to `T_Homesteader_Palette` or dedicated 512×512 PBR.

## Utilities & Resource Profile
| Utility System | Usage / Output Metric | Operational Details |
| :--- | :--- | :--- |
| **💧 Water** | `None (unplumbed / dry)` | None (unplumbed / dry) |
| **⚡ Electricity** | `None (passive / unpowered)` | None (passive / unpowered) |
| **🚽 Sewage / Waste** | `None (no waste discharge)` | None (no waste discharge) |
| **🔋 Battery Power** | `None (no internal battery)` | None (no internal battery) |
| **🌐 Internet / Data** | `None (offline / non-networked)` | None (offline / non-networked) |

## Asset Files & Links
- **Plugin Manifest (JSON)**: [clutter_tall_grass.json](clutter_tall_grass.json)
- **Icon (PNG)**: [clutter_tall_grass.png](clutter_tall_grass.png)
- **3D Mesh (MTL)**: [SM_Tile_Tall_grass.mtl](SM_Tile_Tall_grass.mtl)
- **3D Mesh (OBJ)**: [SM_Tile_Tall_grass.obj](SM_Tile_Tall_grass.obj)
