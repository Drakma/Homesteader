# Technical: How Data Is Stored

This is a reference for anyone working on the asset pipeline or the app's
server. It documents where every piece of state lives on disk, in what format,
and which process owns it.

## The core principle: disk is the source of truth

There is **no database**. The catalog is a folder tree, and every read rebuilds
from it. This was a deliberate replacement for an older design where a
`const ALL_ITEMS = [...]` snapshot was baked directly into `index.html` — a
snapshot that could (and did) drift out of sync with disk after a
create/edit/move/delete.

The current rule: **an item's manifest is the only authority on that item.**
Nothing caches identity, name, or model paths in a second place that could
disagree.

## Root layout

```
Homesteader/
├── assets/               # the catalog itself
│   ├── <category>/       # 17 built-in + user-added categories
│   │   └── <item_id>/
│   │       ├── <item_id>.json     # manifest — the authority
│   │       ├── <item_id>.png      # 128×128 icon
│   │       ├── SM_*.fbx           # one or more models
│   │       └── README.md
│   ├── _asset_requests/  # generation queue (see below)
│   ├── _schemas/         # category schemas + material tags
│   ├── _trash/           # soft-deleted assets
│   ├── _docs/            # markdown shown by the Docs button
│   ├── biomes/           # biome definitions
│   ├── kit_config.json   # categories, subfolders, growth groups
│   └── README.md         # generated master catalog index
└── tools/                # server + pipeline scripts
```

<blockquote>

**Why the underscore folders sit inside <code>assets/</code>:** they travel
with the catalog and are covered by the same backups. They're prefixed
<code>_</code> so they can't collide with a category, and the catalog walk only
visits <code>ALLOWED_CATEGORIES</code> — so anything under them is
automatically invisible without a denylist to maintain.

</blockquote>

## The item manifest

`assets/<category>/<item_id>/<item_id>.json`. **The filename must match the
folder name** — `build_catalog_entry()` looks for exactly
`{item_id}.json` and returns nothing if it's missing or unparseable.

```json
{
  "$schema": "https://homesteader.game/schemas/item_v1.json",
  "id": "crop_growing_corn",
  "name": "Corn (Growing)",
  "category": "farming",
  "description": "A growing stage corn plant.",
  "icon": "crop_growing_corn.png",
  "properties": { "weight_kg": 0.5, "max_stack_size": 1, "base_value": 0.0,
                  "is_consumable": false, "footprint": null,
                  "happiness_modifier": 4, "thirst_restore": 0,
                  "energy_restore": 0, "stamina_restore": 0,
                  "wellness_modifier": 0 },
  "models": [ { "file": "SM_Crop_Corn_Growing.fbx", "format": "fbx" } ],
  "utilities": { "water": {...}, "electricity": {...}, "sewage": {...},
                 "battery": {...}, "internet": {...} },
  "growth": { "is_growable": true, "growth_type": "plant", "species": "corn",
              "max_age": 80, "time_unit": "days", "total_stages": 3,
              "current_stage": {...}, "stages": [...] },
  "plugin_metadata": {...},
  "category_fields": { "crop_species": "corn", "days_to_mature": 90,
                       "dimensions_m": {...}, ... }
}
```

Fields worth knowing:

| Field | Notes |
| --- | --- |
| `id`, `category` | Must match the directory they live in |
| `icon` | A filename **relative to the item folder**, not a path |
| `models[].file` | Also folder-relative; the server prefixes `category/item_id/` when building catalog entries |
| `growth` | Optional; drives the growable badge and grouping |
| `utilities` | Optional; only meaningful for buildings/machines |

**A manifest with unreadable JSON is silently skipped** — not an error, just
"not a real item". A malformed manifest therefore looks like a missing asset,
which is worth remembering when debugging.

## kit_config.json

Everything the UI has *created* — as opposed to the built-in taxonomy, which is
hardcoded. Three top-level keys:

| Key | Holds |
| --- | --- |
| `categories` | User-added categories: `name`, `icon`, `desc`, `prefix` |
| `subfolders` | Species groups within a category: `name`, `icon`, `category` |
| `growth_groups` | Full lifecycle definitions: `growth_type`, `max_age`, `time_unit`, `stages[]` |

Each growth stage references a real item ID:

```json
{ "stage": 1, "name": "sprout", "item_id": "crop_sprout_corn",
  "age_min": 0, "age_max": 30 }
```

Because stages reference item IDs, **renaming an item requires rewriting every
growth group that points at it** — which is exactly what the rename handler does.

<blockquote>

**Legacy growth data still exists in two places.** Older manifests carry their
own hand-authored <code>growth.stages</code> (predating the Growth Groups UI).
At load time the frontend synthesizes a <code>GROWTH_GROUPS</code> entry from
that manifest data for any species that has no persisted group — and a
persisted group always wins. So the same lifecycle can be described in either
place, and the config file takes precedence.

</blockquote>

## The generation queue

`assets/_asset_requests/`, four subfolders by state:

| Folder | Meaning |
| --- | --- |
| `pending/` | Submitted, not yet batched |
| `in_progress/` | A session is working on it |
| `done/` | Finished |
| `batches/` | Finalized batches awaiting pickup |

<blockquote>

**State is the folder, not a field.** Moving a request between states means
moving its file. That makes progress inspectable with a plain directory listing
and means a crashed session can't leave a request in a state that contradicts
its location.

</blockquote>

Also in this folder: `watcher_heartbeat.json`, which the watcher writes so the
UI can tell whether it's actually running (stale after **15 seconds**), and an
`approvals/` subfolder.

## Trash

Soft-deleted assets: `assets/_trash/<category>__<item_id>/`.

The folder itself is moved here — manifest, icon, models and all — so a restore
is a byte-identical move back. A `.trashmeta.json` sidecar inside each entry
records the original location, timestamp, size, and reason:

```json
{ "category": "farming", "item_id": "crop_growing_corn",
  "trashed_at": 1770000.0, "reason": "deleted",
  "size_bytes": 48213, "original_path": "assets/farming/crop_growing_corn" }
```

The double underscore is the key detail: neither a category slug nor an item ID
can contain one (both are validated to `[a-z0-9_]`), so the folder name is
unambiguously splittable. If the sidecar is missing or corrupt, the name alone
is enough to restore — which is why the sidecar is treated as an optimization,
not the source of truth.

## Schemas and tags

`assets/_schemas/`:

- **Category schemas** — the field contract for a category: which keys are
  required, their types, and constraints (`min`/`max`).
- **`material_tags.json`** — recipe material tags: a tag name mapping to a list
  of real catalog item IDs.

## Biomes

`assets/biomes/*.json` — one file per biome, describing the environment and its
member assets.

## What's generated, not authored

| File | Produced by |
| --- | --- |
| `assets/README.md` | `tools/update_catalog_readme.py` — the master index |
| `assets/_asset_requests/batches/*.json` | `finalize_asset_requests()` |

Both are outputs. Editing them by hand is a mistake — the next run overwrites
them.

## Concurrency and write safety

The app is single-process and does no locking. Two saves landing at the same
moment can interleave. In practice this is safe because:

- Writes are performed by one server process, not many
- The catalog cache is in-process, so it's invalidated atomically
- Trash moves use `shutil.move` (an atomic rename within a filesystem)

The one genuinely non-atomic sequence is **trash-then-write-sidecar**: if the
process dies between the move and the sidecar write, the folder is in `_trash/`
untracked. It's recoverable (the name encodes the origin, and the UI surfaces
unrecognized folders rather than hiding them), but it's the known rough edge.
