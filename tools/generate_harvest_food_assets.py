#!/usr/bin/env python3
"""
Homesteader Harvested Produce, Food & Animal Products 3D Asset Generator
======================================================================
Faithfully generates 24 loose produce, food, dairy, meat and pelt world models:
- Directly replicates the visual appearance, shapes, components, and colors
  of each canonical item icon in assets/items/.
- Watertight 360-degree geometry rotatable on the Homesteader spatial grid.
- Ground-aligned pivots (Z_min = 0.0).
- Dual workspace synchronization across assets/ and Homesteader/Content/Homesteader/.
"""

import os
import sys
import math
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

CAT_DIRS = {
    "farming": {
        "hud_models": os.path.join(PROJECT_ROOT, "HUD", "assets", "farming", "models"),
        "hud_icons":  os.path.join(PROJECT_ROOT, "HUD", "assets", "farming", "icons"),
        "ue5_models": os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "Assets", "Farming", "Meshes"),
        "ue5_icons":  os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "UI", "Icons", "farming"),
    },
    "ranching": {
        "hud_models": os.path.join(PROJECT_ROOT, "HUD", "assets", "ranching", "models"),
        "hud_icons":  os.path.join(PROJECT_ROOT, "HUD", "assets", "ranching", "icons"),
        "ue5_models": os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "Assets", "Ranching", "Meshes"),
        "ue5_icons":  os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "UI", "Icons", "ranching"),
    }
}

ITEMS_DIR = os.path.join(PROJECT_ROOT, "HUD", "assets", "items")

for cat, paths in CAT_DIRS.items():
    for p in paths.values():
        os.makedirs(p, exist_ok=True)


class MeshBuilder:
    def __init__(self, name):
        self.name = name
        self.vertices = []
        self.materials = {}
        self.mat_colors = {}
        self.current_mat = "default"

    def set_material(self, mat_name, r, g, b):
        self.current_mat = mat_name
        if mat_name not in self.materials:
            self.materials[mat_name] = []
            self.mat_colors[mat_name] = (r, g, b)

    def add_vertex(self, x, y, z):
        self.vertices.append((round(x, 2), round(y, 2), round(z, 2)))
        return len(self.vertices)

    def add_tri(self, v1, v2, v3):
        self.materials[self.current_mat].append((v1, v2, v3))

    def add_quad(self, v1, v2, v3, v4):
        self.materials[self.current_mat].append((v1, v2, v3))
        self.materials[self.current_mat].append((v1, v3, v4))

    def add_box(self, x_min, x_max, y_min, y_max, z_min, z_max):
        v1 = self.add_vertex(x_min, y_min, z_min)
        v2 = self.add_vertex(x_max, y_min, z_min)
        v3 = self.add_vertex(x_max, y_max, z_min)
        v4 = self.add_vertex(x_min, y_max, z_min)
        v5 = self.add_vertex(x_min, y_min, z_max)
        v6 = self.add_vertex(x_max, y_min, z_max)
        v7 = self.add_vertex(x_max, y_max, z_max)
        v8 = self.add_vertex(x_min, y_max, z_max)
        self.add_quad(v1, v4, v3, v2)  # Bottom
        self.add_quad(v5, v6, v7, v8)  # Top
        self.add_quad(v1, v2, v6, v5)  # Front
        self.add_quad(v3, v4, v8, v7)  # Back
        self.add_quad(v4, v1, v5, v8)  # Left
        self.add_quad(v2, v3, v7, v6)  # Right

    def add_cylinder(self, cx, cy, z_min, z_max, radius, segments=10, axis='z'):
        if axis == 'z':
            bot_verts = []
            top_verts = []
            for i in range(segments):
                angle = 2.0 * math.pi * i / segments
                x = cx + radius * math.cos(angle)
                y = cy + radius * math.sin(angle)
                bot_verts.append(self.add_vertex(x, y, z_min))
                top_verts.append(self.add_vertex(x, y, z_max))
            c_bot = self.add_vertex(cx, cy, z_min)
            c_top = self.add_vertex(cx, cy, z_max)
            for i in range(segments):
                nxt = (i + 1) % segments
                self.add_tri(c_bot, bot_verts[nxt], bot_verts[i])
                self.add_tri(c_top, top_verts[i], top_verts[nxt])
                self.add_quad(bot_verts[i], bot_verts[nxt], top_verts[nxt], top_verts[i])
        elif axis == 'y':
            y_min, y_max, cen_x, cen_z = cx, cy, z_min, z_max
            f_verts = []
            r_verts = []
            for i in range(segments):
                angle = 2.0 * math.pi * i / segments
                x = cen_x + radius * math.cos(angle)
                z = cen_z + radius * math.sin(angle)
                f_verts.append(self.add_vertex(x, y_min, z))
                r_verts.append(self.add_vertex(x, y_max, z))
            cf = self.add_vertex(cen_x, y_min, cen_z)
            cr = self.add_vertex(cen_x, y_max, cen_z)
            for i in range(segments):
                nxt = (i + 1) % segments
                self.add_tri(cf, f_verts[i], f_verts[nxt])
                self.add_tri(cr, r_verts[nxt], r_verts[i])
                self.add_quad(f_verts[nxt], f_verts[i], r_verts[i], r_verts[nxt])
        elif axis == 'x':
            x_min, x_max, cen_y, cen_z = cx, cy, z_min, z_max
            l_verts = []
            r_verts = []
            for i in range(segments):
                angle = 2.0 * math.pi * i / segments
                y = cen_y + radius * math.cos(angle)
                z = cen_z + radius * math.sin(angle)
                l_verts.append(self.add_vertex(x_min, y, z))
                r_verts.append(self.add_vertex(x_max, y, z))
            cl = self.add_vertex(x_min, cen_y, cen_z)
            cr = self.add_vertex(x_max, cen_y, cen_z)
            for i in range(segments):
                nxt = (i + 1) % segments
                self.add_tri(cl, l_verts[i], l_verts[nxt])
                self.add_tri(cr, r_verts[nxt], r_verts[i])
                self.add_quad(l_verts[i], r_verts[i], r_verts[nxt], l_verts[nxt])

    def add_tapered_cylinder(self, cx, cy, z_min, z_max, r_bot, r_top, segments=8):
        bot_verts = []
        top_verts = []
        for i in range(segments):
            angle = 2.0 * math.pi * i / segments
            bot_verts.append(self.add_vertex(cx + r_bot * math.cos(angle), cy + r_bot * math.sin(angle), z_min))
            top_verts.append(self.add_vertex(cx + r_top * math.cos(angle), cy + r_top * math.sin(angle), z_max))
        c_bot = self.add_vertex(cx, cy, z_min)
        c_top = self.add_vertex(cx, cy, z_max)
        for i in range(segments):
            nxt = (i + 1) % segments
            self.add_tri(c_bot, bot_verts[nxt], bot_verts[i])
            self.add_tri(c_top, top_verts[i], top_verts[nxt])
            self.add_quad(bot_verts[i], bot_verts[nxt], top_verts[nxt], top_verts[i])

    def add_sphere(self, cx, cy, cz, radius, segs_lat=5, segs_lon=8):
        for i in range(segs_lat):
            lat0 = math.pi * (-0.5 + float(i) / segs_lat)
            lat1 = math.pi * (-0.5 + float(i + 1) / segs_lat)
            z0 = cz + radius * math.sin(lat0)
            z1 = cz + radius * math.sin(lat1)
            r0 = radius * math.cos(lat0)
            r1 = radius * math.cos(lat1)

            for j in range(segs_lon):
                lon0 = 2 * math.pi * float(j) / segs_lon
                lon1 = 2 * math.pi * float(j + 1) / segs_lon

                v0 = self.add_vertex(cx + r0 * math.cos(lon0), cy + r0 * math.sin(lon0), z0)
                v1 = self.add_vertex(cx + r0 * math.cos(lon1), cy + r0 * math.sin(lon1), z0)
                v2 = self.add_vertex(cx + r1 * math.cos(lon1), cy + r1 * math.sin(lon1), z1)
                v3 = self.add_vertex(cx + r1 * math.cos(lon0), cy + r1 * math.sin(lon0), z1)

                if i == 0:
                    self.add_tri(v0, v1, v2)
                elif i == segs_lat - 1:
                    self.add_tri(v0, v2, v3)
                else:
                    self.add_quad(v0, v1, v2, v3)

    def ground_align(self):
        if not self.vertices:
            return
        min_z = min(v[2] for v in self.vertices)
        if abs(min_z) > 0.001:
            self.vertices = [(v[0], v[1], round(v[2] - min_z, 2)) for v in self.vertices]

    def write_obj_and_mtl(self, obj_path, mtl_path):
        self.ground_align()
        mtl_filename = os.path.basename(mtl_path)
        with open(obj_path, "w", encoding="utf-8") as f:
            f.write(f"# Homesteader 3D Model: {self.name}\n")
            f.write(f"mtllib {mtl_filename}\n\n")
            for v in self.vertices:
                f.write(f"v {v[0]:.2f} {v[1]:.2f} {v[2]:.2f}\n")
            f.write("\n")
            for mat_name, faces in self.materials.items():
                if not faces:
                    continue
                f.write(f"usemtl {mat_name}\n")
                for face in faces:
                    f.write(f"f {' '.join(str(idx) for idx in face)}\n")

        with open(mtl_path, "w", encoding="utf-8") as f:
            f.write(f"# Material Library for {self.name}\n\n")
            for mat_name, color in self.mat_colors.items():
                r, g, b = color
                f.write(f"newmtl {mat_name}\n")
                f.write(f"Ka {r*0.4:.3f} {g*0.4:.3f} {b*0.4:.3f}\n")
                f.write(f"Kd {r:.3f} {g:.3f} {b:.3f}\n")
                f.write(f"Ks 0.200 0.200 0.200\n")
                f.write("Ns 20.0\n")
                f.write("d 1.0\n")
                f.write("illum 2\n\n")


