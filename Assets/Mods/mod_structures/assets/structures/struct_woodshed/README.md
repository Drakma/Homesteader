# Building Woodshed (`struct_woodshed`)

![Building Woodshed Icon](struct_woodshed.png)

## Overview
- **Category**: `building`
- **Item Identifier**: `struct_woodshed`
- **Max Stack Size**: 99
- **Weight**: 1.0 kg
- **Base Economic Value**: $10.0
- **Consumable**: False

## Description
Standard building asset used in the Homesteader simulation.

## 3D Model & Mesh Specifications
- **Physical Dimensions (X × Y × Z)**: `210.0 cm × 310.0 cm × 215.0 cm` (`2.1m × 3.1m × 2.15m`)
- **Mesh Complexity**: 3228 vertices, 1076 polygon faces
- **Bounding Box**: $X_{min}=-105.0$, $X_{max}=105.0$, $Y_{min}=-155.0$, $Y_{max}=155.0$, $Z_{min}=0.0$, $Z_{max}=215.0$
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
- **Plugin Manifest (JSON)**: [struct_woodshed.json](struct_woodshed.json)
- **Icon (PNG)**: [struct_woodshed.png](struct_woodshed.png)
- **3D Mesh (MTL)**: [SM_Building_Woodshed.mtl](SM_Building_Woodshed.mtl)
- **3D Mesh (OBJ)**: [SM_Building_Woodshed.obj](SM_Building_Woodshed.obj)
