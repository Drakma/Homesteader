#!/usr/bin/env python3
"""
make_mppt_models.py
Builds, in code (no paid generation), the MPPT solar charge controllers: 32 A, 64 A and 128 A (GLB, textures, icons, manifests). The detail is in TEXTURES: a printed front
(LCD readout, buttons, LEDs, terminal labels, rating plate) and a brushed anodised shell; the geometry is the body, the heatsink fins, the terminal cover, the glands and the flanges.
Wall item convention (docs/ATTACHED_ITEMS.md): the BACK is the plane y = 0 (Blender), it sticks out towards -y (the game's +z), bottom at z = 0, centred on x.
Run:  python tools/make_mppt_models.py [--install]
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
WORK = os.path.join(ROOT, "assets", "_scratch", "mppt")

# id: (name, amps, width, height, depth, weight kg, price, pv watts at 48 V, fins per side, accent rgb)
UNITS = {
    "electricity_controller_mppt_32a": ("MPPT Charge Controller, Small", 32, 0.20, 0.28, 0.09, 2.2, 180, 1500, 6, (40, 150, 220)),
    "electricity_controller_mppt_64a": ("MPPT Charge Controller, Medium", 64, 0.25, 0.36, 0.10, 4.5, 420, 3000, 8, (60, 180, 110)),
    "electricity_controller_mppt_128a": ("MPPT Charge Controller, Large", 128, 0.32, 0.46, 0.12, 8.5, 950, 6000, 11, (230, 140, 40)),
}
OLD = ("electricity_controller_mppt_60a", "electricity_mpptcontroller")


def font(size, bold=True):
    from PIL import ImageFont
    f = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
    return ImageFont.truetype(f, size) if os.path.exists(f) else ImageFont.load_default()


def mono(size):
    from PIL import ImageFont
    f = "C:/Windows/Fonts/consolab.ttf"
    return ImageFont.truetype(f, size) if os.path.exists(f) else font(size)


def make_textures():
    from PIL import Image, ImageDraw, ImageFilter
    os.makedirs(WORK, exist_ok=True)
    random.seed(11)
    # a brushed anodised shell (tileable enough: fine horizontal streaks over a flat grey)
    shell = Image.new("RGB", (512, 512), (58, 62, 70))
    px = shell.load()
    for y in range(512):
        v = random.randint(-9, 9)
        for x in range(512):
            n = random.randint(-4, 4)
            c = 58 + v + n
            px[x, y] = (c, c + 4, c + 12)
    shell.save(os.path.join(WORK, "shell.png"))
    # the heatsink fins: a darker streaked metal
    fin = Image.new("RGB", (256, 256), (36, 38, 44))
    fp = fin.load()
    for y in range(256):
        v = random.randint(-6, 6)
        for x in range(256):
            c = 40 + v + random.randint(-3, 3)
            fp[x, y] = (c, c + 2, c + 8)
    fin.save(os.path.join(WORK, "fin.png"))

    for uid, (name, amps, w, h, d, kg, price, pv, fins, accent) in UNITS.items():
        W = 1024
        H = int(W * (h - 0.02) / (w - 0.02))
        img = Image.new("RGB", (W, H), (18, 20, 24))
        dr = ImageDraw.Draw(img)
        s = W / 1024.0
        # the bezel and the LCD
        dr.rectangle([0, 0, W - 1, H - 1], outline=(70, 74, 82), width=6)
        dr.rectangle([0, 0, W, int(H * 0.085)], fill=accent)
        dr.text((W // 2, int(H * 0.043)), "HOMESTEAD MPPT", font=font(int(58 * s)), fill=(255, 255, 255), anchor="mm")
        lx0, ly0, lx1, ly1 = int(W * 0.08), int(H * 0.12), int(W * 0.92), int(H * 0.44)
        dr.rectangle([lx0 - 10, ly0 - 10, lx1 + 10, ly1 + 10], fill=(8, 9, 11))
        dr.rectangle([lx0, ly0, lx1, ly1], fill=(18, 58, 52))
        for yy in range(ly0, ly1, 4):                      # a faint pixel grid
            dr.line([(lx0, yy), (lx1, yy)], fill=(14, 50, 45), width=1)
        green = (120, 255, 190)
        dim = (70, 170, 130)
        dr.text((lx0 + 24, ly0 + 22), "PV", font=mono(int(46 * s)), fill=dim, anchor="la")
        dr.text((lx1 - 24, ly0 + 18), "%.1fV  %.1fA" % (96.4 if amps > 32 else 62.8, amps * 0.38), font=mono(int(54 * s)), fill=green, anchor="ra")
        dr.text((lx0 + 24, ly0 + 108), "BAT", font=mono(int(46 * s)), fill=dim, anchor="la")
        dr.text((lx1 - 24, ly0 + 104), "%.1fV  %.1fA" % (52.4, amps * 0.62), font=mono(int(54 * s)), fill=green, anchor="ra")
        dr.text((lx0 + 24, ly0 + 190), "%.2f kW" % (amps * 0.62 * 52.4 / 1000.0), font=mono(int(86 * s)), fill=green, anchor="la")
        # a charge bar
        bx0, by0, bx1, by1 = lx0 + 24, ly1 - 70, lx1 - 24, ly1 - 26
        dr.rectangle([bx0, by0, bx1, by1], outline=dim, width=3)
        segs = 12
        for i in range(segs):
            x0 = bx0 + 6 + i * (bx1 - bx0 - 12) / segs
            dr.rectangle([x0, by0 + 6, x0 + (bx1 - bx0 - 12) / segs - 5, by1 - 6], fill=green if i < 9 else (24, 80, 66))
        dr.text((lx1 - 24, ly1 - 100), "BULK  MPPT", font=mono(int(34 * s)), fill=dim, anchor="ra")
        # four buttons with their marks
        for i, label in enumerate(("MENU", "UP", "DOWN", "OK")):
            cx = int(W * (0.17 + i * 0.22))
            cy = int(H * 0.545)
            dr.ellipse([cx - 52, cy - 52, cx + 52, cy + 52], fill=(40, 44, 52), outline=(90, 96, 108), width=5)
            dr.text((cx, cy), {"MENU": "=", "UP": "^", "DOWN": "v", "OK": "OK"}[label], font=font(int(46 * s)), fill=(220, 224, 232), anchor="mm")
            dr.text((cx, cy + 78), label, font=font(int(30 * s), False), fill=(150, 156, 168), anchor="mm")
        # status LEDs
        for i, (label, col) in enumerate((("CHG", (60, 220, 100)), ("FLT", (80, 60, 40)), ("COM", (60, 140, 230)))):
            cx = int(W * (0.22 + i * 0.28))
            cy = int(H * 0.66)
            dr.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=col, outline=(30, 30, 30), width=3)
            dr.text((cx + 30, cy), label, font=font(int(32 * s)), fill=(190, 196, 208), anchor="lm")
        # the rating plate
        px0, py0, px1, py1 = int(W * 0.08), int(H * 0.715), int(W * 0.92), int(H * 0.835)
        dr.rectangle([px0, py0, px1, py1], fill=(206, 208, 212))
        dr.text((px0 + 24, (py0 + py1) // 2), "%d A" % amps, font=font(int(92 * s)), fill=(20, 20, 20), anchor="lm")
        dr.text((px1 - 24, py0 + 34), "12 / 24 / 48 V AUTO", font=font(int(38 * s)), fill=(30, 30, 30), anchor="rm")
        dr.text((px1 - 24, py1 - 30), "PV MAX 150 V   %d W" % pv, font=font(int(34 * s), False), fill=(50, 50, 50), anchor="rm")
        # the terminal row (the labels above the screw terminals)
        ty = int(H * 0.875)
        labels = ("PV+", "PV-", "BAT+", "BAT-", "LOAD")
        cols = ((220, 60, 50), (40, 40, 44), (220, 60, 50), (40, 40, 44), (230, 200, 60))
        for i, (t, c) in enumerate(zip(labels, cols)):
            cx = int(W * (0.12 + i * 0.19))
            dr.rectangle([cx - 52, ty - 20, cx + 52, ty + 20], fill=c)
            dr.text((cx, ty), t, font=font(int(30 * s)), fill=(255, 255, 255), anchor="mm")
        dr.text((W // 2, int(H * 0.955)), "DISCONNECT PV BEFORE SERVICE", font=font(int(30 * s), False), fill=(150, 156, 168), anchor="mm")
        img.save(os.path.join(WORK, uid + "_front.png"))


def blender_main(out_dir):
    import bpy
    import bmesh
    import math
    from mathutils import Matrix, Vector

    def reset():
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

    def cylinder(name, radius, length, centre, mat, segments=10, axis="z"):
        bm = bmesh.new()
        bm.loops.layers.uv.verify()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=radius, radius2=radius, depth=length)
        if axis == "y":
            bmesh.ops.transform(bm, matrix=Matrix.Rotation(math.pi / 2, 4, 'X'), verts=bm.verts)
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

    def export(objs, path):
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.join()
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True)

    def tris():
        return sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')

    results = {}
    for uid, (name, amps, w, h, d, kg, price, pv, fins, accent) in UNITS.items():
        reset()
        shell = material("Shell", (1, 1, 1), 0.7, 0.45, tex=os.path.join(WORK, "shell.png"))
        finm = material("Heatsink", (1, 1, 1), 0.7, 0.5, tex=os.path.join(WORK, "fin.png"))
        front = material("Front", (1, 1, 1), 0.1, 0.35, tex=os.path.join(WORK, uid + "_front.png"))
        dark = material("Dark", (0.03, 0.03, 0.035), 0.3, 0.5)
        brass = material("Terminal", (0.75, 0.6, 0.22), 0.9, 0.35)
        accm = material("Accent", tuple(c / 255.0 for c in accent), 0.0, 0.5)
        parts = []
        body_w = w - 0.0
        # the shell: a box with a deeper front section; the printed front on it
        parts.append(box("Shell", (body_w * 0.78, d * 0.9, h), (0, -d * 0.45, h / 2), shell, 0.006))
        parts.append(box("FrontFrame", (body_w * 0.78 + 0.004, 0.002, h + 0.004), (0, -d * 0.9, h / 2), dark, 0.0008))
        parts.append(quad_front("Front", 0, h / 2, body_w * 0.78 - 0.012, h - 0.016, -d * 0.9 - 0.0025, front))
        # the heatsink fins down both sides
        fin_h = h * 0.84
        span = body_w * 0.11
        for sx in (-1, 1):
            parts.append(box("FinBase", (0.006, d * 0.9, fin_h), (sx * (body_w * 0.39 + 0.003), -d * 0.45, h * 0.5), finm, 0.001))
            for i in range(fins):
                fz = h * 0.5 - fin_h / 2 + (i + 0.5) * fin_h / fins
                parts.append(box("Fin", (span, d * 0.86, 0.0045), (sx * (body_w * 0.39 + 0.006 + span / 2), -d * 0.45, fz), finm))
        # the accent strip along the top edge and the mounting flanges
        parts.append(box("AccentStrip", (body_w * 0.78, 0.004, 0.008), (0, -d * 0.9 - 0.0015, h - 0.002), accm))
        for z in (0.05, h - 0.05):
            parts.append(box("Flange", (body_w, 0.008, 0.028), (0, 0.004, z), shell, 0.002))
            for sx in (-1, 1):
                parts.append(cylinder("FlangeHole", 0.0055, 0.003, (sx * (body_w / 2 - 0.016), -0.0005, z), dark, 8, "y"))
        # the terminal cover with the screws, under the unit, and the cable glands
        parts.append(box("TerminalCover", (body_w * 0.78, d * 0.86, 0.022), (0, -d * 0.45, -0.011), dark, 0.004))
        for i in range(5):
            x = (-0.4 + i * 0.2) * body_w * 0.78 * 1.0
            parts.append(cylinder("Gland%d" % i, 0.0095, 0.02, (x * 0.9, -d * 0.45, -0.032), dark, 8))
            parts.append(cylinder("Screw%d" % i, 0.0045, 0.004, (x * 0.9, -d * 0.9 - 0.0005, -0.003), brass, 6, "y"))
        export(parts, os.path.join(out_dir, uid + ".glb"))
        results[uid] = tris()

    with open(os.path.join(out_dir, "tris.txt"), "w") as f:
        for k, v in results.items():
            f.write("%s %d\n" % (k, v))


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
    tris = dict(l.split() for l in open(os.path.join(out, "tris.txt")).read().strip().splitlines())
    base = json.load(open(os.path.join(ELEC, "electricity_mpptcontroller", "electricity_mpptcontroller.json"), encoding="utf-8"))
    for uid, (name, amps, w, h, d, kg, price, pv, fins, accent) in UNITS.items():
        folder = os.path.join(ELEC, uid)
        os.makedirs(folder, exist_ok=True)
        m = copy.deepcopy(base)
        m["id"] = uid
        m["name"] = name
        m["icon"] = uid + ".png"
        m["description"] = ("A %d amp MPPT solar charge controller (12/24/48 volt battery systems, up to 150 volts of solar, about %.1f kW at 48 volts) with a finned heat sink, an LCD "
                            "readout and a terminal row. It mounts on a building's wall: aim at a wall of a finished building and left click." % (amps, pv / 1000.0))
        pr = m["properties"]
        pr["weight_kg"] = kg
        pr["base_value"] = price
        pr["max_stack_size"] = 5
        pr["placeable"] = False
        pr["attach_surface"] = "wall"
        pr["attach_side"] = "either"
        pr["stores"] = ["voltvision"]
        pr["sale_unit"] = "ea"
        pr["footprint"] = "%.2fm W x %.2fm D x %.2fm H" % (w, d, h)
        m["models"] = [{"file": uid + ".glb", "format": "glb", "dimensions_m": {"x": w, "y": h, "z": d}, "triangles": int(tris[uid])}]
        text = "Charges the battery bank from solar: %d A, up to %.1f kW (MPPT)" % (amps, pv / 1000.0)
        m["utilities"]["electricity"] = {"metric": text, "details": text}
        m["category_fields"]["dimensions_m"] = {"width": w, "depth": d, "height": h}
        m["category_fields"]["max_power_w"] = pv
        for f in os.listdir(folder):
            if f.endswith((".obj", ".mtl")) or (f.endswith(".glb") and f != uid + ".glb"):
                os.remove(os.path.join(folder, f))
        retry(shutil.copy, os.path.join(out, uid + ".glb"), os.path.join(folder, uid + ".glb"))
        png = os.path.join(WORK, uid + ".png")
        if os.path.exists(png):
            retry(shutil.copy, png, os.path.join(folder, uid + ".png"))
        text = (json.dumps(m, indent=2, ensure_ascii=False) + "\n").replace("\n", "\r\n")
        retry(lambda: open(os.path.join(folder, uid + ".json"), "w", encoding="utf-8", newline="").write(text))
        retry(lambda: open(os.path.join(folder, "README.md"), "w", encoding="utf-8", newline="").write(
            "# %s\n\n**Item ID:** `%s`  \n**Category:** `electricity`  \n**Icon:** ![%s](%s.png)\n\n%s\n" % (name, uid, name, uid, m["description"])))
    for old in OLD:
        d = os.path.join(ELEC, old)
        if os.path.isdir(d):
            shutil.rmtree(d)


def main():
    if "--blender" in sys.argv:
        blender_main(sys.argv[sys.argv.index("--") + 1])
        return
    make_textures()
    out = os.path.join(WORK, "glb")
    os.makedirs(out, exist_ok=True)
    r = subprocess.run([find_blender(), "--background", "--python", os.path.abspath(__file__), "--", out, "--blender"], capture_output=True, text=True)
    print((r.stdout + r.stderr)[-800:])
    print(open(os.path.join(out, "tris.txt")).read())
    if "--render" in sys.argv:
        for uid in UNITS:
            subprocess.run([sys.executable, os.path.join(ROOT, "tools", "render_icon_from_model.py"), os.path.join(out, uid + ".glb"), os.path.join(WORK, uid + ".png")], check=True, capture_output=True)
    if "--install" in sys.argv:
        install(out)
        print("installed")


if __name__ == "__main__":
    main()
