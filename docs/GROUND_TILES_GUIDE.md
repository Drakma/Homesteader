# Homesteader - Ground Tiles & Textures Integration Guide

This guide documents the dedicated ground system for **Homesteader**: 20 distinct seamless PBR ground texture sets (BaseColor, Normal, ORM) and 26 modular 3D ground tile meshes ($200 \times 200\text{ cm}$).

---

## 1. Directory Structure

All ground assets are mirrored in both the workspace and your Unreal Engine project:

```
Content/Homesteader/Assets/Ground/
├── Textures/
│   ├── gravel/             (T_Ground_gravel_BaseColor.png, Normal, ORM)
│   ├── dirt/               (T_Ground_dirt_BaseColor.png, Normal, ORM)
│   ├── road/               (T_Ground_road_BaseColor.png, Normal, ORM)
│   ├── path/               (T_Ground_path_BaseColor.png, Normal, ORM)
│   ├── grass/              (T_Ground_grass_BaseColor.png, Normal, ORM)
│   ├── tall_grass/         (T_Ground_tall_grass_BaseColor.png, Normal, ORM)
│   ├── farmland/           (T_Ground_farmland_BaseColor.png, Normal, ORM)
│   ├── trampled_grass/     (T_Ground_trampled_grass_BaseColor.png, Normal, ORM)
│   ├── concrete/           (T_Ground_concrete_BaseColor.png, Normal, ORM)
│   ├── black_top/          (T_Ground_black_top_BaseColor.png, Normal, ORM)
│   ├── bricks/             (T_Ground_bricks_BaseColor.png, Normal, ORM)
│   ├── mud/                (T_Ground_mud_BaseColor.png, Normal, ORM)
│   ├── swamp/              (T_Ground_swamp_BaseColor.png, Normal, ORM)
│   ├── pond/               (T_Ground_pond_BaseColor.png, Normal, ORM)
│   ├── deep_water/         (T_Ground_deep_water_BaseColor.png, Normal, ORM)
│   ├── sand/               (T_Ground_sand_BaseColor.png, Normal, ORM)
│   ├── wood_planks/        (T_Ground_wood_planks_BaseColor.png, Normal, ORM)
│   ├── snow/               (T_Ground_snow_BaseColor.png, Normal, ORM)
│   ├── forest_floor/       (T_Ground_forest_floor_BaseColor.png, Normal, ORM)
│   └── flagstone/          (T_Ground_flagstone_BaseColor.png, Normal, ORM)
└── Meshes/
    ├── SM_Tile_Gravel.obj, SM_Tile_Dirt.obj, SM_Tile_Grass.obj, ... (20 standard tiles)
    ├── SM_Tile_Farmland_Furrows.obj   (3D tilled ridges)
    ├── SM_Tile_Road_Asphalt.obj       (Crowned asphalt road with drainage)
    ├── SM_Tile_WoodPlanks.obj         (3D wooden deck boards)
    ├── SM_Clutter_TallGrass.obj       (Double-sided 3D grass clump, 55cm)
    ├── SM_Clutter_Pebbles.obj         (Scattered river rocks cluster)
    └── SM_Clutter_Cattails.obj        (Marsh reeds, 120cm)
```

---

## 2. Ground Texture Specifications ($512 \times 512\text{ px}$ Seamless)

Each ground type provides a 3-texture PBR set:

1. **`T_Ground_<Type>_BaseColor.png`**:
   - Stylized, faceted, rich low-poly color texture.
   - Seamlessly tileable with wrapped borders.
   - **UE5 Texture Settings**: Compression `Default`, sRGB `Enabled`, Mip Gen `FromTextureGroup` (Texture Group `World`).
2. **`T_Ground_<Type>_Normal.png`**:
   - Tangent-space Direct-X normal map with inverted green channel ($+Y$ down).
   - Generates realistic micro-surface relief and facet shading.
   - **UE5 Texture Settings**: Compression `Normalmap (DXT5, BC5)`, sRGB `Disabled`.
