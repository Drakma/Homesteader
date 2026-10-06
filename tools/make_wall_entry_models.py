#!/usr/bin/env python3
"""
make_wall_entry_models.py
Builds, in code (no paid generation), the wire entry that goes THROUGH a wall (GLB, textures, icon, manifest): a weatherproof plate with a cable gland, a printed label and
corner screws, and a sleeve through the wall. The game (AttachedObject.ApplyThrough) measures the wall, lengthens the sleeve to it and shows a second plate on the other side, so it
is seen and clicked from both sides.
Node convention: "Plate" (its back on the plane y = 0, its front towards -y in Blender = the game's +z, bottom at z = 0, centred on x) and "Pipe" (a 0.25 m sleeve going into the wall, towards +y).
Run:  python tools/make_wall_entry_models.py [--render] [--install]
"""
import copy
import json
import os
import random
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ELEC = os.path.join(ROOT, "assets", "electricity")
WORK = os.path.join(ROOT, "assets", "_scratch", "wall_entry")
UID = "electricity_wall_entry_wire"
NAME = "Wall Wire Entry"
PLATE = 0.16
SLEEVE = 0.25


def font(size, bold=True):
    from PIL import ImageFont
    f = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
    return ImageFont.truetype(f, size) if os.path.exists(f) else ImageFont.load_default()


def make_textures():
    from PIL import Image, ImageDraw
    os.makedirs(WORK, exist_ok=True)
    random.seed(9)
    pl = Image.new("RGB", (256, 256), (196, 200, 206))
    p = pl.load()
    for y in range(256):
        v = random.randint(-5, 5)
        for x in range(256):
            c = 196 + v + random.randint(-3, 3)
            p[x, y] = (c, c + 3, c + 8)
    pl.save(os.path.join(WORK, "plate.png"))
    img = Image.new("RGB", (512, 96), (30, 32, 36))
    d = ImageDraw.Draw(img)
    d.text((256, 30), "WIRE ENTRY  IP67", font=font(46), fill=(235, 235, 240), anchor="mm")
    d.text((256, 72), "DC  600 V  DO NOT REMOVE WHILE LIVE", font=font(26, False), fill=(170, 176, 188), anchor="mm")
    d.rectangle([2, 2, 509, 93], outline=(90, 94, 104), width=3)
    img.save(os.path.join(WORK, "label.png"))


def blender_main(out_dir):
    import bpy
    import bmesh
    import math
    from mathutils import Matrix, Vector

    bpy.ops.wm.read_factory_settings(use_empty=True)

    def material(name, rgb, metallic=0.0, rough=0.5, tex=None):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
        b.inputs["Metallic"].default_value = metallic
        b.inputs["Roughness"].default_value = rough
        if tex:
            node = m.node_tree.nodes.new("ShaderNodeTexImage")
            node.image = bpy.data.images.load(tex)
            uvn = m.node_tree.nodes.new("ShaderNodeUVMap")
            uvn.uv_map = "UVMap"
            m.node_tree.links.new(uvn.outputs["UV"], node.inputs["Vector"])
            m.node_tree.links.new(node.outputs["Color"], b.inputs["Base Color"])
        return m

    def put(name, bm, mat):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        while len(me.uv_layers) > 1:
            me.uv_layers.remove(me.uv_layers[len(me.uv_layers) - 1])
        if len(me.uv_layers) == 1:
            me.uv_layers[0].name = "UVMap"
        ob = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(ob)
        me.materials.append(mat)
        return ob

    def box(name, size, centre, mat, bevel=0.0):
        bm = bmesh.new()
        bm.loops.layers.uv.verify()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= size[0]
            v.co.y *= size[1]
            v.co.z *= size[2]
        if bevel > 0:
            bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), offset=bevel, offset_type='OFFSET', segments=2, profile=0.5, affect='EDGES')
        for v in bm.verts:
            v.co += Vector(centre)
        return put(name, bm, mat)

    def cyl(name, r1, r2, length, centre, mat, segments=16):
        """A cylinder / cone along y: radius r1 at the low-y end, r2 at the high-y end."""
        bm = bmesh.new()
        bm.loops.layers.uv.verify()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=r1, radius2=r2, depth=length)
        bmesh.ops.transform(bm, matrix=Matrix.Rotation(-math.pi / 2, 4, 'X'), verts=bm.verts)
        for v in bm.verts:
            v.co += Vector(centre)
        return put(name, bm, mat)

    def quad_front(name, cx, cz, w, h, y, mat):
        bm = bmesh.new()
        vs = [bm.verts.new(c) for c in [(cx - w / 2, y, cz - h / 2), (cx + w / 2, y, cz - h / 2), (cx + w / 2, y, cz + h / 2), (cx - w / 2, y, cz + h / 2)]]
        f = bm.faces.new(vs)
        uv = bm.loops.layers.uv.new("UVMap")
        for loop, (u, v) in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
            loop[uv].uv = (u, v)
        return put(name, bm, mat)

    def join(objs, name):
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.join()
        objs[0].name = name
        return objs[0]

    plate_m = material("Plate", (1, 1, 1), 0.6, 0.45, tex=os.path.join(WORK, "plate.png"))
    label_m = material("Label", (1, 1, 1), 0.0, 0.5, tex=os.path.join(WORK, "label.png"))
    dark = material("Rubber", (0.03, 0.03, 0.035), 0.0, 0.7)
    steel = material("Steel", (0.62, 0.64, 0.67), 0.9, 0.35)
    sleeve_m = material("Sleeve", (0.20, 0.21, 0.23), 0.1, 0.6)
    cz = PLATE / 2                                         # the centre of the plate, up from the bottom
    parts = []
    parts.append(box("Plate", (PLATE, 0.012, PLATE), (0, -0.006, cz), plate_m, 0.004))
    parts.append(cyl("Collar", 0.036, 0.036, 0.020, (0, -0.012 - 0.010, cz), steel, 20))          # the raised collar of the gland
    parts.append(cyl("Nut", 0.033, 0.033, 0.008, (0, -0.012 - 0.024, cz), steel, 6))              # the hex locking nut
    parts.append(cyl("Seal", 0.021, 0.021, 0.034, (0, -0.012 - 0.021, cz), dark, 16))             # the rubber seal the wire goes through
    parts.append(cyl("Port", 0.0095, 0.0095, 0.002, (0, -0.012 - 0.0385, cz), material("Bore", (0.0, 0.0, 0.0), 0.0, 1.0), 12))
    for sx in (-1, 1):
        for sz in (-1, 1):
            parts.append(cyl("Screw", 0.0065, 0.0065, 0.006, (sx * (PLATE / 2 - 0.016), -0.012 - 0.003, cz + sz * (PLATE / 2 - 0.016)), steel, 8))
    parts.append(quad_front("Sticker", 0, 0.024, 0.11, 0.0206, -0.0121, label_m))
    join(parts, "Plate")
    pipe = cyl("Pipe", 0.024, 0.024, SLEEVE, (0, SLEEVE / 2, cz), sleeve_m, 16)
    pipe.name = "Pipe"
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, UID + ".glb"), export_format='GLB', use_selection=True, export_apply=True, export_yup=True)
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
    open(os.path.join(out_dir, "tris.txt"), "w").write("%s %d\n" % (UID, tris))


