"""
The generator lockout box (assets/electricity/electricity_generator_lockout_box): a grey weatherproof box with a generator inlet on its front, mounted on the
OUTSIDE wall of a building. A standby generator is wired to it with AC wire; the box switches the building between its breaker box and the generator, never
both (Assets/Scripts/Growth/Wiring.cs, TickLockouts). Its handle is a SEPARATE object named "Handle" with its origin on the hinge: up = on the breaker box,
down = on the generator (it moves by itself, Disconnect.cs animates it).

    blender --background --python tools/make_lockout.py
    python tools/render_icon_from_model.py <glb> <png>

Convention for a wall item (docs/ATTACHED_ITEMS.md): the back against the wall at y = 0, the front facing -y, the bottom at z = 0, centred on x.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_simple_props as props  # noqa: E402

ITEM = 'electricity_generator_lockout_box'
TEMPLATE = 'electricity_switch_disconnect_safety'
ELEC = os.path.join(props.ROOT, 'assets', 'electricity')
FOLDER = os.path.join(ELEC, ITEM)
W, D, H = 0.3, 0.12, 0.4
PIVOT = (W / 2 + 0.012, -D * 0.55, H * 0.62)


def build():
    steel = props.mat('BoxSteel', (0.6, 0.62, 0.64), 0.4)
    dark = props.mat('BoxDark', (0.1, 0.1, 0.11), 0.5)
    yellow = props.mat('Inlet', (0.95, 0.75, 0.1), 0.5)
    red = props.mat('LockoutLever', (0.8, 0.12, 0.1), 0.45)
    grip = props.mat('LockoutGrip', (0.08, 0.08, 0.09), 0.7)
    K = props.Kit()
    K.bx((W, D, H), (0, -D / 2, H / 2), steel)
    K.bx((W + 0.02, D + 0.02, 0.012), (0, -D / 2 - 0.005, H + 0.006), steel)
    K.bx((W - 0.03, 0.006, H - 0.04), (0, -D - 0.003, H / 2), steel)
    # the generator inlet on the front: a yellow round receptacle under a flip cover
    face = T = Matrix.Translation
    K.lathe([(0.0, 0.0), (0.045, 0.0), (0.045, 0.03), (0.035, 0.035), (0.0, 0.035)], yellow, 16, T((0, -D - 0.006, H * 0.35)) @ Matrix.Rotation(math.pi / 2, 4, 'X'))
    for a in (0.0, 2.1, 4.2):
        K.bx((0.008, 0.004, 0.014), (0.02 * math.cos(a), -D - 0.043, H * 0.35 + 0.02 * math.sin(a)), dark)
    K.bx((0.11, 0.012, 0.012), (0, -D - 0.02, H * 0.35 + 0.06), dark)              # the cover's hinge bar
    K.tube((W / 2, PIVOT[1], PIVOT[2]), (PIVOT[0], PIVOT[1], PIVOT[2]), 0.016, 0.016, dark, 10, None, dark)
    K.done(ITEM)
    L = props.Kit()
    L.bx((0.012, 0.022, 0.13), (0.0, 0.0, 0.065), red)
    L.bx((0.03, 0.03, 0.04), (0.0, 0.0, 0.13), grip)
    h = L.done('Handle')
    h.location = PIVOT
    _ = face


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    build()
    os.makedirs(FOLDER, exist_ok=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=os.path.join(FOLDER, ITEM + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
    path = os.path.join(FOLDER, ITEM + '.json')
    m = json.load(open(path if os.path.exists(path) else os.path.join(ELEC, TEMPLATE, TEMPLATE + '.json'), encoding='utf-8'))
    m.update({'id': ITEM, 'icon': ITEM + '.png', 'name': 'Generator Lockout Box',
              'description': 'A weatherproof transfer box with a generator inlet, mounted on the OUTSIDE wall of a building. Wire a standby generator to it with AC '
                             'wire: the building runs on its breaker box while that can carry it, and the box switches it over to the generator when the breaker box '
                             'has no power, cannot carry the load or its batteries run low, then back once they have recovered. Never both at once. The handle shows '
                             'which side is feeding: up the breaker box, down the generator.'})
    m['properties'].update({'placeable': False, 'attach_surface': 'wall', 'attach_side': 'exterior', 'wire_role': 'generator_lockout', 'base_value': 260,
                            'weight_kg': 9.0, 'is_buyable': True, 'stores': ['voltvision']})
    m['models'] = [{'file': ITEM + '.glb', 'format': 'glb', 'dimensions_m': {'x': round(W + 0.05, 3), 'y': round(H + 0.012, 3), 'z': round(D + 0.05, 3)}, 'triangles': tris}]
    m.setdefault('category_fields', {})['dimensions_m'] = {'width': round(W + 0.05, 2), 'depth': round(D + 0.05, 2), 'height': round(H + 0.01, 2)}
    props.save(path, json.dumps(m, indent=2))
    props.save(os.path.join(FOLDER, 'README.md'), '# %s (`%s`)\n\n%s\n\nProcedural model (tools/make_lockout.py), %d triangles. Its handle is a separate object named '
               '`Handle` with its origin on the hinge. `wire_role: generator_lockout`. See docs/WIRING.md.\n' % (m['name'], ITEM, m['description'], tris))
    print('lockout', tris, 'tris')


if __name__ == '__main__':
    main()
