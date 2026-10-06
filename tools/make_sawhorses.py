"""
Builds the three sawhorses as GLBs in headless Blender: free, local, low-poly (no Meshy).

    blender --background --python tools/make_sawhorses.py
    python tools/render_icon_from_model.py assets/tools/<id>/<id>.glb assets/tools/<id>/<id>.png

  tool_sawhorse_wood      a carpenter's A-frame of 2x4 lumber: a capped beam, four splayed legs cut to the floor, plywood gussets, stretchers, screws
  tool_sawhorse_plastic   a folding moulded sawhorse: two yellow leg frames with pressed panels, a black top rail with 2x4 notches, a tray shelf, rubber feet
  tool_sawhorse_metal     a folding steel sawhorse: tube legs, a channel top rail, hinge brackets with bolts, folding stays, rubber feet

A new item gets its manifest from tool_cement_mixer's; an item that is already in the kit keeps its name, price and the rest (only the model entry
and the dimensions change).

Conventions: 1 unit = 1 m, pivot at the centre of the footprint, ground at z = 0, the beam along x.
"""
import json
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_simple_props as props  # noqa: E402    (Kit, mat, save)

ROOT = props.ROOT
TOOLS = os.path.join(ROOT, 'assets', 'tools')
T = Matrix.Translation
mat = props.mat
ALONG_X = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))       # an outline drawn in y-z, pulled out along x


def wood():
    """Pine 2x4s: 38 x 89 mm. The legs lean out 15 degrees and are cut level top and bottom."""
    K, rnd = props.Kit(), random.Random(4)
    pine = [mat('Pine', (0.8, 0.58, 0.32), 0.85), mat('PineLight', (0.86, 0.65, 0.38), 0.85), mat('PineDark', (0.7, 0.49, 0.26), 0.85)]
    end = mat('PineEndGrain', (0.6, 0.4, 0.2), 0.9)
    ply = mat('Plywood', (0.74, 0.55, 0.32), 0.85)
    ply_edge = mat('PlywoodEdge', (0.5, 0.34, 0.18), 0.9)
    screw = mat('Screw', (0.3, 0.3, 0.32), 0.4)
    knot = mat('Knot', (0.42, 0.26, 0.13), 0.9)
    H, L = 0.76, 1.0
    t, w = 0.038, 0.089
    lean = math.radians(15)
    web_top = H - t
    # the beam: a 2x4 on edge with a 2x4 cap laid flat on it
    K.bx((L * 0.9, t, w), (0, 0, web_top - w / 2), pine[0])
    K.bx((L, w, t), (0, 0, H - t / 2), pine[1])
    for s in (-1, 1):
        K.bx((0.002, w - 0.008, t - 0.008), (s * (L / 2 + 0.001), 0, H - t / 2), end)
        K.bx((0.002, t - 0.008, w - 0.008), (s * (L * 0.45 + 0.001), 0, web_top - w / 2), end)
    # the legs
    a = w / 2 / math.cos(lean)
    leg_x = L * 0.45 - 0.1
    y_at = lambda z: t / 2 + a + (web_top - z) * math.tan(lean)           # the middle of a leg at height z
    for sx in (-1, 1):
        for sy in (-1, 1):
            yt, yb = sy * y_at(web_top), sy * y_at(0.0)
            K.prism([(yb - a, 0.0), (yb + a, 0.0), (yt + a, web_top), (yt - a, web_top)], t, T((sx * leg_x - t / 2, 0, 0)) @ ALONG_X, rnd.choice(pine),
                    [end, pine[2], end, pine[2]])
            for z in (web_top - 0.03, web_top - 0.07):                     # two screws into the beam
                K.tube((sx * leg_x, sy * (y_at(z) + a * 0.9), z), (sx * leg_x, sy * (y_at(z) + a * 0.9 + 0.004), z + 0.001), 0.006, 0.006, screw, 6, None, screw)
        # a plywood gusset across each pair of legs, on the outside
        z0, z1 = web_top - 0.26, web_top - 0.02
        gx = sx * (leg_x + t / 2 + 0.006)
        K.prism([(-y_at(z0) - a, z0), (y_at(z0) + a, z0), (y_at(z1) + a, z1), (-y_at(z1) - a, z1)], 0.012, T((gx - 0.006, 0, 0)) @ ALONG_X, ply,
                [ply_edge] * 4)
        for sy in (-1, 1):
            for z in (z0 + 0.04, z0 + 0.12, z1 - 0.04):
                K.tube((gx, sy * y_at(z), z), (gx + sx * 0.008, sy * y_at(z), z), 0.006, 0.006, screw, 6, screw, screw)
    # a stretcher along each side, on the outside of the legs
    zs = 0.26
    for sy in (-1, 1):
        rot = Matrix.Rotation(-sy * lean, 4, 'X')
        y = sy * (y_at(zs) + a * math.cos(lean) * 0.5 + 0.022)
        K.bx((2 * leg_x + t + 0.12, 0.019, 0.07), (0, y, zs), pine[2], rot)
        for sx in (-1, 1):
            K.bx((0.002, 0.014, 0.062), (sx * (leg_x + t / 2 + 0.061), y, zs), end, rot)
            for dz in (-0.018, 0.018):
                K.tube((sx * leg_x, y + sy * 0.008, zs + dz), (sx * leg_x, y + sy * 0.013, zs + dz), 0.006, 0.006, screw, 6, None, screw)
    for x, sy in ((0.22, 1), (-0.3, -1), (0.05, -1)):                      # a few knots
        K.bx((0.03, 0.002, 0.022), (x, sy * (t / 2 + 0.0008), web_top - w * 0.5), knot)
    K.bx((0.04, 0.03, 0.002), (-0.18, 0.012, H + 0.0008), knot)
    return K.done('sawhorse')


