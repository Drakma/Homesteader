# Item Potato Loose (`food_potato`)

![Item Potato Loose Icon](food_potato.png)

## Overview
- **Category**: `farming`
- **Item Identifier**: `food_potato`
- **Max Stack Size**: 99
- **Weight**: 1.0 kg
- **Base Economic Value**: $10.0
- **Consumable**: False

## Description
Standard farming asset used in the Homesteader simulation.

## Growth & Lifecycle (4 Stages)
- **Growth Type**: `crop` (`potato`)
- **Max Age Input**: 20 days
- **Current Stage**: Stage 4 - `large (mature)` (Age 15 - 20 days)

| Stage | Stage Name | Age Range | Stage Item ID |
| :---: | :--- | :---: | :--- |
| 1 | `seed` | 0 – 5 days | `seed_potato` |
| 2 | `sprout` | 5 – 10 days | `crop_potato_sprout` |
| 3 | `growing` | 10 – 15 days | `crop_potato_plant` |
| 4 | `large (mature)` **(Current)** | 15 – 20 days | `crop_potato` |

## 3D Model & Mesh Specifications
- **Physical Dimensions (X × Y × Z)**: `13.9 cm × 13.6 cm × 9.1 cm` (`0.14m × 0.14m × 0.09m`)
- **Mesh Complexity**: 592 vertices, 276 polygon faces
- **Bounding Box**: $X_{min}=-6.6$, $X_{max}=7.33$, $Y_{min}=-6.89$, $Y_{max}=6.71$, $Z_{min}=0.0$, $Z_{max}=9.1$
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
- **Plugin Manifest (JSON)**: [food_potato.json](food_potato.json)
- **Icon (PNG)**: [food_potato.png](food_potato.png)
- **3D Mesh (MTL)**: [SM_Item_Potato_Loose.mtl](SM_Item_Potato_Loose.mtl)
- **3D Mesh (OBJ)**: [SM_Item_Potato_Loose.obj](SM_Item_Potato_Loose.obj)
