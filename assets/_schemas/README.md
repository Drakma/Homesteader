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

## The base schemas (`_base*.schema.json`)

Every item's `properties` block is checked against ALL the `_base*.schema.json` files together (the server's validator and
`tools/validate_schema.py` load every file with that prefix). The base used to be one file of 74 fields; it is now split by topic so a
field is easy to find, and so each topic has one place to describe itself. The manifest layout did NOT change: every field is still
`properties.<field>`, and a field's definition is identical to what it was. Add a new base field to the file whose topic fits it; make a new
`_base_<topic>.schema.json` (`"target": "properties"`, a `title` and a `note`) only for a genuinely new topic. The schema editor lists them
all under **Universal**.

| File | Fields | What it covers |
|---|---|---|
| `_base` | `base_value`, `weight_kg`, `max_stack_size`, `pack_quantity`, `display_weight`, `is_consumable`, `is_spawnable`, `is_buyable`, `is_sellable` | The core of every item: economy, weight, stacking and how its name is shown |
| `_base_vitals` | `happiness_modifier`, `thirst_restore`, `energy_restore`, `stamina_restore`, `wellness_modifier` | What eating, drinking or using it does to the player |
| `_base_store` | `stores`, `sale_unit`, `store_category`, `store_overrides` | The shop listing (the phone shops are generated from it) |
| `_base_placement` | `placeable`, `stacking_limit`, `support_surface`, `deck_heights`, `shelf`, `pushable`, `is_blueprint`, `builds_structure` | How it stands in the world, stacks, carries things; kit and blueprint flags |
| `_base_mounting` | `attach_surface`, `attach_side`, `attach_through`, `attach_item`, `attach_result`, `roof_mount`, `provides_power`, `panel_*` | Items that mount on a building; solar panel geometry |
| `_base_wiring` | `wire_role`, `wire_kind`, `wire_length_m`, `power_radius_tiles`, `capacity_wh`, `voltage_v` | The electrical system |
| `_base_water` | `flow_lph`, `pressurized`, `heater_w`, `filter_stage`, `is_well`, `sewage_capacity_l`, `leach_lpd`, `leach_storage_l` | Pumps, filters, heaters, wells, septic |
| `_base_network` | `net_ports`, `poe`, `poe_powered`, `rack_units`, `rack_capacity_u` | Networking gear and racks |
| `_base_building_look` | `look_target`, `look_color`, `look_smoothness`, `look_metallic`, `look_style` | How a construction material changes a building's look |
| `_base_fences_paths` | `fence_*`, `gate_*`, `path_*` | Fences, gates, paths and roads |
| `_base_tools_fuel` | `build_speed`, `burn_minutes`, `lights_fires`, `sawmill` | Tool speed, fuel burn and fire lighting |
| `_base_dimensions` | `dimensions_m` (`width`, `depth`, `height` in metres) | Under `category_fields`, not `properties` |

