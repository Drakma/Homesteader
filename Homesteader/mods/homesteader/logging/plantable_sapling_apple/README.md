# Sapling Apple (`plantable_sapling_apple`)

![Sapling Apple Icon](plantable_sapling_apple.png)

## Overview
- **Category**: `logging`
- **Item Identifier**: `plantable_sapling_apple`
- **Max Stack Size**: 99
- **Weight**: 1.0 kg
- **Base Economic Value**: $10.0
- **Consumable**: False

## Description
Standard logging asset used in the Homesteader simulation.

## Growth & Lifecycle (4 Stages)
- **Growth Type**: `tree` (`apple`)
- **Max Age Input**: 80 days
- **Current Stage**: Stage 1 - `sapling` (Age 0 - 12 days)

| Stage | Stage Name | Age Range | Stage Item ID |
| :---: | :--- | :---: | :--- |
| 1 | `sapling` **(Current)** | 0 – 12 days | `plantable_sapling_apple` |
| 2 | `small` | 12 – 32 days | `tree_apple_small` |
| 3 | `medium` | 32 – 60 days | `tree_apple_medium` |
| 4 | `large (mature)` | 60 – 80 days | `tree_apple` |

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
- **Plugin Manifest (JSON)**: [plantable_sapling_apple.json](plantable_sapling_apple.json)
- **Icon (PNG)**: [plantable_sapling_apple.png](plantable_sapling_apple.png)
