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
hand-rolled field-spec that `HUD/scripts/validate_schema.py` reads directly:

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
py -3 HUD/scripts/validate_schema.py appliances
```

Reports every item in `assets/appliances/*/*.json` that's missing a required
field or has a field of the wrong type. Exit code 0 = all items comply.

## Categories defined so far

- `appliances` - `dimensions_m` (width/depth/height in meters). Added
  2026-09-15 as the first field, since real-world footprint size was the
  original reason this whole schema system got proposed (a house has a
  finite amount of floor space).
