"""
Builds the pickup-zone flag (assets/building/building_pickup_flag) as a GLB in headless Blender: free, local, low-poly (no Meshy).

    blender --background --python tools/make_pickup_flag.py
    python tools/generate_unity_asset_catalog.py
    python tools/render_icon_from_model.py assets/building/building_pickup_flag/building_pickup_flag.glb assets/building/building_pickup_flag/building_pickup_flag.png

A steel pole driven into a small steel ground plate, a ball on top and an orange flag, in a few slightly waved panels. Planted in the yard it marks the corner of
the market pickup zone (Assets/Scripts/World/PickupFlag.cs, docs/MARKET.md).

Conventions: 1 unit = 1 m, pivot at the pole, ground at z = 0, the flag streams out along +x.
"""
import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_simple_props as props  # noqa: E402    (Kit, mat, save)

ITEM = 'building_pickup_flag'
FOLDER = os.path.join(props.ROOT, 'assets', 'building', ITEM)
mat = props.mat


def build():
    K = props.Kit()
    steel = mat('FlagPole', (0.62, 0.64, 0.67), 0.35)
    dark = mat('FlagBase', (0.25, 0.26, 0.28), 0.5)
    cloth = mat('FlagCloth', (0.95, 0.42, 0.06), 0.8)
    stripe = mat('FlagStripe', (0.98, 0.9, 0.82), 0.8)
    H = 2.4
    K.bx((0.3, 0.3, 0.012), (0, 0, 0.006), dark)                    # the ground plate
    K.tube((0, 0, 0.012), (0, 0, 0.1), 0.05, 0.026, dark, 8, dark)  # the collar it is driven through
    K.tube((0, 0, 0.0), (0, 0, H), 0.016, 0.016, steel, 8, steel)   # the pole
    K.lathe([(0.0, H), (0.03, H + 0.012), (0.034, H + 0.034), (0.026, H + 0.056), (0.0, H + 0.066)], steel, 8)   # the ball on top
    top, w, hgt, n = H - 0.06, 0.95, 0.62, 4
    for k in range(n):                                              # the flag, in panels that wave a little
        x0 = 0.02 + k * w / n
        y = 0.02 * (1 if k % 2 == 0 else -1) * (k / n + 0.25)
        K.bx((w / n, 0.006, hgt), (x0 + w / n / 2, y, top - hgt / 2), cloth if k != 2 else stripe)
    K.bx((0.02, 0.012, hgt + 0.02), (0.012, 0, top - hgt / 2), dark)   # the hem against the pole
    return K.done(ITEM)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj = build()
    os.makedirs(FOLDER, exist_ok=True)
    pts = [v.co for v in obj.data.vertices]
    dims = [round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)]
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=os.path.join(FOLDER, ITEM + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
    path = os.path.join(FOLDER, ITEM + '.json')
    if os.path.exists(path):
        m = json.load(open(path, encoding='utf-8'))
    else:
        m = json.load(open(os.path.join(props.ROOT, 'assets', 'building', 'lumber_post_4x4', 'lumber_post_4x4.json'), encoding='utf-8'))
        m.update({'id': ITEM, 'icon': ITEM + '.png', 'name': 'Pickup Flag',
                  'description': 'A flag on a steel pole. Plant it in the yard: it marks the corner of your market pickup zone, a 10 by 10 tile square reaching from the flag '
                                 'toward the road. Goods left inside it are what the Market app sells and where deliveries are dropped.'})
        p = m['properties']
        p.update({'weight_kg': 3.0, 'base_value': 15, 'max_stack_size': 1, 'placeable': True, 'sale_unit': 'each'})
        for k in ('stacking_limit', 'display_weight'):
            p.pop(k, None)
    m['properties']['footprint'] = '%.2fm W x %.2fm D x %.2fm H' % (dims[0], dims[1], dims[2])
    m['models'] = [{'file': ITEM + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
    m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
    props.save(path, json.dumps(m, indent=2))
    props.save(os.path.join(FOLDER, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_pickup_flag.py), %d triangles, %.2f x %.2f x %.2f m.\n' % (m['name'], m['description'], tris, *dims))
    print('flag', ITEM, '|', tris, 'tris |', dims)


if __name__ == '__main__':
    main()
