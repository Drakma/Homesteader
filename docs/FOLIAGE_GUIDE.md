# Homesteader 3D Low-Poly Foliage & Vegetation System Guide

This guide details the integration of the **28 modular low-poly 3D foliage meshes and matching 128x128 icons** into Unreal Engine 5.

---

## 1. Directory Structure

All foliage assets are mirrored in both the HUD repository and your Unreal Engine 5 project:

| Workspace Path               | Unreal Engine 5 Project Path                 | Purpose                                       |
| :--------------------------- | :------------------------------------------- | :-------------------------------------------- |
| `assets/foliage/models/` | `Content/Homesteader/Assets/Foliage/Meshes/` | 28 Wavefront `.obj` meshes + `.mtl` materials |
| `assets/foliage/icons/`  | `Content/Homesteader/UI/Icons/Foliage/`      | 28 Transparent 128×128 RGBA icons             |

---

## 2. Asset Catalog & Metric Scale

All meshes are modeled in **centimeters ($1\text{ unit} = 1\text{ cm}$)** with the pivot anchored directly at ground level $(0, 0, 0)$ for seamless terrain placement:

### Trees (12 Models)

### Trees (12 Models)

1. `SM_Tree_Oak_Large.obj` ($574\text{ cm}$ tall, 828 tris, multi-tier faceted canopy, 12-sided flared trunk & 4 boughs)
2. `SM_Tree_Oak_Medium.obj` ($421\text{ cm}$ tall, 472 tris, balanced mid-growth canopy)
3. `SM_Tree_Oak_Small.obj` ($252\text{ cm}$ tall, 272 tris, young oak sapling with slender trunk)
4. `SM_Tree_Oak_Autumn.obj` ($465\text{ cm}$ tall, 440 tris, golden/amber autumn canopy)
5. `SM_Tree_Pine_Tall.obj` ($790\text{ cm}$ tall, 380 tris, 6-tier conical evergreen timber pine)
6. `SM_Tree_Pine_Medium.obj` ($490\text{ cm}$ tall, 188 tris, 4-tier mountain spruce)
7. `SM_Tree_Pine_Small.obj` ($300\text{ cm}$ tall, 128 tris, young conifer / Christmas tree)
8. `SM_Tree_Birch_Tall.obj` ($605\text{ cm}$ tall, 488 tris, slender curved white trunk, airy canopy)
9. `SM_Tree_Birch_Medium.obj` ($403\text{ cm}$ tall, 312 tris, twin-stem birch)
10. `SM_Tree_Apple.obj` ($375\text{ cm}$ tall, 808 tris, orchard tree studded with 3D red apples)
11. `SM_Tree_Willow.obj` ($519\text{ cm}$ tall, 280 tris, weeping canopy with 16 cascading tendril ribbons)
12. `SM_Tree_Dead_Snag.obj` ($410\text{ cm}$ tall, 104 tris, weathered bare trunk & 5 dead branch stubs)

### Bushes & Shrubs (5 Models)

13. `SM_Bush_Round_Large.obj` ($148\text{ cm}$ tall, 480 tris, lush spherical hedge)
14. `SM_Bush_Round_Medium.obj` ($102\text{ cm}$ tall, 320 tris, compact garden shrub)
15. `SM_Bush_Berry.obj` ($116\text{ cm}$ tall, 880 tris, wild bush studded with 14 3D ripe berry clusters)
16. `SM_Bush_Flowering.obj` ($109\text{ cm}$ tall, 620 tris, shrub accented with 12 5-petal floral blossom clusters)
17. `SM_Bush_DryScrub.obj` ($92\text{ cm}$ tall, 360 tris, arid sagebrush / desert scrub with gnarled branches)

### Brambles & Thickets (3 Models)

18. `SM_Bramble_Patch_Large.obj` ($65\text{ cm}$ tall, 400 tris, tangled thorny briar patch with 8 curved loops & thorns)
19. `SM_Bramble_Patch_Small.obj` ($42\text{ cm}$ tall, 165 tris, low briar cluster with sharp thorn facets)
20. `SM_Bramble_Arch.obj` ($161\text{ cm}$ tall, 117 tris, arched thorny briar trail barrier)

### Grasses & Wetland Flora (4 Models)

21. `SM_Grass_Tuft_Meadow.obj` ($47\text{ cm}$ tall, 80 tris, 16 curved 3-segment meadow grass blades)
22. `SM_Grass_Tall_Wild.obj` ($92\text{ cm}$ tall, 172 tris, wild prairie grass with 4 golden seed plume stalks)
23. `SM_Grass_Short_Lawn.obj` ($27\text{ cm}$ tall, 80 tris, 16 segmented ground cover lawn blades)
24. `SM_Flora_Reeds_Cattail.obj` ($142\text{ cm}$ tall, 216 tris, marsh reeds with 3 cattails & 12 arching leaves)

