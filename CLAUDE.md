# Homesteader - Project Instructions & Guidelines for Agents

> **IMPORTANT ARCHITECTURAL & PIPELINE UPDATE (2026-09-28)**:
>
> 1. **Engine Target**: The project has officially transitioned from Unreal Engine to **Unity 6 (`6000.6.0f1)`**.
> 2. **Reference-Image + Meshy Image-to-3D Policy (supersedes the old text-to-3D-only policy)**: There is **no free pipeline any more — everything costs money**. The 100% Free Stack, `tools/free_generator.py`, and plain **Meshy text-to-3D are all RETIRED as the default path** — do not call or offer them for a normal new-asset request. The **one and only pipeline is now**: (a) generate a reference image via the `gemini_generate` MCP tool (batch multiple items into one contact sheet where possible, per the batching rule in `ITEM_ICON_STYLE_GUIDE.md`), (b) crop the sheet into one image per item, (c) feed each crop into **Meshy image-to-3D** with `ai_model='meshy-t2'`, `model_type='smart-topology'`, `should_texture=true`. **`model_type='smart-topology'` (meshy-t2) is now MANDATORY, ALWAYS — never `'lowpoly'` or `'standard'`** (this reverses the old lowpoly-only rule). (d) Scale the downloaded GLB to a realistic real-world height and ground its pivot (`Y_min=0`) via a headless Blender script (import → uniform scale → recenter/drop to ground → `transform_apply` → re-export GLB) — do this for every new model, matching realistic sizes already established elsewhere in the catalog. (e) The icon is still **rendered from the finished model** with `tools/render_icon_from_model.py` — that step is unchanged. Always confirm the credit cost against `GET /api/meshy-balance` (or `meshy_check_balance`) and get explicit approval before spending (see `PAID_ITEM_PIPELINE` in `tools/watch_asset_requests.py`).
> 3. **Retired Helper Library**: `tools/free_generator.py` is **dead code — do not use it**. `tools/meshy_client.py`'s `create_text_to_3d()` is no longer the default entry point; `create_image_to_3d()` (updated for `meshy-t2`/`smart-topology`) is.
> 4. **Detailed Reference**: See [MESHY_PIPELINE_GUIDE.md](file:///C:/Users/casey/Desktop/Homesteader/docs/MESHY_PIPELINE_GUIDE.md) and [UNITY_INTEGRATION_GUIDE.md](file:///C:/Users/casey/Desktop/Homesteader/docs/UNITY_INTEGRATION_GUIDE.md). **Known open issue**: models built this way may render with fragmented/jagged-looking shading on curved organic surfaces (e.g. animal faces) specifically in Unity/glTFast at runtime, even though the source GLB, its normals, and Blender's own render are all clean — root cause not yet confirmed (leading theory: texture compression across meshy-t2's small UV islands). Check for this after generating and report findings rather than assuming it's fixed.

---

## 1. Engine Specifications: Unity 6

- **Engine Version**: Unity 6 (`6000.6.0f1`).
- **Scale Standard**: **1 Unit = 1 Meter** (unlike Unreal which was 1 Unit = 1 cm). When exporting from Blender, scale to metric meters.
- **3D Model Format**: **GLB is the default and standard model format** (`.glb`, textures embedded). Mods load GLB at runtime via glTFast with no editor import or prefab step. FBX is kept ONLY for rigged/animated models (Humanoid/Generic animation); OBJ is legacy and is being retired. Convert with `tools/convert_models_to_glb.py`.
- **No foot skating**: every rigged model with walk / run clips must have its gait matched to the game's movement speed. Measure with `python tools/gait_fix.py measure <glb>`; if playback would need to exceed ~1.3x to match, lengthen the stride with `gait_fix.py stretch --target <m/s>` (keeps a backup). Then set the native speed: `GlbClipPlayer.walkNativeSpeed` / `runNativeSpeed` (player) or `movement.walk_native_mps` / `run_native_mps` in the animal AI. Do this on import, not after the user notices.
- **Save game**: the game autosaves and resumes (`Assets/Scripts/Save/`, `docs/SAVE_GAME.md`, F9 saves now). Anything new that changes the world or player state (new placeable things, inventory-like state, world objects) must be added to `GameSave` / `GameSaveManager.Capture()` / `ApplySave()` in the same change.
- **NO EMOJI (user rule)**: never use emoji anywhere: not in chat replies, not in UI text, labels, toasts, docs, commit messages or code comments. Plain text only.
- **Poly budget**: keep every asset model **under 5,000 triangles** (the user's standard). Check the count after any Meshy generation (`meshy-t2` image-to-3D lands around 4,000-4,400) and decimate anything over.
- **Coordinate System**: Left-handed ($Y$-Up, $+Z$-Forward, $+X$-Right).
- **Pivots**: Ground-level pivot ($Z_{min} = 0$, $Y_{min} = 0$ in Unity) for structures, furniture, and placed crops; centered pivot for handheld tools and items.
- **2D UI / Icons**: 128×128 px 32-bit RGBA PNG, imported in Unity as `Texture Type: Sprite (2D and UI)`.
- **Character / Rigging**:
  - Humanoids / Bipeds: Use the Blender Mixamo Addon (`bl_ext.blender_org.mixamo_rig`). Set Unity Animation Type to **Humanoid**; Unity Mecanim auto-maps bones with 100% fidelity.
  - Quadrupeds / Animals: Standard quadruped skeleton or Animal Animator (`bl_ext.blender_org.animal_animator`). Set Unity Animation Type to **Generic**.

---

## 1a. UI Design Rules (UI Toolkit)

- **Text fields** (TextField, number fields, search boxes, dropdowns): text is ALWAYS vertically centered in the box, including placeholder text. Style the inner input, not just the outer element: justify-content: center; -unity-text-align: middle-left; padding-top: 0; padding-bottom: 0; on .unity-base-text-field__input / .unity-base-popup-field__input, and zero margin/padding on the inner TextElement. Horizontal alignment stays left.
- **Toasts**: a toast identical to the NEWEST one still showing (same title, message and kind) never stacks: the one on screen just restarts its timer. Repeats that carry a number use `ToastNotificationSystem.ShowCounted` (one toast, running total). Never fire the same toast several times.
- **Buttons**: label text is ALWAYS centered vertically AND horizontally (-unity-text-align: middle-center).
- Reference implementations: .asset-search-input and .asset-category-dropdown in Resources/HUDTree/HudUI.uss.
- **There is ONE phone.** Its markup is `Homesteader/Assets/Resources/HUDTree/PhoneUI.uxml` and its styles are `PhoneUI.uss` (apps such as Steadify, Volt, Almanac are all in that one uxml). `HudUI.uxml` only instantiates it (`<ui:Instance template="PhoneUI" name="PhoneHost" />`), and `Scripts/UI/Phone/PhoneController.cs` drives it. Never add phone markup to `HudUI.uxml` and never keep a second copy. A horizontal `Slider` needs an explicit height and `.unity-base-slider__drag-container` / tracker / dragger styling (see `.admin-slider` and `.steadify-seek-slider`), or it collapses to zero height and is invisible.

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

## 2. Asset Generation Pipeline (Reference image + Meshy image-to-3D - the only pipeline)

**There is no free generation pipeline any more — everything costs money.** `tools/free_generator.py`, FLUX.1 [schnell], Tencent Hunyuan3D-2.0 and Creative Claw concept images are all **RETIRED**. Do not call them, do not offer them, do not write new code against them. Plain Meshy **text**-to-3D is also no longer the default path (see below).

The one and only pipeline is **reference image -> Meshy image-to-3D**:

1. Generate a reference photo/render of the subject with the `gemini_generate` MCP tool. Batch multiple related items (e.g. every stage of a growth group) into a single contact-sheet prompt where possible, per the batching rule in `docs/ITEM_ICON_STYLE_GUIDE.md`.
2. Crop the sheet into one image per item (`PIL.Image.crop`).
3. Feed each crop to Meshy image-to-3D via `tools/meshy_client.py` -> `create_image_to_3d()`, with `ai_model='meshy-t2'`, `model_type='smart-topology'`, `should_texture=True`. This returns the **model and its texture in a single task**.
4. Scale the downloaded GLB to a realistic real-world height and drop its pivot to the ground (`Y_min=0`) with a headless Blender script (import -> uniform-scale an empty parent to the target height -> recenter XY and drop to Y=0 -> `transform_apply` -> re-export GLB). Match realistic sizes already used elsewhere in the same category.
5. Render the icon from the scaled model exactly as before (unchanged, see (B) below).

**The user's prompt is the input.** A request carries a `PROMPT='...'` marker written by the user. Fold it into the Gemini reference-image prompt **as-is** — never rewrite, replace or paraphrase the user's intent — then append the standing technical rules below.

**`model_type='smart-topology'` (`ai_model='meshy-t2'`) IS MANDATORY, ALWAYS, NO EXCEPTIONS** on every image-to-3D generation. Never `'lowpoly'`, never `'standard'`. (This reverses the old lowpoly-only rule from the text-to-3D era.)

### (A) 3D Model + Texture generation (paid)

```python
import sys
sys.path.append(r"C:\Users\casey\Desktop\Homesteader\tools")
import meshy_client as mc

# 1. Reference image via the gemini_generate MCP tool (batched sheet, then crop
#    with PIL to one image per item) - not shown here, see gemini_generate's own tool docs.
# 2. Image-to-3D from the cropped reference:
preview_id = mc.create_image_to_3d(cropped_image_path, ai_model="meshy-t2", model_type="smart-topology", should_texture=True)
# then poll get_task('image-to-3d', preview_id) and download the GLB.
# 3. Scale + ground the GLB via a headless Blender script (see docs/MESHY_PIPELINE_GUIDE.md
#    for the exact script), then render the icon per (B) below.
```

- Confirm the credit cost and resulting balance against `GET /api/meshy-balance` **before** spending, and wait for explicit approval.
- Download the **GLB** (the project's model format, textures embedded).
- **Known open issue**: this method can produce fragmented/jagged-looking shading on curved organic surfaces (e.g. an animal's face) specifically when viewed in Unity/glTFast at runtime — not visible in the raw GLB data, its normals, or Blender's own render. Root cause unconfirmed (leading theory: texture compression artifacts across meshy-t2's many small UV islands). Flag this to the user after generating rather than assuming it's resolved.

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

- The canonical categories: `farming`, `ranching`, `logging`, `fishing`, `building`, `structures`, `tools`, `electricity`, `water`, `waste`, `internet`, `hud`, `ground`, `food`, `fuel`, `materials`, `ingredients`, `liquids`.
- Naming prefixes:
  - `struct_*`: cabins, barns, sheds, coops.
  - `machinery_*`: tractors, skidsteers.
  - `tool_*`: axes, hoes, hammers, wrenches.
  - `animal_*`: `animal_chicken_*`, `animal_cow_*`, `animal_fish_*`.
  - `fishing_*`: rods, lures, nets, tackle.
  - `seed_*`: plantable seeds (all use 3D seed packet models).
  - `crop_*`: growing crops.
  - `food_*`: direct edible harvests (e.g. `food_apple`, `food_truffle`).
  - `liquid_*`: fluids that fill liquid containers by volume (`weight_kg` is per litre; fluid colour and opacity). No model.
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

## 3a. Structure Model Rules

Building models follow [STRUCTURE_STAGES_GUIDE.md](file:///C:/Users/casey/Desktop/Homesteader/docs/STRUCTURE_STAGES_GUIDE.md): **a chimney stands against an EXTERIOR wall, never inside a room**;
the door is 1.2 m by 2.3 m; walls reach the roof with no gap; layers meeting at a corner never share a coplanar outer face; parts are
named objects (Foundation, Roof, Wall_*, WindowGlass, DoorHinge) and named materials (Log, Siding, Roof, Shingle, Interior, Floor, Masonry).

## 3b. Editor / Schema Sync Rule

- Whenever a field changes in the asset kit rich editor (`assets/index.html`), update the matching base schema / category schema (`assets/_schemas/`), server validation (`tools/server.py`), manifest templates (`tools/process_queued_batch.py`, `docs/ASSET_CREATION_GUIDE.md`, `assets/_schemas/README.md`) and backfill existing manifests in the same change. The reverse also applies: schema or template changes must be reflected in the rich editor.

---

- **Animal AI**: behaviour rules are mod data (`assets/_ai/*.json`, content type `animal_ai`). Schema `assets/_schemas/animal_ai.schema.json`, validator `tools/animal_ai.py` (must stay in step with `Assets/Scripts/Animals/AnimalAIDefinition.cs`), reference `docs/ANIMAL_AI.md`. An animal's own AI is `category_fields.ai` in its manifest (ranching schema, edited in the asset popup's Animal AI card, packaged to `ai/<item_id>.json`); `assets/_ai` holds shared/species profiles.

---

- **One source for items**: an item's name, price, icon, weight, shop listing (`properties.stores`, `sale_unit`, `base_value`) and everything else live ONLY in its manifest under `assets/<category>/<id>/`. The game's `AssetCatalog.json` and the phone shops are generated from the manifests (`tools/generate_unity_asset_catalog.py`, `tools/package_catalog_as_mods.py`); never keep a second hand-edited list of items (the old `StoreCatalogs.json` was one and went stale on renames).
- **Controls**: `docs/CONTROLS.md` is the single list of every key/mouse binding. Check it before assigning a key (F2, F3, F4 are taken) and update it AND the F1 hints list (`HintsPanel.cs`) in the same change whenever a binding is added, moved or removed.

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

---

## 5. Procedural World Rules (terrain dressing, road, camera)

Full list of what changed and why: `docs/PROCEDURAL_WORLD_CHANGES.md`. Plant and bridge code: `docs/PROCEDURAL_VEGETATION.md`.

- **World dressing is procedural, not Meshy.** Plants, rocks, debris and small props are built in code (`Assets/Scripts/World/`). Meshy image-to-3D stays for structures, tools, animals and anything that needs detail.
- **One shader.** Every procedural mesh uses `Homesteader/Vegetation` (wind sway, season growth and colour, tree age growth, snow, rain). Register seasonal materials with `Seasonal(...)` in `ProceduralVegetation.cs`.
- **No mass renderers.** Never leave tens of thousands of separate renderers in the world; scatter output is merged into 32 m chunk meshes (`ProceduralVegetation.Combine`).
- **Felling is decided by the asset kit.** A tree species' growth group (`growth.rules.yield.tool`, `item_id`, amounts) says what fells it (the ACTIVE toolbar item, right-click); `ForestTrees` reads it. Trunks and rocks are solid through a streamed collider pool on the Ignore Raycast layer, so mouse raycasts must use `Physics.DefaultRaycastLayers`, never `~0`.
- **Keep off the road and the water.** Anything scattered checks `IsNearRoad` and water. The owned-land fence (`ProceduralFence`) does the same: no fence over water, an opening where the road passes.
- **Tree growth follows the asset kit.** Four stages (sapling, small, medium, mature) at 16 / 35 / 65 / 100 percent height, windows read from the species' growth group. Nothing is saved: age comes from the seed and the game clock.
- **Maintained grass is player-made only.** World generation never produces `biome_maintained_grass`.
- **Starter zone, road and bridges are game rules as mod data** (`starter_zone`, `starter_road` in `gamerules.json`). Change the mod copy, `assets/_gamerules/`, `assets/_schemas/gamerules.schema.json` and `docs/MODDING_GUIDE.md` together (see 3b).
- **Camera:** orthographic, pulled back along its view direction so the near plane stays at 0.3. Never use a negative near plane (it skews shadow cascades and fog). Shadow distance is fitted to the zoom each frame; fog density is scaled by `IsometricLockedCamera.FogCompensation`.
- **Shaders:** `Mathf.SmoothStep(a, b, t)` is not GLSL `smoothstep(e0, e1, x)`; use `InverseLerp` first. The bog colour in the terrain shader is point sampled (a bilinear tint leaks the river's blue). The water edge may only recede from the smooth shoreline, never advance.
- **Testing in the editor:** one `GenerateTerrain()` per command (several froze Unity). To look at a change, render a temporary camera to a PNG in the scratchpad and read it.
