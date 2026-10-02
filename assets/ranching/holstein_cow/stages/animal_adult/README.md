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
A mature adult Holstein dairy cow, the final growth stage of the `holstein_cow` growth group (stage 3 of 3).

## Growth & Lifecycle (3 Stages)
- **Growth Type**: `animal` (`holstein_cow`)
- **Max Age**: 730 days
- **This Stage**: Stage 3 - `adult` **(Current)** (Age 365 - 730 days)

| Stage | Stage Name | Age Range | Resource |
| :---: | :--- | :---: | :--- |
| 1 | `calf` | 0 - 90 days | `stages/animal_calf/` |
| 2 | `yearling` | 90 - 365 days | `stages/animal_yearling/` |
| 3 | `adult` **(Current)** | 365 - 730 days | `stages/animal_adult/` |

## 3D Model & Mesh Specifications
- **Model**: `SM_Animal_Cow_Holstein.glb` (Meshy AI image-to-3D, smart-topology, meshy-t2, textured)
- **Physical Dimensions (W x H x D)**: `0.6984m x 1.48m x 2.2855m`, 4238 triangles
- **Shading Aesthetic**: 3D Low-Poly Faceted, Metric Scale, Ground-Aligned Pivot ($Y_{min} = 0$).
- **Icon**: rendered from the model via `tools/render_icon_from_model.py`

## Utilities & Resource Profile
| Utility System | Usage / Output Metric | Operational Details |
| :--- | :--- | :--- |
| **Water** | `None (unplumbed / dry)` | None (unplumbed / dry) |
| **Electricity** | `None (passive / unpowered)` | None (passive / unpowered) |
| **Sewage / Waste** | `None (no waste discharge)` | None (no waste discharge) |
| **Battery Power** | `None (no internal battery)` | None (no internal battery) |
| **Internet / Data** | `None (offline / non-networked)` | None (offline / non-networked) |

## Asset Files & Links
- **Plugin Manifest (JSON)**: [animal_adult_holstein_cow.json](animal_adult_holstein_cow.json)
- **Icon (PNG)**: [animal_adult_holstein_cow.png](animal_adult_holstein_cow.png)
- **3D Mesh (GLB)**: [SM_Animal_Cow_Holstein.glb](SM_Animal_Cow_Holstein.glb)
