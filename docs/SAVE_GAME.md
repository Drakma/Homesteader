# Save game

The game saves itself and resumes where it left off. Code: `Assets/Scripts/Save/` (`GameSave.cs` is the data,
`GameSaveManager.cs` captures and applies it).

## What is saved

- **Time:** day of year, minute of day, speed, and a forced weather if one is set.
- **Player:** position, facing, and the camera: the yaw it is turning to (restored as its target, so it does not turn back), the zoom, and whether it was panned off the player with where it was looking.
- **HUD state:** the toolbar (items, counts, selected slot), vitals, resources (water, electricity, bandwidth, fuel by type,
  money) and loan debt.
- **World:** every planted crop and tree (group, position, facing, age, and whether it is withered, dead or a stump),
  every placed structure or prop (item, position, rotation), every phone order waiting for the delivery van (docs/DELIVERY.md), every structure under construction (id, position, turn, stage; docs/CONSTRUCTION.md), and every dropped item.
- **World seed** (the generator reads it from the save whenever it builds the world, however the scene came to load).
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