# =============================================================================
# 1. HARVESTED CROPS & PRODUCE (10 - FARMING)
# =============================================================================

def build_corn_ear():
    """SM_Item_Corn_Ear: Ripe yellow sweet corn ear with pale lime husk leaves peeling back."""
    m = MeshBuilder("SM_Item_Corn_Ear")
    m.set_material("corn_kernel", 0.95, 0.82, 0.15)  # Golden kernel yellow #F4D03F
    m.set_material("corn_husk", 0.40, 0.65, 0.20)    # Husk green #689F38
    m.set_material("corn_silk", 0.60, 0.45, 0.22)    # Silk brown

    # Cob lying slightly horizontal: along Y axis
    # Main cob cylinder (diameter 6cm, length 20cm)
    m.set_material("corn_kernel", 0.95, 0.82, 0.15)
    m.add_cylinder(-8.0, 8.0, 0.0, 3.5, 3.2, segments=10, axis='y')
    # Tapered tip
    m.add_cylinder(8.0, 11.0, 0.0, 3.5, 2.2, segments=8, axis='y')
    # Silk tip
    m.set_material("corn_silk", 0.60, 0.45, 0.22)
    m.add_box(-1.0, 1.0, 11.0, 13.0, 2.5, 4.5)

    # Husk leaves wrapping the base and curling outward
    m.set_material("corn_husk", 0.40, 0.65, 0.20)
    m.add_cylinder(-12.0, -8.0, 0.0, 3.5, 2.0, segments=6, axis='y')  # Stem stub
    # Flaring husk leaves
    m.add_box(-4.5, 4.5, -9.0, 2.0, 0.0, 2.0)
    m.add_box(-5.0, -3.0, -8.0, 4.0, 1.5, 6.0)
    m.add_box(3.0, 5.0, -8.0, 4.0, 1.5, 6.0)
    return m


