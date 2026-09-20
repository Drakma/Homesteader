# Homesteader HUD Layout

The HUD is a 1920×1080 screen overlay built from `assets/hud_kit/sprites/`
plus animations/data bound at runtime. Coordinates below are in pixels
on the 1920×1080 base canvas. The render module (`runtime/render.py`)
is the canonical reference for where each element sits.

## Screen regions

| Position        | Element               | (x, y)    | size           | Backing sprite          |
|-----------------|-----------------------|-----------|----------------|-------------------------|
| Top-left        | Player status panel   | (96, 16)  | 256 × 96       | `panel_large_dialog`    |
| Top-center      | Season/day/time panel | (832, 16) | 256 × 96       | `panel_large_dialog`    |
| Top-right       | Held-asset panel      | (1568, 16)| 256 × 96       | `panel_large_dialog`    |
| Below center    | Time-speed chips      | (832, 128)| 256 × 32       | (chrome-less chips)     |
| Bottom-center   | Tool bar (10 slots)   | (76, 940) | 1768 × 128     | `slot_1x1`, `slot_1x1_active` |

The toolbar is 1768 px wide and centered around the canvas X axis.
At 96 px slots + 56 px spacing, 10 slots take `(10 * 96) + (9 * 56) = 1464`.
The toolbar rect is wider to allow 1×2 wide slots to drop in; current
layout uses only 1×1.

## Vital chips (top-left panel)

Four vital chips render as colored rounded squares 36×36 px each, with
their level value (0-100) printed to the right. Vital ids and colors:

| VitalId       | Glyph | Default fill color                       |
|---------------|-------|-----------------------------------------|
| Wellness      | W     | green (level > 0.7), amber, red         |
| Stamina       | S     | green (level > 0.7), amber, red         |
| Hydration     | H     | green (level > 0.7), amber, red         |
| Battery       | B     | green (level > 0.7), amber, red         |

The 0.7 / 0.4 thresholds define when each color applies. Vital icons
overlay the panel sprite and are positioned via pad=16, icon_w=36,
spacing=26, computed deterministically in `render_player_status`.

## Season/Day/Time panel (top-center)

Three lines stacked vertically at x=rect.x+16:

| Line     | Source                                 | Color                |
|----------|----------------------------------------|----------------------|
| Season   | `phase == DAY ? Summer/Winter/Spring/Autumn : same` | text color (default slate) |
| Day      | `day_of_year` integer                  | text color           |
| Time     | `cycle_minute` (0..40) formatted       | amber if DAY, green if NIGHT |

The day cycle is split **2 phases × 20 minutes each** = 40 minutes per
in-game day. Reference: `runtime/time_system.py: Cycle of 40 minutes`.

## Held-asset panel (top-right)

Three lines stacked vertically at x=rect.x+16:

| Line   | Source                                  | Color  |
|--------|-----------------------------------------|--------|
| Holding | literal "Holding"                       | slate  |
| Name    | `state.held_asset_id`                   | amber  |
| Count   | `state.toolbar[selected_slot].count` if non-empty | slate  |

`state.held_asset_id` mirrors the currently-selected toolbar slot. The
runtime makes them stay in sync (`select_slot` updates both).

## Speed controls (below center panel)

Four chrome-less chip buttons at (832, 128). Each chip is `chip_w = rect.w / 4 = 64`
wide and `rect.h = 32` tall.

| Chip | `Speed` enum | Idle bg          | Active bg         | Idle text   | Active text |
|------|--------------|------------------|-------------------|-------------|-------------|
| 0    | `PAUSE`      | (24, 32, 44, 200)| (40, 50, 64, 220) | slate       | amber       |
| 1    | `SPEED_1X`   | (24, 32, 44, 200)| (40, 50, 64, 220) | slate       | amber       |
| 2    | `SPEED_3X`   | (24, 32, 44, 200)| (40, 50, 64, 220) | slate       | amber       |
| 3    | `SPEED_5X`   | (24, 32, 44, 200)| (40, 50, 64, 220) | slate       | amber       |

Pressing any chip calls `ts.set_speed(speed_enum)`.

## Toolbar (bottom-center)

10 hotbar slots at `rect = (76, 940, 1768, 128)`. The slots are
centered along X.

Slot positions (left-top, in pixels): `start_x + i * (96 + 56)` for
`i = 0..9`. Where `start_x = rect.x + (rect.w - content_w) / 2`,
`content_w = 10 * 96 + 9 * 56 = 1464`.

Empty slots render with `slot_1x1` and no inner label. Filled slots
render with `slot_1x1` plus a stack count label (`xN`) in the bottom-
right corner if `count > 1`. The *currently-selected* slot uses
`slot_1x1_active` (with the amber inset border) instead.

## Time system

`runtime/time_system.py` implements the 20+20 minute day:

```
Spring (1..30)  |  Summer (31..60)  |  Autumn (61..90)  |  Winter (91..120)
120-day year repeating.
```

A real-time second maps to **1 game minute at 1×**. At 3× it's 3 game-minutes
per real-second; at 5× it's 5. Pause stops the clock.

The default initial state in `_render_hud.py` puts the clock at "Summer,
Day 42, 5 minutes into the DAY phase, speed 1x". That matches the
preview at `assets/hud_kit/preview/preview_hud_full.png`.

## Runtime policy

- `HudState` is a singleton. Single source of truth for everything the
 HUD reads from. Don't poke the panel directly; mutate state.
- Vital stamps are themed (`> 0.7 green`, `> 0.4 amber`, `else red`).
 The thresholds live in `render_player_status` and exist as a small
  tunable.
- Season/day-rolling is centralized in `TimeSystem.phase()` and
 `TimeSystem.season()`. Days roll by 1 at midnight, not by year-end.

## Renderer invocation

`runtime/render_full(canvas_size, state, ts)` is the only place
panels are composited. `runtime/_render_hud.py` is the demo driver.

## Future work

1. Replace text-only chip glyphs with real icon lookups from the
 catalog (`assets/structures/.../icon.png`, etc.).
2. Wire `HudState` updates to gameplay (consumable items depleting,
 stamina drain from running, etc.).
3. Hook `TimeSystem.tick` to the game's frame loop.
