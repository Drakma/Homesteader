"""
The safety disconnect switch (assets/electricity/electricity_switch_disconnect_safety): a grey steel enclosure that mounts on a wall, with its throw handle as a
SEPARATE object named "Handle" whose origin is the hinge, so the game can swing it: up is on, down is off (Assets/Scripts/Growth/Disconnect.cs).

    blender --background --python tools/make_disconnect.py
    python tools/render_icon_from_model.py assets/electricity/electricity_switch_disconnect_safety/electricity_switch_disconnect_safety.glb \
        assets/electricity/electricity_switch_disconnect_safety/electricity_switch_disconnect_safety.png

Convention for a wall item (docs/ATTACHED_ITEMS.md): the back against the wall at y = 0, the front facing -y, the bottom at z = 0, centred on x.
"""
import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_simple_props as props  # noqa: E402

ITEM = 'electricity_switch_disconnect_safety'
FOLDER = os.path.join(props.ROOT, 'assets', 'electricity', ITEM)
W, D, H = 0.25, 0.14, 0.36
PIVOT = (W / 2 + 0.012, -D * 0.55, H * 0.6)


def build():
    steel = props.mat('SwitchSteel', (0.62, 0.64, 0.66), 0.4)
    dark = props.mat('SwitchDark', (0.12, 0.12, 0.13), 0.5)
    red = props.mat('SwitchLever', (0.8, 0.12, 0.1), 0.45)
    grip = props.mat('SwitchGrip', (0.08, 0.08, 0.09), 0.7)
    yellow = props.mat('SwitchLabel', (0.95, 0.78, 0.1), 0.5)
    K = props.Kit()
    K.bx((W, D, H), (0, -D / 2, H / 2), steel)                                   # the enclosure
    K.bx((W + 0.02, D + 0.02, 0.012), (0, -D / 2 - 0.005, H + 0.006), steel)     # its rain hood
    K.bx((W - 0.03, 0.006, H - 0.04), (0, -D - 0.003, H / 2), steel)             # the door
    K.bx((0.1, 0.004, 0.035), (0, -D - 0.007, H * 0.78), yellow)                 # the warning label
    K.bx((0.02, 0.012, 0.04), (-W / 2 + 0.03, -D - 0.008, H / 2), dark)          # the door latch
    K.tube((W / 2, PIVOT[1], PIVOT[2]), (PIVOT[0], PIVOT[1], PIVOT[2]), 0.016, 0.016, dark, 10, None, dark)   # the hinge boss
    K.done(ITEM)
    # the handle: from the hinge straight up (on), its origin on the hinge
    L = props.Kit()
    L.bx((0.012, 0.022, 0.13), (0.0, 0.0, 0.065), red)
    L.bx((0.03, 0.03, 0.04), (0.0, 0.0, 0.13), grip)
    h = L.done('Handle')
    h.location = PIVOT


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    build()
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=os.path.join(FOLDER, ITEM + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
    path = os.path.join(FOLDER, ITEM + '.json')
    m = json.load(open(path, encoding='utf-8'))
    m['name'] = 'Safety Disconnect Switch'
    m['description'] = ('A fused safety disconnect in a grey steel box. Mount it on a wall (inside or out) and wire it into a run, AC or DC: between the solar panels '
                        'and the wall entry, the battery and the inverter, or the inverter (or a generator) and a breaker box. Right click it to throw the handle: up the '
                        'power flows, down it is cut.')
    pr = m['properties']
    pr.update({'placeable': False, 'attach_surface': 'wall', 'attach_side': 'either', 'wire_role': 'disconnect'})
    m['models'] = [{'file': ITEM + '.glb', 'format': 'glb', 'dimensions_m': {'x': round(W + 0.05, 3), 'y': round(H + 0.012, 3), 'z': round(D + 0.01, 3)}, 'triangles': tris}]
    m.setdefault('category_fields', {})['dimensions_m'] = {'width': round(W + 0.05, 2), 'depth': round(D + 0.01, 2), 'height': round(H + 0.01, 2)}
    props.save(path, json.dumps(m, indent=2))
    props.save(os.path.join(FOLDER, 'README.md'), '# %s (`%s`)\n\n%s\n\nProcedural model (tools/make_disconnect.py), %d triangles. Its throw handle is a separate '
               'object named `Handle` with its origin on the hinge (up = on, down = off; `Assets/Scripts/Growth/Disconnect.cs`). `wire_role: disconnect`. '
               'See docs/WIRING.md.\n' % (m['name'], ITEM, m['description'], tris))
    print('disconnect', tris, 'tris')


if __name__ == '__main__':
    main()
