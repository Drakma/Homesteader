# Flood-fill the ENCLOSED interiors of each cursor glyph with its category
# colour, keeping the dark outline on top.
#
# Approach (option B):
#   1. Take the glyph's alpha as a mask of solid ink.
#   2. Invert it to get "not ink" - this includes both the outside page and
#      any enclosed regions inside the drawing.
#   3. Flood-fill from the image border to find the TRUE OUTSIDE only.
#   4. Whatever is "not ink" but NOT reached by that flood is an enclosed
#      interior -> that is what gets filled with the category colour.
#   5. Composite: colour fill underneath, original dark strokes on top.
#
# Doing the outside-flood first is what keeps the fill inside the shape; a
# naive fill-everything-non-ink would paint the whole canvas.
from pathlib import Path
from PIL import Image, ImageDraw

PTR = Path(r'C:\Users\casey\Desktop\Homesteader\tools\_ptr')
G = PTR / 'glyphs'
OUT = Path(r'C:\Users\casey\Desktop\Homesteader\assets\hud_kit\cursors')

SIZE = 128
MARGIN = 12

# Outline stays dark on every cursor so the silhouette reads over any terrain.
OUTLINE = (24, 30, 40)

# Category fill colours, chosen to be legible as flat shapes at 48 px.
PALETTE = {
    'tool':     (176, 137, 104),
    'resource': (234, 179, 8),
    'action':   (74, 222, 128),
    'system':   (203, 213, 225),
    'item':     (193, 154, 60),
}

CURSORS = [
    ('r0c00', 'axe',                   'tool'),
    ('r0c01', 'handsaw',               'tool'),
    ('r0c02', 'log_rings',             'resource'),
    ('r0c03', 'sawing',                'tool'),
    ('r0c04', 'mattock',               'tool'),
    ('r0c05', 'plant_seedling',        'action'),
    ('r0c06', 'wheat_sheaf',           'resource'),
    ('r0c07', 'trowel',                'tool'),
    ('r1c00', 'axe_filled',            'tool'),
    ('r1c01', 'plant_seedling_filled', 'action'),
    ('r1c02', 'wheat_sheaf_filled',    'resource'),
    ('r1c03', 'bucket_carry',          'action'),
    ('drawn:sickle', 'sickle',         'tool'),   # redrawn in code: the scan read as a crook, not a sickle
    ('r1c05', 'egg',                   'resource'),
    ('r1c06', 'egg_basket',            'resource'),
    ('r2c00', 'wrenches',              'tool'),
    ('r2c01', 'gear',                  'action'),
    ('r2c02', 'jerrycan',              'resource'),
    ('r2c03', 'screwdriver',           'tool'),
    ('r2c04', 'hammer',                'tool'),
    ('r2c05', 'pickaxe',               'tool'),
    ('r2c06', 'finger_point',          'system'),
    ('r2c07', 'seed_sack',             'resource'),
    ('r2c08', 'tool_belt',             'item'),
    ('r3c00', 'arrow',                 'system'),
    ('r3c01', 'hand_open',             'system'),
    ('r3c02', 'finger_tap',            'system'),
    ('r3c03', 'move',                  'system'),
    ('r3c04', 'ibeam',                 'system'),
    ('r3c06', 'arrow_wait',            'system'),
    ('r3c07', 'arrow_unavailable',     'system'),
    ('r4c00', 'wait_settings',         'system'),
    ('r4c01', 'wait_settings_2',       'system'),
    ('r4c04', 'resize_vertical',       'system'),
    ('r4c05', 'resize_horizontal',     'system'),
    ('r4c06', 'resize_nwse',           'system'),
    ('r4c07', 'resize_nesw',           'system'),
    ('r4c08', 'resize_all',            'system'),
    ('r4c09', 'help',                  'system'),
    # Drawn in code (see draw_steering_wheel): there is no glyph for it on the sheet.
    ('drawn:steering_wheel', 'steering_wheel', 'action'),
    ('drawn:shears', 'shears',         'tool'),   # sheep shears: shown over a sheep that can be sheared
]

