"""
Writes the LOT blueprints (assets/building/lot_dirt, lot_gravel, lot_asphalt, lot_concrete): manifest, README and a drawn icon (no model, like the path kits). A lot blueprint is bought
once at the depot and lays its surface over an area of any size and shape (LotBuilder.cs, docs/LOTS.md).

    python tools/make_lot_blueprints.py
"""
import json
import os
import random

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'building')

LOTS = {
    'lot_dirt': dict(name='Dirt Lot Blueprint', style='dirt', material='mat_pile_dirt_small', m2=3.5, price=90, fill=(124, 92, 60), dark=(92, 66, 42),
                     desc='lays a packed dirt yard, drive or pen over an area of any size'),
    'lot_gravel': dict(name='Gravel Lot Blueprint', style='gravel', material='mat_pile_gravel_medium', m2=8.0, price=220, fill=(160, 155, 145), dark=(112, 108, 100),
                       desc='lays a gravel yard, drive or parking area over an area of any size'),
    'lot_asphalt': dict(name='Asphalt Lot Blueprint', style='asphalt', material='mat_pile_gravel_medium', m2=6.0, price=650, fill=(52, 52, 58), dark=(32, 32, 38),
                        desc='paves a parking lot or yard with asphalt over an area of any size'),
    'lot_concrete': dict(name='Concrete Lot Blueprint', style='concrete', material='building_concrete_mix_bag', m2=1.5, price=480, fill=(176, 176, 170), dark=(128, 128, 122),
                         desc='pours a concrete pad, apron or floor slab over an area of any size'),
}


def manifest(iid, c):
    return {
        '$schema': 'https://homesteader.game/schemas/item_v1.json',
        'id': iid, 'name': c['name'], 'category': 'building',
        'description': 'A blueprint, bought once and yours for good. Hold it, click the corners of a lot (two opposite corners make a rectangle, more corners any other shape) and press Enter: it %s.' % c['desc'],
        'icon': iid + '.png',
        'properties': {
            'weight_kg': 0, 'max_stack_size': 1, 'base_value': c['price'], 'is_consumable': False, 'footprint': '(X=1,Y=1)',
            'happiness_modifier': 0, 'thirst_restore': 0, 'energy_restore': 0, 'stamina_restore': 0, 'wellness_modifier': 0,
            'is_buyable': True, 'stores': ['depot'], 'sale_unit': 'blueprint', 'is_blueprint': True,
            'lot_style': c['style'], 'lot_material_item': c['material'], 'lot_m2_per_item': c['m2'],
        },
        'category_fields': {'dimensions_m': {'width': 0.6, 'depth': 0.4, 'height': 0.2}},
    }


def icon(iid, c):
    S = 4
    im = Image.new('RGBA', (128 * S, 128 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = 64 * S, 66 * S
    w, h, t = 44 * S, 24 * S, 7 * S                      # an isometric slab: half width, half height, thickness
    top = [(cx - w, cy), (cx, cy - h), (cx + w, cy), (cx, cy + h)]
    left = [(cx - w, cy), (cx, cy + h), (cx, cy + h + t), (cx - w, cy + t)]
    right = [(cx, cy + h), (cx + w, cy), (cx + w, cy + t), (cx, cy + h + t)]
    d.polygon([(x, y + 6 * S) for x, y in top], fill=(0, 0, 0, 60))
    d.polygon(left, fill=c['dark'] + (255,))
    d.polygon(right, fill=tuple(int(v * 0.8) for v in c['dark']) + (255,))
    d.polygon(top, fill=c['fill'] + (255,))
    random.seed(iid)
    style = c['style']
    for _ in range(160):
        u, v = random.random(), random.random()
        x = cx + (u - v) * w * 0.92
        y = cy + (u + v - 1.0) * h * 0.92
        if abs(x - cx) / w + abs(y - cy) / h > 0.9:
            continue
        r = random.uniform(0.6, 1.7) * S
        col = tuple(max(0, min(255, int(f + random.randint(-26, 26)))) for f in c['fill']) if style != 'dirt' else tuple(max(0, f - random.randint(0, 24)) for f in c['fill'])
        d.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=col + (255,))
    if style == 'concrete':                               # expansion joints
        d.line([(cx - w * 0.5, cy - h * 0.5), (cx + w * 0.5, cy + h * 0.5)], fill=c['dark'] + (255,), width=int(1.2 * S))
        d.line([(cx - w * 0.5, cy + h * 0.5), (cx + w * 0.5, cy - h * 0.5)], fill=c['dark'] + (255,), width=int(1.2 * S))
    if style == 'asphalt':                                # a painted bay line
        d.line([(cx - w * 0.15, cy - h * 0.55), (cx + w * 0.55, cy + h * 0.15)], fill=(236, 214, 120, 255), width=int(1.6 * S))
    for x, y in top:                                       # the corner markers of the lot
        d.ellipse([x - 3.2 * S, y - 3.2 * S, x + 3.2 * S, y + 3.2 * S], fill=(53, 99, 124, 255), outline=(255, 255, 255, 255), width=int(0.8 * S))
    im = im.resize((128, 128), Image.LANCZOS)
    px = im.load()
    for x in range(128):                                   # 100 % transparent outer perimeter
        for y in (0, 127):
            px[x, y] = (0, 0, 0, 0)
    for y in range(128):
        for x in (0, 127):
            px[x, y] = (0, 0, 0, 0)
    return im


def main():
    for iid, c in LOTS.items():
        folder = os.path.join(OUT, iid)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, iid + '.json'), 'w', encoding='utf-8', newline=chr(10)) as f:
            json.dump(manifest(iid, c), f, indent=2, ensure_ascii=False)
            f.write(chr(10))
        with open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8', newline=chr(10)) as f:
            f.write('# ' + c['name'] + chr(10) + chr(10) + manifest(iid, c)['description'] + chr(10))
        icon(iid, c).save(os.path.join(folder, iid + '.png'))
        print('wrote', iid)


if __name__ == '__main__':
    main()
