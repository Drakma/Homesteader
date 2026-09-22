# Homesteader - Project Instructions & Guidelines for Agents

> **IMPORTANT ARCHITECTURAL & PIPELINE UPDATE (2026-09-16)**:
>
> 1. **Engine Target**: The project has officially transitioned from Unreal Engine to **Unity 6 (`6000.6.0f1`)**.
> 2. **Meshy-Only Policy (supersedes the old free stack)**: There is **no free pipeline any more — everything costs money**. The 100% Free Stack (FLUX.1 [schnell] + Tencent Hunyuan3D-2.0) and `tools/free_generator.py` are **RETIRED**; do not call or offer them. The **one and only pipeline is Meshy text-to-3D** (`tools/meshy_client.py` -> `create_text_to_3d()`), which returns the model **and its texture**. Pass the user's `PROMPT='...'` through **as-is** and append the standing technical rules to it. **LOW POLY IS MANDATORY, ALWAYS** (`model_type='lowpoly'`). The icon is **rendered from the finished model** with `tools/render_icon_from_model.py`. Always confirm the credit cost against `GET /api/meshy-balance` and get explicit approval before spending (see `PAID_ITEM_PIPELINE` in `tools/watch_asset_requests.py`).
> 3. **Retired Helper Library**: `tools/free_generator.py` is **dead code — do not use it**. The live client is `tools/meshy_client.py`.
> 4. **Detailed Reference**: See [MESHY_PIPELINE_GUIDE.md](file:///C:/Users/casey/Desktop/Homesteader/docs/MESHY_PIPELINE_GUIDE.md) and [UNITY_INTEGRATION_GUIDE.md](file:///C:/Users/casey/Desktop/Homesteader/docs/UNITY_INTEGRATION_GUIDE.md).

---

## 1. Engine Specifications: Unity 6

- **Engine Version**: Unity 6 (`6000.6.0f1`).
- **Scale Standard**: **1 Unit = 1 Meter** (unlike Unreal which was 1 Unit = 1 cm). When exporting from Blender, scale to metric meters.
- **3D Model Format**: **GLB is the default and standard model format** (`.glb`, textures embedded). Mods load GLB at runtime via glTFast with no editor import or prefab step. FBX is kept ONLY for rigged/animated models (Humanoid/Generic animation); OBJ is legacy and is being retired. Convert with `tools/convert_models_to_glb.py`.
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
- **Core catalog layout**: the whole catalog is ONE namespaced mod, `mods/homesteader/<category>/<asset_folder>/...`
  (Namespace / Category / Asset folder; `tools/package_catalog_as_mods.py` builds it, plus `mods/homesteader/gamerules/`).
  Append `.disabled` to a namespace, category OR asset folder name to switch it off (the phone Mods app does this);
  the loader, GLB resolver and packager all skip `.disabled` folders. The game loads `mods/` directly - do NOT bulk-sync
  it into `Assets/Mods` (Unity would import ~4 GB of GLBs and freeze).
- **Example mod**: `mods/example_lavender_homestead/`.

---

## 2. Asset Generation Pipeline (Meshy text-to-3D - the only pipeline)

**There is no free generation pipeline any more — everything costs money.** `tools/free_generator.py`, FLUX.1 [schnell], Tencent Hunyuan3D-2.0 and Creative Claw concept images are all **RETIRED**. Do not call them, do not offer them, do not write new code against them.

The one and only pipeline is **Meshy text-to-3D** via `tools/meshy_client.py` -> `create_text_to_3d()`. It returns the **model and its texture in a single task**.

**The user's prompt is the input.** A request carries a `PROMPT='...'` marker written by the user. Pass it to Meshy **as-is** and **append** the standing technical rules below. Never rewrite, replace or paraphrase the user's intent.

**LOW POLY IS MANDATORY, ALWAYS, NO EXCEPTIONS**: `model_type='lowpoly'` on every generation. Never `standard`, never `smart-topology`.

### (A) 3D Model + Texture generation (paid)

```python
import sys
sys.path.append(r"C:\Users\casey\Desktop\Homesteader\tools")
import meshy_client as mc

# user_prompt is the PROMPT='...' text from the request, verbatim.
prompt = f"{user_prompt}, low-poly game asset, modern, faceted low-poly styling"
preview_id = mc.create_text_to_3d(prompt, ai_model="meshy-6", model_type="lowpoly")
# then poll get_task('text-to-3d', preview_id), and refine for the texture pass
```

- Confirm the credit cost and resulting balance against `GET /api/meshy-balance` **before** spending, and wait for explicit approval.
- Download the **GLB** (the project's model format, textures embedded).

### (B) Icon rendered FROM the model (free, local)

There is **no separate 2D generation step**. The icon is always rendered from the finished textured model:

```bash
python tools/render_icon_from_model.py <model_path> assets/<category>/<item_id>/<item_id>.png
```

- Poses the textured model in Blender (isometric 3/4 front view), renders with top-left key lighting.
- **Tool pose**: long-handled tools are drawn diagonally with the handle upper-right and the working end (blade/head) lower-left, exactly like `assets/tools/tool_shovel_trenching/tool_shovel_trenching.png`. The model's own front axis is arbitrary, so **always open the result** and flip `face_left` if the working end is not lower-left.
- **Modern day only**: every item is a MODERN-DAY item unless the request explicitly says otherwise. Never antique/period styling.
- **Standardization** (free): must comply with Homesteader Icon Standards (128×128 px, 32-bit transparent RGBA, $\le 104$ px max dimension, $\ge 12$ px margin, 100% outer perimeter alpha=0, no borders, directional items facing left) via `assets/regen_icons.py` `standardize_icon_image()`.

### (C) Blender & Unity Formatting (free)

- Keep the model as **GLB** (textures embedded). Scale to metric and set the pivot (bottom-aligned for structures/crops, centered for tools).
- No GLB -> FBX conversion. Only rigged/animated models stay FBX (export with `path_mode='COPY'`, `embed_textures=True`).
- Converting an existing FBX/OBJ: `python tools/convert_models_to_glb.py --run`, then `python tools/apply_glb_to_manifests.py` (skips rigged models, keeps the originals).

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
  - 3D Model (`.glb` by default; `.fbx` only when rigged/animated; `.obj` is legacy).

---

## 3b. Editor / Schema Sync Rule

- Whenever a field changes in the asset kit rich editor (`assets/index.html`), update the matching base schema / category schema (`assets/_schemas/`), server validation (`tools/server.py`), manifest templates (`tools/process_queued_batch.py`, `docs/ASSET_CREATION_GUIDE.md`, `assets/_schemas/README.md`) and backfill existing manifests in the same change. The reverse also applies: schema or template changes must be reflected in the rich editor.

---

## 4. Asset Watcher & Request Queue Workflow

- `watch_asset_requests.py` polls `assets/_asset_requests/batches/`.
- When a batch arrives:
  1. **Every item costs money now** — there is no $0 path. Confirm the credit cost against `GET /api/meshy-balance` and get explicit approval before generating (see `PAID_ITEM_PIPELINE`).
  2. Report progress as you go:
     `POST /api/update-asset-request` with `{"id": req_id, "status": "in_progress", "step": "Generating 3D model via Meshy text-to-3D (lowpoly)"}`
  3. Generate the model via `meshy_client.create_text_to_3d(user_prompt, ai_model='meshy-6', model_type='lowpoly')` — pass the request's `PROMPT='...'` through as-is, appending the standing rules.
  4. Download the GLB (model + texture from the single Meshy task).
  5. Render the icon FROM the model: `python tools/render_icon_from_model.py <model_path> assets/<category>/<item_id>/<item_id>.png`, then standardize (128×128 RGBA).
  6. Scale to metric / set pivot as GLB; no FBX conversion.
  7. Assemble `<item_id>.json` and `README.md`.
  8. Mark done: `POST /api/update-asset-request` with `{"id": req_id, "status": "done", "item_id": item_id, "step": "Done - generated via Meshy text-to-3D (lowpoly)", "credits_used": {"creative_claw": 0, "meshy": <credits spent>}}`.
  9. Run `python tools/update_catalog_readme.py` to keep the master catalog in sync.
