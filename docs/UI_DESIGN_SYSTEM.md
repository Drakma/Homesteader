# Homesteader UI Design System

Status: decided 2026-10-02. Phases 1 and 2 of Section 11 are implemented (tokens, 6 px corners, shared controls on Settings and the HUD windows); the rest is migration work. Decisions: 6 px rounded corners everywhere except the HUD header strip; the amber accent edge stays on the left of cards and windows and fades into the normal border color; teal is the secondary accent; dark theme only for now; tooltips scale with the HUD Scale, the mouse pointer does not (yet).

Scope: every UI Toolkit surface (`Assets/Resources/HUDTree/*.uss`): the HUD, windows and modals, the welcome menu and Settings, toasts, and the phone (Steadify, Volt, Almanac and the rest). The sprite kit in `assets/hud_kit/` is covered in Section 12.

Companion rules that already exist and stay in force: CLAUDE.md section 1a (text vertically centered in fields, buttons centered both ways, one phone, sliders need an explicit height) and docs/HUD_TREE.md (document layout).

---

## 1. Why this document exists

The UI shares a palette and a font, so it reads as one game, but each window was built separately and the controls drifted. Counts from the stylesheets today (HudUI.uss, PhoneUI.uss, WelcomeMenu.uss and the small ones):

| Thing | Count today | Target |
|---|---|---|
| Distinct font sizes | 21 (8, 9, 10, 11, 12, 12.5, 13, 14, 15, 16, 17, 18, 19, 20, 24, 28, 30, 32, 34, 40, 44) | 7 |
| Distinct corner radii | 10 (0, 3, 7, 8, 9, 10, 12, 14, 15, 26) | 3 |
| Button classes | about 42, each defining its own height, border and hover | 6 shared |
| Close buttons | 4 different looks (Section 6.3) | 1 |
| Slider styles | 5 (square 14 px, round 18 px, round 14 px, vertical mini, scrollbar) | 1 base + 2 variants |
| Dropdown styles | 2 (different background, size and hover) | 1 |
| Text field styles | 4 (asset search, store search, admin field, mods search) | 1 |
| Checkbox styles | 2 (`window-toggle`, `settings-toggle`) | 1 |
| Hover colors for the accent | 4 (222,153,88 / 241,170,104 / 246,157,75 / 250,179,112) | 1 |

The goal is not a redesign. It is to pick one answer for each control, name it once, and make every window use it.

---

## 2. Principles

1. **Flat, dark slate with one amber accent.** Panels are slate, controls are darker wells, amber means "this is the thing you act on or the thing that is selected". Nothing else is amber.
2. **6 px corners.** Windows, cards, buttons, fields, dropdowns, checkboxes and slider thumbs have a 6 px corner radius (`--r`), a 1 px border and no shadow. The one exception is the HUD header strip across the top of the screen, which stays square. Fully round shapes are for things that are round by nature (dots, avatars, the phone transport buttons, pills).
3. **Hierarchy through weight and color, not size.** Seven text sizes are enough. Bold is for titles, not labels (Section 4).
4. **One control, one look.** A close button, a checkbox or a dropdown looks identical in every window. Variants are named modifiers (`--primary`, `--danger`), never a new class that re-states the whole control.
5. **State is always visible.** Every interactive element has distinct normal, hover, pressed, focus, checked and disabled looks (Section 7).
6. **Readable at 4K.** Sizes are in logical pixels and scale with the HUD Scale setting (Settings > Graphics > Interface). Minimum text size is 11 px, minimum click target is 22 px, preferred 28 px.
7. **No emoji and no system-font fallback glyphs.** Icons come from the HomesteaderHUD font (media glyphs, close mark) or sprites. A glyph the font lacks silently falls back to an emoji font and looks wrong.

---

## 3. Design tokens

Define these once as USS variables in a new `HUDTree/UITokens.uss`, imported by every document. Today the values are copied inline (rgb(224, 138, 60) appears 58 times).

### 3.1 Color

Surfaces (dark to light):

| Token | Value | Use |
|---|---|---|
| `--c-ink` | rgb(18, 22, 29) | Deepest: outer borders, text on amber, scrims at 75 percent |
| `--c-well` | rgb(26, 33, 43) | Inset wells: window headers, fields, slider tracks, unchecked boxes |
| `--c-field` | rgb(29, 36, 46) | Slightly lifted well for dropdown and input bodies on a well |
| `--c-panel` | rgb(43, 52, 66) | Window, card and modal bodies |
| `--c-raised` | rgb(61, 74, 92) | Borders, hover fill on slate buttons, dividers |
| `--c-rim` | rgb(92, 102, 117) | Top-edge highlight on windows, disabled borders |

