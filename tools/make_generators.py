"""
Builds the three standby generators as GLBs in headless Blender: free, local, low-poly (no Meshy).

    python tools/case_labels.py                                    (paints the rating plates: "10 kW  STANDBY GENERATOR")
    blender --background --python tools/make_generators.py
    python tools/render_icon_from_model.py assets/electricity/<id>/<id>.glb assets/electricity/<id>/<id>.png

  electricity_generator_standby_10kw / _14kw / _28kw

One look, three sizes: a cream steel enclosure on a base frame and a concrete pad, a hinged lid with two latches and a lock, a service door with
a handle, louvred vents in both ends, an exhaust grille, corner posts, a status lamp, a conduit and a fuel line into the pad, and the rating
plate front and back. The rating is on the plate, not in the name (user rule: no capacity in a name).

A new item gets its manifest from electricity_generator_standby; an item that is already in the kit keeps its name, price and the rest.

Conventions: 1 unit = 1 m, pivot at the centre of the footprint, ground at z = 0, the front at -y.
"""
import json
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import case_labels  # noqa: E402
import make_simple_props as props  # noqa: E402    (Kit, mat, save)

ELEC = os.path.join(props.ROOT, 'assets', 'electricity')
T = Matrix.Translation
mat = props.mat

# kW: (width, depth, height of the enclosure, kg, price, tank liters)
SIZES = {10: (1.2, 0.65, 0.72, 150.0, 1800, 200), 14: (1.3, 0.7, 0.8, 190.0, 2400, 200), 28: (1.9, 0.9, 1.1, 420.0, 4800, 400)}
L_PER_MIN_PER_KW = 0.0006944


