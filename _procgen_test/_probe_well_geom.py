"""Print the actual well geometry computed by the render pipeline."""
import sys, os
KIT = os.path.abspath(r"C:\Users\casey\Desktop\Homesteader\assets\hud_kit")
sys.path.insert(0, KIT)
from PIL import Image
from runtime.render import render_full, LayoutMetrics
from runtime.state import HudState, ToolbarSlot
from runtime.time_system import TimeSystem, Speed

state = HudState()
for i in range(10):
    state.toolbar[i] = ToolbarSlot(icon_id="apple", count=4 if i % 3 == 0 else (12 if i % 5 == 0 else (2 if i else 255)))
state.selected_slot = 0
ts = TimeSystem(start_day_of_year=42, start_minute=5 * 60, speed=Speed.SPEED_1X)
ts.tick(0.1)

# Just render to test the wells; sample pixels along y=24 to find edges.
img = render_full((1920, 1080), state, ts, show_grid=False).convert("RGB")
pl = img.load()
HEADER_Y = 24  # middle of header band
# Find color transitions along the row that mark the well edges.
print("Sampling header midline to find well edges (brightness > threshold):")
prev = None
for x in range(0, 1920, 1):
    r, g, b = pl[x, HEADER_Y]
    bright = (r + g + b) > 130
    if prev is None or prev != bright:
        if prev is not None:
            print(f"  transition at x={x}: prev_bright={prev}, now_bright={bright}, rgb=({r},{g},{b})")
        prev = bright