Text:

| Token | Value | Use |
|---|---|---|
| `--c-text` | rgb(238, 242, 246) | Labels, values, body |
| `--c-text-strong` | rgb(255, 255, 255) | Text on hover |
| `--c-muted` | rgb(139, 150, 165) | Hints, secondary text, inactive icons |
| `--c-disabled` | rgb(92, 102, 117) | Disabled text |

Accent (amber):

| Token | Value | Use |
|---|---|---|
| `--c-accent` | rgb(224, 138, 60) | Primary fill, checked state, slider thumb, window titles, active tab underline |
| `--c-accent-hi` | rgb(241, 170, 104) | Hover, thumb and primary borders |
| `--c-accent-lo` | rgb(188, 112, 40) | Pressed |
| `--c-accent-tint` | rgba(224, 138, 60, 0.22) | Selected chip or row background |

Status:

| Token | Value | Use |
|---|---|---|
| `--c-danger` | rgb(198, 32, 38) | Danger fill on hover (close, exit, delete) |
| `--c-danger-text` | rgb(228, 92, 96) | Danger text and icon at rest |
| `--c-danger-border` | rgba(227, 83, 88, 0.4) | Danger border at rest |
| `--c-ok` | rgb(54, 196, 177) | Success, enabled, positive deltas |
| `--c-warn` | rgb(246, 157, 75) | Warning |

Rules: never write a literal rgb() in a component rule; use a token. Status colors are never used for decoration. Hover is one step lighter (surface) or the `-hi` accent; pressed is one step darker or the `-lo` accent.

### 3.2 Typography

Fonts (already defined as `--font`, `--font-medium`, `--font-bold`, `--font-italic`, `--font-bold-italic`): the HomesteaderHUD family. No other font is used.

Type scale (7 steps, replacing the 21 sizes in use):

| Token | Size | Weight | Use |
|---|---|---|---|
| `--t-display` | 32 | bold | Welcome title, big numbers |
| `--t-title` | 20 | bold | Dialog and card titles |
| `--t-window` | 15 | bold | Window header title (amber), large button text |
| `--t-body` | 13 | medium | Labels, values, buttons, list rows, field text |
| `--t-small` | 12 | medium | Dense lists, dropdown items, chip text |
| `--t-hint` | 11 | italic | Hints, captions, tooltips, badges |
| `--t-icon` | 18 | bold | Glyph-only buttons (media glyphs need the bold HUD font) |

Weight rules (this is the "labels are always bold" fix):

- **Labels, values and ordinary buttons: medium.** A label next to a control is `--font-medium`, 13 px, `--c-text`.
- **Bold only for:** window and dialog titles, section titles, primary buttons, active tab or chip text, and numeric emphasis in a stat. If everything is bold, nothing is.
- **Italic for hints only** (`--font-italic`, 11 px, `--c-muted`).
- **Section titles** inside a window: bold 13 px, `--c-accent`, 1 px bottom rule in `--c-panel` darkened. One style (today `window-section-title`, `settings-section-title` and `controls-group-title` differ).
- Letter spacing: 0.5 px on titles and primary button text only; none elsewhere.
- Text alignment: single-line text is vertically centered in its box (CLAUDE.md 1a). Left-aligned for labels and fields, centered for buttons.

### 3.3 Spacing and size

A 4 px grid. Allowed values: 2, 4, 8, 12, 16, 24, 32.

| Token | Value | Use |
|---|---|---|
| `--s-1` | 4 | Icon to label, inside chips |
| `--s-2` | 8 | Between controls in a row, field padding |
| `--s-3` | 12 | Between rows, card padding on small panels |
| `--s-4` | 16 | Window body padding, section gap |
| `--s-5` | 24 | Dialog padding |

Control heights (one set, used everywhere):

| Control | Height |
|---|---|
| Window header | 36 |
| Large button (menus) | 40 |
| Standard button, field, dropdown | 30 |
| Compact chip, tab | 26 |
| Checkbox box | 24 square |
| Slider hit area | 22 |
| Close button | 22 square |

