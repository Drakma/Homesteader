# Procedural Vegetation

World dressing built in code, not with Meshy. Flat-shaded low-poly meshes (under a few hundred triangles each),
URP/Lit materials, scattered by biome after terrain generation. Code: `Assets/Scripts/World/ProceduralVegetation.cs`,
called from `HomesteaderTerrainGenerator.SpawnBiomeAssets`. Toggle: `proceduralVegetationEnabled` on the generator.

## What goes where

| Item | Biome / place |
|---|---|
| Trees (maple, birch, oak, poplar, pine) | forest biomes, min 3 m apart, size 0.5625 of the original |
| Rocks, boulders, scree | `biome_rocky_ridge` |
| Cattail groups, small rocks | shoreline (cattails within 0.9 m of water, in noise-driven stands) |
| Rocks, sticks, fallen logs | river and lake beds |
| Flower clumps | `biome_meadow` (pasture; drifts, one colour per area) |
| Large grass tufts | `biome_grass_plains` |

## Wind, seasons, weather

All materials use `Homesteader/Vegetation` (`Assets/Scripts/Vegetation.shader`).

- **Wind:** vertices sway downwind by height above the base, using the global `_GrassWindParams` from
  `WeatherEffectsManager` (direction, speed, gust), so storms bend everything harder. Per-material `_SwayAmp` and
  `_SwayRef` (rocks and debris are rigid).
- **Seasons:** `VegetationSeasons` blends four keyframes (winter, spring, summer, autumn, centred on each season) from the
  in-game day of the year and sets each tracked material's `_BaseColor` and `_Grow`. `_Grow` scales the mesh about
  `_GrowPivotY`: deciduous crowns shrink away in winter and colour in autumn, flowers bloom spring to summer, cattails and
  tufts brown and shorten, conifers stay green. Register a material with `Seasonal(...)` in `ProceduralVegetation.cs`.
- **Weather:** global `_WeatherGroundEffects` (snow, wetness) whitens upward faces and darkens when wet.

## Rules

- Deterministic from `worldSeed`, so nothing is saved; it is rebuilt with the world.
- No colliders. No emoji in names or comments.
- Each scatter is one method (`ScatterRocks`, `ScatterShore`, `ScatterBed`, `ScatterFlowers`, `ScatterTufts`) with its own
  spacing and density constants at the top of its section.
- Grass blades (GPU) are separate: `grassEnabled` on the generator, currently off.
- Meshy image-to-3D remains the pipeline for structures, tools, animals and anything needing detail.

## Road bridges

`World/ProceduralBridge.cs` builds a wooden bridge wherever the starter road (see `starter_road` in the modding guide)
crosses water: an arched plank deck, stringers, posts, two rails and piles into the bed, flat shaded with the
Vegetation shader (snow and rain apply). The deck has a collider so the player walks over the water, and the rails have
invisible walls. The road router treats a river as a fair price to cross (a bridge) when that beats a long detour;
lakes and ponds are a prohibitive price, so the road goes round them. Runs of road over water between 4 and 60 m get a
bridge. `ProceduralBridge.BuildAcross(gen, from, to, width)` builds one anywhere (also the hook for player-built bridges);
`ProceduralBridge.Bridges` lists the current world's bridges. Deterministic from the road and the seed: nothing is saved.

## Chopping trees

`World/ForestTrees.cs`. Every procedural forest tree is registered (species, position, scale, birth day, where its triangles
sit in a chunk mesh). **The asset kit decides what fells a tree:** each species' growth group (`assets/logging/<tree>/<tree>.json`,
mirrored in `mods/homesteader/logging/`) carries `growth.rules.yield` with `tool` (`#axe`, a tag in `tags.json`: tool_axe,
tool_axe_felling, tool_hatchet_camp), `item_id` (the log item) and `amount_min`/`amount_max`. The tool must be the item in the
ACTIVE toolbar slot; a right click on a tree then chops it. The trees have no mouse colliders, so the tree is picked by ray, and
the player must be within 4.5 m. (These kit trees are stand-ins: when the kit's own tree models are replaced by the procedural
ones, the same group data stays the source of the rules.) A species with no kit group falls back to `#axe` and its default log.