def plastic():
    """Two moulded leg frames hinged under a top rail; a tray shelf holds them open."""
    K = props.Kit()
    yellow = mat('SawhorseYellow', (0.96, 0.74, 0.08), 0.5)
    pressed = mat('SawhorseYellowPressed', (0.82, 0.6, 0.05), 0.55)
    black = mat('SawhorseBlack', (0.07, 0.07, 0.08), 0.6)
    grey = mat('SawhorseGrip', (0.2, 0.2, 0.22), 0.7)
    steel = mat('HingePin', (0.6, 0.61, 0.63), 0.35)
    H, L = 0.76, 0.68
    lean = math.radians(15)
    hinge_z = H - 0.075
    run = hinge_z / math.cos(lean)                                          # the length of a leg frame, hinge to floor
    for sy in (-1, 1):
        F = T((0, sy * 0.03, hinge_z)) @ Matrix.Rotation(sy * lean, 4, 'X')  # a frame hangs from its hinge, leaning out
        place = lambda size, x, down, m, out=0.0: K.box(size, F @ T((x, sy * out, -down)), m)
        for sx in (-1, 1):
            place((0.075, 0.034, run - 0.02), sx * (L / 2 - 0.0375), (run - 0.02) / 2 + 0.01, yellow)                  # a leg
            place((0.04, 0.006, run * 0.34), sx * (L / 2 - 0.0375), run * 0.3, pressed, 0.018)                         # its pressed panels
            place((0.04, 0.006, run * 0.3), sx * (L / 2 - 0.0375), run * 0.7, pressed, 0.018)
            place((0.085, 0.045, 0.03), sx * (L / 2 - 0.0375), run - 0.012, black)                                    # the rubber foot
        place((L - 0.15, 0.03, 0.2), 0, 0.11, yellow)                                                               # the top panel
        place((L - 0.26, 0.006, 0.11), 0, 0.11, pressed, 0.016)
        for k in range(5):                                                                                          # ribs across it
            place((0.008, 0.01, 0.1), -0.16 + 0.08 * k, 0.11, yellow, 0.018)
        place((L - 0.15, 0.026, 0.05), 0, run * 0.52, yellow)                                                       # the middle rail
        place((L - 0.15, 0.022, 0.035), 0, run * 0.86, yellow)                                                      # the bottom rail
        for sx in (-1, 1):                                                                                          # a cord hook on each leg
            place((0.03, 0.02, 0.012), sx * (L / 2 + 0.012), run * 0.24, black)
            place((0.012, 0.02, 0.035), sx * (L / 2 + 0.021), run * 0.24 - 0.014, black)
    # the top rail: black, with two notches that take a 2x4 on edge and a grip strip
    K.bx((L + 0.06, 0.1, 0.03), (0, 0, hinge_z + 0.015), black)
    for x0, x1 in ((-L / 2 - 0.03, -0.25), (-0.21, 0.21), (0.25, L / 2 + 0.03)):
        K.bx((x1 - x0, 0.1, 0.045), ((x0 + x1) / 2, 0, hinge_z + 0.0525), black)
        K.bx((x1 - x0 - 0.02, 0.06, 0.004), ((x0 + x1) / 2, 0, H + 0.001), grey)
    K.tube((-L / 2 - 0.035, 0, hinge_z), (L / 2 + 0.035, 0, hinge_z), 0.009, 0.009, steel, 8, steel, steel)             # the hinge pin
    # the tray shelf
    zt = hinge_z - run * 0.52 * math.cos(lean)
    half = 0.03 + run * 0.52 * math.sin(lean) - 0.012
    K.bx((L - 0.17, half * 2, 0.012), (0, 0, zt), black)
    for sy in (-1, 1):
        K.bx((L - 0.17, 0.012, 0.03), (0, sy * (half - 0.006), zt + 0.015), black)
    for sx in (-1, 1):
        K.bx((0.012, half * 2, 0.03), (sx * (L / 2 - 0.091), 0, zt + 0.015), black)
    for k in range(4):
        K.bx((0.012, half * 2 - 0.03, 0.006), (-0.18 + 0.12 * k, 0, zt + 0.009), grey)
    return K.done('sawhorse')


