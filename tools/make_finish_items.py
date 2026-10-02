"""
Creates the building FINISH items in headless Blender (free, local): paints, carpets and tiles, sidings, roofings, bricks and a
field stone. Each gets a small procedural model (GLB), a manifest and a README beside it; the icons are rendered afterwards from the
models (python tools/render_icon_from_model.py, see tools/finish_items_icons.py). What a finish looks like on a building is data on the
item (properties.look_*), read by the game when a stage is built from it (docs/CONSTRUCTION.md, "Look follows the materials").

    blender --background --python tools/make_finish_items.py

Safe to re-run: it rewrites the models, manifests and READMEs of the items listed in ITEMS (and nothing else).
"""
import copy
import json
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_structure_stages as base  # noqa: E402

ROOT = base.ROOT
Builder = base.Builder
mat = base.material

CARDBOARD = (0.62, 0.5, 0.34)


def hexrgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


# --------------------------------------------------------------------------- models

def m_paint(b, c, **_):
    can, paint = mat('Can', (0.72, 0.72, 0.75), 0.4), mat('Paint', c, 0.5)
    b.log((0, 0, 0), (0, 0, 0.2), 0.14, can, sides=14)
    b.log((0, 0, 0.2), (0, 0, 0.214), 0.15, can, sides=14)
    b.log((0, 0, 0.2), (0, 0, 0.206), 0.125, paint, sides=14)
    b.log((0, 0, 0.045), (0, 0, 0.155), 0.1425, paint, sides=14)             # the label band, in the paint colour
    b.box(-0.015, 0.015, -0.16, 0.16, 0.215, 0.23, can)                      # a bail across the top


def m_carpet(b, c, **_):
    cloth, core = mat('Carpet', c, 0.95), mat('Core', CARDBOARD, 0.9)
    b.log((-0.6, 0, 0.14), (0.6, 0, 0.14), 0.14, cloth, sides=14)
    b.log((-0.63, 0, 0.14), (0.63, 0, 0.14), 0.045, core, sides=10)


def m_tile(b, c, smooth=0.6, **_):
    box, tile, grout = mat('Carton', CARDBOARD, 0.9), mat('Tile', c, 1.0 - smooth), mat('Grout', (0.75, 0.75, 0.73), 0.95)
    b.box(-0.22, 0.22, -0.22, 0.22, 0.0, 0.17, box)
    b.box(-0.2, 0.2, -0.2, 0.2, 0.17, 0.176, grout)
    for i in range(3):
        for j in range(3):
            x0, y0 = -0.195 + i * 0.1325, -0.195 + j * 0.1325
            b.box(x0, x0 + 0.125, y0, y0 + 0.125, 0.176, 0.19, tile)


def m_siding(b, c, **_):
    board, strap = mat('Siding', c, 0.8), mat('Strap', (0.2, 0.2, 0.22), 0.6)
    for k in range(8):
        b.box(-0.6, 0.6, -0.1, 0.1, k * 0.032, k * 0.032 + 0.028, board)
    for x in (-0.35, 0.35):
        b.box(x - 0.02, x + 0.02, -0.11, 0.11, -0.003, 0.26, strap)


def m_shingle(b, c, smooth=0.15, **_):
    shingle = mat('Shingle', c, 1.0 - smooth)
    dark = mat('ShingleDark', tuple(v * 0.6 for v in c), 0.9)
    b.box(-0.3, 0.3, -0.18, 0.18, 0.0, 0.1, shingle)
    for k in range(1, 6):
        b.box(-0.3, 0.3, -0.18 + k * 0.06, -0.18 + k * 0.06 + 0.012, 0.1, 0.103, dark)
    b.box(-0.02, 0.02, -0.19, 0.19, -0.005, 0.105, mat('Strap', (0.2, 0.2, 0.22), 0.6))


def m_tileroof(b, c, smooth=0.4, **_):
    t = mat('RoofTile', c, 1.0 - smooth)
    for k in range(6):
        b.box(-0.2, 0.2, -0.13, 0.13, k * 0.05, k * 0.05 + 0.045, t)
        for r in range(4):
            b.box(-0.2 + 0.05 + r * 0.1, -0.2 + 0.07 + r * 0.1, -0.13, 0.13, k * 0.05 + 0.045, k * 0.05 + 0.06, t)   # the ribs


