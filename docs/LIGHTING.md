# Lighting pack

A category of its own (`assets/lighting/<id>/`, ids `lighting_<piece>_<style>_<finish>`, sold at Volt Vision), apart from the older `building_light_*` items.
16 pieces x 2 styles (classic, modern) x 4 metal finishes = 128 items.

- Ceiling (`attach_surface: ceiling`): flush mount, pendant, chandelier, ceiling fan with light, track light.
- Inside wall (`wall`, `interior`): sconce, vanity bar, picture light, swing-arm lamp.
- Outside wall (`wall`, `exterior`, on dusk to dawn): wall lantern, barn light, security flood light.
- Ground (placeable, on dusk to dawn): garden post lamp (2.4 m), yard pole light (3.8 m), bollard, path light.
- Finishes: classic antique brass, oiled bronze, black iron, white; modern chrome, matte black, brushed nickel, white.
- Every light has `requires_power: true`; light offsets follow `docs/ATTACHED_ITEMS.md` (ceiling y is from the lowest point, wall z is out from the wall).

Code: `tools/lighting_models.py`, `tools/make_lighting_assets.py`; schema `assets/_schemas/lighting.schema.json`.

```bash
blender --background --python tools/make_lighting_assets.py      # every item (or: -- chandelier bollard)
python tools/make_lighting_assets.py --icons --force
python tools/generate_unity_asset_catalog.py && python tools/package_catalog_as_mods.py
```
