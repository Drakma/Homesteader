"""
Builds the black poly water cisterns as GLBs in headless Blender: free, local, low-poly (no Meshy).

    blender --background --python tools/make_cisterns.py
    python tools/set_wiring_data.py
    python tools/render_icon_from_model.py assets/water/<id>/<id>.glb assets/water/<id>/<id>.png

  water_cistern_poly_1200l    1.10 m across, 1.45 m tall
  water_cistern_poly_2400l    1.45 m across, 1.70 m tall
  water_cistern_poly_3800l    1.70 m across, 1.95 m tall

One design in three sizes: a black rotomoulded tank standing upright, pressed ribs round the wall, a domed top with a ribbed screw lid over the
manway, a vent and an inlet fitting on the dome, moulded lifting lugs, and at the foot a bulkhead outlet with a ball valve (blue handle).

Each is a water tank on a water line (`wire_role: water_tank`) and a liquid container for water, so the name generators show its size
("Water Cistern (1200 L)"); the size is not in the stored name. A new size gets its manifest from water_cistern_poly_3800l; an item that is
already in the kit keeps its name and the rest (only the model entry and the dimensions change).

Conventions: 1 unit = 1 m, pivot at the centre of the footprint, ground at z = 0, the outlet facing -y.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_simple_props as props  # noqa: E402    (Kit, mat, save)

WATER = os.path.join(props.ROOT, 'assets', 'water')
BASE = 'water_cistern_poly_3800l'
T = Matrix.Translation
mat = props.mat

# liters: (radius, height of the wall, kg empty, price)
SIZES = {1200: (0.55, 1.2, 28.0, 320), 2400: (0.725, 1.42, 45.0, 480), 3800: (0.85, 1.65, 70.0, 650)}


def build(liters):
    r, wall = SIZES[liters][:2]
    K = props.Kit()
    poly = mat('CisternPoly', (0.06, 0.06, 0.065), 0.5)
    rib = mat('CisternRib', (0.11, 0.11, 0.12), 0.45)
    lid = mat('CisternLid', (0.03, 0.03, 0.035), 0.6)
    pvc = mat('OutletPvc', (0.9, 0.9, 0.88), 0.45)
    blue = mat('ValveHandle', (0.12, 0.36, 0.78), 0.45)
    ribs = 5 if liters < 3000 else 6
    # the wall: a foot ring, then a pressed rib every so often
    prof = [(0.0, 0.0), (r * 0.97, 0.0), (r, 0.03)]
    for k in range(ribs):
        z = wall * (k + 0.6) / (ribs + 0.2)
        prof += [(r, z - 0.05), (r * 1.025, z - 0.025), (r * 1.025, z + 0.025), (r, z + 0.05)]
    prof += [(r, wall)]
    K.lathe(prof, poly, 24)
    for k in range(ribs):                                                  # the crown of each rib catches the light
        z = wall * (k + 0.6) / (ribs + 0.2)
        K.lathe([(r * 1.027, z - 0.024), (r * 1.027, z + 0.024)], rib, 24)
    # the dome
    dome = r * 0.34
    dprof = [(r * math.cos(a), wall + dome * math.sin(a)) for a in (0.0, 0.3, 0.65, 1.0, 1.25)]
    neck = r * math.cos(1.25)
    top = wall + dome * math.sin(1.25)
    K.lathe(dprof + [(neck, top)], poly, 24)
    mr = min(0.24, r * 0.4)                                                # the manway: a collar and a ribbed screw lid
    K.lathe([(neck, top), (mr * 1.1, top), (mr * 1.1, top + 0.05), (mr, top + 0.05)], poly, 20)
    K.lathe([(mr * 1.16, top + 0.04), (mr * 1.16, top + 0.085), (mr * 0.9, top + 0.1), (0.0, top + 0.1)], lid, 20)
    for k in range(12):
        a = math.pi * k / 6
        K.bx((0.02, 0.012, 0.05), (mr * 1.17 * math.cos(a), mr * 1.17 * math.sin(a), top + 0.062), lid, Matrix.Rotation(a, 4, 'Z'))
    K.bx((mr * 1.2, 0.03, 0.02), (0, 0, top + 0.108), lid)                    # the grip bar across the lid
    # on the dome: an inlet fitting and a vent; two lifting lugs on its shoulder
    ia = 0.62
    iz = wall + dome * math.sin(ia) - 0.01
    K.lathe([(0.045, 0.0), (0.045, 0.05), (0.03, 0.055), (0.03, 0.09), (0.0, 0.09)], pvc, 10, T((r * math.cos(ia) * 0.98, 0.0, iz)))
    K.path([(-r * 0.62, 0.0, wall + dome * 0.72), (-r * 0.62, 0.0, wall + dome * 0.72 + 0.1), (-r * 0.62 - 0.05, 0.0, wall + dome * 0.72 + 0.1),
            (-r * 0.62 - 0.05, 0.0, wall + dome * 0.72 + 0.05)], 0.014, pvc, 6)
    for s in (-1, 1):
        K.bx((0.05, 0.16, 0.07), (0.0, s * r * 0.86, wall + 0.035), poly)
        K.bx((0.06, 0.05, 0.02), (0.0, s * r * 0.86, wall + 0.075), rib)
    # the outlet at the foot: a bulkhead fitting, a ball valve, a threaded stub
    oz = 0.1
    oy = -r
    K.lathe([(0.05, 0.0), (0.05, 0.02), (0.032, 0.025)], pvc, 10, T((0, oy + 0.005, oz)) @ Matrix.Rotation(math.pi / 2, 4, 'X'))
    K.tube((0, oy, oz), (0, oy - 0.07, oz), 0.022, 0.022, pvc, 10)
    K.lathe([(0.03, -0.03), (0.036, -0.02), (0.036, 0.02), (0.03, 0.03)], pvc, 10, T((0, oy - 0.09, oz)) @ Matrix.Rotation(math.pi / 2, 4, 'X'))
    K.tube((0, oy - 0.09, oz + 0.03), (0, oy - 0.09, oz + 0.055), 0.01, 0.01, pvc, 6)
    K.bx((0.022, 0.1, 0.012), (0, oy - 0.115, oz + 0.06), blue)
    K.tube((0, oy - 0.12, oz), (0, oy - 0.17, oz), 0.022, 0.022, pvc, 10, None, mat('OutletBore', (0.2, 0.2, 0.21), 0.7))
    return K.done('cistern')


def main():
    base = json.load(open(os.path.join(WATER, BASE, BASE + '.json'), encoding='utf-8'))
    for liters, (r, wall, kg, price) in SIZES.items():
        item = 'water_cistern_poly_%dl' % liters
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obj = build(liters)
        obj.name = item
        folder = os.path.join(WATER, item)
        os.makedirs(folder, exist_ok=True)
        pts = [v.co for v in obj.data.vertices]
        dims = [round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)]
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.export_scene.gltf(filepath=os.path.join(folder, item + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
        path = os.path.join(folder, item + '.json')
        new = not os.path.exists(path)
        m = json.loads(json.dumps(base)) if new else json.load(open(path, encoding='utf-8'))
        if new:
            m.update({'id': item, 'icon': item + '.png', 'name': 'Water Cistern'})
        p = m['properties']
        if new or p.get('weight_kg', 0) <= 1.0:                           # (the 3800 L one was a placeholder: 1 kg, price 10, not sold anywhere)
            m['description'] = 'A black poly water cistern for bulk storage: stand it in the yard and pipe a well, a filter or a rain line into it.'
            p.update({'weight_kg': kg, 'base_value': price, 'max_stack_size': 1, 'placeable': True, 'is_buyable': True, 'stores': ['water'], 'sale_unit': 'ea',
                      'wire_role': 'water_tank'})
            m['liquid_container'] = {'capacity_l': liters, 'accepts': ['liquid_water']}
            m['category_fields'] = dict(m.get('category_fields') or {}, capacity_l=liters)
        m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
        m.pop('dimensions', None)
        m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
        props.save(path, json.dumps(m, indent=2))
        props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_cisterns.py), %d triangles, %.2f x %.2f x %.2f m, %d L. `wire_role: water_tank`. '
                   'See docs/WELLS.md.\n' % (m['name'], m['description'], tris, *dims, liters))
        print('cistern', item, '|', tris, 'tris |', dims)


if __name__ == '__main__':
    main()