def find_blender():
    for p in (r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe", "blender"):
        if os.path.exists(p) or p == "blender":
            return p
    return "blender"


def retry(fn, *a):
    for _ in range(30):
        try:
            return fn(*a)
        except OSError:
            time.sleep(1.5)
    raise SystemExit("io failed")


def install(out):
    tris = int(open(os.path.join(out, "tris.txt")).read().split()[1])
    base = json.load(open(os.path.join(ELEC, "electricity_breaker_box_dc_64a", "electricity_breaker_box_dc_64a.json"), encoding="utf-8"))
    m = copy.deepcopy(base)
    m["id"] = UID
    m["name"] = NAME
    m["icon"] = UID + ".png"
    m["description"] = ("A weatherproof wire entry that goes THROUGH a wall, to bring wires into a building from outside. Aim at a wall of a finished building and left click: "
                        "it shows on both sides (a plate with a sealed cable gland on each, joined by a sleeve through the wall) and can be clicked from either side.")
    pr = m["properties"]
    pr["weight_kg"] = 0.6
    pr["base_value"] = 28
    pr["max_stack_size"] = 20
    pr["placeable"] = False
    pr["attach_surface"] = "wall"
    pr["attach_side"] = "either"
    pr["attach_through"] = True
    pr["stores"] = ["voltvision"]
    pr["sale_unit"] = "ea"
    pr["footprint"] = "%.2fm W x %.2fm D x %.2fm H" % (PLATE, SLEEVE, PLATE)
    m["models"] = [{"file": UID + ".glb", "format": "glb", "dimensions_m": {"x": PLATE, "y": PLATE, "z": 0.05}, "triangles": tris}]
    text = "Passes DC wires through a wall (weatherproof, IP67)"
    m["utilities"]["electricity"] = {"metric": text, "details": text}
    m["category_fields"]["dimensions_m"] = {"width": PLATE, "depth": 0.05, "height": PLATE}
    m["category_fields"]["max_power_w"] = 0
    folder = os.path.join(ELEC, UID)
    os.makedirs(folder, exist_ok=True)
    for f in os.listdir(folder):
        if f.endswith((".obj", ".mtl")) or (f.endswith(".glb") and f != UID + ".glb"):
            os.remove(os.path.join(folder, f))
    retry(shutil.copy, os.path.join(out, UID + ".glb"), os.path.join(folder, UID + ".glb"))
    png = os.path.join(WORK, UID + ".png")
    if os.path.exists(png):
        retry(shutil.copy, png, os.path.join(folder, UID + ".png"))
    text = (json.dumps(m, indent=2, ensure_ascii=False) + "\n").replace("\n", "\r\n")
    retry(lambda: open(os.path.join(folder, UID + ".json"), "w", encoding="utf-8", newline="").write(text))
    retry(lambda: open(os.path.join(folder, "README.md"), "w", encoding="utf-8", newline="").write(
        "# %s\n\n**Item ID:** `%s`  \n**Category:** `electricity`  \n**Icon:** ![%s](%s.png)\n\n%s\n" % (NAME, UID, NAME, UID, m["description"])))


def main():
    if "--blender" in sys.argv:
        blender_main(sys.argv[sys.argv.index("--") + 1])
        return
    make_textures()
    out = os.path.join(WORK, "glb")
    os.makedirs(out, exist_ok=True)
    r = subprocess.run([find_blender(), "--background", "--python", os.path.abspath(__file__), "--", out, "--blender"], capture_output=True, text=True)
    print((r.stdout + r.stderr)[-600:])
    print(open(os.path.join(out, "tris.txt")).read())
    if "--render" in sys.argv:
        subprocess.run([sys.executable, os.path.join(ROOT, "tools", "render_icon_from_model.py"), os.path.join(out, UID + ".glb"), os.path.join(WORK, UID + ".png")], check=True, capture_output=True)
    if "--install" in sys.argv:
        install(out)
        print("installed")


if __name__ == "__main__":
    main()
