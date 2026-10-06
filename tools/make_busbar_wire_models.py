#!/usr/bin/env python3
"""
make_busbar_wire_models.py
Builds, in code (no paid generation), the DC wiring parts that connect the solar, battery and inverter items together (GLB, textures, icons, manifests):
  - wall-mountable DC bus bars in 3 sizes (100 A, 250 A, 500 A): copper bars on an insulating plate, studs and a printed label
  - DC wire for INSIDE (twin red / black) and WEATHER-RATED (UV and wet rated, black jacket) in 10 m coils and 25 m spools
The detail is in TEXTURES: brushed copper, the printed labels, the wound cable (rings of insulation) and the jacket print.
Wall item convention (docs/ATTACHED_ITEMS.md): the BACK is the plane y = 0 (Blender), it sticks out towards -y (the game's +z), bottom at z = 0, centred on x.
Run:  python tools/make_busbar_wire_models.py [--render] [--install]
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
WORK = os.path.join(ROOT, "assets", "_scratch", "busbar_wire")

# id: (name, amps, width, height, depth, studs per bar, bar height, bar thickness, weight kg, price)
BUSBARS = {
    "electricity_busbar_dc_100a": ("DC Bus Bar, Small", 100, 0.30, 0.15, 0.060, 6, 0.024, 0.005, 1.5, 45),
    "electricity_busbar_dc_250a": ("DC Bus Bar, Medium", 250, 0.45, 0.19, 0.070, 9, 0.032, 0.007, 3.5, 110),
    "electricity_busbar_dc_500a": ("DC Bus Bar, Large", 500, 0.60, 0.25, 0.085, 12, 0.044, 0.010, 7.0, 260),
}
# id: (name, kind, metres, spool radius, spool width, weight kg, price)
WIRES = {
    "electricity_wire_dc_indoor_10m": ("Indoor DC Wire Coil", "indoor", 10, 0.13, 0.10, 2.4, 38),
    "electricity_wire_dc_indoor_25m": ("Indoor DC Wire Spool", "indoor", 25, 0.19, 0.15, 5.8, 85),
    "electricity_wire_dc_outdoor_10m": ("Weatherproof DC Wire Coil", "outdoor", 10, 0.13, 0.10, 3.2, 55),
    "electricity_wire_dc_outdoor_25m": ("Weatherproof DC Wire Spool", "outdoor", 25, 0.19, 0.15, 7.8, 125),
}


def font(size, bold=True):
    from PIL import ImageFont
    f = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
    return ImageFont.truetype(f, size) if os.path.exists(f) else ImageFont.load_default()


def make_textures():
    from PIL import Image, ImageDraw
    os.makedirs(WORK, exist_ok=True)
    random.seed(3)
    # brushed copper
    cu = Image.new("RGB", (512, 128), (184, 108, 62))
    p = cu.load()
    for y in range(128):
        v = random.randint(-10, 10)
        for x in range(512):
            c = random.randint(-5, 5)
            p[x, y] = (184 + v + c, 108 + v // 2 + c, 62 + v // 3 + c)
    cu.save(os.path.join(WORK, "copper.png"))
    # the insulating plate
    pl = Image.new("RGB", (256, 256), (70, 74, 80))
    p = pl.load()
    for y in range(256):
        for x in range(256):
            c = random.randint(-4, 4)
            p[x, y] = (70 + c, 74 + c, 80 + c)
    pl.save(os.path.join(WORK, "plate.png"))

    for uid, (name, amps, w, h, d, studs, bh, bt, kg, price) in BUSBARS.items():
        W, H = 768, 256
        img = Image.new("RGB", (W, H), (226, 226, 222))
        dr = ImageDraw.Draw(img)
        dr.rectangle([0, 0, W, 64], fill=(40, 40, 46))
        dr.text((W // 2, 34), "DC BUS BAR", font=font(46), fill=(255, 255, 255), anchor="mm")
        dr.text((30, 150), "%d A" % amps, font=font(110), fill=(20, 20, 20), anchor="lm")
        dr.text((W - 30, 120), "150 V DC MAX", font=font(40), fill=(30, 30, 30), anchor="rm")
        dr.text((W - 30, 175), "COPPER  %d STUDS" % studs, font=font(32, False), fill=(60, 60, 60), anchor="rm")
        dr.rectangle([0, 214, W // 2, H], fill=(210, 50, 40))
        dr.text((W // 4, 235), "+ POSITIVE", font=font(32), fill=(255, 255, 255), anchor="mm")
        dr.rectangle([W // 2, 214, W, H], fill=(30, 30, 34))
        dr.text((3 * W // 4, 235), "- NEGATIVE", font=font(32), fill=(255, 255, 255), anchor="mm")
        dr.rectangle([2, 2, W - 3, H - 3], outline=(70, 70, 70), width=4)
        img.save(os.path.join(WORK, uid + "_label.png"))

    for uid, (name, kind, metres, R, width, kg, price) in WIRES.items():
        # the wound cable: rings of insulation across the width of the spool (rows of the image run along the spool)
        rings = 14 if metres <= 10 else 22
        Hh = rings * 12
        wind = Image.new("RGB", (64, Hh), (20, 20, 22))
        dr = ImageDraw.Draw(wind)
        for i in range(rings):
            y0 = i * 12
            if kind == "indoor":
                col = (200, 40, 36) if i % 2 == 0 else (28, 28, 30)        # a red and a black wire side by side
            else:
                col = (26, 27, 30)
            dr.rectangle([0, y0 + 1, 64, y0 + 11], fill=col)
            dr.line([(0, y0 + 3), (64, y0 + 3)], fill=tuple(min(255, c + 30) for c in col), width=1)
        wind.save(os.path.join(WORK, uid + "_wind.png"))
        # the flange label
        W, H = 512, 512
        img = Image.new("RGB", (W, H), (214, 190, 140))
        dr = ImageDraw.Draw(img)
        head = (200, 40, 36) if kind == "indoor" else (230, 160, 30)
        dr.rectangle([0, 0, W, 100], fill=head)
        dr.text((W // 2, 52), "DC WIRE", font=font(64), fill=(255, 255, 255), anchor="mm")
        dr.text((W // 2, 200), "%d m" % metres, font=font(150), fill=(30, 30, 30), anchor="mm")
        dr.text((W // 2, 310), "INDOOR  RED / BLACK" if kind == "indoor" else "WEATHER RATED", font=font(46), fill=(40, 40, 40), anchor="mm")
        dr.text((W // 2, 370), "600 V  90 C  6 mm2" if kind == "indoor" else "UV  WET  -40 TO 90 C  6 mm2", font=font(36, False), fill=(60, 60, 60), anchor="mm")
        dr.text((W // 2, 440), "TINNED COPPER  FLEXIBLE", font=font(32, False), fill=(60, 60, 60), anchor="mm")
        dr.rectangle([4, 4, W - 5, H - 5], outline=(90, 70, 40), width=6)
        img.save(os.path.join(WORK, uid + "_label.png"))


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
        elif axis == "x":
            bmesh.ops.transform(bm, matrix=Matrix.Rotation(math.pi / 2, 4, 'Y'), verts=bm.verts)
        for v in bm.verts:
            v.co += Vector(centre)
        return put(name, bm, mat)

    def wound(name, radius, length, centre, mat, segments=32):
        """A cylinder along z (the spool lies on its side) whose UV runs u round it and v up it: the winding texture's rings are stacked up the spool."""
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new("UVMap")
        ring0 = [bm.verts.new((math.cos(2 * math.pi * i / segments) * radius, math.sin(2 * math.pi * i / segments) * radius, -length / 2)) for i in range(segments)]
        ring1 = [bm.verts.new((math.cos(2 * math.pi * i / segments) * radius, math.sin(2 * math.pi * i / segments) * radius, length / 2)) for i in range(segments)]
        for i in range(segments):
            j = (i + 1) % segments
            f = bm.faces.new((ring0[i], ring0[j], ring1[j], ring1[i]))
            for loop, (u, v) in zip(f.loops, [(i / segments, 0), ((i + 1) / segments, 0), ((i + 1) / segments, 1), (i / segments, 1)]):
                loop[uvl].uv = (u, v)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for v in bm.verts:
            v.co += Vector(centre)
        return put(name, bm, mat)

    def quad_top(name, cx, cy, w, l, z, mat):
        bm = bmesh.new()
        vs = [bm.verts.new(c) for c in [(cx - w / 2, cy - l / 2, z), (cx + w / 2, cy - l / 2, z), (cx + w / 2, cy + l / 2, z), (cx - w / 2, cy + l / 2, z)]]
        f = bm.faces.new(vs)
        uv = bm.loops.layers.uv.new("UVMap")
        for loop, (u, v) in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
            loop[uv].uv = (u, v)
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

    # ---------------------------------------------------------------- bus bars (wall items)
    for uid, (name, amps, w, h, d, studs, bh, bt, kg, price) in BUSBARS.items():
        reset()
        copper = material("Copper", (1, 1, 1), 0.9, 0.35, tex=os.path.join(WORK, "copper.png"))
        plate = material("Plate", (1, 1, 1), 0.0, 0.6, tex=os.path.join(WORK, "plate.png"))
        label = material("Label", (1, 1, 1), 0.0, 0.5, tex=os.path.join(WORK, uid + "_label.png"))
        steel = material("Steel", (0.6, 0.62, 0.65), 0.9, 0.35)
        red = material("RedCap", (0.8, 0.1, 0.08), 0.0, 0.5)
        blk = material("BlackCap", (0.04, 0.04, 0.045), 0.0, 0.5)
        parts = []
        parts.append(box("Plate", (w, 0.014, h), (0, -0.007, h / 2), plate, 0.003))     # the back is y = 0; everything sticks out towards -y
        zp, zn = h * 0.70, h * 0.36                   # the positive bar above, the negative below
        span = w * 0.84
        for z, cap, tag in ((zp, red, "P"), (zn, blk, "N")):
            parts.append(box("Bar" + tag, (span, bt, bh), (0, -(0.014 + 0.012 + bt / 2), z), copper, 0.001))
            for sx in (-1, 1):
                parts.append(cylinder("Standoff" + tag, 0.010, 0.012, (sx * span * 0.42, -(0.014 + 0.006), z), steel, 8, "y"))
                parts.append(box("EndCap" + tag, (0.028, 0.02, bh + 0.012), (sx * (span / 2 + 0.014), -(0.014 + 0.012 + bt / 2), z), cap, 0.003))
            for i in range(studs):
                x = (-0.5 + (i + 0.5) / studs) * span * 0.92
                parts.append(cylinder("Stud" + tag, 0.0065 if amps < 400 else 0.008, 0.024 if amps < 400 else 0.032, (x, -(0.014 + 0.012 + bt + 0.012), z), steel, 8, "y"))
                parts.append(cylinder("Nut" + tag, 0.0105 if amps < 400 else 0.013, 0.007, (x, -(0.014 + 0.012 + bt + 0.020), z), steel, 6, "y"))
        lw = w * 0.26
        parts.append(quad_front("Label", 0, h - lw / 3.0 / 2 - 0.002, lw, lw / 3.0, -0.0145, label))
        export(parts, os.path.join(out_dir, uid + ".glb"))
        results[uid] = tris()

    # ---------------------------------------------------------------- wire coils and spools (lying on their side, axis vertical)
    for uid, (name, kind, metres, R, width, kg, price) in WIRES.items():
        reset()
        wind = material("Winding", (1, 1, 1), 0.0, 0.45, tex=os.path.join(WORK, uid + "_wind.png"))
        label = material("Label", (1, 1, 1), 0.0, 0.6, tex=os.path.join(WORK, uid + "_label.png"))
        flange_m = material("Flange", (0.55, 0.40, 0.26), 0.0, 0.85)
        steel = material("Ferrule", (0.75, 0.77, 0.80), 0.9, 0.3)
        red = material("Red", (0.75, 0.08, 0.06), 0.0, 0.5)
        blk = material("Black", (0.03, 0.03, 0.035), 0.0, 0.5)
        tie = material("Tie", (0.9, 0.9, 0.88), 0.0, 0.6)
        fl = 0.008                                     # the spool lies on its side: a flange on the ground, the winding above it, a flange and the label on top
        zc = fl + width / 2
        top = fl + width + fl
        core_r = R * 0.45
        parts = []
        parts.append(cylinder("Core", core_r, width, (0, 0, zc), flange_m, 14, "z"))
        parts.append(cylinder("FlangeLow", R, fl, (0, 0, fl / 2), flange_m, 24, "z"))
        parts.append(cylinder("FlangeTop", R, fl, (0, 0, top - fl / 2), flange_m, 24, "z"))
        parts.append(wound("Winding", R * 0.93, width, (0, 0, zc), wind))
        # the label sticker on the top flange
        parts.append(quad_top("Label", 0, 0, R * 1.15, R * 1.15, top + 0.0005, label))
        # (no loose ends standing up from the top: the top is flat, so coils and spools stack)
        # two cable ties round the winding
        for z in (fl + width * 0.25, fl + width * 0.75):
            parts.append(cylinder("Tie", R * 0.935, 0.006, (0, 0, z), tie, 24, "z"))
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


