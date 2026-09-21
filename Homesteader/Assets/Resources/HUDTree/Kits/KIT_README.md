# HUD Kit Art in Unity (`Atlases/Kit/`)

This directory is the Unity-side landing zone for art built by
`assets/hud_kit/`. It is **additive** — it does not modify the
existing live HUD chrome. Apply it by enabling the
`_enableKitOverlay` flag on `HudUIBuilder` (or `_enableKitOverlay` on
`HudSceneBootstrap`).

## Files

| Path | Role |
|---|---|
| `Atlases/Kit/button_atlas_kit.png` | 200x896 (auto-resized to 256x1024 by Unity import); 4 colors × 4 states per the existing button matrix in `HudUI.uss`. |
| `Atlases/Kit/vital_atlas_kit.png` | 128×512. Rows: thirst, hunger, stamina, wellness. |
| `Atlases/Kit/resource_atlas_kit.png` | 128×512. Rows: water, electricity, bandwidth, fuel. |
| `Atlases/Kit/slot_atlas_kit.png` | 128×384. Rows: slot_1x1, slot_1x1_active, slot_1x2. |
| `Atlases/Kit/decor_atlas_kit.png` | 128×512. Rows: close_x, glow_accent, separator_dot, double_divider. |
| `Atlases/Kit/speed_controls/*.png` | 64×64 standalone chip sprites (PAUSE/1X/3X/5X/9X). |
| `Atlases/Kit/panels/*.png` | 128×128 standalone panel sprites (panel_compact_dialog, panel_large_dialog, panel_drawer, panel_modal, panel_toast). |
| `Atlases/Kit/status_windows/*.png` | 128×128 divider/corner sprites. |
| `../HudUI_kit.uss` | Companion style sheet: buttons, vitals, resources, slots, decor. Mounted as a sibling sheet on the HUD root when the overlay flag is on. |
| `../HUDOverlay_kit.uxml` | Overlay tree: `KitVitals`, `KitResources`, `KitDecor`. |

## Source

The PNGs here are baked from `../../../assets/hud_kit/sprites/`.

To re-bake (e.g., after editing kit sprites):

```powershell
python tools/bake_kit_atlases.py
```

The script is **idempotent**: it re-emits the same atlas files. After
running it, trigger `AssetDatabase.Refresh()` (Tools > HUD > Refresh
AssetDatabase, or the menu item) so Unity re-imports the new PNGs.

## Why this is a separate folder

The existing `Atlases/` content is procedural painting emitted by
`Assets/UI/bake_atlases.py` (single-row button rectangles, etc.). The
kit brings hand-designed chrome with palette discipline from
`assets/hud_kit/palette.json` and a 16×24 design grid. They live
side-by-side so the existing HUD keeps working and the kit overlay
can be enabled or disabled.

## Custom font

`assets/hud_kit/font/` ships the Homesteader HUD typeface - hand-drawn
on a 16x24 design grid, not based exactly on Segoe UI or Fira despite
structural inspiration. The font is built by fontTools during bake.

### Family

Five TTF files (one per face), all monospaced at 16 px design width:

  - `homesteader_hud.ttf`             Regular     weight 400
  - `homesteader_hud_medium.ttf`      Medium      weight 500
  - `homesteader_hud_bold.ttf`        Bold        weight 700
  - `homesteader_hud_italic.ttf`      Italic      weight 400 + -10° shear
  - `homesteader_hud_bold_italic.ttf` Bold Italic weight 700 + -10° shear

87 glyphs in each file: ASCII 0-9, A-Z, a-z, space, plus 20 punctuation
glyphs (,-'()?!%&*<>[]~;^=\\) and 5 special-purpose marks. The
glyphOrder omits U+0020 (space) intentionally to keep fontTools from
stripping it on save; Unity falls back to the font's average advance
for missing codepoints, which is the correct behavior for space.

Bold synthesis: the same 16x24 polylines are duplicated with inner
stroked outlines offset by 1.5 PX (Medium) or 3 PX (Bold). Visible
weight gain without breaking the design grid.

Italic synthesis: a horizontal shear is applied at draw time with
slope = tan(-10 degrees). Same Regular geometry; just skewed.

### Style classes in `HudUI.uss`

  - `var(--font)`                 Regular
  - `var(--font-medium)`          Medium
  - `var(--font-bold)`            Bold
  - `var(--font-italic)`          Italic
  - `var(--font-bold-italic)`     Bold Italic
  - `.underlined`                 underline + italic decoration
  - `.font-regular / .font-medium / .font-bold / .font-italic / .font-bi`
                                   explicit font binding
  - `.numeric-label`              Medium + tighter letter-spacing
  - `.active-label`               Bold + amber color (active state)
  - `.link-label`                 Italic + underline (citations/links)

### Re-bake

```powershell
python tools/bake_kit_fonts.py
```

Reads `assets/hud_kit/font/glyph_specs.py` and `_build_hud_ttf.py`,
writes the 5 TTFs into the same source directory, mirrors them into
`Homesteader/Assets/Resources/HUDTree/Fonts/`, and refreshes nothing
inside Unity (run the kit overlay's refresh command afterwards if
needed).

### Kerning

No kern table ships with the font. fontTools 4.65 dropped the legacy
'kern' table API, and full GPOS construction is out of scope. UI
Toolkit's `kerning-mode` USS property and `letter-spacing` reach the
same per-pair feel via runtime, with the cost that font metrics are
fixed monospace + per-label class tweaking.

## Where it shows up in Unity

When `_enableKitOverlay` is True on a `HudUIBuilder`:

1. `HUDOverlay_kit.uxml` is added as a full-overlay sibling on the
   UIDocument root.
2. `HudUI_kit.uss` is added as a sibling style sheet on the same root.

The existing `HudUI` tree continues to render unchanged below.
