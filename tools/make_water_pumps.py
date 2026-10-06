#!/usr/bin/env python3
"""
make_water_pumps.py
Builds, in code (no paid generation), the four surface water pumps that pull stored water out of a cistern (docs/WELLS.md, "Pumps between tanks"): an electric
motor on a base with the pump head on its end, a suction port in front and the outlet on top. Sized by their flow: low capacity (1200 L/h), the electric water
pump (2000), the shallow well jet pump (2400, with its small pressure bell) and high capacity (3600). They stand on the floor (placeable), the pivot at the
bottom centre.  Run:  python tools/make_water_pumps.py [--install]
"""
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATER = os.path.join(ROOT, "assets", "water")
WORK = os.path.join(ROOT, "assets", "_scratch", "water_pumps")
# id: (scale, motor colour, jet bell)
PUMPS = {
    "water_pump_low_capacity": (0.85, (0.15, 0.32, 0.62), False),
    "water_pump": (1.0, (0.12, 0.42, 0.25), False),
    "water_pump_jet_shallow_well": (1.05, (0.2, 0.22, 0.25), True),
    "water_pump_high_capacity": (1.3, (0.62, 0.12, 0.1), False),
}


def blender_main(out_dir):
    import bpy
    import bmesh
    from mathutils import Vector

    def reset():
        bpy.ops.wm.read_factory_settings(use_empty=True)

    def material(name, rgb, metallic=0.0, rough=0.5):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes.get("Principled BSDF")
        b.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
        b.inputs["Metallic"].default_value = metallic
        b.inputs["Roughness"].default_value = rough
        return m

    def put(name, bm, mat):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(ob)
        me.materials.append(mat)
        return ob

    def box(name, size, centre, mat):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = Vector((v.co.x * size[0] + centre[0], v.co.y * size[1] + centre[1], v.co.z * size[2] + centre[2]))
        return put(name, bm, mat)

    def cyl(name, r, length, centre, axis, mat, seg=18):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=length)
        for v in bm.verts:
            x, y, z = v.co.x, v.co.y, v.co.z
            if axis == "x":
                x, y, z = z, y, x
            elif axis == "y":
                x, y, z = x, z, y
            v.co = Vector((x + centre[0], y + centre[1], z + centre[2]))
        return put(name, bm, mat)

    results = {}
    for pid, (k, motor_rgb, jet) in PUMPS.items():
        reset()
        motor = material("Motor", motor_rgb, 0.3, 0.4)
        steel = material("Steel", (0.55, 0.57, 0.6), 0.8, 0.35)
        base = material("Base", (0.18, 0.18, 0.19), 0.5, 0.6)
        brass = material("Brass", (0.78, 0.6, 0.25), 0.9, 0.3)
        box("Base", (0.42 * k, 0.2 * k, 0.03 * k), (0, 0, 0.015 * k), base)
        cyl("Motor", 0.085 * k, 0.24 * k, (0.08 * k, 0, 0.13 * k), "x", motor)
        for i in range(5):
            cyl("Fin", 0.09 * k, 0.008 * k, (0.0 + i * 0.04 * k, 0, 0.13 * k), "x", motor)
        cyl("FanCover", 0.08 * k, 0.04 * k, (0.22 * k, 0, 0.13 * k), "x", base)
        cyl("Head", 0.1 * k, 0.1 * k, (-0.1 * k, 0, 0.13 * k), "x", steel)
        cyl("Suction", 0.025 * k, 0.08 * k, (-0.19 * k, 0, 0.13 * k), "x", brass)
        cyl("Outlet", 0.022 * k, 0.09 * k, (-0.1 * k, 0, 0.27 * k), "z", brass)
        box("Box", (0.06 * k, 0.07 * k, 0.05 * k), (0.09 * k, -0.07 * k, 0.22 * k), base)
        for x in (-0.15, 0.15):
            box("Foot", (0.04 * k, 0.16 * k, 0.04 * k), (x * k, 0, 0.05 * k), base)
        if jet:
            cyl("Bell", 0.07 * k, 0.16 * k, (-0.1 * k, 0, 0.4 * k), "z", steel)
            cyl("Gauge", 0.025 * k, 0.012 * k, (-0.1 * k, -0.07 * k, 0.4 * k), "y", brass)
        path = os.path.join(out_dir, pid + ".glb")
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=False, export_apply=True, export_yup=True)
        results[pid] = sum(len(p.vertices) - 2 for ob in bpy.context.scene.objects if ob.type == 'MESH' for p in ob.data.polygons)
    with open(os.path.join(out_dir, "tris.txt"), "w") as f:
        for kk, v in results.items():
            f.write("%s %d\n" % (kk, v))


def find_blender():
    for p in [shutil.which("blender"), r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"]:
        if p and os.path.exists(p):
            return p
    raise SystemExit("blender not found")


def install(out):
    tris = dict(l.split() for l in open(os.path.join(out, "tris.txt")).read().strip().splitlines())
    for pid, (k, _c, jet) in PUMPS.items():
        d = os.path.join(WATER, pid)
        p = os.path.join(d, pid + ".json")
        raw = open(p, "rb").read().decode("utf-8")
        crlf = "\r\n" in raw
        m = json.loads(raw)
        h = round((0.48 if jet else 0.32) * k, 2)
        dims = {"width": round(0.42 * k, 2), "depth": round(0.2 * k, 2), "height": h}
        m["models"] = [{"file": pid + ".glb", "format": "glb", "dimensions_m": {"x": dims["width"], "y": h, "z": dims["depth"]}, "triangles": int(tris[pid])}]
        m.setdefault("category_fields", {})["dimensions_m"] = dims
        m["properties"]["placeable"] = True
        for f in os.listdir(d):
            if f.endswith((".obj", ".mtl")) or (f.endswith(".glb") and f != pid + ".glb"):
                os.remove(os.path.join(d, f))
        shutil.copy(os.path.join(out, pid + ".glb"), os.path.join(d, pid + ".glb"))
        subprocess.run([sys.executable, os.path.join(ROOT, "tools", "render_icon_from_model.py"), os.path.join(d, pid + ".glb"), os.path.join(d, pid + ".png")], check=True, capture_output=True)
        t = json.dumps(m, indent=2, ensure_ascii=False) + "\n"
        if crlf:
            t = t.replace("\n", "\r\n")
        open(p, "wb").write(t.encode("utf-8"))
        print("installed", pid, tris[pid])


def main():
    if "--blender" in sys.argv:
        blender_main(sys.argv[sys.argv.index("--") + 1])
        return
    out = os.path.join(WORK, "glb")
    os.makedirs(out, exist_ok=True)
    r = subprocess.run([find_blender(), "--background", "--python", os.path.abspath(__file__), "--", out, "--blender"], capture_output=True, text=True)
    if not os.path.exists(os.path.join(out, "tris.txt")):
        print((r.stdout + r.stderr)[-2000:])
        return
    if "--install" in sys.argv:
        install(out)


if __name__ == "__main__":
    main()
