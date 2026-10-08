"""
Builds the cases of drywall tape as GLBs in headless Blender: free, local, low-poly (no Meshy).

    python tools/case_labels.py        (paints the labels: the name and x<count>)
    blender --background --python tools/make_tape_cases.py
    python tools/render_icon_from_model.py assets/building/<id>/<id>.glb assets/building/<id>/<id>.png

  building_drywall_tape_roll_case_6     a closed, taped cardboard case, six rolls lying flat in one layer (3 by 2)
  building_drywall_tape_roll_case_12    the same case twice as deep, two layers

A new case gets its manifest from the single roll (building_drywall_tape_roll): name, weight (rolls plus the box), price (10 percent off) and
pack_quantity. A case that is already in the kit keeps its name, price and the rest. The ~drywall_tape equivalency (a roll = 1, a case = 6 or 12)
is saved through the kit.

Conventions: 1 unit = 1 m, pivot at the centre of the footprint, ground at z = 0.
"""
import json
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_simple_props as props  # noqa: E402    (Kit, mat, save)
import case_labels  # noqa: E402          (the printed label: the name and x<count>)

BUILD = os.path.join(props.ROOT, 'assets', 'building')
ROLL = 'building_drywall_tape_roll'
BOX_KG = 0.25
T = Matrix.Translation
mat = props.mat


def close_lid(K, W, D, H, t):
    """Shuts a case: the two top flaps lie flat and meet in the middle, and a strip of packing tape runs along the seam and down both ends. The top of the case is then at H + t."""
    card = mat('Cardboard', (0.72, 0.56, 0.36), 0.9)
    tape = mat('PackingTape', (0.5, 0.33, 0.16), 0.25)
    seam = mat('FlapSeam', (0.3, 0.22, 0.12), 0.9)
    for s in (-1, 1):
        K.bx((W, D / 2 - 0.0006, t), (0, s * (D / 4 + 0.0003), H + t / 2), card)             # a flap, lying over the opening
    K.bx((W - 2 * t, 0.0012, 0.0004), (0, 0, H + t + 0.0001), seam)                              # the line where they meet
    tw = min(0.05, D * 0.3)
    K.bx((W + 0.0016, tw, 0.0008), (0, 0, H + t + 0.0004), tape)                                  # the tape along the seam
    for s in (-1, 1):                                                                            # and down both ends
        K.bx((0.0008, tw, 0.07), (s * (W / 2 + 0.0004), 0, H + t - 0.035 + 0.0008), tape)
    return H + t


def build(layers):
    K = props.Kit()
    card = mat('Cardboard', (0.72, 0.56, 0.36), 0.9)
    inside = mat('CardboardInside', (0.62, 0.47, 0.29), 0.9)
    paper = mat('TapePaper', (0.95, 0.94, 0.88), 0.8)
    edge = mat('TapeEdge', (0.84, 0.82, 0.74), 0.8)
    core = mat('TapeCore', (0.55, 0.5, 0.42), 0.9)
    label = mat('CaseLabel', (0.96, 0.96, 0.94), 0.7)
    ink = mat('CaseLabelInk', (0.15, 0.3, 0.6), 0.7)
    r, w, gap, t = 0.05, 0.052, 0.004, 0.004
    cols, rows = 3, 2
    W, D, H = cols * (2 * r + gap) + gap + 2 * t, rows * (2 * r + gap) + gap + 2 * t, layers * (w + 0.002) + t + 0.012
    K.bx((W, D, t), (0, 0, t / 2), card)                                    # the bottom, the four walls (the rolls inside are not seen: the case is shut)
    for s in (-1, 1):
        K.bx((W, t, H), (0, s * (D / 2 - t / 2), H / 2), card)
        K.bx((t, D - 2 * t, H), (s * (W / 2 - t / 2), 0, H / 2), card)
    H = close_lid(K, W, D, H, t)                                            # the flaps shut and taped
    obj = K.done('case')
    obj['case_size'] = (W, D, H)
    return obj


def main():
    src = json.load(open(os.path.join(BUILD, ROLL, ROLL + '.json'), encoding='utf-8'))
    for n in (6, 12):
        item = '%s_case_%d' % (ROLL, n)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obj = build(n // 6)
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
            m.update({'id': item, 'name': 'Drywall Tape Case', 'description': 'A cardboard case of %d rolls of paper drywall tape.' % n, 'icon': item + '.png'})
            p = m['properties']
            p.update({'weight_kg': round(src['properties']['weight_kg'] * n + BOX_KG, 2), 'base_value': round(src['properties']['base_value'] * n * 0.9),
                      'max_stack_size': 5, 'pack_quantity': n, 'placeable': True})
        m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
        m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
        props.save(path, json.dumps(m, indent=2))
        props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_tape_cases.py), %d triangles, %.2f x %.2f x %.2f m: a closed, taped cardboard case, '
                   '%d rolls of `%s` lying flat.\n' % (m['name'], m['description'], tris, *dims, n, ROLL))
        print('case', item, '|', tris, 'tris |', dims)


if __name__ == '__main__':
    main()
