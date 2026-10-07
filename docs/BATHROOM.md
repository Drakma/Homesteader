# Bathroom pack

A category of its own (`assets/bathroom/<id>/`, ids `bathroom_<piece>_<style>_<color>`, sold at the furniture store), apart from the kit's `appliance_toilet_flush`, sinks and shower stall.
18 pieces x 2 styles (classic, modern) x 4 colours = 144 items.

- Fixtures (glaze colour; classic white, bone, sage, black; modern white, matte black, stone grey, navy): toilet, pedestal sink, alcove tub, freestanding tub (clawfoot / oval), shower stall.
- Cabinetry (wood colour): single and double vanity (stone top, basins, faucets: support surfaces), medicine cabinet, bathroom mirror, linen cabinet, towel shelf (a shelf with a towel bar under it).
- Textiles (fabric colour): laundry hamper, towel stack, bath mat.
- Accessories (metal finish): towel bar, toilet paper holder, robe hook rail, soap set.
- Wall items (medicine cabinet, mirror, towel shelf, towel bar, paper holder, hook rail) are `attach_surface: wall`, `attach_side: interior`.
- Water use is in `category_fields.water_per_use_l` / `water_usage_lpm`, like the kit's appliances.

Code: `tools/bathroom_colors.py`, `tools/bathroom_lib.py` (palette, open-vessel builder, faucet), `tools/bathroom_models.py`, `tools/make_bathroom_assets.py`; schema `assets/_schemas/bathroom.schema.json`.

```bash
blender --background --python tools/make_bathroom_assets.py      # every item (or: -- toilet vanity_single)
python tools/make_bathroom_assets.py --icons --force
python tools/generate_unity_asset_catalog.py && python tools/package_catalog_as_mods.py
```