### 3.4 Shape, border, elevation

| Token | Value | Use |
|---|---|---|
| `--r` | 6 px | Default for every window, card, button, field, checkbox and thumb. The HUD header strip is the exception (0) |
| `--r-pill` | half the height | Pills, transport buttons, dots, avatars |
| `--r-card` | 8 | Only the phone device skin and album art (the "device" exception, Section 6.12) |
| Border | 1 px `--c-raised` | Controls. Windows: 1 px `--c-ink` with a `--c-rim` top edge |
| Accent edge | 3 px bar on the left of a card or window, `--c-accent` at the top fading into `--c-raised` (the normal border color) at the bottom (`hs-accent-edge`, texture `Textures/accent_edge.png`) | Marks cards and windows (welcome card, Settings, loading card, HUD windows and modals); toasts still use a flat 2 px edge |
| Shadow | none, except toasts (`0 4px 12px` ink at 0.6) | Do not add shadows to controls |

### 3.5 Motion

Only toast slide and fade (0.35 s, ease-out-cubic) and a 0.1 s color transition on hover are allowed. Add the hover transition globally to interactive classes so it is uniform.

---

## 4. Do and do not (quick reference)

| Do | Do not |
|---|---|
| Labels in medium 13 | Bold labels |
| One amber for fills, one hi for hover | Invent a new orange for a hover |
| Close = one 22 px square with the close glyph | Red outline in one window, gray in another, a "Close" text button in a third |
| 30 px tall controls | 28, 32, 34 and 40 px mixed in one row |
| 6 px (`--r`) | Radius 3, 7, 10, 12, 15 for variety |
| Tokens (`var(--c-accent)`) | Literal rgb() values |
| Glyphs from the HUD font | Unicode symbols the font lacks (they render in an emoji font) |
| Disable with `--c-disabled` text and 0.55 opacity | Hide a control that cannot be used right now without saying why |

---

## 5. Layout patterns

- **Windows** (`.window`): header 36 px (`--c-well`, title amber bold 15, close button right), body padding 16, optional footer row with a 1 px top rule and right-aligned buttons, optional status bar and resize handle (asset spawner). Windows are draggable by the header; they never overflow the screen.
- **Modals** (`.modal` over `.window-shade`): same chrome as a window, centered, 75 percent ink scrim, one primary and one secondary button right-aligned, Escape closes.
- **Settings-style rows**: label left (min width 150, medium 13), control right, 6 px between rows. Toggle rows put the box at the right edge.
- **Forms**: label above field for long fields, label left for short ones. Never mix in one section.
- **Lists and tiles**: row height 30 (or 40 with an icon), hover = `--c-raised`, selected = `--c-accent-tint` with a 2 px accent left edge.
- **Tabs and nav** (Settings sidebar, market and almanac tabs): text only, `--c-muted` at rest, `--c-text` on hover, bold `--c-text` with a 2 px accent underline (or accent left bar for vertical) when active. No filled tab backgrounds.
- **Z-order**: map behind the phone; phone and mini player behind the wallpaper on load; toasts above windows; tooltips on top.

---

## 6. Components

Each entry gives the one spec. "Today" lists what exists so the migration knows what to replace.

### 6.1 Window, modal, card

- Body `--c-panel`, border 1 px `--c-ink`, top border `--c-rim`, radius 0, no shadow.
- Header `--c-well`, 36 px, 1 px bottom border `--c-raised`, left padding 14, right padding 8.
- Title: window 15 px bold amber (0.5 px spacing). Dialog title 20 px bold `--c-text`.
- Welcome card keeps its 2 px accent left edge and 92 percent opacity (it sits over the world).
- Today: `.window`, `.modal`, `.window-header`, `.welcome-card`, `.settings-card`, `.asset-spawner-window` repeat the same properties; fold them into `.hs-window`.

### 6.2 Buttons

Six variants, one base class `.hs-btn` (height 30, padding 0 14, border 1, radius 0, medium 13, centered text):

| Variant | Look | Use |
|---|---|---|
| default (secondary) | `--c-panel` fill, `--c-raised` border, `--c-text` | Cancel, neutral actions |
| `--primary` | `--c-accent` fill, `--c-ink` bold text, `--c-accent-hi` border | The one main action per window |
| `--danger` | transparent, `--c-danger-border` border, `--c-danger-text`; hover `--c-danger` fill, white text | Exit, delete, close |
| `--ghost` | no fill or border, `--c-muted` text; hover `--c-raised` fill | Toolbar and header actions, back arrows |
| `--chip` | 26 px, default look; `--active` = `--c-accent-tint` fill, accent-hi border, bold text | Filters, category chips, segmented choices |
| `--icon` | 28 px square, glyph at `--t-icon`, ghost look | Glyph-only buttons |

