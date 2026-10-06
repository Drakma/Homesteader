"""
Builds the safety disconnect switch (assets/electricity/electricity_switch_disconnect_safety) as a GLB in headless Blender: free, local,
low-poly (no Meshy), with painted pictures for the lettering.

    python tools/case_labels.py                                   (paints the door label and the ON / OFF plate)
    blender --background --python tools/make_disconnect_switch.py
    python tools/render_icon_from_model.py assets/electricity/electricity_switch_disconnect_safety/electricity_switch_disconnect_safety.glb \
        assets/electricity/electricity_switch_disconnect_safety/electricity_switch_disconnect_safety.png

A grey steel safety switch: the enclosure with mounting ears, a door with a raised rim on two hinges, a latch with a padlock hasp, the operating
handle on the left side (up: on) with a red grip on its pivot hub, a conduit hub on top and one underneath, and on the door the label and the
ON / OFF plate beside the handle (pictures).

The item is already in the kit: only its model entry, its dimensions and its README are written.

Conventions: 1 unit = 1 m, pivot at the centre of the footprint, ground at z = 0, the door facing -y.
"""
import json
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import case_labels  # noqa: E402
import make_simple_props as props  # noqa: E402    (Kit, mat, save)

ITEM = 'electricity_switch_disconnect_safety'
FOLDER = os.path.join(props.ROOT, 'assets', 'electricity', ITEM)
T = Matrix.Translation
mat = props.mat


def build():
    K = props.Kit()
    grey = mat('SwitchSteel', (0.58, 0.6, 0.62), 0.45)
    shade = mat('SwitchSteelShade', (0.44, 0.46, 0.48), 0.5)
    dark = mat('SwitchDark', (0.1, 0.1, 0.11), 0.6)
    red = mat('SwitchGrip', (0.8, 0.1, 0.08), 0.45)
    zinc = mat('SwitchZinc', (0.75, 0.76, 0.78), 0.3)
    W, D, H = 0.2, 0.1, 0.3
    z0 = 0.03                                                             # room underneath for the conduit hub
    yb, yf = D / 2, -D / 2 + 0.014                                        # the back; the front of the body (the door stands in front of it)
    K.bx((W, yb - yf, H), (0, (yb + yf) / 2, z0 + H / 2), grey)
    for sx in (-1, 1):                                                    # mounting ears
        for z in (z0 - 0.012, z0 + H + 0.012):
            K.bx((0.03, 0.004, 0.03), (sx * W * 0.3, yb - 0.002, z), shade)
    # the door: a panel with a raised rim, two hinges on the right, the latch and hasp on the left
    dy = yf - 0.006
    K.bx((W + 0.008, 0.012, H + 0.008), (0, yf - 0.006, z0 + H / 2), grey)
    rim = 0.012
    for z in (z0 + rim / 2, z0 + H - rim / 2):
        K.bx((W + 0.008, 0.005, rim), (0, dy - 0.008, z), shade)
    for sx in (-1, 1):
        K.bx((rim, 0.005, H + 0.008), (sx * (W / 2 + 0.004 - rim / 2), dy - 0.008, z0 + H / 2), shade)
    for z in (z0 + H * 0.22, z0 + H * 0.78):
        K.tube((W / 2 + 0.006, yf - 0.006, z - 0.025), (W / 2 + 0.006, yf - 0.006, z + 0.025), 0.006, 0.006, zinc, 8, zinc, zinc)
    K.bx((0.02, 0.01, 0.045), (-W * 0.36, dy - 0.012, z0 + H * 0.2), zinc)
    K.lathe([(0.009, 0.0), (0.012, 0.004), (0.012, 0.008), (0.009, 0.012)], zinc, 8, T((-W * 0.36, dy - 0.02, z0 + H * 0.2)) @ Matrix.Rotation(1.5708, 4, 'X'), closed=False)
    # the operating handle on the left side (the side the icon shows): a hub on the side of the box, an arm up to a red grip (on)
    hx = -W / 2
    hz = z0 + H * 0.56
    K.lathe([(0.03, 0.0), (0.03, 0.014), (0.022, 0.02), (0.0, 0.02)], shade, 12, T((hx, 0.0, hz)) @ Matrix.Rotation(-1.5708, 4, 'Y'))
    K.box((0.012, 0.022, 0.11), T((hx - 0.026, 0.0, hz)) @ Matrix.Rotation(-0.35, 4, 'X') @ T((0, 0, 0.05)), zinc)
    K.box((0.022, 0.03, 0.05), T((hx - 0.026, 0.0, hz)) @ Matrix.Rotation(-0.35, 4, 'X') @ T((0, 0, 0.115)), red)
    K.bx((0.006, 0.05, 0.14), (hx - 0.003, 0.0, hz), dark)                                                # the slot plate behind it
    # the conduit hubs, top and bottom
    for z, s in ((z0 + H, 1), (z0, -1)):
        K.lathe([(0.022, 0.0), (0.022, s * 0.01), (0.017, s * 0.012), (0.017, s * 0.03), (0.0, s * 0.03)], zinc, 10, T((0, 0.008, z)))
        K.lathe([(0.026, s * 0.002), (0.026, s * 0.008)], shade, 6, T((0, 0.008, z)))
    obj = K.done('switch')
    # the pictures on the door: the label, and the ON / OFF plate beside the handle
    y = dy - 0.0065
    lw = W * 0.7
    lh = lw / case_labels.ASPECT
    zc = z0 + H * 0.7
    obj = case_labels.add_flat(obj, 'disconnect_label', [[(-lw / 2 + 0.012, y, zc - lh / 2), (lw / 2 + 0.012, y, zc - lh / 2), (lw / 2 + 0.012, y, zc + lh / 2), (-lw / 2 + 0.012, y, zc + lh / 2)]])
    pw, ph = 0.034, 0.085
    px, pz = -W * 0.34, z0 + H * 0.46
    return case_labels.add_flat(obj, 'disconnect_onoff', [[(px - pw / 2, y, pz - ph / 2), (px + pw / 2, y, pz - ph / 2), (px + pw / 2, y, pz + ph / 2), (px - pw / 2, y, pz + ph / 2)]])


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj = build()
    obj.name = ITEM
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
    m.pop('dimensions', None)
    m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
    props.save(path, json.dumps(m, indent=2))
    props.save(os.path.join(FOLDER, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_disconnect_switch.py), %d triangles, %.2f x %.2f x %.2f m: a grey steel '
               'enclosure, a rimmed door on two hinges, a latch with a hasp, the side handle with a red grip, conduit hubs top and bottom. The door label and the '
               'ON / OFF plate are pictures (tools/case_labels.py).\n' % (m['name'], m['description'], tris, *dims))
    print('switch', ITEM, '|', tris, 'tris |', dims)


if __name__ == '__main__':
    main()
