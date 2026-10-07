import sys
import bpy
from mathutils import Vector
glb = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
dg = bpy.context.evaluated_depsgraph_get()
# glTF Y-up -> blender: x same, y = -gltf z, z = gltf y. Blender y: front -, back +. origin = footprint middle.
# The main wing's back wall is at blender y = AD/2 - mid, mid = (-4.5 + 14.5)/2 = 5 -> y = -0.5
for x in (-6.0, 0.5, 2.0, 4.0, 6.0, 7.0):
    for z in (1.0, 2.2):
        o = Vector((x, 3.0, z))
        hit, loc, nor, idx, ob, mat = bpy.context.scene.ray_cast(dg, o, Vector((0, -1, 0)), distance=12.0)
        print('x=%.1f z=%.1f from y=3 toward the main wing: %s' % (x, z, ('hit %s at y=%.2f' % (ob.name, loc.y)) if hit else 'open'))
