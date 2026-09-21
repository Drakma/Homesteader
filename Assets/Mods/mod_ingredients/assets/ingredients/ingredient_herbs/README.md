# Item Cabbage Harvested (`ingredient_herbs`)

![Item Cabbage Harvested Icon](ingredient_herbs.png)

## Overview
- **Category**: `farming`
- **Item Identifier**: `ingredient_herbs`
- **Max Stack Size**: 99
- **Weight**: 1.0 kg
- **Base Economic Value**: $10.0
- **Consumable**: False

## Description
Standard farming asset used in the Homesteader simulation.

## Growth & Lifecycle (4 Stages)
- **Growth Type**: `crop` (`cabbage`)
- **Max Age Input**: 18 days
- **Current Stage**: Stage 4 - `large (mature)` (Age 14 - 18 days)

| Stage | Stage Name | Age Range | Stage Item ID |
| :---: | :--- | :---: | :--- |
| 1 | `seed` | 0 – 4 days | `seed_cabbage` |
| 2 | `sprout` | 4 – 9 days | `crop_cabbage_sprout` |
| 3 | `growing` | 9 – 14 days | `crop_cabbage_head` |
| 4 | `large (mature)` **(Current)** | 14 – 18 days | `crop_cabbage` |

## 3D Model & Mesh Specifications
- **Physical Dimensions (X × Y × Z)**: `28.4 cm × 24.6 cm × 15.0 cm` (`0.28m × 0.25m × 0.15m`)
- **Mesh Complexity**: 792 vertices, 306 polygon faces
- **Bounding Box**: $X_{min}=-14.2$, $X_{max}=14.2$, $Y_{min}=-12.3$, $Y_{max}=12.3$, $Z_{min}=0.0$, $Z_{max}=15.0$
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
- **Plugin Manifest (JSON)**: [ingredient_herbs.json](ingredient_herbs.json)
- **Icon (PNG)**: [ingredient_herbs.png](ingredient_herbs.png)
- **3D Mesh (MTL)**: [SM_Item_Cabbage_Harvested.mtl](SM_Item_Cabbage_Harvested.mtl)
- **3D Mesh (OBJ)**: [SM_Item_Cabbage_Harvested.obj](SM_Item_Cabbage_Harvested.obj)
