#!/usr/bin/env python3
"""
make_water_heater.py
Builds, in code (no paid generation), the electric water heater for the well water system (docs/WELLS.md): a 190 liter (50 gallon) white tank with a 4500 W
element. It is a water tank on the water line (wire_role water_tank) that also heats what it holds while it has power (heater_w), placed in the pump house
after the filters. Run:  python tools/make_water_heater.py [--install]
"""
import copy
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATER = os.path.join(ROOT, "assets", "water")
WORK = os.path.join(ROOT, "assets", "_scratch", "water_heater")
HID = "water_heater_electric_190l"


def blender_main(out_dir):
    import bpy
    import bmesh
    from mathutils import Vector

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

    def cyl(name, r, h, base, mat, seg=24, axis="z"):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=h)
        for v in bm.verts:
            x, y, z = v.co.x, v.co.y, v.co.z + h / 2
            if axis == "y":
                x, y, z = v.co.x, -(v.co.z + h / 2), v.co.y
            v.co = Vector((x + base[0], y + base[1], z + base[2]))
        return put(name, bm, mat)

    def box(name, size, centre, mat):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = Vector((v.co.x * size[0] + centre[0], v.co.y * size[1] + centre[1], v.co.z * size[2] + centre[2]))
        return put(name, bm, mat)

    white = material("Shell", (0.93, 0.93, 0.91), 0.1, 0.35)
    grey = material("Trim", (0.55, 0.56, 0.58), 0.6, 0.4)
    copper = material("Copper", (0.72, 0.42, 0.24), 0.9, 0.35)
    label = material("Label", (0.85, 0.25, 0.15), 0.0, 0.5)
    cyl("Tank", 0.28, 1.42, (0, 0, 0.04), white)
    cyl("Top", 0.27, 0.04, (0, 0, 1.46), grey)
    cyl("Base", 0.26, 0.04, (0, 0, 0), grey)
    for x in (-0.09, 0.09):
        cyl("Pipe", 0.016, 0.22, (x, 0, 1.50), copper, 10)
    box("Panel", (0.14, 0.02, 0.10), (0, -0.28, 0.45), grey)
    box("Panel2", (0.14, 0.02, 0.10), (0, -0.28, 1.10), grey)
    box("Label", (0.20, 0.012, 0.26), (0.0, -0.28, 0.78), label)
    cyl("Valve", 0.012, 0.10, (0.20, -0.18, 1.30), copper, 8, "y")
    path = os.path.join(out_dir, HID + ".glb")
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=False, export_apply=True, export_yup=True)
    n = sum(len(p.vertices) - 2 for ob in bpy.context.scene.objects if ob.type == 'MESH' for p in ob.data.polygons)
    with open(os.path.join(out_dir, "tris.txt"), "w") as f:
        f.write("%s %d\n" % (HID, n))


def find_blender():
    for p in [shutil.which("blender"), r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"]:
        if p and os.path.exists(p):
            return p
    raise SystemExit("blender not found")


def install(out):
    tris = dict(l.split() for l in open(os.path.join(out, "tris.txt")).read().strip().splitlines())
    tpl = json.load(open(os.path.join(WATER, "water_pressuretank_well", "water_pressuretank_well.json"), encoding="utf-8"))
    d = os.path.join(WATER, HID)
    os.makedirs(d, exist_ok=True)
    m = copy.deepcopy(tpl)
    m["id"] = HID
    m["name"] = "Electric Water Heater"
    m["icon"] = HID + ".png"
    m["description"] = ("A 190 liter (50 gallon) electric water heater with a 4500 W element. Pipe it after the filters (pipe wrench, PVC pipe): it fills like a tank and heats "
                        "what it holds to 55 C while the building it stands in has power, drawing its element's watts while it heats.")
    pr = m["properties"]
    pr["weight_kg"] = 55.0
    pr["base_value"] = 650
    pr["max_stack_size"] = 1
    pr["placeable"] = True
    pr["is_buyable"] = True
    pr["stores"] = ["depot"]
    pr["wire_role"] = "water_tank"
    pr["heater_w"] = 4500
    cf = m.setdefault("category_fields", {})
    cf["dimensions_m"] = {"width": 0.56, "depth": 0.56, "height": 1.72}
    cf["capacity_l"] = 190
    cf["power_draw_w"] = 4500
    m["models"] = [{"file": HID + ".glb", "format": "glb", "dimensions_m": {"x": 0.56, "y": 1.72, "z": 0.56}, "triangles": int(tris[HID])}]
    for f in os.listdir(d):
        if f.endswith(".glb") and f != HID + ".glb":
            os.remove(os.path.join(d, f))
    shutil.copy(os.path.join(out, HID + ".glb"), os.path.join(d, HID + ".glb"))
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "render_icon_from_model.py"), os.path.join(d, HID + ".glb"), os.path.join(d, HID + ".png")], check=True, capture_output=True)
    text = json.dumps(m, indent=2, ensure_ascii=False) + "\n"
    open(os.path.join(d, HID + ".json"), "wb").write(text.replace("\n", "\r\n").encode("utf-8"))
    open(os.path.join(d, "README.md"), "w", encoding="utf-8").write("# %s\n\n**Item ID:** `%s`  \n**Category:** `water`  \n**Icon:** ![%s](%s.png)\n\n%s\n" % (m["name"], HID, m["name"], HID, m["description"]))


def main():
    if "--blender" in sys.argv:
        blender_main(sys.argv[sys.argv.index("--") + 1])
        return
    out = os.path.join(WORK, "glb")
    os.makedirs(out, exist_ok=True)
    r = subprocess.run([find_blender(), "--background", "--python", os.path.abspath(__file__), "--", out, "--blender"], capture_output=True, text=True)
    print(open(os.path.join(out, "tris.txt")).read() if os.path.exists(os.path.join(out, "tris.txt")) else (r.stdout + r.stderr)[-1500:])
    if "--install" in sys.argv:
        install(out)
        print("installed")


if __name__ == "__main__":
    main()
