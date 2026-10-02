"""
Builds the generic delivery box van (assets/vehicles/vehicle_delivery_boxvan): a white cargo van with a cab, a box body, an
orange stripe, tail and head lights and four SEPARATE wheels (named Wheel_*, origin on the hub, so the game can spin them), plus
an empty named FrontMarker at the nose (the game reads it to learn which way the model faces). Low-poly, made in headless
Blender (free, no Meshy credits). Writes the GLB, the manifest and the README; render the icon afterwards:

    blender --background --python tools/make_boxvan.py
    python tools/render_icon_from_model.py assets/vehicles/vehicle_delivery_boxvan/vehicle_delivery_boxvan.glb assets/vehicles/vehicle_delivery_boxvan/vehicle_delivery_boxvan.png
"""
import json
import math
import os

import bmesh
import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEM = 'vehicle_delivery_boxvan'
FOLDER = os.path.join(ROOT, 'assets', 'vehicles', ITEM)

LENGTH, WIDTH, HEIGHT = 6.2, 2.2, 3.1
WHEEL_R, WHEEL_W = 0.42, 0.3
FRONT_AXLE_Y, REAR_AXLE_Y = 2.1, -1.9


def mat(name, rgb, rough=0.5, metal=0.0, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1.0)
        b.inputs['Emission Strength'].default_value = 1.5
    return m


def box(name, x0, x1, y0, y1, z0, z1, material, bevel=0.0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = x0 + (v.co.x + 0.5) * (x1 - x0)
        v.co.y = y0 + (v.co.y + 0.5) * (y1 - y0)
        v.co.z = z0 + (v.co.z + 0.5) * (z1 - z0)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=1, affect='EDGES')
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    return o