# Glyph sources, in order: the scanned sheet glyphs in tools/_ptr/glyphs when
# they are present, else the previously built mono PNG (whose alpha IS the
# fitted glyph), else a code-drawn glyph.
DRAWN = {}


def draw_steering_wheel():
    # A three-spoke car wheel: rim, hub, spokes at 12, 4 and 8 o'clock. Drawn
    # at 4x and downsampled so the strokes are anti-aliased like the scans.
    k = 4
    S = SIZE * k
    im = Image.new('L', (S, S), 0)
    d = ImageDraw.Draw(im)
    c = S / 2
    r_out = (SIZE / 2 - MARGIN) * k
    stroke = 16 * k      # rim width
    spoke = 10 * k
    # rim
    d.ellipse([c - r_out, c - r_out, c + r_out, c + r_out], outline=255, width=stroke)
    # spokes
    import math
    r_in = r_out - stroke / 2
    for ang in (-90, 30, 150):
        a = math.radians(ang)
        x, y = c + math.cos(a) * r_in, c + math.sin(a) * r_in
        d.line([(c, c), (x, y)], fill=255, width=spoke)
    # hub
    r_hub = 13 * k
    d.ellipse([c - r_hub, c - r_hub, c + r_hub, c + r_hub], fill=255)
    # Hollow the solid shape to an outline so it matches the scanned line art:
    # the stroke stays, and the interior becomes an enclosed region that the
    # variant builders fill (white or category colour).
    from PIL import ImageFilter, ImageChops
    line = 4 * k
    inner = im.filter(ImageFilter.MinFilter(line * 2 + 1))
    outline = ImageChops.subtract(im, inner)
    # The rim's inner edge, so the ring reads as a ring and not a disc.
    r_rim = r_out - stroke
    ImageDraw.Draw(outline).ellipse([c - r_rim, c - r_rim, c + r_rim, c + r_rim], outline=255, width=line)
    outline = outline.resize((SIZE, SIZE), Image.LANCZOS)
    out = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    out.putalpha(outline)
    return out


DRAWN['steering_wheel'] = draw_steering_wheel


def _hollow(solid, k, line=4, accents=None):
    # Solid shape mask (L, at k x) -> anti-aliased outline on the SIZE canvas,
    # plus optional accent strokes drawn as (callable taking an ImageDraw).
    from PIL import ImageFilter, ImageChops
    inner = solid.filter(ImageFilter.MinFilter(line * k * 2 + 1))
    outline = ImageChops.subtract(solid, inner)
    if accents:
        d = ImageDraw.Draw(outline)
        accents(d)
        # accents only count inside the shape
        outline = ImageChops.multiply(outline, solid)
    outline = outline.resize((SIZE, SIZE), Image.LANCZOS)
    out = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    out.putalpha(outline)
    return out


