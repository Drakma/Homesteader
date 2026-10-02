"""
Builds the manual hand saw (assets/tools/tool_saw_hand): a steel blade with a toothed edge and a wooden handle, low-poly, in headless
Blender (free, no Meshy credits). Writes the GLB, the manifest and the README; render the icon afterwards:

    blender --background --python tools/make_hand_saw.py
    python tools/render_icon_from_model.py assets/tools/tool_saw_hand/tool_saw_hand.glb assets/tools/tool_saw_hand/tool_saw_hand.png

The saw lies along X (blade toward -X, handle toward +X), flat in the XZ plane, centred on its middle (handheld tools use a centred pivot).
"""
import json
import os

import bmesh
import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEM = 'tool_saw_hand'
FOLDER = os.path.join(ROOT, 'assets', 'tools', ITEM)

BLADE_LEN, BLADE_H_HANDLE, BLADE_H_TIP, THICK = 0.50, 0.11, 0.035, 0.012
HANDLE_LEN, HANDLE_H, HANDLE_T = 0.15, 0.13, 0.034
TEETH = 22


def mat(name, rgb, rough, metal):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    return m


def obj_from(name, bm, materials):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in materials:
        me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    return o


def box(bm, x0, x1, y0, y1, z0, z1, idx):
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r['verts']:
        v.co.x = x0 + (v.co.x + 0.5) * (x1 - x0)
        v.co.y = y0 + (v.co.y + 0.5) * (y1 - y0)
        v.co.z = z0 + (v.co.z + 0.5) * (z1 - z0)
    for f in bm.faces:
        if all(v in r['verts'] for v in f.verts):
            f.material_index = idx


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    steel = mat('SawSteel', (0.72, 0.74, 0.78), 0.35, 0.9)
    wood = mat('SawWood', (0.45, 0.28, 0.14), 0.8, 0.0)
    dark = mat('SawRivet', (0.2, 0.2, 0.22), 0.5, 0.8)

    # ---- the blade: a tapered plate in XZ (the toothed edge along the bottom), THICK in Y
    bm = bmesh.new()
    x_tip = -BLADE_LEN - HANDLE_LEN * 0.0
    pts_top = [(x_tip, 0.0, BLADE_H_TIP), (0.0, 0.0, BLADE_H_HANDLE)]
    # outline, going round: top edge tip -> handle, then the toothed bottom edge handle -> tip
    outline = [(pts_top[0][0], pts_top[0][2]), (pts_top[1][0], pts_top[1][2])]
    teeth = []
    for i in range(TEETH + 1):
        t = i / TEETH                           # 0 at the handle, 1 at the tip
        x = -t * BLADE_LEN
        z_base = 0.0
        teeth.append((x, z_base))
        if i < TEETH:
            teeth.append((x - BLADE_LEN / TEETH * 0.5, -0.012))   # a tooth point below the edge
    outline += teeth
    front = [bm.verts.new((x, -THICK / 2, z)) for x, z in outline]
    back = [bm.verts.new((x, THICK / 2, z)) for x, z in outline]
    bm.faces.new(front[::-1])
    bm.faces.new(back)
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((front[i], front[j], back[j], back[i]))
    blade = obj_from('Blade', bm, [steel])

    # ---- the handle: a wooden D (a grip with an open hand hole), at the +X end, joined to the blade by two rivets
    bm = bmesh.new()
    gx0, gx1 = 0.0, HANDLE_LEN
    top_z = BLADE_H_HANDLE - 0.01
    bot_z = top_z - HANDLE_H
    bar = 0.032
    box(bm, gx0, gx1, -HANDLE_T / 2, HANDLE_T / 2, top_z - bar, top_z, 0)             # top bar
    box(bm, gx0, gx1, -HANDLE_T / 2, HANDLE_T / 2, bot_z, bot_z + bar, 0)             # bottom bar
    box(bm, gx0, gx0 + bar, -HANDLE_T / 2, HANDLE_T / 2, bot_z, top_z, 0)             # the front post (against the blade)
    box(bm, gx1 - bar, gx1, -HANDLE_T / 2, HANDLE_T / 2, bot_z, top_z, 0)             # the back post
    handle = obj_from('Handle', bm, [wood])

    bm = bmesh.new()
    for x in (0.03, 0.11):
        box(bm, x - 0.008, x + 0.008, -HANDLE_T / 2 - 0.004, HANDLE_T / 2 + 0.004, top_z - 0.025, top_z - 0.009, 0)
    rivets = obj_from('Rivets', bm, [dark])

    # centre on the middle of the whole saw
    total_x0, total_x1 = -BLADE_LEN - BLADE_LEN / TEETH, HANDLE_LEN
    cx = (total_x0 + total_x1) / 2
    cz = ((bot_z) + BLADE_H_HANDLE) / 2
    for o in (blade, handle, rivets):
        o.location = (-cx, 0.0, -cz)
    bpy.ops.object.select_all(action='DESELECT')
    for o in (blade, handle, rivets):
        o.select_set(True)
    bpy.context.view_layer.objects.active = blade
    bpy.ops.object.join()
    saw = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True)
    saw.name = ITEM

    os.makedirs(FOLDER, exist_ok=True)
    out = os.path.join(FOLDER, ITEM + '.glb')
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_yup=True)
    tris = sum(len(p.vertices) - 2 for p in saw.data.polygons)
    print('model:', out, tris, 'tris')

    d = {
        '$schema': 'https://homesteader.game/schemas/item_v1.json',
        'id': ITEM,
        'name': 'Hand Saw',
        'category': 'tools',
        'description': 'A manual crosscut hand saw with a toothed steel blade and a wooden grip. Slow, but it needs no power.',
        'icon': ITEM + '.png',
        'properties': {
            'weight_kg': 0.5, 'max_stack_size': 1, 'base_value': 18, 'is_consumable': False, 'footprint': None,
            'happiness_modifier': 0, 'thirst_restore': 0, 'energy_restore': 0, 'stamina_restore': 0, 'wellness_modifier': 0,
            'is_buyable': True, 'stores': ['depot'], 'sale_unit': 'ea',
        },
        'models': [{'file': ITEM + '.glb', 'format': 'glb',
                    'dimensions_m': {'x': round(BLADE_LEN + HANDLE_LEN + 0.02, 2), 'y': round(BLADE_H_HANDLE + 0.02, 2), 'z': round(HANDLE_T, 3)},
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
        'category_fields': {
            'dimensions_m': {'width': 0.67, 'depth': 0.034, 'height': 0.13},
            'fuel_type': 'none', 'fuel_consumption_l_per_min': 0, 'power_draw_w': 0, 'tank_capacity_l': 0,
        },
    }
    json.dump(d, open(os.path.join(FOLDER, ITEM + '.json'), 'w', encoding='utf-8'), indent=2)
    with open(os.path.join(FOLDER, 'README.md'), 'w', encoding='utf-8') as f:
        f.write(f'''# Hand Saw (`{ITEM}`)

![Icon]({ITEM}.png)

## Overview
- **Category**: `tools`
- **Item Identifier**: `{ITEM}`
- **Weight**: 0.5 kg
- **Base Economic Value**: $18
- **Sold at**: Nail It (depot)

## Description
{d['description']}

It is an alternative to the circular saws in a construction stage's tool group (any one tool of the group is enough).

## Asset Files & Links
- **Plugin Manifest (JSON)**: [{ITEM}.json]({ITEM}.json)
- **Model (GLB, {tris} triangles)**: [{ITEM}.glb]({ITEM}.glb)
- **Icon (PNG)**: [{ITEM}.png]({ITEM}.png)
''')


main()
