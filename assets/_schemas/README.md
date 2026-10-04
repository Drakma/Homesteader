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

## radio_station.schema.json

Format of a Steadify radio station (`assets/_radio/<id>.json`, mod content type `radio`). A root-level data file like
`animal_ai.schema.json`: speakers (name, voice id, style), the segment order, the sentence banks the almanac script
writer fills from the day's facts, and the persona given to the Claude script writer. Packaged to `radio/<id>.json` by
`tools/package_catalog_as_mods.py`. See `docs/RADIO.md`.

## light_emitter.schema.json

The optional top-level `lights` list on any asset manifest: each entry is a light the asset emits once placed in the
world (type point / spot, colour, intensity, range, position offset on the model, when it is on: always / night / hours,
fade, flicker, shadows, requires_power). Edited in the asset popup's **Lights** card; runtime is
`Assets/Scripts/Growth/LightEmitter.cs`; validated by `tools/light_emitter.py` on save.

## Component (add-on) schemas

A component schema is its own schema file with `"component": true`. It is not part of the base schema or a category: it is ADDED to an individual
asset (the asset popup's "Add schema" button) and lives in its own top-level block on the manifest, named by the schema's `target`. The block is
validated only on assets that have it. `on_add` lists manifest values set when the schema is added.

- `liquids` (`liquids.schema.json`, category_fields): a fluid that fills liquid containers by volume (category `liquids`, ids `liquid_*`, no model).
  - `properties.weight_kg` is kilograms PER LITRE (water 1.0, diesel 0.83); a container weighs its own weight plus litres x this.
  - `color` (string `#RRGGBB`, required, shown as a colour swatch in the editor): the fluid colour.
  - `opacity_pct` (number 0 to 100, required): 100 = fully opaque (milk), about 70 for fuels, about 35 for water.
  - `flammable` (boolean, optional).
  - `dimensions_m` is one litre (a 10 cm cube). Tags `#liquid`, `#liquid_fuel`, `#liquid_dairy`, `#liquid_oil` are in `material_tags.json`. Generator: `tools/make_liquid_assets.py`.
- `liquid_container` (`liquid_container.schema.json`, component, target `liquid_container`): the asset holds ONE liquid at a time by volume.
  - `capacity_l` (number > 0, required): the most litres it holds.
  - `accepts` (array, optional): liquid assets and/or `#liquid...` tags chosen with the asset picker; empty = any liquid.
  - `on_add`: sets `properties.max_stack_size` to 1. Separate from `container` (solid items by weight). Runtime: `Assets/Scripts/UI/Liquids.cs` (`LiquidRules`).
- Shop listing (base `properties`, set in the asset popup under **Sold At**): `stores` (the phone shops that sell it: depot, lumber, grocer, feed,
  water, vehicles, equipment, livestock, furniture, voltvision, trailershack), `sale_unit` (ea, kit, box ...), optional `store_category`
  (the shop's chip label when it differs from the asset category default) and `store_overrides` (`{"shop": {"category", "unit", "price"}}`
  for one shop that sells it differently). The price is `base_value`. There is NO separate store file: the phone builds every shop from
  `AssetCatalog.json`, which `tools/generate_unity_asset_catalog.py` writes from the manifests (`store_listings`).
- `container` (`container.schema.json`, target `container`): the asset holds other items up to a weight.
  - `capacity_kg` (number > 0, required): the most weight it can hold (sum of weight_kg x count inside).
  - `stacking_limit` (integer >= 1, optional): identical placed containers can be stacked this high in one grid square in the world; omitted or 1 = no stacking.
  - `disposable` (boolean, optional, default false): a PLACED container is removed from the world when its last item is taken out (cardboard delivery boxes); crates and baskets leave it off.
  - `show_fill` (boolean, optional, default true): a PLACED container draws what is inside as blocks that rise as it fills (one slab per kind of item: average colour on the sides, icon on top; `Assets/Scripts/Growth/ContainerFill.cs`). Set false for closed boxes.
  - `single_type` (boolean, optional, default false): takes only one kind of item at a time; once it holds something only more of that item goes in (crates).
  - `accepts` (array, optional): tags (`#tag`) and/or exact asset ids chosen with the asset picker; empty = anything.
  - `on_add`: sets `properties.max_stack_size` to 1 (a container carries its own contents, so it is one per toolbar slot).

- `attach_surface` / `attach_side` / `provides_power` (base properties): an item that mounts on a finished building's wall or ceiling (a breaker box, sconces, ceiling lights); see docs/ATTACHED_ITEMS.md.

- `look_target` / `look_color` / `look_smoothness` / `look_metallic` (base properties): a construction material that sets how a building looks (roof or walls colour and sheen); see docs/CONSTRUCTION.md "Look follows the materials".
