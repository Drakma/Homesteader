# Homesteader Mod System

How mods are discovered, validated, and loaded into the game at startup.

---

## 1. Where mods live

On startup the game scans two locations:

| Location                    | Purpose                                                           |
| :-------------------------- | :---------------------------------------------------------------- |
| `<persistentDataPath>/Mods` | Player-installed mods. This is the main folder.                   |
| `<StreamingAssets>/Mods`    | Mods that ship **inside the build** (bundled content, tutorials). |

Each location can contain **either** a mod **folder** or a mod **`.zip` archive**:

```
Mods/
├── my_biome_mod/          <- folder mod
│   ├── mod.json
│   └── biomes/
│       └── biome_lavender_fields.json
├── autumn_pack.zip        <- archive mod
│   ├── mod.json
│   └── ...
└── _staging/              <- managed automatically; do not edit
```

### Folder vs. zip

- **Folder mods** are read in place — ideal while developing.
- **Zipped mods** are extracted into `Mods/_staging/<hash>/` on first load and
  reused on later runs (the folder name is a hash of the archive, so a changed
  zip is re-extracted automatically).
- A zip whose contents are all inside a **single top-level folder** works fine —
  the loader flattens it. So right-clicking a folder → _Send to → Compressed
  (zipped) folder_ produces a valid mod.
- Append `.disabled` to a folder or zip name to skip it without deleting it
  (`my_mod.disabled/`, `autumn_pack.zip.disabled`).

---

## 2. The manifest (`mod.json`)

Every mod has a `mod.json` at its root. This is the only file the loader requires.

```json
{
	"id": "lavender_homestead",
	"name": "Lavender Homestead",
	"version": "1.2.0",
	"author": "Casey",
	"date": "2026-09-15",
	"description": "Adds lavender fields, a lavender drying shed, and lavender tea.",

	"compatibility": { "min": "0.1.0" },
	"load_after": ["base_flower_pack"],
	"dependencies": [],

	"contents": [
		{ "type": "biome", "path": "biomes/lavender_fields.json" },
		{ "type": "structure", "path": "assets/structures", "group": "shed" },
		{ "type": "food", "path": "assets/food/tea_lavender.json" }
	]
}
```

### Field reference

| Field                        | Required | Notes                                                                |
| :--------------------------- | :------- | :------------------------------------------------------------------- |
| `id`                         | **yes**  | Unique, snake*case (`^[a-z0-9*]+$`). Used as the dependency key.     |
| `name`                       | no       | Display name. Defaults to `id`.                                      |
| `version`                    | no       | Any string; semver recommended. Defaults to `1.0.0`.                 |
| `author`                     | no       | Defaults to `Unknown`.                                               |
| `date`                       | no       | Release date, `YYYY-MM-DD`.                                          |
| `description`                | no       | Shown in the load report and mod UI.                                 |
| `homepage`                   | no       | Link back to the mod's page.                                         |
| `icon`                       | no       | Relative path to a preview image.                                    |
| `compatibility.min` / `.max` | no       | Supported game versions (accepts flat `game_version_min`/`max` too). |
| `dependencies`               | no       | Mod ids that must load **before** this one.                          |
| `load_after`                 | no       | Soft ordering — load after these ids if present.                     |
| `contents`                   | **yes**  | What the mod contributes. See below.                                 |
| `namespace` | no | Optional namespace for this mod's asset ids. Defaults to the mod `id`. |

### Shorthand form

A single-content-type mod may skip the `contents` array:

```json
{
	"id": "tiny_biome",
	"type": "biome",
	"path": "biomes"
}
```

---

## 3. Content entries

Each entry names a **type** and a **path** (relative to the mod root).

```json
{ "type": "biome", "path": "biomes/*.json", "group": "terrain" }
```

**`type`** is one of:

`structure`, `biome`, `food`, `ingredient`, `farming`, `ranching`, `logging`,
`fishing`, `tool`, `electricity`, `water`, `waste`, `internet`, `vehicle`,
`appliance`, `material`, `fuel`, `ped`, `texture`, `recipe`, `script`.

An **unknown type is not fatal** — it's logged as a warning and the entry is
skipped, so a mod built for a newer game version still loads everything else.

**`path`** accepts three forms:

| Form                  | Meaning                                             |
| :-------------------- | :-------------------------------------------------- |
| `biomes/river.json`   | One exact file.                                     |
| `biomes/*.json`       | Every `.json` directly in `biomes/`.                |
| `biomes` or `biomes/` | Every matching file under `biomes/`, **recursive**. |

Paths are confined to the mod folder. Anything that tries to escape it (`../`,
absolute paths) is rejected and logged.

