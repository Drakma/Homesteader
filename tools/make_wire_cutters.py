"""
Builds the wire cutters (assets/tools/tool_wire_cutters) as a GLB in headless Blender: free, local, low-poly (no Meshy).

    blender --background --python tools/make_wire_cutters.py
    python tools/render_icon_from_model.py assets/tools/tool_wire_cutters/tool_wire_cutters.glb assets/tools/tool_wire_cutters/tool_wire_cutters.png

Diagonal cutters lying flat: two steel halves crossing at a pivot bolt, short jaws with a ground cutting edge, a wire notch behind them, and
curved handles in red dipped grips with a dark end band. The jaws point along -x (the working end, lower left in the icon).

A new item gets its manifest from tool_wrench_adjustable (a hand tool: it goes in the tools category, so the toolboxes take it); an item that
is already in the kit keeps its name, price and the rest.

Conventions: 1 unit = 1 m, a hand tool: pivot at the centre, lying on z = 0.
"""
import json
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_simple_props as props  # noqa: E402    (Kit, mat, save)

ITEM = 'tool_wire_cutters'
TOOLS = os.path.join(props.ROOT, 'assets', 'tools')
T = Matrix.Translation
mat = props.mat


def build():
    K = props.Kit()
    steel = mat('CutterSteel', (0.62, 0.63, 0.65), 0.3)
    edge = mat('CutterEdge', (0.82, 0.83, 0.85), 0.2)
    dark = mat('CutterDark', (0.2, 0.2, 0.22), 0.45)
    grip = mat('CutterGrip', (0.8, 0.1, 0.08), 0.55)
    band = mat('CutterGripBand', (0.08, 0.08, 0.09), 0.6)
    t = 0.009                                                           # how thick the steel is
    for s in (1, -1):                                                   # the two halves: the jaw on one side of the pivot, its handle crossing to the other
        z0 = 0.0 if s > 0 else t * 0.5                                  # (one half lies over the other at the pivot)
        jaw = [(0.012, s * 0.013), (-0.016, s * 0.012), (-0.04, s * 0.006), (-0.047, s * 0.002), (-0.047, s * 0.0004), (-0.012, s * 0.0004), (-0.008, s * 0.003),
               (-0.002, s * 0.0004), (0.012, s * 0.0004)]
        K.prism(jaw if s > 0 else jaw[::-1], t, T((0, 0, z0)), steel)
        K.box((0.034, 0.0018, t * 0.7), T((-0.029, s * 0.0013, z0 + t / 2)) @ Matrix.Rotation(s * 0.1, 4, 'Z'), edge)        # the ground cutting edge
        # the handle, bare steel out of the pivot and then the dipped grip
        pts = [(0.006, -s * 0.004, z0 + t / 2), (0.03, -s * 0.014, t * 0.75), (0.055, -s * 0.021, t * 0.75)]
        K.path(pts, 0.0048, steel, 8)
        g = [(0.05, -s * 0.0198, t * 0.75), (0.085, -s * 0.0262, t * 0.75), (0.12, -s * 0.0268, t * 0.75), (0.15, -s * 0.0235, t * 0.75)]
        K.path(g, 0.0074, grip, 10)
        K.tube(g[-1], (0.158, -s * 0.0222, t * 0.75), 0.0078, 0.0066, band, 10, band, band)
        K.tube(g[0], (0.053, -s * 0.0204, t * 0.75), 0.0082, 0.0082, band, 10, band, band)                                    # the collar where the grip starts
    K.lathe([(0.0085, 0.0), (0.0085, t * 1.5), (0.006, t * 1.5 + 0.0015), (0.0, t * 1.5 + 0.0015)], dark, 12, T((0.002, 0, 0)))  # the pivot bolt
    K.bx((0.008, 0.0012, 0.0008), (0.002, 0, t * 1.5 + 0.0016), steel)
    K.bx((0.012, 0.003, 0.004), (0.03, 0.0, t * 0.75), dark)                                                               # the return spring between the handles
    return K.done(ITEM)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj = build()
    folder = os.path.join(TOOLS, ITEM)
    os.makedirs(folder, exist_ok=True)
    pts = [v.co for v in obj.data.vertices]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    obj.data.transform(T((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])))
    dims = [round(hi[i] - lo[i], 3) for i in range(3)]
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=os.path.join(folder, ITEM + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
    path = os.path.join(folder, ITEM + '.json')
    if os.path.exists(path):
        m = json.load(open(path, encoding='utf-8'))
    else:
        m = json.load(open(os.path.join(TOOLS, 'tool_wrench_adjustable', 'tool_wrench_adjustable.json'), encoding='utf-8'))
        m.update({'id': ITEM, 'icon': ITEM + '.png', 'name': 'Wire Cutters',
                  'description': 'Diagonal cutting pliers with dipped grips, for cutting electrical wire, fence wire and cable ties.'})
        p = m['properties']
        p.update({'weight_kg': 0.25, 'base_value': 14, 'max_stack_size': 1, 'stores': ['depot'], 'placeable': True})
        p.pop('store_overrides', None)
        p.pop('build_speed', None)
        m['category_fields'] = {'fuel_type': 'none', 'fuel_consumption_l_per_min': 0, 'power_draw_w': 0, 'tank_capacity_l': 0}
    m['models'] = [{'file': ITEM + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
    m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 3), 'depth': round(dims[1], 3), 'height': round(dims[2], 3)})
    props.save(path, json.dumps(m, indent=2))
    props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_wire_cutters.py), %d triangles, %.3f x %.3f x %.3f m. A hand tool in the '
               'tools category, so it goes in a toolbox.\n' % (m['name'], m['description'], tris, *dims))
    print('tool', ITEM, '|', tris, 'tris |', dims)


if __name__ == '__main__':
    main()
