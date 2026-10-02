"""
Builds the manure slurry tank asset (assets/waste/waste_tank_manure_slurry): a round concrete-and-steel slurry store, 5000 L,
as a low-poly GLB made in headless Blender (free, local, no Meshy credits), plus its manifest and README. The icon is
rendered from the model afterwards with tools/render_icon_from_model.py.

    blender --background --python tools/make_slurry_tank.py
    python tools/render_icon_from_model.py assets/waste/waste_tank_manure_slurry/waste_tank_manure_slurry.glb assets/waste/waste_tank_manure_slurry/waste_tank_manure_slurry.png
"""
import json
import math
import os

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEM = 'waste_tank_manure_slurry'
FOLDER = os.path.join(ROOT, 'assets', 'waste', ITEM)

RADIUS, HEIGHT = 1.25, 1.7          # metres: about 8.4 cubic metres inside; the item holds 5000 L
SIDES = 24


def material(name, rgb, rough=0.9, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    return m


def mesh_obj(name, verts, faces, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    for p in me.polygons:
        p.use_smooth = False
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    return o


def cylinder(name, r_bottom, r_top, z0, z1, mat, cap_top=True, cap_bottom=True, cx=0.0, cy=0.0, sides=SIDES):
    v, f = [], []
    for z, r in ((z0, r_bottom), (z1, r_top)):
        for i in range(sides):
            a = 2 * math.pi * i / sides
            v.append((cx + math.cos(a) * r, cy + math.sin(a) * r, z))
    for i in range(sides):
        j = (i + 1) % sides
        f.append((i, j, sides + j, sides + i))
    if cap_bottom:
        c = len(v)
        v.append((cx, cy, z0))
        f += [(c, j, i) for i, j in ((k, (k + 1) % sides) for k in range(sides))]
    if cap_top:
        c = len(v)
        v.append((cx, cy, z1))
        f += [(c, sides + i, sides + (i + 1) % sides) for i in range(sides)]
    return mesh_obj(name, v, f, mat)


def main():
    # start from an EMPTY scene: the default one has a 2 m cube, which used to end up in the export
    bpy.ops.wm.read_factory_settings(use_empty=True)
    concrete = material('Concrete', (0.58, 0.58, 0.55), 0.95)
    steel = material('Steel', (0.35, 0.37, 0.4), 0.45, 0.8)
    lid = material('Lid', (0.2, 0.28, 0.2), 0.8)
    parts = []
    # the round wall, resting on the ground
    parts.append(cylinder('Wall', RADIUS, RADIUS, 0.0, HEIGHT, concrete, cap_top=False))
    # a thick rim and a base plinth
    parts.append(cylinder('Rim', RADIUS + 0.06, RADIUS + 0.06, HEIGHT - 0.12, HEIGHT + 0.04, concrete))
    parts.append(cylinder('Plinth', RADIUS + 0.08, RADIUS + 0.08, 0.0, 0.14, concrete, cap_bottom=False))
    # two steel hoop bands
    for z in (0.55, 1.15):
        parts.append(cylinder(f'Band{z}', RADIUS + 0.03, RADIUS + 0.03, z, z + 0.08, steel, cap_top=False, cap_bottom=False))
    # the lid with a hatch and a pump stub
    parts.append(cylinder('Lid', RADIUS, RADIUS, HEIGHT + 0.04, HEIGHT + 0.12, lid, cap_bottom=False))
    parts.append(cylinder('Hatch', 0.32, 0.32, HEIGHT + 0.12, HEIGHT + 0.22, steel, sides=16))
    parts.append(cylinder('PumpStub', 0.09, 0.09, HEIGHT + 0.12, HEIGHT + 0.5, steel, cx=0.8, sides=10))
    # the outlet pipe low on the wall
    parts.append(cylinder('Outlet', 0.07, 0.07, 0.22, 0.36, steel, cx=RADIUS + 0.12, sides=10))

    for o in bpy.data.objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = ITEM

    os.makedirs(FOLDER, exist_ok=True)
    out = os.path.join(FOLDER, ITEM + '.glb')
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_yup=True)
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    print('model:', out, tris, 'tris')

    manifest_path = os.path.join(FOLDER, ITEM + '.json')
    d = {
        '$schema': 'https://homesteader.game/schemas/item_v1.json',
        'id': ITEM,
        'name': '5000L Manure Slurry Tank',
        'category': 'waste',
        'description': 'A round concrete slurry store with steel bands and a hatch. Holds liquid manure from the barn.',
        'icon': ITEM + '.png',
        'properties': {
            'weight_kg': 2400.0, 'max_stack_size': 1, 'base_value': 1800.0, 'is_consumable': False, 'footprint': None,
            'happiness_modifier': 0, 'thirst_restore': 0, 'energy_restore': 0, 'stamina_restore': 0, 'wellness_modifier': 0,
            'placeable': True,
        },
        'models': [{'file': ITEM + '.glb', 'format': 'glb',
                    'dimensions_m': {'x': round(2 * RADIUS + 0.4, 2), 'y': round(HEIGHT + 0.5, 2), 'z': round(2 * RADIUS + 0.4, 2)},
                    'triangles': tris}],
        'utilities': {
            'water': {'metric': 'None (unplumbed / dry)', 'details': 'None (unplumbed / dry)'},
            'electricity': {'metric': 'None (passive / unpowered)', 'details': 'None (passive / unpowered)'},
            'sewage': {'metric': 'None (no waste discharge)', 'details': 'None (no waste discharge)'},
            'battery': {'metric': 'None (no internal battery)', 'details': 'None (no internal battery)'},
            'internet': {'metric': 'None (offline / non-networked)', 'details': 'None (offline / non-networked)'},
        },
        'growth': {'is_growable': False, 'growth_type': None, 'species': None, 'max_age': None, 'time_unit': None,
                   'total_stages': 0, 'current_stage': None, 'stages': []},
        'plugin_metadata': {'version': '1.0.0', 'author': 'Homesteader Core', 'compatible_api': 'v1'},
        'category_fields': {'dimensions_m': {'width': round(2 * RADIUS + 0.4, 2), 'depth': round(2 * RADIUS + 0.4, 2), 'height': round(HEIGHT + 0.5, 2)}, 'power_draw_w': 0},
        'liquid_container': {'capacity_l': 5000, 'accepts': ['liquid_manure_slurry']},
    }
    json.dump(d, open(manifest_path, 'w', encoding='utf-8'), indent=2)

    with open(os.path.join(FOLDER, 'README.md'), 'w', encoding='utf-8') as f:
        f.write(f'''# 5000L Manure Slurry Tank (`{ITEM}`)

![Icon]({ITEM}.png)

## Overview
- **Category**: `waste`
- **Item Identifier**: `{ITEM}`
- **Weight**: 2400.0 kg (empty)
- **Liquid capacity**: 5000 L of manure slurry (`liquid_container`)
- **Placeable**: yes

## Description
{d['description']}

## Asset Files & Links
- **Plugin Manifest (JSON)**: [{ITEM}.json]({ITEM}.json)
- **Model (GLB, {tris} triangles)**: [{ITEM}.glb]({ITEM}.glb)
- **Icon (PNG)**: [{ITEM}.png]({ITEM}.png)
''')


main()
