# Movable windows

With a wrench in the active slot, Shift + right click on a window of a finished building picks it up (a plain right click only says what the keys do). It slides along its own wall with the cursor (never over a door, another window or a corner), the hole in the wall follows it, a left click sets it down and Esc (or a right click) puts it back. The height stays where it is; the sill is 1.05 m, above a kitchen counter (0.92 m). Each window's offset is saved with the building (`SavedSite.windowShifts`).

## How it is made

- **The models** (`tools/make_structure_stages.py`, `make_house_stages.py`, `make_building_stages.py`): in the finished stages (complete and finishings) the walls are SOLID under their windows. Each window is its own objects, `WindowFrame_<k>` (trim, sill, muntins, shutters and a lining through the wall INSIDE the opening) and `WindowGlass_<k>` (the pane), and an empty `WinSpec_<k>_<wall>_<u0>_<u1>_<z0>_<z1>` (millimetres: the opening along the wall in the file's x or y, and its height above the ground). `door_only`, `movable_window` and `base.next_window` do it. The earlier stages (framing, walls) keep their openings. Windows with no spec (the glass of garage doors, the gable vent) stay as they are (`WindowGlass`).
- **The hole** (`Growth/StructureWindows.cs`, on the model's root): each wall's meshes are copied with every triangle clipped against the window rectangles, so the hole is real for the eye, for shadows, for rays (paint, rooms, the cursor) and for the colliders. The original meshes are kept; moving a window re-cuts only its wall. No shader is involved, so the draw cost is the same as before (one mesh per wall part).
- **Other systems:** the cutaway hides a window's frame and pane with its wall (`StructureCutaway`, entry kinds 1 and 5); paint skips window objects (`ConstructionSite.Ignorable`); the pane casts no shadow (`ConstructionSite.ShowModel`).
- **Rule:** a window keeps `ReachM` (4.5 m) of the player, `CornerMarginM` from the end of its wall, `NeighbourMarginM` from other windows and `DoorMarginM` from doors (`StructureWindows.Allowed`).

Regenerate a structure with its generator, then `python tools/fix_structure_overlaps.py` twice and `python tools/package_catalog_as_mods.py`.

## Muntins, taking a window out, swapping and putting one in

Every window in every finished building (the L-shaped house too: its cross wing's walls are `Wall_*@B` and its windows' specs say `front@B` and so on) acts the same:

| With | Right click on a window | Right click on a bare wall |
|---|---|---|
| a wrench + Shift | picks it up and slides it along its wall (left click sets it down, Esc puts it back) | |
| a wrench + Ctrl | takes it out: the wall closes and the window goes into the toolbar as its item | |
| a window item (`building_window_double_hung`, `_picture`, `_slider`) | swaps it for the held type (the old one goes into the toolbar) | puts one in where the cursor is, at the building's sill height |

- **Putting one in:** with a window item (`building_window_*`) in hand, a LEFT or right click on a wall of a finished building puts it in (on a window: swaps it); a window item is never set on the ground.
- **Muntins** are part of the window ITEM: every window type comes in five looks: plain, two panes, four panes (the base item `building_window_<type>`, a cross, the default), six and eight (ids end `_plain`, `_panes2`, `_panes6`, `_panes8`; `tools/make_window_variants.py`). No key changes the bars: click a window with a different window item in hand and it is swapped. The patterns (`StructureWindows.MuntinGrid`): 0 plain, 1 one vertical bar, 2 a cross, 3 two vertical bars and a horizontal one, 4 three vertical bars and a horizontal one. Old saves keep their number (0-3 meant the same).
- **Types:** a window built by the game (`StructureWindows.BuildFrame`) is a frame with casing, a sill and a lining through the wall, a pane, and the bar of its type (a meeting rail for the double-hung, a meeting stile for the slider), in the building's own trim material and the glass material of its windows. It keeps its sill and is never taller than the head of the building's tallest window (`_headLimit`); it must fit: off corners, doors and other windows (`FitCentre`), else "no room".
- **Items:** a swapped or removed window comes back as the item of its kind (the nearest of the three by width when it was built into the model). A full toolbar stops it.
- **Save:** `SavedSite.windowStates`, one string per window: `index|wall|centre|sill|type|muntins|removed|baked`. A put-in window has an index from 1000.
- **Models:** `tools/make_l_house.py` rewrites each wing's WinSpec empties into the whole house's frame (`respec`) and keeps the windows' objects uncut and unrenamed.

## Shutters

`building_window_shutters` (assets/building, `tools/make_window_shutters.py`) is a pair of louvred shutters, a window property like the bars. Right click (or left click) a window of a finished building with the item in hand: the pair is fitted, centred on the window (0.38 m each, 4 cm proud of the wall, a hand of room beside it: not within 0.49 m of the ends of the wall). A wrench and a plain right click on a window with shutters takes them off into the toolbar; taking a window out takes its shutters off with it; swapping a window keeps them. The shutters a building came with (the front windows of the farmhouse and the L-shaped house) are the model's own and are shown or hidden the same way (`Win.BakedShutters`); the ones fitted are built in `StructureWindows.Refresh` (`WindowShutter_<index>`, the building's shutter material or a blue-grey one, with the louvre picture of `StructureLook`). They slide with the window. Saved as the 9th field of `SavedSite.windowStates` (`...|baked|shutters`); a save from before keeps what the model came with.

## Window item models

Every window item has the model of its own pattern of bars (`tools/make_window_pattern_models.py`: 3 types x 5 patterns, GLB and icon). A sliding window is two windows side by side: the left sash in front, the right one behind, each with its own frame and its own grid of bars (in the game `StructureWindows.SashFrames` and `WindowBars` do the same for a slider that was put in or swapped).
