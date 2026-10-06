"""
Builds the cases of PVC fittings and PVC cans as GLBs in headless Blender: free, local, low-poly (no Meshy).

    python tools/case_labels.py        (paints the labels: the name and x<count>)
    blender --background --python tools/make_fitting_cases.py
    python tools/render_icon_from_model.py assets/building/<id>/<id>.glb assets/building/<id>/<id>.png

  pipe_pvc_elbow_case_10 / _20             90-degree elbows
  pipe_pvc_tee_case_10 / _20               tee fittings
  building_valve_ball_pvc_case_10 / _20    ball valves
  building_pvc_cement_can_case_6 / _12     cans of PVC cement
  building_pvc_primer_can_case_6 / _12     cans of PVC primer
  building_insulation_spray_foam_case_8 / _16     tall cans of spray foam, in a tall case
  building_weatherstripping_roll_case_6 / _12     rolls of weatherstripping, lying flat

Each is an open cardboard case with the top layer of its contents showing (a case of 20 fittings is the case of 10 twice as deep). A new case
gets its manifest from the single item: name, weight (the contents plus the box), price (10 percent off), pack_quantity, placeable, and
stacking_limit 6 (cases stack six high). A case that is already in the kit keeps its name, price and the rest. The equivalencies (a single = 1,
a case = its count) are saved through the kit.

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
import case_labels  # noqa: E402          (the printed label: the name and x<count>)

BUILD = os.path.join(props.ROOT, 'assets', 'building')
BOX_KG = 0.3
STACKING_LIMIT = 6
T = Matrix.Translation
mat = props.mat
PVC = (0.93, 0.93, 0.91)


def socket(K, p0, p1, r, m):
    """A leg of a fitting from p0 out to p1, with the thicker socket on its outer part and the dark bore at the end."""
    p0, p1 = [props.Vector(p) for p in (p0, p1)]
    mid = p0 + (p1 - p0) * 0.42
    K.tube(p0, mid, r, r, m, 10)
    K.tube(mid, p1, r * 1.2, r * 1.2, m, 10, m, K.bore)
    K.tube(p1, p1 + (p1 - p0).normalized() * 0.0006, r * 0.92, r * 0.92, K.bore, 10, None, K.bore)


def elbow(K, x, y, z, m):
    r, leg = 0.021, 0.048
    c = (x - 0.018, y - 0.018, z + r * 1.2)
    socket(K, c, (c[0] + leg, c[1], c[2]), r, m)
    socket(K, c, (c[0], c[1] + leg, c[2]), r, m)
    K.lathe([(0.0, -r), (r * 0.7, -r * 0.7), (r, 0.0), (r * 0.7, r * 0.7), (0.0, r)], m, 10, T(c))       # the rounded corner


def tee(K, x, y, z, m):
    r = 0.021
    c = (x, y - 0.012, z + r * 1.2)
    socket(K, c, (c[0] + 0.05, c[1], c[2]), r, m)
    socket(K, c, (c[0] - 0.05, c[1], c[2]), r, m)
    socket(K, c, (c[0], c[1] + 0.046, c[2]), r, m)


def valve(K, x, y, z, m):
    r = 0.021
    c = (x, y, z + r * 1.2)
    socket(K, c, (c[0] + 0.062, c[1], c[2]), r, m)
    socket(K, c, (c[0] - 0.062, c[1], c[2]), r, m)
    K.tube((c[0] - 0.02, c[1], c[2]), (c[0] + 0.02, c[1], c[2]), r * 1.35, r * 1.35, m, 10, m, m)       # the ball's housing
    K.tube(c, (c[0], c[1], c[2] + r * 1.9), r * 0.55, r * 0.5, m, 8)
    K.bx((0.085, 0.016, 0.008), (c[0] + 0.02, c[1], c[2] + r * 1.9 + 0.004), K.handle)                    # the red handle
    K.bx((0.02, 0.022, 0.012), (c[0], c[1], c[2] + r * 1.9 + 0.002), K.handle)


def can_of(r, h, straw=False):
    """A can standing up: a label round it, a ribbed cap. straw: the long nozzle of a spray foam can, clipped to its side."""
    def can(K, x, y, z, m):
        mx = T((x, y, z))
        K.lathe([(r, 0.0), (r, h), (r * 0.96, h + 0.004), (r * 0.5, h + 0.006)], m, 14, mx)
        K.lathe([(r * 1.01, h * 0.22), (r * 1.01, h * 0.74)], K.label, 14, mx)
        K.lathe([(r * 0.5, h + 0.006), (r * 0.5, h + 0.03), (r * 0.42, h + 0.034), (0.0, h + 0.034)], K.cap, 10, mx)
        for k in range(6):                                                                             # the grip ribs of the cap
            a = math.pi * k / 3
            K.bx((0.004, 0.004, 0.02), (x + r * 0.5 * math.cos(a), y + r * 0.5 * math.sin(a), z + h + 0.018), K.cap, Matrix.Rotation(a, 4, 'Z'))
        if straw:
            K.tube((x + r * 0.75, y + r * 0.75, z + h * 0.3), (x + r * 0.75, y + r * 0.75, z + h * 0.98), 0.003, 0.003, K.cap, 5, K.cap, K.cap)
    return can


def roll_of(r, w):
    """A roll lying flat: the wound strip, its wraps showing on the face, a core."""
    def roll(K, x, y, z, m):
        mx = T((x, y, z))
        K.lathe([(r * 0.34, w), (r, w), (r, 0.0)], m, 14, mx)
        K.lathe([(r * 0.34, w + 0.001), (r * 0.28, w + 0.001), (r * 0.28, w * 0.3)], K.core, 12, mx)
        for rr in (0.5, 0.66, 0.82):
            K.lathe([(r * rr, w + 0.0004), (r * rr + 0.0012, w + 0.0004)], K.bore, 14, mx)
    return roll


def build(part, cell, height, cols, rows, layers, body_rgb, ink_rgb, cap_rgb=None):
    """An open cardboard case with cols x rows of `part` showing; `layers` deep."""
    K = props.Kit()
    card = mat('Cardboard', (0.72, 0.56, 0.36), 0.9)
    inside = mat('CardboardInside', (0.62, 0.47, 0.29), 0.9)
    sticker = mat('CaseLabel', (0.96, 0.96, 0.94), 0.7)
    ink = mat('CaseLabelInk', ink_rgb, 0.7)
    body = mat('PartBody', body_rgb, 0.45)
    K.bore = mat('PartBore', (0.2, 0.2, 0.21), 0.8)
    K.handle = mat('ValveHandle', (0.8, 0.12, 0.1), 0.5)
    K.cap = mat('CanCap', cap_rgb or (0.1, 0.1, 0.11), 0.5)
    K.core = mat('RollCore', (0.7, 0.7, 0.7), 0.8)
    K.label = mat('CanLabel', ink_rgb, 0.7)
    t, gap = 0.004, 0.006
    W, D = cols * cell[0] + gap * 2 + 2 * t, rows * cell[1] + gap * 2 + 2 * t
    H = t + layers * height + 0.014
    K.bx((W, D, t), (0, 0, t / 2), card)
    for s in (-1, 1):
        K.bx((W, t, H), (0, s * (D / 2 - t / 2), H / 2), card)
        K.bx((t, D - 2 * t, H), (s * (W / 2 - t / 2), 0, H / 2), card)
        K.bx((W - 2 * t, 0.0006, H - t), (0, s * (D / 2 - t - 0.0003), H / 2 + t / 2), inside)
        K.bx((0.0006, D - 2 * t, H - t), (s * (W / 2 - t - 0.0003), 0, H / 2 + t / 2), inside)
        K.box((W, D * 0.48, t * 0.6), T((0, s * D / 2, H)) @ Matrix.Rotation(s * 0.45, 4, 'X') @ T((0, s * D * 0.24, 0)), card)      # the flaps, standing open and leaning out
        K.box((W * 0.3, D - 2 * t, t * 0.6), T((s * W / 2, 0, H)) @ Matrix.Rotation(-s * 0.45, 4, 'Y') @ T((s * W * 0.15, 0, 0)), card)
    z0 = t + (layers - 1) * height
    if layers > 1:                                                                                      # a divider sheet over the layer underneath
        K.bx((W - 2 * t - 0.002, D - 2 * t - 0.002, 0.002), (0, 0, z0 - 0.001), inside)
    for i in range(cols):
        for j in range(rows):
            part(K, (i - (cols - 1) / 2) * cell[0], (j - (rows - 1) / 2) * cell[1], z0, body)
    obj = K.done('case')
    obj['case_size'] = (W, D, H)
    return obj


# single: (part, cell, layer height, {count: (cols, rows, layers)}, body colour, label ink, cap colour (default: black))
CASES = {
    'pipe_pvc_elbow': (elbow, (0.088, 0.088), 0.056, {10: (5, 2, 1), 20: (5, 2, 2)}, PVC, (0.15, 0.3, 0.6), None),
    'pipe_pvc_tee': (tee, (0.126, 0.09), 0.056, {10: (2, 5, 1), 20: (2, 5, 2)}, PVC, (0.15, 0.3, 0.6), None),
    'building_valve_ball_pvc': (valve, (0.16, 0.07), 0.08, {10: (2, 5, 1), 20: (2, 5, 2)}, PVC, (0.8, 0.12, 0.1), None),
    'building_pvc_cement_can': (can_of(0.043, 0.1), (0.094, 0.094), 0.14, {6: (3, 2, 1), 12: (4, 3, 1)}, (0.7, 0.7, 0.72), (0.85, 0.55, 0.1), (0.9, 0.5, 0.08)),
    'building_pvc_primer_can': (can_of(0.043, 0.1), (0.094, 0.094), 0.14, {6: (3, 2, 1), 12: (4, 3, 1)}, (0.7, 0.7, 0.72), (0.55, 0.25, 0.65), (0.5, 0.2, 0.62)),
    # spray foam: tall cans, so a tall case
    'building_insulation_spray_foam': (can_of(0.034, 0.24, straw=True), (0.076, 0.076), 0.28, {8: (4, 2, 1), 16: (4, 4, 1)}, (0.95, 0.85, 0.2), (0.2, 0.3, 0.55), None),
    'building_weatherstripping_roll': (roll_of(0.06, 0.1), (0.126, 0.126), 0.104, {6: (3, 2, 1), 12: (3, 2, 2)}, (0.18, 0.18, 0.2), (0.2, 0.45, 0.3), None),
}


def main():
    for single, (part, cell, height, counts, body, ink, label) in CASES.items():
        src = json.load(open(os.path.join(BUILD, single, single + '.json'), encoding='utf-8'))
        for n, (cols, rows, layers) in counts.items():
            item = '%s_case_%d' % (single, n)
            bpy.ops.wm.read_factory_settings(use_empty=True)
            obj = build(part, cell, height, cols, rows, layers, body, ink, label)
            obj = case_labels.add(obj, item, tuple(obj['case_size']))
            obj.name = item
            folder = os.path.join(BUILD, item)
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
                m.update({'id': item, 'name': '%s Case' % src['name'], 'description': 'A cardboard case of %d: %s' % (n, src['description']),
                          'icon': item + '.png'})
                p = m['properties']
                p.update({'weight_kg': round(src['properties']['weight_kg'] * n + BOX_KG, 2), 'base_value': round(src['properties']['base_value'] * n * 0.9),
                          'max_stack_size': 5, 'pack_quantity': n})
            m['properties'].update({'placeable': True, 'stacking_limit': STACKING_LIMIT})
            m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
            m['category_fields'] = {'dimensions_m': {'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)}}
            props.save(path, json.dumps(m, indent=2))
            props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_fitting_cases.py), %d triangles, %.2f x %.2f x %.2f m: an open '
                       'cardboard case of %d `%s`. Cases stack %d high.\n' % (m['name'], m['description'], tris, *dims, n, single, STACKING_LIMIT))
            print('case', item, '|', tris, 'tris |', dims)


if __name__ == '__main__':
    main()
