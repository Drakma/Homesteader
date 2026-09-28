"""Render a slider preview showing 3 track kinds (lightslate, slate, disabled)."""
import sys, os
KIT = os.path.abspath(r"C:\Users\casey\Desktop\Homesteader\assets/hud_kit")
sys.path.insert(0, KIT)
from runtime.render import render_slider, LayoutMetrics
from PIL import Image, ImageDraw, ImageFont

TRACK_KINDS = [
    ("Lightslate", "lightslate"),
    ("Slate",      "slate"),
    ("Disabled",   "disabled"),
]
VALUE = 0.55

BG = (16, 20, 28, 255)
SL_W = 360
SL_H = 40
GAP = 28
HEAD_W = 160
HEAD_H = 32

canvas_w = HEAD_W + SL_W + GAP
canvas_h = HEAD_H + len(TRACK_KINDS) * (SL_H + GAP) + GAP
canvas = Image.new("RGBA", (canvas_w, canvas_h), BG)
m = LayoutMetrics(canvas_w, canvas_h)
draw = ImageDraw.Draw(canvas)

state_font = ImageFont.truetype("arial.ttf", 14)

for ri, (row_label, kind) in enumerate(TRACK_KINDS):
    by = HEAD_H + ri * (SL_H + GAP)
    bb = draw.textbbox((0, 0), row_label, font=state_font)
    tw = bb[2] - bb[0]
    draw.text((HEAD_W - tw - 12, by + (SL_H - 12) // 2),
              row_label, fill=(220, 224, 230), font=state_font)
    bx = HEAD_W
    render_slider(canvas, bx, by, SL_W, SL_H, VALUE, m,
                  track_kind=kind, state="unclicked")

target = r"C:\Users\casey\Desktop\Homesteader\preview\preview_slider_three.png"
canvas.save(target)
print("saved", target)
