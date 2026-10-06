"""
Builds a textured cardboard box GLB in headless Blender: ONE box mesh (12 triangles) with the atlas of tools/box_textures.py on it (name of the contents on the
sides, colour band, taped seam on top). Driven by tools/rebuild_boxes.py:

    blender --background --python tools/make_box_models.py -- <spec.json>

spec.json: a list of {id, folder, w, d, h, atlas (png path)}; writes <folder>/<id>.glb. Pivot at the middle of the footprint, bottom at z = 0, front = -Y.
"""
import json
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import box_textures  # noqa: E402  (layout only: no PIL needed here)


def build(item):
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    w, d, h = item['w'], item['d'], item['h']
    lay = box_textures.layout(w, d, h)
    W, H = lay['size']
    x0, x1, y0, y1 = -w / 2, w / 2, -d / 2, d / 2
    # face -> its four corners as seen from OUTSIDE (bottom left, bottom right, top right, top left) and which way the picture runs
    faces = {
        'front': [(x0, y0, 0), (x1, y0, 0), (x1, y0, h), (x0, y0, h)],
        'back': [(x1, y1, 0), (x0, y1, 0), (x0, y1, h), (x1, y1, h)],
        'left': [(x0, y1, 0), (x0, y0, 0), (x0, y0, h), (x0, y1, h)],
        'right': [(x1, y0, 0), (x1, y1, 0), (x1, y1, h), (x1, y0, h)],
        'top': [(x0, y0, h), (x1, y0, h), (x1, y1, h), (x0, y1, h)],
        'bottom': [(x0, y1, 0), (x1, y1, 0), (x1, y0, 0), (x0, y0, 0)],
    }
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    for name, corners in faces.items():
        fx, fy, fw, fh = lay['faces'][name]
        verts = [bm.verts.new(c) for c in corners]
        f = bm.faces.new(verts)
        rect = [(fx, fy + fh), (fx + fw, fy + fh), (fx + fw, fy), (fx, fy)]       # image pixels (origin top left): bottom left, bottom right, top right, top left
        for loop, (px, py) in zip(f.loops, rect):
            loop[uv].uv = (px / W, 1.0 - py / H)
    me = bpy.data.meshes.new(item['id'])
    bm.to_mesh(me)
    bm.free()
    img = bpy.data.images.load(item['atlas'])
    img.pack()
    mat = bpy.data.materials.new('Box')
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    tex.interpolation = 'Linear'
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.9
    me.materials.append(mat)
    obj = bpy.data.objects.new(item['id'], me)
    bpy.context.collection.objects.link(obj)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    out = os.path.join(item['folder'], item['id'] + '.glb')
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_yup=True, export_image_format='AUTO')
    print('box', item['id'], len(me.polygons) * 2, 'tris ->', out)


def main():
    spec = json.load(open(sys.argv[sys.argv.index('--') + 1], encoding='utf-8'))
    for item in spec:
        build(item)


if __name__ == '__main__':
    main()
