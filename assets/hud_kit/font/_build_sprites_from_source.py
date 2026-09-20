"""_build_sprites_from_source.py - extract 8 sprites from sprites_source.jpg.

Layout (2816x1536): 2 rows x 4 cols, each sprite roughly 700x700 above a label.
This script samples each expected cell, finds a tight bbox, crops the sprite,
and saves to assets/hud_kit/sprites/{vitals,resources}/<id>.png at 128x128
RGBA (104 px subject, 12 px margin, perimeter alpha=0, no border).

Bolt and meter are mirrored horizontally so they "face left" (left-facing kit
default).

Output paths:
  vitals:   vital_heart.png vital_stamina.png vital_thirst.png vital_wellness.png
  resources: resource_water.png resource_electricity.png resource_bandwidth.png resource_propane.png
"""
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "sprites_source.jpg")
SPRITES_ROOT = os.path.join(HERE, "..", "sprites")
VITAL_DIR = os.path.join(SPRITES_ROOT, "vitals")
RES_DIR = os.path.join(SPRITES_ROOT, "resources")

# Cell centers (image is 2816x1536, 4 columns x 2 rows).
# We sample a window around each center, then refine bbox.
COLS = 4
ROWS = 2
W_SRC, H_SRC = 2816, 1536
COL_X = [W_SRC * (i + 0.5) / COLS for i in range(COLS)]
ROW_Y = [H_SRC * (0 + 0.5) / ROWS * 0.78, H_SRC * (1 + 0.5) / ROWS * 0.78]
# Top row icons are roughly in y=[80, 700]; bottom row in y=[770, 1390].
# Use approximate centers, then refine.
SPRITE_CENTERS = {
    # Top row (y=~380): heart, runner, glass, bread (col 0..3).
    "vital_wellness":        (COL_X[0], 380),
    "vital_stamina":         (COL_X[1], 380),
    "vital_thirst":          (COL_X[2], 380),
    "vital_hunger":          (COL_X[3], 380),
    # Bottom row (y=~1080): water drop, lightning, gas pump, signal meter.
    "resource_water":        (COL_X[0], 1080),
    "resource_electricity":  (COL_X[1], 1080),
    "resource_fuel":         (COL_X[2], 1080),
    "resource_bandwidth":    (COL_X[3], 1080),
}

# White sticker halo: pixels with R,G,B all > 240 are part of the halo.
# Background: ~(231,225,214). Labels: dark grey (~<80). Subject: anything else.

CANVAS = 128
MARGIN = 12
SUBJECT_MAX = CANVAS - 2 * MARGIN  # 104


def _load():
    img = Image.open(SRC).convert("RGB")
    return img


def _is_white(p):
    r, g, b = p
    return r > 240 and g > 240 and b > 240


def _is_bg(p):
    r, g, b = p
    return abs(r - 231) < 8 and abs(g - 225) < 8 and abs(b - 214) < 8


def _is_label(p):
    r, g, b = p
    return r < 80 and g < 80 and b < 80


def _is_subject(p):
    return not (_is_white(p) or _is_bg(p) or _is_label(p))


def _crop_sprite(img, center, half_w=380, half_h=380):
    cx, cy = center
    box = (max(0, cx - half_w), max(0, cy - half_h),
           min(img.width, cx + half_w), min(img.height, cy + half_h))
    return img.crop(box)


def _tight_bbox(sub_img):
    """Find tight bbox of non-background pixels INCLUDING the white halo."""
    w, h = sub_img.size
    px = sub_img.load()
    min_x, min_y = w, h
    max_x, max_y = -1, -1
    for y in range(h):
        for x in range(w):
            p = px[x, y]
            # Include white halo (fills the crop) - we need a separate
            # pass to find where subject starts. The labels are black;
            # background is beige. Halo is near-white.
            if _is_bg(p):
                continue
            if _is_label(p):
                continue
            # Else: halo or subject - treat as part of bbox.
            if x < min_x: min_x = x
            if x > max_x: max_x = x
            if y < min_y: min_y = y
            if y > max_y: max_y = y
    return (min_x, min_y, max_x, max_y)


def _strip_white_to_alpha(rgba):
    """Convert near-white pixels to transparent. Keep other pixels intact."""
    out = rgba.copy()
    px = out.load()
    w, h = out.size
    for y in range(h):
        for x in range(w):
            r, g, b, _a = px[x, y]
            # The halo is whitish but not pure white; the JPG has noise.
            # Threshold: pixels very close to white -> transparent.
            whiteness = min(r, g, b)
            if whiteness > 235 and (r - g) < 25 and (g - b) < 25 and abs(r - b) < 25:
                px[x, y] = (0, 0, 0, 0)
    return out


def _scale_to_canvas(rgba, mirror=False):
    if mirror:
        rgba = rgba.transpose(Image.FLIP_LEFT_RIGHT)
    bbox = rgba.getbbox()
    if not bbox:
        return Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    cropped = rgba.crop(bbox)
    sw, sh = cropped.size
    scale = SUBJECT_MAX / max(sw, sh)
    new_w = max(1, int(round(sw * scale)))
    new_h = max(1, int(round(sh * scale)))
    scaled = cropped.resize((new_w, new_h), Image.LANCZOS)
    out = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    px = (CANVAS - new_w) // 2
    py = (CANVAS - new_h) // 2
    out.alpha_composite(scaled, (px, py))
    return out


def main():
    img = _load()
    os.makedirs(VITAL_DIR, exist_ok=True)
    os.makedirs(RES_DIR, exist_ok=True)

    # Iterate by ID; decide dir from id prefix.
    for sid, center in SPRITE_CENTERS.items():
        sub = _crop_sprite(img, center)
        bbox = _tight_bbox(sub)
        if bbox[2] < bbox[0] or bbox[3] < bbox[1]:
            print(f"[warn] {sid}: empty bbox at {center}")
            continue
        sprite_rgb = sub.crop(bbox)
        # Add a small padding so the halo isn't clipped, then strip white.
        pad = 6
        padded = Image.new("RGB",
                            (sprite_rgb.width + 2 * pad,
                             sprite_rgb.height + 2 * pad),
                            (231, 225, 214))
        padded.paste(sprite_rgb, (pad, pad))
        rgba = padded.convert("RGBA")
        rgba = _strip_white_to_alpha(rgba)
        # Determine mirror: lightning bolt and meter mirror left.
        mirror = sid in ("resource_electricity", "resource_bandwidth")
        canvas_img = _scale_to_canvas(rgba, mirror=mirror)
        out_dir = VITAL_DIR if sid.startswith("vital_") else RES_DIR
        out_path = os.path.join(out_dir, f"{sid}.png")
        canvas_img.save(out_path, "PNG")
        print(f"[sprite] {sid} -> {out_path} ({canvas_img.size})")


if __name__ == "__main__":
    main()