- **Hits:** 1 sapling, 2 small, 3 medium, 5 mature. **Logs:** the yield roll for a mature tree, a quarter and a half of it for
  small and medium, none for a sapling. If the toolbar has no room the tree stays up.
- **Hold to chop:** holding the right button still on a tree swings every 0.8 s until it falls (a short click is one swing; dragging
  pans the camera). The player turns to the tree and plays the `Chop_Tree_RT` clip (`PedController.BeginWork`). Each hit gives a
  procedural thock, wood chips, and the tree shudders (a live copy stands in for the baked one, then the baked tree returns after 4 s
  without hits). No toasts, except failures (wrong tool, too far, toolbar full), at most one every 2.5 s.
- **Felling:** the tree's vertices are collapsed in its chunk mesh, a stump is left, and a copy of the tree falls over and
  disappears. Chainsaws are not wired (they would need fuel; add them to a tag if you want).
- **Hover (WAILA, F3):** name, stage, age, height, logs it will give, the tool needed and chops left.
- **Save:** felled trees are saved by position (`GameSave.fellTrees`) and re-applied after the forest regenerates.
  The trees' growth clock (`VegetationSeasons.GrowthDay`) is saved too and never goes backwards: growth stops at mature, and a
  season change or the Admin app jumping the date back can no longer shrink trees.

## Audio listener

The AudioListener is on `AudioListenerAnchor`, which follows the camera's focal point (the player), not on the camera: the
orthographic camera is pulled far back, and 3D sounds (footsteps, chopping, animals) are silent beyond 25 m.

## Solid trees and rocks

`World/ForestSolids.cs`. Trunks and rocks with a radius of at least 0.4 m (boulders, rocks, bigger shore and bed rocks; not
scree, sticks, flowers or tufts) block the player and animals. With thousands of them baked into meshes, real colliders exist
only near the player: a pool of 320 capsule colliders is re-placed onto the solids within 30 m whenever the player has moved
2.5 m, or a tree is felled. The colliders sit on the Ignore Raycast layer, and every mouse raycast (hover, planting, placing,
WAILA) uses `Physics.DefaultRaycastLayers`, so the mouse still sees through them to the ground. Do not use `~0` for a mouse raycast.

## Fruit trees and the willow grove

- **Species.** apple, lemon and orange are fruit trees (`Shape.Orchard`: a short trunk and a round crown carrying low-poly fruit); willow is
  `Shape.Weeping` (a low dome of leaves with a curtain of drooping strands). They are scattered thinly through meadow and grass plains
  (`Species.Scatter`); willows fill the `biome_willow_grove` biome (damp ground within 18 m of the water, noise-gated) and the marsh.
- **Fruit is its own submesh**, the tail of each variant's vertices. `ForestTrees.SyncFruit` (every 1.5 s) hides it by collapsing just
  those vertices, and puts it back, so picking never removes the tree. Fruit shows when the tree is old enough (the age where the kit's
  `fruit_stage` begins, the fruiting stage) and has not been picked in the last `regrow_days`; the fruit material is bare in winter.
- **Picking** is `ForestTrees.TryPickFruit` (right-click a ripe fruiting tree by hand, kit `growth.rules.fruit.drops`); picked trees are saved in
  `GameSave.pickedTrees`. Fell drops add `yield.extras`.
- **Willow grove** is the 17th terrain ground mode (`biome_willow_grove`, mode 16): the biome map alpha is `(mode + 0.5) / 17`, so
  `HomesteaderTerrainGenerator` (both bake loops) and `GenerativeTerrainURP.shader` must change together.
- **Icons.** `ForestTrees.MakeIconProxy(species, stage)` builds a tree at one growth stage for rendering the asset-kit icons (summer colours,
  fruit hidden except on the fruiting stage).
- **Planted fruit trees.** A sapling of a procedural species grows the procedural tree itself (`ForestTrees.ApplyPlantPrefabs` gives the kit group
  generated stage models). A planted tree is a `PlantedGrowth`: at the kit's fruiting stage it shows its fruit and `CanPickFruit`; a right-click
  by hand (`PlantedGrowth.PickFruit`) gives the drops, switches it to the stage before (no fruit) until `regrow_days` pass, and is saved in
  `SavedPlant.fruitPickedUntil`. With the harvest tool in hand the click fells it instead.
