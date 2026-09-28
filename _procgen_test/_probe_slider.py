"""Render a slider preview showing multiple colors and states."""
import sys, os
KIT = os.path.abspath(r"C:\Users\casey\Desktop\Homesteader\assets/hud_kit")
sys.path.insert(0, KIT)
from runtime.render import render_slider, LayoutMetrics
from PIL import Image, ImageDraw, ImageFont

COLORS = ["red", "green", "amber", "slate"]
STATES = ["unclicked", "hover", "clicked", "disabled"]
LABELS = {
    "unclicked": "Unclicked",
    "hover":     "Hover",
    "clicked":   "Clicked",
    "disabled":  "Disabled",
}

BG = (16, 20, 28, 255)
SL_W = 360
SL_H = 40
GAP = 28
HEAD_W = 160
HEAD_H = 32
VALUES = [0.25, 0.65, 0.85, 0.10]

canvas_w = HEAD_W + len(STATES) * (SL_W + GAP) + GAP
canvas_h = HEAD_H + len(COLORS) * (SL_H + GAP) + GAP
canvas = Image.new("RGBA", (canvas_w, canvas_h), BG)
m = LayoutMetrics(canvas_w, canvas_h)
draw = ImageDraw.Draw(canvas)

state_font = ImageFont.truetype("arial.ttf", 14)
for ci, state in enumerate(STATES):
    bx = HEAD_W + ci * (SL_W + GAP)
    bb = draw.textbbox((0, 0), LABELS[state], font=state_font)
    tw = bb[2] - bb[0]
    draw.text((bx + (SL_W - tw) // 2, 6),
              LABELS[state], fill=(220, 224, 230), font=state_font)

for ri, color in enumerate(COLORS):
    by = HEAD_H + ri * (SL_H + GAP)
    bb = draw.textbbox((0, 0), color, font=state_font)
    tw = bb[2] - bb[0]
    draw.text((HEAD_W - tw - 12, by + (SL_H - 12) // 2),
              color, fill=(220, 224, 230), font=state_font)
    for ci, state in enumerate(STATES):
        bx = HEAD_W + ci * (SL_W + GAP)
        render_slider(canvas, bx, by, SL_W, SL_H, VALUES[ci], m,
                       color=color, state=state)

target = r"C:\Users\casey\Desktop\Homesteader\preview\preview_slider.png"
canvas.save(target)
print("saved", target)
