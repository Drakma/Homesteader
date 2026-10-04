# Homesteader controls

The single list of every key and mouse binding in the game. **Check it before assigning a key, and update it in
the same change whenever you add, move or remove one.** Keys are read through the Input System
(`Keyboard.current`) with a legacy `Input` fallback; while a window, the phone's text box, or the asset spawner
owns the keyboard, game hotkeys are ignored (`HudBindings.KeyboardCaptured`).

## Rebinding

Settings > Controls (the Settings dialog opens from the menu) lets the player rebind these actions: move
up / down / left / right, run, rotate camera left / right, pause, faster / slower time, phone, flashlight,
map, rotate placement. They are read through `Homesteader.Controls.KeyBindings` (`BindAction` enum,
`Assets/Scripts/Controls/KeyBindings.cs`), never by key, and saved in `PlayerPrefs` (`Homesteader.Key.*`).
The keys listed below are the **defaults**. Binding a key that another action already uses swaps the two.
Esc, 0 - 9 (and numpad), F1 - F12 and Ctrl are reserved and can't be bound. **A new rebindable action goes in
`BindAction` and `KeyBindings.All`, and its call site must use `KeyBindings.WasPressedThisFrame` / `IsPressed`.**

## Movement and camera

| Input | Action | Where |
| :--- | :--- | :--- |
| W A S D | Walk. Directions follow the camera (isometric), so straight up the screen is W+D | `PedController` |
| Left Shift (hold) | Run | `PedController` |
| Q / E | Rotate the camera 90 degrees left / right | `IsometricLockedCamera` |
| Ctrl + mouse wheel | Zoom in / out in steps of 1 from 3 up to the Zoom Max Level (Settings > General, 3 to 50, default 15) | `IsometricLockedCamera` |
| Right mouse + drag | Pan the camera off the player | `IsometricLockedCamera` |

## Toolbar, tools and the world