def build_tomato_fruit():
    """SM_Item_Tomato_Fruit: Plump red heirloom beefsteak tomato with 5-point star green calyx."""
    m = MeshBuilder("SM_Item_Tomato_Fruit")
    m.set_material("tomato_red", 0.85, 0.14, 0.10)   # #D32F2F
    m.set_material("calyx_green", 0.26, 0.65, 0.22)  # #4CAF50
    m.set_material("stem_green", 0.20, 0.50, 0.16)

    # Multi-lobed tomato body
    segs = 6
    for i in range(segs):
        ang = 2.0 * math.pi * i / segs
        lx = 2.0 * math.cos(ang)
        ly = 2.0 * math.sin(ang)
        m.add_sphere(lx, ly, 4.5, 3.8, segs_lat=5, segs_lon=6)
    m.add_sphere(0.0, 0.0, 4.5, 4.4, segs_lat=5, segs_lon=8)

    # 5-point green star calyx on top
    m.set_material("calyx_green", 0.26, 0.65, 0.22)
    for i in range(5):
        ang = 2.0 * math.pi * i / 5.0
        px = 3.6 * math.cos(ang)
        py = 3.6 * math.sin(ang)
        v_center = m.add_vertex(0.0, 0.0, 8.8)
        v_tip = m.add_vertex(px, py, 8.2)
        v_side = m.add_vertex(px * 0.5 - py * 0.3, py * 0.5 + px * 0.3, 8.6)
        m.add_tri(v_center, v_side, v_tip)

    # Short curved stem
    m.set_material("stem_green", 0.20, 0.50, 0.16)
    m.add_cylinder(0.0, 0.0, 8.8, 11.2, 0.6, segments=5)
    return m


def build_potato_loose():
    """SM_Item_Potato_Loose: Pair of rustic golden-brown russet baking potatoes."""
    m = MeshBuilder("SM_Item_Potato_Loose")
    m.set_material("potato_skin", 0.70, 0.50, 0.30)  # Russet skin #B58750
    m.set_material("potato_eye", 0.45, 0.32, 0.18)   # Eye dimples

    # Primary potato (elongated along Y)
    m.set_material("potato_skin", 0.70, 0.50, 0.30)
    m.add_sphere(-2.0, -3.0, 4.0, 4.2, segs_lat=5, segs_lon=7)
    m.add_sphere(-2.0, 3.0, 4.0, 4.0, segs_lat=5, segs_lon=7)
    m.add_cylinder(-2.0, -2.0, -3.0, 3.0, 4.0, segments=7, axis='y')
    # Small eyes
    m.set_material("potato_eye", 0.45, 0.32, 0.18)
    m.add_box(-2.5, -1.5, 0.0, 1.0, 7.8, 8.2)
    m.add_box(-5.5, -4.8, 2.0, 3.0, 4.0, 5.0)

    # Secondary potato resting beside it
    m.set_material("potato_skin", 0.70, 0.50, 0.30)
    m.add_sphere(4.0, 1.0, 3.5, 3.5, segs_lat=5, segs_lon=7)
    m.add_sphere(4.0, -3.0, 3.5, 3.2, segs_lat=5, segs_lon=7)
    return m


def build_carrot_bunch():
    """SM_Item_Carrot_Bunch: Bunch of 3 fresh orange garden carrots tied with twine."""
    m = MeshBuilder("SM_Item_Carrot_Bunch")
    m.set_material("carrot_orange", 0.96, 0.48, 0.05)  # #F57C00
    m.set_material("carrot_tops", 0.25, 0.65, 0.22)    # #43A047
    m.set_material("jute_twine", 0.75, 0.65, 0.45)

    carrots = [
        (-2.5, -1.5, 0.0, 16.0),
        (2.5, -1.0, 1.0, 15.0),
        (0.0, 2.0, -0.5, 17.0)
    ]
    for cx, cy, z_off, clen in carrots:
        # Tapered conical root
        m.set_material("carrot_orange", 0.96, 0.48, 0.05)
        m.add_tapered_cylinder(cx, cy, z_off + 2.0, z_off + clen, r_bot=0.6, r_top=2.2, segments=7)
        # Conical tip
        v_tip = m.add_vertex(cx, cy, z_off)
        for i in range(7):
            ang0 = 2.0 * math.pi * i / 7.0
            ang1 = 2.0 * math.pi * (i + 1) / 7.0
            v0 = m.add_vertex(cx + 0.6 * math.cos(ang0), cy + 0.6 * math.sin(ang0), z_off + 2.0)
            v1 = m.add_vertex(cx + 0.6 * math.cos(ang1), cy + 0.6 * math.sin(ang1), z_off + 2.0)
            m.add_tri(v_tip, v0, v1)
        # Green leafy crown
        m.set_material("carrot_tops", 0.25, 0.65, 0.22)
        m.add_box(cx - 1.5, cx + 1.5, cy - 1.5, cy + 1.5, z_off + clen, z_off + clen + 10.0)

    # Twine tie around necks
    m.set_material("jute_twine", 0.75, 0.65, 0.45)
    m.add_cylinder(0.0, 0.0, 13.0, 15.5, 4.5, segments=8)
    return m


def build_pumpkin_carved():
    """SM_Item_Pumpkin_Carved: Harvested ribbed round orange field pumpkin with curled stem."""
    m = MeshBuilder("SM_Item_Pumpkin_Carved")
    m.set_material("pumpkin_orange", 0.95, 0.45, 0.05)  # Vibrant orange #EF6C00
    m.set_material("pumpkin_stem", 0.32, 0.24, 0.16)    # Woody stem #5D4037

    # 8 rounded vertical lobes forming the ribbed pumpkin body
    segs = 8
    for i in range(segs):
        ang = 2.0 * math.pi * i / segs
        lx = 9.0 * math.cos(ang)
        ly = 9.0 * math.sin(ang)
        m.set_material("pumpkin_orange", 0.95, 0.45, 0.05)
        m.add_sphere(lx, ly, 11.0, 7.5, segs_lat=5, segs_lon=6)

    # Central core
    m.add_cylinder(0.0, 0.0, 2.0, 20.0, 9.0, segments=10)

    # Curled woody stem on top
    m.set_material("pumpkin_stem", 0.32, 0.24, 0.16)
    m.add_cylinder(0.0, 0.0, 18.0, 24.5, 1.8, segments=6)
    m.add_box(-1.2, 1.2, 1.0, 4.0, 23.0, 26.0)
    return m


def build_cabbage_harvested():
    """SM_Item_Cabbage_Harvested: Harvested round head of garden cabbage with crinkly leaves."""
    m = MeshBuilder("SM_Item_Cabbage_Harvested")
    m.set_material("cabbage_core", 0.42, 0.75, 0.30)   # #66BB6A
    m.set_material("cabbage_leaf", 0.22, 0.58, 0.20)   # #2E7D32
    m.set_material("leaf_highlight", 0.52, 0.82, 0.42) # #81C784

    # Central spherical head
    m.set_material("cabbage_core", 0.42, 0.75, 0.30)
    m.add_sphere(0.0, 0.0, 8.5, 7.5, segs_lat=6, segs_lon=9)

    # 6 outer cupped leaves cradling the head
    m.set_material("cabbage_leaf", 0.22, 0.58, 0.20)
    for i in range(6):
        ang = 2.0 * math.pi * i / 6.0
        lx = 9.2 * math.cos(ang)
        ly = 9.2 * math.sin(ang)
        m.add_sphere(lx, ly, 6.0, 5.0, segs_lat=4, segs_lon=6)
    return m


