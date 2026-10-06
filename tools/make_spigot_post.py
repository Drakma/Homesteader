"""
Builds the yard spigot on a post (assets/water/water_spigot_post) as a GLB in headless Blender: free, local, low-poly (no Meshy).

    blender --background --python tools/make_spigot_post.py
    python tools/set_wiring_data.py
    python tools/render_icon_from_model.py assets/water/water_spigot_post/water_spigot_post.glb assets/water/water_spigot_post/water_spigot_post.png

A treated wooden post set in a gravel pad, a galvanized riser clamped up its front out of the ground, an elbow at the top and a brass hose bib
with a red wheel handle, its spout pointing down and out; a hook on the side of the post for a hose or a bucket.

It is a spigot like the wall ones (tools/make_water_fixtures.py; `wire_role: water_spigot`) but it stands in the yard, so it is PIPED: with the
pipe wrench and PVC pipe, to a water tank, a filter or a well (Wiring.cs, the "water" kind). A right click with a bucket, jug or watering can in
hand then fills it (WaterTap.cs). docs/WELLS.md.

A new item gets its manifest from water_spigot_outdoor; an item that is already in the kit keeps its name, price and the rest.

Conventions: 1 unit = 1 m, pivot at the centre of the post, ground at z = 0, the spigot facing -y.
"""
import json
import math
import os
import random
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_simple_props as props  # noqa: E402    (Kit, mat, save)

ITEM = 'water_spigot_post'
WATER = os.path.join(props.ROOT, 'assets', 'water')
T = Matrix.Translation
mat = props.mat


