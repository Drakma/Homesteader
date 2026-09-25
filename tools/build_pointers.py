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
from PIL import Image

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
    ('r1c04', 'sickle',                'tool'),
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
]

# Hotspot is where the click actually lands, so it is measured from the
# rendered alpha rather than guessed. 'tip' = the ink pixel nearest the top-left
# corner, correct for anything that points (arrows, fingers, tool cutting
# edges). 'centre' = the ink centroid, correct for objects the player grabs or
# that rotate about themselves (resize arrows, gears, buckets).
HOTSPOTS = {
    'axe': 'tip', 'handsaw': 'tip', 'log_rings': 'centre', 'sawing': 'tip',
    'mattock': 'tip', 'plant_seedling': 'centre', 'wheat_sheaf': 'centre',
    'trowel': 'tip', 'axe_filled': 'tip', 'plant_seedling_filled': 'centre',
    'wheat_sheaf_filled': 'centre', 'bucket_carry': 'centre', 'sickle': 'tip',
    'egg': 'centre', 'egg_basket': 'centre', 'wrenches': 'centre',
    'gear': 'centre', 'jerrycan': 'centre', 'screwdriver': 'tip',
    'hammer': 'tip', 'pickaxe': 'tip', 'finger_point': 'tip',
    'seed_sack': 'centre', 'tool_belt': 'centre', 'arrow': 'tip',
    'hand_open': 'centre', 'finger_tap': 'tip', 'move': 'centre',
    'ibeam': 'centre', 'arrow_wait': 'tip', 'arrow_unavailable': 'tip',
    'wait_settings': 'centre', 'wait_settings_2': 'centre',
    'resize_vertical': 'centre', 'resize_horizontal': 'centre',
    'resize_nwse': 'centre', 'resize_nesw': 'centre', 'resize_all': 'centre',
    'help': 'tip',
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
                d = x * x + y * y
                if best is None or d < best[0]:
                    best = (d, x, y)
    return (best[1], best[2]) if best else (0, 0)


def load_fitted(gid):
    im = Image.open(G / f'{gid}.png').convert('RGBA')
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


def build_mono(glyph):
    w, h = glyph.size
    ap = glyph.getchannel('A').load()
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    op = out.load()
    for y in range(h):
        for x in range(w):
            op[x, y] = (0, 0, 0, ap[x, y])
    return out


if __name__ == '__main__':
    import json
    mono_dir = OUT / 'mono'
    col_dir = OUT / 'color'
    mono_dir.mkdir(parents=True, exist_ok=True)
    col_dir.mkdir(parents=True, exist_ok=True)

    manifest = {}
    filled = 0
    for gid, name, cat in CURSORS:
        g = load_fitted(gid)
        build_mono(g).save(mono_dir / f'cursor_{name}.png', 'PNG')
        build_colour(g, PALETTE[cat]).save(col_dir / f'cursor_{name}.png', 'PNG')

        mode = HOTSPOTS.get(name, 'centre')
        hx, hy = measure_hotspot(g, mode)

        n = sum(1 for row in enclosed_mask(g) for v in row if v)
        if n:
            filled += 1
        manifest[f'cursor_{name}'] = {
            'category': cat,
            'mono': f'mono/cursor_{name}.png',
            'color': f'color/cursor_{name}.png',
            'size': [SIZE, SIZE],
            'hotspot': [hx, hy],
            'hotspot_mode': mode,
            'hotspot_note': HOTSPOT_NOTE.get(name, ''),
            'source_glyph': gid,
        }
        print(f'  {name:24} {cat:9} hotspot=({hx:3},{hy:3}) {mode:6} enclosed={n:5}')

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
            'mono': 'Black line art on transparency, as scanned.',
            'color': 'Category-coloured: outline kept, enclosed interiors flood-filled.',
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
        'cursors': [dict({'name': k}, **v) for k, v in manifest.items()],
    }
    (OUT / 'cursors_array.json').write_text(
        json.dumps(array_doc, indent=2) + '\n', encoding='utf-8')

    print(f'\n{len(manifest)} cursors written to {OUT}')
    print(f'{filled}/{len(CURSORS)} glyphs had enclosed regions to fill')
    print('wrote cursors.json')
