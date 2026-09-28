"""Render a 4 (color) x 4 (state) button grid for visual review."""
import sys, os
KIT = os.path.abspath(r"C:\Users\casey\Desktop\Homesteader\assets/hud_kit")
sys.path.insert(0, KIT)
from runtime.render import render_button, LayoutMetrics
from PIL import Image, ImageDraw, ImageFont

COLORS = ["red", "green", "amber", "slate"]
STATES = ["disabled", "hover", "clicked", "unclicked"]
LABELS = {
    "disabled":  "Disabled",
    "hover":     "Hover",
    "clicked":   "Clicked",
    "unclicked": "Unclicked",
}
COL_HEAD_BG = (32, 38, 50, 255)
ROW_HEAD_BG = (24, 28, 36, 255)
BG = (16, 20, 28, 255)

BTN_W = 200
BTN_H = 56
GAP = 24
HEAD_W = 120
HEAD_H = 32

canvas_w = HEAD_W + len(STATES) * (BTN_W + GAP) + GAP
canvas_h = HEAD_H + len(COLORS) * (BTN_H + GAP) + GAP
canvas = Image.new("RGBA", (canvas_w, canvas_h), BG)
m = LayoutMetrics(canvas_w, canvas_h)
draw = ImageDraw.Draw(canvas)

# Column headers (state names).
state_font = ImageFont.truetype("arial.ttf", 14)
for ci, state in enumerate(STATES):
    bx = HEAD_W + ci * (BTN_W + GAP)
    bb = draw.textbbox((0, 0), LABELS[state], font=state_font)
    tw = bb[2] - bb[0]
    draw.text((bx + (BTN_W - tw) // 2, 6),
              LABELS[state], fill=(220, 224, 230), font=state_font)

# Row headers (color names).
for ri, color in enumerate(COLORS):
    by = HEAD_H + ri * (BTN_H + GAP)
    bb = draw.textbbox((0, 0), color, font=state_font)
    tw = bb[2] - bb[0]
    draw.text((HEAD_W - tw - 12, by + (BTN_H - 12) // 2),
              color, fill=(220, 224, 230), font=state_font)
    # Buttons in this row.
    for ci, state in enumerate(STATES):
        bx = HEAD_W + ci * (BTN_W + GAP)
        render_button(canvas, bx, by, BTN_W, BTN_H, "OK", m,
                      color=color, state=state)

target = r"C:\Users\casey\Desktop\Homesteader\preview\preview_buttons.png"
canvas.save(target)
print("saved", target)
