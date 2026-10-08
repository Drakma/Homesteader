# Save game

The game saves itself and resumes where it left off. Code: `Assets/Scripts/Save/` (`GameSave.cs` is the data,
`GameSaveManager.cs` captures and applies it).

## Where saves live

Every save is a file in the **Saves** folder next to the game (the Unity project folder in the editor; `SaveSlots.cs`):

- `Saves/Name.json`: the save made with the Save button or F9 (one per game name, overwritten each time).
- `Saves/Name-autosave.1.json`, `.2`, `.3` ...: the autosaves. `.1` is the newest; each autosave rolls the older ones up one number and the oldest past the number kept is deleted.
- `Saves/Name.world`: the generated ground of that game (see "World snapshot" below), shared by all its saves.
- `Saves/Name.jpg` / `Name-autosave.N.jpg`: a small picture of the game taken now and then while playing, saved with each save and shown in the Load list.

`Name` is the name typed when the game was started (New Game asks for it; a taken name gets " 2", " 3" ...). Settings > General > Saving sets the autosave interval (minutes, default 5) and how many autosaves are kept (default 5). The game also autosaves when it is paused or closed. Continue loads the newest file; **Load** lists every file in the folder (name, date, size, in-game day, world, picture) to pick from or delete. A save made before the folder existed (one `autosave.json` in the data folder) is copied in once as the game "Homestead".

## What is saved

- **Time:** day of year, minute of day, speed, and a forced weather if one is set.
- **Player:** position, facing, and the camera: the yaw it is turning to (restored as its target, so it does not turn back), the zoom, and whether it was panned off the player with where it was looking.
- **HUD state:** the toolbar (items, counts, selected slot), vitals, resources (water, electricity, bandwidth, fuel by type,
  money) and loan debt.
- **World:** every planted crop and tree (group, position, facing, age, and whether it is withered, dead or a stump),
  every placed structure or prop (item, position, rotation), every phone order waiting for the delivery van (docs/DELIVERY.md), every structure under construction (id, position, turn, stage; docs/CONSTRUCTION.md), and every dropped item.