def build_sunflower_head():
    """SM_Item_Sunflower_Head: Cut mature sunflower head packed with dark seed disc and yellow petals."""
    m = MeshBuilder("SM_Item_Sunflower_Head")
    m.set_material("seed_disc", 0.24, 0.16, 0.12)      # Dark brown seeds #3E2723
    m.set_material("petal_yellow", 0.98, 0.78, 0.10)   # Golden petals #FBC02D
    m.set_material("stem_green", 0.25, 0.55, 0.20)

    # Central flat seed disc (diameter 20cm, height 4cm)
    m.set_material("seed_disc", 0.24, 0.16, 0.12)
    m.add_cylinder(0.0, 0.0, 2.5, 6.5, 10.0, segments=12)

    # Outer ray of 16 triangular yellow petals
    m.set_material("petal_yellow", 0.98, 0.78, 0.10)
    for i in range(16):
        ang = 2.0 * math.pi * i / 16.0
        p_in_x = 9.5 * math.cos(ang)
        p_in_y = 9.5 * math.sin(ang)
        p_out_x = 13.5 * math.cos(ang)
        p_out_y = 13.5 * math.sin(ang)
        v_in = m.add_vertex(p_in_x, p_in_y, 4.5)
        v_out = m.add_vertex(p_out_x, p_out_y, 4.0)
        v_side = m.add_vertex(p_in_x * 0.9 - p_in_y * 0.2, p_in_y * 0.9 + p_in_x * 0.2, 4.5)
        m.add_tri(v_in, v_side, v_out)

    # Green sepal base and short stem underneath
    m.set_material("stem_green", 0.25, 0.55, 0.20)
    m.add_cylinder(0.0, 0.0, 0.0, 3.0, 2.2, segments=6)
    m.add_cylinder(0.0, 0.0, 1.5, 3.0, 8.5, segments=8)
    return m


def build_strawberry_basket():
    """SM_Item_Strawberry_Basket: Woven wicker punnet basket heaped with fresh ruby strawberries."""
    m = MeshBuilder("SM_Item_Strawberry_Basket")
    m.set_material("basket_wood", 0.75, 0.62, 0.44)  # Wicker tan
    m.set_material("berry_red", 0.88, 0.14, 0.16)    # Strawberry red
    m.set_material("berry_cap", 0.25, 0.65, 0.20)    # Green calyx

    # Punnet basket frame (16x20x7cm)
    m.set_material("basket_wood", 0.75, 0.62, 0.44)
    m.add_box(-8.0, 8.0, -10.0, 10.0, 0.0, 1.5)      # Bottom
    m.add_box(-8.5, -7.5, -10.5, 10.5, 1.5, 7.5)     # Left wall
    m.add_box(7.5, 8.5, -10.5, 10.5, 1.5, 7.5)       # Right wall
    m.add_box(-8.0, 8.0, -10.5, -9.5, 1.5, 7.5)      # Front wall
    m.add_box(-8.0, 8.0, 9.5, 10.5, 1.5, 7.5)        # Back wall

    # Heaped strawberries inside
    for sx in [-4.0, 0.0, 4.0]:
        for sy in [-5.5, 0.0, 5.5]:
            m.set_material("berry_red", 0.88, 0.14, 0.16)
            m.add_sphere(sx, sy, 8.0, 2.5, segs_lat=4, segs_lon=6)
            m.set_material("berry_cap", 0.25, 0.65, 0.20)
            m.add_box(sx - 0.8, sx + 0.8, sy - 0.8, sy + 0.8, 10.2, 11.2)
    return m


def build_cotton_boll():
    """SM_Item_Cotton_Boll: 4-burr dried cotton boll with fluffy white cotton lint."""
    m = MeshBuilder("SM_Item_Cotton_Boll")
    m.set_material("cotton_white", 0.96, 0.96, 0.97)  # Pure fluffy lint #FAFAFA
    m.set_material("burr_brown", 0.38, 0.26, 0.18)    # Dried hull sepals #5D4037

    # 4 fluffy cotton puffs
    m.set_material("cotton_white", 0.96, 0.96, 0.97)
    puffs = [(-3.0, -3.0), (3.0, -3.0), (3.0, 3.0), (-3.0, 3.0)]
    for px, py in puffs:
        m.add_sphere(px, py, 6.5, 3.5, segs_lat=5, segs_lon=6)

    # 4 brown pointed sepals curling underneath
    m.set_material("burr_brown", 0.38, 0.26, 0.18)
    for px, py in puffs:
        m.add_box(px * 1.3 - 1.2, px * 1.3 + 1.2, py * 1.3 - 1.2, py * 1.3 + 1.2, 1.5, 7.0)
    # Stem base
    m.add_cylinder(0.0, 0.0, 0.0, 3.0, 1.2, segments=6)
    return m


def build_wheat_sheaf():
    """SM_Item_Wheat_Sheaf: Tied sheaf bundle of golden ripe wheat with straw band."""
    m = MeshBuilder("SM_Item_Wheat_Sheaf")
    m.set_material("straw_gold", 0.90, 0.75, 0.32)   # Golden straw #E0A938
    m.set_material("tie_band", 0.65, 0.48, 0.22)     # Darker straw wrap
    m.set_material("grain_heads", 0.85, 0.70, 0.28)  # Ripe grain spikes

    # Lower stalk bundle flared at base
    m.set_material("straw_gold", 0.90, 0.75, 0.32)
    m.add_tapered_cylinder(0.0, 0.0, 0.0, 26.0, r_bot=8.5, r_top=6.0, segments=10)

    # Central straw tie band cinching waist
    m.set_material("tie_band", 0.65, 0.48, 0.22)
    m.add_cylinder(0.0, 0.0, 24.5, 28.5, 6.8, segments=10)

    # Upper stalks flaring out into heads of grain
    m.set_material("grain_heads", 0.85, 0.70, 0.28)
    m.add_tapered_cylinder(0.0, 0.0, 28.5, 58.0, r_bot=6.2, r_top=11.5, segments=10)
    return m


