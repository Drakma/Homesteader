# Homesteader - Project Instructions & Guidelines for Agents

> **IMPORTANT ARCHITECTURAL & PIPELINE UPDATE (2026-09-16)**:
>
> 1. **Engine Target**: The project has officially transitioned from Unreal Engine to **Unity 6 (`6000.6.0f1`)**.
> 2. **Default-Free Policy (2026-09-17 update)**: The **100% Free Stack** is the DEFAULT for all generation. Paid services (CreativeClaw, Meshy.ai) are available as an explicit **opt-in per request** via the Request Asset / Request Growth Group dialog's "Generation Pipeline" dropdown - only use them when a request is marked `PIPELINE=paid`, and always confirm the credit cost with the user before spending (see PAID_ITEM_PIPELINE in `tools/watch_asset_requests.py`).
> 3. **Ready Helper Library**: `tools/free_generator.py` provides pre-tested Python functions for the free stack.
> 4. **Detailed Reference**: See [FREE_PIPELINE_GUIDE.md](file:///C:/Users/casey/Desktop/Homesteader/docs/FREE_PIPELINE_GUIDE.md) and [UNITY_INTEGRATION_GUIDE.md](file:///C:/Users/casey/Desktop/Homesteader/docs/UNITY_INTEGRATION_GUIDE.md).

---

## 1. Engine Specifications: Unity 6

- **Engine Version**: Unity 6 (`6000.6.0f1`).
- **Scale Standard**: **1 Unit = 1 Meter** (unlike Unreal which was 1 Unit = 1 cm). When exporting FBX/GLB from Blender, scale to metric meters.
- **Coordinate System**: Left-handed ($Y$-Up, $+Z$-Forward, $+X$-Right).
- **Pivots**: Ground-level pivot ($Z_{min} = 0$, $Y_{min} = 0$ in Unity) for structures, furniture, and placed crops; centered pivot for handheld tools and items.
- **2D UI / Icons**: 128×128 px 32-bit RGBA PNG, imported in Unity as `Texture Type: Sprite (2D and UI)`.
- **Character / Rigging**:
  - Humanoids / Bipeds: Use the Blender Mixamo Addon (`bl_ext.blender_org.mixamo_rig`). Set Unity Animation Type to **Humanoid**; Unity Mecanim auto-maps bones with 100% fidelity.
  - Quadrupeds / Animals: Standard quadruped skeleton or Animal Animator (`bl_ext.blender_org.animal_animator`). Set Unity Animation Type to **Generic**.

---

## 1a. UI Design Rules (UI Toolkit)

- **Text fields** (TextField, number fields, search boxes, dropdowns): text is ALWAYS vertically centered in the box, including placeholder text. Style the inner input, not just the outer element: justify-content: center; -unity-text-align: middle-left; padding-top: 0; padding-bottom: 0; on .unity-base-text-field__input / .unity-base-popup-field__input, and zero margin/padding on the inner TextElement. Horizontal alignment stays left.
- **Buttons**: label text is ALWAYS centered vertically AND horizontally (-unity-text-align: middle-center).
- Reference implementations: .asset-search-input and .asset-category-dropdown in Resources/HUDTree/HudUI.uss.

---

## 1b. Mod System (Runtime Content Loading)

Mods are loaded from disk at startup, before terrain generation, so modded
biomes are baked into the world.

- **Locations**: `<persistentDataPath>/Mods` and `<StreamingAssets>/Mods`.
- **Shapes**: a mod is either a **folder** or a **`.zip` archive** containing a
  `mod.json` at its root (a zip whose files sit inside one top-level folder is
  flattened automatically). Append `.disabled` to a folder/zip name to skip it.
- **Manifest** (`mod.json`): `id` (required, snake_case), `name`, `version`,
  `author`, `date`, `description`, plus a `contents[]` list where each entry has a
  `type` (biome / structure / food / …) and a `path` (exact, wildcard, or folder).
- **Load order**: dependencies first, then `load_after`, then alphabetical.
- **Merge rule**: core content always wins — a mod biome whose id collides with
  a core biome is rejected and logged, never overwritten.
- **Code**: `Homesteader/Assets/Scripts/Modding/`
  - `ModJson.cs` — dependency-free JSON reader (arbitrary shapes).
  - `ModManifestParser.cs` — validates `mod.json` into a `ModManifest`.
  - `ModDiscovery.cs` — scans folders/zips, extracts archives, orders mods.
  - `ModFileResolver.cs` — path/wildcard expansion, sandboxed to the mod root.
  - `ModLoader.cs` — applies content into game registries (the ONLY merge site).
  - `ModManager.cs` — MonoBehaviour bootstrapper; add it to a boot-scene object.
- **Full spec**: [MODDING_GUIDE.md](file:///C:/Users/casey/Desktop/Homesteader/docs/MODDING_GUIDE.md).
- **Example mod**: `mods/example_lavender_homestead/`.

---

## 2. Zero-Cost Asset Generation Pipeline ($0 Cost, Default)

Use the free stack below via `assets/free_generator.py` for every request unless it's explicitly marked `PIPELINE=paid` (chosen by the user in the Request Asset / Request Growth Group dialog's "Generation Pipeline" dropdown). For a `PIPELINE=paid` item, use CreativeClaw/Meshy instead for that item only - always confirm the credit cost with the user before spending (see `PAID_ITEM_PIPELINE` in `assets/watch_asset_requests.py`).

### (A) 2D Item Icons ($0)

- **Model**: **FLUX.1 [schnell]** on Hugging Face Spaces (`black-forest-labs/FLUX.1-schnell`) or Google AI Studio (free tier) / Pollinations.ai.
- **How to Call**:

  ```python
  import sys
  sys.path.append(r"C:\Users\casey\Desktop\Homesteader\tools")
  import free_generator as fg

  raw_icon_path = fg.generate_icon_flux(
      item_name="Carrot",
      description="freshly harvested orange carrot with leafy green top",
      direction="left"
  )
  ```

- **Standardization**:
  Must comply with Homesteader Icon Standards (128×128 px, 32-bit transparent RGBA, $\le 104$ px max dimension, $\ge 12$ px margin, 100% outer perimeter alpha=0, no borders, directional items facing left):
  ```python
  ok, msg = fg.standardize_icon(raw_icon_path, target_icon_path)
  ```

### (B) 3D Model Generation ($0)

- **Model**: **Tencent Hunyuan3D-2.0** on Hugging Face Spaces (`tencent/Hunyuan3D-2`).
- Generates game-ready low-poly textured 3D meshes directly from the standardized 2D icon:
  ```python
  glb_path = fg.generate_3d_hunyuan(
      icon_path=target_icon_path,
      output_dir=target_folder,
      item_id=item_id,
      target_faces=8000
  )
  ```

### (C) Blender & Unity Formatting ($0)

- Convert GLB to Unity-ready FBX with embedded textures:
  ```python
  fbx_path = fg.convert_glb_to_unity_fbx(glb_path, output_fbx_path)
  ```
- All Blender exports MUST set `path_mode='COPY'` and `embed_textures=True`.

---

## 3. Mandatory Directory & Item Structure

Every asset must live in `assets/<category>/<item_id>/`:

- The 16 canonical categories: `farming`, `ranching`, `logging`, `fishing`, `building`, `structures`, `tools`, `electricity`, `water`, `waste`, `internet`, `hud`, `ground`, `food`, `fuel`, `materials`.
- Naming prefixes:
  - `struct_*`: cabins, barns, sheds, coops.
  - `machinery_*`: tractors, skidsteers.
  - `tool_*`: axes, hoes, hammers, wrenches.
  - `animal_*`: `animal_chicken_*`, `animal_cow_*`, `animal_fish_*`.
  - `fishing_*`: rods, lures, nets, tackle.
  - `seed_*`: plantable seeds (all use 3D seed packet models).
  - `crop_*`: growing crops.
  - `food_*`: direct edible harvests (e.g. `food_apple`, `food_truffle`).
  - `ingredient_*`: cooking/crafting drops (singular `ingredient_`, e.g. `ingredient_beef`, `ingredient_fillet_salmon`).
  - `fuel_*`: hydrocarbons, propane, firewood cords, bulk fuel tanks.
  - `mat_*`: lumber, gravel/dirt piles, bales, wool, pelts.
  - `electricity_*`: solar, wind, batteries, generators (never `electric_`).
  - `water_*`: cisterns, pumps, filters, sprinklers.
  - `waste_*`: septic tanks, compost bins, composting toilets, manure.
  - `net_*`: antennas, dishes, routers (never `internet_`).
  - `tile_*` & `clutter_*`: ground tiles and clutter in `assets/ground/`.
- Required files in each item directory:
  - `<item_id>.png` (128×128 RGBA, NEVER `icon.png`).
  - `<item_id>.json` (Plugin manifest).
  - `README.md` (Human-readable preview).
  - 3D Model (`.fbx`, `.glb`, or `.obj`).

---

## 4. Asset Watcher & Request Queue Workflow

- `watch_asset_requests.py` polls `assets/_asset_requests/batches/`.
- When a batch arrives:
  1. No cost approval is needed for regular items - the generation cost is **$0** via the free stack. An item marked `PIPELINE=paid` is the exception: confirm the credit cost with the user before generating (see `PAID_ITEM_PIPELINE`).
  2. Report progress as you go:
     `POST /api/update-asset-request` with `{"id": req_id, "status": "in_progress", "step": "Generating 2D icon via FLUX (Free)"}`
  3. Generate icon via `free_generator.generate_icon_flux()`.
  4. Standardize icon via `free_generator.standardize_icon()`.
  5. Generate 3D model via `free_generator.generate_3d_hunyuan()` (skip if `NO_MODEL=true` or icon-only).
  6. Convert to Unity FBX/GLB.
  7. Assemble `<item_id>.json` and `README.md`.
  8. Mark done: `POST /api/update-asset-request` with `{"id": req_id, "status": "done", "item_id": item_id, "step": "Done - generated via free FLUX + Hunyuan3D pipeline", "credits_used": {"creative_claw": 0, "meshy": 0}}`.
  9. Run `python tools/update_catalog_readme.py` to keep the master catalog in sync.
