"""
Shrinks the textures of a GLB in headless Blender and re-exports it: every image is scaled so its longer side is `size` pixels and the GLB is written
with JPEG textures (no alpha is needed on these models). Geometry is untouched.

    blender --background --python tools/shrink_glb_textures.py -- <in.glb> <out.glb> <size> [jpeg_quality]
"""
import sys

import bpy

argv = sys.argv[sys.argv.index('--') + 1:]
src, dst, size = argv[0], argv[1], int(argv[2])
quality = int(argv[3]) if len(argv) > 3 else 85
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
for img in bpy.data.images:
    w, h = img.size
    if max(w, h) > size:
        k = size / float(max(w, h))
        img.scale(max(1, int(w * k)), max(1, int(h * k)))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', use_selection=False, export_yup=True,
                          export_image_format='JPEG', export_jpeg_quality=quality)
tris = sum(len(p.vertices) - 2 for o in bpy.context.scene.objects if o.type == 'MESH' for p in o.data.polygons)
print('SHRUNK', dst, 'tris', tris, [(i.size[0], i.size[1]) for i in bpy.data.images])
