# Pine Sapling (`plantable_pine_sapling`)

![Pine Sapling Icon](plantable_pine_sapling.png)

## Overview
- **Category**: `logging`
- **Item Identifier**: `plantable_pine_sapling`
- **Max Stack Size**: 10
- **Weight**: 3.5 kg
- **Base Economic Value**: $15.0
- **Consumable**: False

## Description
A young pine sapling with its roots wrapped in burlap and ready to plant.

## Growth & Lifecycle (4 Stages)
- **Growth Type**: `tree` (`pine`)
- **Max Age Input**: 100 days
- **Current Stage**: Stage 1 - `sapling` (Age 0 - 15 days)

| Stage | Stage Name | Age Range | Stage Item ID |
| :---: | :--- | :---: | :--- |
| 1 | `sapling` **(Current)** | 0 – 15 days | `plantable_pine_sapling` |
| 2 | `small` | 15 – 40 days | `tree_pine_small` |
| 3 | `medium` | 40 – 75 days | `tree_pine_medium` |
| 4 | `large (mature)` | 75 – 100 days | `tree_pine_tall` |

## 3D Model & Mesh Specifications
- **Physical Dimensions**: *Model geometry dynamically procedural or referenced via sub-mesh components.*
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
- **Plugin Manifest (JSON)**: [plantable_pine_sapling.json](plantable_pine_sapling.json)
- **Icon (PNG)**: [plantable_pine_sapling.png](plantable_pine_sapling.png)