def m_metal(b, c, smooth=0.6, metal=0.8, **_):
    sheet = mat('Metal', c, 1.0 - smooth)
    for k in range(3):
        b.box(-0.6, 0.6, -0.4, 0.4, k * 0.025, k * 0.025 + 0.02, sheet)
        for r in range(8):
            x = -0.55 + r * 0.15
            b.box(x, x + 0.03, -0.4, 0.4, k * 0.025 + 0.02, k * 0.025 + 0.04, sheet)
    b.box(-0.02, 0.02, -0.42, 0.42, -0.004, 0.09, mat('Strap', (0.2, 0.2, 0.22), 0.6))


def m_thatch(b, c, **_):
    straw, strap = mat('Thatch', c, 0.98), mat('Strap', (0.35, 0.25, 0.15), 0.9)
    b.log((-0.45, 0, 0.18), (0.45, 0, 0.18), 0.18, straw, sides=10)
    for x in (-0.25, 0.25):
        b.log((x - 0.015, 0, 0.18), (x + 0.015, 0, 0.18), 0.19, strap, sides=10)


def m_brick(b, c, smooth=0.1, **_):
    brick, pallet = mat('Brick', c, 1.0 - smooth), mat('Pallet', (0.55, 0.42, 0.27), 0.9)
    b.box(-0.35, 0.35, -0.25, 0.25, 0.0, 0.05, pallet)
    for layer in range(4):
        z0 = 0.05 + layer * 0.07
        for i in range(3):
            for j in range(4):
                x0, y0 = -0.34 + i * 0.23, -0.24 + j * 0.12
                b.box(x0, x0 + 0.215, y0, y0 + 0.108, z0, z0 + 0.065, brick)


def m_stone(b, c, **_):
    stone = mat('Stone', c, 0.97)
    import random
    rnd = random.Random(7)
    for k in range(9):
        r = rnd.uniform(0.09, 0.16)
        x, y = rnd.uniform(-0.3, 0.3), rnd.uniform(-0.2, 0.2)
        z = r * 0.7 + (0.12 if k > 5 else 0.0)
        res = bmesh.ops.create_icosphere(b.bm, subdivisions=1, radius=r)
        i = b.mat_index(stone)
        for v in res['verts']:
            v.co.x, v.co.y, v.co.z = v.co.x * rnd.uniform(1.0, 1.4) + x, v.co.y * rnd.uniform(0.9, 1.3) + y, v.co.z * 0.8 + z
        for f in b.bm.faces:
            if all(v in res['verts'] for v in f.verts):
                f.material_index = i


KINDS = {'paint': m_paint, 'carpet': m_carpet, 'tile': m_tile, 'siding': m_siding, 'shingle': m_shingle, 'tileroof': m_tileroof,
         'metal': m_metal, 'thatch': m_thatch, 'brick': m_brick, 'stone': m_stone}
DIMS = {'paint': (0.3, 0.23, 0.32), 'carpet': (1.26, 0.28, 0.28), 'tile': (0.44, 0.19, 0.44), 'siding': (1.2, 0.26, 0.22),
        'shingle': (0.6, 0.1, 0.38), 'tileroof': (0.4, 0.3, 0.26), 'metal': (1.2, 0.09, 0.84), 'thatch': (0.9, 0.36, 0.36),
        'brick': (0.7, 0.33, 0.5), 'stone': (0.8, 0.3, 0.6)}

# --------------------------------------------------------------------------- the items
# (id, name, kind, colour, look_target, smoothness, metallic, price, unit, stack, weight_kg, extra properties)
ITEMS = []


def add(i, name, kind, col, target, sm, met, price, unit, stack, kg, category='building', **extra):
    ITEMS.append(dict(id=i, name=name, kind=kind, color=col, target=target, smooth=sm, metal=met, price=price, unit=unit, stack=stack,
                      kg=kg, category=category, extra=extra))


for slug, name, col in (('ivory', 'Ivory', '#f1ecdc'), ('cream', 'Warm Cream', '#ead9b0'), ('sage', 'Sage Green', '#a9b99a'),
                        ('sky_blue', 'Sky Blue', '#9cc4e0'), ('navy', 'Deep Navy', '#27395e'), ('barn_red', 'Barn Red', '#8e2f26'),
                        ('charcoal', 'Charcoal', '#3b3d42'), ('mustard', 'Mustard Yellow', '#d6a935'), ('lavender', 'Lavender', '#b7a6d4'),
                        ('terracotta', 'Terracotta', '#c4694a')):
    add(f'building_paint_{slug}', f'Interior Paint: {name}', 'paint', col, 'interior', 0.25, 0.0, 34, 'can', 4, 5.0)

