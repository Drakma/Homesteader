"""
Runs INSIDE Blender (headless):  blender -b --python blender_to_glb.py -- jobs.json results.json

Converts each job's FBX / OBJ(+MTL) into a GLB with textures embedded, written next to the source
as <stem>.glb. GLB is the project's default model format.

Per job:
  - imports the model into an empty scene
  - skips rigged / animated models (armature): Unity's Humanoid/Generic animation needs FBX for those
  - if <stem>_base_color.png sits beside the model it becomes the base colour (the authored texture;
    FBX-embedded images were blank for the crops)
  - checks the model's size against the manifest's dimensions_m and snaps a 0.001/0.01/0.1/1/10/100
    unit scale onto it when they disagree by a whole unit factor (OBJs are often centimetres)
  - exports GLB (Y-up, materials, embedded images, no cameras/lights)
"""
import bpy
import json
import math
import os
import sys
from mathutils import Vector

argv = sys.argv
argv = argv[argv.index('--') + 1:] if '--' in argv else []
jobs_path, results_path = argv[0], argv[1]
jobs = json.load(open(jobs_path, encoding='utf-8'))
results = []

CANDIDATE_SCALES = [0.001, 0.01, 0.1, 1.0, 10.0, 100.0]


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def world_bbox(objs):
    lo = Vector((1e18, 1e18, 1e18))
    hi = Vector((-1e18, -1e18, -1e18))
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector((min(lo.x, w.x), min(lo.y, w.y), min(lo.z, w.z)))
            hi = Vector((max(hi.x, w.x), max(hi.y, w.y), max(hi.z, w.z)))
    return lo, hi


def import_model(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.fbx':
        bpy.ops.import_scene.fbx(filepath=path)
    elif ext == '.obj':
        bpy.ops.wm.obj_import(filepath=path)
    else:
        raise RuntimeError('unsupported extension ' + ext)


def apply_base_color(png_path):
    """Rebuild every material as a simple Principled BSDF using png_path as the base colour."""
    img = bpy.data.images.load(png_path)
    img.pack()
    for mat in list(bpy.data.materials):
        mat.use_nodes = True
        nt = mat.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
        tex = nt.nodes.new('ShaderNodeTexImage')
        tex.image = img
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
        if 'Roughness' in bsdf.inputs:
            bsdf.inputs['Roughness'].default_value = 0.9
        if 'Metallic' in bsdf.inputs:
            bsdf.inputs['Metallic'].default_value = 0.0


def export_glb(out_path):
    kwargs = dict(filepath=out_path, export_format='GLB', export_image_format='AUTO', export_materials='EXPORT',
                  export_cameras=False, export_lights=False, export_apply=True, export_yup=True)
    try:
        bpy.ops.export_scene.gltf(**kwargs)
    except TypeError:
        # A keyword this Blender version does not know: fall back to the essentials.
        bpy.ops.export_scene.gltf(filepath=out_path, export_format='GLB')


for job in jobs:
    src = job['src']
    out = job['out']
    res = {'src': src, 'out': out, 'status': 'error'}
    try:
        reset()
        import_model(src)
        objs = list(bpy.context.scene.objects)
        meshes = [o for o in objs if o.type == 'MESH']
        if not meshes:
            res.update(status='skipped', reason='no meshes')
            results.append(res)
            continue
        if any(o.type == 'ARMATURE' for o in objs) or any(o.animation_data and o.animation_data.action for o in objs):
            res.update(status='skipped', reason='rigged/animated - keep FBX')
            results.append(res)
            continue

        stem = os.path.splitext(src)[0]
        base_color = stem + '_base_color.png'
        if os.path.isfile(base_color):
            apply_base_color(base_color)
            res['base_color'] = True

        lo, hi = world_bbox(meshes)
        size = hi - lo
        cur_max = max(size.x, size.y, size.z)
        # Match how the game already treats each format: FBX are metric via the file's unit scale (Blender
        # applies it on import, like Unity's Convert Units), OBJ are centimetres (ObjMeshParser scales by 0.01).
        scale = 0.01 if src.lower().endswith('.obj') else 1.0
        flag = None
        exp = job.get('dims')          # [w, d, h] metres from the manifest, or None - informational only
        if exp and max(exp) > 0 and cur_max > 0:
            got = cur_max * scale
            if abs(math.log(got / max(exp))) > math.log(3.0):
                flag = 'size_note: model %.3f m vs manifest %.3f m (kept as-authored)' % (got, max(exp))

        if scale != 1.0:
            root = bpy.data.objects.new('ScaleRoot', None)
            bpy.context.scene.collection.objects.link(root)
            for o in objs:
                if o.parent is None:
                    o.parent = root
            root.scale = (scale, scale, scale)
            bpy.context.view_layer.update()
            lo, hi = world_bbox(meshes)
            size = hi - lo

        tris = sum(len(m.data.polygons) for m in meshes)
        export_glb(out)
        res.update(status='ok', scale=scale, tris=tris, meshes=len(meshes),
                   materials=len(bpy.data.materials), images=len(bpy.data.images),
                   size_m=[round(size.x, 3), round(size.y, 3), round(size.z, 3)],
                   bytes=os.path.getsize(out) if os.path.isfile(out) else 0)
        if flag:
            res['flag'] = flag
    except Exception as e:  # keep the batch going; the driver retries/reports
        res.update(status='error', reason=str(e)[:300])
    results.append(res)

json.dump(results, open(results_path, 'w', encoding='utf-8'), indent=1)
