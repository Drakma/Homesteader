# Item Corn Ear (`ingredient_corn`)

![Item Corn Ear Icon](ingredient_corn.png)

## Overview
- **Category**: `farming`
- **Item Identifier**: `ingredient_corn`
- **Max Stack Size**: 99
- **Weight**: 1.0 kg
- **Base Economic Value**: $10.0
- **Consumable**: False

## Description
Standard farming asset used in the Homesteader simulation.

## Growth & Lifecycle (4 Stages)
- **Growth Type**: `crop` (`corn`)
- **Max Age Input**: 24 days
- **Current Stage**: Stage 4 - `large (mature)` (Age 18 - 24 days)

| Stage | Stage Name | Age Range | Stage Item ID |
| :---: | :--- | :---: | :--- |
| 1 | `seed` | 0 – 6 days | `seed_corn` |
| 2 | `sprout` | 6 – 12 days | `crop_corn_sprout` |
| 3 | `growing` | 12 – 18 days | `crop_corn_stalk` |
| 4 | `large (mature)` **(Current)** | 18 – 24 days | `crop_corn` |

## 3D Model & Mesh Specifications
- **Physical Dimensions (X × Y × Z)**: `10.0 cm × 25.0 cm × 6.5 cm` (`0.1m × 0.25m × 0.07m`)
- **Mesh Complexity**: 86 vertices, 144 polygon faces
- **Bounding Box**: $X_{min}=-5.0$, $X_{max}=5.0$, $Y_{min}=-12.0$, $Y_{max}=13.0$, $Z_{min}=0.0$, $Z_{max}=6.54$
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
- **Plugin Manifest (JSON)**: [ingredient_corn.json](ingredient_corn.json)
- **Icon (PNG)**: [ingredient_corn.png](ingredient_corn.png)
- **3D Mesh (MTL)**: [SM_Item_Corn_Ear.mtl](SM_Item_Corn_Ear.mtl)
- **3D Mesh (OBJ)**: [SM_Item_Corn_Ear.obj](SM_Item_Corn_Ear.obj)
