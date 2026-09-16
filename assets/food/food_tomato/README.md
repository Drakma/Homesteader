# Item Tomato Fruit (`food_tomato`)

![Item Tomato Fruit Icon](food_tomato.png)

## Overview
- **Category**: `farming`
- **Item Identifier**: `food_tomato`
- **Max Stack Size**: 99
- **Weight**: 1.0 kg
- **Base Economic Value**: $10.0
- **Consumable**: False

## Description
Standard farming asset used in the Homesteader simulation.

## Growth & Lifecycle (4 Stages)
- **Growth Type**: `crop` (`tomato`)
- **Max Age Input**: 22 days
- **Current Stage**: Stage 4 - `large (mature)` (Age 16 - 22 days)

| Stage | Stage Name | Age Range | Stage Item ID |
| :---: | :--- | :---: | :--- |
| 1 | `seed` | 0 – 6 days | `seed_tomato` |
| 2 | `sprout` | 6 – 11 days | `crop_tomato_sprout` |
| 3 | `growing` | 11 – 16 days | `crop_tomato_vine` |
| 4 | `large (mature)` **(Current)** | 16 – 22 days | `crop_tomato` |

## 3D Model & Mesh Specifications
- **Physical Dimensions (X × Y × Z)**: `11.2 cm × 9.7 cm × 11.1 cm` (`0.11m × 0.1m × 0.11m`)
- **Mesh Complexity**: 907 vertices, 377 polygon faces
- **Bounding Box**: $X_{min}=-5.61$, $X_{max}=5.61$, $Y_{min}=-4.86$, $Y_{max}=4.86$, $Z_{min}=0.0$, $Z_{max}=11.1$
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
- **Plugin Manifest (JSON)**: [food_tomato.json](food_tomato.json)
- **Icon (PNG)**: [food_tomato.png](food_tomato.png)
- **3D Mesh (MTL)**: [SM_Item_Tomato_Fruit.mtl](SM_Item_Tomato_Fruit.mtl)
- **3D Mesh (OBJ)**: [SM_Item_Tomato_Fruit.obj](SM_Item_Tomato_Fruit.obj)