3. **`T_Ground_<Type>_ORM.png`**:
   - Channel-packed material texture:
     - **R (Red)** = **Ambient Occlusion** (recessed crevice shading).
     - **G (Green)** = **Roughness** (slick wet surfaces like mud/water have low values; dry stone/dirt have high values).
     - **B (Blue)** = **Metallic** ($0.0$ for organics, $0.05\text{–}0.1$ for asphalt/mineral glints).
   - **UE5 Texture Settings**: Compression `Masks (no sRGB)` or `Default`, sRGB `Disabled`.

---

## 3. Modular 3D Ground Tile Specifications

- **Footprint**: Exactly **$200 \times 200\text{ cm}$** ($2\text{m} \times 2\text{m}$).
- **Thickness / Depth**: **$20\text{ cm}$** (top surface at $Z = 0$, base at $Z = -20\text{ cm}$).
- **Beveling**: $2\text{ cm}$ inward bevel on bottom edges to guarantee zero seam flickering when snapping adjacent tiles.
- **UV Layout**: Top face is normalized to full $[0, 1]$ UV space for 1:1 seamless texture mapping.

### Specialized Variants:

- **`SM_Tile_Farmland_Furrows`**: Features 4 physical sinusoidal ridges ($4.5\text{ cm}$ height) running across the tile, ideal for farm plots and seed planting.
- **`SM_Tile_Road_Asphalt`**: Crowned road profile ($+3\text{ cm}$ high in center, sloping down to $0\text{ cm}$ at shoulders) for authentic roadway drainage.
- **`SM_Tile_WoodPlanks`**: 8 individual physical floorboards separated by physical gaps for cabin decks and boat docks.
- **`SM_Clutter_TallGrass`**: Crossed-quad foliage clump ($40\text{ cm}$ wide, $55\text{ cm}$ tall) for foliage painting on grass tiles.
- **`SM_Clutter_Cattails`**: $120\text{ cm}$ tall marsh reeds for swamp and pond edges.
- **`SM_Clutter_Pebbles`**: 12 faceted low-poly stones for riverbeds and gravel driveways.

---

## 4. Unreal Engine 5 Setup Guide

### Method A: Creating Material Instances from `M_Homesteader_Master`

1. Navigate to `/Game/Homesteader/Assets/Materials/`.
2. Right-click `M_Homesteader_Master` -> **Create Material Instance**.
3. Name it **`MI_Ground_<Type>`** (e.g., `MI_Ground_Farmland`, `MI_Ground_Grass`).
4. In the Material Instance Details:
   - Check **BaseColor** parameter -> select `T_Ground_<Type>_BaseColor`.
   - Check **Normal** parameter -> select `T_Ground_<Type>_Normal`.
   - Check **ORM** parameter -> select `T_Ground_<Type>_ORM`.
5. Assign `MI_Ground_<Type>` to the corresponding static mesh or landscape layer.

### Method B: UE5 Landscape Layer Painting

1. Open the **Landscape** tool in Unreal Engine (Shift + 2).
2. Under **Paint** -> **Target Layers**, click the **+** icon to create Layer Info objects:
   - `Layer_Grass` -> assign `MI_Ground_Grass`
   - `Layer_Dirt` -> assign `MI_Ground_Dirt`
   - `Layer_Farmland` -> assign `MI_Ground_Farmland`
   - `Layer_Gravel` -> assign `MI_Ground_Gravel`
   - `Layer_Mud` -> assign `MI_Ground_Mud`
3. Paint smoothly across the terrain with automatic weight blending.

### Method C: Grid-Snapped Mesh Placement

1. In the Unreal Editor Viewport, set **Grid Snapping** to **$100$** or **$200$**.
2. Drag `SM_Tile_*` meshes directly into the level.
3. Tiles will seamlessly align edge-to-edge without gaps or overlapping z-fighting.

---

## 5. Verification Commands

To re-run automated verification on all textures and meshes at any time:

```powershell
python scripts\validate_ground_assets.py
```
