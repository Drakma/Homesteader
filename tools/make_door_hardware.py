"""
Builds the door hardware set (assets/building/building_door_hardware_set) as a GLB in headless Blender: free, local, low-poly (no Meshy).

    blender --background --python tools/make_door_hardware.py
    python tools/render_icon_from_model.py assets/building/building_door_hardware_set/building_door_hardware_set.glb assets/building/building_door_hardware_set/building_door_hardware_set.png

The set laid out as it comes out of the box: the two knobs on their roses (one keyed, one with a thumb turn), the latch with its faceplate and bolt,
the strike plate, a pair of butt hinges opened flat (knuckles, pin, screw holes) and the screws. Satin brass, a steel bolt.

The item is already in the kit: only its model entry, its dimensions and its README are written. tools/make_building_items2.py no longer builds it
(HAND_MADE in tools/make_building_items.py).

Conventions: 1 unit = 1 m, pivot at the centre of the footprint, ground at z = 0.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_simple_props as props  # noqa: E402    (Kit, mat, save)

ITEM = 'building_door_hardware_set'
FOLDER = os.path.join(props.ROOT, 'assets', 'building', ITEM)
T = Matrix.Translation
mat = props.mat


def knob(K, at, brass, shade, dark, keyed):
    """A knob standing on its rose: the rose with a stepped edge, the neck, the knob, then a key cylinder or a thumb turn."""
    mx = T((at[0], at[1], 0.0))
    K.lathe([(0.0, 0.0), (0.034, 0.0), (0.034, 0.004), (0.03, 0.008), (0.018, 0.01), (0.013, 0.012)], brass, 16, mx)
    K.lathe([(0.013, 0.012), (0.011, 0.02), (0.012, 0.03), (0.02, 0.034)], shade, 12, mx)
    K.lathe([(0.02, 0.034), (0.028, 0.04), (0.031, 0.05), (0.029, 0.06), (0.022, 0.067), (0.012, 0.07), (0.0, 0.07)], brass, 16, mx)
    for sx in (1, -1):                                                     # the two screws through the rose
        K.lathe([(0.0035, 0.0085), (0.0035, 0.0095), (0.0, 0.0095)], dark, 6, T((at[0] + sx * 0.025, at[1], 0.0)))
    if keyed:
        K.lathe([(0.009, 0.07), (0.009, 0.072), (0.0, 0.072)], shade, 10, mx)
        K.bx((0.002, 0.009, 0.001), (at[0], at[1], 0.0725), dark)          # the keyway
    else:
        K.lathe([(0.008, 0.07), (0.008, 0.0715), (0.0, 0.0715)], shade, 10, mx)
        K.bx((0.02, 0.005, 0.007), (at[0], at[1], 0.075), brass, Matrix.Rotation(0.5, 4, 'Z'))       # the thumb turn


def hinge(K, at, brass, shade, dark):
    """A butt hinge opened flat: two leaves, five knuckles round a pin with a tip at each end, three screw holes in each leaf."""
    x, y = at
    lw, lh, t, r = 0.036, 0.089, 0.003, 0.0055
    for s in (-1, 1):
        K.bx((lw, lh, t), (x + s * (lw / 2 + r * 0.6), y, t / 2), brass)
        for k in (-1, 0, 1):
            cx = x + s * (lw * (0.72 if k else 0.4) + r * 0.6)
            K.lathe([(0.0042, t), (0.0042, t + 0.0006), (0.0, t + 0.0006)], dark, 8, T((cx, y + k * lh * 0.34, 0.0)))
    for k in range(5):
        y0 = y - lh / 2 + lh * k / 5
        K.tube((x, y0 + 0.0008, r), (x, y0 + lh / 5 - 0.0008, r), r, r, brass if k % 2 == 0 else shade, 8, shade, shade)
    K.tube((x, y - lh / 2 - 0.004, r), (x, y - lh / 2, r), r * 0.5, r * 0.8, shade, 8, shade)
    K.tube((x, y + lh / 2, r), (x, y + lh / 2 + 0.004, r), r * 0.8, r * 0.5, shade, 8, None, shade)


def screw(K, at, angle, brass, dark):
    mx = T((at[0], at[1], 0.004)) @ Matrix.Rotation(angle, 4, 'Z') @ Matrix.Rotation(math.pi / 2, 4, 'Y')
    K.lathe([(0.0, 0.0), (0.004, 0.0), (0.004, 0.0015), (0.0017, 0.004), (0.0017, 0.024), (0.0, 0.03)], brass, 6, mx)


def build():
    K = props.Kit()
    brass = mat('SatinBrass', (0.83, 0.58, 0.16), 0.32)
    shade = mat('SatinBrassShade', (0.6, 0.4, 0.1), 0.38)
    dark = mat('ScrewHole', (0.12, 0.1, 0.07), 0.6)
    steel = mat('LatchBolt', (0.72, 0.73, 0.75), 0.3)
    knob(K, (-0.105, 0.05), brass, shade, dark, keyed=True)
    knob(K, (-0.105, -0.05), brass, shade, dark, keyed=False)
    # the latch: a barrel lying down, a faceplate at its end, the sloped bolt through it
    y, r = 0.055, 0.011
    K.tube((-0.035, y, r + 0.0005), (0.03, y, r + 0.0005), r, r, shade, 12, shade)
    K.bx((0.006, 0.014, 0.012), (-0.02, y, r + 0.012), shade)                                # the hub the spindle turns
    K.bx((0.003, 0.026, 0.057), (0.0315, y, 0.0285), brass)
    for dz in (-0.022, 0.022):
        K.lathe([(0.0035, 0.0), (0.0035, 0.0006), (0.0, 0.0006)], dark, 6, T((0.033, y, 0.0285 + dz)) @ Matrix.Rotation(math.pi / 2, 4, 'Y'))
    bolt = [(0.0, -0.008), (0.012, -0.008), (0.012, -0.002), (0.004, 0.008), (0.0, 0.008)]
    K.prism(bolt, 0.013, T((0.033, y, r + 0.0005 - 0.0065)), steel)
    # the strike plate: a plate with the hole for the bolt, a curved lip, two screw holes
    sy = -0.05
    for dx in (-0.017, 0.017):
        K.bx((0.012, 0.058, 0.002), (0.012 + dx, sy, 0.001), brass)
    for dy in (-0.022, 0.022):
        K.bx((0.022, 0.014, 0.002), (0.012, sy + dy, 0.001), brass)
        K.lathe([(0.0035, 0.002), (0.0035, 0.0026), (0.0, 0.0026)], dark, 6, T((0.012, sy + dy, 0.0)))
    K.bx((0.008, 0.03, 0.002), (0.038, sy, 0.0035), brass, Matrix.Rotation(-0.6, 4, 'Y'))       # the lip
    hinge(K, (0.115, 0.056), brass, shade, dark)
    hinge(K, (0.115, -0.056), brass, shade, dark)
    for x, yy, a in ((-0.03, -0.004, 0.3), (-0.005, 0.004, -0.5), (0.02, -0.006, 1.1), (0.045, 0.003, 2.4), (-0.05, 0.002, 1.9), (0.06, -0.008, 0.1)):
        screw(K, (x, yy), a, brass, dark)
    return K.done(ITEM)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj = build()
    pts = [v.co for v in obj.data.vertices]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    obj.data.transform(T((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])))
    dims = [round(hi[i] - lo[i], 3) for i in range(3)]
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=os.path.join(FOLDER, ITEM + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
    path = os.path.join(FOLDER, ITEM + '.json')
    m = json.load(open(path, encoding='utf-8'))
    m['models'] = [{'file': ITEM + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
    m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
    props.save(path, json.dumps(m, indent=2))
    props.save(os.path.join(FOLDER, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_door_hardware.py), %d triangles, %.2f x %.2f x %.2f m: two knobs on their roses '
               '(one keyed, one with a thumb turn), the latch and its faceplate, the strike plate, a pair of butt hinges and the screws.\n' % (m['name'], m['description'], tris, *dims))
    print('hardware', ITEM, '|', tris, 'tris |', dims)


if __name__ == '__main__':
    main()
