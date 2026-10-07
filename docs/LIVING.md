# Living room pack

A category of its own (`assets/living/<id>/`, ids `living_<piece>_<style>_<color>`, shop chip "Living Room", sold at the furniture store "Sofa So Good"), apart from the kit's general furniture and the kitchen pack.
26 pieces x 2 styles (classic, modern) x 4 colours = 208 items.

- Upholstered pieces (sofa, loveseat, armchair, recliner, sectional, ottoman, pouf, accent chair), lamps (shade), rugs and the plant pot vary in FABRIC colour. Classic: burgundy, forest, navy, camel (leather). Modern: charcoal, stone, teal, mustard.
- Wooden pieces (tables, TV stand, sideboard, bookshelf, display cabinet, toy chest, rocker, piano, TV, mirror, picture, clock) vary in WOOD colour. Classic: mahogany, walnut, cherry, oak. Modern: birch, walnut, white, black.
- Classic: turned legs, rolled arms, button tufting, mouldings, brass. Modern: clean slabs, slim tapered legs, black metal.
- Lamps carry a `lights` entry (point light, needs power, 12 W). Tables, shelves, consoles and the bookshelf (five `deck_heights`) are support surfaces. Mirror, picture and clock are wall items.

Code: `tools/living_colors.py` (palette lists, no Blender), `tools/living_lib.py` (textures, Palette), `tools/living_models.py` (one function per piece), `tools/make_living_assets.py` (item list, manifests, GLBs, icons).

```bash
blender --background --python tools/make_living_assets.py          # every item (or: -- sofa bookshelf)
python tools/make_living_assets.py --icons --force                 # the icons
python tools/generate_unity_asset_catalog.py && python tools/package_catalog_as_mods.py
```

Schema: `assets/_schemas/living.schema.json`; category registered in `assets/kit_config.json`.