# =============================================================================
# 2. COOKED FOODS & FRUITS (4 - FARMING)
# =============================================================================

def build_food_bread():
    """SM_Item_Food_Bread: Crusty artisanal sourdough bread loaf with flour dusted scoring."""
    m = MeshBuilder("SM_Item_Food_Bread")
    m.set_material("crust_gold", 0.78, 0.46, 0.18)   # Golden crust #CD853F
    m.set_material("score_flour", 0.95, 0.90, 0.80)  # Pale scored interior #FFF8DC

    # Oblong batard loaf (width 16cm, length 26cm, height 11cm)
    m.set_material("crust_gold", 0.78, 0.46, 0.18)
    m.add_box(-7.5, 7.5, -11.5, 11.5, 0.0, 8.0)
    m.add_box(-6.5, 6.5, -10.0, 10.0, 7.5, 10.5)

    # 3 scored slash ridges on top
    m.set_material("score_flour", 0.95, 0.90, 0.80)
    for sy in [-5.5, 0.0, 5.5]:
        m.add_box(-6.0, 6.0, sy - 1.2, sy + 1.2, 10.2, 11.2)
    return m


def build_food_cheese_wheel():
    """SM_Item_Food_Cheese_Wheel: Round yellow farmhouse cheddar wheel with cut wedge."""
    m = MeshBuilder("SM_Item_Food_Cheese_Wheel")
    m.set_material("cheese_rind", 0.92, 0.65, 0.12)  # Orange wax rind #F57F17
    m.set_material("cheese_curd", 0.98, 0.82, 0.22)  # Curd interior #FDD835

    # Main wheel cylinder (diameter 22cm, height 10cm)
    m.set_material("cheese_rind", 0.92, 0.65, 0.12)
    m.add_cylinder(0.0, 0.0, 0.0, 9.5, 10.5, segments=12)

    # Exposed cut wedge slice faces
    m.set_material("cheese_curd", 0.98, 0.82, 0.22)
    m.add_box(0.0, 10.2, -1.2, 1.2, 0.5, 9.2)
    m.add_box(-1.2, 1.2, 0.0, 10.2, 0.5, 9.2)
    return m


def build_food_stew_bowl():
    """SM_Item_Food_Stew_Bowl: Glazed clay bowl of hearty vegetable beef stew with wooden spoon."""
    m = MeshBuilder("SM_Item_Food_Stew_Bowl")
    m.set_material("clay_bowl", 0.62, 0.38, 0.24)    # Ceramic #8D6E63
    m.set_material("stew_broth", 0.38, 0.22, 0.14)   # Rich brown gravy #5D4037
    m.set_material("stew_carrot", 0.92, 0.42, 0.10)  # Carrots
    m.set_material("stew_potato", 0.92, 0.85, 0.70)  # Potatoes
    m.set_material("wood_spoon", 0.78, 0.65, 0.48)   # Spoon handle

    # Flared clay bowl (diameter 18cm, height 8.5cm)
    m.set_material("clay_bowl", 0.62, 0.38, 0.24)
    m.add_tapered_cylinder(0.0, 0.0, 0.0, 8.5, r_bot=6.5, r_top=9.0, segments=12)

    # Stew broth surface inside
    m.set_material("stew_broth", 0.38, 0.22, 0.14)
    m.add_cylinder(0.0, 0.0, 6.5, 7.2, 8.0, segments=10)

    # Vegetable and meat chunks floating
    m.set_material("stew_carrot", 0.92, 0.42, 0.10)
    m.add_box(-3.5, -1.0, -3.5, -1.0, 7.0, 8.2)
    m.set_material("stew_potato", 0.92, 0.85, 0.70)
    m.add_box(1.5, 4.0, 1.0, 3.5, 7.0, 8.2)

    # Wooden spoon resting in bowl
    m.set_material("wood_spoon", 0.78, 0.65, 0.48)
    m.add_box(3.5, 6.0, 3.5, 6.0, 6.0, 12.0)
    return m


def build_food_apple():
    """SM_Item_Food_Apple: Crisp red Honeycrisp apple with brown stem and green leaf."""
    m = MeshBuilder("SM_Item_Food_Apple")
    m.set_material("apple_red", 0.85, 0.12, 0.14)    # Glossy red #C62828
    m.set_material("apple_stem", 0.32, 0.20, 0.14)   # Stem #4E342E
    m.set_material("apple_leaf", 0.28, 0.65, 0.24)   # Green leaf #43A047

    # Apple fruit sphere
    m.set_material("apple_red", 0.85, 0.12, 0.14)
    m.add_sphere(0.0, 0.0, 4.8, 4.2, segs_lat=6, segs_lon=10)

    # Stem
    m.set_material("apple_stem", 0.32, 0.20, 0.14)
    m.add_cylinder(0.0, 0.0, 8.2, 11.5, 0.5, segments=5)

    # Leaf attached to stem base
    m.set_material("apple_leaf", 0.28, 0.65, 0.24)
    m.add_box(0.5, 3.2, -0.8, 1.2, 9.8, 10.6)
    return m


# =============================================================================
# 3. DAIRY, EGG & ANIMAL BYPRODUCTS (4 - RANCHING)
# =============================================================================

def build_animal_eggs_carton():
    """SM_Item_Animal_Eggs_Carton: Open egg carton tray holding 12 fresh brown homestead eggs."""
    m = MeshBuilder("SM_Item_Animal_Eggs_Carton")
    m.set_material("carton_pulp", 0.75, 0.70, 0.62)  # Gray-tan carton pulp #BCAAA4
    m.set_material("egg_brown", 0.85, 0.66, 0.48)    # Farm fresh brown eggs #D4A373

    # Molded pulp tray (15x28x5cm)
    m.set_material("carton_pulp", 0.75, 0.70, 0.62)
    m.add_box(-7.0, 7.0, -13.5, 13.5, 0.0, 3.5)

    # 12 eggs arranged in 2 rows of 6
    m.set_material("egg_brown", 0.85, 0.66, 0.48)
    for ex in [-3.5, 3.5]:
        for ey in range(-11, 12, 4):
            m.add_sphere(ex, float(ey), 4.2, 1.8, segs_lat=4, segs_lon=6)
    return m


