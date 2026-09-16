# Homesteader - Ground Tile Auto-Blending Setup

This document covers the new ground-to-ground blending system: when two
adjacent 1x1 ground tiles have different types (e.g. grass next to mud), the
seam between them fades softly instead of showing a hard rectangular edge.

It's an **autotile** system (like the classic RimWorld/Stardew Valley
approach): placing tiles is all that's required — blending happens
automatically at runtime based on each tile's neighbors, no manual painting.

This document is written for whoever does the Unreal Editor work (that might
be you, a teammate, or a future session with editor access) because the
material graph and content-import steps below can't be done from a script —
they need the actual Unreal Editor.

---

## 1. What's already done (code + assets, no editor needed)

- **`Source/Homesteader/Public/World/GroundTileSubsystem.h` +
  `Private/World/GroundTileSubsystem.cpp`** — the runtime brain. Tracks
  which ground type occupies each grid cell, and whenever a tile is
  registered/removed, recomputes a 4-bit neighbor bitmask (N/E/S/W) for that
  tile and its neighbors, then applies a dynamic material instance blending
  the tile's own textures with the single highest-priority differing
  neighbor type, masked by one of 16 precomputed soft-edged blend masks.
- **`Source/Homesteader/Public/World/GroundTileActor.h` +
  `Private/World/GroundTileActor.cpp`** — `AGroundTileActor`, the actor
  class ground tiles must use (instead of a plain `StaticMeshActor`) so they
  self-register with the subsystem above.
- **`scripts/generate_blend_masks.py`** — generated the 16 blend masks at
  `HUD/assets/ground/blend_masks/T_GroundBlendMask_00.png` through `_15.png`
  and copied them to
  `Homesteader/Content/Homesteader/Assets/Ground/BlendMasks/`.
- **`FGroundTypeBlendInfo`** (`Source/Homesteader/Public/Core/HomesteaderTypes.h`)
  — a DataTable row struct (`BlendPriority: int32`, `bBlendable: bool`).
  Blend priority and blendability are data-driven, not hardcoded, so
  designers can retune them without touching C++.
- **`Content/Homesteader/Data/DT_GroundTypes.csv`** — the default 20 ground
  types' priorities and blendability, ready to import as a DataTable (§3.5
  below). This is the same CSV → DataTable workflow already used for
  `DT_Items.csv`, `DT_Crops.csv`, etc.
- **`UHomesteaderGameInstance::GroundTypeDataTable`** — new property
  alongside the existing `ItemDataTable`/`CropDataTable`/etc., plus a
  `GetGroundTypeInfo(FName GroundType)` accessor `UGroundTileSubsystem`
  reads from.

None of this does anything yet without the material asset, content import,
and DataTable assignment steps below.

---

## 2. Build the `M_Ground_Blend` material (Unreal Editor)

Create a new Material asset at exactly:

```
/Game/Homesteader/Assets/Materials/M_Ground_Blend
```

(i.e. `Content/Homesteader/Assets/Materials/M_Ground_Blend.uasset`) — the
subsystem loads this exact path by default (`UGroundTileSubsystem::BlendMaterialPath`).

### Parameters (must be named exactly this — the C++ sets them by name)

Add 7 **Texture Sample Parameter 2D** nodes:

| Parameter Name | Purpose | Texture import type |
| :-- | :-- | :-- |
| `BaseColorA` | This tile's own BaseColor | Default (sRGB on) |
| `NormalA` | This tile's own Normal map | Normal Map (sRGB off) |
| `ORMA` | This tile's own ORM (AO/Rough/Metal) | Masks (sRGB off) |
| `BaseColorB` | Overlay (neighbor) BaseColor | Default (sRGB on) |
| `NormalB` | Overlay Normal map | Normal Map (sRGB off) |
| `ORMB` | Overlay ORM | Masks (sRGB off) |
| `BlendMask` | Soft edge mask (grayscale) | Masks (sRGB off) |

### Graph

1. **Blend factor**: take `BlendMask`'s output, add a **Component Mask (R)**
   node so you have a single scalar `Alpha` (0 = show A, 1 = show B).
2. **Base Color**: `Lerp(A = BaseColorA.RGB, B = BaseColorB.RGB, Alpha)` →
   plug into the material's **Base Color** pin.
3. **Normal**: `Lerp(A = NormalA.RGB, B = NormalB.RGB, Alpha)` → plug into
   **Normal**. (A straight RGB lerp of two normal maps isn't mathematically
   perfect, but at this low-poly stylized scale it reads fine — don't
   over-engineer this with a full reoriented-normal-blend node setup unless
   you actually see an artifact in play.)
4. **ORM**: `Lerp(A = ORMA.RGB, B = ORMB.RGB, Alpha)`, then split with three
   **Component Mask** nodes:
   - `.R` → **Ambient Occlusion** pin
   - `.G` → **Roughness** pin
   - `.B` → **Metallic** pin
5. Material settings: **Blend Mode = Opaque**, **Shading Model = Default Lit**.
6. Save.

That's the whole graph — 7 texture params, 3 lerps, 3 component masks, one
R-mask for the blend factor. No custom HLSL needed.

---

## 3. Import the textures (Unreal Editor)

