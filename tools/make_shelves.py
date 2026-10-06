"""
Builds the wall shelves (assets/building/building_shelf_wall_*) as GLBs in headless Blender: free, local, low-poly (no Meshy).

    blender --background --python tools/make_shelves.py
    python tools/render_icon_from_model.py assets/building/<id>/<id>.glb assets/building/<id>/<id>.png      (each)

A single board on steel angle brackets, screwed to a wall. It mounts on a building's wall like a light does (`attach_surface: wall`) and it is a
SHELF (`properties.shelf`): things are stood on its top face in a row (Shelf.cs, docs/ATTACHED_ITEMS.md). The top of the model's bounds is the
face things stand on, so NOTHING of the model may rise above the board.

An item that is already in the kit keeps its name, price and the rest; a new one gets its manifest from the wall sconce.

Conventions (a wall item): 1 unit = 1 m, the BACK is the plane y = 0 and it sticks out towards -y, bottom at z = 0, centred on x.
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

# id: name, board length, depth, thickness, bracket count, style, weight, price, description
SHELVES = {
    'building_shelf_wall_wood': dict(name='Wall Shelf', L=0.9, D=0.25, t=0.028, n=2, style='wood', kg=2.6, price=14,
                                     text='A pine board on two black steel angle brackets.'),
    'building_shelf_wall_wood_long': dict(name='Long Wall Shelf', L=1.8, D=0.25, t=0.028, n=3, style='wood', kg=5.0, price=24,
                                          text='A long pine board on three black steel angle brackets.'),
    'building_shelf_wall_steel': dict(name='Steel Wall Shelf', L=1.2, D=0.35, t=0.02, n=3, style='steel', kg=6.5, price=32,
                                      text='A deep galvanized steel shelf on heavy angle brackets, for a garage or a shed.'),
}
USE = ' Mount it on a wall, then stand things on it: left click with the item in hand, right click the item to take it back.'


def bracket(K, x, top, depth, steel, screw, heavy):
    """An angle bracket under the board at x: a leg down the wall, a leg out under the board, a brace between them, screw heads on both legs."""
    w = 0.034 if heavy else 0.028          # the strap's width
    g = 0.005 if heavy else 0.004          # its thickness
    down = min(top, 0.24 if heavy else 0.2)
    out = depth * 0.86
    K.bx((w, g, down), (x, -g / 2, top - down / 2), steel)                       # down the wall
    K.bx((w, out, g), (x, -out / 2, top - g / 2), steel)                         # out under the board
    # the brace: from low on the wall leg to far out on the top leg
    a, b = (-g, top - down * 0.92), (-out * 0.9, top - g)
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    K.box((w * 0.55, length, g), T((x, mid[0], mid[1])) @ Matrix.Rotation(ang, 4, 'X'), steel)
    for z in (top - down * 0.25, top - down * 0.75):                             # screws into the wall
        K.bx((0.012, 0.004, 0.012), (x, -g - 0.002, z), screw)
    for y in (-out * 0.3, -out * 0.75):                                          # and up into the board
        K.bx((0.012, 0.012, 0.004), (x, y, top - g - 0.002), screw)


def build(item, c):
    K = props.Kit()
    L, D, t, heavy = c['L'], c['D'], c['t'], c['style'] == 'steel'
    drop = 0.24 if heavy else 0.2          # how far the brackets reach below the board
    H = drop + (0.004 if heavy else t)     # the top of the board: the highest point of the model
    under = H - t
    black = mat('BracketSteel', (0.07, 0.07, 0.08), 0.5)
    galv = mat('ShelfGalvanized', (0.62, 0.65, 0.67), 0.35)
    galv_dark = mat('ShelfGalvanizedEdge', (0.5, 0.53, 0.55), 0.4)
    screw = mat('ScrewHead', (0.72, 0.72, 0.7), 0.3)
    if heavy:
        # a folded sheet: the deck, a lip turned down along the front and both ends, a strip up the wall under it
        K.bx((L, D, 0.004), (0, -D / 2, H - 0.002), galv)
        K.bx((L, 0.004, t), (0, -D + 0.002, H - t / 2), galv_dark)
        for s in (-1, 1):
            K.bx((0.004, D, t), (s * (L / 2 - 0.002), -D / 2, H - t / 2), galv_dark)
        K.bx((L, 0.004, 0.05), (0, -0.002, H - 0.025), galv_dark)
        for k in range(4):                                                        # stiffening ribs pressed into the deck, seen from below and at the ends
            y = -D * (0.2 + 0.2 * k)
            K.bx((L - 0.02, 0.012, 0.006), (0, y, H - 0.007), galv_dark)
    else:
        pine = mat('ShelfPine', (0.8, 0.64, 0.42), 0.75)
        grain = mat('ShelfPineGrain', (0.7, 0.53, 0.32), 0.8)
        end = mat('ShelfEndGrain', (0.66, 0.5, 0.3), 0.85)
        K.bx((L - 0.004, D, t), (0, -D / 2, under + t / 2), pine)
        for s in (-1, 1):                                                         # the sawn ends
            K.bx((0.002, D, t), (s * (L / 2 - 0.001), -D / 2, under + t / 2), end)
        K.bx((L - 0.004, 0.002, t * 0.5), (0, -D - 0.0005, under + t / 2), grain)   # a darker line along the front edge
        for k, (y, x0, x1) in enumerate(((-D * 0.22, -0.46, 0.2), (-D * 0.5, -0.3, 0.44), (-D * 0.78, -0.42, 0.1))):   # grain lines let into the top face
            K.bx(((x1 - x0) * L, 0.004, 0.0006), ((x0 + x1) / 2 * L, y, H - 0.0002), grain)
    n = c['n']
    inset = 0.12 if L < 1.0 else 0.16
    for k in range(n):
        x = -L / 2 + inset + (L - 2 * inset) * k / (n - 1)
        bracket(K, x, under if not heavy else H - 0.004, D, galv_dark if heavy else black, screw, heavy)
    return K.done(item)


def main():
    for item, c in SHELVES.items():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obj = build(item, c)
        folder = os.path.join(BUILDING, item)
        os.makedirs(folder, exist_ok=True)
        pts = [v.co for v in obj.data.vertices]
        lo = [min(p[i] for p in pts) for i in range(3)]
        hi = [max(p[i] for p in pts) for i in range(3)]
        dims = [round(hi[i] - lo[i], 3) for i in range(3)]
        assert abs(lo[2]) < 0.002 and hi[1] < 0.002, (item, lo, hi)   # bottom on z = 0, nothing behind the wall plane
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.export_scene.gltf(filepath=os.path.join(folder, item + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
        path = os.path.join(folder, item + '.json')
        if os.path.exists(path):
            m = json.load(open(path, encoding='utf-8'))
        else:
            m = json.load(open(os.path.join(BUILDING, 'building_light_sconce_interior', 'building_light_sconce_interior.json'), encoding='utf-8'))
            m.update({'id': item, 'icon': item + '.png', 'name': c['name'], 'description': c['text'] + USE})
            m.pop('lights', None)
            p = m['properties']
            p.update({'weight_kg': c['kg'], 'base_value': c['price'], 'max_stack_size': 10, 'placeable': False, 'is_buyable': True, 'stores': ['depot'], 'sale_unit': 'ea'})
        m['properties'].update({'attach_surface': 'wall', 'attach_side': 'either', 'shelf': True})
        m['properties']['footprint'] = '%.2fm W x %.2fm D x %.2fm H' % (dims[0], dims[1], dims[2])
        m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
        m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
        props.save(path, json.dumps(m, indent=2))
        props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_shelves.py), %d triangles, %.2f x %.2f x %.2f m. A wall item '
                   '(`attach_surface: wall`) that is a shelf (`shelf: true`): things stand on its top face. See docs/ATTACHED_ITEMS.md.\n' % (m['name'], m['description'], tris, *dims))
        print('shelf', item, '|', tris, 'tris |', dims)


if __name__ == '__main__':
    main()