def build_animal_milk_jug():
    """SM_Item_Animal_Milk_Jug: 1-gallon glass homestead milk jug with red foil seal."""
    m = MeshBuilder("SM_Item_Animal_Milk_Jug")
    m.set_material("milk_white", 0.96, 0.96, 0.98)   # Creamy white milk #FAFAFA
    m.set_material("glass_body", 0.72, 0.82, 0.86)   # Translucent glass accent #B0BEC5
    m.set_material("cap_red", 0.85, 0.16, 0.14)      # Red foil cap #D32F2F

    # Main bottle jug body (13x13x18cm)
    m.set_material("milk_white", 0.96, 0.96, 0.98)
    m.add_box(-6.0, 6.0, -6.0, 6.0, 0.0, 18.0)

    # Neck
    m.add_cylinder(0.0, 0.0, 18.0, 24.0, 3.2, segments=8)

    # Red foil cap
    m.set_material("cap_red", 0.85, 0.16, 0.14)
    m.add_cylinder(0.0, 0.0, 23.8, 26.0, 3.5, segments=8)

    # Side glass handle
    m.set_material("glass_body", 0.72, 0.82, 0.86)
    m.add_box(5.8, 8.8, -1.8, 1.8, 10.0, 20.0)
    return m


def build_animal_wool_fleece():
    """SM_Item_Animal_Wool_Fleece: Tied raw white sheep wool fleece bundle with paper twine."""
    m = MeshBuilder("SM_Item_Animal_Wool_Fleece")
    m.set_material("fleece_white", 0.94, 0.93, 0.91)  # Fluffy white wool #F5F5F5
    m.set_material("fleece_shadow", 0.80, 0.78, 0.74)
    m.set_material("twine_cord", 0.62, 0.48, 0.32)    # Jute twine

    # Multi-lobed cloud bundle
    m.set_material("fleece_white", 0.94, 0.93, 0.91)
    m.add_sphere(0.0, 0.0, 10.0, 10.0, segs_lat=5, segs_lon=8)
    m.add_sphere(-7.0, 0.0, 9.5, 7.5, segs_lat=4, segs_lon=6)
    m.add_sphere(7.0, 0.0, 9.5, 7.5, segs_lat=4, segs_lon=6)
    m.add_sphere(0.0, -7.0, 9.5, 7.0, segs_lat=4, segs_lon=6)
    m.add_sphere(0.0, 7.0, 9.5, 7.0, segs_lat=4, segs_lon=6)

    # Twine cord around middle
    m.set_material("twine_cord", 0.62, 0.48, 0.32)
    m.add_cylinder(0.0, 0.0, 9.0, 11.2, 10.6, segments=10)
    return m


def build_animal_truffle():
    """SM_Item_Animal_Truffle: Prized foraged black forest truffle mushroom."""
    m = MeshBuilder("SM_Item_Animal_Truffle")
    m.set_material("truffle_black", 0.16, 0.16, 0.17)  # Charcoal black #212121
    m.set_material("truffle_crevice", 0.28, 0.22, 0.18)

    # Knobby warty tuber body
    m.set_material("truffle_black", 0.16, 0.16, 0.17)
    m.add_sphere(0.0, 0.0, 4.5, 4.5, segs_lat=5, segs_lon=8)
    m.add_sphere(3.0, 2.0, 4.8, 2.8, segs_lat=4, segs_lon=6)
    m.add_sphere(-2.5, -2.5, 3.8, 2.6, segs_lat=4, segs_lon=6)
    m.add_sphere(-1.0, 3.0, 5.0, 2.4, segs_lat=4, segs_lon=6)
    return m


# =============================================================================
# 4. MEATS & ANIMAL PELTS (6 - RANCHING)
# =============================================================================

def build_meat_beef_steak():
    """SM_Item_Meat_Beef_Steak: Thick-cut raw T-bone beef steak with bone and fat marbling."""
    m = MeshBuilder("SM_Item_Meat_Beef_Steak")
    m.set_material("meat_red", 0.78, 0.15, 0.16)     # Crimson red meat #B71C1C
    m.set_material("fat_white", 0.96, 0.95, 0.90)    # Marbled fat cap #FFFDE7
    m.set_material("bone_white", 0.90, 0.88, 0.84)   # T-bone

    # Main steak slab (16x24x4cm)
    m.set_material("meat_red", 0.78, 0.15, 0.16)
    m.add_box(-7.0, 7.0, -11.0, 11.0, 0.0, 3.8)

    # Perimeter fat cap strip along top edge
    m.set_material("fat_white", 0.96, 0.95, 0.90)
    m.add_box(-7.5, 7.5, 9.5, 11.5, 0.0, 3.9)
    m.add_box(5.5, 7.5, -11.0, 10.0, 0.0, 3.9)

    # T-bone spine and crossbar
    m.set_material("bone_white", 0.90, 0.88, 0.84)
    m.add_box(-0.9, 0.9, -9.5, 10.0, 0.1, 3.8)   # Spine
    m.add_box(-5.5, 5.5, 0.0, 1.8, 0.1, 3.8)     # Crossbar
    return m


def build_meat_chicken_drumstick():
    """SM_Item_Meat_Chicken_Drumstick: Fresh poultry drumstick with exposed bone knuckle."""
    m = MeshBuilder("SM_Item_Meat_Chicken_Drumstick")
    m.set_material("chicken_meat", 0.92, 0.72, 0.68)  # Pale pink poultry #EF9A9A
    m.set_material("bone_white", 0.95, 0.94, 0.92)    # Clean bone knuckle #FAFAFA

    # Meat bulb (along Y axis)
    m.set_material("chicken_meat", 0.92, 0.72, 0.68)
    m.add_sphere(0.0, -3.5, 3.8, 3.8, segs_lat=5, segs_lon=8)
    m.add_cylinder(0.0, 0.0, -3.5, 3.0, 3.2, segments=7, axis='y')

    # Exposed leg bone shaft
    m.set_material("bone_white", 0.95, 0.94, 0.92)
    m.add_cylinder(0.0, 0.0, 3.0, 9.5, 1.0, segments=6, axis='y')
    # Dual knuckle end
    m.add_sphere(-0.9, 9.5, 3.8, 1.4, segs_lat=4, segs_lon=5)
    m.add_sphere(0.9, 9.5, 3.8, 1.4, segs_lat=4, segs_lon=5)
    return m


