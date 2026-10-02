# Save game

The game saves itself and resumes where it left off. Code: `Assets/Scripts/Save/` (`GameSave.cs` is the data,
`GameSaveManager.cs` captures and applies it).

## What is saved

- **Time:** day of year, minute of day, speed, and a forced weather if one is set.
- **Player:** position, facing, and the camera's orbit and zoom.
- **HUD state:** the toolbar (items, counts, selected slot), vitals, resources (water, electricity, bandwidth, fuel by type,
  money) and loan debt.
- **World:** every planted crop and tree (group, position, facing, age, and whether it is withered, dead or a stump),
  every placed structure or prop (item, position, rotation), every phone order waiting for the delivery van (docs/DELIVERY.md), every structure under construction (id, position, turn, stage; docs/CONSTRUCTION.md), and every dropped item.
- **World seed** (informational: the terrain is regenerated from the same seed, so it must not change between runs).

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

- **Steadify mini player:** `miniPlayerOpen`, `miniPlayerX`, `miniPlayerY` (whether the pop-out player is showing and where). Captured and restored through `SteadifyMiniPlayer.Capture` / `Restore`.

- **Containers:** each toolbar slot saves the contents of a container item in it (`SavedSlot.contentIds` / `contentCounts`).
- **Placed containers:** `SavedPlaced.level` (position in a stack, 0 = on the ground) and `contentIds` / `contentCounts` (what the container holds).
