# Homesteader 3D Low-Poly Foliage & Vegetation System Guide

This guide details the integration of the **28 modular low-poly 3D foliage meshes and matching 128x128 icons** into **Unity 6 (`6000.6.0f1`)**.

---

## 1. Directory Structure

All foliage assets are mirrored in both the workspace and your Unity 6 project:

| Workspace Path               | Unity 6 Project Path                          | Purpose                                       |
| :--------------------------- | :------------------------------------------- | :-------------------------------------------- |
| `assets/foliage/models/` | `Assets/Homesteader/Assets/Foliage/Meshes/`  | 28 Wavefront `.obj` meshes + `.mtl` materials |
| `assets/foliage/icons/`  | `Assets/Homesteader/UI/Icons/Foliage/`       | 28 Transparent 128×128 RGBA icons             |

---

## 2. Asset Catalog & Metric Scale

All meshes are modeled in **meters ($1\text{ unit} = 1\text{ m}$)** with the pivot anchored directly at ground level $(0, 0, 0)$ for seamless terrain placement:

### Trees (12 Models)

1. `SM_Tree_Oak_Large.obj` ($5.74\text{ m}$ tall, 828 tris, multi-tier faceted canopy, 12-sided flared trunk & 4 boughs)
2. `SM_Tree_Oak_Medium.obj` ($4.21\text{ m}$ tall, 472 tris, balanced mid-growth canopy)
3. `SM_Tree_Oak_Small.obj` ($2.52\text{ m}$ tall, 272 tris, young oak sapling with slender trunk)
4. `SM_Tree_Oak_Autumn.obj` ($4.65\text{ m}$ tall, 440 tris, golden/amber autumn canopy)
5. `SM_Tree_Pine_Tall.obj` ($7.90\text{ m}$ tall, 380 tris, 6-tier conical evergreen timber pine)
6. `SM_Tree_Pine_Medium.obj` ($4.90\text{ m}$ tall, 188 tris, 4-tier mountain spruce)
7. `SM_Tree_Pine_Small.obj` ($3.00\text{ m}$ tall, 128 tris, young conifer / Christmas tree)
8. `SM_Tree_Birch_Tall.obj` ($6.05\text{ m}$ tall, 488 tris, slender curved white trunk, airy canopy)
9. `SM_Tree_Birch_Medium.obj` ($4.03\text{ m}$ tall, 312 tris, twin-stem birch)
10. `SM_Tree_Apple.obj` ($3.75\text{ m}$ tall, 808 tris, orchard tree studded with 3D red apples)
11. `SM_Tree_Willow.obj` ($5.19\text{ m}$ tall, 280 tris, weeping canopy with 16 cascading tendril ribbons)
12. `SM_Tree_Dead_Snag.obj` ($4.10\text{ m}$ tall, 104 tris, weathered bare trunk & 5 dead branch stubs)

### Bushes & Shrubs (5 Models)

13. `SM_Bush_Round_Large.obj` ($1.48\text{ m}$ tall, 480 tris, lush spherical hedge)
14. `SM_Bush_Round_Medium.obj` ($1.02\text{ m}$ tall, 320 tris, compact garden shrub)
15. `SM_Bush_Berry.obj` ($1.16\text{ m}$ tall, 880 tris, wild bush studded with 14 3D ripe berry clusters)
16. `SM_Bush_Flowering.obj` ($1.09\text{ m}$ tall, 620 tris, shrub accented with 12 5-petal floral blossom clusters)
17. `SM_Bush_DryScrub.obj` ($0.92\text{ m}$ tall, 360 tris, arid sagebrush / desert scrub with gnarled branches)

### Brambles & Thickets (3 Models)

18. `SM_Bramble_Patch_Large.obj` ($0.65\text{ m}$ tall, 400 tris, tangled thorny briar patch with 8 curved loops & thorns)
19. `SM_Bramble_Patch_Small.obj` ($0.42\text{ m}$ tall, 165 tris, low briar cluster with sharp thorn facets)
20. `SM_Bramble_Arch.obj` ($1.61\text{ m}$ tall, 117 tris, arched thorny briar trail barrier)

### Grasses & Wetland Flora (4 Models)

21. `SM_Grass_Tuft_Meadow.obj` ($0.47\text{ m}$ tall, 80 tris, 16 curved 3-segment meadow grass blades)
22. `SM_Grass_Tall_Wild.obj` ($0.92\text{ m}$ tall, 172 tris, wild prairie grass with 4 golden seed plume stalks)
23. `SM_Grass_Short_Lawn.obj` ($0.27\text{ m}$ tall, 80 tris, 16 segmented ground cover lawn blades)
24. `SM_Flora_Reeds_Cattail.obj` ($1.42\text{ m}$ tall, 216 tris, marsh reeds with 3 cattails & 12 arching leaves)

### Forest Floor & Features (4 Models)

