# Homesteader - Ground Tiles & Textures Integration Guide

This guide documents the dedicated ground system for **Homesteader**: 20 distinct seamless PBR ground texture sets (BaseColor, Normal, ORM) and 26 modular 3D ground tile meshes ($100 \times 100\text{ cm}$).

---

## 1. Directory Structure

All ground assets are mirrored in both the workspace and your Unity 6 project:

```
Assets/Homesteader/Assets/Ground/
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
│   ├── forest_floor/      (T_Ground_forest_floor_BaseColor.png, Normal, ORM)
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
   - **Unity Texture Import Settings**: Texture Type `Default`, sRGB `Enabled`, Compression `Normal Quality`, Generate Mip Maps `Enabled`.
2. **`T_Ground_<Type>_Normal.png`**:
   - Tangent-space normal map.
   - Generates realistic micro-surface relief and facet shading.
   - **Unity Texture Import Settings**: Texture Type `Normal Map`, sRGB `Disabled`, Create from Grayscale `Unchecked`.
3. **`T_Ground_<Type>_ORM.png`**:
   - Channel-packed material texture:
     - **R (Red)** = **Ambient Occlusion** (recessed crevice shading).
     - **G (Green)** = **Roughness** (slick wet surfaces like mud/water have low values; dry stone/dirt have high values).
     - **B (Blue)** = **Metallic** ($0.0$ for organics, $0.05\text{–}0.1$ for asphalt/mineral glints).
   - **Unity Texture Import Settings**: Texture Type `Default`, sRGB `Disabled`, Compression `Normal Quality`.

---

## 3. Modular 3D Ground Tile Specifications

- **Footprint**: Exactly **$100 \times 100\text{ cm}$** ($1\text{m} \times 1\text{m}$, exactly 1 grid cell).
- **Thickness / Depth**: **$20\text{ cm}$** (top surface at $Y = 0$, base at $Y = -0.20\text{ m}$).
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

## 4. Unity 6 Setup Guide

### Method A: Creating URP Materials

1. Navigate to `Assets/Homesteader/Assets/Ground/Materials/`.
2. Create a new **URP Lit Shader** material named **`MI_Ground_<Type>`** (e.g., `MI_Ground_Farmland`, `MI_Ground_Grass`).
3. In the Material Inspector:
   - Assign `T_Ground_<Type>_BaseColor` to the **Base Map** slot.
   - Assign `T_Ground_<Type>_Normal` to the **Normal Map** slot.
   - Assign `T_Ground_<Type>_ORM` to the **Mask Map** (or use a custom shader graph that unpacks R=AO, G=Roughness, B=Metallic).
4. Assign `MI_Ground_<Type>` to the corresponding mesh renderer or terrain layer.

### Method B: Unity Terrain Layer Painting

1. Open the **Terrain** inspector and navigate to **Paint Terrain**.
2. Under **Layers**, click **Edit Terrain Layers** -> **Add Layer**:
   - `Layer_Grass` -> assign `MI_Ground_Grass`
   - `Layer_Dirt` -> assign `MI_Ground_Dirt`
   - `Layer_Farmland` -> assign `MI_Ground_Farmland`
   - `Layer_Gravel` -> assign `MI_Ground_Gravel`
   - `Layer_Mud` -> assign `MI_Ground_Mud`
3. Paint smoothly across the terrain with automatic weight blending.

### Method C: Grid-Snapped Mesh Placement

1. In the Unity Editor, set **Grid Snapping** (Edit > Grid and Snap Settings) to **$1.0$** (1 meter).
2. Drag `SM_Tile_*` meshes directly into the scene.
3. Tiles will seamlessly align edge-to-edge without gaps or overlapping z-fighting.

---

## 5. Verification Commands

To re-run automated verification on all textures and meshes at any time:

```powershell
C:\Python313\python.exe scripts\validate_ground_assets.py
```
