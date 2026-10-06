"""
Builds the workshop shelving units (assets/building/building_shelving_*) as GLBs in headless Blender: free, local, low-poly (no Meshy).

    blender --background --python tools/make_shelving_units.py
    python tools/generate_unity_asset_catalog.py
    python tools/render_icon_from_model.py assets/building/<id>/<id>.glb assets/building/<id>/<id>.png      (each)

Three free-standing units, 1.2 m wide, 0.6 m deep and 2.0 m high, each with FOUR deep shelves:
  building_shelving_melamine_white   white melamine boards, a thin back panel, a kick plate
  building_shelving_melamine_black   the same in black melamine
  building_shelving_steel            a bolted steel frame (four angle posts, braced across the back) with sheet-steel shelves

They are placed things that carry items like a pallet (`support_surface`), once for each shelf (`deck_heights`, the height of every shelf's top face): point at the open front
of a shelf and the item goes ON that shelf, packed side by side and stacked up to its stacking limit, as far up as the next shelf allows (PalletDeck.cs, docs/PALLETS or ATTACHED_ITEMS).

An item that is already in the kit keeps its name, price and the rest; a new one gets its manifest from the wood pallet.

Conventions: 1 unit = 1 m, pivot at the centre of the footprint, ground at z = 0, the open front facing -y.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_simple_props as props  # noqa: E402    (Kit, mat, save)

BUILDING = os.path.join(props.ROOT, 'assets', 'building')
T = Matrix.Translation
mat = props.mat

W, D, H = 1.2, 0.6, 2.0
DECKS = [0.15, 0.62, 1.09, 1.56]        # the top face of each shelf
DECK_TEXT = ', '.join('%.2f' % d for d in DECKS)

UNITS = {
    'building_shelving_melamine_white': dict(name='White Melamine Shelving Unit', kind='melamine', rgb=(0.93, 0.93, 0.91), edge=(0.82, 0.82, 0.8), kg=48.0, price=95,
                                             text='A 2 m workshop shelving unit in white melamine, with four deep shelves and a back panel.'),
    'building_shelving_melamine_black': dict(name='Black Melamine Shelving Unit', kind='melamine', rgb=(0.07, 0.07, 0.08), edge=(0.16, 0.16, 0.17), kg=48.0, price=95,
                                             text='A 2 m workshop shelving unit in black melamine, with four deep shelves and a back panel.'),
    'building_shelving_steel': dict(name='Steel Shelving Unit', kind='steel', rgb=(0.64, 0.66, 0.69), edge=(0.2, 0.22, 0.26), kg=36.0, price=120,
                                    text='A 2 m bolted steel workshop shelving unit with four deep shelves, braced across the back.'),
}
USE = ' Place it, then stand things on its shelves: point at the open front of a shelf and put an item down there; like things stack on each other.'


def melamine(K, rgb, edge):
    board = mat('Melamine_%s' % ('Black' if rgb[0] < 0.3 else 'White'), rgb, 0.45)
    band = mat('EdgeBanding', edge, 0.5)
    foot = mat('LevellingFoot', (0.1, 0.1, 0.11), 0.6)
    t = 0.022
    for sx in (-1, 1):                                              # the two side panels, with edge banding on the front
        x = sx * (W / 2 - t / 2)
        K.bx((t, D, H - 0.04), (x, 0, 0.04 + (H - 0.04) / 2), board)
        K.bx((t + 0.002, 0.003, H - 0.04), (x, -D / 2 - 0.0015, 0.04 + (H - 0.04) / 2), band)
        for fy in (-D / 2 + 0.06, D / 2 - 0.06):                     # levelling feet
            K.tube((x, fy, 0.0), (x, fy, 0.04), 0.022, 0.022, foot, 8, foot)
    inner = W - 2 * t
    for z in DECKS:                                                  # the four shelves (their top faces are at DECKS)
        K.bx((inner, D - 0.012, t), (0, 0.006, z - t / 2), board)
        K.bx((inner, 0.003, t), (0, -D / 2 + 0.0005, z - t / 2), band)
        for sx in (-1, 1):                                           # shelf pins under each
            for fy in (-D / 2 + 0.07, D / 2 - 0.08):
                K.tube((sx * (inner / 2 - 0.004), fy, z - t - 0.004), (sx * (inner / 2 - 0.004), fy, z - t), 0.004, 0.004, band, 6)
    K.bx((W, D, t), (0, 0, H - t / 2), board)                        # the top
    K.bx((W + 0.002, 0.003, t), (0, -D / 2 - 0.0015, H - t / 2), band)
    K.bx((inner, 0.006, H - 0.04 - 0.02), (0, D / 2 - 0.003, 0.04 + 0.01 + (H - 0.06) / 2), board)   # the thin back panel
    K.bx((inner, 0.014, 0.1), (0, -D / 2 + 0.05, 0.075 - 0.02), board)                              # the kick plate under the first shelf
    K.bx((inner, 0.003, 0.1), (0, -D / 2 + 0.043, 0.075 - 0.02), band)


def steel(K, rgb, edge):
    sheet = mat('SteelShelf', rgb, 0.4)
    post = mat('SteelPost', (0.46, 0.49, 0.54), 0.4)
    dark = mat('SteelBolt', edge, 0.5)
    foot = mat('LevellingFoot', (0.08, 0.08, 0.09), 0.6)
    p = 0.04
    px, py = W / 2 - p / 2, D / 2 - p / 2
    for sx in (-1, 1):
        for sy in (-1, 1):                                           # four square-section posts on feet
            K.bx((p, p, H - 0.03), (sx * px, sy * py, 0.03 + (H - 0.03) / 2), post)
            K.tube((sx * px, sy * py, 0.0), (sx * px, sy * py, 0.03), 0.02, 0.02, foot, 8, foot)
    for z in DECKS:                                                  # sheet-steel shelves: a flat tray, a flange turned down at the front and back
        K.bx((W - 2 * p, D - 2 * p, 0.012), (0, 0, z - 0.006), sheet)
        for sy in (-1, 1):
            K.bx((W - 2 * p, 0.005, 0.03), (0, sy * (D / 2 - p - 0.0025), z - 0.027), sheet)
        for sx in (-1, 1):
            for sy in (-1, 1):                                       # a bolt through each post
                K.bx((0.012, 0.012, 0.01), (sx * px, sy * py + sy * 0.0, z - 0.012), dark)
    for z in (0.0, H - 0.03):                                        # a rail across the top, and the base, at the front and back
        pass
    K.bx((W - 2 * p, 0.03, 0.03), (0, D / 2 - p / 2, H - 0.015), post)
    K.bx((W - 2 * p, 0.03, 0.03), (0, -D / 2 + p / 2, H - 0.015), post)
    for sx in (-1, 1):
        K.bx((0.03, D - 2 * p, 0.03), (sx * (W / 2 - p / 2), 0, H - 0.015), post)
    # a cross brace on the back plane between each pair of shelves' top two bays
    y = D / 2 - p / 2
    for z0, z1 in ((DECKS[0], DECKS[1]), (DECKS[2], DECKS[3])):
        x0, x1 = -(W / 2 - p), (W / 2 - p)
        dx, dz = x1 - x0, z1 - z0 - 0.03
        length = math.hypot(dx, dz)
        for flip in (1, -1):
            ang = math.atan2(dz, dx) * flip
            K.box((length, 0.006, 0.02), T((0, y + 0.012, (z0 + z1) / 2)) @ Matrix.Rotation(-ang, 4, 'Y'), post)


def build(item, spec):
    K = props.Kit()
    K.smooth = False
    (melamine if spec['kind'] == 'melamine' else steel)(K, spec['rgb'], spec['edge'])
    return K.done(item)


def main():
    only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for item, spec in UNITS.items():
        if only and item not in only:
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obj = build(item, spec)
        folder = os.path.join(BUILDING, item)
        os.makedirs(folder, exist_ok=True)
        pts = [v.co for v in obj.data.vertices]
        dims = [round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)]
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.export_scene.gltf(filepath=os.path.join(folder, item + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
        path = os.path.join(folder, item + '.json')
        if os.path.exists(path):
            m = json.load(open(path, encoding='utf-8'))
        else:
            m = json.load(open(os.path.join(BUILDING, 'building_pallet_wood', 'building_pallet_wood.json'), encoding='utf-8'))
            m.update({'id': item, 'icon': item + '.png', 'name': spec['name'], 'description': spec['text'] + USE})
            p = m['properties']
            p.update({'weight_kg': spec['kg'], 'base_value': spec['price'], 'max_stack_size': 1, 'placeable': True, 'support_surface': True,
                      'stores': ['depot'], 'is_buyable': True})
            for k in ('pack_quantity', 'stacking_limit', 'display_weight', 'sale_unit'):
                p.pop(k, None)
        m['properties']['deck_heights'] = DECK_TEXT
        m['properties']['footprint'] = '%.2fm W x %.2fm D x %.2fm H' % (dims[0], dims[1], dims[2])
        m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
        m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
        props.save(path, json.dumps(m, indent=2))
        props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_shelving_units.py), %d triangles, %.2f x %.2f x %.2f m. '
                   'Four shelves, tops at %s m (`properties.deck_heights`).\n' % (m['name'], m['description'], tris, *dims, DECK_TEXT))
        print('shelving', item, '|', tris, 'tris |', dims)


if __name__ == '__main__':
    main()