25. `SM_Flora_Fern_Forest.obj` ($0.58\text{ m}$ tall, 90 tris, 9 radiating tiered arching fronds)
26. `SM_Flora_Mushroom_Cluster.obj` ($0.64\text{ m}$ tall, 309 tris, trio of hemispherical spotted forest mushrooms)
27. `SM_Flora_Tree_Stump.obj` ($0.68\text{ m}$ tall, 224 tris, weathered cut stump with 4 root buttresses, moss & rings)
28. `SM_Flora_Fallen_Log.obj` ($0.60\text{ m}$ tall, 208 tris, $2.50\text{ m}$ long 12-sided mossy fallen timber log)

---

## 3. Importing into Unity 6

1. In the **Project window**, navigate to `Assets/Homesteader/Assets/Foliage/Meshes/`.
2. Drag and drop the `.obj` and `.mtl` files into the folder.
3. In the **Model Import Inspector**:
   - **Model Tab**:
     - **Scale Factor**: `1.0` (Unity maps 1 meter to 1 unit)
     - **Convert Units**: `Checked`
     - **Bake Axis Conversion**: `Checked` (preserves proper $Y$-Up orientation)
     - **Read/Write**: `Checked` (enables runtime mesh manipulation if needed)
     - **Generate Colliders**: `Checked` for trees and stumps; `Unchecked` for grasses and bushes.
   - **Materials Tab**:
     - Set **Location** to `Use Embedded Materials` (reads `.mtl` definitions).
     - **Import Normals**: `Import` (preserve authored normals).

---

## 4. Setting up Terrain Foliage Painting

Unity 6 does not have a built-in foliage painter equivalent to Unreal's Foliage Mode. Use one of these approaches:

### Method A: Unity Terrain Detail System

1. Open the **Terrain** inspector and navigate to **Paint Details**.
2. Add each foliage mesh as a detail prototype:
   - Trees (`SM_Tree_*`): Add as **Tree prototypes** with appropriate bend factor.
   - Bushes, brambles, grasses: Add as **Detail prototypes** (grass meshes use `Render Mode: Vertex Lit`).
3. Recommended settings per foliage category:

| Parameter                   | Large Trees                     | Bushes & Brambles                | Grasses & Lawn                    | Forest Floor (Stumps/Mushrooms) |
| :-------------------------- | :------------------------------ | :------------------------------- | :-------------------------------- | :------------------------------ |
| **Density**                 | $15 - 35\text{ / }10\text{m}^2$ | $60 - 120\text{ / }10\text{m}^2$ | $400 - 800\text{ / }10\text{m}^2$ | $10 - 25\text{ / }10\text{m}^2$ |
| **Radius**                  | $3.5\text{ m}$                  | $1.2\text{ m}$                   | $0.3\text{ m}$                    | $1.8\text{ m}$                  |
| **Scale X (Min/Max)**       | $0.85 - 1.25$                   | $0.80 - 1.20$                    | $0.75 - 1.30$                     | $0.90 - 1.15$                   |
| **Random Yaw**              | `True`                          | `True`                           | `True`                            | `True`                          |
| **Align to Normal**         | `False` (Grow Up)               | `True`                           | `True`                            | `False`                         |
| **Cull Distance (Min/Max)** | $150\text{ / }350\text{ m}$     | $80\text{ / }180\text{ m}$       | $35\text{ / }80\text{ m}$         | $50\text{ / }120\text{ m}$      |

### Method B: GPU Instancer / Custom Scatter

For more control, use a third-party instancing solution (e.g., GPU Instancer) or a custom scatter script that places prefabs on the terrain with the same density/radius parameters above.

---

## 5. Master Material & Wind Animation

For a vibrant stylized field, create a lightweight URP shader or Shader Graph `M_Foliage_Master`:

1. **Surface Type**: `Opaque` (or `Transparent` for translucent leaves).
2. **Render Face**: `Both` (ensures leaf and grass cards are visible from both sides).
3. **Vertex Displacement (Wind)**:
   - Use a **Shader Graph** with a **Position** node connected to a **Time**-driven sine wave on the vertex's Y-axis.
   - Set `WindIntensity = 0.25`, `WindWeight = 0.5`, `WindSpeed = 0.15`.
   - Multiply the offset by normalized vertex height (`(WorldPosition.y - ObjectPosition.y) / MeshHeight`) so trunks and roots stay firmly locked to the ground while leaf crowns gently sway.

---

## 6. 128×128 Transparent Preview Icons

All 28 preview icons are generated according to strict Homesteader rules:

- **Dimensions**: $128 \times 128\text{ px}$ 32-bit RGBA.
- **Safe Margin**: Minimum $12\text{ px}$ clean padding on all borders (max item bounding box $\le 104\text{ px}$).
- **Outer Perimeter**: 100% of perimeter pixels have `alpha == 0`.
- **Lighting**: 3/4 isometric view (~$35^\circ$ pitch, $45^\circ$ yaw) with top-left directional key lighting matching all other HUD item icons.
- Ready for inventory drag-and-drop, seed/sapling planting UI, and crafting databases.
