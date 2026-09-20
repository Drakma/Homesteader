"""_build_sprites_from_sprite2.py - extract 8 sprites from sprite2_source.jpg.

Layout (2816x1536): 2 rows x 4 cols, each sprite on a clean white
background. Find each non-white bounding box, crop, composite onto
transparent background, scale to 128x128 (104 px subject, 12 px
margin, perimeter alpha=0).

Maps to the kit IDs:
  vital_wellness / vital_stamina / vital_thirst / vital_hunger
  resource_water / resource_electricity / resource_fuel / resource_bandwidth

Cell centers are estimated; refine once by detection.

Bolt and meter are kept in their original source orientation (not
mirrored), which is the direction the kit uses for them.
"""
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "sprite2_source.jpg")
SPRITES_ROOT = os.path.join(HERE, "..", "sprites")
VITAL_DIR = os.path.join(SPRITES_ROOT, "vitals")
RES_DIR = os.path.join(SPRITES_ROOT, "resources")


CANVAS = 128
MARGIN = 12
SUBJECT_MAX = CANVAS - 2 * MARGIN

# Image is 2816 x 1536, 2 rows of 4, each cell ~700 x ~700.
# Top row icons: y ~ 380. Bottom row: y ~ 1080.
# Column centers around x ~ 352, 1056, 1760, 2464.
COL_X = [352, 1056, 1760, 2464]


SPRITE_CENTERS = {
    # Top row (y ~ ...): heart, runner, glass, bread (col 0..3).
    "vital_wellness":        (COL_X[0], 380),
    "vital_stamina":         (COL_X[1], 380),
    "vital_thirst":          (COL_X[2], 380),
    "vital_hunger":          (COL_X[3], 380),
    # Bottom row (y ~ 1080): water drop, lightning, gas pump, signal meter.
    "resource_water":        (COL_X[0], 1080),
    "resource_electricity":  (COL_X[1], 1080),
    "resource_fuel":         (COL_X[2], 1080),
    "resource_bandwidth":    (COL_X[3], 1080),
}


