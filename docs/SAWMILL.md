# The stationary sawmill

Code: `Assets/Scripts/Growth/Sawmill.cs`, the choice menu in `HudBindings.ShowChoiceMenu`. Model: `tools/make_sawmill.py` (+ `tools/sawmill_pictures.py`). Item: `vehicle_sawmill_stationary`
(`properties.sawmill: true`, placeable).

## Using it

1. Place the sawmill (an 850 kg machine, 6.4 m long, 1.4 m wide and 1.8 m high: the track is the length of a 4 m log and a metre each end, the rest is kept slim).
2. Left click it with an UNCUT LOG in the active slot (`mat_log_<species>_uncut_long / _medium / _small`): the log lies on the cradles. One log at a time. Shift + right click takes it off again.
3. Right click the sawmill. A menu asks what lumber to cut and shows how many pieces each type gives from THIS log.
4. The player walks round to the BACK of the sawmill (the side opposite the lumber) and stands at the start of the track while the saw carriage runs along the log three times, back to the start after each, with the blade turning. The uncut log shrinks with each pass and is gone at the end.
5. The lumber comes out as strapped BUNDLES, each in the next free place along the front of the sawmill: the pieces are made up into the biggest bundles they make, then the next size, (the packs the equivalencies give the lumber: 2x4 studs 40 and 20 to a bundle; 2x6 boards 25 and 10; 4x4 posts and 2x8 joists stacks of 20 and 10; 2x10 joists 15 and 6). What does not make a bundle is left as loose pieces: they fill the stacks of that lumber already there (any within 5 m of the machine, up to 20 high, turned like the stack) and the rest starts a new stack. If the bundles would not fit in the lumber area the cut does not start: take lumber away.

The sawmill is picked up like any placed thing (Shift + right click) while its track is empty.

## What a log gives

A piece is no longer than the log, and a log gives pieces in proportion to its volume (a medium log about 0.64 of a long log's pieces, a small one is too short for lumber).

| Lumber | Item | Long log (4.0 m) | Medium (2.4 m) | Shortest log |
|---|---|---|---|---|
| 2x4 stud | `lumber_stud_2x4` | 20 | 12 | 2.4 m |
| 2x6 board | `lumber_board_2x6` | 14 | 8 | 2.4 m |
| 4x4 post | `lumber_post_4x4` | 10 | 6 | 2.4 m |
| 2x8 joist | `lumber_joist_2x8` | 10 | - | 3.6 m |
| 2x10 joist | `building_lumber_joist_2x10` | 8 | - | 4.0 m |

The table is `Sawmill.Types` in the code (not yet in the asset kit). The lumber items carry `stacking_limit: 20` so identical pieces stack.

## The model

Three parts found by name: `Frame` (bed, beams, rails, legs), `SawCarriage` (travels along the track from its home end to the mirror of it) and `SawBlade` (a child of the carriage; spins about
its own z). The bed is 6 m: an uncut log of 4 m with a metre of clear track at each end. Painted pictures give the detail (maker's plate, engine cover, fuel tank label, hazard
stickers, the ruler along the bed).

## Fuel

The sawmill runs on GASOLINE. It is a liquid container (`liquid_container`: 20 L, accepts `liquid_gasoline`), so its tank shows as "Holds" in the look-at panel and in ResView's fuel list, and the fuel is saved and travels with it like any tank's. Right click it with a container of gasoline in hand (a gas can) to pour what fits in. A cut burns 0.5 L (`Sawmill.FuelPerCutL`), taken when the cut starts; with less than that in the tank the menu does not open ("out of gasoline").

## The window

Right click asks in a floating, draggable window built to the per-window checklist of `docs/UI_DESIGN_SYSTEM.md` (section 10): the `window` chrome with the accent edge and a 36 px header (amber title, the shared `hs-close`); a gauge (label medium 13, an 8 px bar) for the fuel; a hint in italic 11 muted; the section title `CUT THE LOG INTO` (bold amber 13); and one 40 px list row per lumber type (icon, name in medium 13, hover `--c-raised`) with a standard `hs-btn` "Cut" (30 px, centred). A button that cannot be pressed (no gasoline) is disabled and says why in its tooltip. It does not block the game; X, Escape or walking away closes it, and it remembers where it was left (`HudBindings.ShowChoiceMenu`). Its `choice-*` classes in HudUI.uss are layout and the row hover only, from tokens.

## Not done yet

Species do not matter: lumber is lumber. The yield table is in code, not the asset kit.

The sawmill is fixed in place for the tidy-up (`WaterTap.IsFixed`): it is never carried into the lines.
