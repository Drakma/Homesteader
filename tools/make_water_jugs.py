"""
Builds the small water jugs (sold full) and their pallets as GLBs in headless Blender: free, local, low-poly.

    blender --background --python tools/make_water_jugs.py
    python tools/render_icon_from_model.py assets/water/<id>/<id>.glb assets/water/<id>/<id>.png        (every item below)
    python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py

  water_jug_1l            a 1 L bottle: ribbed body, shoulder, neck, screw cap, a label band
  water_jug_5l            a 5 L jug: the same with a carrying handle over the cap
  water_jug_<n>l_pallet_5 / _10     5 or 10 of them standing on a wooden pallet

A jug is a LIQUID CONTAINER (the manifest's liquid_container block: capacity_l, accepts liquid_water) and it comes full: filled_with = liquid_water,
filled_l = its capacity. Its weight_kg is the EMPTY jug (a container weighs its own weight plus liters x the liquid's weight per liter); a pallet's
weight is the full jugs plus the pallet. An item that is already in the kit keeps its name, price and the rest: only the model entry and dimensions change.

Conventions: 1 unit = 1 m, pivot at the centre of the footprint, ground at z = 0.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_romex as shapes  # noqa: E402    (Mesh: lathe, box, radial_box, cylinder; material)

ROOT = shapes.ROOT
WATER = os.path.join(ROOT, 'assets', 'water')
PALLET_W, PALLET_D, PALLET_H = 1.2, 1.0, 0.15
PALLET_KG = 20.0

# size: (id, liters, body radius, body height, empty kg, price, thirst restored)
JUGS = {
    '1l': ('water_jug_1l', 1.0, 0.04, 0.2, 0.05, 2, 10),
    '5l': ('water_jug_5l', 5.0, 0.085, 0.24, 0.2, 6, 25),
}
PALLET_COUNTS = (5, 10)


def jug(M, mats, radius, height, handle, plain=False):
    """One jug: a ribbed body full of water, a shoulder, a neck with a screw cap, a label band and (the big one) a handle.
    `plain`: without the ribs (the jugs on a pallet: far fewer triangles)."""
    plastic, label, ink, cap = mats
    r, h = radius, height
    neck = r * 0.36
    ribs = 0 if plain else 5
    prof = [(0.0, 0.0), (r * 0.9, 0.0), (r, h * 0.04)]
    band0, band1 = h * 0.34, h * 0.66                        # the label goes round the middle, where the body is smooth
    for k in range(ribs):                                    # ribs under the label
        za = h * 0.06 + (band0 - h * 0.08) * k / ribs
        zb = h * 0.06 + (band0 - h * 0.08) * (k + 1) / ribs
        prof += [(r, za), (r, za + (zb - za) * 0.7), (r * 0.955, zb)]
    prof += [(r, band0), (r, band1)]
    for k in range(0 if plain else 3):                       # and over it
        za = band1 + (h * 0.9 - band1) * k / 3
        zb = band1 + (h * 0.9 - band1) * (k + 1) / 3
        prof += [(r * 0.955, za + (zb - za) * 0.3), (r, zb)]
    prof += [(r, h), (r * 0.72, h + r * 0.38), (neck, h + r * 0.62), (neck, h + r * 0.8)]
    M.lathe(prof, plastic, closed=False)
    top = h + r * 0.8
    M.lathe([(neck * 1.12, top - 0.004), (neck * 1.12, top + neck * 0.75), (0.0, top + neck * 0.75)], cap, closed=False)     # the cap
    M.lathe([(r * 1.004, band0 + h * 0.01), (r * 1.004, band1 - h * 0.01)], label, closed=False)                             # the label
    if not plain:
        M.lathe([(r * 1.008, band0 + h * 0.09), (r * 1.008, band0 + h * 0.15)], ink, closed=False)
    if handle:                                               # a carrying handle: two posts on the shoulder and a grip over the cap
        hz = top + neck * 0.75 + 0.012
        for s in (-1, 1):
            M.box((0.014, 0.022, hz - (h + r * 0.3)), Matrix.Translation((s * r * 0.62, 0.0, (hz + h + r * 0.3) / 2)), cap)
        M.box((r * 1.24 + 0.014, 0.022, 0.014), Matrix.Translation((0.0, 0.0, hz + 0.007)), cap)
    return top


def build_jug(item, radius, height, handle, seg):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    shapes.SEG = seg
    M = shapes.Mesh()
    jug(M, materials(), radius, height, handle)
    return M.finish(item)


def materials():
    return (shapes.material('JugPlastic', (0.5, 0.74, 0.93), 0.25), shapes.material('JugLabel', (0.96, 0.97, 0.98), 0.8),
            shapes.material('JugLabelInk', (0.12, 0.35, 0.7), 0.8), shapes.material('JugCap', (0.1, 0.3, 0.62), 0.5))


def build_pallet(item, radius, height, handle, count):
    """`count` jugs standing in rows on a wooden pallet (lighter jugs: fewer sides, so ten of them stay inside the triangle budget)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    shapes.SEG = 8
    wood = shapes.material('PalletWood', (0.62, 0.47, 0.3), 0.9)
    mats = materials()
    P = shapes.Mesh()
    w, d, h = PALLET_W, PALLET_D, PALLET_H
    for y in (-d / 2 + 0.05, 0.0, d / 2 - 0.05):
        P.box((w, 0.1, h - 0.044), Matrix.Translation((0.0, y, h / 2)), wood)
    for k in range(7):
        x = -w / 2 + 0.05 + (w - 0.1) * k / 6
        P.box((0.1, d, 0.022), Matrix.Translation((x, 0.0, h - 0.011)), wood)
    for x in (-w / 2 + 0.05, 0.0, w / 2 - 0.05):
        P.box((0.1, d, 0.022), Matrix.Translation((x, 0.0, 0.011)), wood)
    pallet = P.finish(item)
    cols = 5 if count >= 5 else count
    rows = math.ceil(count / cols)
    pitch = max(radius * 2.25, 0.16)
    objs = [pallet]
    for n in range(count):
        i, j = n % cols, n // cols
        M = shapes.Mesh()
        jug(M, mats, radius, height, handle, plain=True)
        o = M.finish('jug')
        o.location = ((i - (cols - 1) / 2) * pitch, (j - (rows - 1) / 2) * pitch, PALLET_H)
        objs.append(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = pallet
    bpy.ops.object.join()
    return pallet


def write(item, obj, name, desc, props, liquid, note):
    me = obj.data
    bpy.context.view_layer.update()
    pts = [v.co for v in me.vertices]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    dims = [hi[i] - lo[i] for i in range(3)]
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    folder = os.path.join(WATER, item)
    os.makedirs(folder, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=os.path.join(folder, item + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
    path = os.path.join(folder, item + '.json')
    if os.path.exists(path):
        m = json.load(open(path, encoding='utf-8'))
    else:
        m = json.load(open(os.path.join(WATER, 'water_jug_20l', 'water_jug_20l.json'), encoding='utf-8'))
        m['id'] = item
        m['icon'] = item + '.png'
        m['name'] = name
        m['description'] = desc
        m['properties'].update(props)
        m['properties'].update({'placeable': True, 'is_buyable': True, 'stores': ['grocer'], 'sale_unit': 'ea'})
        m.pop('liquid_container', None)
        if liquid:
            m['liquid_container'] = liquid
    m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': round(dims[0], 3), 'y': round(dims[2], 3), 'z': round(dims[1], 3)}, 'triangles': tris}]
    cf = dict(m.get('category_fields') or {})
    cf['dimensions_m'] = {'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)}
    cf['capacity_l'] = liquid['capacity_l'] if liquid else 0
    m['category_fields'] = cf
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(m, f, indent=2)
    with open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# %s\n\n%s\n\nProcedural model (tools/make_water_jugs.py), %d triangles. %s\n' % (m['name'], m['description'], tris, note))
    print('jug', item, '|', m['name'], '|', tris, 'tris', '%.3f %.3f %.3f' % tuple(dims))


def main():
    for size, (item, liters, radius, height, empty_kg, price, thirst) in JUGS.items():
        handle = liters >= 5
        label = ('%g L' % liters)
        obj = build_jug(item, radius, height, handle, 16)
        write(item, obj, 'Full Water Jug', 'A %s plastic jug of drinking water, sold full.' % label,
              {'weight_kg': empty_kg, 'base_value': price, 'max_stack_size': 1, 'thirst_restore': thirst},
              {'capacity_l': liters, 'accepts': ['liquid_water'], 'filled_with': 'liquid_water', 'filled_l': liters},
              'A liquid container: %g L of `liquid_water`, full when bought. `weight_kg` is the empty jug.' % liters)
        for n in PALLET_COUNTS:
            pid = '%s_pallet_%d' % (item, n)
            pobj = build_pallet(pid, radius, height, handle, n)
            write(pid, pobj, 'Full Water Jug Pallet', 'A wooden pallet with %d full %s jugs of drinking water.' % (n, label),
                  {'weight_kg': round((empty_kg + liters) * n + PALLET_KG, 1), 'base_value': round(price * n * 0.9), 'max_stack_size': 1, 'thirst_restore': 0},
                  None, '%d of `%s` on a 1.2 m by 1.0 m pallet.' % (n, item))


if __name__ == '__main__':
    main()