def metal():
    """Steel tube legs under a channel rail, folding on bolted hinge brackets, held open by flat stays."""
    K = props.Kit()
    galv = mat('SawhorseSteel', (0.68, 0.7, 0.72), 0.35)
    dark = mat('SawhorseBracket', (0.36, 0.37, 0.39), 0.45)
    rail = mat('SawhorseRail', (0.14, 0.27, 0.5), 0.45)
    black = mat('SawhorseRubber', (0.06, 0.06, 0.07), 0.7)
    tag = mat('SawhorseTag', (0.95, 0.8, 0.12), 0.6)
    H, L = 0.76, 0.95
    r = 0.017
    lean = math.radians(16)
    top = H - 0.05
    leg_x = L / 2 - 0.12
    y_at = lambda z: 0.022 + (top - z) * math.tan(lean)
    # the rail: a channel, open underneath, painted; a wear strip on top
    K.bx((L, 0.07, 0.006), (0, 0, H - 0.003), rail)
    for sy in (-1, 1):
        K.bx((L, 0.006, 0.05), (0, sy * 0.032, H - 0.025), rail)
    for sx in (-1, 1):
        K.bx((0.006, 0.07, 0.05), (sx * (L / 2 - 0.003), 0, H - 0.025), rail)
    K.bx((0.09, 0.002, 0.03), (0.22, -0.0355, H - 0.026), tag)
    for sx in (-1, 1):
        # the hinge bracket: two plates down from the rail, a bolt through each leg top
        for sy in (-1, 1):
            K.bx((0.09, 0.005, 0.085), (sx * leg_x, sy * 0.04, top - 0.01), dark)
        K.tube((sx * leg_x, -0.05, top - 0.02), (sx * leg_x, 0.05, top - 0.02), 0.006, 0.006, dark, 6, dark, dark)
        for sy in (-1, 1):
            K.lathe([(0.011, 0.0), (0.011, 0.007), (0.0, 0.007)], dark, 6, T((sx * leg_x, sy * 0.043, top - 0.02)) @ Matrix.Rotation(-sy * math.pi / 2, 4, 'X'))
            # the leg, its rubber foot
            p_top = Vector((sx * leg_x, sy * y_at(top), top))
            p_bot = Vector((sx * leg_x, sy * y_at(0.03), 0.03))
            K.tube(p_bot, p_top, r, r, galv, 10, None, galv)
            K.tube((p_bot.x, sy * y_at(0.0), 0.0), p_bot + Vector((0, -sy * 0.006, 0.03)), r * 1.5, r * 1.25, black, 10, black, black)
        # the stays: two flat bars from each leg to a pin in the middle, a little below level when locked
        zs = 0.36
        for sy in (-1, 1):
            a, b = Vector((sx * leg_x + sx * 0.02, sy * y_at(zs), zs)), Vector((sx * leg_x + sx * 0.02, 0, zs - 0.035))
            d = b - a
            K.box((0.004, d.length + 0.02, 0.02), T((a + b) / 2) @ Matrix.Rotation(math.atan2(d.z, d.y), 4, 'X'), dark)
            K.tube((sx * leg_x, sy * y_at(zs), zs), (sx * leg_x + sx * 0.028, sy * y_at(zs), zs), 0.005, 0.005, dark, 6, dark, dark)
        K.tube((sx * leg_x + sx * 0.012, 0, zs - 0.035), (sx * leg_x + sx * 0.03, 0, zs - 0.035), 0.006, 0.006, galv, 6, galv, galv)
    for sy in (-1, 1):                                                       # a tube along each side joins the pair of legs, and one low down
        for z in (top - 0.16, 0.2):
            K.tube((-leg_x, sy * y_at(z), z), (leg_x, sy * y_at(z), z), r * 0.85, r * 0.85, galv, 8)
    return K.done('sawhorse')


