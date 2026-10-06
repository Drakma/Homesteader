#!/usr/bin/env python3
"""
make_solar_breaker_models.py
Builds, in code (no paid generation), detailed GLB models, textures and icons for:
  - solar panels: 100 W rigid, 200 W, 400 W commercial (aluminium frame, cell grid with busbars and fingers, cables with MC4 connectors)
  - outdoor breaker boxes: 50 A, 100 A, 200 A (steel enclosure, door, rain hood, hinges, latch and padlock, conduit hubs, printed rating label)
Run:  python tools/make_solar_breaker_models.py            (textures + Blender export + icons)
Blender runs headless (this same file is its script with --blender).
Conventions: GLB, metres, ground pivot (panels lie flat, centred, y_min = 0); wall boxes: x centred, y up from 0, back at z = 0 and the front at +z (the
AttachController convention: a wall model occupies z = 0 .. +depth).
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ELEC = os.path.join(ROOT, "assets", "electricity")
WORK = os.path.join(ROOT, "assets", "_scratch", "solar_breaker")

PANELS = {
    # id: (name, width m, length m, cell columns, cell rows)
    "electricity_solar_panel_100w_rigid": ("100W Rigid Solar Panel", 0.54, 0.67, 5, 6),
    "electricity_solar_panel_200w": ("200W Solar Panel", 0.80, 1.40, 6, 10),
    "electricity_solar_panel_400w_commercial": ("400W Commercial Solar Panel", 1.00, 2.00, 6, 12),
}
BREAKERS = {
    # id: (name, amps, width, height, depth, accent rgb)
    "electricity_panel_breaker_outdoor_50a": ("Outdoor Breaker Box 50A", 50, 0.30, 0.40, 0.12, (40, 160, 80)),
    "electricity_panel_breaker_outdoor_100a": ("Outdoor Breaker Box 100A", 100, 0.36, 0.52, 0.14, (40, 100, 200)),
    "electricity_panel_breaker_outdoor_200a": ("Outdoor Breaker Box 200A", 200, 0.46, 0.72, 0.16, (210, 70, 40)),
}
FRAME = 0.03


# ------------------------------------------------------------------------------------------------ textures (PIL)
def make_textures():
    from PIL import Image, ImageDraw, ImageFont
    import random
    os.makedirs(WORK, exist_ok=True)
    random.seed(7)

    for pid, (_, w, l, cols, rows) in PANELS.items():
        fw = FRAME if w > 0.6 else 0.022
        aw, al = w - 2 * fw, l - 2 * fw
        tw = 1024
        th = int(round(tw * al / aw))
        img = Image.new("RGB", (tw, th), (205, 208, 214))   # white back sheet showing at the edge and between the cells
        d = ImageDraw.Draw(img)
        margin = int(tw * 0.03)
        gap = max(3, int(tw * 0.006))
        cw = (tw - 2 * margin - gap * (cols - 1)) / cols
        ch = (th - 2 * margin - gap * (rows - 1)) / rows
        chamfer = min(cw, ch) * 0.1
        for r in range(rows):
            for c in range(cols):
                x0 = margin + c * (cw + gap)
                y0 = margin + r * (ch + gap)
                x1, y1 = x0 + cw, y0 + ch
                shade = random.randint(-6, 6)
                base = (24 + shade, 40 + shade, 86 + shade * 2)
                pts = [(x0 + chamfer, y0), (x1 - chamfer, y0), (x1, y0 + chamfer), (x1, y1 - chamfer), (x1 - chamfer, y1), (x0 + chamfer, y1), (x0, y1 - chamfer), (x0, y0 + chamfer)]
                d.polygon(pts, fill=base)
                # a soft lighter band across the cell (anti-reflective coating)
                d.polygon([(x0 + chamfer, y0), (x1 - chamfer, y0), (x1, y0 + chamfer), (x1, y0 + ch * 0.35), (x0, y0 + ch * 0.35), (x0, y0 + chamfer)], fill=(base[0] + 6, base[1] + 10, base[2] + 18))
                # fine fingers across the cell
                step = max(5, int(ch / 28))
                yy = y0 + step
                while yy < y1 - 2:
                    d.line([(x0 + 2, yy), (x1 - 2, yy)], fill=(base[0] + 22, base[1] + 30, base[2] + 40), width=1)
                    yy += step
                # three busbars down the cell
                for k in (1, 2, 3):
                    bx = x0 + cw * k / 4.0
                    d.line([(bx, y0 + 1), (bx, y1 - 1)], fill=(196, 202, 212), width=max(2, int(cw / 55)))
        # a faint glass reflection over the whole face
        over = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        od = ImageDraw.Draw(over)
        od.polygon([(0, th * 0.1), (tw * 0.55, 0), (tw, 0), (tw, th * 0.04), (tw * 0.4, th * 0.32), (0, th * 0.4)], fill=(255, 255, 255, 14))
        img = Image.alpha_composite(img.convert("RGBA"), over).convert("RGB")
        img.save(os.path.join(WORK, pid + "_cells.png"))

    def font(size, bold=True):
        for f in (r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\segoeuib.ttf"):
            if os.path.exists(f):
                return ImageFont.truetype(f, size)
        return ImageFont.load_default()

    for bid, (_, amps, w, h, dep, accent) in BREAKERS.items():
        W, H = 768, 384
        img = Image.new("RGB", (W, H), (236, 236, 232))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, W, 78], fill=accent)
        d.text((W // 2, 40), "OUTDOOR SERVICE PANEL", font=font(44), fill=(255, 255, 255), anchor="mm")
        d.text((26, 215), str(amps), font=font(190), fill=(20, 20, 20), anchor="lm")
        tx = 26 + d.textlength(str(amps), font=font(190)) + 10
        d.text((tx, 190), "A", font=font(92), fill=(20, 20, 20), anchor="lm")
        d.text((W - 30, 150), "120/240 V", font=font(46), fill=(30, 30, 30), anchor="rm")
        d.text((W - 30, 205), "1 PHASE  3 WIRE", font=font(34, False), fill=(30, 30, 30), anchor="rm")
        d.text((W - 30, 252), "NEMA 3R", font=font(34, False), fill=(30, 30, 30), anchor="rm")
        d.rectangle([0, 300, W, H], fill=(245, 200, 20))
        d.text((W // 2, 342), "WARNING  SHOCK HAZARD", font=font(44), fill=(20, 20, 20), anchor="mm")
        d.rectangle([2, 2, W - 3, H - 3], outline=(60, 60, 60), width=4)
        img.save(os.path.join(WORK, bid + "_label.png"))


# ------------------------------------------------------------------------------------------------ Blender
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
            me.uv_layers.remove(me.uv_layers[len(me.uv_layers) - 1])   # one UV set per mesh, so a joined mesh has just one
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
            bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), offset=bevel, offset_type='OFFSET', segments=1, profile=0.5, affect='EDGES')
        for v in bm.verts:
            v.co += Vector(centre)
        return put(name, bm, mat)

    def cylinder(name, radius, length, axis, centre, mat, segments=10):
        bm = bmesh.new()
        bm.loops.layers.uv.verify()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=radius, radius2=radius, depth=length)
        if axis == "x":
            bmesh.ops.transform(bm, matrix=Matrix.Rotation(math.pi / 2, 4, 'Y'), verts=bm.verts)
        elif axis == "y":
            bmesh.ops.transform(bm, matrix=Matrix.Rotation(math.pi / 2, 4, 'X'), verts=bm.verts)
        for v in bm.verts:
            v.co += Vector(centre)
        return put(name, bm, mat)

    def quad(name, corners, mat):
        """A flat textured quad: corners counter-clockwise seen from the front, UV (0,0) to (1,1)."""
        bm = bmesh.new()
        vs = [bm.verts.new(c) for c in corners]
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
        n = 0
        for o in bpy.data.objects:
            if o.type == 'MESH':
                n += sum(len(p.vertices) - 2 for p in o.data.polygons)
        return n

    results = {}

    # ---------------------------------------------------------------- solar panels: bare (flat), roof mount (raised on rails) and ground mount (tilted rack)
    def strut(name, p0, p1, thick, mat):
        """A square bar from point p0 to point p1."""
        a, b = Vector(p0), Vector(p1)
        d = b - a
        ob = box(name, (thick, thick, d.length), (0, 0, 0), mat)
        ob.data.transform(d.to_track_quat('Z', 'Y').to_matrix().to_4x4())
        ob.data.transform(Matrix.Translation((a + b) / 2))
        return ob

    def panel_parts(pid, w, l, mats):
        """The panel itself, lying flat and centred, its underside at z = 0 (no wires: it is a bare module)."""
        fw = FRAME if w > 0.6 else 0.022
        t = 0.04 if w > 0.6 else 0.032
        frame, back, cells, conn = mats
        parts = []
        for sx in (-1, 1):
            parts.append(box("RailL%d" % sx, (fw, l, t), (sx * (w / 2 - fw / 2), 0, t / 2), frame, 0.004))
        for sy in (-1, 1):
            parts.append(box("RailS%d" % sy, (w - 2 * fw, fw, t), (0, sy * (l / 2 - fw / 2), t / 2), frame, 0.004))
        parts.append(box("Laminate", (w - 2 * fw + 0.004, l - 2 * fw + 0.004, t * 0.5), (0, 0, t * 0.5 - t * 0.04), back, 0.0))
        zt = t * 0.5 - t * 0.04 + t * 0.25 + 0.0006
        hw, hl = (w - 2 * fw) / 2, (l - 2 * fw) / 2
        parts.append(quad("CellFace", [(-hw, -hl, zt), (hw, -hl, zt), (hw, hl, zt), (-hw, hl, zt)], cells))
        lip = 0.006
        for sx in (-1, 1):
            parts.append(box("LipL%d" % sx, (lip, l - 2 * fw, 0.004), (sx * (w / 2 - fw - lip / 2 + 0.002), 0, t - 0.002), frame))
        for sy in (-1, 1):
            parts.append(box("LipS%d" % sy, (w - 2 * fw, lip, 0.004), (0, sy * (l / 2 - fw - lip / 2 + 0.002), t - 0.002), frame))
        parts.append(box("JBox", (0.11, 0.05, 0.018), (0, l / 2 - fw - 0.06, -0.006), conn, 0.003))   # the junction box on the back, under the panel
        return parts, t

    def join_one(parts):
        bpy.ops.object.select_all(action='DESELECT')
        for o in parts:
            o.select_set(True)
        bpy.context.view_layer.objects.active = parts[0]
        bpy.ops.object.join()
        return parts[0]

    for pid, (_, w, l, cols, rows) in PANELS.items():
        size = pid.split("_")[3]   # 100w, 200w, 400w
        for variant in ("flat", "roof_rack", "ground_rack", "stack_4", "stack_8"):
            reset()
            frame = material("Alum_Frame", (0.74, 0.76, 0.80), 0.85, 0.32)
            back = material("Backsheet", (0.86, 0.87, 0.88), 0.0, 0.7)
            cells = material("PV_Cells", (1, 1, 1), 0.0, 0.18, tex=os.path.join(WORK, pid + "_cells.png"))
            conn = material("Connector", (0.06, 0.06, 0.07), 0.0, 0.45)
            steel = material("Mount_Steel", (0.50, 0.52, 0.55), 0.8, 0.4)
            dark = material("Mount_Dark", (0.08, 0.08, 0.09), 0.3, 0.5)
            foam = material("Foam", (0.12, 0.12, 0.13), 0.0, 0.9)
            strap = material("Strap", (0.10, 0.25, 0.60), 0.0, 0.5)
            wood = material("Wood", (0.55, 0.40, 0.24), 0.0, 0.8)
            if variant.startswith("stack_"):
                count = int(variant.split("_")[1])
                vid = pid + "_stack_" + str(count)
                tt = 0.04 if w > 0.6 else 0.032
                pitch = tt + 0.006
                base = 0.05
                allparts = []
                for i in range(count):
                    parts, _t = panel_parts(pid, w, l, (frame, back, cells, conn))
                    one = join_one(parts)
                    one.data.transform(Matrix.Translation((0, 0, base + i * pitch)))
                    allparts.append(one)
                top = base + (count - 1) * pitch + tt
                for sy in (-1, 1):
                    allparts.append(box("Runner", (w * 0.92, 0.08, base), (0, sy * (l / 2 - 0.2), base / 2), wood, 0.003))
                for sx in (-1, 1):
                    for sy in (-1, 1):
                        allparts.append(box("Corner", (0.05, 0.05, top - base + 0.02), (sx * (w / 2 - 0.012), sy * (l / 2 - 0.012), (top + base) / 2), foam, 0.004))
                for sy in (-1, 1):
                    yy = sy * l * 0.22
                    allparts.append(box("StrapTop", (w + 0.014, 0.022, 0.004), (0, yy, top + 0.004), strap))
                    for sx in (-1, 1):
                        allparts.append(box("StrapSide", (0.004, 0.022, top - base + 0.012), (sx * (w / 2 + 0.008), yy, (top + base) / 2), strap))
                export(allparts, os.path.join(out_dir, vid + ".glb"))
                results[vid] = tris()
                continue
            parts, t = panel_parts(pid, w, l, (frame, back, cells, conn))
            kind = variant.split("_")[0]
            with_panel = variant in ("flat", "roof_array", "ground_array")
            vid = pid if variant == "flat" else "electricity_solar_%s_%s_%s" % ("array" if with_panel else "mount", size, kind)
            if not with_panel:
                for o in parts:
                    bpy.data.objects.remove(o, do_unlink=True)   # the rack alone: the panel is fitted in the game
                panel = None
            else:
                panel = join_one(parts)
            if variant == "flat":
                export([panel], os.path.join(out_dir, vid + ".glb"))
            elif kind == "roof":
                # flush mount: the panel rides on two rails, held by L feet with flashing plates (it follows the roof; the pivot is the roof surface)
                lift = 0.10
                if panel is not None:
                    panel.data.transform(Matrix.Translation((0, 0, lift)))
                rest = []
                for sx in (-1, 1):
                    rest.append(box("Rail%d" % sx, (0.04, l * 0.94, 0.035), (sx * w * 0.28, 0, lift - 0.0175), steel, 0.003))
                ys = [-(l / 2 - 0.12), (l / 2 - 0.12)] if l < 1.0 else [-(l / 2 - 0.12), 0.0, (l / 2 - 0.12)]
                for sx in (-1, 1):
                    for y in ys:
                        x = sx * w * 0.28
                        rest.append(box("Flash", (0.11, 0.11, 0.006), (x, y, 0.003), dark, 0.002))
                        rest.append(box("FootUp", (0.035, 0.035, lift - 0.035), (x, y, (lift - 0.035) / 2 + 0.006), steel, 0.002))
                        rest.append(box("FootCap", (0.06, 0.05, 0.012), (x, y, lift - 0.042), steel, 0.002))
                        rest.append(cylinder("Bolt", 0.009, 0.01, "z", (x, y + 0.035, 0.011), dark, 6))
                export(([panel] if panel is not None else []) + rest, os.path.join(out_dir, vid + ".glb"))
            else:
                # ground mount: the panel tilted 30 degrees on a steel rack, the low edge a little off the ground, on foot plates
                tilt = math.radians(30)
                low = 0.30
                shift = low + (l / 2) * math.sin(tilt)
                if panel is not None:
                    panel.data.transform(Matrix.Rotation(tilt, 4, 'X'))
                    panel.data.transform(Matrix.Translation((0, 0, shift)))
                rest = []
                inset = 0.12
                def under(sv):
                    """The underside of the panel at distance sv along its slope from the middle: (y, z)."""
                    return (sv * math.cos(tilt), sv * math.sin(tilt) + shift - 0.012)
                xs = (-(w / 2 - 0.14), (w / 2 - 0.14))
                sf, sb = -(l / 2 - inset), (l / 2 - inset)
                (yf, zf), (yb, zb) = under(sf), under(sb)
                for x in xs:
                    rest.append(strut("LegF", (x, yf, 0.01), (x, yf, zf), 0.04, steel))
                    rest.append(strut("LegB", (x, yb, 0.01), (x, yb, zb), 0.04, steel))
                    rest.append(strut("Brace", (x, yf, zf * 0.45), (x, yb, zb * 0.55), 0.03, steel))
                    for y in (yf, yb):
                        rest.append(box("Foot", (0.12, 0.12, 0.012), (x, y, 0.006), dark, 0.002))
                for sv in (sf, sb):
                    y, z = under(sv)
                    pur = box("Purlin", (w * 0.92, 0.04, 0.04), (0, 0, 0), steel, 0.003)
                    pur.data.transform(Matrix.Rotation(tilt, 4, 'X'))
                    pur.data.transform(Matrix.Translation((0, y, z - 0.012)))
                    rest.append(pur)
                export(([panel] if panel is not None else []) + rest, os.path.join(out_dir, vid + ".glb"))
            results[vid] = tris()

    # ---------------------------------------------------------------- outdoor breaker boxes (front faces -y, back wall at y = 0, bottom of the box at z = 0)
    for bid, (_, amps, w, h, dep, accent) in BREAKERS.items():
        reset()
        steel = material("Enclosure", (0.58, 0.60, 0.62), 0.55, 0.45)
        door = material("Door", (0.66, 0.68, 0.70), 0.5, 0.42)
        dark = material("Dark", (0.05, 0.05, 0.06), 0.3, 0.5)
        brass = material("Brass", (0.75, 0.6, 0.22), 0.9, 0.35)
        stripe = material("Stripe", tuple(c / 255.0 for c in accent), 0.0, 0.5)
        label = material("Label", (1, 1, 1), 0.0, 0.6, tex=os.path.join(WORK, bid + "_label.png"))
        db = dep - 0.026          # body depth; the door and its lip add the rest
        parts = []
        parts.append(box("Body", (w, db, h), (0, -db / 2, h / 2), steel, 0.006))
        parts.append(box("Door", (w - 0.016, 0.016, h - 0.016), (0, -db - 0.008, h / 2), door, 0.004))
        parts.append(box("DoorPanel", (w * 0.8, 0.006, h * 0.56), (0, -db - 0.019, h * 0.40), door, 0.003))   # the raised centre of the door
        parts.append(box("Hood", (w + 0.03, dep + 0.012, 0.014), (0, -(dep + 0.012) / 2 + 0.004, h + 0.007), steel, 0.004))   # the rain hood over the top
        parts.append(box("HoodLip", (w + 0.03, 0.012, 0.03), (0, -dep - 0.006, h - 0.004), steel, 0.003))
        parts.append(box("Stripe", (w * 0.8, 0.003, 0.016), (0, -db - 0.0225, h - 0.045), stripe))
        # the printed label
        lw, lh = w * 0.74, w * 0.74 * 0.5
        y = -db - 0.0235
        zc = h * 0.62
        parts.append(quad("Label", [(-lw / 2, y, zc - lh / 2), (lw / 2, y, zc - lh / 2), (lw / 2, y, zc + lh / 2), (-lw / 2, y, zc + lh / 2)], label))
        # hinges down the left edge
        hz = [h * 0.15, h * 0.5, h * 0.85] if h > 0.45 else [h * 0.2, h * 0.8]
        for i, z in enumerate(hz):
            parts.append(cylinder("Hinge%d" % i, 0.007, 0.05, "z", (-w / 2 + 0.004, -db - 0.012, z), dark, 8))
        # latch(es) on the right edge and a padlock on the lower one
        lz = [h * 0.22] if h < 0.6 else [h * 0.22, h * 0.78]
        for i, z in enumerate(lz):
            parts.append(box("Latch%d" % i, (0.03, 0.014, 0.07), (w / 2 - 0.028, -db - 0.024, z), dark, 0.003))
            parts.append(box("LatchHasp%d" % i, (0.012, 0.01, 0.045), (w / 2 - 0.028, -db - 0.034, z), brass, 0.002))
        pz = lz[0] - 0.055
        parts.append(cylinder("LockShackle", 0.005, 0.03, "z", (w / 2 - 0.028, -db - 0.034, pz + 0.04), brass, 8))
        parts.append(box("Padlock", (0.034, 0.018, 0.04), (w / 2 - 0.028, -db - 0.034, pz), brass, 0.004))
        # conduit hubs under the box
        for i, sx in enumerate((-0.28, 0.28)):
            parts.append(cylinder("Hub%d" % i, 0.017, 0.045, "z", (sx * w, -db / 2, -0.0225), dark, 10))
            parts.append(cylinder("Nut%d" % i, 0.022, 0.012, "z", (sx * w, -db / 2, 0.008), dark, 6))
        # mounting ears top and bottom
        for z in (h * 0.06, h * 0.94):
            parts.append(box("Ear%s" % z, (w + 0.05, 0.004, 0.022), (0, -0.002, z), steel, 0.0015))
        export(parts, os.path.join(out_dir, bid + ".glb"))
        results[bid] = tris()

    with open(os.path.join(out_dir, "tris.txt"), "w") as f:
        for k, v in results.items():
            f.write("%s %d\n" % (k, v))


# ------------------------------------------------------------------------------------------------ driver
def find_blender():
    for p in (r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe", r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe", "blender"):
        if os.path.exists(p) or p == "blender":
            return p
    return "blender"


def main():
    if "--blender" in sys.argv:
        out = sys.argv[sys.argv.index("--") + 1]
        blender_main(out)
        return
    make_textures()
    out = os.path.join(WORK, "glb")
    os.makedirs(out, exist_ok=True)
    cmd = [find_blender(), "--background", "--python", os.path.abspath(__file__), "--", out, "--blender"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print((r.stdout + r.stderr)[-2500:])
    print(open(os.path.join(out, "tris.txt")).read())


if __name__ == "__main__":
    main()
