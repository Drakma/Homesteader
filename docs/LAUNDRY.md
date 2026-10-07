# Laundry and mudroom pack

A category of its own (`assets/laundry/<id>/`, ids `laundry_<piece>_<style>_<color>`, sold at the furniture store). 12 pieces x 2 styles (classic, modern) x 4 colours = 96 items. Floor pieces are placeable, wall pieces mount on inside walls; all are bolted down (`wrench_remove`).

- Wood colour: mudroom bench, coat rack (wall), mudroom lockers, shoe rack, laundry wall cabinet (wall), folding counter, utility sink (deep steel basin, tall faucet, `water_per_use_l`), drying rack, storage shelves with baskets.
- Fabric colour: ironing board, laundry basket, three-bag sorter.
- The washer and dryer are the kit's `appliance_washer_*` and `appliance_dryer_*`.

Code: `tools/laundry_models.py`, `tools/make_laundry_assets.py` (palettes from `tools/living_lib.py`); schema `assets/_schemas/laundry.schema.json`.

```bash
blender --background --python tools/make_laundry_assets.py
python tools/make_laundry_assets.py --icons --force
python tools/generate_unity_asset_catalog.py && python tools/package_catalog_as_mods.py
```
