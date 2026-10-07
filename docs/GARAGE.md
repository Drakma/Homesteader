# Garage and workshop pack

A category of its own (`assets/garage/<id>/`, ids `garage_<piece>_<style>_<color>`). 14 pieces x 2 styles (classic, modern) x 4 colours = 112 items. Floor pieces are placeable, wall pieces mount on walls; all are bolted down (`wrench_remove`).

- Wood colour: workbench (vise), pegboard wall panel with tools (wall), sawhorse, shop stool.
- Painted-steel colour (classic red, forest green, navy, black; modern steel grey, matte black, safety orange, white): lumber rack (wall), rolling tool chest, top tool chest, tall cabinet, base cabinet with wood top, wall cabinet (wall), steel shelving with boxes, parts cabinet, air compressor (1500 W), bench grinder (400 W).

Code: `tools/garage_colors.py`, `tools/garage_lib.py`, `tools/garage_models.py`, `tools/make_garage_assets.py`; schema `assets/_schemas/garage.schema.json`.

```bash
blender --background --python tools/make_garage_assets.py
python tools/make_garage_assets.py --icons --force
python tools/generate_unity_asset_catalog.py && python tools/package_catalog_as_mods.py
```