def draw_sickle():
    # Crescent blade at the upper left, wooden handle running to the lower
    # right (the tool axis the whole set shares). The blade tip is the hotspot.
    import math
    k = 4
    S = SIZE * k
    solid = Image.new('L', (S, S), 0)
    d = ImageDraw.Draw(solid)
    # Blade: a thick arc, thinning towards the tip, centred upper-left of canvas centre.
    cx, cy = 52 * k, 56 * k
    r = 30 * k
    # draw the arc as a chain of discs whose radius shrinks toward the tip
    for i in range(0, 101):
        t = i / 100
        ang = math.radians(-205 + 235 * t)        # tip (left) over the top -> heel (lower right)
        x = cx + math.cos(ang) * r
        y = cy + math.sin(ang) * r
        w = (2.5 + 8.5 * t) * k                   # 2.5 px at the tip, 11 px at the heel
        d.ellipse([x - w, y - w, x + w, y + w], fill=255)
    # Heel -> handle. Heel is the arc end at ang = 110 deg.
    hx = cx + math.cos(math.radians(30)) * r
    hy = cy + math.sin(math.radians(30)) * r
    # Ferrule and handle along the shared axis (down-right, 45 deg).
    ux, uy = math.cos(math.radians(45)), math.sin(math.radians(45))
    fx0, fy0 = hx + ux * 2 * k, hy + uy * 2 * k
    fx1, fy1 = fx0 + ux * 10 * k, fy0 + uy * 10 * k
    d.line([(fx0, fy0), (fx1, fy1)], fill=255, width=14 * k)
    gx1, gy1 = fx1 + ux * 34 * k, fy1 + uy * 34 * k
    d.line([(fx1, fy1), (gx1, gy1)], fill=255, width=16 * k)
    d.ellipse([gx1 - 8 * k, gy1 - 8 * k, gx1 + 8 * k, gy1 + 8 * k], fill=255)

    def accents(dd):
        # ferrule band and a grain line down the handle; an edge line inside the blade
        px, py = -uy, ux
        dd.line([(fx1 + px * 9 * k, fy1 + py * 9 * k), (fx1 - px * 9 * k, fy1 - py * 9 * k)], fill=255, width=3 * k)
        dd.line([(fx1 + ux * 6 * k + px * 3 * k, fy1 + uy * 6 * k + py * 3 * k),
                 (gx1 - ux * 6 * k + px * 3 * k, gy1 - uy * 6 * k + py * 3 * k)], fill=255, width=2 * k)
        for i in range(10, 96):
            t = i / 100
            ang = math.radians(-205 + 235 * t)
            w = (2.5 + 8.5 * t) * k
            rr = r - w * 0.45                      # a line along the inner (cutting) edge
            x = cx + math.cos(ang) * rr
            y = cy + math.sin(ang) * rr
            dd.ellipse([x - 1.2 * k, y - 1.2 * k, x + 1.2 * k, y + 1.2 * k], fill=255)

    return _hollow(solid, k, line=4, accents=accents)


DRAWN['sickle'] = draw_sickle


def draw_shears():
    # Sheep (blade) shears: two triangular blades pointing to the upper left,
    # two arms and the sprung bow at the lower right. Authored in (u, v): u
    # runs along the shared tool axis (top-left -> bottom-right), v across it.
    import math
    k = 4
    S = SIZE * k
    c = S / 2
    r2 = math.sqrt(2)

    def P(u, v):
        return (c + (u - v) / r2 * k, c + (u + v) / r2 * k)

    solid = Image.new('L', (S, S), 0)
    d = ImageDraw.Draw(solid)
    for sgn in (-1, 1):
        d.polygon([P(-58, sgn * 1.5), P(4, sgn * 29), P(4, sgn * 4)], fill=255)        # blade
        d.line([P(2, sgn * 16), P(34, sgn * 16)], fill=255, width=15 * k)              # arm
    # bow: half ring on the +u side joining the two arms
    for i in range(0, 61):
        a = math.radians(-90 + 180 * i / 60)
        x, y = P(34 + math.cos(a) * 16, math.sin(a) * 16)
        d.ellipse([x - 7.5 * k, y - 7.5 * k, x + 7.5 * k, y + 7.5 * k], fill=255)

    def accents(dd):
        for sgn in (-1, 1):
            dd.line([P(-34, sgn * 7), P(2, sgn * 15)], fill=255, width=int(1.5 * k))   # the ground edge of each blade
            dd.line([P(4, sgn * 6), P(4, sgn * 27)], fill=255, width=2 * k)            # blade shoulder

    return _hollow(solid, k, line=3, accents=accents)


DRAWN['shears'] = draw_shears