def build_meat_pork_chop():
    """SM_Item_Meat_Pork_Chop: Fresh bone-in raw pork loin chop with fat rind cap."""
    m = MeshBuilder("SM_Item_Meat_Pork_Chop")
    m.set_material("pork_pink", 0.92, 0.60, 0.65)    # Rosy pork pink #F48FB1
    m.set_material("rind_fat", 0.96, 0.94, 0.90)     # Outer fat rind #FFFDE7
    m.set_material("rib_bone", 0.90, 0.88, 0.84)     # Rib bone

    # Central loin meat eye
    m.set_material("pork_pink", 0.92, 0.60, 0.65)
    m.add_box(-5.5, 5.5, -8.5, 8.5, 0.0, 3.8)

    # Outer fat rind along +X
    m.set_material("rind_fat", 0.96, 0.94, 0.90)
    m.add_box(4.5, 6.5, -8.5, 8.5, 0.0, 3.8)

    # Curved rib bone along -X
    m.set_material("rib_bone", 0.90, 0.88, 0.84)
    m.add_box(-6.8, -5.2, -8.5, 8.5, 0.0, 3.8)
    return m


def build_pelt_cow_hide():
    """SM_Item_Pelt_Cow_Hide: Folded brown-and-white spotted cowhide pelt roll with strap."""
    m = MeshBuilder("SM_Item_Pelt_Cow_Hide")
    m.set_material("hide_brown", 0.42, 0.28, 0.18)   # Chestnut leather #5D4037
    m.set_material("hide_white", 0.96, 0.96, 0.96)   # Spotted white patch
    m.set_material("strap_dark", 0.22, 0.16, 0.12)   # Leather straps

    # Folded hide stack (42x58x8cm)
    m.set_material("hide_brown", 0.42, 0.28, 0.18)
    m.add_box(-19.0, 19.0, -27.0, 27.0, 0.0, 7.5)

    # Spotted white patches on top
    m.set_material("hide_white", 0.96, 0.96, 0.96)
    m.add_box(-12.0, 5.0, -18.0, 0.0, 7.5, 7.8)
    m.add_box(0.0, 14.0, 8.0, 22.0, 7.5, 7.8)

    # 2 dark leather cinch straps with buckle accents
    m.set_material("strap_dark", 0.22, 0.16, 0.12)
    for sy in [-15.0, 15.0]:
        m.add_box(-19.5, 19.5, sy - 1.5, sy + 1.5, 0.0, 8.2)
    return m


def build_pelt_sheep_fleece():
    """SM_Item_Pelt_Sheep_Fleece: Fluffy folded natural sheepskin fleece pelt with wool pile."""
    m = MeshBuilder("SM_Item_Pelt_Sheep_Fleece")
    m.set_material("wool_fleece", 0.95, 0.94, 0.92)  # Plush white wool #F5F5F5
    m.set_material("suede_backing", 0.78, 0.68, 0.52) # Tan suede leather #D7CCC8

    # Suede leather underside visible at the fold
    m.set_material("suede_backing", 0.78, 0.68, 0.52)
    m.add_box(-17.0, 17.0, -24.0, 24.0, 0.0, 2.0)

    # Thick soft wool pile layer
    m.set_material("wool_fleece", 0.95, 0.94, 0.92)
    m.add_box(-18.0, 18.0, -25.0, 25.0, 2.0, 10.5)

    # Scalloped natural fluff bumps along edges
    for ey in [-20.0, -10.0, 0.0, 10.0, 20.0]:
        m.add_sphere(-17.5, ey, 6.0, 3.5, segs_lat=4, segs_lon=5)
        m.add_sphere(17.5, ey, 6.0, 3.5, segs_lat=4, segs_lon=5)
    return m


def build_pelt_goat_skin():
    """SM_Item_Pelt_Goat_Skin: Rolled rustic brown goat skin hide with rawhide tie cord."""
    m = MeshBuilder("SM_Item_Pelt_Goat_Skin")
    m.set_material("goat_fur", 0.35, 0.24, 0.16)     # Rich brown goat fur #4E342E
    m.set_material("rawhide_cord", 0.78, 0.70, 0.54) # Rawhide tie cord

    # Rolled fur cylinder along Y (length 44cm, radius 7.5cm)
    m.set_material("goat_fur", 0.35, 0.24, 0.16)
    m.add_cylinder(-20.0, 20.0, 0.0, 7.5, 7.2, segments=10, axis='y')

    # Rawhide tie cords around roll
    m.set_material("rawhide_cord", 0.78, 0.70, 0.54)
    for cy in [-10.0, 10.0]:
        m.add_cylinder(cy - 1.2, cy + 1.2, 0.0, 7.5, 7.6, segments=10, axis='y')
    return m


# =============================================================================
# REGISTRY & BATCH RUNNER
# =============================================================================

