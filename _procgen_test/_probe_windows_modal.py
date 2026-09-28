"""Probe: render the HUD plus a mock window and modal."""
import sys, os
KIT = os.path.abspath(r"C:\Users\casey\Desktop\Homesteader\assets/hud_kit")
sys.path.insert(0, KIT)
from runtime.render import (
    render_full, render_window, render_modal, LayoutMetrics,
)
from runtime.state import HudState, ToolbarSlot
from runtime.time_system import TimeSystem, Speed

state = HudState()
for i in range(10):
    state.toolbar[i] = ToolbarSlot(
        icon_id="apple",
        count=4 if i % 3 == 0 else (12 if i % 5 == 0 else (2 if i else 255)),
    )
state.selected_slot = 0
ts = TimeSystem(start_day_of_year=42, start_minute=5 * 60, speed=Speed.SPEED_1X)
ts.tick(0.1)

SIZE = (1920, 1080)
img = render_full(SIZE, state, ts, show_grid=False)
m = LayoutMetrics(*SIZE)

# Mock normal window: top-right area, sized 360x160.
render_window(img, x=1500, y=120, w=380, h=180,
              title="Settings", m=m)

# Mock modal: centered, larger.
render_modal(img, x=560, y=300, w=800, h=480,
             title="Confirm Action",
             body="Are you sure you want to do that?",
             m=m)

target = r"C:\Users\casey\Desktop\Homesteader\preview\preview_with_windows.png"
img.save(target)
print("saved", target)