# Hotspot is where the click actually lands, so it is measured from the
# rendered alpha rather than guessed. 'tip' = the ink pixel nearest the top-left
# corner, correct for anything that points (arrows, fingers, tool cutting
# edges). 'centre' = the ink centroid, correct for objects the player grabs or
# that rotate about themselves (resize arrows, gears, buckets).
HOTSPOTS = {
    'axe': 'tip', 'handsaw': 'tip', 'log_rings': 'centre', 'sawing': 'tip',
    'mattock': 'tip', 'plant_seedling': 'centre', 'wheat_sheaf': 'centre',
    'trowel': 'tip_br', 'axe_filled': 'tip', 'plant_seedling_filled': 'centre',
    'wheat_sheaf_filled': 'centre', 'bucket_carry': 'centre', 'sickle': (25, 69),
    'egg': 'centre', 'egg_basket': 'centre', 'wrenches': 'centre',
    'gear': 'centre', 'jerrycan': 'centre', 'screwdriver': 'tip',
    'hammer': 'tip', 'pickaxe': 'tip', 'finger_point': 'tip',
    'seed_sack': 'centre', 'tool_belt': 'centre', 'arrow': 'tip',
    'hand_open': 'centre', 'finger_tap': 'tip', 'move': 'centre',
    'ibeam': 'centre', 'arrow_wait': 'tip', 'arrow_unavailable': 'tip',
    'wait_settings': 'centre', 'wait_settings_2': 'centre',
    'resize_vertical': 'centre', 'resize_horizontal': 'centre',
    'resize_nwse': 'centre', 'resize_nesw': 'centre', 'resize_all': 'centre',
    'help': 'tip', 'steering_wheel': 'centre', 'shears': (23, 23),
}

HOTSPOT_NOTE = {
    'arrow': 'Arrow tip: the click point is the point of the arrow.',
    'arrow_wait': 'Arrow tip, so the pointer still points while busy.',
    'arrow_unavailable': 'Arrow tip, so the pointer still points when blocked.',
    'finger_point': 'Index fingertip.',
    'finger_tap': 'Tapping fingertip.',
    'help': 'Top of the question mark, which still reads as a pointer.',
    'axe': 'Cutting corner of the axe head.',
    'axe_filled': 'Cutting corner of the axe head.',
    'pickaxe': 'Leading point of the pick.',
    'mattock': 'Leading corner of the mattock blade.',
    'sickle': 'Tip of the sickle point.',
    'trowel': 'Tip of the trowel blade.',
    'screwdriver': 'Tip of the screwdriver blade.',
    'hammer': 'Face of the hammer head.',
    'handsaw': 'Leading corner of the saw blade.',
    'sawing': 'Where the saw meets the log.',
    'move': 'Centroid: all four directions are equidistant.',
    'resize_all': 'Centroid: all four directions are equidistant.',
    'resize_vertical': 'Centroid: up and down are equidistant.',
    'resize_horizontal': 'Centroid: left and right are equidistant.',
    'resize_nwse': 'Centroid: both diagonal ends are equidistant.',
    'resize_nesw': 'Centroid: both diagonal ends are equidistant.',
    'ibeam': 'Centroid: the text insertion point.',
    'gear': 'Centroid: the gear rotates about itself.',
    'steering_wheel': 'Centroid: the wheel turns about its hub.',
    'shears': 'Where the two blade tips meet.',
    'sickle': 'Point of the blade.',
    'wait_settings': 'Centroid: status cursor, no click point.',
    'wait_settings_2': 'Centroid: status cursor, no click point.',
}

# Alpha above this counts as a solid stroke. Lowered from 110 to 60: the
# source art is anti-aliased, so a high cut left mid-alpha stroke pixels
# classified as "not ink", and the flood fill then painted over the outline.
# 60 keeps the full stroke as outline while still finding true interiors.
INK_T = 60

