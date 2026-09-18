# Animal Chicken Chick (`animal_baby_white_chicken`)

![Animal Chicken Chick Icon](animal_baby_white_chicken.png)

## Overview
- **Category**: `ranching`
- **Item Identifier**: `animal_baby_white_chicken`
- **Max Stack Size**: 99
- **Weight**: 1.0 kg
- **Base Economic Value**: $10.0
- **Consumable**: False

## Description
Standard ranching asset used in the Homesteader simulation.

## Growth & Lifecycle (4 Stages)
- **Growth Type**: `animal` (`chicken`)
- **Max Age Input**: 180 days
- **Current Stage**: Stage 2 - `juvenile` (Age 27 - 72 days)

| Stage | Stage Name | Age Range | Stage Item ID |
| :---: | :--- | :---: | :--- |
| 1 | `baby` | 0 – 27 days | `baby_chick` |
| 2 | `juvenile` **(Current)** | 27 – 72 days | `animal_baby_white_chicken` |
| 3 | `adult` | 72 – 126 days | `animal_chicken_hen` |
| 4 | `large (mature)` | 126 – 180 days | `animal_chicken_red` |

## 3D Model & Mesh Specifications
- **Physical Dimensions (X × Y × Z)**: `15.0 cm × 29.0 cm × 23.0 cm` (`0.15m × 0.29m × 0.23m`)
- **Mesh Complexity**: 80 vertices, 60 polygon faces
- **Bounding Box**: $X_{min}=-7.5$, $X_{max}=7.5$, $Y_{min}=-18.000002$, $Y_{max}=10.999999$, $Z_{min}=0.0$, $Z_{max}=23.0$
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
- **Plugin Manifest (JSON)**: [animal_baby_white_chicken.json](animal_baby_white_chicken.json)
- **Icon (PNG)**: [animal_baby_white_chicken.png](animal_baby_white_chicken.png)
- **3D Mesh (FBX)**: [SKM_Animal_Chicken_Chick.fbx](SKM_Animal_Chicken_Chick.fbx)
- **3D Mesh (MTL)**: [SKM_Animal_Chicken_Chick.mtl](SKM_Animal_Chicken_Chick.mtl)
- **3D Mesh (OBJ)**: [SKM_Animal_Chicken_Chick.obj](SKM_Animal_Chicken_Chick.obj)
- **3D Mesh (MTL)**: [SM_Animal_Chicken_Chick.mtl](SM_Animal_Chicken_Chick.mtl)
- **3D Mesh (OBJ)**: [SM_Animal_Chicken_Chick.obj](SM_Animal_Chicken_Chick.obj)
