"""Decimate one dense clutter mesh to a target face count and export a game-ready OBJ.

Run headless:
    blender -b --python tools/decimate_clutter.py -- <src.obj> <dst.obj> <target_faces>

Why a script file rather than a one-liner: the model is a single mesh with
hundreds of thousands of faces, and the decimate modifier's collapse mode needs
a real ratio computed from the mesh's own triangle count. Doing that inline in
a --python-expr string means quoting a small program into a shell, which is
where this kind of thing breaks.

The output is written with materials untouched (Blender writes the .mtl
alongside), so an existing texture reference survives the round trip.
"""
import os
import sys

import bpy


def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    if len(argv) < 3:
        raise SystemExit("usage: -- <src.obj> <dst.obj> <target_faces>")
    return argv[0], argv[1], int(argv[2])


def main():
    src, dst, target = parse_args()
    if not os.path.isfile(src):
        raise SystemExit("source not found: " + src)

    # Start from an empty scene: the default startup file ships a cube, a
    # camera and a light, and any of them would end up in the export.
    bpy.ops.wm.read_factory_settings(use_empty=True)

    bpy.ops.wm.obj_import(filepath=src)

    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        raise SystemExit("no mesh objects imported from " + src)

    # Join first: a clutter scan often arrives as several objects, and the
    # decimate ratio has to be computed against the TOTAL triangle count or
    # each piece is decimated independently and the result overshoots.
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active

    # Deliberately NO edit-mode round trip here. Entering and leaving edit mode
    # before applying the modifier leaves the active object in a context where
    # modifier_apply discards its own result, which silently pinned every run
    # to 27,824 triangles no matter what target was asked for. bl_mesh_triangulate
    # is also unnecessary: these scans are already all-triangles on import
    # (polys == triangles == 1,785,269), so the ratio below is a true triangle
    # ratio as-is.
    obj.data.calc_loop_triangles()
    before = len(obj.data.loop_triangles)

    if before <= target:
        print("already at or below target (%d <= %d) - nothing to do" % (before, target))
        ratio = 1.0
    else:
        ratio = target / float(before)

    print("triangles before: %d" % before)
    print("target           : %d" % target)
    print("decimate ratio   : %.6f" % ratio)

    mod = obj.modifiers.new(name="Decimate", type="DECIMATE")
    mod.decimate_type = "COLLAPSE"
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=mod.name)

    obj.data.calc_loop_triangles()
    after = len(obj.data.loop_triangles)
    print("triangles after  : %d" % after)
    if before:
        print("reduction        : %.2f%%" % (100.0 * (1 - after / float(before))))

    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    bpy.ops.wm.obj_export(
        filepath=dst,
        export_materials=True,
        export_triangulated_mesh=True,
        # Keep the mesh's own scale: the asset pipeline normalises size at
        # import time, so baking a unit conversion here would double-apply it.
        global_scale=1.0,
    )
    print("wrote " + dst)


if __name__ == "__main__":
    main()
