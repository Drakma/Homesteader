# Homesteader Ground Assets (`assets/ground`)

Central repository for all modular ground tiles, scatter clutter props, seamless PBR texture sets, and landscape blend masks.

---

## 1. World Grid & Ground Scale Standards

| Property                | Value                                     | Source of Truth                           |
| :---------------------- | :---------------------------------------- | :---------------------------------------- |
| **Grid Cell Footprint** | `100 cm × 100 cm` (`1m × 1m`)             | `UGridSystemSubsystem::TileSize = 100.0f` |
| **Engine Units**        | `1 UU = 1 cm`                             | Unreal Engine default                     |
| **Tile Slab Height**    | `20 cm` with `2 cm` underside inset bevel | `SM_Tile_*` geometry                      |
| **Texel Density**       | `512 px / meter`                          | 1 texture repeat = 1 grid cell            |

All ground tile meshes and ground textures map **1:1 to the 1m × 1m building grid**.

---

## 2. Directory Structure

```
assets/ground/
├── <item_id>/           # 32 Ground Item Folders (10 Clutter props + 22 Modular Tiles)
│   ├── <item_id>.png    # 128×128 32-bit RGBA icon
│   ├── <item_id>.json   # Machine-readable plugin manifest (utilities, footprint, metrics)
│   ├── README.md        # Human-readable preview & specifications
│   └── <model>.obj/.mtl # 3D mesh files
├── blend_masks/         # 16 procedural landscape blend masks (T_GroundBlendMask_00.png – 15.png)
├── models/              # Shared master mesh library (SM_Tile_* and SM_Clutter_*)
└── textures/            # 20 seamless PBR ground texture sets (512×512 BaseColor, Normal, ORM)
    ├── black_top/       # Asphalt / compacted road surface
    ├── bricks/          # Cobblestone / brick paving
    ├── concrete/        # Smooth industrial concrete slab
    ├── deep_water/      # Deep lake / reservoir water surface
    ├── dirt/            # Compacted homestead earth
    ├── farmland/        # Aerated tilled soil
    ├── flagstone/       # Rustic irregular paving stones
    ├── forest_floor/    # Pine needles, leaf humus, and dark loam
    ├── grass/           # Vibrant homestead meadow grass
    ├── gravel/          # Compacted interlocking small stone aggregate
    ├── mud/             # Saturated wet earth with subtle puddling
    ├── path/            # Beaten foot trail earth
    ├── pond/            # Shallow littoral water surface
    ├── road/            # Country graded dirt road
    ├── sand/            # Riverbed / beach fine aggregate
    ├── snow/            # Cold alpine snow pack
    ├── swamp/           # Murky wetland turf
    ├── tall_grass/      # Wild pasture prairie grass
    ├── trampled_grass/  # Livestock corral worn pasture
    └── wood_planks/     # Timber boardwalk and decking planks
```

---

## 3. PBR Texture Specifications

Each of the 20 ground types provides 3 seamless 512×512 PNG maps:

1. **`T_Ground_<type>_BaseColor.png`**: sRGB diffuse albedo color with organic multi-octave tactile noise.
2. **`T_Ground_<type>_Normal.png`**: Tangent-space Direct-X normal map (**+Y inverted** for Unreal Engine).
3. **`T_Ground_<type>_ORM.png`**: Linear packed utility map:
   - **Red Channel**: Ambient Occlusion (AO)
   - **Green Channel**: Roughness
   - **Blue Channel**: Metallic (0.0 for natural terrain, modulated for water/metals)

---

## 4. Ground Mesh Tiles (`models/`)

- **Standard Modular Tiles** (`SM_Tile_<Type>.obj` / `.mtl`):
  - Dimension: `100.0 cm × 100.0 cm × 20.0 cm`
  - UV Mapping: `0.0 – 1.0` continuous top face UVs
  - Pivot: Ground-centered at `(0, 0, 0)` with top surface at $Z = 0$
- **Surface Geometry Variants**:
  - `SM_Tile_Farmland_Furrows`: Moldboard plow furrow ridges
  - `SM_Tile_Road_Asphalt`: Crowned road camber for rain runoff
  - `SM_Tile_WoodPlanks`: Subdivided deck boards with nail recesses
- **Scatter Clutter Props**:
  - `SM_Clutter_Acorns`, `SM_Clutter_Branch`, `SM_Clutter_Cattails`, `SM_Clutter_DirtClump`, `SM_Clutter_GrassTuft`, `SM_Clutter_Leaves`, `SM_Clutter_Pebbles`, `SM_Clutter_Pinecones`, `SM_Clutter_TallGrass`, `SM_Clutter_Twigs`.
