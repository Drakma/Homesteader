"""
Builds the hanging grow lights as GLBs in headless Blender: free, local, low-poly (no Meshy).

    blender --background --python tools/make_grow_lights.py
    python tools/render_icon_from_model.py assets/building/<id>/<id>.glb assets/building/<id>/<id>.png

  building_light_grow_2bulb / _4bulb / _8bulb      "Small Grow Light", "Grow Light", "Large Grow Light"

The fluorescent ceiling fixtures' cousins (building_light_fluorescent_*, tools/make_attached_items.py): the same 1.2 m length and tube counts, but
a black finned aluminium housing with a white reflector, glowing magenta tubes, hung from two ceiling plates on four cables, a power cord up to
the ceiling. Their light is magenta-violet and steady (no start-up flicker).

A new item gets its manifest from the fluorescent fixture with the same number of tubes (so it mounts on a ceiling the same way and needs the
building's power); an item that is already in the kit keeps its name, price and the rest.

Convention for a ceiling item (docs/ATTACHED_ITEMS.md): it hangs from its TOP: z = 0 is its lowest point, its height is where it meets the
ceiling; centred on x and y; 1 unit = 1 m.
"""
import json
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_simple_props as props  # noqa: E402    (Kit, mat, save)

BUILD = os.path.join(props.ROOT, 'assets', 'building')
T = Matrix.Translation
mat = props.mat
LENGTH, PITCH, DROP = 1.2, 0.075, 0.3
COLOR = '#E070FF'

# tubes: (name, price, kg, the lights: (x, z) offsets across the fixture, intensity, range, watts each)
LIGHTS = {
    2: ('Small Grow Light', 60, 3.0, [(-0.3, 0.0), (0.3, 0.0)], 6.0, 12.0, 30),
    4: ('Grow Light', 110, 5.0, [(-0.3, 0.0), (0.3, 0.0)], 7.5, 16.0, 60),
    8: ('Large Grow Light', 200, 9.0, [(-0.3, -0.15), (0.3, -0.15), (-0.3, 0.15), (0.3, 0.15)], 7.5, 20.0, 60),
}


def build(n):
    K = props.Kit()
    black = mat('GrowHousing', (0.08, 0.08, 0.09), 0.5)
    fin = mat('GrowFins', (0.2, 0.2, 0.22), 0.4)
    white = mat('GrowReflector', (0.93, 0.94, 0.95), 0.35)
    grey = mat('GrowHolder', (0.5, 0.52, 0.55), 0.5)
    steel = mat('GrowCable', (0.7, 0.71, 0.73), 0.3)
    tube = mat('GrowTube', (1.0, 0.42, 0.92), 0.15)
    bsdf = tube.node_tree.nodes['Principled BSDF']                      # the tubes glow
    for key in ('Emission Color', 'Emission'):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = (1.0, 0.35, 0.9, 1.0)
            break
    if 'Emission Strength' in bsdf.inputs:
        bsdf.inputs['Emission Strength'].default_value = 2.5
    W = n * PITCH + 0.05
    zb, zt = 0.034, 0.075                                                # the housing sits over the tubes
    K.bx((LENGTH, W, zt - zb), (0, 0, (zb + zt) / 2), black)
    K.bx((LENGTH - 0.03, W - 0.02, 0.003), (0, 0, zb - 0.0015), white)                       # the reflector, under it
    for s in (-1, 1):                                                    # the reflector's wings, tilted down and out
        K.box((LENGTH, 0.045, 0.003), T((0, s * (W / 2 + 0.014), zb - 0.012)) @ Matrix.Rotation(-s * 0.55, 4, 'X'), white)
        K.bx((0.012, W, zt), (s * (LENGTH / 2 - 0.006), 0, zt / 2), black)                   # the end caps
    fins = max(4, int(W / 0.03))
    for k in range(fins):                                                # cooling fins along the top
        K.bx((LENGTH - 0.08, 0.004, 0.022), (0, -W / 2 + 0.02 + (W - 0.04) * k / (fins - 1), zt + 0.011), fin)
    for i in range(n):                                                   # the tubes and their holders
        y = (i - (n - 1) / 2.0) * PITCH
        K.tube((-LENGTH / 2 + 0.05, y, 0.0185), (LENGTH / 2 - 0.05, y, 0.0185), 0.0185, 0.0185, tube, 8, tube, tube)
        for x in (-LENGTH / 2 + 0.03, LENGTH / 2 - 0.03):
            K.bx((0.04, 0.04, 0.036), (x, y, 0.018), grey)
    # hung on four cables from two ceiling plates, and a power cord up to the ceiling
    for sx in (-1, 1):
        x = sx * LENGTH * 0.33
        K.bx((0.1, 0.06, 0.008), (x, 0, DROP - 0.004), fin)
        K.lathe([(0.012, DROP - 0.03), (0.012, DROP - 0.008)], steel, 6, T((x, 0, 0)))
        for sy in (-1, 1):
            K.tube((x, sy * (W / 2 - 0.02), zt + 0.02), (x, 0, DROP - 0.03), 0.0025, 0.0025, steel, 5)
            K.bx((0.016, 0.016, 0.012), (x, sy * (W / 2 - 0.02), zt + 0.006), steel)
    cx = LENGTH / 2 - 0.04
    K.path([(cx, 0, zt), (cx + 0.02, 0.02, zt + 0.07), (cx - 0.03, 0.03, DROP - 0.09), (cx - 0.06, 0, DROP)], 0.005, black, 6)
    K.lathe([(0.02, DROP - 0.012), (0.02, DROP)], black, 8, T((cx - 0.06, 0, 0)))
    return K.done('grow_light'), W


def main():
    for n, (name, price, kg, spots, intensity, rng, watts) in LIGHTS.items():
        item = 'building_light_grow_%dbulb' % n
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obj, W = build(n)
        obj.name = item
        folder = os.path.join(BUILD, item)
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
            src = 'building_light_fluorescent_%dbulb' % n
            m = json.load(open(os.path.join(BUILD, src, src + '.json'), encoding='utf-8'))
            m.update({'id': item, 'icon': item + '.png', 'name': name,
                      'description': 'A hanging grow light with %d magenta tubes under a finned black housing: a steady violet light for plants indoors. Mount it on a ceiling '
                                     'inside a building; it lights while the building has power (a breaker box on the outside).' % n})
            m['properties'].update({'weight_kg': kg, 'base_value': price})
            # the light hangs DROP below the ceiling, so its lamps are lower than a flush fixture's (offset: x along the fixture, y down, z across)
            m['lights'] = [{'id': 'tube%d' % (k + 1), 'color': COLOR, 'intensity': intensity, 'range_m': rng, 'offset_m': [x, -(DROP + 0.06), z], 'on': 'always',
                            'power_w': watts, 'type': 'point', 'shadows': False, 'requires_power': True} for k, (x, z) in enumerate(spots)]
        m['properties']['footprint'] = '%.2fm W x %.2fm D x %.2fm H' % (dims[0], dims[1], dims[2])
        m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
        m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': dims[0], 'depth': dims[1], 'height': dims[2]})
        props.save(path, json.dumps(m, indent=2))
        props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_grow_lights.py), %d triangles, %.2f x %.2f x %.2f m, %d tubes. Mounts on a '
                   'ceiling (interior side) and hangs %.2f m below it. See docs/ATTACHED_ITEMS.md.\n' % (m['name'], m['description'], tris, *dims, n, DROP))
        print('grow light', item, '|', m['name'], '|', tris, 'tris |', dims)


if __name__ == '__main__':
    main()
