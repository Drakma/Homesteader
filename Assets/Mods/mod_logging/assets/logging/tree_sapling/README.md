# Tree Sapling (`tree_sapling`)

![Tree Sapling Icon](tree_sapling.png)

## Overview
- **Category**: `logging`
- **Item Identifier**: `tree_sapling`
- **Max Stack Size**: 99
- **Weight**: 1.0 kg
- **Base Economic Value**: $10.0
- **Consumable**: False

## Description
Standard logging asset used in the Homesteader simulation.

## Growth & Lifecycle (4 Stages)
- **Growth Type**: `tree` (`oak`)
- **Max Age Input**: 100 days
- **Current Stage**: Stage 1 - `sapling` (Age 0 - 15 days)

| Stage | Stage Name | Age Range | Stage Item ID |
| :---: | :--- | :---: | :--- |
| 1 | `sapling` **(Current)** | 0 – 15 days | `sapling_oak` |
| 2 | `small` | 15 – 40 days | `tree_oak_small` |
| 3 | `medium` | 40 – 75 days | `tree_oak_medium` |
| 4 | `large (mature)` | 75 – 100 days | `tree_oak_large` |

## 3D Model & Mesh Specifications
- **Physical Dimensions (X × Y × Z)**: `48.0 cm × 48.0 cm × 110.0 cm` (`0.48m × 0.48m × 1.1m`)
- **Mesh Complexity**: 92 vertices, 30 polygon faces
- **Bounding Box**: $X_{min}=-24.0$, $X_{max}=24.0$, $Y_{min}=-24.0$, $Y_{max}=24.0$, $Z_{min}=0.0$, $Z_{max}=110.0$
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
- **Plugin Manifest (JSON)**: [tree_sapling.json](tree_sapling.json)
- **Icon (PNG)**: [tree_sapling.png](tree_sapling.png)
- **3D Mesh (FBX)**: [SM_Tree_Sapling.fbx](SM_Tree_Sapling.fbx)
- **3D Mesh (MTL)**: [SM_Tree_Sapling.mtl](SM_Tree_Sapling.mtl)
- **3D Mesh (OBJ)**: [SM_Tree_Sapling.obj](SM_Tree_Sapling.obj)
