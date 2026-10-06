"""
Builds the DC breaker boxes as GLBs in headless Blender: free, local, low-poly (no Meshy).

    python tools/case_labels.py                                   (paints the rating labels: "32A  DC BREAKER BOX")
    blender --background --python tools/make_dc_breaker_boxes.py
    python tools/render_icon_from_model.py assets/electricity/<id>/<id>.glb assets/electricity/<id>/<id>.png

  electricity_breaker_box_dc_32a     two breakers
  electricity_breaker_box_dc_64a     four breakers
  electricity_breaker_box_dc_128a    eight breakers

A white wall box: the enclosure with mounting ears, a door frame round an open window, the row of white breakers with blue levers on their rail
in the dark well behind it, a hinge down the left and a latch on the right, cable glands underneath, and the rating label under the window. The rating is
`category_fields.max_current_a`, which the name generators show ("DC Breaker Box (32 A)"); it is not in the stored name.

A new item gets its manifest from electricity_panel_breaker_outdoor_100a (a wall-mounted box); an item that is already in the kit keeps its
name, price and the rest.

Conventions (the wall boxes of tools/make_solar_breaker_models.py): 1 unit = 1 m, x centred, the back against the wall at y = 0, the front
facing -y, the bottom of the box at z = 0.
"""
import json
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import case_labels  # noqa: E402
import make_simple_props as props  # noqa: E402    (Kit, mat, save)

ELEC = os.path.join(props.ROOT, 'assets', 'electricity')
T = Matrix.Translation
mat = props.mat

# amps: (width, depth, height, breakers, kg, price)
BOXES = {32: (0.2, 0.1, 0.24, 2, 1.2, 45), 64: (0.3, 0.11, 0.28, 4, 2.0, 80), 128: (0.44, 0.12, 0.34, 8, 3.4, 150)}