The raw PNGs already exist on disk in the exact Content folder locations,
but Unreal still needs you to import them into `.uasset` Texture2D objects
once:

1. In the Content Browser, navigate to
   `Content/Homesteader/Assets/Ground/Textures/<type>/` for each of the 20
   ground types — you should see the 3 loose PNGs (`BaseColor`, `Normal`,
   `ORM`) show up as importable tiles. Select all and import (or double-
   click each). Repeat for all 20 type folders (60 textures total).
2. Do the same for `Content/Homesteader/Assets/Ground/BlendMasks/` (16
   `T_GroundBlendMask_NN` PNGs).
3. For every `_Normal` texture: open it, set **Compression Settings =
   Normal Map** (this also disables sRGB automatically).
4. For every `_ORM` texture and every `T_GroundBlendMask_NN` mask texture:
   set **Compression Settings = Masks (no sRGB)**.
5. Leave `_BaseColor` textures on the default (sRGB on) settings.

This only needs to happen once; after that, `UGroundTileSubsystem` resolves
these by their conventional path at runtime (`/Game/Homesteader/Assets/
Ground/Textures/<type>/T_Ground_<type>_<Map>`), so no manual per-type
material instances are needed — one shared `M_Ground_Blend` handles every
ground type dynamically.

### 3.5 Import the ground-type DataTable

Same workflow you'd use for `DT_Items.csv`:

1. In the Content Browser, right-click in `Content/Homesteader/Data/` →
   **Import to /Game/...** → select `DT_GroundTypes.csv`.
2. When prompted for the row struct, choose **GroundTypeBlendInfo**.
3. Name the resulting asset `DT_GroundTypes`.
4. Open your `UHomesteaderGameInstance` Blueprint subclass (the same place
   `ItemDataTable` etc. are already assigned) and assign `GroundTypeDataTable`
   → `DT_GroundTypes`.

If you add a new ground type later, add a row to `DT_GroundTypes.csv` (or
directly in the DataTable editor) with its `BlendPriority` and `bBlendable` —
no C++ change needed. A ground type with no row at all defaults to
`BlendPriority=0, bBlendable=true` (it can still be blended *onto* by a
higher-priority neighbor, but never initiates a blend itself).

---

## 4. Placing tiles

Use `AGroundTileActor` (or a Blueprint child of it, e.g. `BP_GroundTile`) to
place ground going forward — **not** a plain `StaticMeshActor`. Per
instance, set:

- **TileMesh** → the modular mesh matching the type, e.g. `SM_Tile_Grass`
  for `GroundType = "grass"` (see `GRID_AND_GROUND_STANDARDS.md` §2 for the
  full mesh list).
- **GroundType** → the matching FName, e.g. `"grass"`, `"mud"`, `"dirt"`.

Placement position determines grid coordinate automatically via
`UGridSystemSubsystem::WorldToGrid` — just snap the actor to the grid as
usual (`SnapWorldPositionToGrid`) so it lines up with its neighbors.

**Existing tiles placed as plain `StaticMeshActor`s will not participate in
blending** — they were never registered with `UGroundTileSubsystem`. They'll
keep rendering with their static, unblended material, which looks the same
as it always has (not broken, just not blended). Migrate them to
`AGroundTileActor` when you want them to start blending against neighbors.

### Default blend priority (higher blends *over* lower; equal-or-lower never initiates a blend)

Set in `DT_GroundTypes.csv` (§3.5), not hardcoded:

```
1: grass, dirt, sand, snow, forest_floor, farmland, path, gravel
2: tall_grass, trampled_grass
3: mud, swamp
4: pond, deep_water
```

### Never blend (hardscape — a crisp edge is the correct look here)

`bBlendable=false` in `DT_GroundTypes.csv` for:

```
road, black_top, concrete, bricks, wood_planks, flagstone
```

Edit `DT_GroundTypes.csv` (or the `DT_GroundTypes` DataTable directly in the
editor) to retune either of these — no C++ change needed.

---

## 5. Testing checklist

1. Build the C++ (this session couldn't compile it — first build will catch
   any typos in the new files).
2. Complete §3.5 (import `DT_GroundTypes.csv`, assign it to
   `GroundTypeDataTable` on your GameInstance Blueprint) — without this,
   every ground type defaults to priority 0 / blendable, so nothing ever
   "wins" a blend against anything else.
3. Place two adjacent `AGroundTileActor`s: `GroundType="grass"` next to
   `GroundType="mud"`.
4. Play in Editor. The mud tile's edge facing the grass tile should show a
   soft organic gradient into grass, rather than a hard rectangular seam.
5. Check `LogGroundTile` in the Output Log if nothing blends — it warns by
   name if the blend material or a specific texture failed to load (most
   likely cause: step 2 above, or §2/§3 weren't done for that ground type yet).
6. Try flipping which tile "wins" (e.g. swap which one is higher-priority)
   by testing a `mud`/`pond` pair — pond (priority 4) should bleed onto mud
   (priority 3), not the other way around.
7. If the blend appears on the *wrong* edge (e.g. the north edge blends when
   you placed a differing tile to the south), the North/East/South/West
   convention in `GroundTileSubsystem.cpp` and `generate_blend_masks.py` is
   inverted relative to how your level's tiles are actually laid out — flip
   the bit assignment in one of the two places to match the other.
