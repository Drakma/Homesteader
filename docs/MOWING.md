# Mowing

A push mower (`tool_push_mower`, manifest `properties.pushable` + `properties.mower_width_m`) turns grass into a fresh-cut striped lawn.

- Take the handles like a wheelbarrow (right click, empty slot). While pushed, `PushMower` samples the deck path (deck width across, the distance moved along) and calls `LawnSoil.Mow`.
- `LawnSoil` mirrors `FarmlandSoil`: grid squares (`PlantingValidator.GridSizeM`), painted into the baked biome map as mode 5 (`biome_maintained_grass`), `TerrainGroundBake.Rebake` redraws the ground, `SiteClearing.ClearGround` removes grass tufts and flowers. Trees, bushes and rocks stay.
- Not mowed: water, near a road, farmland, lawn already.
- Stripes: `HomesteaderTerrainGround.hlsl` (`BiomeLandColor`, lawn branch) draws bands 0.6 m wide, light and dark, with soft edges and blade noise. Biome map red channel selects the direction (mode + 0.25 = stripes along Z). The first square takes the mower's travel direction; squares mown next to lawn continue that lawn's direction.
- `PlantingZone.BiomeAt` reports mown squares as `biome_maintained_grass`.
- Save: `GameSave.mowedCells` / `mowedAlongZ`, captured and applied in `GameSaveManager`; `LawnSoil.Clear()` on a new world (`ProceduralVegetation`).
- Model: `tools/make_push_mower.py` (+x front, handles at -x). Fuel is not modeled.
