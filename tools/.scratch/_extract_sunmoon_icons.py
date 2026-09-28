"""Extract 7 icons (skipping ECLIPSE SUN at index 3) from sun-moon.jpg
   and write each as a 128x128 PNG with a 12 px transparent margin
   around a 104x104 content area.
"""
from PIL import Image
import os

SRC = r"C:\Users\casey\Downloads\sun-moon.jpg"
OUT_DIR = r"C:\Users\casey\Desktop\Homesteader\preview\sunmoon_icons"
os.makedirs(OUT_DIR, exist_ok=True)

NOMINAL_OUT = 128
MARGIN = 12
INNER = NOMINAL_OUT - MARGIN * 2  # 104

# 4 columns x 2 rows. Skip column 3 (ECLIPSE SUN). We keep:
#   (0,0) MORNING SUN, (1,0) NOON SUN, (2,0) SUNSET SUN,
#   (0,1) NEW MOON, (1,1) FIRST QUARTER, (2,1) FULL MOON, (3,1) LAST QUARTER
kept = [
    ("morning_sun.png", 0, 0),
    ("noon_sun.png",   1, 0),
    ("sunset_sun.png", 2, 0),
    ("new_moon.png",    0, 1),
    ("first_quarter_moon.png", 1, 1),
    ("full_moon.png",   2, 1),
    ("last_quarter_moon.png", 3, 1),
]

img = Image.open(SRC).convert("RGBA")
W, H = img.size
cellW = W // 4
cellH = H // 2

# Each tile has a transparent corner where the white background meets.
# We trim to alpha-bbox, then place the content centered into a
# 128x128 canvas with 12 px margin -> 104 px content box.
def crop_alpha_bbox(tile):
    a = tile.split()[3]
    bbox = a.getbbox()
    if bbox is None:
        # No alpha -> treat whole tile as content with white turned to transparent
        tile = tile.convert("RGBA")
        # Replace near-white pixels with transparent
        px = tile.load()
        for y in range(tile.height):
            for x in range(tile.width):
                r, g, b, A = px[x, y]
                if r > 245 and g > 245 and b > 245:
                    px[x, y] = (r, g, b, 0)
        a = tile.split()[3]
        bbox = a.getbbox() or (0, 0, tile.width, tile.height)
    return tile.crop(bbox)

for name, col, row in kept:
    box = (col * cellW, row * cellH, (col + 1) * cellW, (row + 1) * cellH)
    tile = img.crop(box).convert("RGBA")

    # Make near-white background transparent.
    px = tile.load()
    for y in range(tile.height):
        for x in range(tile.width):
            r, g, b, A = px[x, y]
            if r > 240 and g > 240 and b > 240 and A > 0:
                px[x, y] = (r, g, b, 0)

    cx = tile.crop(tile.getbbox() or (0, 0, tile.width, tile.height))

    # Resize the trimmed content to fit within INNER x INNER maintaining aspect
    cw, ch = cx.size
    if cw <= 0 or ch <= 0:
        continue
    scale = min(INNER / cw, INNER / ch)
    nw = max(1, int(round(cw * scale)))
    nh = max(1, int(round(ch * scale)))
    resized = cx.resize((nw, nh), Image.LANCZOS)

    canvas = Image.new("RGBA", (NOMINAL_OUT, NOMINAL_OUT), (0, 0, 0, 0))
    px_off = (NOMINAL_OUT - nw) // 2
    py_off = (NOMINAL_OUT - nh) // 2
    canvas.alpha_composite(resized, (px_off, py_off))

    out_path = os.path.join(OUT_DIR, name)
    canvas.save(out_path)
    print(f"wrote {out_path} ({canvas.size})")
