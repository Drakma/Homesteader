# Home Office pack

A category of its own (`assets/office/<id>/`, ids `office_<piece>_<style>_<color>`). 9 pieces x 2 styles (classic, modern) x 4 colours = 72 items. Floor pieces are placeable, wall pieces mount on walls; all are bolted down (`wrench_remove`).

- Wood colour: writing desk, executive desk, credenza, filing cabinet, lateral file, whiteboard (wall), cork board (wall).
- Fabric colour: swivel office chair, guest chair.

Code: `tools/office_models.py`, `tools/make_office_assets.py` (palettes from `tools/living_lib.py`); schema `assets/_schemas/office.schema.json`.

```bash
blender --background --python tools/make_office_assets.py
python tools/make_office_assets.py --icons --force
python tools/generate_unity_asset_catalog.py && python tools/package_catalog_as_mods.py
```