**`group`** is a free-form subcategory hint for your own organization.

---

## 4. What each type does today

| Type            | Behavior in this build                                                                                                   |
| :-------------- | :----------------------------------------------------------------------------------------------------------------------- |
| `biome`         | Parsed into the game's `BiomeData` and **appended to the terrain generator**. Modded biomes participate in world baking. |
| Everything else | Parsed into `AssetManifestSummary` and appended to the generator's **asset registry**.                                   |
| `script`        | Indexed but **not executed** - reserved for a future code-loading layer.                                                 |

### Spawnable vs. data-only assets

An asset is **data-only unless it says otherwise**. It can always be crafted and
placed by the player; only a _spawnable_ asset is additionally scattered by world
generation.

```json
{
  "id": "food_tea_lavender",
  "category": "food",
  "properties": { "is_spawnable": false }
}
```

To make an asset spawn in the world, set `properties.is_spawnable` to `true`
**and** name the biomes it belongs in:

```json
{
  "id": "struct_lavender_drying_shed",
  "category": "structures",
  "properties": { "is_spawnable": true },
  "spawning": {
    "biomes": ["biome_lavender_fields", "biome_meadow"],
    "density_per_hectare": 0.4,
    "clustering": 0.6,
    "elevation_min_m": 0.0,
    "elevation_max_m": 40.0,
    "slope_max_deg": 15.0,
    "scale_min": 0.95,
    "scale_max": 1.05,
    "align_to_surface_normal": true
  }
}
```

The load rule is deliberate:

- `is_spawnable: true` with an **empty or missing `spawning.biomes`** is a
  contradiction. The asset loads, is reported as a warning, and is **not**
  placed - it never silently vanishes.
- `is_spawnable: false` (or omitted) means any `spawning` block is ignored.
- The Asset Kit exposes this as a **Spawnable in World** toggle plus a
  multi-select **Choose Biomes...** picker that writes `spawning.biomes[]` for you.

> **Prefab binding.** Assets are registered as data even when no 3D prefab can be
> resolved, so recipes and values still work. To make a modded asset actually
> _place_, an `IModAssetResolver` must supply its prefab (see section 7) **and**
> the asset must be spawnable with at least one biome.

---

## 4b. Namespaces

A bare `id` is only unique **within a namespace**, because two mods can each ship
something called `tree_oak`. Every registered asset therefore carries a
namespace, and the registry keys on the combined **qualified id**:

```
qualified_id = "<namespace>:<id>"
```

- A mod's namespace **defaults to its `mod.json` `id`**.
- An asset may override it with an explicit `namespace` (or `ns`) field - useful
  when several mods should share one brand's namespace.
- Built-in content is `core`.

So `lavender_homestead:tree_oak` and `autumn_pack:tree_oak` coexist instead of
one replacing the other. If two assets resolve to the _same_ qualified id, the
first registered wins and the duplicate is reported - never silently overwritten.

```json
{
  "id": "struct_lavender_drying_shed",
  "namespace": "lavender_homestead",
  "qualified_id": "lavender_homestead:struct_lavender_drying_shed"
}
```

Both fields are optional: omit them and the mod id is used automatically.

---

## 4c. Growth groups and stage resources
A growth group owns its lifecycle once, in its own manifest, with each stage's
files under `stages/<stage_folder>/`:

```
assets/<category>/<group>/<group>.json      <- the scheme (authoritative)
assets/<category>/<group>/stages/<folder>/  <- that stage's resources
```

Each `stages[]` entry names its own resources explicitly:

```json
{
  "stage": 2,
  "name": "framing",
  "age_min": 33,
  "age_max": 66,
  "resource": "stages/struct_framing/",
  "model": "my_house_frame.fbx",
  "icon": "framing_icon.png"
}
```

**Resource filenames and folder names are the author's choice, not a
convention.** There is no required prefix such as `SM_`, no required suffix, and
no rule tying the model's name to the icon's name or to the stage's `name`. Call
them whatever makes sense in your mod. Nothing validates the *names*.

The only contract is **resolution**: `resource` + `model` must name a real file
inside your group folder, and `resource` + `icon` must name a real image. The
group is identified by `resource` and `model` together, looked up relative to
`<category>/<group>/`, so two groups can each ship a differently-named mesh for
the same stage without colliding. Namespaces (§4b) likewise keep two mods'
groups apart.

Stage folders are **resources, not catalog assets** - the catalog skips the
`stages` directory, so a stage is never a standalone item and `ALL_ITEMS` will
not contain one. Read a stage's `model`/`icon` from the group manifest's
`stages[]` entries, never by looking an id up in the catalog.

