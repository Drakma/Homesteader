"""blender --background --python tools/preview_glb.py -- <glb> <out.png> [top] [noroof]
A quick 900 px look at a stage model: an isometric view, or straight down ("top") with the roof and walls facing the camera hidden."""
import math
import sys

import bpy

argv = sys.argv[sys.argv.index('--') + 1:]
glb, out = argv[0], argv[1]
top = 'top' in argv
noroof = 'noroof' in argv or top
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
if noroof:
    for o in objs:
        if o.name.startswith('Roof'):
            o.hide_render = True
mn = [min(v[i] for o in objs for v in (o.matrix_world @ __import__('mathutils').Vector(c) for c in o.bound_box)) for i in range(3)]
mx = [max(v[i] for o in objs for v in (o.matrix_world @ __import__('mathutils').Vector(c) for c in o.bound_box)) for i in range(3)]
ctr = [(a + b) / 2 for a, b in zip(mn, mx)]
size = max(b - a for a, b in zip(mn, mx))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
bpy.context.collection.objects.link(cam)
cam.data.type = 'ORTHO'
cam.data.ortho_scale = size * 1.25
if top:
    cam.location = (ctr[0], ctr[1], ctr[2] + size * 3)
    cam.rotation_euler = (0, 0, 0)
else:
    d = size * 3
    cam.location = (ctr[0] + d * 0.6, ctr[1] - d * 0.7, ctr[2] + d * 0.55)
    direction = __import__('mathutils').Vector(ctr) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
sun.data.energy = 3.5
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))
bpy.context.collection.objects.link(sun)
w = bpy.data.worlds.new('w'); w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.75, 0.82, 0.9, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
bpy.context.scene.world = w
s = bpy.context.scene
s.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
s.render.resolution_x = s.render.resolution_y = 900
s.render.filepath = out
bpy.ops.render.render(write_still=True)