def _strip_text_region(rgba: Image.Image) -> Image.Image:
    """Detect and remove text-label regions of a sprite.

    The source sheet labels each icon with running text above and/or
    below the icon. After cropping to the alpha bbox, those labels can
    still be inside the bbox. We identify them by connected-component
    analysis on the alpha channel: text glyphs are many small clusters,
    while icon artwork is dominated by a much larger component. We then
    zero-alpha any pixel that belongs to label-region components.
    """
    alpha = rgba.split()[3]
    bbox = alpha.getbbox()
    if bbox is None:
        return rgba
    _l, t, _r, b = bbox
    width = bbox[2] - bbox[0]
    height = b - t
    if width <= 8 or height <= 8:
        return rgba

    # Build a binary mask of content pixels.
    mask = alpha.point(lambda v: 1 if v > 8 else 0).load()
    W, H = rgba.size
    visited = [[False] * W for _ in range(H)]

    # 8-connected flood fill. Returns (size, bbox).
    def flood(sx: int, sy: int):
        stack = [(sx, sy)]
        min_x = max_x = sx
        min_y = max_y = sy
        size = 0
        while stack:
            x, y = stack.pop()
            if x < 0 or y < 0 or x >= W or y >= H:
                continue
            if visited[y][x] or not mask[x, y]:
                continue
            visited[y][x] = True
            size += 1
            if x < min_x:
                min_x = x
            elif x > max_x:
                max_x = x
            if y < min_y:
                min_y = y
            elif y > max_y:
                max_y = y
            stack.append((x + 1, y))
            stack.append((x - 1, y))
            stack.append((x, y + 1))
            stack.append((x, y - 1))
            stack.append((x + 1, y + 1))
            stack.append((x + 1, y - 1))
            stack.append((x - 1, y + 1))
            stack.append((x - 1, y - 1))
        return size, (min_x, min_y, max_x, max_y)

    components = []
    for y in range(t, b + 1):
        for x in range(_l, _r + 1):
            if not visited[y][x] and mask[x, y]:
                size, cb = flood(x, y)
                components.append((size, cb))

    if not components:
        return rgba

    # The largest component is the icon proper (or part of it).
    components.sort(key=lambda c: c[0], reverse=True)
    icon_size = components[0][0]
    # Treat any component smaller than 5% of the icon size as "text glyph."
    glyph_threshold = max(20, icon_size // 20)

    # Find y-bands that contain text glyphs (a 'band' is a contiguous
    # vertical range of rows that includes at least 2 small components).
    glyph_rows = set()
    for size, (gx0, gy0, gx1, gy1) in components:
        if size >= glyph_threshold:
            continue
        for y in range(gy0, gy1 + 1):
            glyph_rows.add(y)

    if not glyph_rows:
        return rgba

    # Group adjacent glyph rows into bands.
    sorted_rows = sorted(glyph_rows)
    bands = []
    cur = [sorted_rows[0], sorted_rows[0]]
    for r in sorted_rows[1:]:
        if r - cur[1] <= 4:  # small gap tolerance within a band
            cur[1] = r
        else:
            bands.append(tuple(cur))
            cur = [r, r]
    bands.append(tuple(cur))

    # Keep bands that are "label-like": height < 25% of total bbox, and
    # contain enough distinct glyphs relative to band height (i.e., text,
    # not a small icon highlight).
    label_bands = []
    for band in bands:
        bh = band[1] - band[0] + 1
        if bh >= int(height * 0.30):
            continue
        glyph_count = sum(
            1 for size, cb in components
            if size < glyph_threshold
            and cb[1] <= band[1] and cb[3] >= band[0]
        )
        if glyph_count >= 3:
            label_bands.append(band)

    if not label_bands:
        return rgba

    # Zero alpha in label bands. Expand each band a few rows for safety.
    px = rgba.load()
    for y0, y1 in label_bands:
        y0e = max(0, y0 - 2)
        y1e = min(H - 1, y1 + 2)
        for y in range(y0e, y1e + 1):
            for x in range(W):
                if mask[x, y]:
                    px[x, y] = (0, 0, 0, 0)

    # Re-crop to the new alpha bbox.
    alpha2 = rgba.split()[3]
    new_bbox = alpha2.getbbox()
    if new_bbox is None:
        return rgba
    return rgba.crop((0, 0, rgba.width, new_bbox[3]))


def main():
    img = Image.open(SRC).convert("RGB")

    for sid, (cx, cy) in SPRITE_CENTERS.items():
        # Crop a generous window around the cell center.
        half = 360
        box = (max(0, cx - half), max(0, cy - half),
               min(img.width, cx + half), min(img.height, cy + half))
        sub = img.crop(box)

        # Find tight bbox of non-white pixels.
        # White: r,g,b all > 240. Anything else is content.
        gray = sub.convert("L")
        # Mask: inverted (True = content).
        bw = gray.point(lambda v: 0 if v > 240 else 255)
        bbox = bw.getbbox()
        if not bbox:
            print(f"[warn] no content for {sid}")
            continue
        sprite = sub.crop(bbox)

        # Add small padding so we don't clip the bbox edges, then convert
        # to RGBA and make whites transparent.
        pad = 8
        rgba = Image.new("RGBA",
                          (sprite.width + 2 * pad,
                           sprite.height + 2 * pad),
                          (0, 0, 0, 0))
        sprite_rgba = sprite.convert("RGBA")
        rgba.paste(sprite_rgba, (pad, pad))
        # Walk pixels and strip near-white.
        px = rgba.load()
        w, h = rgba.size
        for y in range(h):
            for x in range(w):
                r, g, b, _ = px[x, y]
                if r > 235 and g > 235 and b > 235:
                    px[x, y] = (0, 0, 0, 0)

        # Strip the text-label region (label sits below the icon).
        rgba = _strip_text_region(rgba)

        # Flip bolt and meter across the vertical axis (left <-> right).
        if sid in ("resource_electricity", "resource_bandwidth"):
            rgba = rgba.transpose(Image.FLIP_LEFT_RIGHT)

        # Scale to fit SUBJECT_MAX within CANVAS, preserving aspect.
        sw, sh = rgba.size
        scale = SUBJECT_MAX / max(sw, sh)
        new_w = max(1, int(round(sw * scale)))
        new_h = max(1, int(round(sh * scale)))
        scaled = rgba.resize((new_w, new_h), Image.LANCZOS)
        out = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
        out.alpha_composite(
            scaled,
            ((CANVAS - new_w) // 2, (CANVAS - new_h) // 2),
        )

        out_dir = VITAL_DIR if sid.startswith("vital_") else RES_DIR
        out_path = os.path.join(out_dir, f"{sid}.png")
        os.makedirs(out_dir, exist_ok=True)
        out.save(out_path, "PNG")
        print(f"[sprite2] {sid} -> {out_path} ({out.size})")


if __name__ == "__main__":
    main()
