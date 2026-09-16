# Cattails (`clutter_cattails`)

![Cattails Icon](clutter_cattails.png)

## Overview
- **Category**: `building`
- **Item Identifier**: `clutter_cattails`
- **Max Stack Size**: 99
- **Weight**: 1.0 kg
- **Base Economic Value**: $10.0
- **Consumable**: False

## Description
Standard building asset used in the Homesteader simulation.

## 3D Model & Mesh Specifications
- **Physical Dimensions (X × Y × Z)**: `18.0 cm × 18.0 cm × 120.0 cm` (`0.18m × 0.18m × 1.2m`)
- **Mesh Complexity**: 8 vertices, 4 polygon faces
- **Bounding Box**: $X_{min}=-9.0$, $X_{max}=9.0$, $Y_{min}=-9.0$, $Y_{max}=9.0$, $Z_{min}=0.0$, $Z_{max}=120.0$
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
- **Plugin Manifest (JSON)**: [clutter_cattails.json](clutter_cattails.json)
- **Icon (PNG)**: [clutter_cattails.png](clutter_cattails.png)
- **3D Mesh (MTL)**: [SM_Clutter_Cattails.mtl](SM_Clutter_Cattails.mtl)
- **3D Mesh (OBJ)**: [SM_Clutter_Cattails.obj](SM_Clutter_Cattails.obj)