Large button (`--lg`): height 40, 15 px, 0.5 px spacing (welcome menu). Transport buttons on the phone are `--pill` icon buttons (40, 32 and 52 px) and are the one place circular buttons are correct.

Rules: one primary button per window; destructive actions are `--danger`; never color a button green or blue (the sprite kit has a green; the UI does not use it, success is shown with text and `--c-ok`).

Today: 42 button classes (`.action-btn`, `.welcome-btn`, `.admin-chip-btn`, `.admin-action-btn`, `.bank-action-btn`, `.market-tab-btn`, `.almanac-tab-btn`, `.container-panel-btn`, `.mod-toggle-btn`, `.settings-action-btn` and more) each with their own height (22 to 52), border and hover. Map each to a variant in the migration table (Section 11).

### 6.3 Close button

One spec: `.hs-close` = 22 x 22 px square, glyph from the HUD font at 14 px, `--c-danger-text` at rest with a `--c-danger-border` 1 px border and transparent fill, hover = `--c-danger` fill with white glyph and `--c-danger` border. It sits in the window header, 8 px from the right edge.

Variants allowed: a text "Close" button (`.hs-btn --primary`) in the footer of Settings is fine as an additional control; the header X remains.

Today's four looks:

| Where | Class | Look |
|---|---|---|
| HUD windows and modals | `.window-close-btn` | 22 px, red outline, red text, red fill on hover (the target spec) |
| Settings | `.settings-close-btn` / footer `Close` | Amber primary text button, no header X |
| Steadify mini player | `.steadify-mini-close` | 18 x 16, gray text, no border, different red on hover (170, 60, 50) |
| Sprite kit | `decor/close_x.png` | A slate X sprite, unused by the UI Toolkit windows |

The X character itself is a Unicode symbol in the UXML (`text="..."`). Add a close glyph to the HUD font like the media glyphs (assets/hud_kit/font/_add_media_glyphs.py) so it never falls back to a system font, then use that.

### 6.4 Checkbox / toggle

Unity's Toggle draws nothing useful in the runtime theme, so every part is styled. One spec, `.hs-toggle`:

- Box 24 x 24, `--c-well` fill, 2 px `--c-raised` border, radius `--r`.
- Checked: `--c-accent` fill, `--c-accent-hi` border, a check mark glyph (HUD font) in `--c-ink`, 16 px. A fill alone is not enough; the mark makes the state readable for color-blind players.
- Hover: border `--c-accent-hi`. Focus: 2 px `--c-accent` outline. Disabled: 0.55 opacity.
- The row label is part of the click target (label click toggles); the whole row is at least 30 px tall.
- With a built-in label (`<Toggle label="...">`) the label is `--font-medium` 13, `--c-text`, 8 px from the box.
- Selectors to style in Unity 6: `.unity-toggle__input` (box), `.unity-toggle__checkmark` (mark), and both `.hs-toggle:checked` and `.unity-toggle__input:checked` because the pseudo-state lands on different elements across versions.

A segmented on/off switch (Steadify shuffle and repeat, mods enable) is a separate component, `.hs-switch` (36 x 18 pill, knob 14), and is for instant settings; checkboxes are for options that are applied with the form.

Today: `.window-toggle` (18 px box) and `.settings-toggle` (28 px box), plus `.mod-toggle-btn` (enabled and disabled buttons). The first two merge; the third becomes `.hs-switch`.

### 6.5 Slider

`.hs-slider`, horizontal, one geometry:

- Hit area 22 px high (explicit height on the slider and `.unity-base-slider__drag-container`, with `justify-content: center`, or it collapses to zero; CLAUDE.md 1a).
- Track 6 px, `--c-well` fill, 1 px `--c-raised` border, radius 0; the filled part is not drawn by Unity, so add a second element or leave the track plain.
- Thumb 16 x 16, `--c-accent` fill, 1 px `--c-accent-hi` border, radius 0 (sharp, matches the windows); hover `--c-accent-hi`; dragging `--c-accent-lo`.
- Label left, min-width 150, medium 13. Value shown to the right in an input field (30 px) or as text; unit in the label ("HUD Scale (%)").
- Ticks or min/max labels (`.admin-scale-row`) in 11 px muted below the track.

