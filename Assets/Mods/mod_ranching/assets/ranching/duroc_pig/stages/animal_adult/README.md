# Animal Pig Duroc (`animal_adult_duroc_pig`)

![Animal Pig Duroc Icon](animal_adult_duroc_pig.png)

## Overview
- **Category**: `ranching`
- **Item Identifier**: `animal_adult_duroc_pig`
- **Max Stack Size**: 99
- **Weight**: 1.0 kg
- **Base Economic Value**: $10.0
- **Consumable**: False

## Description
Standard ranching asset used in the Homesteader simulation.

## Growth & Lifecycle (4 Stages)
- **Growth Type**: `animal` (`pig`)
- **Max Age Input**: 365 days
- **Current Stage**: Stage 4 - `large (mature)` (Age 255 - 365 days)

| Stage | Stage Name | Age Range | Stage Item ID |
| :---: | :--- | :---: | :--- |
| 1 | `baby` | 0 – 55 days | `baby_piglet` |
| 2 | `juvenile` | 55 – 146 days | `animal_pig_piglet` |
| 3 | `adult` | 146 – 255 days | `animal_pig_adult` |
| 4 | `large (mature)` **(Current)** | 255 – 365 days | `animal_adult_duroc_pig` |

## 3D Model & Mesh Specifications
- **Physical Dimensions (X × Y × Z)**: `54.0 cm × 114.2 cm × 70.0 cm` (`0.54m × 1.14m × 0.7m`)
- **Mesh Complexity**: 208 vertices, 150 polygon faces
- **Bounding Box**: $X_{min}=-27.0$, $X_{max}=27.0$, $Y_{min}=-70.199997$, $Y_{max}=44.0$, $Z_{min}=-3e-06$, $Z_{max}=70.0$
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
- **Plugin Manifest (JSON)**: [animal_adult_duroc_pig.json](animal_adult_duroc_pig.json)
- **Icon (PNG)**: [animal_adult_duroc_pig.png](animal_adult_duroc_pig.png)
- **3D Mesh (FBX)**: [SKM_Animal_Pig_Duroc.fbx](SKM_Animal_Pig_Duroc.fbx)
- **3D Mesh (MTL)**: [SKM_Animal_Pig_Duroc.mtl](SKM_Animal_Pig_Duroc.mtl)
- **3D Mesh (OBJ)**: [SKM_Animal_Pig_Duroc.obj](SKM_Animal_Pig_Duroc.obj)
- **3D Mesh (MTL)**: [SM_Animal_Pig_Duroc.mtl](SM_Animal_Pig_Duroc.mtl)
- **3D Mesh (OBJ)**: [SM_Animal_Pig_Duroc.obj](SM_Animal_Pig_Duroc.obj)
