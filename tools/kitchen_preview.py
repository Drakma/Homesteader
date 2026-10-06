"""
A contact sheet of kitchen models, for judging them while they are built (headless Blender):

    blender --background --python tools/kitchen_preview.py -- out.png fridge_top:stainless range_oven:black ...

Each argument is <model function>:<finish>; they stand in a row, lit like the item icons (warm key, cool fill), seen from a 3/4 front-left view.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitchen_lib as L  # noqa: E402
import kitchen_models as M  # noqa: E402


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    out = argv[0]
    specs = argv[1:]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    fins = L.finishes()
    x = 0.0
    objs = []
    for spec in specs:
        name, _, fin = spec.partition(':')
        K = getattr(M, name)(M.CAB_KEYS.get(fin, fin) if name in M.CAB_MODELS else fins[fin or 'stainless'])
        o = K.build()
        lo, hi = L.bounds(o)
        o.location.x = x - lo.x
        x += (hi.x - lo.x) + 0.35
        objs.append(o)
        print(spec, 'tris', o['triangles'], 'size', round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2))
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = 1800, 700
    scene.render.film_transparent = False
    world = bpy.data.worlds.new('W')
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.58, 0.62, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
    floor = bpy.data.meshes.new('floor')
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=30)
    bm.to_mesh(floor)
    fo = bpy.data.objects.new('floor', floor)
    scene.collection.objects.link(fo)
    fm = bpy.data.materials.new('floor')
    fm.diffuse_color = (0.42, 0.40, 0.37, 1)
    fo.data.materials.append(fm)
    center = Vector((x / 2 - 0.35, 0.0, 0.7))
    cam = bpy.data.cameras.new('c')
    cam.type = 'ORTHO'
    cam.ortho_scale = max(3.4, x * 1.12)
    co = bpy.data.objects.new('c', cam)
    scene.collection.objects.link(co)
    scene.camera = co
    yaw, pitch, dist = math.radians(-25), math.radians(22), 14
    co.location = center + Vector((math.sin(yaw) * math.cos(pitch), -math.cos(yaw) * math.cos(pitch), math.sin(pitch))) * dist
    t = bpy.data.objects.new('t', None)
    t.location = center
    scene.collection.objects.link(t)
    tr = co.constraints.new('TRACK_TO')
    tr.target, tr.track_axis, tr.up_axis = t, 'TRACK_NEGATIVE_Z', 'UP_Y'
    for nm, energy, col, off in (('key', 4.2, (1.0, 0.95, 0.88), Vector((-6, -6, 9))), ('fill', 1.4, (0.85, 0.92, 1.0), Vector((7, -4, 4)))):
        ld = bpy.data.lights.new(nm, 'SUN')
        ld.energy = energy
        ld.color = col
        lo_ = bpy.data.objects.new(nm, ld)
        scene.collection.objects.link(lo_)
        lo_.location = center + off
        lt = lo_.constraints.new('TRACK_TO')
        lt.target, lt.track_axis, lt.up_axis = t, 'TRACK_NEGATIVE_Z', 'UP_Y'
    scene.render.filepath = out
    scene.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)


main()