| Input | Action | Where |
| :--- | :--- | :--- |
| 1 - 9, 0 (or numpad) | Select toolbar slot 1 - 10 | `HudBindings` |
| Mouse wheel | Cycle toolbar slot (not while Ctrl is held, the phone is open, or the game is paused) | `HudBindings` |
| Drag a toolbar slot onto another | Swap the two slots (the active slot follows its item); a plain click still selects | `HudBindings` |
| C (rebindable) | Open / close the contents window of the PLACED container under the cursor (within reach; it also has a Pick up button, which works on any box in a stack: the ones above fall down to fill the gap), else of the container in the active toolbar slot (or the first container in the toolbar): put items in, take them out. Containers (baskets) have a weight capacity and accept only certain categories; picked-up items they accept go into them first | `ContainerPanel` |
| Delete | Empty the active toolbar slot (the items are removed, not dropped) | `HudBindings` |
| Right click | Plant with the selected seed / harvest the plant in reach; with a felling tool (axe) in the active slot, click a tree: one click keeps swinging until it is down (walking away stops it) (a fruiting tree with ripe fruit, spawned or PLANTED, is picked by right-click with anything else in hand, one click picking every fruit in turn; the tree stays); dragging pans the camera instead | `PlantingController`, `ForestTrees` |
| Left click (placeable item selected) | First click brings out a translucent shadow that follows the square under the cursor (blue = valid, red = not); a second left click, or Enter, places it. Esc, walking, or choosing another slot puts the shadow away. Only items whose manifest sets `properties.placeable = true` do this. An identical stackable item stacks; when a stack is full or the item differs, the item goes in free space in the same 1 m square by its real size, and existing stacks slide over to make room if that helps; otherwise "no room" | `PlacementController` |
| Left click (an item that mounts on a building in the active slot: a breaker box, a wall light, a ceiling light) | First click brings out a translucent preview over the building under the cursor (a wall item sits flat on the wall, outside or inside as the item says; a ceiling light is aimed at the FLOOR: it hangs from the ceiling over the spot the cursor is on, with a line from the floor spot up to it; R turns it); blue = valid, red = not. A second left click, or Enter, mounts it. Esc, walking, or another slot puts it away. Only a finished building takes them; within 3.5 m. A ceiling light needs you inside | `AttachController` |
| Right click on a mounted item | Takes the breaker box or light down into the toolbar (within 4 m) | `AttachedObject`, `PlacementController` |
| Right click on a placed object | Pick up the top one of its stack into the toolbar (within placement reach); a container keeps what it holds. On a placed CONTAINER, when the active slot holds something, a right click instead moves items between them: what the slot holds goes in if the container accepts it (as many as fit by weight, the rest stays in the slot), otherwise, if the slot holds an item the container has and the slot is not full, items come out into the slot (as many as it takes). If the active slot holds a CONTAINER (a basket in hand), it is what that basket carries that moves: its contents go into the placed container, and when nothing can go in, the placed container's contents go into the basket (what it accepts and has room for; the rest stays). With an EMPTY active slot a right click picks the container up. A right click on a FINISHED STORAGE STRUCTURE (a grain silo) works the same way with the active slot (items it accepts go in by weight, matching items come out) and, with an empty slot, says how full it is and what is in it. A right click that drags still pans the camera. Hovering a placed object shows its name, how many are stacked and what a container holds (WAILA) | `PlacementController`, `WailaPanel` |
| Shift + right click on a construction site that has not been started | Remove it (only the dirt area): the structure item returns to the toolbar. Not possible once the first stage is built | `PlacementController`, `ConstructionSite` |
| P (over a construction site) | Pin that site's recipe list to the right of the viewport (it keeps updating as you gather materials; drag it by the left mouse button to move it, the spot is remembered); P again unpins it. The pin is remembered between sessions (it comes back when the site does); it is let go when the structure is finished or removed | `ConstructionHover` |
| Left click (fence item in hand) | Place a fence post; click the FIRST post to close the enclosure, Enter finishes an open line, right click or Backspace undoes the last post, Esc cancels. The 4 m square round the first post is a work site: materials dropped there are used first. The ped then walks the fence line building it section by section (a movement key or Esc stops it); posts and panels come out of the hotbar as each section is finished (docs/FENCES.md). With a GATE item in hand a left click on a built fence puts a gate in it; a right click on a gate opens or shuts it | `FenceBuilder`, `FenceRun` |
| Left click (path or road kit in hand) | Adds a control point; the route is a smooth curve through the points. Enter lays it, Backspace or right click undoes the last point, Esc cancels. The 4 m square round the first point is a work site for materials. The ped then walks the route laying it a section at a time (docs/PATHS.md) | `PathBuilder`, `PathRun` |
| Right click on a fence POST (axe in the active slot) | Takes down the post-to-post section nearest the cursor, gates in it included; a closed loop opens, an open run splits | `FenceBuilder`, `FenceRun` |
| Right click inside a finished building (within 2.4 m of an interior door) | Opens or shuts the nearest interior door: swings (`DoorHinge_<n>`), slides (`DoorSlide_<n>`: barn and stall doors) or rolls up (`DoorRoll_<n>`: garage doors); a click aimed at a big door reaches it from further away. The front door still takes the click outside | `ConstructionSite` |
| Right click on a wall or door of a building (a paint can, `building_paint_*`, in the active slot) | Paints what is under the cursor with the can's colour: a DOOR leaf; the SHUTTERS of a wall (all of that wall's); the OUTSIDE of a wall (all of that wall); or, inside, just the SECTION of the wall in that room (the stretch of wall face around the click, ending at corners, partitions, doorways and window openings). The can is not used up. Saved with the building | `ConstructionSite.TryPaint`, `StructureLook.Paint` |
| Right click on a berry bush (a shovel, tag `tool_shovel`, in the active slot) | Digs the bush up (within 4 m): it goes into the toolbar as its item (`bush_blueberry` ...) and is gone from the world, saved | `BerryBushes.TryDig` |
| Right click on open ground (a dug-up bush item in the active slot) | Plants the bush there (within 4 m, not in water, not within 0.6 m of a building or 0.9 m of another bush); the item is used up. A planted bush bears berries like a generated one; saved | `BerryBushes.TryPlant` |
| Right click on a CHIMNEY (finished building, within 4 m) | With firewood in hand (an item with `burn_minutes`) it goes into the fireplace; with a lighter (`lights_fires`, not used up) it lights the fire. The fire burns the fuel down in game time, lights the room and smokes out of the flue; the fuel and fire are saved with the building | `Fireplace`, `PlacementController` |
| Right click on a construction site | Build the site's current stage when the hover list shows everything there (materials within 4 m of the foundation, tools in the toolbar or placed there). Materials are used up, tools are not. The stage then takes 30 seconds: the ped walks to the materials, carries them to the site and works round the foundation on its own; pressing a movement key stops it and nothing is used up. On a FINISHED building it opens / closes its front door instead (within 4 m); the door is part of the walls, so open it to walk in | `PlacementController`, `ConstructionSite` |
| F (rebindable) | Drop the held item on the ground in front of you (one; Shift: the whole stack, up to 24). A container that holds things is placed as itself, keeping its contents | `PlacementController` |
| Right click on an item lying on the ground | Pick one up into the toolbar (within reach) | `PlacementController`, `WorldItem` |
| Left click (placeable item) over a pallet | The shadow lands ON the pallet, turned like it, in the pallet's free space (identical items stack up to their limit); a loaded pallet cannot be picked up until it is cleared | `PlacementController`, `PalletDeck` |
| R (Shift+R) | Rotate the shadow being placed 12.5 degrees clockwise (counter-clockwise); a STRUCTURE (construction site) turns in quarter turns so its walls stay on the grid | `PlacementController` |
| L (rebindable) | Player light: flashlight, then lantern, then off | `PlayerLight` |
| V (rebindable) | Cutaway view: while you stand inside a finished building, its roof and the walls between the camera and you stop being drawn (the window panes stay, so you can see where the windows are) (they still cast shadows) so the interior shows; V turns it on or off, remembered (default on) | `StructureCutaway` |
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
| Ctrl + click a phone launcher tile | Pin / unpin that app as a shortcut on the viewport (click the shortcut to open straight to it) | `PhoneController` |
| Right click the pinned-apps grip (the strip beside the shortcuts) | Switch the pinned shortcuts between a vertical column (grip on top) and a horizontal row (grip on the left); the choice is remembered | `PhoneController` |
| Esc | Close the top window (container contents, asset spawner, modal), the phone or a focused text field; only when none is open does it bring up the welcome menu | `HudBindings` |