Variants: `--round` (phone skin: thumb radius 8, track radius 3, used in Steadify seek and volume, `--c-raised` track), `--vertical` (mini player volume, 4 px track, 14 px thumb). Scrollbars are a separate component (Section 6.9).

Today: `.window-slider` (square 14 px), `.admin-slider` (round 18 px), `.steadify-seek-slider` / `.steadify-volume-slider` (round 14 px), `.steadify-mini-volume` (vertical). Unify to the spec plus the two named variants.

### 6.6 Dropdown

`.hs-dropdown`: height 30, `--c-field` fill, 1 px `--c-raised` border, radius 0, text 13 medium `--c-text`, vertically centered, left padding 8, a chevron glyph at the right. Hover: border `--c-accent`. Open: border `--c-accent`.

The popup (`.unity-base-dropdown__container-outer`): `--c-panel` fill, 1 px `--c-raised` border, items 28 px, hover `--c-raised`, selected item bold with an accent left edge. The popup is already styled once in HudUI.uss and applies globally; keep that.

Today: `.asset-category-dropdown` (170 x 30, 12 px, panel fill) and `.settings-dropdown` (200 wide, 14 px, field fill). Merge: width is set per place, everything else is shared.

### 6.7 Text field and search box

`.hs-field`: height 30, `--c-well` fill, 1 px `--c-raised` border, radius 0, 13 medium, padding 0 8, text and placeholder vertically centered (style the inner input and the placeholder element, CLAUDE.md 1a). Placeholder `--c-muted`. Focus: border `--c-accent`. Error: border `--c-danger`.

Numeric fields: the same, right-aligned digits, 70 px wide. Search box: the same with a magnifier glyph at the left and a clear glyph at the right.

Today: `.asset-search-input`, `.store-search-input`, `.mods-search-input`, `.admin-text-field` (four copies with small differences).

### 6.8 Progress and vitals bars

Track `--c-well` with a 1 px `--c-raised` border; fill color by meaning (health `--c-danger-text`, stamina and water `--c-ok`, accent for generic). Height 8 (inline), 14 (HUD vitals, with the icon at the left). Value text 12 px, right of the bar. No gradients or animation beyond width.

### 6.9 Scrollbar

6 px wide, `--c-ink` at 0.4 for the track, `--c-accent` at 0.45 for the thumb (0.85 on hover), radius 0, no arrow buttons, 6 px margin top and bottom. Today this is defined only for `.phone-app-scroll`; make it global so windows, lists and the Settings pages all match.

### 6.10 Tooltip

