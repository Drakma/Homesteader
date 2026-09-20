# Homesteader HUD Kit — Style Guide

Canonical look-and-feel rules for all HUD chrome: panels, buttons,
toolbar slots, dividers, status windows, and decorative elements.

The kit at `assets/hud_kit/sprites/` is the single source of truth.
Existing PNGs in `assets/hud/<item>/<item>.png` were measured to
produce this guide; future HUD work should reuse the kit rather
than draw pixel-by-pixel from scratch.

## 1. Canvas

Every sprite in the kit is `128x128 RGBA` with these constraints:

- Perimeter alpha = 0. The four edges are fully transparent.
- Subject sits within an interior `104x104` box (12 px margin on
  every side).
- Subject does not exceed 104 px on its longest axis.

This matches the global icon standard per `AGENTS.md` §4 and makes
the sprites safe to composite into Unity spritesheets without
clipping or scaling artifacts.

## 2. Color families

Five canonical body colors. The role each plays is fixed; do not
swap colors across roles. Hex values live in `palette.json`.

| Role                | Hex       | Where                                          |
|---------------------|-----------|------------------------------------------------|
| `body_dialog`       | `#18202c` | Main dialog background, drawers, modal panels. |
| `body_status`       | `#0e1b20` | Deep-context status windows.                   |
| `body_button_slate` | `#253142` | Neutral button body (cancel, dismiss).         |
| `body_button_amber` | `#784b06` | Call-to-action button (Proceed, Confirm).      |
| `body_button_green` | `#1e4620` | Success/affirm button (Yes, Apply, Save).      |

The "highlight" along the top-left edges of every shape is achieved
by adding `+12` to each RGB channel of the body color (clamped at
255). That's the only allowed elevation. Do not invent new shadows
or glows.

## 3. Borders and corners

Every panel and button gets:

- **2 px outer border**, color `#0a0e15`. The border sits inside the
 104x104 content box so it doesn't touch the perimeter alpha=0 zone.
- **8 px corner radius**. All shapes are rounded rectangles. No
  chamfered squares, no notches, no asymmetric rounding.

## 4. Components

The kit ships these sprite families. Names follow
`<role>_<variant>.png`:

### 4.1 Panels (`sprites/panels/`)

- `panel_compact_dialog.png` — small modal/toast panel.
- `panel_large_dialog.png` — full-screen-level modal.
- `panel_drawer.png` — side drawer; the long edge is on the right.
- `panel_modal.png` — generic centered modal.
- `panel_toast.png` — bottom corner notification.

### 4.2 Buttons (`sprites/buttons/`)

Twelve sprites, three colors × four states:

| Color      | Files                                       |
|------------|--------------------------------------------|
| slate      | `btn_slate_normal/hover/pressed/disabled`  |
| amber      | `btn_amber_normal/hover/pressed/disabled`  |
| green      | `btn_green_normal/hover/pressed/disabled`  |

State affordances:

- `normal` — body color + standard border.
- `hover` — `+8` to each body RGB channel, lighter border (`#1a1f29`).
- `pressed` — `-8` to each body RGB channel, lighter border.
- `disabled` — body greyscale `0.55x` and alpha through the body
  is reduced to `0.55x`.

### 4.3 Toolbar slots (`sprites/toolbar_slots/`)

- `slot_1x1.png` — single rounded rectangle for a hotbar cell.
- `slot_1x1_active.png` — same shape with a 2 px `#c19a3c` (amber-bright)
  inset border to mark the selected slot.
- `slot_1x2.png` — wide slot (1x2 cells).

### 4.4 Status dividers (`sprites/status_windows/`)

- `divider_h.png` — horizontal 64-px-wide divider line on transparent
  rim.
- `divider_v.png` — vertical 64-px-tall divider.
- `corner_tl.png`, `corner_tr.png`, `corner_bl.png`, `corner_br.png`
  — 32×32 quarter-rounds for framing exterior edges of status windows.

### 4.5 Decoratives (`sprites/decor/`)

- `close_x.png` — small X glyph, slate color.
- `glow_accent.png` — small accent dot.
- `separator_dot.png` — bullet between items.
- `double_divider.png` — paired 1-px lines.

## 5. Naming, manifest, and validate

- Every sprite is named using only the role+state (no dashes, no
  version suffixes, no extra metadata in filenames).
- `hud_kit.json` is the catalog. Each entry includes `id`, `display_name`,
  `path`, `anchor` (top-left, center, top-center, mid-left, etc.),
  `vec_dims` (the content-box dimensions in pixels), `palette_role`,
  and `usage`.
- Run `_validate_palette.py` to drift-check the kit sprites match
  `palette.json`. Drift > `expected_sample_delta_per_channel_max`
  (`2`) is a hard violation.
- Run `_build_sprites.py` to regenerate (idempotent) when needed.

## 6. Composition

`compose_preview.py` builds sample composites:

- `preview_window.png` — a panel above a row of three buttons.
- `preview_toolbar.png` — a 5-slot toolbar with the 3rd slot active.
- `preview_status.png` — a status window with a divider and four
  corner accents.

Composites are visual smoke tests. They should be readable as a
HUD when canonical. Any obvious imbalance (colors don't match,
borders don't match, content shrinks too far) is a bug.

## 7. Future additions

When adding to the kit:

- Add the new sprite to `hud_kit.json` with proper `anchor` and
  `usage` fields.
- Add an expectation in `_validate_palette.py` for its body hex.
- Re-render via `_build_sprites.py` and check the composite.
- Reference the canonical hex codes — never invent new ones.
