# Category schemas

Per-category field definitions on top of the base item manifest
(`$schema": "https://homesteader.game/schemas/item_v1.json"` -
id/name/category/description/icon/properties/models/utilities/growth/plugin_metadata,
already used by every item).

We're defining these incrementally, one category and one field at a time, as
real needs come up - not designing the whole thing up front. Each category
gets its own `<category>.schema.json` file here only once it actually has
fields worth enforcing; categories with no file yet just use the base schema.

## Format

Not full JSON Schema (no `jsonschema` dependency in this project) - a small
hand-rolled field-spec that `tools/validate_schema.py` reads directly:

```json
{
	"category": "appliances",
	"fields": {
		"<field name under the item's category_fields key>": {
			"type": "object | string | number | boolean",
			"required": true,
			"properties": { "...": "for type: object, nested field types" }
		}
	}
}
```

An item's manifest carries category-specific data under a top-level
`category_fields` key (separate from the base `properties` block, so we never
collide with the fixed base schema).

## Validating

```
py -3 tools/validate_schema.py appliances
```

Reports every item in `assets/appliances/*/*.json` that's missing a required
field or has a field of the wrong type. Exit code 0 = all items comply.

## Namespaces
An item's `id` is only unique **within its namespace**. Two sources can
legitimately produce the same id (`shed`, `tree_oak`) - a namespaced
`qualified_id` (`namespace:id`) is what registries key on, so they coexist
instead of clobbering each other.

- `namespace` - lowercase snake_case. Defaults to `core` for built-in content.
- `qualified_id` - `<namespace>:<id>`, written into the manifest for clarity.
- Mods declare theirs in `mod.json`; the mod's `id` is used unless the manifest
  asset sets an explicit `namespace`/`ns` field.

This mirrors the Unity side (`AssetManifestSummary.ns` / `.QualifiedId`), where a
colliding qualified id is rejected - first one wins - rather than overwritten.

## Categories defined so far

- `_base` - Base schema applied to EVERY item's `properties` block:
  - `base_value` (number >= 0, dollars)
  - `weight_kg` (number >= 0, kilograms)
  - `max_stack_size` (integer >= 1)
  - `is_consumable` (boolean)
  - `is_spawnable` (boolean, optional - defaults to `false` when omitted so older
    manifests stay valid). When `true`, the item is scattered into the world by
    terrain generation and must also declare a `spawning` block naming at least
    one target biome via `spawning.biomes[]`. When `false`/absent the item is
    data-only: craftable and placeable, but never auto-placed by the generator.
  - Player vitals: `happiness_modifier`, `thirst_restore`, `energy_restore`, `stamina_restore`, `wellness_modifier` (numbers between -100 and +100).
- `_base_dimensions` - `dimensions_m` (`width`, `depth`, `height` in meters) under `category_fields`.
- `appliances` - `dimensions_m` (width/depth/height in meters). Added
  2026-09-15 as the first field, since real-world footprint size was the
  original reason this whole schema system got proposed (a house has a
  finite amount of floor space).

## animal_ai.schema.json

Format of an animal AI definition (`assets/_ai/<id>.json`, mod content type `animal_ai`). It is not a category
schema: it describes a root-level data file, like `gamerules.schema.json`. `ranching.schema.json` gains the
optional `ai` object field (`editor: "animal_ai"`): the animal's own AI definition, edited in the Animal AI card of the asset popup and packaged to `ai/<item_id>.json`. Shared/species profiles live in `assets/_ai`. Validation lives in `tools/animal_ai.py`. See `docs/ANIMAL_AI.md`.

## light_emitter.schema.json

The optional top-level `lights` list on any asset manifest: each entry is a light the asset emits once placed in the
world (type point / spot, colour, intensity, range, position offset on the model, when it is on: always / night / hours,
fade, flicker, shadows, requires_power). Edited in the asset popup's **Lights** card; runtime is
`Assets/Scripts/Growth/LightEmitter.cs`; validated by `tools/light_emitter.py` on save.