def prism(name, profile_yz, x0, x1, material):
    """A side profile (y, z points, in order) extruded across x0..x1."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    left = [bm.verts.new((x0, y, z)) for y, z in profile_yz]
    right = [bm.verts.new((x1, y, z)) for y, z in profile_yz]
    bm.faces.new(left[::-1])
    bm.faces.new(right)
    n = len(profile_yz)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((left[i], left[j], right[j], right[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    return o


def wheel(name, x, y, tire, rim):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    sides = 14
    for side, (xs, m) in enumerate(((-WHEEL_W / 2, 0), (WHEEL_W / 2, 0))):
        pass
    ring_a, ring_b = [], []
    for i in range(sides):
        a = 2 * math.pi * i / sides
        ring_a.append(bm.verts.new((-WHEEL_W / 2, math.cos(a) * WHEEL_R, math.sin(a) * WHEEL_R)))
        ring_b.append(bm.verts.new((WHEEL_W / 2, math.cos(a) * WHEEL_R, math.sin(a) * WHEEL_R)))
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((ring_a[i], ring_a[j], ring_b[j], ring_b[i]))
    outer = bm.faces.new(ring_b)
    inner = bm.faces.new(ring_a[::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    # a smaller hub cap on each side, as the rim colour
    for f in bm.faces:
        f.material_index = 0
    bm.to_mesh(me)
    bm.free()
    me.materials.append(tire)
    o = bpy.data.objects.new(name, me)
    o.location = (x, y, WHEEL_R)   # origin = the hub
    bpy.context.collection.objects.link(o)
    hub = box(name + '_hub', -WHEEL_W / 2 - 0.01, WHEEL_W / 2 + 0.01, -0.12, 0.12, -0.12, 0.12, rim)
    hub.parent = o
    return o, hub


def main():
    # start from an EMPTY scene: the default one has a 2 m cube, which used to end up in the export
    bpy.ops.wm.read_factory_settings(use_empty=True)
    white = mat('VanWhite', (0.93, 0.94, 0.95), 0.45)
    cream = mat('VanCab', (0.88, 0.9, 0.92), 0.45)
    dark = mat('VanDark', (0.16, 0.17, 0.19), 0.7, 0.3)
    glass = mat('VanGlass', (0.1, 0.16, 0.22), 0.1, 0.0)
    stripe = mat('VanStripe', (0.88, 0.5, 0.18), 0.5)
    tire = mat('VanTire', (0.06, 0.06, 0.07), 0.9)
    rim = mat('VanRim', (0.7, 0.72, 0.75), 0.4, 0.8)
    red = mat('VanTail', (0.8, 0.08, 0.06), 0.4, 0.0, (0.8, 0.05, 0.03))
    yellow = mat('VanHead', (1.0, 0.92, 0.6), 0.3, 0.0, (1.0, 0.9, 0.5))

    parts = []
    hw = WIDTH / 2
    parts.append(box('Chassis', -hw + 0.12, hw - 0.12, -3.0, 3.05, 0.45, 0.85, dark))
    parts.append(box('CargoBox', -hw, hw, -3.1, 1.15, 0.8, HEIGHT, white, bevel=0.05))
    parts.append(box('Stripe', -hw - 0.01, hw + 0.01, -3.0, 1.1, 1.35, 1.75, stripe))
    cab = [(1.2, 0.8), (3.05, 0.8), (3.05, 1.45), (2.55, 2.25), (1.2, 2.25)]
    parts.append(prism('Cab', cab, -hw + 0.04, hw - 0.04, cream))
    # side windows and the windscreen
    parts.append(box('SideGlassL', -hw + 0.02, -hw + 0.07, 1.55, 2.45, 1.35, 2.05, glass))
    parts.append(box('SideGlassR', hw - 0.07, hw - 0.02, 1.55, 2.45, 1.35, 2.05, glass))
    parts.append(prism('Windscreen', [(2.58, 1.5), (2.97, 1.5), (2.57, 2.17), (2.48, 2.17)], -hw + 0.18, hw - 0.18, glass))
    # bumpers, grille, lights
    parts.append(box('FrontBumper', -hw + 0.05, hw - 0.05, 3.0, 3.2, 0.5, 0.95, dark))
    parts.append(box('RearBumper', -hw + 0.05, hw - 0.05, -3.25, -3.05, 0.5, 0.95, dark))
    parts.append(box('HeadL', -hw + 0.2, -hw + 0.55, 3.04, 3.12, 1.0, 1.25, yellow))
    parts.append(box('HeadR', hw - 0.55, hw - 0.2, 3.04, 3.12, 1.0, 1.25, yellow))
    parts.append(box('TailL', -hw + 0.1, -hw + 0.3, -3.16, -3.1, 0.95, 1.5, red))
    parts.append(box('TailR', hw - 0.3, hw - 0.1, -3.16, -3.1, 0.95, 1.5, red))
    # mirrors
    parts.append(box('MirrorL', -hw - 0.18, -hw + 0.02, 2.5, 2.62, 1.55, 1.95, dark))
    parts.append(box('MirrorR', hw - 0.02, hw + 0.18, 2.5, 2.62, 1.55, 1.95, dark))
    # roll-up door seam on the back
    parts.append(box('RearSeam', -hw + 0.15, hw - 0.15, -3.115, -3.1, 1.0, HEIGHT - 0.2, dark))

    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    body = bpy.context.view_layer.objects.active
    body.name = 'Body'

    wheels = []
    for nm, x, y in (('Wheel_FL', -hw + 0.15, FRONT_AXLE_Y), ('Wheel_FR', hw - 0.15, FRONT_AXLE_Y),
                     ('Wheel_RL', -hw + 0.15, REAR_AXLE_Y), ('Wheel_RR', hw - 0.15, REAR_AXLE_Y)):
        w, hub = wheel(nm, x, y, tire, rim)
        wheels.append(w)
        wheels.append(hub)

    marker = bpy.data.objects.new('FrontMarker', None)
    marker.location = (0.0, 3.2, 1.0)
    bpy.context.collection.objects.link(marker)

    # hub caps live under their wheels; join each pair so a wheel is ONE object (the hub is a child, kept as is)
    bpy.ops.object.select_all(action='SELECT')
    os.makedirs(FOLDER, exist_ok=True)
    out = os.path.join(FOLDER, ITEM + '.glb')
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_yup=True)
    tris = 0
    for o in bpy.data.objects:
        if o.type == 'MESH':
            tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
    print('model:', out, tris, 'tris')

    d = {
        '$schema': 'https://homesteader.game/schemas/item_v1.json',
        'id': ITEM,
        'name': 'Delivery Box Van',
        'category': 'vehicles',
        'description': 'A plain white cargo van with an orange stripe. It brings your orders down the road to the homestead the day after you place them.',
        'icon': ITEM + '.png',
        'properties': {
            'weight_kg': 3500.0, 'max_stack_size': 1, 'base_value': 38000.0, 'is_consumable': False, 'footprint': None,
            'happiness_modifier': 0, 'thirst_restore': 0, 'energy_restore': 0, 'stamina_restore': 0, 'wellness_modifier': 0,
            'placeable': False,
        },
        'models': [{'file': ITEM + '.glb', 'format': 'glb',
                    'dimensions_m': {'x': WIDTH, 'y': HEIGHT, 'z': 6.4}, 'triangles': tris}],
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
            'dimensions_m': {'width': WIDTH, 'depth': 6.4, 'height': HEIGHT},
            'vehicle_type': 'van', 'fuel_type': 'diesel', 'fuel_consumption_l_per_min': 0.1, 'tank_capacity_l': 90,
            'top_speed_kmh': 110, 'seats': 2, 'cargo_capacity_m3': 11,
        },
    }
    json.dump(d, open(os.path.join(FOLDER, ITEM + '.json'), 'w', encoding='utf-8'), indent=2)
    with open(os.path.join(FOLDER, 'README.md'), 'w', encoding='utf-8') as f:
        f.write(f'''# Delivery Box Van (`{ITEM}`)

![Icon]({ITEM}.png)

## Overview
- **Category**: `vehicles`
- **Item Identifier**: `{ITEM}`
- **Placeable**: no (it drives itself: see `Assets/Scripts/World/DeliveryService.cs`)

## Description
{d['description']}

The model's four wheels are separate objects named `Wheel_FL`, `Wheel_FR`, `Wheel_RL`, `Wheel_RR` with their origin on the hub, so the game
spins them while it drives; an empty named `FrontMarker` sits at the nose so the game knows which way the model faces.

## Asset Files & Links
- **Plugin Manifest (JSON)**: [{ITEM}.json]({ITEM}.json)
- **Model (GLB, {tris} triangles)**: [{ITEM}.glb]({ITEM}.glb)
- **Icon (PNG)**: [{ITEM}.png]({ITEM}.png)
''')


main()
