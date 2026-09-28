# Planted Sapling Pine (`tree_sapling_pine`)

![Planted Sapling Pine Icon](tree_sapling_pine.png)

## Overview
- **Category**: `logging`
- **Item Identifier**: `tree_sapling_pine`
- **Max Stack Size**: 99
- **Weight**: 1.0 kg
- **Base Economic Value**: $10.0
- **Consumable**: False

## Description
Standard logging asset used in the Homesteader simulation.

## Growth & Lifecycle (4 Stages)
- **Growth Type**: `tree` (`pine`)
- **Max Age Input**: 100 days
- **Current Stage**: Stage 1 - `sapling` (Age 0 - 15 days)

| Stage | Stage Name | Age Range | Stage Item ID |
| :---: | :--- | :---: | :--- |
| 1 | `sapling` **(Current)** | 0 – 15 days | `sapling_pine` |
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
- **Plugin Manifest (JSON)**: [tree_sapling_pine.json](tree_sapling_pine.json)
- **Icon (PNG)**: [tree_sapling_pine.png](tree_sapling_pine.png)
