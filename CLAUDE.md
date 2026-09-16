# Homesteader - Project Instructions & Guidelines for Agents

> **IMPORTANT ARCHITECTURAL & PIPELINE UPDATE (2026-09-16)**:
>
> 1. **Engine Target**: The project has officially transitioned from Unreal Engine to **Unity 6 (`6000.6.0f1`)**.
> 2. **Zero-Credit Policy**: **NO PAID APIS** (CreativeClaw or Meshy.ai). All generation must use the **100% Free Stack**.
> 3. **Ready Helper Library**: `assets/free_generator.py` provides pre-tested Python functions for the free stack.
> 4. **Detailed Reference**: See [FREE_PIPELINE_GUIDE.md](file:///C:/Users/casey/Desktop/Homesteader/HUD/FREE_PIPELINE_GUIDE.md) and [UNITY_INTEGRATION_GUIDE.md](file:///C:/Users/casey/Desktop/Homesteader/HUD/UNITY_INTEGRATION_GUIDE.md).

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

## 2. Zero-Cost Asset Generation Pipeline ($0 Cost)

Under no circumstances should paid API keys or credits (CreativeClaw, Meshy.ai) be consumed. Use the free stack below via `assets/free_generator.py`:

### (A) 2D Item Icons ($0)

- **Model**: **FLUX.1 [schnell]** on Hugging Face Spaces (`black-forest-labs/FLUX.1-schnell`) or Google AI Studio (free tier) / Pollinations.ai.
- **How to Call**:

  ```python
  import sys
  sys.path.append(r"C:\Users\casey\Desktop\Homesteader\assets")
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
  1. No cost approval is needed since the generation cost is **$0**.
  2. Report progress as you go:
     `POST /api/update-asset-request` with `{"id": req_id, "status": "in_progress", "step": "Generating 2D icon via FLUX (Free)"}`
  3. Generate icon via `free_generator.generate_icon_flux()`.
  4. Standardize icon via `free_generator.standardize_icon()`.
  5. Generate 3D model via `free_generator.generate_3d_hunyuan()` (skip if `NO_MODEL=true` or icon-only).
  6. Convert to Unity FBX/GLB.
  7. Assemble `<item_id>.json` and `README.md`.
  8. Mark done: `POST /api/update-asset-request` with `{"id": req_id, "status": "done", "item_id": item_id, "step": "Done - generated via free FLUX + Hunyuan3D pipeline", "credits_used": {"creative_claw": 0, "meshy": 0}}`.
  9. Run `python update_catalog_readme.py` to keep the master catalog in sync.