def build(amps):
    W, D, H, count = BOXES[amps][:4]
    K = props.Kit()
    white = mat('BoxWhite', (0.94, 0.94, 0.92), 0.45)
    shade = mat('BoxWhiteShade', (0.78, 0.78, 0.76), 0.5)
    inside = mat('BoxInside', (0.2, 0.23, 0.27), 0.5)
    lever = mat('BreakerLever', (0.12, 0.3, 0.62), 0.45)
    steel = mat('BoxSteel', (0.62, 0.63, 0.65), 0.35)
    dark = mat('BoxDark', (0.1, 0.1, 0.11), 0.6)
    yb = -D * 0.72                                                        # the front of the body; the door stands in front of it
    K.bx((W, D * 0.72, H), (0, yb / 2, H / 2), white)
    for sx in (-1, 1):                                                    # mounting ears, top and bottom
        for z in (-0.012, H + 0.012):
            K.bx((0.03, 0.004, 0.03), (sx * W * 0.32, -0.002, z), shade)
            K.lathe([(0.004, 0.0), (0.004, 0.0015), (0.0, 0.0015)], dark, 6, T((sx * W * 0.32, -0.004, z)) @ Matrix.Rotation(1.5708, 4, 'X'))
    # the door: a frame round a smoked window, a little proud of the body
    door_d = D * 0.28
    yf = yb - door_d
    fw = 0.022
    K.bx((W - 0.006, door_d, fw), (0, yb - door_d / 2, H - fw / 2 - 0.003), white)
    K.bx((W - 0.006, door_d, H * 0.3), (0, yb - door_d / 2, H * 0.15 + 0.003), white)
    for sx in (-1, 1):
        K.bx((fw, door_d, H - 0.006), (sx * (W / 2 - 0.003 - fw / 2), yb - door_d / 2, H / 2), white)
    wz0, wz1 = H * 0.3 + 0.003, H - fw - 0.003
    ww = W - 0.006 - 2 * fw
    K.bx((ww, 0.002, wz1 - wz0), (0, yb - 0.001, (wz0 + wz1) / 2), inside)             # the back of the well the breakers sit in
    # the breakers on their rail, seen through the window
    zc = (wz0 + wz1) / 2
    pole = min(0.018, (ww - 0.02) / count)
    bh = min(0.082, (wz1 - wz0) * 0.8)
    K.bx((ww - 0.01, 0.004, 0.035), (0, yb - 0.003, zc), steel)                        # the rail
    for k in range(count):
        x = (k - (count - 1) / 2) * pole
        K.bx((pole - 0.0012, door_d * 0.5, bh), (x, yb - door_d * 0.25, zc), white)
        K.bx((pole - 0.0012, door_d * 0.14, bh * 0.34), (x, yb - door_d * 0.56, zc), shade)
        K.bx((pole * 0.5, 0.008, bh * 0.2), (x, yb - door_d * 0.66, zc + bh * 0.05), lever, Matrix.Rotation(-0.5, 4, 'X'))
    # the hinge down the left, the latch on the right
    K.tube((-W / 2 - 0.004, yf + door_d * 0.5, H * 0.08), (-W / 2 - 0.004, yf + door_d * 0.5, H * 0.92), 0.005, 0.005, shade, 8, shade, shade)
    K.bx((0.012, 0.012, H * 0.2), (W / 2 + 0.002, yf + door_d * 0.5, H * 0.5), dark)
    K.bx((0.006, 0.02, H * 0.12), (W / 2 + 0.008, yf + door_d * 0.5, H * 0.5), steel)
    # the cable glands underneath
    glands = 2 if count <= 2 else 3 if count <= 4 else 4
    for k in range(glands):
        x = (k - (glands - 1) / 2) * W / (glands + 0.5)
        K.lathe([(0.016, 0.0), (0.016, -0.012), (0.012, -0.014), (0.012, -0.03), (0.0, -0.03)], shade, 8, T((x, yb / 2, 0.0)))
        K.lathe([(0.019, -0.002), (0.019, -0.008)], steel, 6, T((x, yb / 2, 0.0)))
    obj = K.done('box')
    lw = min(W * 0.8, 0.26)                                                           # the rating label, on the door under the window
    lh = min(lw / case_labels.ASPECT, H * 0.22)
    lw = lh * case_labels.ASPECT
    y, zl = yf - 0.0006, H * 0.15 + 0.003
    quad = [(-lw / 2, y, zl - lh / 2), (lw / 2, y, zl - lh / 2), (lw / 2, y, zl + lh / 2), (-lw / 2, y, zl + lh / 2)]
    return case_labels.add_flat(obj, 'breaker_box_dc_%da' % amps, [quad])


def main():
    src = json.load(open(os.path.join(ELEC, 'electricity_panel_breaker_outdoor_100a', 'electricity_panel_breaker_outdoor_100a.json'), encoding='utf-8'))
    for amps, (W, D, H, count, kg, price) in BOXES.items():
        item = 'electricity_breaker_box_dc_%da' % amps
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obj = build(amps)
        obj.name = item
        folder = os.path.join(ELEC, item)
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
            m.update({'id': item, 'icon': item + '.png', 'name': 'DC Breaker Box',
                      'description': 'A white wall-mounted DC breaker box with %d breakers behind its window, for battery and solar circuits.' % count})
            p = m['properties']
            p.update({'weight_kg': kg, 'base_value': price, 'max_stack_size': 10, 'placeable': False, 'attach_surface': 'wall', 'attach_side': 'interior',
                      'footprint': '%.2fm W x %.2fm D x %.2fm H' % (dims[0], dims[1], dims[2])})
            p.pop('provides_power', None)                # (the outdoor service box brings a building its power; this one does not, yet)
            m['category_fields'] = {'fuel_type': 'none', 'fuel_consumption_l_per_min': 0, 'max_power_w': 0, 'tank_capacity_l': 0, 'max_current_a': amps}
        m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
        m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
        props.save(path, json.dumps(m, indent=2))
        props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_dc_breaker_boxes.py), %d triangles, %.2f x %.2f x %.2f m. Rated %d A: the rating '
                   'is on the label under the window and stored in `category_fields.max_current_a`.\n' % (m['name'], m['description'], tris, *dims, amps))
        print('box', item, '|', tris, 'tris |', dims)


if __name__ == '__main__':
    main()
