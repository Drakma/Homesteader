# Homesteader - Ground Tile Auto-Blending Setup

> **STATUS: UNREAL ENGINE 5 LEGACY — NOT YET PORTED TO UNITY 6**
>
> The ground tile blending system (subsystem, actor, material, DataTable) was
> originally written for Unreal Engine 5. The project has since switched to
> **Unity 6 (`6000.6.0f1`)**, but this blending system has **not yet been ported**.
>
> The blend masks and texture assets are engine-agnostic PNGs and are ready to
> use. The C++ subsystem/actor (`UGroundTileSubsystem`, `AGroundTileActor`) needs
> a C# MonoBehaviour equivalent, and the UE5 material graph needs a URP Shader
> Graph rebuild. The design and blend-priority data below remain the spec for
> that future port.
>
> **See `docs/GRID_AND_GROUND_STANDARDS.md` §5 for the current status note.**

This document covers the ground-to-ground blending system: when two
adjacent 1x1 ground tiles have different types (e.g. grass next to mud), the
seam between them fades softly instead of showing a hard rectangular edge.

It's an **autotile** system (like the classic RimWorld/Stardew Valley
approach): placing tiles is all that's required — blending happens
automatically at runtime based on each tile's neighbors, no manual painting.

---

## 1. What's already done (code + assets, no editor needed)

- **`Source/Homesteader/Public/World/GroundTileSubsystem.h` +
  `Private/World/GroundTileSubsystem.cpp`** — the runtime brain (UE5 C++).
  Tracks which ground type occupies each grid cell, and whenever a tile is
  registered/removed, recomputes a 4-bit neighbor bitmask (N/E/S/W) for that
  tile and its neighbors, then applies a dynamic material instance blending
  the tile's own textures with the single highest-priority differing
  neighbor type, masked by one of 16 precomputed soft-edged blend masks.
  **Needs C# port for Unity 6.**
- **`Source/Homesteader/Public/World/GroundTileActor.h` +
  `Private/World/GroundTileActor.cpp`** — `AGroundTileActor`, the actor
  class ground tiles must use (instead of a plain `StaticMeshActor`) so they
  self-register with the subsystem above. **Needs C# MonoBehaviour port.**
- **`tools/generate_blend_masks.py`** — generated the 16 blend masks at
  `assets/ground/blend_masks/T_GroundBlendMask_00.png` through `_15.png`
  and copied them to `Homesteader/Assets/Homesteader/Assets/Ground/BlendMasks/`.
  These PNGs are engine-agnostic and ready to use in Unity.
- **`FGroundTypeBlendInfo`** (`Source/Homesteader/Public/Core/HomesteaderTypes.h`)
  — a DataTable row struct (`BlendPriority: int32`, `bBlendable: bool`).
  Blend priority and blendability are data-driven, not hardcoded.
  **Needs a C# ScriptableObject equivalent for Unity 6.**
- **`Content/Homesteader/Data/DT_GroundTypes.csv`** — the default 20 ground
  types' priorities and blendability. **Needs migration to a Unity-compatible
  data format (ScriptableObject or JSON).**

None of this does anything yet without the material asset, content import,
and data assignment steps below — all of which need to be rebuilt for Unity 6.

---

## 2. Build the `M_Ground_Blend` material (Unity 6 — URP Shader Graph)

> **The UE5 material graph instructions below are preserved as the spec for
> the Unity 6 URP Shader Graph rebuild.** The parameter names and blend logic
> are the same; only the node system changes (UE5 Material Graph → Unity URP
> Shader Graph).

Create a new URP Shader Graph material at:

```
Assets/Homesteader/Assets/Materials/M_Ground_Blend
```

### Parameters (must be named exactly this — the C# sets them by name)

Add 7 **Texture2D** properties:

| Parameter Name | Purpose | Texture import type |
| :-- | :-- | :-- |
| `BaseColorA` | This tile's own BaseColor | Default (sRGB on) |
| `NormalA` | This tile's own Normal map | Normal Map (sRGB off) |
| `ORMA` | This tile's own ORM (AO/Rough/Metal) | Default (sRGB off) |
| `BaseColorB` | Overlay (neighbor) BaseColor | Default (sRGB on) |
| `NormalB` | Overlay Normal map | Normal Map (sRGB off) |
| `ORMB` | Overlay ORM | Default (sRGB off) |
| `BlendMask` | Soft edge mask (grayscale) | Default (sRGB off) |

### Graph

1. **Blend factor**: take `BlendMask`'s R channel as a single scalar `Alpha`
   (0 = show A, 1 = show B).
2. **Base Color**: `Lerp(A = BaseColorA.RGB, B = BaseColorB.RGB, Alpha)` →
   plug into the material's **Base Color** output.
