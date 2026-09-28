"""Render checkbox + radio in normal and disabled states."""
import sys, os
KIT = os.path.abspath(r"C:\Users\casey\Desktop\Homesteader\assets/hud_kit")
sys.path.insert(0, KIT)
from runtime.render import (
    render_checkbox, render_radio, LayoutMetrics,
)
from PIL import Image, ImageDraw, ImageFont

BG = (16, 20, 28, 255)
SIZE = 28
GAP = 24
HEAD_W = 120
HEAD_H = 32
LABEL_W = 100

canvas_w = HEAD_W + (SIZE + LABEL_W) * 8 + GAP
canvas_h = HEAD_H + SIZE * 2 + GAP * 2
canvas = Image.new("RGBA", (canvas_w, canvas_h), BG)
m = LayoutMetrics(canvas_w, canvas_h)
draw = ImageDraw.Draw(canvas)

font = ImageFont.truetype("arial.ttf", 14)

# Two rows: Checkboxes, Radios.
ROWS = [
    ("Checkboxes", [
        ("Unchecked", False, "unclicked"),
        ("Checked",   True,  "unclicked"),
        ("",          None,  None),
        ("",          None,  None),
        ("Unchecked Disabled", False, "disabled"),
        ("Checked Disabled",   True,  "disabled"),
    ]),
    ("Radios", [
        ("Unselected", False, "unclicked"),
        ("Selected",   True,  "unclicked"),
        ("",           None,  None),
        ("",           None,  None),
        ("Unselected Disabled", False, "disabled"),
        ("Selected Disabled",   True,  "disabled"),
    ]),
]

# Section labels across the top:
for ci, (lbl, _, _) in enumerate(ROWS[0][1]):
    if not lbl:
        continue
    bx = HEAD_W + ci * (SIZE + LABEL_W)
    bb = draw.textbbox((0, 0), lbl, font=font)
    tw = bb[2] - bb[0]
    draw.text((bx + (SIZE + LABEL_W - tw) // 2, 6),
              lbl, fill=(220, 224, 230), font=font)

for ri, (row_label, cells) in enumerate(ROWS):
    by = HEAD_H + ri * (SIZE + GAP) + GAP
    bb = draw.textbbox((0, 0), row_label, font=font)
    tw = bb[2] - bb[0]
    draw.text((12, by + (SIZE - 14) // 2),
              row_label, fill=(220, 224, 230), font=font)
    for ci, (lbl, val, state) in enumerate(cells):
        bx = HEAD_W + ci * (SIZE + LABEL_W)
        if val is None:
            continue
        if ri == 0:
            render_checkbox(canvas, bx, by, SIZE, m,
                             checked=val, state=state)
        else:
            render_radio(canvas, bx, by, SIZE, m,
                          selected=val, state=state)

target = r"C:\Users\casey\Desktop\Homesteader\preview\preview_inputs.png"
canvas.save(target)
print("saved", target)
