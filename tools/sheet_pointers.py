# Labelled sheets for the cursor set: mono, colour, and side-by-side, plus a
# true-size strip (48px) since that is the size HUD elements actually render at.
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r'C:\Users\casey\Desktop\Homesteader')
OUT = ROOT / 'assets' / 'hud_kit' / 'cursors'

# Grouped so the sheet reads by purpose rather than by source-sheet order.
GROUPS = [
    ('Farm and forestry',
     ['axe', 'axe_filled', 'handsaw', 'log_rings', 'sawing', 'mattock',
      'trowel', 'sickle']),
    ('Harvest and livestock',
     ['plant_seedling', 'plant_seedling_filled', 'wheat_sheaf',
      'wheat_sheaf_filled', 'bucket_carry', 'egg', 'egg_basket', 'seed_sack']),
    ('Tools and trades',
     ['wrenches', 'gear', 'jerrycan', 'screwdriver', 'hammer', 'pickaxe',
      'tool_belt']),
    ('System pointers',
     ['arrow', 'arrow_wait', 'arrow_unavailable', 'wait_settings',
      'wait_settings_2', 'hand_open', 'finger_point', 'finger_tap',
      'move', 'ibeam', 'help']),
    ('Resize',
     ['resize_all', 'resize_vertical', 'resize_horizontal',
      'resize_nwse', 'resize_nesw']),
]

CELL = 138
PAD = 8
LABEL = 26
COLS = 8
BG = (36, 44, 56, 255)
FG = (236, 241, 247, 255)
GRID = (74, 86, 104, 255)
TITLE = (193, 154, 60, 255)


def font(sz, bold=False):
    name = 'segoeuib.ttf' if bold else 'segoeui.ttf'
    try:
        return ImageFont.truetype(f'C:/Windows/Fonts/{name}', sz)
    except Exception:
        return ImageFont.load_default()


def load(variant, name):
    for ext in ('.png',):
        p = OUT / variant / f'cursor_{name}{ext}'
        if p.exists():
            return Image.open(p).convert('RGBA')
    return None


def sheet(variants, dest, show_title=True):
    cols = COLS
    rows_total = sum((len(names) + cols - 1) // cols for _, names in GROUPS)
    # Header allowance per group.
    H = 46 * len(GROUPS) + rows_total * (CELL + LABEL) + 60
    W = cols * CELL
    img = Image.new('RGBA', (W * len(variants), H), BG)
    d = ImageDraw.Draw(img)

    if show_title:
        d.text((16, 12), 'Homesteader - Cursors', fill=TITLE, font=font(22, True))
        d.text((W * len(variants) - 320, 20),
               f'{sum(len(n) for _, n in GROUPS)} pointers  |  {labels}',
               fill=FG, font=font(13))

    for vi, variant in enumerate(variants):
        ox = vi * W
        y = 56
        for gname, names in GROUPS:
            d.text((ox + 16, y + 6), gname, fill=TITLE, font=font(15, True))
            y += 40
            for i, nm in enumerate(names):
                im = load(variant, nm)
                if im is None:
                    continue
                im.thumbnail((CELL - 2 * PAD, CELL - 2 * PAD), Image.LANCZOS)
                x = ox + (i % cols) * CELL
                yy = y + (i // cols) * (CELL + LABEL)
                img.alpha_composite(im, (x + (CELL - im.size[0]) // 2,
                                         yy + (CELL - im.size[1]) // 2))
                d.rectangle([x, yy, x + CELL - 1, yy + CELL - 1], outline=GRID)
                tw = d.textlength(nm, font=font(13))
                d.text((x + (CELL - tw) / 2, yy + CELL + 4), nm,
                       fill=FG, font=font(13))
            used = (len(names) + cols - 1) // cols
            y += used * (CELL + LABEL) + 8

    img.convert('RGB').save(dest, 'PNG')
    print(f'wrote {dest.name}  ({img.size[0]}x{img.size[1]})')


labels = 'mono + colour'

# 1. Mono sheet.
sheet(['mono'], OUT / 'sheet_mono.png')

# 2. Colour sheet.
sheet(['color'], OUT / 'sheet_color.png')

# 3. Side-by-side, same cursor in both variants for direct comparison.
W = COLS * CELL
rows_total = sum((len(n) + COLS - 1) // COLS for _, n in GROUPS)
H = 46 * len(GROUPS) + rows_total * (CELL + LABEL) + 60
img = Image.new('RGBA', (W, H), BG)
d = ImageDraw.Draw(img)
d.text((16, 12), 'Homesteader - Cursors: mono vs colour', fill=TITLE, font=font(22, True))
d.text((16, 40), 'left = mono (as scanned)    right = colour (kit palette)',
       fill=FG, font=font(14))
y = 76
HALF = (CELL - 2 * PAD) // 2
for gname, names in GROUPS:
    d.text((16, y), gname, fill=TITLE, font=font(15, True))
    y += 38
    for i, nm in enumerate(names):
        x = (i % COLS) * CELL
        yy = y + (i // COLS) * (CELL + LABEL)
        for vi, variant in enumerate(['mono', 'color']):
            im = load(variant, nm)
            if im is None:
                continue
            im.thumbnail((HALF, CELL - 2 * PAD), Image.LANCZOS)
            img.alpha_composite(im, (x + vi * HALF + (HALF - im.size[0]) // 2,
                                     yy + (CELL - im.size[1]) // 2))
        d.rectangle([x, yy, x + CELL - 1, yy + CELL - 1], outline=GRID)
        tw = d.textlength(nm, font=font(12))
        d.text((x + (CELL - tw) / 2, yy + CELL + 3), nm, fill=FG, font=font(12))
    used = (len(names) + COLS - 1) // COLS
    y += used * (CELL + LABEL) + 8
img.convert('RGB').save(OUT / 'sheet_compare.png', 'PNG')
print(f'wrote sheet_compare.png  ({img.size[0]}x{img.size[1]})')

# 4. True-size strip at 48px, the real HUD size.
allnames = [n for _, names in GROUPS for n in names]
sw = 60
strip = Image.new('RGBA', (sw * len(allnames), sw * 2 + 30), BG)
d = ImageDraw.Draw(strip)
for vi, variant in enumerate(['mono', 'color']):
    for i, nm in enumerate(allnames):
        im = load(variant, nm)
        if im is None:
            continue
        im = im.resize((44, 44), Image.LANCZOS)
        strip.alpha_composite(im, (i * sw + (sw - 44) // 2, vi * sw + 10))
strip.convert('RGB').save(OUT / 'sheet_48px.png', 'PNG')
print(f'wrote sheet_48px.png  ({strip.size[0]}x{strip.size[1]})')