# id: (builder, name, description, weight kg, price, what the model is)
SAWHORSES = {
    'tool_sawhorse_wood': (wood, 'Wooden Sawhorse', 'A carpenter\'s sawhorse built from pine 2x4s with plywood gussets. Sturdy, heavy, and does not fold.', 9.0, 18,
                           'A capped 2x4 beam on four splayed legs, plywood gussets, side stretchers, screws.'),
    'tool_sawhorse_plastic': (plastic, 'Plastic Sawhorse', 'A folding moulded plastic sawhorse with a tray shelf and notches in the top rail that hold a 2x4 on edge. Light and quick to set up.', 4.0, 28,
                              'Two yellow leg frames hinged under a black notched rail, a tray shelf, rubber feet.'),
    'tool_sawhorse_metal': (metal, 'Metal Sawhorse', 'A folding steel sawhorse with tube legs, a channel top rail and locking stays. Carries the heaviest loads.', 7.5, 42,
                            'Galvanized tube legs on bolted hinge brackets under a painted channel rail, folding stays, rubber feet.'),
}


def main():
    for item, (build, name, desc, kg, price, note) in SAWHORSES.items():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obj = build()
        folder = os.path.join(TOOLS, item)
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
            m = json.load(open(os.path.join(TOOLS, 'tool_cement_mixer', 'tool_cement_mixer.json'), encoding='utf-8'))
            m.update({'id': item, 'name': name, 'description': desc, 'icon': item + '.png'})
            p = m['properties']
            p.update({'weight_kg': kg, 'base_value': price, 'max_stack_size': 1, 'placeable': True})
            p.pop('build_speed', None)
            none = lambda what: {'metric': what, 'details': what}
            m['utilities']['electricity'] = none('None (unpowered)')
            m['category_fields'] = {'fuel_type': 'none', 'fuel_consumption_l_per_min': 0, 'power_draw_w': 0, 'tank_capacity_l': 0}
        m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
        m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
        props.save(path, json.dumps(m, indent=2))
        props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_sawhorses.py), %d triangles, %.2f x %.2f x %.2f m. %s\n'
                   % (m['name'], m['description'], tris, *dims, note))
        print('sawhorse', item, '|', tris, 'tris |', dims)


if __name__ == '__main__':
    main()
