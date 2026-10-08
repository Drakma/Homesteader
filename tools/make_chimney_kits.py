"""
Builds the CHIMNEY KITS (assets/building/building_chimney_kit_*) as GLBs in headless Blender: free, local, low-poly (no Meshy), manifests and READMEs included.

    blender --background --python tools/make_chimney_kits.py
    python tools/render_icon_from_model.py assets/building/<id>/<id>.glb assets/building/<id>/<id>.png      (each)
    python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py

A kit is a small pallet of masonry (brick or fieldstone), a steel flue liner and a bag of mortar mix. It is not placed on the ground: with it in the active slot
(attach_surface "chimney") a left click on an OUTSIDE wall of a finished building, aimed at from outside or from inside, brings out the preview and a second click builds
the chimney there (Growth/Chimney.cs, docs/CHIMNEYS.md). Sold at the depot.

Conventions: 1 unit = 1 m, pivot at the centre of the footprint, ground at z = 0.
"""
import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_simple_props as props  # noqa: E402

BUILD = os.path.join(props.ROOT, 'assets', 'building')
mat = props.mat

KITS = {
    'building_chimney_kit_brick': dict(name='Brick Chimney Kit', kind='brick', rgb=(0.55, 0.22, 0.16), kg=420.0, price=1450,
                                       text='A pallet of face brick, a steel flue liner and a bag of mortar mix: everything for a brick chimney with a fireplace.'),
    'building_chimney_kit_stone': dict(name='Fieldstone Chimney Kit', kind='stone', rgb=(0.52, 0.5, 0.46), kg=520.0, price=1900,
                                       text='A pallet of split fieldstone, a steel flue liner and a bag of mortar mix: everything for a stone chimney with a fireplace.'),
}
USE = (' Hold it, click an outside wall of a finished building (from outside or from inside) and click again to build it: the stack stands outside and rises a metre past '
       'the roof, the mantel and firebox are inside. It cannot go on a window or a door.')


def build(item, spec):
    K = props.Kit()
    K.smooth = False
    wood = mat('PalletWood', (0.62, 0.48, 0.3), 0.9)
    unit = mat('Masonry_' + spec['kind'], spec['rgb'], 0.85)
    unit2 = mat('MasonryDark_' + spec['kind'], tuple(c * 0.82 for c in spec['rgb']), 0.85)
    steel = mat('FlueSteel', (0.62, 0.64, 0.67), 0.35)
    bag = mat('MortarBag', (0.82, 0.8, 0.74), 0.9)
    wrap = mat('StrapBand', (0.1, 0.1, 0.11), 0.6)
    W, D = 1.0, 0.8
    for x in (-0.4, 0.0, 0.4):                                             # the pallet: three bearers and the deck
        K.bx((0.09, D, 0.08), (x, 0, 0.04), wood)
    K.bx((W, D, 0.03), (0, 0, 0.095), wood)
    z0 = 0.11
    for bx in (-0.25, 0.25):                                               # the masonry: courses laid in a running bond
        for course in range(5):
            for k in range(3):
                shade = unit if (course + k) % 2 == 0 else unit2
                off = 0.0 if course % 2 == 0 else 0.04
                K.bx((0.14, 0.34, 0.07), (bx - 0.15 + k * 0.15 + off * 0.5, -0.18, z0 + 0.035 + course * 0.075), shade)
    for course in range(5):
        for k in range(3):
            shade = unit if (course + k) % 2 else unit2
            K.bx((0.14, 0.34, 0.07), (-0.15 + k * 0.15, 0.2, z0 + 0.035 + course * 0.075), shade)
    top = z0 + 5 * 0.075
    K.tube((-0.45, 0.0, top + 0.09), (0.45, 0.0, top + 0.09), 0.09, 0.09, steel, 14, steel, steel)   # the flue liner lying across the top
    K.bx((0.34, 0.2, 0.16), (0.28, -0.22, top + 0.08), bag)                                           # the bag of mortar mix
    for x in (-0.3, 0.3):                                                                             # a strap round the load
        K.bx((0.025, D + 0.01, 0.002), (x, 0, top + 0.002), wrap)
    return K.done(item)


def main():
    src = json.load(open(os.path.join(BUILD, 'building_pvc_cement_can', 'building_pvc_cement_can.json'), encoding='utf-8'))
    only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for item, spec in KITS.items():
        if only and item not in only:
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obj = build(item, spec)
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
        existed = os.path.exists(path)
        m = json.load(open(path, encoding='utf-8')) if existed else json.loads(json.dumps(src))
        if not existed:
            m.update({'id': item, 'name': spec['name'], 'category': 'building', 'description': spec['text'] + USE, 'icon': item + '.png'})
            m['properties'].update({'weight_kg': spec['kg'], 'base_value': spec['price'], 'max_stack_size': 1, 'stores': ['depot'], 'sale_unit': 'kit',
                                    'display_weight': True, 'is_buyable': True, 'footprint': '%.2fm W x %.2fm D x %.2fm H' % (dims[0], dims[1], dims[2])})
        m['properties'].update({'placeable': False, 'attach_surface': 'chimney'})
        m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
        m['category_fields'] = {'dimensions_m': {'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)}}
        props.save(path, json.dumps(m, indent=2))
        props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_chimney_kits.py), %d triangles, %.2f x %.2f x %.2f m.\n' % (m['name'], m['description'], tris, dims[0], dims[1], dims[2]))
        print('kit', item, '|', tris, 'tris |', dims)


if __name__ == '__main__':
    main()