def build(kw):
    W, D, H = SIZES[kw][:3]
    K = props.Kit()
    cream = mat('GeneratorPaint', (0.88, 0.8, 0.58), 0.45)
    shade = mat('GeneratorPaintShade', (0.7, 0.62, 0.42), 0.5)
    dark = mat('GeneratorDark', (0.1, 0.1, 0.11), 0.7)
    steel = mat('GeneratorTrim', (0.6, 0.61, 0.63), 0.35)
    concrete = mat('GeneratorPad', (0.6, 0.59, 0.56), 0.95)
    pad, frame = 0.1, 0.06
    K.bx((W + 0.34, D + 0.34, pad * 0.6), (0, 0, pad * 0.3), concrete)
    K.bx((W + 0.26, D + 0.26, pad * 0.4), (0, 0, pad * 0.8), concrete)
    K.bx((W + 0.02, D + 0.02, frame), (0, 0, pad + frame / 2), dark)
    z0 = pad + frame
    body = H * 0.78
    K.bx((W, D, body), (0, 0, z0 + body / 2), cream)
    for sx in (-1, 1):                                                   # corner posts
        for sy in (-1, 1):
            K.bx((0.035, 0.035, body), (sx * (W / 2 - 0.008), sy * (D / 2 - 0.008), z0 + body / 2), shade)
    # the lid: overhangs a little, a raised panel on top, a hinge along the back, two latches and a lock on the front
    zl = z0 + body
    lid = H * 0.22
    K.bx((W + 0.04, D + 0.04, lid), (0, 0, zl + lid / 2), cream)
    K.bx((W - 0.16, D - 0.16, 0.012), (0, 0, zl + lid + 0.006), shade)
    K.bx((W + 0.045, 0.012, 0.012), (0, D / 2 + 0.022, zl + 0.006), steel)
    for x in (-W * 0.3, W * 0.3):
        K.bx((0.045, 0.014, 0.06), (x, -D / 2 - 0.024, zl + 0.012), steel)
    K.lathe([(0.014, 0.0), (0.014, 0.005), (0.0, 0.005)], steel, 8, T((0, -D / 2 - 0.02, zl + lid * 0.5)) @ Matrix.Rotation(1.5708, 4, 'X'))
    # the front: a service door on the right with a handle, a status lamp
    dw, dh = W * 0.4, body * 0.74
    K.bx((dw, 0.006, dh), (W * 0.24, -D / 2 - 0.003, z0 + body * 0.5), shade)
    K.bx((dw - 0.03, 0.004, dh - 0.03), (W * 0.24, -D / 2 - 0.007, z0 + body * 0.5), cream)
    K.bx((0.016, 0.014, 0.09), (W * 0.24 - dw / 2 + 0.04, -D / 2 - 0.014, z0 + body * 0.5), steel)
    K.lathe([(0.012, 0.0), (0.012, 0.006), (0.0, 0.008)], mat('StatusLamp', (0.2, 0.85, 0.3), 0.3), 8,
            T((-W * 0.42, -D / 2 - 0.001, z0 + body * 0.86)) @ Matrix.Rotation(1.5708, 4, 'X'))
    # the ends: louvred vents; the right end has the exhaust grille above them
    slats = 7
    for sx in (-1, 1):
        x = sx * (W / 2 + 0.002)
        K.bx((0.004, D * 0.7, body * 0.5), (x - sx * 0.001, 0, z0 + body * 0.4), dark)
        for k in range(slats):
            K.bx((0.01, D * 0.7, 0.02), (x + sx * 0.004, 0, z0 + body * 0.18 + k * body * 0.44 / (slats - 1)), cream, Matrix.Rotation(sx * 0.6, 4, 'Y'))
    K.bx((0.006, D * 0.36, body * 0.16), (W / 2 + 0.003, 0, z0 + body * 0.84), steel)
    for k in range(5):
        K.bx((0.008, 0.006, body * 0.14), (W / 2 + 0.005, -D * 0.14 + k * D * 0.07, z0 + body * 0.84), dark)
    # the services, on the left end: a conduit and a fuel line down into the pad
    for y, r, m in ((D * 0.26, 0.022, steel), (D * 0.36, 0.012, dark)):
        K.path([(-W / 2, y, z0 + 0.14), (-W / 2 - 0.07, y, z0 + 0.14), (-W / 2 - 0.07, y, pad * 0.5)], r, m, 7)
    obj = K.done('generator')
    # the rating plate, front (left of the door) and back
    lh = min(body * 0.44, W * 0.44 / case_labels.ASPECT)
    lw = lh * case_labels.ASPECT
    zc = z0 + body * 0.56
    quads = []
    for side, xc in ((-1, -W * 0.24), (1, W * 0.24)):
        y = side * (D / 2 + 0.0025)
        xl, xr = xc + side * lw / 2, xc - side * lw / 2          # the reader's left and right
        quads.append([(xl, y, zc - lh / 2), (xr, y, zc - lh / 2), (xr, y, zc + lh / 2), (xl, y, zc + lh / 2)])
    return case_labels.add_flat(obj, 'generator_%dkw' % kw, quads)


def main():
    src = json.load(open(os.path.join(ELEC, 'electricity_generator_standby', 'electricity_generator_standby.json'), encoding='utf-8'))
    for kw, (W, D, H, kg, price, tank) in SIZES.items():
        item = 'electricity_generator_standby_%dkw' % kw
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obj = build(kw)
        obj.name = item
        folder = os.path.join(ELEC, item)
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
            m = json.loads(json.dumps(src))
            m.update({'id': item, 'icon': item + '.png', 'name': 'Standby Generator',
                      'description': 'An automatic standby generator in a weatherproof enclosure on a concrete pad, for whole-property backup power.'})
            p = m['properties']
            p.update({'weight_kg': kg, 'base_value': price, 'max_stack_size': 1, 'placeable': True,
                      'footprint': '%.1fm W x %.1fm D x %.1fm H' % (dims[0], dims[1], dims[2])})
            m['category_fields'] = dict(m.get('category_fields') or {}, max_power_w=kw * 1000, tank_capacity_l=tank,
                                        fuel_consumption_l_per_min=round(kw * L_PER_MIN_PER_KW, 6))
        m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
        m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
        props.save(path, json.dumps(m, indent=2))
        props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_generators.py), %d triangles, %.2f x %.2f x %.2f m. A %d kW unit: the '
                   'rating is on the plate on its front and back.\n' % (m['name'], m['description'], tris, *dims, kw))
        print('generator', item, '|', tris, 'tris |', dims)


if __name__ == '__main__':
    main()
