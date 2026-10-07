# Bedroom pack

A category of its own (`assets/bedroom/<id>/`, ids `bedroom_<piece>_<style>_<color>`, sold at the furniture store), apart from the kit's furniture and the other room packs.
16 pieces x 2 styles (classic, modern) x 4 colours = 128 items. All are placeable and bolted down (`wrench_remove`: a right click with a wrench takes them up).

- Upholstered / bedding (fabric colour: classic burgundy, forest, navy, camel leather; modern charcoal, stone, teal, mustard): queen, king, twin and bunk beds, bed-end bench, vanity stool, desk chair.
- Case goods (wood colour: classic mahogany, walnut, cherry, oak; modern birch, walnut, white, black): nightstand, dresser, chest of drawers, dressing table with mirror, wardrobe, blanket chest, crib, standing mirror, desk. Tops are support surfaces.
- Classic: turned posts, tufted headboards, raised-panel drawers, brass knobs. Modern: platform frames, slab fronts, slim tapered legs, black metal.

Code: `tools/bedroom_models.py`, `tools/make_bedroom_assets.py` (palettes from `tools/living_lib.py`); schema `assets/_schemas/bedroom.schema.json`.

```bash
blender --background --python tools/make_bedroom_assets.py      # every item (or: -- bed_queen dresser)
python tools/make_bedroom_assets.py --icons --force
python tools/generate_unity_asset_catalog.py && python tools/package_catalog_as_mods.py
```