def build():
    K, rnd = props.Kit(), random.Random(3)
    wood = mat('PostWood', (0.47, 0.36, 0.23), 0.9)
    end = mat('PostEndGrain', (0.62, 0.5, 0.33), 0.9)
    gravel = [mat('Gravel', (0.56, 0.55, 0.52), 0.95), mat('GravelDark', (0.44, 0.43, 0.41), 0.95), mat('GravelLight', (0.67, 0.66, 0.62), 0.95)]
    galv = mat('RiserPipe', (0.66, 0.68, 0.7), 0.35)
    strap = mat('PipeStrap', (0.4, 0.41, 0.43), 0.45)
    brass = mat('SpigotBrass', (0.78, 0.6, 0.24), 0.35)
    red = mat('SpigotHandle', (0.78, 0.1, 0.08), 0.5)
    H, w = 1.0, 0.09
    # the gravel pad: a low mound with stones on it (the splash keeps the ground from turning to mud)
    K.lathe([(0.0, 0.03), (0.2, 0.028), (0.3, 0.012), (0.34, 0.0)], gravel[0], 12)
    for _ in range(26):
        a, d = rnd.uniform(0, 2 * math.pi), rnd.uniform(0.07, 0.3)
        s = rnd.uniform(0.02, 0.04)
        K.box((s, s * rnd.uniform(0.7, 1.2), s * 0.6), T((d * math.cos(a), d * math.sin(a), 0.028 - 0.014 * (d / 0.3))) @ Matrix.Rotation(rnd.uniform(0, 3), 4, 'Z'), rnd.choice(gravel[1:]))
    # the post, its top cut to shed rain
    K.bx((w, w, H - 0.03), (0, 0, (H - 0.03) / 2), wood)
    K.prism([(-w / 2, 0.0), (w / 2, 0.0), (w / 2, 0.012), (-w / 2, 0.03)], w, T((0, w / 2, H - 0.03)) @ Matrix.Rotation(math.pi / 2, 4, 'X'), end, [wood, wood, end, wood])
    # the riser up the front, two straps, an elbow out at the top
    y = -w / 2 - 0.018
    r = 0.013
    top = 0.74
    K.tube((0, y, 0.0), (0, y, top), r, r, galv, 10, galv)
    for z in (0.2, 0.55):
        K.bx((0.07, 0.006, 0.02), (0, -w / 2 - 0.003, z), strap)
        K.bx((0.006, 0.04, 0.02), (-0.032, y + 0.01, z), strap)
        K.bx((0.006, 0.04, 0.02), (0.032, y + 0.01, z), strap)
        K.bx((0.07, 0.006, 0.02), (0, y - r - 0.002, z), strap)
    K.lathe([(r * 1.35, -0.02), (r * 1.35, 0.02)], galv, 10, T((0, y, top)))                              # the elbow fitting
    K.tube((0, y, top), (0, y - 0.05, top), r, r, galv, 10)
    # the hose bib: body, the stem up to a red wheel handle, the spout down and out with a threaded end
    by = y - 0.065
    K.lathe([(r * 1.5, -0.022), (r * 1.7, -0.012), (r * 1.7, 0.012), (r * 1.5, 0.022)], brass, 10, T((0, by, top)) @ Matrix.Rotation(math.pi / 2, 4, 'X'))
    K.tube((0, by, top), (0, by, top + 0.045), 0.008, 0.008, brass, 8)
    wheel = T((0, by, top + 0.05))
    K.lathe([(0.03 + 0.006 * math.cos(a), 0.006 * math.sin(a)) for a in [math.pi / 2 * k for k in range(4)]], red, 12, wheel, closed=True)
    for k in range(2):
        K.box((0.06, 0.007, 0.006), wheel @ Matrix.Rotation(k * math.pi / 2, 4, 'Z'), red)
    K.lathe([(0.008, 0.0), (0.008, 0.006), (0.0, 0.007)], brass, 6, wheel)
    spout = [(0, by - 0.018, top), (0, by - 0.05, top - 0.012), (0, by - 0.065, top - 0.05)]
    K.path(spout, 0.011, brass, 8)
    K.tube(spout[-1], (0, by - 0.068, top - 0.068), 0.0135, 0.0135, brass, 10, brass, mat('SpoutBore', (0.12, 0.1, 0.07), 0.6))   # the hose thread
    # a hook on the side for a hose or a bucket
    K.path([(w / 2, 0, 0.82), (w / 2 + 0.07, 0, 0.82), (w / 2 + 0.085, 0, 0.84), (w / 2 + 0.085, 0, 0.88)], 0.006, strap, 6)
    K.bx((0.006, 0.05, 0.05), (w / 2 + 0.003, 0, 0.82), strap)
    return K.done(ITEM)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj = build()
    folder = os.path.join(WATER, ITEM)
    os.makedirs(folder, exist_ok=True)
    pts = [v.co for v in obj.data.vertices]
    dims = [round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)]
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=os.path.join(folder, ITEM + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
    path = os.path.join(folder, ITEM + '.json')
    if os.path.exists(path):
        m = json.load(open(path, encoding='utf-8'))
    else:
        m = json.load(open(os.path.join(WATER, 'water_spigot_outdoor', 'water_spigot_outdoor.json'), encoding='utf-8'))
        m.update({'id': ITEM, 'icon': ITEM + '.png', 'name': 'Spigot Post',
                  'description': 'A brass hose bib on a wooden post, for water out in the yard. Set it in the ground and pipe it to a water tank, a filter or a well (pipe wrench, '
                                 'PVC pipe); a right click with a bucket, jug or watering can in hand then fills it. It gives whatever water it is piped to, raw or filtered.'})
        p = m['properties']
        p.update({'weight_kg': 9.0, 'base_value': 38, 'max_stack_size': 1, 'placeable': True, 'wire_role': 'water_spigot'})
        for k in ('attach_surface', 'attach_side'):
            p.pop(k, None)
    m['properties']['footprint'] = '%.2fm W x %.2fm D x %.2fm H' % (dims[0], dims[1], dims[2])
    m['models'] = [{'file': ITEM + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
    m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
    props.save(path, json.dumps(m, indent=2))
    props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_spigot_post.py), %d triangles, %.2f x %.2f x %.2f m. `wire_role: water_spigot`, '
               'standing in the yard (not mounted): it is piped. See docs/WELLS.md.\n' % (m['name'], m['description'], tris, *dims))
    print('spigot', ITEM, '|', tris, 'tris |', dims)


if __name__ == '__main__':
    main()