---

## 4d. Planting and harvesting: the group owns its lifecycle

A mod can ship plantable trees and crops entirely as data, and the **growth group owns everything
about its lifecycle** (nothing about it lives on the seed or sapling item):

| Rule in `growth.rules` | Meaning |
| :--- | :--- |
| `planting.item_id` | The item that plants it (seed / sapling). One item plants one group. |
| `yield.item_id` / `yield.amount_min`..`amount_max` | The ingredient dropped when harvested, and how many: a random whole number from min to max, inclusive. |
| `yield.tool` | What harvests it: empty = by hand, an item id, or a `#tag`. |
| `failure.withered` (crops) / `yield.stump` (trees) / `failure.dead` | The withered version (crops only), the stump left after a tree is harvested (trees only), and the dead version. Each is `resource` + `model`, like a stage. |
| `planting.seasons/biomes`, temperature, `needs`, `failure` | Where and when it grows and what stops it. |

See `assets/_schemas/growth_group.schema.json`. The loader registers each group in `GrowthRegistry`
and resolves every stage, withered and dead prefab from that folder's own manifest
(`prefabs/<manifest id>.prefab`).

**Planting.** With the planting item as the active toolbar slot, a right-*click* on the ground (a
right-drag still pans the camera) checks the spot and plants stage 1 on the centre of that grid
square, consuming one item. A spot is rejected, with a message saying why, when it is: not ground,
too steep, not in the squares right next to the player, water, outside the group's `planting.biomes`,
outside its `planting.seasons`, outside its temperature range, or already occupied. Plants advance
through their stages as game days pass, pausing while the season/temperature rules forbid growth.

**Failure.** Out of season with `out_of_season: "wither"` the plant shows its withered version until
conditions return (crops only). Frost (`frost_kills`) or `out_of_season: "die"` kills it: the dead version stays
in the world for good, or the plant is removed if the group has none.