def measure_hotspot(glyph, mode):
    # (x, y) from the rendered alpha. 'tip' picks the ink pixel nearest the
    # top-left corner; 'centre' returns the ink centroid.
    w, h = glyph.size
    if isinstance(mode, tuple):
        return mode                      # authored point (drawn glyphs know where their tip is)
    ap = glyph.getchannel('A').load()
    if mode == 'centre':
        xs = ys = n = 0
        for y in range(h):
            for x in range(w):
                if ap[x, y] > 32:
                    xs += x
                    ys += y
                    n += 1
        return (int(round(xs / n)), int(round(ys / n))) if n else (w // 2, h // 2)
    best = None
    for y in range(h):
        for x in range(w):
            if ap[x, y] > 128:
                # 'tip_br': the working end sits at the lower right once the tool lies top-left -> bottom-right.
                d = (w - x) ** 2 + (h - y) ** 2 if mode == 'tip_br' else x * x + y * y
                if best is None or d < best[0]:
                    best = (d, x, y)
    return (best[1], best[2]) if best else (0, 0)


def load_fitted(gid, name=None):
    if gid.startswith('drawn:'):
        return DRAWN[gid.split(':', 1)[1]]()
    src = G / f'{gid}.png'
    if not src.exists():
        # The scan glyphs are not kept in the repo; ink/ holds each glyph's raw
        # stroke alpha on the fitted canvas (black = ink), and is the source of
        # truth for rebuilds. (Never read mono/ for this: once mono/ is filled
        # white its alpha is the whole silhouette, not the strokes.)
        prev = OUT / 'ink' / f'cursor_{name}.png'
        if not prev.exists():
            raise SystemExit(f'no glyph source for {name}: neither {src} nor {prev}')
        return Image.open(prev).convert('RGBA')
    im = Image.open(src).convert('RGBA')
    a = im.getchannel('A')
    bbox = a.getbbox()
    if bbox:
        im = im.crop(bbox)
    box = SIZE - 2 * MARGIN
    im.thumbnail((box, box), Image.LANCZOS)
    canvas = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    canvas.alpha_composite(im, ((SIZE - im.size[0]) // 2, (SIZE - im.size[1]) // 2))
    return canvas


def enclosed_mask(glyph):
    # 1 where a pixel is an ENCLOSED interior, 0 elsewhere.
    w, h = glyph.size
    ap = glyph.getchannel('A').load()

    not_ink = [[ap[x, y] <= INK_T for x in range(w)] for y in range(h)]
    outside = [[False] * w for _ in range(h)]

    stack = []
    for x in range(w):
        for y in (0, h - 1):
            if not_ink[y][x] and not outside[y][x]:
                outside[y][x] = True
                stack.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if not_ink[y][x] and not outside[y][x]:
                outside[y][x] = True
                stack.append((x, y))

    while stack:
        x, y = stack.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not_ink[ny][nx] and not outside[ny][nx]:
                outside[ny][nx] = True
                stack.append((nx, ny))

    return [[not_ink[y][x] and not outside[y][x] for x in range(w)] for y in range(h)]


def build_colour(glyph, fill):
    w, h = glyph.size
    enc = enclosed_mask(glyph)
    ap = glyph.getchannel('A').load()
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    op = out.load()
    for y in range(h):
        for x in range(w):
            if enc[y][x]:
                op[x, y] = (fill[0], fill[1], fill[2], 255)
            elif ap[x, y] > 0:
                op[x, y] = (OUTLINE[0], OUTLINE[1], OUTLINE[2], ap[x, y])
            else:
                op[x, y] = (0, 0, 0, 0)
    return out


# The HUD accent (docs/UI_DESIGN_SYSTEM.md): amber, with its hover (hi) and
# pressed (lo) steps as the light and shadow ends of the gradient.
ACCENT_HI = (241, 170, 104)
ACCENT = (224, 138, 60)
ACCENT_LO = (188, 112, 40)


def build_amber(glyph, cell=4, levels=6):
    # Same strokes as the black-and-white set, but the white interior becomes
    # a PIXELATED amber gradient: lit from the upper left with a bevel along
    # the inside of the outline, then quantised to a few shades on a coarse
    # pixel grid (with a 2x2 ordered dither between bands) so it reads as
    # chunky pixel-art shading rather than a smooth airbrush.
    import numpy as np
    from scipy import ndimage
    w, h = glyph.size
    enc = np.array(enclosed_mask(glyph), dtype=bool)
    a = np.array(glyph.getchannel('A'), dtype=np.float32)

    out = np.zeros((h, w, 4), dtype=np.float32)
    if enc.any():
        ys, xs = np.nonzero(enc)
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        span = max(1.0, float((x1 - x0) + (y1 - y0)))
        yy, xx = np.mgrid[0:h, 0:w]
        # Lightness 1 at the top-left corner of the filled area, 0 at the bottom-right.
        light = 1.0 - np.clip(((xx - x0) + (yy - y0)) / span, 0, 1)

        # Bevel: distance into the interior from the outline, its slope as the
        # surface normal; edges facing the light go lighter, facing away darker.
        dist = ndimage.distance_transform_edt(enc)
        gy, gx = np.gradient(ndimage.gaussian_filter(dist, 1.0))
        n = np.sqrt(gx * gx + gy * gy) + 1e-6
        facing = (-gx - gy) / n / np.sqrt(2)
        rim = np.clip(1.0 - dist / 6.0, 0, 1)
        light = np.clip(light * 0.7 + 0.15 + facing * rim * 0.45, 0, 1)

        # Quantise on a coarse grid: average each cell, dither with a 2x2 Bayer
        # threshold per cell, snap to one of `levels` shades.
        ch, cw = -(-h // cell), -(-w // cell)
        pad = np.zeros((ch * cell, cw * cell), dtype=np.float32)
        pad[:h, :w] = light
        cells = pad.reshape(ch, cell, cw, cell).mean(axis=(1, 3))
        bayer = (np.array([[0, 2], [3, 1]], dtype=np.float32) + 0.5) / 4.0 - 0.5   # [-0.375, 0.375]
        dither = np.tile(bayer, (-(-ch // 2), -(-cw // 2)))[:ch, :cw]
        q = np.clip(np.floor(cells * (levels - 1) + 0.5 + dither * 0.9), 0, levels - 1)
        q = np.kron(q, np.ones((cell, cell)))[:h, :w]

        # Shade ramp: lo darkened a step at the dark end, hi lifted toward white at the light end.
        hi, mid, lo = (np.array(c, dtype=np.float32) for c in (ACCENT_HI, ACCENT, ACCENT_LO))
        white = np.array([255, 255, 255], dtype=np.float32)
        stops = [lo * 0.8, lo, mid, hi, hi + (white - hi) * 0.35, hi + (white - hi) * 0.6]
        ramp = np.array(stops[:levels], dtype=np.float32)
        col = ramp[q.astype(int)]

        out[enc, :3] = np.clip(col[enc], 0, 255)
        out[enc, 3] = 255

    ink = (~enc) & (a > 0)
    out[ink, 0] = OUTLINE[0]
    out[ink, 1] = OUTLINE[1]
    out[ink, 2] = OUTLINE[2]
    out[ink, 3] = a[ink]
    return Image.fromarray(out.astype(np.uint8), 'RGBA')


def orient_tool(glyph, name):
    # Every tool lies the same way as the axe: main axis from the top-left to
    # the bottom-right. The axis is the ink's principal component; a glyph
    # drawn bottom-left to top-right is mirrored. Mirroring is decided from
    # the ink itself, so a rebuild never flips an already-correct glyph back.
    import numpy as np
    a = np.array(glyph.getchannel('A')) > INK_T
    ys, xs = np.nonzero(a)
    if len(xs) < 10:
        return glyph, False
    cov = np.cov(np.stack([xs - xs.mean(), ys - ys.mean()]))
    vals, vecs = np.linalg.eigh(cov)
    vx, vy = vecs[:, np.argmax(vals)]
    if vx * vy < 0:   # leaning the wrong way (y grows downwards, so TL->BR is vx*vy > 0)
        return glyph.transpose(Image.FLIP_LEFT_RIGHT), True
    return glyph, False


# Tools that lie along one axis and must match the axe. Crossed wrenches have no main axis.
ORIENTED_TOOLS = {'axe', 'axe_filled', 'handsaw', 'sawing', 'mattock', 'trowel', 'sickle',
                  'screwdriver', 'hammer', 'pickaxe'}


def build_mono(glyph):
    # Black and white only: the stroke stays black, enclosed interiors are
    # filled white, so the cursor reads on dark and light ground alike.
    return build_colour(glyph, (255, 255, 255))


if __name__ == '__main__':
    import json
    mono_dir = OUT / 'mono'
    col_dir = OUT / 'color'
    amber_dir = OUT / 'amber'
    amber_dir.mkdir(parents=True, exist_ok=True)
    mono_dir.mkdir(parents=True, exist_ok=True)
    col_dir.mkdir(parents=True, exist_ok=True)
    ink_dir = OUT / 'ink'
    ink_dir.mkdir(parents=True, exist_ok=True)

    manifest = {}
    filled = 0
    for gid, name, cat in CURSORS:
        g = load_fitted(gid, name)
        if name in ORIENTED_TOOLS and not gid.startswith('drawn:'):   # drawn glyphs are authored on the axis
            g, flipped = orient_tool(g, name)
            if flipped:
                print(f'  {name:24} mirrored to lie top-left -> bottom-right')
        # Keep the raw stroke alpha so the set can be rebuilt without the scans.
        ink = Image.new('RGBA', g.size, (0, 0, 0, 0))
        ink.putalpha(g.getchannel('A'))
        ink.save(ink_dir / f'cursor_{name}.png', 'PNG')
        build_mono(g).save(mono_dir / f'cursor_{name}.png', 'PNG')
        build_colour(g, PALETTE[cat]).save(col_dir / f'cursor_{name}.png', 'PNG')
        build_amber(g).save(amber_dir / f'cursor_{name}.png', 'PNG')

        mode = HOTSPOTS.get(name, 'centre')
        hx, hy = measure_hotspot(g, mode)

        n = sum(1 for row in enclosed_mask(g) for v in row if v)
        if n:
            filled += 1
        manifest[f'cursor_{name}'] = {
            'category': cat,
            'mono': f'mono/cursor_{name}.png',
            'color': f'color/cursor_{name}.png',
            'amber': f'amber/cursor_{name}.png',
            'size': [SIZE, SIZE],
            'hotspot': [hx, hy],
            'hotspot_mode': 'point' if isinstance(mode, tuple) else mode,
            'hotspot_note': HOTSPOT_NOTE.get(name, ''),
            'source_glyph': gid,
        }
        print(f'  {name:24} {cat:9} hotspot=({hx:3},{hy:3}) {str(mode):6} enclosed={n:5}')

    removed = [
        {'name': 'arrow_2', 'reason': 'duplicate of arrow (93.8% silhouette overlap)'},
        {'name': 'arrow_wait_2', 'reason': 'duplicate of arrow_wait (80.5%)'},
        {'name': 'arrow_unavailable_2', 'reason': 'duplicate of arrow_unavailable (91.5%)'},
    ]

    doc = {
        '_comment': (
            'Homesteader cursor set. Generated by tools/build_pointers.py from '
            'the pointers.jpg reference sheet. Hotspots are measured from each '
            'rendered image: tip = ink pixel nearest top-left, centre = ink '
            'centroid. Coordinates are in pixels from the top-left of the '
            f'{SIZE}x{SIZE} image, matching Cursor.SetCursor(texture, hotspot, mode).'
        ),
        'source_sheet': 'pointers.jpg',
        'canvas': [SIZE, SIZE],
        'margin': MARGIN,
        'variants': {
            'mono': 'Black and white only: black outline, enclosed interiors filled white.',
            'color': 'Category-coloured: outline kept, enclosed interiors flood-filled.',
            'amber': 'HUD accent: outline kept, interiors filled with an amber gradient and bevel lit from the upper left (3D look).',
        },
        'palette': {k: list(v) for k, v in PALETTE.items()},
        'cursors': manifest,
        'removed_duplicates': removed,
    }
    (OUT / 'cursors.json').write_text(json.dumps(doc, indent=2) + '\n', encoding='utf-8')

    # Unity's JsonUtility cannot bind a Dictionary, so it needs the cursors as
    # an ARRAY of {name, def} entries. Both shapes are written from this single
    # source so they cannot drift apart.
    array_doc = {
        'source_sheet': doc['source_sheet'],
        'canvas': doc['canvas'],
        'margin': doc['margin'],
        # Nested under 'def' to match CursorManager.CursorEntry {name, def}.
        'cursors': [{'name': k, 'def': v} for k, v in manifest.items()],
    }
    (OUT / 'cursors_array.json').write_text(
        json.dumps(array_doc, indent=2) + '\n', encoding='utf-8')

    print(f'\n{len(manifest)} cursors written to {OUT}')
    print(f'{filled}/{len(CURSORS)} glyphs had enclosed regions to fill')
    print('wrote cursors.json')
