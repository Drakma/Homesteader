# Horse Stable (`struct_complete_stable`)

![Horse Stable Icon](struct_complete_stable.png)

## Overview
- **Category**: `ranching`
- **Item Identifier**: `struct_complete_stable`
- **Max Stack Size**: 1
- **Weight**: 9000.0 kg
- **Base Economic Value**: $15000.0
- **Consumable**: False

## Description
A stable with multiple stall doors.

## ⚠️ Known Defect (flagged for regeneration)
`SM_Struct_Stable.fbx` has a corrupted mesh region near one roof corner: a cluster of
vertices is displaced far from the surface, stretching the surrounding triangles into
long degenerate spikes. In-engine this reads as a visible gap/tear in the roof from
certain angles (confirmed via Unity, Sept 2026 scale-validation pass - wireframe
inspection showed the spike geometry directly, not a rendering/material issue).
Needs the model regenerated via the Meshy pipeline or manually patched in Blender to
remove the spike triangles and rebuild that corner. Not fixable via engine-side
material/culling/z-write settings - already ruled out.

## 3D Model & Mesh Specifications
- **Physical Dimensions (X × Y × Z)**: `550.0 cm × 910.0 cm × 400.0 cm` (`5.5m × 9.1m × 4.0m`)
- **Mesh Complexity**: 1908 vertices, 656 polygon faces
- **Bounding Box**: $X_{min}=-275.0$, $X_{max}=275.0$, $Y_{min}=-455.0$, $Y_{max}=455.0$, $Z_{min}=0.0$, $Z_{max}=400.0$
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
- **Plugin Manifest (JSON)**: [struct_complete_stable.json](struct_complete_stable.json)
- **Icon (PNG)**: [struct_complete_stable.png](struct_complete_stable.png)
- **3D Mesh (MTL)**: [SM_Struct_Stable.mtl](SM_Struct_Stable.mtl)
- **3D Mesh (OBJ)**: [SM_Struct_Stable.obj](SM_Struct_Stable.obj)
- **3D Mesh (FBX)**: [SM_Struct_Stable.fbx](SM_Struct_Stable.fbx)