**Harvesting.** A ready, living plant (at `yield.harvest_stage`, the last stage by default) is
harvested by right-clicking its square (the player's own square or the eight around it). `yield.tool`
must be the active toolbar slot when set; a tag (`#sickle`) is satisfied by any member of that tag in
`tags.json`. The `yield.item_id` goes to the toolbar; perennials (`yield.regrows`) drop back to
`regrow_stage`. A harvested tree with a `yield.stump` becomes that stump for good; anything else is removed. A mod ships its tag registry as `tags.json` at the mod
root (`{"tags": {"sickle": ["tool_sickle"]}}`), union-merged across mods.

Requires the stage models to be imported as prefabs: run **Homesteader > Mods > Generate Mod Prefabs**
after syncing the mod into Unity. A group whose stage 1 has no prefab reports that instead of planting.

---

## 4e. Game rules as mod data

The constants behind planting and harvesting are **data in a mod**, not code. A mod lists a
`gamerules` content entry and ships a `gamerules.json`; the game's built-in numbers are only
the defaults for anything the file leaves out.

```json
{ "contents": [ { "type": "gamerules", "path": "gamerules.json" } ] }
```

```json
{
  "planting": { "grid_size_m": 1.0, "reach_cells": 1, "max_slope_deg": 25,
                "crop_spacing_m": 0.5, "tree_spacing_m": 2.0,
                "water_biomes": ["biome_pond", "biome_river", "biome_lake"] },
  "harvest":  { "reach_cells": 1 },
  "zones": [ { "id": "starter_farmland", "biome": "biome_farmland", "center": [0, 8],
               "size": [10, 10], "texture": "textures/farmland_grid.png",
               "tile_m": 1.0, "height_offset_m": 0.005 } ]
}
```

- **Rules:** grid size, reach (in squares), steepest plantable slope, plant spacing, and the biomes
  that can never be planted in.
- **Zones:** rectangular patches of ground that count as a biome (e.g. farmland) on flat-ground
  worlds. The game builds a flat textured quad for each one when the mod loads, so a mod supplies
  its own farmland plots and their texture.
- **Merge:** mods apply in load order; a later mod overrides individual keys, a list value replaces
  the whole list, and a zone with the same `id` replaces the earlier one.

The source lives in `assets/_gamerules/` (packaged as the `mod_gamerules` mod by
`tools/package_catalog_as_mods.py`). Reference: `assets/_schemas/gamerules.schema.json`.

---

## 5. Biome files

Biome JSON mirrors `assets/biomes/*.json` exactly:

```json
{
	"id": "biome_lavender_fields",
	"name": "Lavender Fields",
	"priority": 7,
	"description": "Purple flowering meadows on gentle slopes.",
	"color_hex": "#8b5cf6",
	"moisture": 0.45,
	"nutrients": 0.7,
	"noise": {
		"frequency": 0.012,
		"octaves": 3,
		"persistence": 0.5,
		"threshold": 0.55,
		"dither_bandwidth": 0.04
	},
	"elevation": {
		"base_offset_m": 1.0,
		"noise_amplitude_m": 2.0,
		"noise_frequency": 0.011,
		"max_slope_deg": 18.0
	},
	"generative_ground": {
		"shader_mode": "standard_dither",
		"primary_color_hex": "#7e22ce",
		"secondary_color_hex": "#c084fc",
		"slope_color_hex": "#a8a29e",
		"pattern_scale": 1.0,
		"pattern_intensity": 0.5,
		"normal_micro_roughness": 0.2
	}
}
```

Rules enforced by the loader:

- `id` is **required** and **must start with `biome_`**.
- `color_hex` must be a `#rrggbb` string.
- Out-of-range values are clamped (`octaves` → 1–8); missing fields fall back to defaults.
- **An id that already exists in the base game is rejected**, not overwritten.
  Core content always wins; new biomes are additive only.

---

## 6. Load order

Order is resolved automatically:

1. **Dependencies first** (`dependencies`), recursively.
2. **Then `load_after`** hints.
3. **Then alphabetical by `id`** for a stable, reproducible result.

Missing dependencies and cycles are logged as warnings and never block loading.
Duplicate `id`s: the first mod wins, the rest are flagged.

Because mods load before terrain generation, modded biomes are baked into the
world. `ModManager.generateTerrainAfterLoad` controls this (on by default).

---

## 7. Scripting interface

The system is split so you can extend it without touching the loader:

| Class               | Role                                                                             |
| :------------------ | :------------------------------------------------------------------------------- |
| `ModJson`           | Dependency-free JSON reader (arbitrary shapes, no `JsonUtility` limits).         |
| `ModManifestParser` | `mod.json` → `ModManifest`, with validation.                                     |
| `ModDiscovery`      | Scans folders + zips, extracts archives, resolves load order.                    |
| `ModFileResolver`   | Path/wildcard expansion, sandboxed to the mod folder.                            |
| `ModLoader`         | Applies content into game registries. Merge rules live here only.                |
| `ModManager`        | MonoBehaviour bootstrapper. Exposes `LoadedMods`, `Results`, `ModsLoaded` event. |

### Supplying prefabs

Implement `IModAssetResolver` and assign it to `ModManager.assetResolverBehaviour`:

```csharp
public class MyAssetResolver : MonoBehaviour, IModAssetResolver
{
    public bool TryResolvePrefab(ModInfo mod, ModJsonValue manifest, out GameObject prefab)
    {
        prefab = null;
        string modelPath = manifest["models"]?[0]?["file"].AsString();
        if (modelPath == null) return false;

        // Load from Addressables, an AssetBundle, or import the OBJ/GLB at runtime...
        prefab = Addressables.LoadAssetAsync<GameObject>(mod.Manifest.Id + "/" + modelPath).WaitForCompletion();
        return prefab != null;
    }
}
```

### Reading API

```csharp
var manager = ModManager.Instance;
foreach (var mod in manager.LoadedMods)
    Debug.Log(mod.Manifest);              // id v version (author)

foreach (var mod in manager.ModsProviding("biome"))
    Debug.Log($"{mod.Id} adds biomes");

Debug.Log($"{manager.ModdedBiomeCount} biomes came from mods");
```

---

## 8. Startup checklist

1. Add a `ModManager` to a boot-scene GameObject.
2. Leave `terrainGenerator` empty (it auto-finds one) or assign it explicitly.
3. Set `modsDirectoryOverride` only if you want a non-default location.
4. Press play — the console logs a full report, and `modload_report.txt` is
   written beside the mods folder.

### Defaults

| Setting                      | Default |
| :--------------------------- | :------ |
| `loadOnStartup`              | `true`  |
| `generateTerrainAfterLoad`   | `true`  |
| `includeStreamingAssetsMods` | `true`  |
| `writeReportFile`            | `true`  |
| `verboseLogging`             | `true`  |

---

## 9. Authoring checklist

- [ ] `mod.json` at the root (not nested one level deeper, unless inside a zip).
- [ ] Unique snake_case `id`.
- [ ] Every `contents` entry has a valid `type` and a `path` that exists.
- [ ] Biome ids start with `biome_` and don't collide with core biomes.
- [ ] Test by dropping the folder in `Mods/` and checking `modload_report.txt`.