def load(p):
    return json.load(open(p, encoding="utf-8"))


def write_item(folder, uid, m, out):
    os.makedirs(folder, exist_ok=True)
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
        "# %s\n\n**Item ID:** `%s`  \n**Category:** `electricity`  \n**Icon:** ![%s](%s.png)\n\n%s\n" % (m["name"], uid, m["name"], uid, m["description"])))


def install(out):
    tris = dict(l.split() for l in open(os.path.join(out, "tris.txt")).read().strip().splitlines())
    bus_tpl = load(os.path.join(ELEC, "electricity_breaker_box_dc_64a", "electricity_breaker_box_dc_64a.json"))
    wire_tpl = load(os.path.join(ROOT, "assets", "building", "building_romex_14_2_spool", "building_romex_14_2_spool.json"))
    for uid, (name, amps, w, h, d, studs, bh, bt, kg, price) in BUSBARS.items():
        m = copy.deepcopy(bus_tpl)
        m["id"] = uid
        m["name"] = name
        m["icon"] = uid + ".png"
        m["description"] = ("A %d amp DC bus bar: a positive and a negative copper bar with %d studs each on an insulating plate, to join the solar, battery and inverter wiring in one place. "
                            "It mounts on a building's wall: aim at a wall of a finished building and left click." % (amps, studs))
        pr = m["properties"]
        pr["weight_kg"] = kg
        pr["base_value"] = price
        pr["max_stack_size"] = 10
        pr["placeable"] = False
        pr["attach_surface"] = "wall"
        pr["attach_side"] = "either"
        pr["stores"] = ["voltvision"]
        pr["sale_unit"] = "ea"
        pr["footprint"] = "%.2fm W x %.3fm D x %.2fm H" % (w, d, h)
        m["models"] = [{"file": uid + ".glb", "format": "glb", "dimensions_m": {"x": w, "y": h, "z": d}, "triangles": int(tris[uid])}]
        text = "Joins DC circuits: %d A, 150 V DC, %d studs per bar" % (amps, studs)
        m["utilities"]["electricity"] = {"metric": text, "details": text}
        m["category_fields"]["dimensions_m"] = {"width": w, "depth": d, "height": h}
        m["category_fields"]["max_power_w"] = 0
        write_item(os.path.join(ELEC, uid), uid, m, out)
    for uid, (name, kind, metres, R, width, kg, price) in WIRES.items():
        m = copy.deepcopy(wire_tpl)
        m["category"] = "electricity"                          # (the Romex template is a building item)
        m["category_fields"] = copy.deepcopy(bus_tpl["category_fields"])
        m["category_fields"]["max_power_w"] = 0
        m["category_fields"]["max_current_a"] = 55
        m["utilities"] = copy.deepcopy(bus_tpl["utilities"])
        text = "Carries DC: 6 mm2 tinned copper, about 55 A, %s" % ("inside only" if kind == "indoor" else "weather rated (UV, wet)")
        m["utilities"]["electricity"] = {"metric": text, "details": text}
        m["id"] = uid
        m["name"] = name
        m["icon"] = uid + ".png"
        if kind == "indoor":
            m["description"] = "A %d m %s of flexible 6 mm2 tinned-copper DC wire, red and black, for the wiring INSIDE a building (600 V, 90 C). Not for outdoor use." % (metres, "coil" if metres <= 10 else "spool")
        else:
            m["description"] = "A %d m %s of weather-rated flexible 6 mm2 tinned-copper DC wire (solar PV wire): a UV-resistant, wet-rated black jacket for runs outdoors, between panels and the building." % (metres, "coil" if metres <= 10 else "spool")
        pr = m["properties"]
        pr["weight_kg"] = kg
        pr["base_value"] = price
        pr["max_stack_size"] = 5
        pr["placeable"] = True
        pr["display_weight"] = True
        pr["stores"] = ["voltvision"]
        pr["sale_unit"] = "ea"
        pr["footprint"] = "%.2fm W x %.2fm D x %.2fm H" % (2 * R, 2 * R, width + 0.016 + 0.17)
        m["models"] = [{"file": uid + ".glb", "format": "glb", "dimensions_m": {"x": round(2 * R, 3), "y": round(width + 0.016 + 0.17, 3), "z": round(2 * R, 3)}, "triangles": int(tris[uid])}]
        m["category_fields"]["dimensions_m"] = {"width": round(2 * R, 3), "depth": round(2 * R, 3), "height": round(width + 0.016 + 0.17, 3)}
        write_item(os.path.join(ELEC, uid), uid, m, out)


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
        for uid in list(BUSBARS) + list(WIRES):
            subprocess.run([sys.executable, os.path.join(ROOT, "tools", "render_icon_from_model.py"), os.path.join(out, uid + ".glb"), os.path.join(WORK, uid + ".png")], check=True, capture_output=True)
    if "--install" in sys.argv:
        install(out)
        print("installed")


if __name__ == "__main__":
    main()
