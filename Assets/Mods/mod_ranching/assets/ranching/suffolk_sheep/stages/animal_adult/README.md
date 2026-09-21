# Animal Sheep Suffolk (`animal_adult_suffolk_sheep`)

![Animal Sheep Suffolk Icon](animal_adult_suffolk_sheep.png)

## Overview
- **Category**: `ranching`
- **Item Identifier**: `animal_adult_suffolk_sheep`
- **Max Stack Size**: 99
- **Weight**: 1.0 kg
- **Base Economic Value**: $10.0
- **Consumable**: False

## Description
Standard ranching asset used in the Homesteader simulation.

## Growth & Lifecycle (4 Stages)
- **Growth Type**: `animal` (`sheep`)
- **Max Age Input**: 500 days
- **Current Stage**: Stage 4 - `large (mature)` (Age 350 - 500 days)

| Stage | Stage Name | Age Range | Stage Item ID |
| :---: | :--- | :---: | :--- |
| 1 | `baby` | 0 – 75 days | `baby_lamb` |
| 2 | `juvenile` | 75 – 200 days | `animal_sheep_lamb` |
| 3 | `adult` | 200 – 350 days | `animal_sheep_adult` |
| 4 | `large (mature)` **(Current)** | 350 – 500 days | `animal_adult_suffolk_sheep` |

## 3D Model & Mesh Specifications
- **Physical Dimensions (X × Y × Z)**: `58.0 cm × 132.0 cm × 104.0 cm` (`0.58m × 1.32m × 1.04m`)
- **Mesh Complexity**: 160 vertices, 120 polygon faces
- **Bounding Box**: $X_{min}=-29.0$, $X_{max}=29.0$, $Y_{min}=-84.0$, $Y_{max}=47.999996$, $Z_{min}=-1e-06$, $Z_{max}=104.0$
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
- **Plugin Manifest (JSON)**: [animal_adult_suffolk_sheep.json](animal_adult_suffolk_sheep.json)
- **Icon (PNG)**: [animal_adult_suffolk_sheep.png](animal_adult_suffolk_sheep.png)
- **3D Mesh (FBX)**: [SKM_Animal_Sheep_Suffolk.fbx](SKM_Animal_Sheep_Suffolk.fbx)
- **3D Mesh (MTL)**: [SKM_Animal_Sheep_Suffolk.mtl](SKM_Animal_Sheep_Suffolk.mtl)
- **3D Mesh (OBJ)**: [SKM_Animal_Sheep_Suffolk.obj](SKM_Animal_Sheep_Suffolk.obj)
- **3D Mesh (MTL)**: [SM_Animal_Sheep_Suffolk.mtl](SM_Animal_Sheep_Suffolk.mtl)
- **3D Mesh (OBJ)**: [SM_Animal_Sheep_Suffolk.obj](SM_Animal_Sheep_Suffolk.obj)
