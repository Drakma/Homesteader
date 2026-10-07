# Dining Room pack

A category of its own (`assets/dining/<id>/`, ids `dining_<piece>_<style>_<color>`). 8 pieces x 2 styles (classic, modern) x 4 colours = 64 items. Floor pieces are placeable, wall pieces mount on walls; all are bolted down (`wrench_remove`).

- Wood colour: dining table (seats six), round pedestal table, china cabinet with plates, bar cart with bottles, wine rack.
- Fabric colour: dining chair, host chair with arms, dining bench.

Code: `tools/dining_models.py`, `tools/make_dining_assets.py` (palettes from `tools/living_lib.py`); schema `assets/_schemas/dining.schema.json`.

```bash
blender --background --python tools/make_dining_assets.py
python tools/make_dining_assets.py --icons --force
python tools/generate_unity_asset_catalog.py && python tools/package_catalog_as_mods.py
```