Not defined today (Unity's default shows). Spec `.hs-tooltip`: `--c-ink` fill at 0.95, 1 px `--c-raised` border, radius 0, padding 4 8, 11 px italic `--c-text`, max width 260, appears after 0.5 s, never covers its control. Use it for settings, locked or disabled controls (say why) and icon-only buttons.

### 6.11 Toast

Keep the current design: `--c-well` fill 0.95, 1 px accent border at 0.45, 2 px accent left edge, shadow, icon + title (bold 13) + message (12). The four kinds differ by the left edge and icon color only (info = accent, success = ok, warning = warn, error and severe = danger). The window and settings changes should not toast on routine toggles (for example the grid key).

### 6.12 Phone (device skin)

The phone is the one surface that may use rounded corners, because it is a physical object: bezel radius 26, app tiles radius 8 to 12, round transport buttons, album art radius 8. Inside an app, the controls (buttons, fields, sliders, toggles) still use the shared components; only the outer device shape and media chrome round. Apps use the same type scale; the app title bar uses `--t-window`.

### 6.13 Icons and glyphs

- Glyphs: close mark, check mark, chevrons, media (play, pause, next, previous, shuffle, repeat, speaker, pop-out) live in the HomesteaderHUD font. Any new glyph goes into the font with `_add_media_glyphs.py`, not into UXML as a Unicode character.
- Icons: 128 px sprites downscaled; UI icon boxes are 16, 24 or 32 px. Tint with `-unity-background-image-tint-color` for state.
- Never emoji.

### 6.14 Badges, chips and tags

Badge: 11 px bold, `--c-ink` text on `--c-accent` (count) or `--c-raised` (neutral), padding 1 6, radius 0 (or pill for counters). Chip: Section 6.2.

### 6.15 Dividers and spacing elements

1 px `--c-raised` line; section gap 16; do not use empty labels as spacers.

---

## 7. States

| State | Surface controls | Accent controls | Text |
|---|---|---|---|
| Normal | per spec | accent fill | `--c-text` |
| Hover | border `--c-accent-hi` or fill `--c-raised` | `--c-accent-hi` | `--c-text-strong` |
| Pressed | fill one step darker | `--c-accent-lo` | unchanged |
| Focus (keyboard) | 2 px `--c-accent` outline | same | unchanged |
| Checked or selected | `--c-accent-tint` fill or accent fill | accent | bold where it is a tab or chip |
| Disabled | 0.55 opacity, `--c-disabled` text, no hover | same | `--c-disabled` |
| Error | border `--c-danger` | n/a | message in `--c-danger-text` |

Pressed and hover must differ from normal by more than 8 RGB points so they read on a bad monitor.

---

## 8. Accessibility and scaling

- All sizes are logical pixels; the HUD Scale (50 to 300 percent, 200 by default at 4K) multiplies them. Do not hard-code absolute pixel positions that assume 1080p.
- Contrast: `--c-text` on `--c-panel` is about 11:1; `--c-muted` on `--c-panel` is about 4.2:1 (hints only, never for required text); `--c-ink` on `--c-accent` is about 6.8:1.
- State is never conveyed by color alone (check mark, bold, underline).
- Tooltips on every icon-only control.
- Keyboard: Tab order follows reading order, Escape closes the top window, Enter activates the focused button. Key assignments are listed in docs/CONTROLS.md.

---

## 9. Naming and structure

- Shared classes use the `hs-` prefix (`hs-btn`, `hs-btn--primary`, `hs-toggle`, `hs-slider`, `hs-dropdown`, `hs-field`, `hs-close`, `hs-window`, `hs-tooltip`). Block-element-modifier: `hs-btn`, `hs-btn--danger`, `hs-btn__icon`.
- Feature classes keep their own prefix (`steadify-`, `bank-`, `asset-`) but only for layout (flex direction, widths, margins); they must not restate color, border, font or hover of a shared control.
- Files:
  - `UITokens.uss`: the variables in Section 3 (colors, type, spacing, radius).
  - `UIControls.uss`: every `hs-` component in Section 6.
  - Existing files keep layout only and import both.
- A control in UXML is `class="hs-btn hs-btn--primary"`, plus an optional feature class for position.

---

## 10. Per-window checklist (definition of done)

For any new or touched window:

1. Uses `.hs-window` chrome with a 36 px header and the shared close button.
2. Every button is an `hs-btn` variant; one primary.
3. Labels are medium 13, section titles bold amber 13, hints italic 11 muted.
4. Spacing values are on the 4 px grid; control heights come from Section 3.3.
5. Checkboxes, sliders, dropdowns and fields are the shared components with visible hover, focus and disabled states.
6. No literal rgb() or font sizes outside the token list; no radius other than `--r` (phone shell excepted).
7. No emoji; any glyph is in the HUD font.
8. Text in fields and buttons is vertically centered (CLAUDE.md 1a).
9. Checked at 1080p and 4K with HUD Scale 100 and 200 percent; nothing clips or overlaps.
10. Tooltip on icon-only and disabled controls.

An audit script (`tools/audit_ui.py`, to write) can enforce 6 mechanically: grep the USS files for `rgb(` outside UITokens.uss, font sizes not in the scale, radii not in the set, and new `*-btn` classes.

---

## 11. Migration plan

Order is chosen so each step is visible and low risk.

| Phase | Work | Result |
|---|---|---|
| 1 | Create `UITokens.uss`; add it to every UIDocument; replace literal colors and sizes in HudUI.uss, WelcomeMenu.uss, PhoneUI.uss with tokens (mechanical, no visual change) | One place to retune the look |
| 2 | Build `UIControls.uss` with `hs-close`, `hs-toggle`, `hs-slider`, `hs-dropdown`, `hs-field`, scrollbar, tooltip; switch Settings (the newest page) and the HUD windows to them | Checkbox, slider, dropdown and close become uniform where players look most |
| 3 | Add the close and check glyphs to the HUD font; swap Unicode characters in UXML | No fallback glyphs |
| 4 | Collapse the button classes into `hs-btn` variants window by window (Section 6.2 table below) | One button system |
| 5 | Phone apps: shared controls inside, device skin outside; type scale applied | Phone matches the HUD |
| 6 | Remove dead classes (`WindowPanel.uxml` is unreferenced; the duplicate `window` and `modal` blocks), add `audit_ui.py` to CI or a pre-commit step | Stays uniform |

Button class mapping (starting point):

| Existing class | New |
|---|---|
| `action-btn--primary`, `welcome-btn--primary`, `admin-action-btn`, `bank-action-btn` | `hs-btn hs-btn--primary` |
| `action-btn--secondary`, `welcome-btn`, `settings-action-btn`, `container-panel-btn` | `hs-btn` |
| `welcome-btn--exit`, `window-close-btn`, `admin-vital-zero-btn` | `hs-btn hs-btn--danger` (close: `hs-close`) |
| `admin-chip-btn`, `asset-category-chip`, `market-tab-btn`, `almanac-tab-btn`, `settings-nav-btn` | `hs-btn hs-btn--chip` (tabs: underline variant) |
| `phone-back-btn`, `header-settings-btn`, `steadify-popout-btn`, `steadify-mini-btn` | `hs-btn hs-btn--ghost hs-btn--icon` |
| `steadify-transport-btn*` | `hs-btn hs-btn--icon hs-btn--pill` |
| `mod-toggle-btn--*` | `hs-switch` |

Risks: UI Toolkit selectors for built-in controls differ between Unity versions (the toggle's `:checked` lands on different elements), so each shared control needs one visual check in the editor after the change; the HUD font has to be regenerated and re-imported before the glyph swap.

---

## 12. Relationship to the sprite kit

`assets/hud_kit/STYLE_GUIDE.md` and `palette.json` describe a different look: 8 px rounded corners, a 2 px near-black border, and slate, amber (#784b06) and green button bodies. The shipped UI Toolkit styles do not use those sprites; they use flat squares with the colors in Section 3.1. Treat this document as canonical for UI Toolkit. Either retire the sprite kit's guide or update it to point here, so two contradictory style guides do not both claim to be the source of truth. The kit remains useful for the toolbar slots and the baked header strip, which are still sprites.

---

## 13. Decisions (2026-10-02)

1. Corners: 6 px rounded everywhere except the HUD header strip.
2. Accent: amber stays the primary accent and sits on the left edge of cards and windows, fading into the normal border color. Teal (`--c-secondary`, `-hi`, `-lo`) is the secondary accent for information, success, enabled states and positive values (`hs-btn--teal`).
3. Theme: dark only for now. Tokens keep a light theme possible later.
4. Scaling: tooltips scale with the HUD Scale setting (they are drawn inside the panel). The mouse pointer does not scale, yet.

## 14. Implementation status

Done:
- `UITokens.uss` plus `tools/sync_ui_tokens.py` (copies the tokens into each document's `:root`, replaces literal colors and zero radii with tokens).
- `UIControls.uss`: accent edge, close, buttons, checkbox, slider, dropdown, field, scrollbars, tooltip.
- Buttons: every older per-window button class (about 35) now takes its look from the shared groups via `tools/ui_migrate_buttons.py`; class names in UXML and C# did not change, and the feature stylesheets keep only layout. The groups are neutral, primary (amber), danger, teal, ghost and active.
- Type scale: all font sizes snapped to 11, 12, 13, 15, 18, 20 and 32.
- Settings and the HUD windows use `hs-close`, `hs-toggle`, `hs-slider`, `hs-dropdown`; the dead `WindowPanel.uxml` is removed.
- `tools/audit_ui.py` reports anything off the system (add `--strict` for a pre-commit hook).

Intentionally left as is:
- Phone device skin: its larger radii (10 to 28 px) and the Steadify media buttons (`steadify-transport-btn`, `steadify-mini-btn`) keep their own round shapes.
- Toasts keep a flat colored left edge per kind (a gradient edge cannot be recolored per kind).
- The close button is a plain X and the check mark is a drawn image (`Textures/check.png`); a font glyph for each would need the HUD font regenerated.
- Remaining literal rgb() values are one-off colors (the phone's brighter orange, media greens, the almanac purple); fold them into tokens as each screen is redesigned.