### Forest Floor & Features (4 Models)

25. `SM_Flora_Fern_Forest.obj` ($58\text{ cm}$ tall, 90 tris, 9 radiating tiered arching fronds)
26. `SM_Flora_Mushroom_Cluster.obj` ($64\text{ cm}$ tall, 309 tris, trio of hemispherical spotted forest mushrooms)
27. `SM_Flora_Tree_Stump.obj` ($68\text{ cm}$ tall, 224 tris, weathered cut stump with 4 root buttresses, moss & rings)
28. `SM_Flora_Fallen_Log.obj` ($60\text{ cm}$ tall, 208 tris, $250\text{ cm}$ long 12-sided mossy fallen timber log)

---

## 3. Importing into Unreal Engine 5

1. Open **Content Drawer** and navigate to `Content/Homesteader/Assets/Foliage/Meshes/`.
2. Drag and drop the `.obj` and `.mtl` files into the folder.
3. In the **FBX/OBJ Import Options**:
   - **Mesh** -> Set **Normal Import Method** to `Import Normals`.
   - **Material** -> Set **Material Search Location** to `Local` and check **Create Material Instances**.
   - Ensure **Import Uniform Scale** is `1.0`.

---

## 4. Setting up Landscape Foliage Painting

1. In the UE5 Mode Toolbar, switch from **Select Mode** to **Foliage Mode** (`Shift + 3`).
2. Drag the foliage static meshes (`SM_Tree_*`, `SM_Bush_*`, `SM_Grass_*`) into the Foliage palette.
3. Recommended settings per foliage category:

| Parameter                   | Large Trees                     | Bushes & Brambles                | Grasses & Lawn                    | Forest Floor (Stumps/Mushrooms) |
| :-------------------------- | :------------------------------ | :------------------------------- | :-------------------------------- | :------------------------------ |
| **Density**                 | $15 - 35\text{ / }10\text{m}^2$ | $60 - 120\text{ / }10\text{m}^2$ | $400 - 800\text{ / }10\text{m}^2$ | $10 - 25\text{ / }10\text{m}^2$ |
| **Radius**                  | $350\text{ cm}$                 | $120\text{ cm}$                  | $30\text{ cm}$                    | $180\text{ cm}$                 |
| **Scale X (Min/Max)**       | $0.85 - 1.25$                   | $0.80 - 1.20$                    | $0.75 - 1.30$                     | $0.90 - 1.15$                   |
| **Random Yaw**              | `True`                          | `True`                           | `True`                            | `True`                          |
| **Align to Normal**         | `False` (Grow Up)               | `True`                           | `True`                            | `False`                         |
| **Collision Preset**        | `BlockAll` / Capsule            | `OverlapAll` / Slowdown          | `NoCollision`                     | `BlockAll`                      |
| **Cull Distance (Min/Max)** | $15,000\text{ / }35,000$        | $8,000\text{ / }18,000$          | $3,500\text{ / }8,000$            | $5,000\text{ / }12,000$         |

---

## 5. Master Material & Wind Animation

For a vibrant stylized field, create a lightweight master material `M_Foliage_Master`:

1. **Shading Model**: `Default Lit` or `Subsurface` (for translucent leaves).
2. **Two Sided**: Checked (ensures leaf and grass cards are visible from both sides).
3. **World Position Offset (Wind)**:
   - Use the **SimpleGrassWind** material node connected to **World Position Offset**.
   - Set `WindIntensity = 0.25`, `WindWeight = 0.5`, `WindSpeed = 0.15`.
   - Multiply the offset by normalized vertex height (`(WorldPosition.Z - ObjectPosition.Z) / MeshHeight`) so trunks and roots stay firmly locked to the ground while leaf crowns gently sway.

---

## 6. 128×128 Transparent Preview Icons

All 28 preview icons are generated according to strict Homesteader rules:

- **Dimensions**: $128 \times 128\text{ px}$ 32-bit RGBA.
- **Safe Margin**: Minimum $15\text{ px}$ clean padding on all borders (max item bounding box $\le 98\text{ px}$).
- **Outer Perimeter**: 100% of perimeter pixels have `alpha == 0`.
- **Lighting**: 3/4 isometric view (~$35^\circ$ pitch, $45^\circ$ yaw) with top-left directional key lighting matching all other HUD item icons.
- Ready for inventory drag-and-drop, seed/sapling planting UI, and crafting databases.
