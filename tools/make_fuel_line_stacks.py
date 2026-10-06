"""
The fuel line stacks (assets/fuel/fuel_pipe_line_stack_10 and _stack_20): ten and twenty of the 3 m fuel line (tools/make_fuel_line.py) strapped into a bundle, like the propane
pipe stacks. They lay fuel line (`wire_kind: fuel`, 3 m a length, 30 and 60 m a stack) from a bulk fuel tank to a pump (docs/WIRING.md). Free, local, low-poly (no Meshy).

    blender --background --python tools/make_fuel_line_stacks.py
    python tools/set_wiring_data.py
    python tools/render_icon_from_model.py assets/fuel/<id>/<id>.glb assets/fuel/<id>/<id>.png      (each)

Lies along x on the ground, centred, like the single. A new item gets its manifest from fuel_pipe_line (name "Fuel Line Stack", no count in the name: it is shown from
pack_quantity); one already in the kit keeps its name, price and the rest. The equivalency (fuel_line: 1, 10, 20) is saved by this script.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_simple_props as props  # noqa: E402

FUEL = os.path.join(props.ROOT, 'assets', 'fuel')
SINGLE = 'fuel_pipe_line'
R, L = 0.016, 3.0
GAP = 0.0
# n: the rows of the bundle, bottom row first (hexagonal packing: each row sits in the dips of the one below)
BUNDLES = {10: [4, 3, 2, 1], 20: [6, 5, 4, 3, 2]}


def build(n):
    pipe = props.mat('FuelPipe', (0.08, 0.08, 0.09), 0.4)
    red = props.mat('FuelBand', (0.75, 0.1, 0.08), 0.5)
    brass = props.mat('FuelFitting', (0.78, 0.6, 0.25), 0.35)
    strap = props.mat('BundleStrap', (0.82, 0.8, 0.74), 0.6)
    K = props.Kit()
    rows = BUNDLES[n]
    d = 2 * R + GAP
    top = 0.0
    for j, count in enumerate(rows):
        z = R + j * d * math.sin(math.radians(60))
        for i in range(count):
            y = (i - (count - 1) / 2) * d
            K.tube((-L / 2, y, z), (L / 2, y, z), R, R, pipe, 8, pipe, pipe)
            for x in (-1.0, 0.0, 1.0):
                K.tube((x - 0.04, y, z), (x + 0.04, y, z), R * 1.06, R * 1.06, red, 8)
            for x in (-L / 2, L / 2 - 0.06):
                K.tube((x, y, z), (x + 0.06, y, z), R * 1.3, R * 1.3, brass, 8, brass, brass)
        top = z + R
    width = rows[0] * d
    for x in (-1.1, 0.0, 1.1):                                    # three straps round the bundle
        K.bx((0.04, width + 0.012, top + 0.006), (x, 0.0, (top + 0.006) / 2 - 0.003), strap)
    return K.done('stack')


def main():
    from itertools import chain  # noqa: F401
    src = json.load(open(os.path.join(FUEL, SINGLE, SINGLE + '.json'), encoding='utf-8'))
    for n in BUNDLES:
        item = '%s_stack_%d' % (SINGLE, n)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obj = build(n)
        obj.name = item
        folder = os.path.join(FUEL, item)
        os.makedirs(folder, exist_ok=True)
        pts = [v.co for v in obj.data.vertices]
        lo = [min(p[i] for p in pts) for i in range(3)]
        dims = [round(max(p[i] for p in pts) - lo[i], 3) for i in range(3)]
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
            sp = src['properties']
            m.update({'id': item, 'icon': item + '.png', 'name': src['name'] + ' Stack',
                      'description': '%d lengths of fuel line strapped together, %d m in all: gasoline and diesel line for a long run to a pump.' % (n, int(L * n))})
            p = m['properties']
            p.update({'weight_kg': round(sp['weight_kg'] * n, 2), 'base_value': round(sp['base_value'] * n * 0.9), 'max_stack_size': 1, 'placeable': True,
                      'pack_quantity': n, 'sale_unit': 'kit', 'display_weight': True, 'wire_kind': 'fuel', 'wire_length_m': float(L * n)})
        m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
        m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
        props.save(path, json.dumps(m, indent=2))
        props.save(os.path.join(folder, 'README.md'), '# %s (`%s`)\n\n%s\n\nProcedural model (tools/make_fuel_line_stacks.py): %d lengths in %d rows, strapped, %d triangles. '
                   '`wire_kind: fuel`, %d m a stack. See docs/WIRING.md.\n' % (m['name'], item, m['description'], n, len(BUNDLES[n]), tris, int(L * n)))
        print('fuel line stack', item, '|', tris, 'tris |', dims)
    # the equivalency: a length, a stack of 10 and a stack of 20 count as 1, 10 and 20
    eq_path = os.path.join(props.ROOT, 'assets', '_schemas', 'equivalencies.json')
    raw = open(eq_path, encoding='utf-8', newline='').read()
    eq = json.loads(raw)
    groups = eq['equivalencies']
    if 'fuel_line' not in groups:
        groups['fuel_line'] = {'unit': 'pcs', 'label': 'Fuel Line', 'members': [
            {'item': SINGLE, 'value': 1}, {'item': SINGLE + '_stack_10', 'value': 10}, {'item': SINGLE + '_stack_20', 'value': 20}]}
        text = json.dumps(eq, indent=2, ensure_ascii=False) + '\n'
        if '\r\n' in raw:
            text = text.replace('\n', '\r\n')
        props.save(eq_path, text)
        print('equivalency fuel_line saved')


if __name__ == '__main__':
    main()
