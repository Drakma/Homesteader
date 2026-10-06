"""
The fuel line (assets/fuel/fuel_pipe_line): a 3 m length of black coated steel pipe with a red band, for running gasoline or diesel from a bulk fuel tank to
a fuel pump (and tank to tank). Laid with the pipe wrench like a propane line (docs/WIRING.md, "Fuel pumps"); underground when it runs outside.

    blender --background --python tools/make_fuel_line.py
    python tools/render_icon_from_model.py assets/fuel/fuel_pipe_line/fuel_pipe_line.glb assets/fuel/fuel_pipe_line/fuel_pipe_line.png

Lies along x on the ground, centred.
"""
import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_simple_props as props  # noqa: E402

ITEM = 'fuel_pipe_line'
FUEL = os.path.join(props.ROOT, 'assets', 'fuel')
FOLDER = os.path.join(FUEL, ITEM)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    pipe = props.mat('FuelPipe', (0.08, 0.08, 0.09), 0.4)
    red = props.mat('FuelBand', (0.75, 0.1, 0.08), 0.5)
    brass = props.mat('FuelFitting', (0.78, 0.6, 0.25), 0.35)
    r = 0.016
    K = props.Kit()
    K.tube((-1.5, 0, r), (1.5, 0, r), r, r, pipe, 10, pipe, pipe)
    for x in (-1.0, 0.0, 1.0):
        K.tube((x - 0.04, 0, r), (x + 0.04, 0, r), r * 1.06, r * 1.06, red, 10)
    for x in (-1.5, 1.44):
        K.tube((x, 0, r), (x + 0.06, 0, r), r * 1.3, r * 1.3, brass, 8, brass, brass)   # the threaded ends
    K.done(ITEM)
    os.makedirs(FOLDER, exist_ok=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=os.path.join(FOLDER, ITEM + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
    path = os.path.join(FOLDER, ITEM + '.json')
    if os.path.exists(path):
        m = json.load(open(path, encoding='utf-8'))
    else:
        m = json.load(open(os.path.join(FUEL, 'fuel_pipe_propane', 'fuel_pipe_propane.json'), encoding='utf-8'))
        m.update({'id': ITEM, 'icon': ITEM + '.png', 'name': 'Fuel Line',
                  'description': 'A 3 m length of black coated steel pipe for gasoline or diesel. With a pipe wrench in hand, right click a bulk fuel tank and then a '
                                 'fuel pump to lay it (or tank to tank): it runs underground outside.'})
        m['properties'].update({'weight_kg': 4.0, 'base_value': 18, 'max_stack_size': 10, 'placeable': True, 'wire_kind': 'fuel', 'wire_length_m': 3.0,
                                'is_buyable': True, 'stores': ['water']})
    m['models'] = [{'file': ITEM + '.glb', 'format': 'glb', 'dimensions_m': {'x': 3.0, 'y': 0.042, 'z': 0.042}, 'triangles': tris}]
    m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': 3.0, 'depth': 0.04, 'height': 0.04})
    props.save(path, json.dumps(m, indent=2))
    props.save(os.path.join(FOLDER, 'README.md'), '# %s (`%s`)\n\n%s\n\nProcedural model (tools/make_fuel_line.py), %d triangles. `wire_kind: fuel`, 3 m a length. '
               'See docs/WIRING.md.\n' % (m['name'], ITEM, m['description'], tris))
    print('fuel line', tris, 'tris')


if __name__ == '__main__':
    main()