3. **Normal**: `Lerp(A = NormalA.RGB, B = NormalB.RGB, Alpha)` → plug into
   **Normal**. (A straight RGB lerp of two normal maps isn't mathematically
   perfect, but at this low-poly stylized scale it reads fine.)
4. **ORM**: `Lerp(A = ORMA.RGB, B = ORMB.RGB, Alpha)`, then split with three
   channel masks:
   - `.R` → **Ambient Occlusion**
   - `.G` → **Roughness**
   - `.B` → **Metallic**
5. Material settings: **Surface Type = Opaque**, **Workflow = Metallic**.
6. Save.

---

## 3. Import the textures (Unity 6)

The raw PNGs already exist on disk in the exact folder locations, but Unity
still needs you to import them once:

1. In the Project window, navigate to
   `Assets/Homesteader/Assets/Ground/Textures/<type>/` for each of the 20
   ground types — you should see the 3 loose PNGs (`BaseColor`, `Normal`,
   `ORM`). Select all and set import settings. Repeat for all 20 type folders
   (60 textures total).
2. Do the same for `Assets/Homesteader/Assets/Ground/BlendMasks/` (16
   `T_GroundBlendMask_NN` PNGs).
3. For every `_Normal` texture: set **Texture Type = Normal Map** (this also
   disables sRGB automatically).
4. For every `_ORM` texture and every `T_GroundBlendMask_NN` mask texture:
   set **sRGB = Disabled**.
5. Leave `_BaseColor` textures on the default (sRGB on) settings.

This only needs to happen once; after that, the C# blend component resolves
these by their conventional path at runtime, so no manual per-type material
instances are needed — one shared `M_Ground_Blend` handles every ground type
dynamically.

### 3.5 Ground-type data (Unity 6)

Migrate `DT_GroundTypes.csv` to a C# ScriptableObject or JSON data file
with the same fields (`BlendPriority: int`, `Blendable: bool` per ground type).
Assign it to the blend component's data reference.

If you add a new ground type later, add a row with its `BlendPriority` and
`Blendable` — no code change needed. A ground type with no row at all
defaults to `BlendPriority=0, Blendable=true` (it can still be blended
*onto* by a higher-priority neighbor, but never initiates a blend itself).

---

## 4. Placing tiles

Use the `GroundTileActor` MonoBehaviour (or a prefab child of it, e.g.
`BP_GroundTile`) to place ground going forward — **not** a plain mesh
renderer. Per instance, set:

- **TileMesh** → the modular mesh matching the type, e.g. `SM_Tile_Grass`
  for `GroundType = "grass"` (see `GRID_AND_GROUND_STANDARDS.md` §2 for the
  full mesh list).
- **GroundType** → the matching string, e.g. `"grass"`, `"mud"`, `"dirt"`.

Placement position determines grid coordinate automatically via
`PlantingValidator.SnapToGrid` — just snap the object to the grid as
usual so it lines up with its neighbors.

**Existing tiles placed as plain mesh renderers will not participate in
blending** — they were never registered with the blend subsystem. They'll
keep rendering with their static, unblended material, which looks the same
as it always has (not broken, just not blended). Migrate them to
`GroundTileActor` when you want them to start blending against neighbors.

### Default blend priority (higher blends *over* lower; equal-or-lower never initiates a blend)

```
1: grass, dirt, sand, snow, forest_floor, farmland, path, gravel
2: tall_grass, trampled_grass
3: mud, swamp
4: pond, deep_water
```

### Never blend (hardscape — a crisp edge is the correct look here)

`Blendable=false` for:

```
road, black_top, concrete, bricks, wood_planks, flagstone
```

Edit the ground-type data file to retune either of these — no code change
needed.

---

## 5. Testing checklist

1. Complete the C# port of `GroundTileSubsystem` and `GroundTileActor`.
2. Complete §3.5 (import ground-type data, assign it to the blend
   component's data reference) — without this, every ground type defaults to
   priority 0 / blendable, so nothing ever "wins" a blend against anything
   else.
3. Place two adjacent `GroundTileActor`s: `GroundType="grass"` next to
   `GroundType="mud"`.
4. Play in Editor. The mud tile's edge facing the grass tile should show a
   soft organic gradient into grass, rather than a hard rectangular seam.
5. Check the console log if nothing blends — it warns by name if the blend
   material or a specific texture failed to load (most likely cause: step 2
   above, or §2/§3 weren't done for that ground type yet).
6. Try flipping which tile "wins" (e.g. swap which one is higher-priority)
   by testing a `mud`/`pond` pair — pond (priority 4) should bleed onto mud
   (priority 3), not the other way around.
7. If the blend appears on the *wrong* edge (e.g. the north edge blends when
   you placed a differing tile to the south), the North/East/South/West
   convention in the blend component and `generate_blend_masks.py` is
   inverted relative to how your level's tiles are actually laid out — flip
   the bit assignment in one of the two places to match the other.
