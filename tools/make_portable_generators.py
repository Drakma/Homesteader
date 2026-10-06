"""
Builds the two wheeled open-frame generators as GLBs in headless Blender: free, local, low-poly (no Meshy), with painted pictures for the detail.

    python tools/case_labels.py                                   (paints the pictures: control panel, tank label, heat shield, cooling fins)
    blender --background --python tools/make_portable_generators.py
    python tools/render_icon_from_model.py assets/electricity/<id>/<id>.glb assets/electricity/<id>/<id>.png

  electricity_generator               the 5 kW portable generator: red tank
  electricity_generator_frame_7500w   the 7.5 kW frame generator: yellow tank, a size bigger

One design: a black tube frame (two side loops and cross tubes), a fuel tank on top with a cap and a gauge, the engine (crankcase, finned
cylinder, air filter, recoil starter with its pull handle), the alternator, a muffler behind a perforated heat shield, a control panel, two
wheels on an axle at one end, two rubber feet at the other, and a folding handle. The control panel, the tank label, the heat shield and the
cooling fins are pictures on the model, not geometry.

Both items are already in the kit: only the model entry, the dimensions and the README are written.

Conventions: 1 unit = 1 m, pivot at the centre of the footprint, ground at z = 0, the length along x, the control panel facing -y.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import case_labels  # noqa: E402
import make_simple_props as props  # noqa: E402    (Kit, mat, save, RX, RY)

ELEC = os.path.join(props.ROOT, 'assets', 'electricity')
T = Matrix.Translation
mat = props.mat

# item: (watts, length, width, height of the frame, wheel radius, tank colour)
GENERATORS = {
    'electricity_generator': (5000, 0.66, 0.46, 0.5, 0.1, (0.78, 0.08, 0.06)),
    'electricity_generator_frame_7500w': (7500, 0.78, 0.54, 0.58, 0.115, (0.95, 0.72, 0.06)),
}


def build(watts, L, W, H, wr, tank_rgb):
    K = props.Kit()
    frame = mat('GeneratorFrame', (0.07, 0.07, 0.08), 0.5)
    tank = mat('GeneratorTank', tank_rgb, 0.35)
    engine = mat('EngineCast', (0.42, 0.43, 0.45), 0.5)
    black = mat('GeneratorBlack', (0.06, 0.06, 0.07), 0.7)
    steel = mat('GeneratorSteel', (0.66, 0.67, 0.69), 0.3)
    rubber = mat('Tyre', (0.05, 0.05, 0.055), 0.9)
    hub = mat('WheelHub', (0.85, 0.85, 0.83), 0.4)
    copper = mat('Alternator', (0.2, 0.2, 0.22), 0.5)
    r = 0.014                                                            # the frame tube
    z0 = wr * 0.9                                                        # the bottom rail of the frame
    zt = z0 + H
    xl, xr = -L / 2, L / 2
    # the frame: a loop each side, cross tubes at the four corners and under the engine
    for sy in (-1, 1):
        y = sy * W / 2
        c = 0.05
        loop = [(xl + c, y, z0), (xr - c, y, z0), (xr, y, z0 + c), (xr, y, zt - c), (xr - c, y, zt), (xl + c, y, zt), (xl, y, zt - c), (xl, y, z0 + c), (xl + c, y, z0)]
        K.path(loop, r, frame, 8, caps=False)
    for x, z in ((xl + 0.05, z0), (xr - 0.05, z0), (xl + 0.05, zt), (xr - 0.05, zt), (-L * 0.12, z0), (L * 0.16, z0)):
        K.tube((x, -W / 2, z), (x, W / 2, z), r, r, frame, 8)
    K.bx((L * 0.62, W * 0.7, 0.008), (0, 0, z0 + r), steel)                                 # the engine plate
    # the tank on top: a flat body with slanted shoulders, the cap, the gauge
    th = H * 0.24
    tz = zt - th + 0.01
    tl, tw = L * 0.86, W * 0.86
    side = [(-tw / 2 + 0.03, 0.0), (tw / 2 - 0.03, 0.0), (tw / 2, 0.03), (tw / 2, th - 0.035), (tw / 2 - 0.035, th), (-tw / 2 + 0.035, th), (-tw / 2, th - 0.035), (-tw / 2, 0.03)]
    along_x = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    K.prism(side, tl, T((-tl / 2, 0, tz)) @ along_x, tank)
    K.lathe([(0.034, 0.0), (0.034, 0.014), (0.03, 0.02), (0.0, 0.02)], black, 12, T((tl * 0.22, 0, tz + th)))
    K.lathe([(0.024, 0.0), (0.024, 0.006), (0.0, 0.007)], steel, 10, T((-tl * 0.22, 0, tz + th)))
    K.lathe([(0.018, 0.0072), (0.0, 0.0072)], mat('GaugeFace', (0.92, 0.92, 0.88), 0.4), 10, T((-tl * 0.22, 0, tz + th)))
    # the engine, in the left half: crankcase, the cylinder leaning back, the air filter, the recoil starter on the front
    ex = -L * 0.2
    ez = z0 + r + 0.008
    eh = (tz - ez) * 0.62
    K.bx((L * 0.3, W * 0.5, eh), (ex, 0.0, ez + eh / 2), engine)
    cyl = T((ex, W * 0.06, ez + eh)) @ Matrix.Rotation(-0.35, 4, 'X')
    ch = (tz - ez) * 0.36
    K.box((L * 0.2, W * 0.3, ch), cyl @ T((0, 0, ch / 2 - 0.01)), engine)
    K.box((L * 0.22, W * 0.32, 0.02), cyl @ T((0, 0, ch - 0.005)), black)                                        # the head cover
    K.bx((L * 0.16, W * 0.2, 0.09), (ex - L * 0.02, -W * 0.22, ez + eh + 0.05), black)                           # the air filter
    front = -W * 0.25
    rc = T((ex, front, ez + eh * 0.5)) @ Matrix.Rotation(math.pi / 2, 4, 'X')
    rr = min(eh * 0.46, L * 0.13)
    K.lathe([(rr, 0.0), (rr, 0.03), (rr * 0.8, 0.045), (0.0, 0.048)], black, 14, rc)                                 # the recoil starter
    K.bx((0.05, 0.02, 0.018), (ex + rr * 0.8, front - 0.055, ez + eh * 0.5 + rr * 0.55), black)                      # its pull handle
    K.tube((ex + rr * 0.5, front - 0.04, ez + eh * 0.5 + rr * 0.4), (ex + rr * 0.8, front - 0.055, ez + eh * 0.5 + rr * 0.55), 0.003, 0.003, steel, 5)
    # the alternator, in the right half, and the control panel on its front
    ax0, ax1 = ex + L * 0.15, L * 0.34
    ar = min(eh * 0.52, W * 0.2)
    az = ez + ar + 0.01
    K.lathe([(ar * 0.9, 0.0), (ar, 0.02), (ar, ax1 - ax0 - 0.03), (ar * 0.8, ax1 - ax0), (0.0, ax1 - ax0)], copper, 14, T((ax0, W * 0.04, az)) @ props.RX)
    for k in range(4):                                                                                               # the bolts through it
        a = math.pi / 4 + k * math.pi / 2
        K.tube((ax0 + 0.01, W * 0.04 + ar * 1.02 * math.cos(a), az + ar * 1.02 * math.sin(a)), (ax1 - 0.02, W * 0.04 + ar * 1.02 * math.cos(a), az + ar * 1.02 * math.sin(a)),
               0.004, 0.004, steel, 5)
    pw, ph = L * 0.38, (tz - ez) * 0.72
    px, pz = L * 0.2, ez + (tz - ez) * 0.5
    py = -W / 2 + 0.03
    K.bx((pw, 0.03, ph), (px, py + 0.015, pz), black)
    # the muffler at the back, behind its heat shield
    mz = ez + eh + 0.05
    K.lathe([(0.0, 0.0), (0.04, 0.0), (0.045, 0.02), (0.045, L * 0.3), (0.04, L * 0.32), (0.0, L * 0.32)], steel, 10, T((ex - L * 0.1, W * 0.27, mz)) @ props.RX)
    K.tube((ex + L * 0.22, W * 0.27, mz), (ex + L * 0.27, W * 0.33, mz - 0.01), 0.012, 0.012, steel, 6, None, black)        # the tail pipe
    # the wheels at the right end, on an axle; the feet at the left; the handle folded down the left end
    wx = xr - 0.07
    K.tube((wx, -W / 2 - 0.05, wr), (wx, W / 2 + 0.05, wr), 0.008, 0.008, steel, 6)
    for sy in (-1, 1):
        mx = T((wx, sy * (W / 2 + 0.035), wr)) @ props.RY
        tyre = [(wr * 0.62, -0.022), (wr * 0.94, -0.024), (wr, -0.014), (wr, 0.014), (wr * 0.94, 0.024), (wr * 0.62, 0.022)]
        K.lathe(tyre, rubber, 16, mx, closed=True)
        K.lathe([(wr * 0.62, -0.016), (wr * 0.2, -0.02), (0.0, -0.022)], hub, 12, mx)
        K.lathe([(wr * 0.62, 0.016), (wr * 0.2, 0.02), (0.0, 0.022)], hub, 12, mx)
        K.bx((0.03, 0.006, z0 - wr + 0.03), (wx, sy * (W / 2 - 0.004), (z0 + wr) / 2), frame)                              # the axle bracket
        fx = xl + 0.06
        K.tube((fx, sy * W / 2, z0), (fx, sy * W / 2, 0.02), r * 0.9, r * 0.9, frame, 8)                                   # a foot
        K.lathe([(0.026, 0.0), (0.026, 0.016), (0.018, 0.022)], rubber, 10, T((fx, sy * W / 2, 0.0)))
        hy = sy * (W / 2 - 0.05)
        K.path([(xl - 0.02, hy, zt - 0.04), (xl - 0.024, hy, zt - 0.3)], 0.011, frame, 8)                                  # a handle arm, hanging
        K.tube((xl - 0.024, hy, zt - 0.3), (xl - 0.024, hy, zt - 0.42), 0.016, 0.016, rubber, 8, rubber, rubber)           # its grip
        K.bx((0.03, 0.03, 0.03), (xl - 0.008, hy, zt - 0.03), steel)                                                       # its pivot
    obj = K.done('generator')
    # the pictures: the control panel, the tank label both sides, the heat shield, the cooling fins on the cylinder and the recoil vents
    e = 0.0015
    y = py - e
    obj = case_labels.add_flat(obj, 'generator_panel_%d' % watts,
                               [[(px - pw / 2 + 0.006, y, pz - ph / 2 + 0.006), (px + pw / 2 - 0.006, y, pz - ph / 2 + 0.006),
                                 (px + pw / 2 - 0.006, y, pz + ph / 2 - 0.006), (px - pw / 2 + 0.006, y, pz + ph / 2 - 0.006)]])
    lh = th * 0.62
    lw = lh * case_labels.ASPECT
    lz = tz + th * 0.5
    labels = []
    for sy in (-1, 1):
        yy = sy * (tw / 2 + e)
        x0, x1 = (-lw / 2, lw / 2) if sy < 0 else (lw / 2, -lw / 2)
        labels.append([(x0, yy, lz - lh / 2), (x1, yy, lz - lh / 2), (x1, yy, lz + lh / 2), (x0, yy, lz + lh / 2)])
    obj = case_labels.add_flat(obj, 'generator_tank_%d' % watts, labels)
    sx0, sx1 = ex - L * 0.11, ex + L * 0.23
    ys = W * 0.27 + 0.05
    obj = case_labels.add_flat(obj, 'generator_shield', [[(sx1, ys, mz - 0.055), (sx0, ys, mz - 0.055), (sx0, ys, mz + 0.055), (sx1, ys, mz + 0.055)],
                                                         [(sx0, ys - 0.1, mz + 0.056), (sx1, ys - 0.1, mz + 0.056), (sx1, ys, mz + 0.056), (sx0, ys, mz + 0.056)]])
    fx0, fx1 = ex - L * 0.15 - e, ex + L * 0.15 + e
    fins = [[(fx0, W * 0.25, ez + 0.02), (fx0, -W * 0.25, ez + 0.02), (fx0, -W * 0.25, ez + eh - 0.01), (fx0, W * 0.25, ez + eh - 0.01)],          # the crankcase's left end
            [(ex - rr * 0.6, front - 0.049, ez + eh * 0.5 - rr * 0.6), (ex + rr * 0.6, front - 0.049, ez + eh * 0.5 - rr * 0.6),
             (ex + rr * 0.6, front - 0.049, ez + eh * 0.5 + rr * 0.6), (ex - rr * 0.6, front - 0.049, ez + eh * 0.5 + rr * 0.6)]]                 # the recoil vents
    return case_labels.add_flat(obj, 'generator_fins', fins)


def main():
    for item, (watts, L, W, H, wr, rgb) in GENERATORS.items():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obj = build(watts, L, W, H, wr, rgb)
        obj.name = item
        folder = os.path.join(ELEC, item)
        path = os.path.join(folder, item + '.json')
        if not os.path.exists(path):
            print('SKIP (not in the kit)', item)
            continue
        pts = [v.co for v in obj.data.vertices]
        lo = [min(p[i] for p in pts) for i in range(3)]
        hi = [max(p[i] for p in pts) for i in range(3)]
        obj.data.transform(T((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])))
        dims = [round(hi[i] - lo[i], 3) for i in range(3)]
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.export_scene.gltf(filepath=os.path.join(folder, item + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
        m = json.load(open(path, encoding='utf-8'))
        m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
        m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
        props.save(path, json.dumps(m, indent=2))
        props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_portable_generators.py), %d triangles, %.2f x %.2f x %.2f m: a tube frame '
                   'on two wheels and two feet, tank, engine, alternator, muffler, folding handle. The control panel, tank label, heat shield and cooling fins are '
                   'pictures (tools/case_labels.py).\n' % (m['name'], m['description'], tris, *dims))
        print('generator', item, '|', tris, 'tris |', dims)


if __name__ == '__main__':
    main()
