# Decor (curtains, drapes and plants)

A category of its own, `decor` (`assets/decor/<id>/`, ids `decor_<piece>_<style>_<colour>`), built by `tools/make_decor_assets.py` and `tools/decor_models.py`:

| Piece | Size | What it is |
|---|---|---|
| Curtains | 1.8 x 1.6 m | a pair of sill-length panels on a rod, open at the sides (classic: brass rod, rings, finials, folds; modern: slim black rail, soft wave folds) |
| Drapes | 2.3 x 2.5 m | a pair of floor-length lined panels tied back at the sides, with a puddle at the floor, under a valance (classic) or on a ceiling track (modern) |

Each piece comes in a classic and a modern style and the four fabric colours of the living room pack (`tools/living_colors.py`): 2 x 2 x 4 = 16 items. They mount on an INSIDE wall
like a wall light (`attach_surface: wall`, `attach_side: interior`): the click sets the height of the HEM (a drape's floor), the model's back is the wall and it stands 0.1 m out.
Sold in the furniture shop. Rebuild: `blender --background --python tools/make_decor_assets.py`, then `python tools/make_decor_assets.py --icons --force`,
`python tools/generate_unity_asset_catalog.py` and `python tools/package_catalog_as_mods.py`.

## House plants

Built by `tools/decor_plants.py` (colours in `tools/decor_colors.py`: four pot colours per style). Floor plants are placed like furniture (`placeable`); the succulent is small enough for a shelf; the hanging fern mounts on a ceiling inside (`attach_surface: ceiling`).

| Piece | Size | |
|---|---|---|
| Fiddle-Leaf Fig | 0.6 x 1.7 m | trunk with a crown of big leaves |
| Parlor Palm | 0.9 x 1.2 m | arching fronds with paired leaflets |
| Snake Plant | 0.3 x 1.0 m | stiff upright blades |
| Monstera | 0.7 x 1.4 m | stems with big split leaves |
| Succulent Pot | 0.13 x 0.17 m | a rosette in a small pot |
| Hanging Fern | 0.7 x 1.0 m | a basket on three chains, fronds drooping all round |

Classic has a tapered pot on a saucer, modern a plain drum planter: (2 curtains + 6 plants) x 2 styles x 4 colours = 64 items.

## Hanging

Curtains and drapes hang with their top 10 cm above the window nearest the cursor on that wall (within 1.5 m along it) and are centred on it (`AttachController.CurtainAboveWindowM`, `StructureWindows.OpeningNear`). With no window near, they hang where the cursor is. Either way the top never passes the ceiling.
