"""blender --background --python tools/scale_wheelbarrows.py
Scales the three wheelbarrow GLBs to a real size (1.45 m long), drops the pivot to the ground (lowest point at Y = 0, centred on X/Z) and re-exports
the GLB. The originals (GLB + FBX) are kept in assets/_originals/wheelbarrows/."""
import bpy, os, shutil, mathutils

ROOT = r'C:\Users\casey\Desktop\Homesteader'
LENGTH = 1.45
TEX = 1024
NAMES = {'tool_wheelbarrow': 'SM_Tool_Wheelbarrow', 'tool_plastic_wheelbarrow': 'SM_Tool_Plastic_Wheelbarrow', 'tool_steel_wheelbarrow': 'SM_Tool_Steel_Wheelbarrow'}
for item, stem in NAMES.items():
    d = os.path.join(ROOT, 'assets', 'tools', item)
    glb = os.path.join(d, stem + '.glb')
    keep = os.path.join(ROOT, 'assets', '_originals', 'wheelbarrows', item)
    os.makedirs(keep, exist_ok=True)
    for f in (stem + '.glb', stem + '.fbx', stem + '_base_color.png'):
        if os.path.exists(os.path.join(d, f)) and not os.path.exists(os.path.join(keep, f)):
            shutil.copy2(os.path.join(d, f), os.path.join(keep, f))
    src = os.path.join(keep, stem + '.glb')            # always work from the untouched original
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    root = bpy.data.objects.new('root', None)
    bpy.context.scene.collection.objects.link(root)
    for o in bpy.context.scene.objects:
        if o is not root and o.parent is None:
            o.parent = root
    bpy.context.view_layer.update()

    def bounds():
        mn = mathutils.Vector((1e9,) * 3); mx = mathutils.Vector((-1e9,) * 3)
        for o in meshes:
            for c in o.bound_box:
                w = o.matrix_world @ mathutils.Vector(c)
                mn = mathutils.Vector((min(mn.x, w.x), min(mn.y, w.y), min(mn.z, w.z)))
                mx = mathutils.Vector((max(mx.x, w.x), max(mx.y, w.y), max(mx.z, w.z)))
        return mn, mx
    mn, mx = bounds()
    s = LENGTH / (mx.x - mn.x)
    root.scale = (s, s, s)
    bpy.context.view_layer.update()
    mn, mx = bounds()
    root.location = (-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z)   # Blender Z is up (glTF Y)
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.context.scene.objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for img in bpy.data.images:
        if img.size[0] > TEX:                       # the Meshy texture is 4096 x 4096 (7 MB): 1024 is plenty for a wheelbarrow
            img.scale(TEX, TEX)
    bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', use_selection=False, export_image_format='JPEG', export_jpeg_quality=88)
    mn, mx = bounds()
    print('DONE', item, 'scale %.3f' % s, 'size', tuple(round(v, 3) for v in (mx - mn)))
