# Animal Cow Holstein (`animal_adult_holstein_cow`)

![Animal Cow Holstein Icon](animal_adult_holstein_cow.png)

## Overview
- **Category**: `ranching`
- **Item Identifier**: `animal_adult_holstein_cow`
- **Max Stack Size**: 99
- **Weight**: 1.0 kg
- **Base Economic Value**: $10.0
- **Consumable**: False

## Description
Standard ranching asset used in the Homesteader simulation.

## Growth & Lifecycle (4 Stages)
- **Growth Type**: `animal` (`cattle`)
- **Max Age Input**: 730 days
- **Current Stage**: Stage 4 - `large (mature)` (Age 511 - 730 days)

| Stage | Stage Name | Age Range | Stage Item ID |
| :---: | :--- | :---: | :--- |
| 1 | `baby` | 0 – 110 days | `baby_calf` |
| 2 | `juvenile` | 110 – 292 days | `animal_cow_calf` |
| 3 | `adult` | 292 – 511 days | `animal_cow_adult` |
| 4 | `large (mature)` **(Current)** | 511 – 730 days | `animal_adult_holstein_cow` |

## 3D Model & Mesh Specifications
- **Physical Dimensions (X × Y × Z)**: `69.0 cm × 157.0 cm × 148.0 cm` (`0.69m × 1.57m × 1.48m`)
- **Mesh Complexity**: 272 vertices, 202 polygon faces
- **Bounding Box**: $X_{min}=-34.5$, $X_{max}=34.5$, $Y_{min}=-100.000015$, $Y_{max}=57.0$, $Z_{min}=-1e-06$, $Z_{max}=148.0$
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
- **Plugin Manifest (JSON)**: [animal_adult_holstein_cow.json](animal_adult_holstein_cow.json)
- **Icon (PNG)**: [animal_adult_holstein_cow.png](animal_adult_holstein_cow.png)
- **3D Mesh (FBX)**: [SKM_Animal_Cow_Holstein.fbx](SKM_Animal_Cow_Holstein.fbx)
- **3D Mesh (MTL)**: [SKM_Animal_Cow_Holstein.mtl](SKM_Animal_Cow_Holstein.mtl)
- **3D Mesh (OBJ)**: [SKM_Animal_Cow_Holstein.obj](SKM_Animal_Cow_Holstein.obj)
- **3D Mesh (MTL)**: [SM_Animal_Cow_Holstein.mtl](SM_Animal_Cow_Holstein.mtl)
- **3D Mesh (OBJ)**: [SM_Animal_Cow_Holstein.obj](SM_Animal_Cow_Holstein.obj)
