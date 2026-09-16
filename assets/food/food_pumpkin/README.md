# Item Pumpkin Carved (`food_pumpkin`)

![Item Pumpkin Carved Icon](food_pumpkin.png)

## Overview
- **Category**: `farming`
- **Item Identifier**: `food_pumpkin`
- **Max Stack Size**: 99
- **Weight**: 1.0 kg
- **Base Economic Value**: $10.0
- **Consumable**: False

## Description
Standard farming asset used in the Homesteader simulation.

## Growth & Lifecycle (4 Stages)
- **Growth Type**: `crop` (`pumpkin`)
- **Max Age Input**: 30 days
- **Current Stage**: Stage 4 - `large (mature)` (Age 22 - 30 days)

| Stage | Stage Name | Age Range | Stage Item ID |
| :---: | :--- | :---: | :--- |
| 1 | `seed` | 0 – 8 days | `seed_pumpkin` |
| 2 | `sprout` | 8 – 15 days | `crop_pumpkin_sprout` |
| 3 | `growing` | 15 – 22 days | `crop_pumpkin_patch` |
| 4 | `large (mature)` **(Current)** | 22 – 30 days | `crop_pumpkin` |

## 3D Model & Mesh Specifications
- **Physical Dimensions (X × Y × Z)**: `32.3 cm × 30.4 cm × 24.0 cm` (`0.32m × 0.3m × 0.24m`)
- **Mesh Complexity**: 1004 vertices, 460 polygon faces
- **Bounding Box**: $X_{min}=-16.13$, $X_{max}=16.13$, $Y_{min}=-15.18$, $Y_{max}=15.18$, $Z_{min}=0.0$, $Z_{max}=24.0$
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
- **Plugin Manifest (JSON)**: [food_pumpkin.json](food_pumpkin.json)
- **Icon (PNG)**: [food_pumpkin.png](food_pumpkin.png)
- **3D Mesh (MTL)**: [SM_Item_Pumpkin_Carved.mtl](SM_Item_Pumpkin_Carved.mtl)
- **3D Mesh (OBJ)**: [SM_Item_Pumpkin_Carved.obj](SM_Item_Pumpkin_Carved.obj)
