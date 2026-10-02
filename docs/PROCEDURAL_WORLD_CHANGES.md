# Procedural world: changes and rules (2026-09-30)

What was built or changed in this stretch of work, where it lives, and the rules that follow from it. The short rule
list is also in `CLAUDE.md` (section 5). Details for the plant and bridge code are in `docs/PROCEDURAL_VEGETATION.md`.

## 1. World dressing (code-built, not Meshy)

| Change | Where |
|---|---|
| Trees, rocks and scree, shoreline cattails and rocks, river and lake bed rocks and debris, meadow flower clumps, prairie grass tufts | `Assets/Scripts/World/ProceduralVegetation.cs` |
| Promoted from temporary to permanent; toggle is `proceduralVegetationEnabled` on the terrain generator (keeps the old saved value) | `HomesteaderTerrainGenerator.cs` |
| One shader for all of it: wind sway, season growth and colour, age growth, snow, rain | `Assets/Scripts/Vegetation.shader` |
| Season blending (winter, spring, summer, autumn keyframes from the in-game day) and the `_VegDay` global | `Assets/Scripts/World/VegetationSeasons.cs` |
| Scattered objects are merged into 32 m chunk meshes after generation (20k renderers cost about 70 fps) | `ProceduralVegetation.Combine` |
| Tree growth: four stages (sapling, small, medium, mature) at 16, 35, 65, 100 percent height, windows read from each species' growth group in `logging/<tree>/<tree>.json`; mixed-age starting stand; nothing saved | `Vegetation.shader` (`VegAgeScale`), `ProceduralVegetation.StageEnds/RollAge` |
| Bare winter branches on deciduous trees; pine tiers overlap more (4 tiers, 8 sides) | `BuildBroadleaf/AddBranches`, `BuildConifer` |
| Tuning values used: trees 0.5625 of original size, 3 m minimum tree spacing, cattails within 0.9 m of water in groups, flowers in `biome_meadow` only and only from 1 March, tufts in `biome_grass_plains` only | constants in `ProceduralVegetation.cs` |

## 2. Starter zone, road and bridges (game rules as mod data)

| Change | Where |
|---|---|
| `starter_zone`: a 16 m square (`grass_area_m`) around the spawn point is grass plains or meadow (never maintained grass, which is player-made only); at least one water feature in the tile; water at most 15 percent of the tile | `Growth/GameRules.cs`, `HomesteaderTerrainGenerator.cs` (`EnforceStarterZoneWater`, `InStarterGrassArea`) |
| `starter_road`: dirt and gravel road from a map edge to the edge of the grass area, routed around water and hills, meandering, blends into the lawn over 18 m; ruts 0.72 m off centre | `HomesteaderTerrainGenerator.Road.cs`, terrain shader `RoadTexture` |
| Bridges where the road crosses water (4 to 60 m), with colliders | `Assets/Scripts/World/ProceduralBridge.cs` |
| Trees, rocks, flowers and tufts keep off the road; terracing eases off the road bed | `IsNearRoad`, `RoadInfluence` |
| Owned-land boundary is a procedural post-and-rail fence instead of the white or yellow line; it follows the terrain, stops for water (post at each bank) and leaves an opening with gate posts where the road passes; the invisible land walls still block movement | `Assets/Scripts/World/ProceduralFence.cs`, `BoxMesher.cs`, `Land/LandBoundaryController.cs` |
| Removed the `starter_farmland` zone quad from `gamerules.json` | `mods/homesteader/gamerules/`, `assets/_gamerules/` |
| Schema and docs for all of the above | `assets/_schemas/gamerules.schema.json`, `docs/MODDING_GUIDE.md` section 4e |

## 3. Camera, shadows and fog

- The orthographic camera sits far back along its view direction (orbit radius + 2 x zoom + 5 m) so everything in view
  is in front of it and the near plane stays at 0.3. A negative near plane skewed shadow cascades and fog.
- Shadow distance is set each frame to fit the zoom (`IsometricLockedCamera`); one shadow cascade, 4096 map. A long
  fixed range made shadow edges shimmer.
- Fog density is multiplied by `IsometricLockedCamera.FogCompensation` (orbit radius / camera distance) in
  `WeatherEffectsManager.SmoothFog`, otherwise snow and rain fog grey out the player.

## 4. Terrain and water fixes

- Biome map bake samples texel centres (`+ 0.5`), so colours line up with the data trees and rocks use.
- Shoreline lapping in `WaterSurface.shader`: the waterline only ever recedes from the smooth shoreline, never advances
  (advancing washed the bank cyan).
- Bog (wetland) colour is point sampled in `GenerativeTerrainURP.shader`; the bilinear tint pulled in the river's blue and
  made a cyan fringe on one bank.
- Grass (GPU) is switched off with `grassEnabled` on the generator; it must skip the road when it returns.

## 5. Rules that came out of this

1. World dressing (plants, rocks, debris, small props) is procedural and code-built; Meshy image-to-3D stays for
   structures, tools, animals and anything needing detail.
2. Every procedural mesh uses `Homesteader/Vegetation` so wind, seasons, snow and rain apply. Register seasonal
   materials with `Seasonal(...)`.
3. Never put tens of thousands of separate renderers in the world: merge scatter output into chunk meshes.
4. Anything scattered must keep off the road (`IsNearRoad`) and off water.
5. Maintained grass is player-made only: world generation never produces it.
6. Starter zone, road and bridge behaviour is data in `gamerules.json`; change the mod copy, the `assets/_gamerules`
   source, the schema and the modding guide together.
7. Do not use a negative camera near plane. Keep the camera pulled back and the near plane at 0.3.
8. `Mathf.SmoothStep(a, b, t)` is not GLSL `smoothstep(e0, e1, x)`; use `InverseLerp` first.
9. Do not run several `GenerateTerrain()` calls in one editor command (it froze Unity); one seed per command.
10. To look at a scene change, render a temporary camera to a PNG in the scratchpad and read it.