- **Small plants fade with the VIEW, not the player.** `VegetationFocusFade` finds the ground point at the middle of the window and sets the
  `_VegFocus` shader global; small plants (flowers, tufts, cattails, bed debris, scree: the materials only the non-shadow-casting `_ns` chunks use,
  flagged `_FocusFade`) shrink to nothing between 34 and 46 m of it, and `_ns` chunks wholly beyond 46 m are switched off. Panning moves the
  fade with the camera. Trees and shadow casters are untouched.
- **Forest thinning.** `ForestThinning` (25%) leaves that share of the trees out of the TREE biomes; a skipped spot still blocks its
  neighbours (otherwise they fill the gap). Fruit trees and willows are not thinned.
- **Crowns fade away at random.** Deciduous crowns shrink away whole, one tree at a time: the Vegetation shader gives each tree a random threshold
  (`crownFade`, from a hash of its position) that the material's `_LeafLoss` has to pass, so some trees lose their crown early in autumn and others
  late. `_LeafLoss` is keyed by season in `VegetationSeasons` (`Entry.Loss`: winter, spring, summer, autumn = 1, 0.3, 0, 0.22): all crowns gone in
  winter, some back in spring, all there in summer. Conifers and the citrus trees (evergreen) are not touched.

- **Sand (`biome_sand`, terrain mode 17).** Random stretches of the shoreline (a low-frequency noise mask inside the shoreline fringe) plus two or three
  small irregular sand pits (`SandPits()` in `HomesteaderTerrainGenerator`: seeded centres 4 to 8 m across, off the road, the starter zone and the water,
  with a noise-wobbled outline). Nothing grows on it. Definition: `assets/biomes/biome_sand.json`; texture: `SandTexture` in `GenerativeTerrainURP.shader`.

- **Shrubs and bushes (`ScatterShrubs`).** Leafy clumps built from 20-triangle leaf clusters on a few twigs, merged into the non-shadow chunks like the flowers and tufts (so they also fade with the view centre). Mostly in the tree biomes, willow grove and marsh in patches (a slow noise field), thick clumps along the shorelines out to 9 m from the water, and the odd bush elsewhere. Not on sand, rocky ridge, road verges or water.

- **Fruit is picked one at a time.** Each right-click with the kit's Pick With tool takes ONE random fruit off a procedural fruit tree (the kit's `fruit.drops` are what one fruit gives); the drawn fruit disappears from the baked mesh individually. A tree carries 24 apples / 26 lemons or oranges. The picked fruit all comes back `regrow_days` after the LATEST pick. Saved as `pickedTreeMasks` (a bit mask per tree). Planted fruit trees work the same way (their own mesh copy hides the picked fruit; saved as `fruitGoneMask`).
- **Picking gesture.** `FruitPickAnimator` (on the ped) plays a code-driven two-bone IK on LeftArm / LeftForeArm over the current animation: the left hand reaches up toward the fruit, the fruit comes off the tree, the hand bends in to the right hand (the basket) and the item lands in the toolbar (about 1.5 s; a click during it is ignored).

- **Berry bushes** (in `ScatterShrubs`): elderberry near the water (2 to 14 m), haskap on wet ground (marsh, willow grove, or 5 to 22 m from the water), blueberry and raspberry along the edges of the forests, huckleberry inside them. Each kind has its own noise field, so it comes in tight clumps and is uncommon. They are the ordinary bush with berries (a third submesh, in fruit from summer, bare in winter), and they take the place of some of the ordinary bushes, which are now 45% fewer. They are picked like the fruit trees (`BerryBushes.cs`): right-click with the tool, one berry at a time, the same reach gesture; the rules are the bush assets' `fruiting` add-on schema (`bush_blueberry` etc.: tools, drops, regrow_days). Picking a bush takes the WHOLE bush in one go: the player kneels (`Fixing_Kneeling_RT`, else `Farm_PlantSeed_RT`) and stays down while the left arm goes straight out for the berries in up to four quick cycles (twice the tree speed), then stands. Moving cancels any pick (tree or bush): a berry already in the hand goes in the basket, the rest stays on the plant. No berries in winter. Saved as `pickedBushes` / `pickedBushMasks`.
