# Piles of bulk material

Sand, gravel, dirt, mulch, bedding stone and manure lie in PILES that GROW as material is added (`PileService`).

- A pile holds a number of shovelfuls (0.005 m3 each). Which pile item it is follows from how many it holds: the stages of the material's equivalency (m3), smallest first:
  tiny (2 shovelfuls, 0.01 m3), small (10), medium (40), large (150, the most one pile holds). The model swaps to the stage that fits and is scaled between stages (`PileVisual`).
- A pile with no contents is a WHOLE pile of its stage (what is bought, or dropped from the toolbar or the asset spawner). A part-filled one lists its shovelfuls as its contents (saved with it).
- Adding: a loaded shovel, right click on a pile of that material, puts its shovelfuls on it. Right click on open ground with a loaded shovel empties it there: onto a pile of that
  material within about 1.25 m, else as a new tiny pile that grows with the rest. A wheelbarrow dump and breaking a stone with a pickaxe add the same way.
- Overflow: what a full pile (150) cannot take starts another pile next to it.
- Taking: an empty shovel, right click on a pile, takes a shovelful; the pile shrinks and goes down a stage when it should; the last shovelful removes it.
- Every size can be bought and dropped (the tiny ones too). A whole pile in the toolbar is dropped as a placed pile.
- Models: `tools/make_pile_models.py` (textured, with `tools/make_pile_textures.py`); the stages are the `mat_pile_<material>_<size>` / `waste_pile_manure_<size>` items, listed as members of the
  material's equivalency in `assets/_schemas/equivalencies.json`, each worth its volume in m3 (`GrowthRegistry.PilesOfScoop`, `BulkOf`).