for slug, name, kind, col, sm in (('carpet_beige', 'Beige Carpet', 'carpet', '#cdb994', 0.04), ('carpet_grey', 'Grey Carpet', 'carpet', '#8a8d92', 0.04),
                                  ('carpet_brown', 'Brown Carpet', 'carpet', '#6b4a33', 0.04), ('carpet_navy', 'Navy Carpet', 'carpet', '#2c3a5c', 0.04),
                                  ('carpet_burgundy', 'Burgundy Carpet', 'carpet', '#6e2231', 0.04),
                                  ('tile_white', 'White Ceramic Tile', 'tile', '#ecebe6', 0.8), ('tile_slate', 'Slate Tile', 'tile', '#4b5057', 0.5),
                                  ('tile_terracotta', 'Terracotta Tile', 'tile', '#b8643f', 0.35), ('tile_speckled', 'Speckled Grey Tile', 'tile', '#a9a9a4', 0.6),
                                  ('vinyl_plank', 'Wood-look Vinyl Plank', 'tile', '#a47a4f', 0.3)):
    add(f'building_floor_{slug}', name, kind, col, 'floor', sm, 0.0, 120 if kind == 'carpet' else 85, 'roll' if kind == 'carpet' else 'box',
        6 if kind == 'carpet' else 10, 22.0 if kind == 'carpet' else 18.0)

for slug, name, col, sm in (('cream', 'Cream Clapboard Siding', '#e3d6b4', 0.2), ('white', 'White Clapboard Siding', '#eeeeea', 0.25),
                            ('barn_red', 'Barn Red Board Siding', '#8a3128', 0.2), ('slate_blue', 'Slate Blue Clapboard Siding', '#5b7189', 0.2),
                            ('sage', 'Sage Green Clapboard Siding', '#8fa387', 0.2), ('cedar_shake', 'Cedar Shake Siding', '#9a6b3f', 0.1),
                            ('weathered_grey', 'Weathered Grey Shiplap', '#8d8f8c', 0.1), ('charcoal_batten', 'Charcoal Board and Batten', '#3d4044', 0.2),
                            ('brick_veneer', 'Red Brick Veneer', '#9a4a3a', 0.15), ('stucco_tan', 'Tan Stucco Panels', '#cbb48c', 0.05)):
    add(f'building_siding_{slug}', name, 'siding', col, 'walls', sm, 0.0, 140, 'bundle', 8, 30.0)

add('roofing_shingles_brown', 'Brown Asphalt Shingles', 'shingle', '#5a4636', 'roof', 0.15, 0.0, 85, 'bundle', 12, 28.0)
add('roofing_shingles_weathered', 'Weathered Wood Shingles', 'shingle', '#7b7568', 'roof', 0.1, 0.0, 95, 'bundle', 12, 26.0)
add('roofing_shingles_red', 'Red Asphalt Shingles', 'shingle', '#8a3b30', 'roof', 0.15, 0.0, 85, 'bundle', 12, 28.0)
add('roofing_shingles_green', 'Forest Green Shingles', 'shingle', '#3f5b44', 'roof', 0.15, 0.0, 85, 'bundle', 12, 28.0)
add('roofing_cedar_shakes', 'Cedar Shake Roofing', 'shingle', '#9c6e44', 'roof', 0.08, 0.0, 130, 'bundle', 12, 24.0)
add('roofing_slate_tile', 'Natural Slate Tile', 'tileroof', '#5a6068', 'roof', 0.5, 0.0, 240, 'pallet', 6, 90.0)
add('roofing_clay_tile', 'Terracotta Clay Tile', 'tileroof', '#b3613f', 'roof', 0.35, 0.0, 220, 'pallet', 6, 85.0)
add('roofing_seam_red', 'Standing Seam Red Metal Roofing', 'metal', '#8f2d27', 'roof', 0.6, 0.85, 160, 'bundle', 8, 35.0)
add('roofing_seam_green', 'Standing Seam Green Metal Roofing', 'metal', '#2f6a49', 'roof', 0.6, 0.85, 160, 'bundle', 8, 35.0)
add('roofing_seam_black', 'Standing Seam Black Metal Roofing', 'metal', '#25272b', 'roof', 0.6, 0.85, 170, 'bundle', 8, 35.0)
add('roofing_thatch', 'Reed Thatch Bundle', 'thatch', '#c9a85c', 'roof', 0.02, 0.0, 70, 'bundle', 14, 16.0)

for slug, name, col in (('brown', 'Brown', '#6a3f2c'), ('tan', 'Tan', '#c9a27a'), ('white', 'White Washed', '#d9d4c7'), ('grey', 'Grey', '#8a8984'),
                        ('charcoal', 'Charcoal', '#43454a'),
                        # the reds: a family of red bricks, light to deep
                        ('salmon', 'Salmon Red', '#c9755c'), ('rust', 'Rust Red', '#a4472f'), ('dark_red', 'Dark Red', '#7a2c24'),
                        ('oxblood', 'Oxblood', '#5a1f1f'), ('old_mill', 'Old Mill Red', '#8c4a3a'), ('pressed_red', 'Pressed Red', '#b0402f')):
    add(f'masonry_brick_{slug}', f'{name} Brick', 'brick', col, 'chimney,foundation', 0.1, 0.0, 110, 'pallet', 6, 120.0, look_style='brick')
