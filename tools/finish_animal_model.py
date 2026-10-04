"""
Finishes a Meshy animal model in headless Blender: scale it to a realistic height, stand it on the ground (z = 0) centred on x / y, make sure it
faces -Y (the game's +z, a model's front), apply the transform and export a GLB with its texture embedded.

    blender --background --python tools/finish_animal_model.py -- <in.glb> <out.glb> <height_m> [flip]

`flip` turns it half a turn about the vertical axis (when the head is at +Y). Prints the triangle count and the final size.
"""
import math
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
src, dst, height = argv[0], argv[1], float(argv[2])
flip = 'flip' in argv

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for o in bpy.context.scene.objects:
    if o.type not in ('MESH',):
        bpy.data.objects.remove(o, do_unlink=True)


def bounds():
    mn = [min((o.matrix_world @ Vector(c))[i] for o in meshes for c in o.bound_box) for i in range(3)]
    mx = [max((o.matrix_world @ Vector(c))[i] for o in meshes for c in o.bound_box) for i in range(3)]
    return mn, mx


# one empty parent: scale / turn it, then apply
root = bpy.data.objects.new('AnimalRoot', None)
bpy.context.collection.objects.link(root)
for o in meshes:
    o.parent = root
bpy.context.view_layer.update()
mn, mx = bounds()
h0 = mx[2] - mn[2]
s = height / h0
root.scale = (s, s, s)
if flip:
    root.rotation_euler = (0, 0, math.pi)
bpy.context.view_layer.update()
mn, mx = bounds()
root.location = (-(mn[0] + mx[0]) / 2, -(mn[1] + mx[1]) / 2, -mn[2])
bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:
    o.select_set(True)
    o.hide_set(False)
bpy.context.view_layer.objects.active = meshes[0]
for o in meshes:
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.data.objects.remove(root, do_unlink=True)
mn, mx = bounds()
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', use_selection=True, export_yup=True)
tris = sum(len(p.vertices) - 2 for o in meshes for p in o.data.polygons)
print('FINISHED', dst, 'tris', tris, 'size', [round(b - a, 3) for a, b in zip(mn, mx)], 'min z', round(mn[2], 4))
