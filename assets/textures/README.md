# Homesteader Shared Textures (`assets/textures`)

Central repository for project-wide shared textures, color palettes, and skeletal mesh color maps.

---

## 1. Directory Structure

```
assets/textures/
├── palettes/
│   └── T_Homesteader_Palette.png     # Master 3D low-poly color palette texture
└── animals/
    └── T_Baby_Calf_BaseColor.png     # Skeletal mesh base color map for baby calf
```

---

## 2. Master Color Palette (`T_Homesteader_Palette.png`)

- **Resolution**: 512 × 512 px (or compact palette atlas)
- **Role**: Single source of truth for flat-shaded 3D low-poly models across the entire game (buildings, tools, farm machinery, fence posts, utility infrastructure, and clutter).
- **Material Workflow**: Models map specific UV island coordinates directly into designated color swatches within `T_Homesteader_Palette`, ensuring instant material batching, zero texture switching draw-call overhead, and coherent visual art style across all assets.

---

## 3. Skeletal & Entity Textures (`animals/`)

- **`T_Baby_Calf_BaseColor.png`**: UV mapped diffuse texture for the baby cattle livestock entity model.