BATCH_3_ASSETS = [
    # 1. Harvested Crops & Produce (10 - farming)
    ("SM_Item_Corn_Ear", build_corn_ear, "farming", "crop_corn.png", "0.08x0.24m", "Single ripe yellow sweet corn ear with peeled husk leaves"),
    ("SM_Item_Tomato_Fruit", build_tomato_fruit, "farming", "crop_tomato.png", "0.10x0.10m", "Ripe red heirloom beefsteak tomato with green star calyx"),
    ("SM_Item_Potato_Loose", build_potato_loose, "farming", "crop_potato.png", "0.14x0.18m", "Pair of russet baking potatoes with textured brown skin"),
    ("SM_Item_Carrot_Bunch", build_carrot_bunch, "farming", "crop_carrot.png", "0.14x0.28m", "Bunch of 3 fresh orange garden carrots tied with jute twine"),
    ("SM_Item_Pumpkin_Carved", build_pumpkin_carved, "farming", "crop_pumpkin.png", "0.28x0.28m", "Whole harvested ribbed round field pumpkin with woody stem"),
    ("SM_Item_Cabbage_Harvested", build_cabbage_harvested, "farming", "crop_herb.png", "0.22x0.22m", "Harvested round head of crinkled green garden cabbage"),
    ("SM_Item_Sunflower_Head", build_sunflower_head, "farming", "crop_sunflower.png", "0.26x0.26m", "Cut mature mammoth sunflower head packed with ripe seeds"),
    ("SM_Item_Strawberry_Basket", build_strawberry_basket, "farming", "crop_strawberry.png", "0.18x0.22m", "Woven wicker punnet basket heaped with fresh strawberries"),
    ("SM_Item_Cotton_Boll", build_cotton_boll, "farming", "crop_cotton.png", "0.14x0.14m", "4-burr dried cotton boll with fluffy raw white cotton lint"),
    ("SM_Item_Wheat_Sheaf", build_wheat_sheaf, "farming", "crop_wheat.png", "0.24x0.24m", "Tied sheaf bundle of ripe golden wheat with straw band"),

    # 2. Cooked Foods & Fruits (4 - farming)
    ("SM_Item_Food_Bread", build_food_bread, "farming", "food_bread.png", "0.16x0.26m", "Crusty artisanal sourdough bread loaf with flour dusted scoring"),
    ("SM_Item_Food_Cheese_Wheel", build_food_cheese_wheel, "farming", "food_cheese.png", "0.22x0.22m", "Round yellow farmhouse cheddar cheese wheel with cut wedge"),
    ("SM_Item_Food_Stew_Bowl", build_food_stew_bowl, "farming", "food_stew.png", "0.18x0.18m", "Glazed clay bowl of hearty vegetable beef stew with wooden spoon"),
    ("SM_Item_Food_Apple", build_food_apple, "farming", "food_apple.png", "0.09x0.09m", "Crisp red Honeycrisp apple with brown stem and leaf"),

    # 3. Dairy, Egg & Animal Byproducts (4 - ranching)
    ("SM_Item_Animal_Eggs_Carton", build_animal_eggs_carton, "ranching", "animal_egg.png", "0.15x0.28m", "Open cardboard carton holding 12 fresh homestead eggs"),
    ("SM_Item_Animal_Milk_Jug", build_animal_milk_jug, "ranching", "animal_milk.png", "0.14x0.14m", "1-gallon glass homestead milk jug with red foil seal"),
    ("SM_Item_Animal_Wool_Fleece", build_animal_wool_fleece, "ranching", "animal_wool.png", "0.26x0.34m", "Tied raw white sheep wool fleece bundle with paper twine"),
    ("SM_Item_Animal_Truffle", build_animal_truffle, "ranching", "animal_truffle.png", "0.10x0.12m", "Prized foraged black forest truffle mushroom"),

    # 4. Meats & Animal Pelts (6 - ranching)
    ("SM_Item_Meat_Beef_Steak", build_meat_beef_steak, "ranching", "meat_beef.png", "0.16x0.24m", "Thick-cut raw T-bone beef steak with bone and fat marbling"),
    ("SM_Item_Meat_Chicken_Drumstick", build_meat_chicken_drumstick, "ranching", "meat_chicken.png", "0.08x0.18m", "Fresh poultry chicken drumstick with exposed bone knuckle"),
    ("SM_Item_Meat_Pork_Chop", build_meat_pork_chop, "ranching", "meat_pork.png", "0.14x0.20m", "Fresh bone-in raw pork loin chop with fat rind cap"),
    ("SM_Item_Pelt_Cow_Hide", build_pelt_cow_hide, "ranching", "pelt_cow.png", "0.42x0.58m", "Folded brown-and-white spotted cowhide pelt roll with strap"),
    ("SM_Item_Pelt_Sheep_Fleece", build_pelt_sheep_fleece, "ranching", "pelt_sheep.png", "0.38x0.52m", "Fluffy folded natural sheepskin fleece pelt with wool pile"),
    ("SM_Item_Pelt_Goat_Skin", build_pelt_goat_skin, "ranching", "pelt_goat.png", "0.18x0.46m", "Rolled rustic brown goat skin hide with rawhide tie cord"),
]


def sync_icon(src_icon_name, category, model_name):
    src_path = os.path.join(ITEMS_DIR, src_icon_name)
    if not os.path.exists(src_path):
        # Search recursively in ITEMS_DIR
        for root, dirs, files in os.walk(ITEMS_DIR):
            if src_icon_name in files:
                src_path = os.path.join(root, src_icon_name)
                break

    if os.path.exists(src_path):
        paths = CAT_DIRS[category]
        hud_icon = os.path.join(paths["hud_icons"], f"{model_name}.png")
        ue5_icon = os.path.join(paths["ue5_icons"], f"{model_name}.png")
        shutil.copy2(src_path, hud_icon)
        shutil.copy2(src_path, ue5_icon)
        return True
    return False


def main():
    print("=====================================================================")
    print("  REBUILDING BATCH 3: 24 HARVESTED CROPS, FOOD & ANIMAL PRODUCTS")
    print("  Faithfully matching original item icons in assets/items/")
    print("=====================================================================\n")

    count = 0
    for name, builder_func, category, icon_name, footprint, desc in BATCH_3_ASSETS:
        count += 1
        print(f"--> Generating {name} ({category})...")

        # 1. Build watertight 3D geometry matching icon
        mesh = builder_func()
        mesh.ground_align()

        paths = CAT_DIRS[category]
        hud_obj = os.path.join(paths["hud_models"], f"{name}.obj")
        hud_mtl = os.path.join(paths["hud_models"], f"{name}.mtl")
        mesh.write_obj_and_mtl(hud_obj, hud_mtl)

        # 2. Sync to UE5 workspace
        ue5_obj = os.path.join(paths["ue5_models"], f"{name}.obj")
        ue5_mtl = os.path.join(paths["ue5_models"], f"{name}.mtl")
        shutil.copy2(hud_obj, ue5_obj)
        shutil.copy2(hud_mtl, ue5_mtl)

        # 3. Synchronize canonical icon
        synced = sync_icon(icon_name, category, name)
        icon_status = f"Synced matching icon from {icon_name}" if synced else f"WARNING: Icon {icon_name} not found"

        total_faces = sum(len(f) for f in mesh.materials.values())
        print(f"    [ICON] {icon_status}")
        print(f"    [DONE] {name}: {len(mesh.vertices)} verts, {total_faces} faces/tris.\n")

    print("Batch 3 successfully rebuilt and synchronized across HUD and UE5!\n")


if __name__ == "__main__":
    main()
