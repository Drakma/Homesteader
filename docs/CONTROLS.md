# Homesteader controls

The single list of every key and mouse binding in the game. **Check it before assigning a key, and update it in
the same change whenever you add, move or remove one.** Keys are read through the Input System
(`Keyboard.current`) with a legacy `Input` fallback; while a window, the phone's text box, or the asset spawner
owns the keyboard, game hotkeys are ignored (`HudBindings.KeyboardCaptured`).

## Movement and camera

| Input | Action | Where |
| :--- | :--- | :--- |
| W A S D | Walk. Directions follow the camera (isometric), so straight up the screen is W+D | `PedController` |
| Left Shift (hold) | Run | `PedController` |
| Q / E | Rotate the camera 90 degrees left / right | `IsometricLockedCamera` |
| Ctrl + mouse wheel | Zoom in / out in steps of 1 from 2.5 (no upper limit) | `IsometricLockedCamera` |
| Right mouse + drag | Pan the camera off the player | `IsometricLockedCamera` |

## Toolbar, tools and the world

| Input | Action | Where |
| :--- | :--- | :--- |
| 1 - 9, 0 (or numpad) | Select toolbar slot 1 - 10 | `HudBindings` |
| Mouse wheel | Cycle toolbar slot (not while Ctrl is held, the phone is open, or the game is paused) | `HudBindings` |
| Right click | Plant with the selected seed / harvest the plant in reach | `PlantingController` |
| Left click | Place the selected structure / prop on the square under the cursor (a translucent shadow shows where; blue = valid, red = not) | `PlacementController` |
| R (Shift+R) | Rotate the shadow being placed 12.5 degrees clockwise (counter-clockwise) | `PlacementController` |
| F | Player light: flashlight, then lantern, then off | `PlayerLight` |
| M | Show / hide the map. Dots: faint yellow = you, white = animals, red = predators / aggressive animals | `MiniMap` |
| Drag the map | Move the map (position, size and zoom are remembered) | `MiniMap` |
| Shift + mouse wheel over the map | Make the map bigger / smaller | `MiniMap` |
| Mouse wheel over the map | Zoom the map in / out (it does not zoom the game view or cycle the toolbar there) | `MiniMap` |

## Time and menus

| Input | Action | Where |
| :--- | :--- | :--- |
| Space | Pause / resume time | `HudBindings` |
| ] / [ | Faster / slower time speed | `HudBindings` |
| Tab | Open / close the phone | `HudBindings` |
| Esc | Close the top window, phone or modal; otherwise open Settings | `HudBindings` |

## Debug and development

| Key | Action | Where |
| :--- | :--- | :--- |
| F2 | Toggle ground grid brightness | `GridBrightnessToggle` |
| F3 | Toggle the WAILA panel (what is under the cursor) | `WailaPanel` |
| F4 | Toggle the hover outline | `HoverOutline` |
| F5 | Spawn the dev animal (Labrador) beside the player | `AnimalSpawner` |
| F6 | Toggle animal AI debug labels (behavior, needs, top scores) | `AnimalSpawner` |
| F9 | Save the game now (it also autosaves every 30 seconds) | `GameSaveManager` |

## Free keys (do not reuse the ones above)

F1, F7, F8, F10 - F12, and every unlisted letter (G, H, T, Y, U, I, O, P, Z, X, C, V, B, N). Keep W A S D Q E F Space Tab
Esc [ ] and 0 - 9 as they are.

## Not bound yet (clips exist, no key)

`PedController.Carrying` switches walking to the two-arm carry clip. The work clips (Chop_Tree_RT, Dig, Hoe,
Farm_PlantSeed_RT, Pet, Fixing_Kneeling_RT, Sleeping_RT) and the Drag upper-body clip are played by gameplay code
through `GlbClipPlayer.BeginAction` / `PlayUpperBody`; nothing triggers them from a key right now.
