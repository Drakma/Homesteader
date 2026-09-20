"""Render the 5 kit fonts to PNGs for visual sanity check.

Outputs:
  tools/.scratch/hud_font_regular.png
  tools/.scratch/hud_font_medium.png
  tools/.scratch/hud_font_bold.png
  tools/.scratch/hud_font_italic.png
  tools/.scratch/hud_font_bold_italic.png
"""

import os
from PIL import Image, ImageDraw, ImageFont

KIT = r"C:\Users\casey\Desktop\Homesteader\assets\hud_kit\font"
OUT = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch"

os.makedirs(OUT, exist_ok=True)

TTFS = [
    ("regular",       "homesteader_hud.ttf"),
    ("medium",        "homesteader_hud_medium.ttf"),
    ("bold",          "homesteader_hud_bold.ttf"),
    ("italic",        "homesteader_hud_italic.ttf"),
    ("bold_italic",   "homesteader_hud_bold_italic.ttf"),
]

# Sample HUD strings to render.
SAMPLE = "Hold: wooden_axe  Day 42  Summer 5:00 AM"

def render(font_path: str, label: str):
    im = Image.new('RGB', (1100, 100), 'white')
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(font_path, 32)
    d.text((20, 24), label, fill='black', font=f)
    out = os.path.join(OUT, 'hud_font_' + label + '.png')
    im.save(out)
    return out, f.size

print("Rendering 5 kit fonts...")
for label, fname in TTFS:
    path = os.path.join(KIT, fname)
    if not os.path.isfile(path):
        print("MISSING:", path)
        continue
    out_path, font_size = render(path, label)
    print("write", out_path, "font_size=", font_size)
print("done")
