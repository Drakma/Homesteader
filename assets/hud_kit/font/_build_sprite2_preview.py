"""_build_sprite2_preview.py - render a preview sheet of all 8 sprite2 icons.

Reads the 4 vitals and 4 resources, lays them out in a 2-row grid with
labels, and writes _sprite2_preview.png. Used for visual verification of
build_sprites_from_sprite2.py output.
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.dirname(HERE)
SPRITES_ROOT = os.path.join(KIT_ROOT, "sprites")

VITALS = ["vital_wellness", "vital_stamina", "vital_thirst", "vital_hunger"]
RESOURCES = ["resource_water", "resource_electricity",
             "resource_fuel", "resource_bandwidth"]

CELL = 160
PAD = 16
LABEL_H = 28
BG = (24, 24, 30, 255)

W = PAD + 4 * (CELL + PAD)
H = PAD + 2 * (CELL + LABEL_H + PAD) + PAD

out = Image.new("RGBA", (W, H), BG)
draw = ImageDraw.Draw(out)

try:
    font = ImageFont.truetype("arial.ttf", 16)
except OSError:
    font = ImageFont.load_default()


def paste_at(grid_x, grid_y, fname, label):
    x = PAD + grid_x * (CELL + PAD)
    y = PAD + grid_y * (CELL + LABEL_H + PAD)
    p = os.path.join(SPRITES_ROOT, fname + ".png")
    im = Image.open(p).convert("RGBA")
    ox = x + (CELL - im.width) // 2
    oy = y + (CELL - im.height) // 2
    out.alpha_composite(im, (ox, oy))
    bbox = draw.textbbox((0, 0), label, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x + (CELL - tw) // 2, y + CELL + 4), label,
              fill=(220, 220, 220, 255), font=font)


for i, sid in enumerate(VITALS):
    paste_at(i, 0, sid, sid.replace("vital_", ""))

for i, sid in enumerate(RESOURCES):
    paste_at(i, 1, sid, sid.replace("resource_", ""))

target = os.path.join(HERE, "_sprite2_preview.png")
out.save(target)
print(f"wrote {target} ({out.size})")