Field notes worth keeping (the field's own `note` in its schema file has the rest):
- `base_value` (number >= 0, dollars), `weight_kg` (kilograms), `max_stack_size` (integer >= 1): required on every item.
- `build_speed` (number >= 0.1, optional, tools): 1 = the baseline 30 s per stage, 0.5 = twice as long (a hammer, a hand saw), 2 = twice as fast. Each tool group counts its fastest tool at the site; a stage takes as long as its slowest group.
- `pack_quantity` (number >= 1, optional): a stack / pallet / case / bundle of N items. The SHOWN name is generated, `Name xN` then the weight when shown (`Name x10 (200 kg)`); the stored name stays plain (`Cement Bag Pallet`).
- `display_weight` (boolean, optional): materials and packaged goods show `Name (9 kg)` (or lb), generated from `weight_kg` through `UnitFormat`. Never put a weight, measurement or count in the stored name (`tools/migrate_item_names.py` moved the existing ones out). Shown names come from `HudBindings.GetDisplayName`: store lists, the active slot, WAILA and the construction lists.
- `is_spawnable` (boolean, optional, default `false`): when `true` the item is scattered into the world by terrain generation and must also declare a `spawning` block naming at least one target biome via `spawning.biomes[]`.
- `is_buyable` / `is_sellable` (booleans, optional): added to the schema 2026-10-05 (they were on nearly every manifest but undeclared).
- Player vitals: numbers between -100 and +100.

### Known overlaps (candidates for a later clean-up, not changed yet)

These are real duplications, left alone because moving data changes manifests and the game's catalog export:
- `fuel_type`, `fuel_consumption_l_per_min`, `tank_capacity_l`, `power_draw_w` and `is_connected` are re-declared in several category schemas (appliances, electricity, tools, vehicles, waste, water, internet) with slightly different required/optional rules. A shared "field set" mechanism that categories can include would remove them.
- `fertilizer_growth_bonus_pct` is in both `materials` and `waste`.
- `pushable` and `stacking_limit` exist in `_base_placement` AND in the `container` component. The export writes both to the same catalog field (`container_stacking_limit`), so the game cannot tell them apart; pick one home.
- `validate_schema.py` skips growth groups (as the server does) but does not check component schemas (container, liquid_container, fruiting); only the server's validation does.
- Existing data that fails today's schemas (run `py -3 tools/validate_schema.py <category>`): food and materials items missing `dimensions_m`, structures that are blueprints without `dimensions_m` or the five vitals, and a few water / waste items missing power or capacity fields.

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
  - `properties.weight_kg` is kilograms PER LITRE (water 1.0, diesel 0.83); a container weighs its own weight plus liters x this.
  - `color` (string `#RRGGBB`, required, shown as a colour swatch in the editor): the fluid colour.
  - `opacity_pct` (number 0 to 100, required): 100 = fully opaque (milk), about 70 for fuels, about 35 for water.
  - `flammable` (boolean, optional).
  - `dimensions_m` is one liter (a 10 cm cube). Tags `#liquid`, `#liquid_fuel`, `#liquid_dairy`, `#liquid_oil` are in `material_tags.json`. Generator: `tools/make_liquid_assets.py`.
- Placed stacking (base `properties.stacking_limit`, integer, optional): how many identical placed items stack on each other in one grid square (the building
  bags: 4). Needs `placeable`. A container uses `container.stacking_limit` instead. Both are exported to the game as `container_stacking_limit`
  (`ContainerRules.StackingLimit`), so no game code distinguishes them.
- `liquid_container` (`liquid_container.schema.json`, component, target `liquid_container`): the asset holds ONE liquid at a time by volume.
  - `capacity_l` (number > 0, required): the most liters it holds.
  - `accepts` (array, optional): liquid assets and/or `#liquid...` tags chosen with the asset picker; empty = any liquid.
  - `filled_with` (string, optional) and `filled_l` (number, optional): a container that is sold full names the liquid asset it holds when bought and how many liters
    (the 1 L and 5 L water jugs, `tools/make_water_jugs.py`). Exported to the game catalog as `liquid_filled_with` / `liquid_filled_l`; the game does not track a
    container's contents yet, so nothing reads them at runtime so far.
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
  - `fill_x_min` / `fill_x_max` / `fill_y_min` / `fill_y_max` / `fill_z_min` / `fill_z_max` (numbers 0-1, optional): where the visible contents sit, as fractions of the model's overall bounds (x = length, y = height, z = width). Omit for a plain open box; set them when the opening is only part of the model (a wheelbarrow tub). Catalog: `container_fill_region`.
  - `pushable` (boolean, optional, default false): a push item (a wheelbarrow): a placed one is grabbed and pushed with right click rather than picked up; Shift + right click dumps its contents as piles. Catalog: `container_pushable`.
  - `single_type` (boolean, optional, default false): takes only one kind of item at a time; once it holds something only more of that item goes in (crates).
  - `accepts` (array, optional): tags (`#tag`) and/or exact asset ids chosen with the asset picker; empty = anything.
  - `on_add`: sets `properties.max_stack_size` to 1 (a container carries its own contents, so it is one per toolbar slot).

- `attach_item` / `attach_result` (base properties): a mount takes an item (a solar panel) and becomes its result. `attach_surface` may be `roof` (aimed at from the ground).
- `attach_surface` / `attach_side` / `provides_power` (base properties): an item that mounts on a finished building's wall or ceiling (a breaker box, sconces, ceiling lights); see docs/ATTACHED_ITEMS.md.

- `look_target` / `look_color` / `look_smoothness` / `look_metallic` (base properties): a construction material that sets how a building looks (roof or walls colour and sheen); see docs/CONSTRUCTION.md "Look follows the materials".
- container `max_items` / `slot_pitch_m` / `slot_start_m`: a slotted container (a battery rack) holds at most `max_items` items and draws them as their real models, one `slot_pitch_m` above the other from `slot_start_m`; see docs/BATTERIES.md.
