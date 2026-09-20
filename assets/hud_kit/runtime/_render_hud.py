"""_render_hud.py - render the full HUD as a 1920x1080 PNG preview.

Usage:
    python assets/hud_kit/runtime/_render_hud.py

Writes preview PNG to assets/hud_kit/preview/preview_hud_full.png.
This is the canonical visual I'm using to validate the layout.
"""

import os
import sys

# Allow running as a script in spite of the package layout.
HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.dirname(HERE)
sys.path.insert(0, KIT_ROOT)

from runtime.render import render_full
from runtime.state import HudState, VitalId, Vital, ToolbarSlot
from runtime.time_system import TimeSystem, Speed

OUT = os.path.join(KIT_ROOT, "preview", "preview_hud_full.png")
os.makedirs(os.path.dirname(OUT), exist_ok=True)


def sample_state():
    state = HudState()
    state.toolbar = [
        ToolbarSlot(icon_id="tool_axe", count=1),
        ToolbarSlot(),
        ToolbarSlot(icon_id="fishing_rod", count=1),
        ToolbarSlot(),
        ToolbarSlot(icon_id="apple", count=4),
        ToolbarSlot(),
        ToolbarSlot(icon_id="mat_log_oak", count=12),
        ToolbarSlot(),
        ToolbarSlot(icon_id="food_salmon_grilled", count=2),
        ToolbarSlot(),
    ]
    state.selected_slot = 2
    state.held_asset_id = "fishing_rod"
    state.update_vital(Vital(VitalId.WELLNESS, 50))
    state.update_vital(Vital(VitalId.STAMINA, 30))
    state.update_vital(Vital(VitalId.THIRST, 10))
    state.update_vital(Vital(VitalId.HUNGER, -20))
    return state


def sample_time():
    # Start at 8:00 AM on Summer, Day 42, 1x speed. With 12-hour cycle
    # (1440 min total), start_minute=480 maps to 8:00 AM.
    ts = TimeSystem(start_day_of_year=42, start_minute=8 * 60,
                    speed=Speed.SPEED_1X)
    ts.tick(0.1)
    return ts


def main():
    """Render the canonical 1920x1080 preview. The HUD layout is fully
    proportional via LayoutMetrics - this single render confirms the
    square-corner + fit-to-content behavior the user wants to verify.
    """
    state = sample_state()
    ts = sample_time()
    OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "preview")
    OUT_DIR = os.path.abspath(OUT_DIR)
    os.makedirs(OUT_DIR, exist_ok=True)

    canvas_size = (1920, 1080)
    img = render_full(canvas_size, state, ts, show_grid=False)
    out_path = os.path.join(OUT_DIR, "preview_hud_full.png")
    img.save(out_path, "PNG")
    print(f"[render-hud] {out_path} ({canvas_size[0]}x{canvas_size[1]})")


if __name__ == "__main__":
    main()