## Debug and development

| Key | Action | Where |
| :--- | :--- | :--- |
| F1 | Show / hide the controls hints list down the left of the viewport (white text, keys in outlined boxes; starts hidden, remembered; the keys follow your rebinds) | `HintsPanel` |
| F2 | Toggle ground grid brightness | `GridBrightnessToggle` |
| F3 | Toggle the WAILA panel (what is under the cursor) | `WailaPanel` |
| F5 | Spawn the dev animal (Labrador) beside the player | `AnimalSpawner` |
| F6 | Toggle animal AI debug labels (behavior, needs, top scores) | `AnimalSpawner` |
| F11 | Hides the whole HUD (everything but the welcome menu) for a clean view, and shows it again; not saved | `HudVisibility` |
| F9 | Save the game now under its name (it also autosaves on the interval set in Settings > General > Saving, default 5 minutes, keeping the last 5) | `GameSaveManager` |

## Free keys (do not reuse the ones above)

F7, F8, F10 - F12, and every unlisted letter (G, H, T, Y, U, I, O, P, Z, X, V, B, N). Keep W A S D Q E F L Space Tab
Esc [ ] and 0 - 9 as they are.

## Not bound yet (clips exist, no key)

`PedController.Carrying` switches walking to the two-arm carry clip. The work clips (Chop_Tree_RT, Dig, Hoe,
Farm_PlantSeed_RT, Pet, Fixing_Kneeling_RT, Sleeping_RT) and the Drag upper-body clip are played by gameplay code
through `GlbClipPlayer.BeginAction` / `PlayUpperBody`; nothing triggers them from a key right now.
