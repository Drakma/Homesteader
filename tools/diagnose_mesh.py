"""Diagnose why Blender's collapse decimate hits a floor on a scanned mesh.

Reports the mesh's structure so we can tell the difference between:
  - a single connected shell (decimate should reach any target), and
  - many disconnected shells / loose geometry (collapse bottoms out early,
    because each shell can only be reduced to its own minimum).

Run: blender -b --python tools/diagnose_mesh.py -- <src.obj>
"""
import sys

import bpy


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    if not argv:
        raise SystemExit("usage: -- <src.obj>")
    return argv[0]


def main():
    src = parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.obj_import(filepath=src)

    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    me = obj.data

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.quads_convert_to_tris(quad_method="BEAUTY", ngon_method="BEAUTY")
    bpy.ops.object.mode_set(mode="OBJECT")
    me.calc_loop_triangles()

    print("objects joined   : %d" % len(meshes))
    print("verts            : %d" % len(me.vertices))
    print("edges            : %d" % len(me.edges))
    print("polys            : %d" % len(me.polygons))
    print("triangles        : %d" % len(me.loop_triangles))

    # Euler characteristic per-shell tells us how many shells there are, via
    # the count of boundary/non-manifold edges.
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.mesh.select_non_manifold()
    non_manifold = bpy.context.tool_settings.mesh_select_mode
    bpy.ops.object.mode_set(mode="OBJECT")

    # Count loose (disconnected) pieces by walking UV-linked islands instead:
    # simpler and robust - count how many separate mesh "islands" exist by
    # flood-filling via edges.
    parent = list(range(len(me.vertices)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for e in me.edges:
        union(e.vertices[0], e.vertices[1])

    from collections import Counter
    roots = Counter(find(i) for i in range(len(me.vertices)))
    sizes = sorted(roots.values(), reverse=True)
    print("disconnected shells: %d" % len(roots))
    print("largest shell      : %d verts" % (sizes[0] if sizes else 0))
    print("5 largest sizes    : %s" % sizes[:5])
    print("median shell size  : %d" % (sizes[len(sizes) // 2] if sizes else 0))


if __name__ == "__main__":
    main()
