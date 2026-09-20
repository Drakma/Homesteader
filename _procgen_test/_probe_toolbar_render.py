"""Probe the actual toolbar coordinates in the render pipeline."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.dirname(HERE)
# add kit_root so 'runtime' package resolves at /KIT_ROOT/runtime
sys.path.insert(0, os.path.join(KIT_ROOT, "assets", "hud_kit"))

import torch
from runtime.render import render_full, LayoutMetrics
from runtime.state import HudState, VitalId, Vital, ToolbarSlot
from runtime.time_system import TimeSystem, Speed

state = HudState()
# Populate toolbar slots so quantity text gets drawn.
for i in range(10):
    state.toolbar[i] = ToolbarSlot(icon_id=f"apple", count=4 if i % 3 == 0 else (12 if i % 5 == 0 else (2 if i else 255)))
state.selected_slot = 0
ts = TimeSystem(start_day_of_year=42, start_minute=5 * 60, speed=Speed.SPEED_1X)
ts.tick(0.1)

img = render_full((1920, 1080), state, ts, show_grid=False)
m = LayoutMetrics(1920, 1080)
print(f"image size: {img.size}")
print(f"LayoutMetrics: canvas={m.canvas_w}x{m.canvas_h}, scale={m.s}")

# Recompute toolbar coords to check
n_slots = 10
slot_size = m.px(64)  # = 64
slot_gap = m.px(4)    # = 4
bar_w = n_slots * slot_size + (n_slots - 1) * slot_gap  # 676
print(f"toolbar bar_w = {bar_w}")
print(f"toolbar start_x = {(m.canvas_w - bar_w) // 2}")
print(f"toolbar y = {m.canvas_h - slot_size - m.px(8)}")

img.save(rf"{KIT_ROOT}\preview\preview_hud_full.png")
print("saved")