- **World seed** (the generator reads it from the save whenever it builds the world, however the scene came to load).
- **Door states:** each saved building site carries `openDoors`, the names of the interior, barn and garage door objects left open (`ConstructionSite.OpenDoorList` / `SetOpenDoors`); the front door is `doorOpen`. A building loads with its doors as they were left, also after a stage change.
- **Tilled ground:** `tilledCells` (grid squares tilled into farmland with a hoe; painted into the terrain's biome map again after the world is generated on load).
- **Broken rocks:** `brokenRocks` (x, z of scattered rocks broken with a pickaxe; the rocks themselves come from the seed and are removed again after the world is generated on load).
- **Berry bushes:** `dugBushes` (x, z of generated bushes dug up with a shovel; the bushes themselves come from the seed) and `plantedBushes` (kind, position, turn, size of bushes the player planted). Picked-berry state is kept as before and applies to planted bushes too.
- **Painted doors (placed):** a placed object that was painted with a paint can (a door item) carries `paintId`, the paint item's id, in its `SavedPlaced`; it is painted again when the save is restored (`PlacedObject.ApplyPaint`).
- **Paint:** each saved building site carries `wallPaints`: `"Wall_Front|out=building_paint_sage"` (the outside of a wall), `"Door:DoorSlide_b1L=building_paint_navy"` (a door leaf), `"Shutter:Wall_Front=..."` (a wall's shutters) and `"P|item|origin|normal|tangent|cell|order|row:first:last;..."` (a painted section of an inside wall: the grid it was laid on and the runs of cells, in the site's local space). They are painted again whenever a stage model shows (`ConstructionSite.ApplyWallPaints`).
- **World snapshot** (`world.snapshot` beside the save, `WorldSnapshot.cs`): the heightmap, biome map, water features and road line the generator produced, written the first time the world is saved. On the next run the generator restores them instead of evaluating its noise (`HomesteaderTerrainGenerator.Snapshot.cs`), so a change to the generator, the mods or the rules cannot move the ground a save was made on. It holds the ground as generated, before any building grading (construction sites grade it again). It is deleted with the save on New Game, ignored when its seed or size does not fit, and an old save without one writes it on its first save.

Not saved yet: animals (only dev-spawned ones exist), snow and puddle accumulation (weather-driven), open windows.

## When

- On start, after the mods, terrain, player and HUD exist, the last save is restored. Only then does autosave begin, so a
  fresh world can never overwrite a save that has not been restored.
- Autosave every 30 real seconds, when Play stops, and when the app pauses or quits.
- **F9** saves right now.

## Where

`Application.persistentDataPath/Saves/autosave.json` (on this machine
`C:\Users\casey\AppData\LocalLow\DefaultCompany\Homesteader\Saves\`). The previous good save is `autosave.bak.json`; a
damaged main file falls back to it. Writes go to a temporary file first, so a crash mid-save cannot corrupt the save.

## New game

Delete `autosave.json` and `autosave.bak.json` and start the game.

## Adding something to the save

Add a field to `GameSave`, fill it in `GameSaveManager.Capture()` and apply it in `ApplySave()`. Bump
`GameSave.CurrentVersion` only when an old save could no longer be read.

- **Steadify music:** `musicPlaying` (older saves: true). The track is prepared at start-up but only started by `AudioManager.StartMusicAfterLoad` once the save has been applied (and not when a radio station is tuned in, or music was paused when saved).
- **Steadify mini player:** `miniPlayerOpen`, `miniPlayerX`, `miniPlayerY` (whether the pop-out player is showing and where). Captured and restored through `SteadifyMiniPlayer.Capture` / `Restore`.
- **Steadify radio:** `radioStation` (the station tuned in, empty when off), `radioLine` (the line reached), `radioPaused`. Captured and restored through `RadioPlayer.Capture` / `Restore`; the episode itself is rebuilt from the on-disk cache or written again (`docs/RADIO.md`).

- **Containers:** each toolbar slot saves the contents of a container item in it (`SavedSlot.contentIds` / `contentCounts`).
- **Placed containers:** `SavedPlaced.level` (position in a stack, 0 = on the ground) and `contentIds` / `contentCounts` (what the container holds).

## Load screen

Continue and Load show the welcome menu's progress bar from the first frame of the reloaded scene until the game is fully standing: terrain (0 - 50%),
the save itself (50 - 100%: the world state, placed objects, structures, paths and fences, drops, then "Raising buildings" while
every structure's model loads, and "Settling objects" which sets the objects that stand on the ground back onto it after the ground has been graded under
the buildings). `GameSaveManager.LoadProgress` / `LoadPhase` feed the bar and `Restored` ends it; the screen fades out only then.

- **Septic tanks and leach fields:** `SavedSite.sewageL` / `sludgeL` hold a septic tank's liquid and sludge (a leach field's liquid in `sewageL`); restored onto the site's node on load. Pending pump-outs are `DeliveryService.Order` entries with `septic` set (docs/SEPTIC.md).
- **Storage structures (grain silos):** `SavedSite.contentIds` / `contentCounts` hold what a finished storage structure contains; restored onto the site on load.

## Placed things never hover

`PlacedObject.SettleOnGround` runs after a load AND every 3 s while playing (`PlacedObject.Settler`): anything not held by something (the ground, a floor or deck of a building, a pallet, the piece under it in its stack) is lowered onto what is under it, a stack with a gap in it closes up, and a stack whose bottom piece has nothing under it comes down. Things on a floor, a foundation or a deck stay while the building is there and come down when it is gone.
- Meal Builder saved meals: `savedMeals` (name, foods, drink), `Kitchen/SavedMeals.cs`. A container stack in a cabinet or toolbar slot keeps the liquid it holds: `contentLiquid` / `contentStored` beside `contentIds` / `contentCounts` (and `contentUsed`: the uses taken from the opened item on top).
- Placed liquid containers (tanks, drums, cans): the liquid in a tank is `SavedPlaced.liquidId`, its liters ride in `wireUsed` (`LiquidRules.Held`). A pending bulk fuel order is a delivery with `fuel = true` (`DeliveryService.Order`).

- **Wall shelves**: what stands on a shelf is saved with the mounted shelf, as parallel lists in `SavedAttached` (`shelfIds`, `shelfX` its place along the board, `shelfUsed` a coil's used metres, `shelfLiquids`); `Shelf.Restore` puts the models back as they load.
- **Network**: the Cat6 cables are saved with the other wires (`SavedWire`, kind `net`); what is in a wall rack is saved with the rack in `SavedAttached.shelfIds` (bottom unit first). Online state, power and the phone signal are worked out, never saved.
- **Internet plan**: `netPlan` (the plan id, empty = none) and `netPlanDaysLeft` (`NetPlan.cs`).
- **Sawmill**: the log on its track is saved with the sawmill (`SavedPlaced.sawLog`); the cut itself is not (it takes about 12 seconds; a save in the middle of it keeps the log). The lumber is ordinary placed items.
