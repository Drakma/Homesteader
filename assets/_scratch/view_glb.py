"""blender --background --python view_glb.py -- model.glb out.png azimuth_deg elevation_deg [hide_roof]"""
import math
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
glb, out, az, el = argv[0], argv[1], float(argv[2]), float(argv[3])
hide_list = argv[4].split(',') if len(argv) > 4 else []
hide = False
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
mn = Vector((1e9, 1e9, 1e9))
mx = Vector((-1e9, -1e9, -1e9))
for o in bpy.data.objects:
    if o.type == 'MESH':
        if any(o.name.startswith(h) or (h == 'hide_roof' and o.name.startswith(('Roof', 'Porch'))) for h in hide_list):
            o.hide_render = True
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mn = Vector((min(mn[i], w[i]) for i in range(3)))
            mx = Vector((max(mx[i], w[i]) for i in range(3)))
center = (mn + mx) / 2
size = max((mx - mn).length, 1.0)
cam_d = bpy.data.cameras.new('c')
cam_d.type = 'ORTHO'
cam_d.ortho_scale = size * 0.85
cam = bpy.data.objects.new('c', cam_d)
bpy.context.collection.objects.link(cam)
a, e = math.radians(az), math.radians(el)
cam.location = center + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * size * 2
direction = center - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam
sun = bpy.data.lights.new('s', 'SUN')
sun.energy = 3.0
so = bpy.data.objects.new('s', sun)
so.rotation_euler = (math.radians(50), 0, math.radians(30))
bpy.context.collection.objects.link(so)
bpy.context.scene.world = bpy.data.worlds.new('w')
bpy.context.scene.world.use_nodes = True
bpy.context.scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.7, 0.8, 0.9, 1)
bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 1000
bpy.context.scene.render.resolution_y = 700
bpy.context.scene.render.filepath = out
bpy.ops.render.render(write_still=True)
