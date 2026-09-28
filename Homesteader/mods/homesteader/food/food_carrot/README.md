# Item Carrot Bunch (`food_carrot`)

![Item Carrot Bunch Icon](food_carrot.png)

## Overview
- **Category**: `farming`
- **Item Identifier**: `food_carrot`
- **Max Stack Size**: 99
- **Weight**: 1.0 kg
- **Base Economic Value**: $10.0
- **Consumable**: False

## Description
Standard farming asset used in the Homesteader simulation.

## Growth & Lifecycle (4 Stages)
- **Growth Type**: `crop` (`carrot`)
- **Max Age Input**: 16 days
- **Current Stage**: Stage 4 - `large (mature)` (Age 12 - 16 days)

| Stage | Stage Name | Age Range | Stage Item ID |
| :---: | :--- | :---: | :--- |
| 1 | `seed` | 0 – 4 days | `seed_carrot` |
| 2 | `sprout` | 4 – 8 days | `crop_carrot_sprout` |
| 3 | `growing` | 8 – 12 days | `crop_carrot_patch` |
| 4 | `large (mature)` **(Current)** | 12 – 16 days | `crop_carrot` |

## 3D Model & Mesh Specifications
- **Physical Dimensions (X × Y × Z)**: `9.2 cm × 9.0 cm × 27.0 cm` (`0.09m × 0.09m × 0.27m`)
- **Mesh Complexity**: 135 vertices, 173 polygon faces
- **Bounding Box**: $X_{min}=-4.5$, $X_{max}=4.7$, $Y_{min}=-4.5$, $Y_{max}=4.5$, $Z_{min}=0.0$, $Z_{max}=27.0$
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
- **Plugin Manifest (JSON)**: [food_carrot.json](food_carrot.json)
- **Icon (PNG)**: [food_carrot.png](food_carrot.png)
- **3D Mesh (MTL)**: [SM_Item_Carrot_Bunch.mtl](SM_Item_Carrot_Bunch.mtl)
- **3D Mesh (OBJ)**: [SM_Item_Carrot_Bunch.obj](SM_Item_Carrot_Bunch.obj)
