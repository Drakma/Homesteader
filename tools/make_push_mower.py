"""
Builds the PUSH MOWER (docs/MOWING.md) as a GLB in headless Blender (free, local, low-poly) and writes its manifest:

    blender --background --python tools/make_push_mower.py
    python tools/render_icon_from_model.py assets/tools/tool_push_mower/tool_push_mower.glb assets/tools/tool_push_mower/tool_push_mower.png
Afterwards: python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py

A red walk-behind mower with a 53 cm deck (properties.mower_width_m), four wheels, a small engine on top and a bent handle with a bar. Pushed like a wheelbarrow
(properties.pushable): the deck is the middle, the handles are at -x, the front at +x, the bottom at z = 0.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_simple_props as props  # noqa: E402

OUT = os.path.join(props.ROOT, 'assets', 'tools', 'tool_push_mower')
T = Matrix.Translation
mat = props.mat
ITEM = 'tool_push_mower'
WIDTH = 0.53


def build():
    K = props.Kit()
    red = mat('MowerDeck', (0.72, 0.08, 0.06), 0.4)
    black = mat('MowerBlack', (0.07, 0.07, 0.08), 0.6)
    grey = mat('MowerSteel', (0.5, 0.52, 0.55), 0.4)
    rubber = mat('MowerTyre', (0.04, 0.04, 0.045), 0.8)
    hub = mat('MowerHub', (0.75, 0.76, 0.78), 0.4)
    L, W = 0.62, WIDTH
    K.bx((L, W, 0.04), (0, 0, 0.17), red)                                   # the deck top
    for sy in (-1, 1):
        K.bx((L, 0.03, 0.12), (0, sy * (W / 2 - 0.015), 0.12), red)          # the deck sides, skirt down to 6 cm
    K.bx((0.03, W, 0.12), (L / 2 - 0.015, 0, 0.12), red)                    # the front skirt
    K.bx((0.03, W, 0.12), (-L / 2 + 0.015, 0, 0.12), red)                   # the rear skirt
    K.bx((0.2, 0.22, 0.02), (L / 2 - 0.04, 0, 0.19), black)                 # the discharge flap
    K.bx((0.26, 0.26, 0.14), (0.02, 0, 0.26), black)                        # the engine block
    K.lathe([(0.0, 0.0), (0.07, 0.0), (0.07, 0.05), (0.0, 0.05)], red, matrix=T((0.02, 0, 0.33)), seg=12)   # the engine cover
    K.lathe([(0.0, 0.0), (0.025, 0.0), (0.025, 0.03), (0.0, 0.03)], black, matrix=T((0.09, 0.08, 0.33)), seg=8)   # the fuel cap
    wr = 0.09
    for sx, r in ((1, 0.075), (-1, 0.09)):                                  # small wheels in front, bigger at the back
        for sy in (-1, 1):
            at = ((L / 2 - 0.06) if sx > 0 else (-L / 2 + 0.05), sy * (W / 2 + 0.02), r)
            m = props.RY @ Matrix.Identity(4)
            K.lathe([(0.0, -0.025), (r, -0.025), (r, 0.025), (0.0, 0.025)], rubber, matrix=T(at) @ m, seg=14)
            K.lathe([(0.0, -0.03), (r * 0.5, -0.03), (r * 0.5, 0.03), (0.0, 0.03)], hub, matrix=T(at) @ m, seg=10)
    for sy in (-1, 1):                                                       # the handle: up and back from the rear of the deck, then a bar across
        K.tube((-L / 2 + 0.05, sy * 0.2, 0.2), (-L / 2 - 0.42, sy * 0.21, 0.95), 0.014, 0.014, grey, sides=8)
    K.tube((-L / 2 - 0.42, -0.23, 0.95), (-L / 2 - 0.42, 0.23, 0.95), 0.016, 0.016, black, sides=8)
    K.bx((0.04, 0.12, 0.03), (-L / 2 - 0.4, 0.12, 0.9), grey)                # the bail bar bracket
    # more detail: a rear grass bag, deck rim and bolts, engine vents and recoil starter, wheel tread, handle grips, control bail, height lever
    bag = mat('GrassBag', (0.16, 0.2, 0.17), 0.8)
    K.bx((0.3, 0.3, 0.22), (-L / 2 - 0.12, 0, 0.33), bag)                                      # the grass bag on the back
    K.bx((0.32, 0.32, 0.03), (-L / 2 - 0.12, 0, 0.45), black)                                  # its frame top
    K.bx((0.05, 0.22, 0.05), (-L / 2 - 0.01, 0, 0.2), black)                                   # its chute
    for sy in (-1, 1):
        K.bx((L + 0.02, 0.02, 0.025), (0, sy * (W / 2 + 0.005), 0.065), black)                   # the rubber deck rim
        K.bx((0.05, 0.06, 0.02), (L / 2 - 0.1, sy * 0.1, 0.195), grey)                           # deck bolts
        K.bx((0.05, 0.06, 0.02), (-L / 2 + 0.1, sy * 0.1, 0.195), grey)
        K.bx((0.012, 0.035, 0.03), (-L / 2 - 0.42, sy * 0.2, 0.95), black)                       # the handle grips
        K.tube((-L / 2 - 0.42, sy * 0.15, 0.95), (-L / 2 - 0.42, sy * 0.23, 0.95), 0.022, 0.022, black, sides=8)
        K.bx((0.012, 0.04, 0.05), (-0.1, sy * 0.15, 0.32), grey)                                 # the engine cooling vents
    for i in range(4):
        K.bx((0.012, 0.2, 0.012), (0.0 + i * 0.05 - 0.07, 0, 0.335), black)                      # slots across the engine cover
    K.lathe([(0.0, 0.0), (0.045, 0.0), (0.045, 0.035), (0.0, 0.035)], black, matrix=T((-0.06, 0, 0.38)), seg=10)   # the recoil starter housing
    K.tube((-0.06, 0, 0.4), (-0.2, 0, 0.72), 0.006, 0.006, black, sides=5)                       # the starter cord
    K.bx((0.025, 0.07, 0.025), (-0.2, 0, 0.73), red)                                             # its pull handle
    K.tube((-L / 2 - 0.4, -0.2, 0.9), (-L / 2 - 0.2, -0.2, 0.62), 0.008, 0.008, grey, sides=5)   # the control bail cable guide
    K.tube((-L / 2 - 0.4, 0.21, 0.88), (-L / 2 - 0.4, -0.21, 0.88), 0.01, 0.01, grey, sides=6)   # the control bail bar
    K.bx((0.03, 0.02, 0.07), (0.1, W / 2 + 0.01, 0.12), black)                                   # the cutting height lever
    for sx, r in ((1, 0.075), (-1, 0.09)):
        for sy in (-1, 1):
            x = (L / 2 - 0.06) if sx > 0 else (-L / 2 + 0.05)
            for k in range(8):                                                                   # tread blocks round each tyre
                a = k * math.pi / 4
                K.bx((0.02, 0.05, 0.02), (x + math.cos(a) * r, sy * (W / 2 + 0.02), r + math.sin(a) * r), rubber, rot=Matrix.Rotation(-a, 4, 'Y'))
    return K.done(ITEM)


def main():
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj = build()
    pts = [v.co for v in obj.data.vertices]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    obj.data.transform(T((0, -(lo[1] + hi[1]) / 2, -lo[2])))   # the deck stays at the origin in x (handles at -x); centred on y; the bottom at z = 0
    dims = [round(hi[i] - lo[i], 3) for i in range(3)]
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, ITEM + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
    base = json.load(open(os.path.join(props.ROOT, 'assets', 'tools', 'tool_shovel_trenching', 'tool_shovel_trenching.json'), encoding='utf-8'))
    m = json.loads(json.dumps(base))
    desc = ('A walk-behind push mower with a 53 cm cutting deck. Push it over open ground (right click the handles with an empty hand, right click again to let go) and the grass under the deck is cut '
            'into a fresh lawn with light and dark stripes that run the way you walked. It does not cut farmland, roads or water.')
    m['id'], m['name'], m['description'], m['icon'] = ITEM, 'Push Mower', desc, ITEM + '.png'
    p = m['properties']
    p.update({'weight_kg': 32.0, 'base_value': 340, 'max_stack_size': 1, 'placeable': True, 'pushable': True, 'mower_width_m': WIDTH,
              'footprint': '%.2fm W x %.2fm D x %.2fm H' % (dims[1], dims[0], dims[2]), 'stores': ['depot'], 'sale_unit': 'ea', 'store_category': 'Power Tools/Garden & Farm'})
    p.pop('build_speed', None)
    for k in ('container', 'dimensions'):
        m.pop(k, None)                                  # the shovel's (a bulk-scoop container, its obj size): a mower is not a container, and a leftover container block would override pushable
    m['category_fields']['dimensions_m'] = {'width': round(dims[1], 2), 'depth': round(dims[0], 2), 'height': round(dims[2], 2)}
    m['models'] = [{'file': ITEM + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
    props.save(os.path.join(OUT, ITEM + '.json'), json.dumps(m, indent=2))
    props.save(os.path.join(OUT, 'README.md'), '# Push Mower\n\n%s\n\nProcedural model (tools/make_push_mower.py), %d triangles, %.2f x %.2f x %.2f m. `pushable`, `mower_width_m` %.2f. See docs/MOWING.md.\n' % (desc, tris, dims[0], dims[1], dims[2], WIDTH))
    print('built', ITEM, '|', tris, 'tris |', dims)


if __name__ == '__main__':
    main()