add('masonry_fieldstone', 'Field Stone', 'stone', '#8f8a80', 'chimney,foundation', 0.05, 0.0, 95, 'pile', 6, 150.0, look_style='brick')

# existing items that become part of the system (only their look properties and tag membership change)
EXISTING = {
    'building/masonry_brick_red': dict(look_target='chimney,foundation', look_color='#9b4a3a', look_smoothness=0.1, look_metallic=0.0, look_style='brick'),
    'building/masonry_cinder_block': dict(look_target='foundation', look_color='#9b9b97', look_smoothness=0.05, look_metallic=0.0, look_style='block'),
    'building/80lb_cement_bag': dict(look_target='foundation', look_color='#9a9a96', look_smoothness=0.05, look_metallic=0.0, look_style='poured'),
    'building/post_wood_round_6inch': dict(look_target='foundation', look_color='#735236', look_smoothness=0.1, look_metallic=0.0, look_style='stilts'),
    'building/building_paint_interior_wall': dict(look_target='interior', look_color='#f1eee6', look_smoothness=0.25, look_metallic=0.0),
    'building/part_floor_wood_1m': dict(look_target='floor', look_color='#9a7048', look_smoothness=0.3, look_metallic=0.0),
    'building/part_floor_stone_1m': dict(look_target='floor', look_color='#8d8c88', look_smoothness=0.5, look_metallic=0.0),
}


def build_model(it, out):
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    b = Builder(it['id'])
    KINDS[it['kind']](b, hexrgb(it['color']), smooth=it['smooth'], metal=it['metal'])
    obj = b.finish()
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_yup=True)
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def write_manifest(it, folder, tris):
    tmpl = json.load(open(os.path.join(ROOT, 'assets', 'building', 'building_paint_interior_wall', 'building_paint_interior_wall.json'), encoding='utf-8'))
    m = copy.deepcopy(tmpl)
    w, h, dpt = DIMS[it['kind']]
    m['id'] = it['id']
    m['name'] = it['name']
    m['category'] = it['category']
    m['icon'] = it['id'] + '.png'
    m['description'] = f"{it['name']}: a building finish. Used as a construction material it sets how that part of the building looks."
    p = m['properties']
    p['weight_kg'] = it['kg']
    p['max_stack_size'] = it['stack']
    p['base_value'] = it['price']
    p['footprint'] = f'{w}m W x {dpt}m D x {h}m H'
    p['is_buyable'] = True
    p['stores'] = ['depot']
    p['sale_unit'] = it['unit']
    p['look_target'] = it['target']
    p['look_color'] = it['color']
    p['look_smoothness'] = it['smooth']
    p['look_metallic'] = it['metal']
    for k, v in it['extra'].items():
        p[k] = v
    m['models'] = [{'file': it['id'] + '.glb', 'format': 'glb', 'dimensions_m': {'x': w, 'y': h, 'z': dpt}, 'triangles': tris}]
    m['category_fields'] = {'dimensions_m': {'width': w, 'depth': dpt, 'height': h}}
    json.dump(m, open(os.path.join(folder, it['id'] + '.json'), 'w', encoding='utf-8'), indent=2)
    open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8').write(
        f"# {it['name']}\n\nCategory: {it['category']}. Look target: {it['target']}, colour {it['color']}.\n\n"
        f"Generated by tools/make_finish_items.py (procedural model, {tris} triangles).\n")


def main():
    made = []
    for it in ITEMS:
        folder = os.path.join(ROOT, 'assets', it['category'], it['id'])
        os.makedirs(folder, exist_ok=True)
        tris = build_model(it, os.path.join(folder, it['id'] + '.glb'))
        write_manifest(it, folder, tris)
        made.append(it['id'])
        print('item', it['id'], tris)
    for rel, props in EXISTING.items():
        cat, iid = rel.split('/')
        p = os.path.join(ROOT, 'assets', cat, iid, iid + '.json')
        m = json.load(open(p, encoding='utf-8'))
        m.setdefault('properties', {}).update(props)
        json.dump(m, open(p, 'w', encoding='utf-8'), indent=2)
        print('existing', iid)
    json.dump(made, open(os.path.join(ROOT, 'tools', '_finish_items.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
