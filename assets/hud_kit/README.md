# Runtime HUD

The runtime HUD module lives under `runtime/`:

- `time_system.py` — game-clock state machine (20 min day + 20 min night, 120-day year, 1x/3x/5x speed multipliers).
- `state.py` — `HudState`: vital levels, toolbar slots, selected slot, held asset.
- `render.py` — lays out the panels and renders the active icon glyphs on top of each panel.
- `_render_hud.py` — top-level driver: builds state, ticks the clock, writes a 1920×1080 PNG smoke test.
- `preview/preview_hud_full.png` — the rendered smoke test.
- `HUD_LAYOUT.md` — definitive coords, sprite names, and contracts.

Run:

```powershell
python assets\hud_kit\runtime\_render_hud.py
```

To consume this kit from Unity: read `hud_kit.json` + `HUD_LAYOUT.md`,
load the kit's PNG sprites by `path`, and drive the panels by feeding
runtime state values. The Unity side is a separate MonoBehaviour and is
not provided here.
