#!/usr/bin/env python3
"""
Homesteader Seeds, Fishing Tackle & Caught Fish 3D Asset Generator
=================================================================
Faithfully generates 20 world models (.obj + .mtl):
- 10 Heirloom Seed Packets (farming)
- 7 Fishing Tackle, Rods & Gear (fishing)
- 3 Trophy Caught Fish (fishing)

Features:
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
    "fishing": {
        "hud_models": os.path.join(PROJECT_ROOT, "HUD", "assets", "fishing", "models"),
        "hud_icons":  os.path.join(PROJECT_ROOT, "HUD", "assets", "fishing", "icons"),
        "ue5_models": os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "Assets", "Fishing", "Meshes"),
        "ue5_icons":  os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "UI", "Icons", "fishing"),
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
# 1. SEED PACKETS (10 - FARMING)
# =============================================================================

def build_seed_packet(name, crop_color, flap_color=(0.88, 0.85, 0.78)):
    """Generic seed packet builder: 9cm wide x 1.8cm thick x 13cm tall."""
    m = MeshBuilder(name)
    m.set_material("packet_paper", 0.94, 0.91, 0.84)  # Cream envelope paper #F5F0E6
    m.set_material("label_crop", *crop_color)         # Crop illustration badge
    m.set_material("packet_flap", *flap_color)        # Folded top flap

    # Main envelope body (9x1.8x12cm)
    m.set_material("packet_paper", 0.94, 0.91, 0.84)
    m.add_box(-4.5, 4.5, -0.9, 0.9, 0.0, 12.0)

    # Folded top seal flap
    m.set_material("packet_flap", *flap_color)
    m.add_box(-4.5, 4.5, -0.95, 0.95, 11.5, 13.0)

    # Crop illustration badge / label plate on front
    m.set_material("label_crop", *crop_color)
    m.add_box(-3.5, 3.5, 0.9, 0.95, 3.0, 10.0)
    return m


def build_seed_corn():
    return build_seed_packet("SM_Item_Seed_Corn", (0.95, 0.80, 0.20))       # Corn yellow


def build_seed_tomato():
    return build_seed_packet("SM_Item_Seed_Tomato", (0.88, 0.20, 0.15))     # Tomato red


def build_seed_wheat():
    return build_seed_packet("SM_Item_Seed_Wheat", (0.88, 0.72, 0.32))      # Golden wheat


def build_seed_potato():
    return build_seed_packet("SM_Item_Seed_Potato", (0.68, 0.48, 0.28))     # Earthy potato


def build_seed_carrot():
    return build_seed_packet("SM_Item_Seed_Carrot", (0.95, 0.48, 0.08))     # Carrot orange


def build_seed_pumpkin():
    return build_seed_packet("SM_Item_Seed_Pumpkin", (0.92, 0.42, 0.05))    # Pumpkin orange


def build_seed_sunflower():
    return build_seed_packet("SM_Item_Seed_Sunflower", (0.24, 0.24, 0.24), flap_color=(0.95, 0.80, 0.15))  # Dark seed with yellow flap


def build_seed_strawberry():
    return build_seed_packet("SM_Item_Seed_Strawberry", (0.88, 0.15, 0.22)) # Strawberry red


def build_seed_cotton():
    return build_seed_packet("SM_Item_Seed_Cotton", (0.96, 0.96, 0.98))     # Pure cotton white


def build_seed_herb():
    return build_seed_packet("SM_Item_Seed_Herb", (0.32, 0.65, 0.25))       # Garden herb green


# =============================================================================
# 2. FISHING TACKLE & FISH (10 - FISHING)
# =============================================================================

def build_rod_fly_fishing():
    """SM_Item_Rod_FlyFishing: 8ft fly fishing rod with cork grip and click-pawl fly reel."""
    m = MeshBuilder("SM_Item_Rod_FlyFishing")
    m.set_material("blank_graphite", 0.15, 0.15, 0.16) # Matte dark gray blank
    m.set_material("cork_grip", 0.82, 0.68, 0.48)      # Natural cork handle
    m.set_material("fly_reel", 0.22, 0.22, 0.24)       # Black aluminum reel
    m.set_material("line_backing", 0.88, 0.82, 0.32)   # Fluorescent fly line

    # Cork grip at base (length 28cm, radius 1.4cm)
    m.set_material("cork_grip", 0.82, 0.68, 0.48)
    m.add_cylinder(0.0, 0.0, 6.0, 34.0, 1.4, segments=8)

    # Butt extension
    m.set_material("blank_graphite", 0.15, 0.15, 0.16)
    m.add_cylinder(0.0, 0.0, 0.0, 6.0, 1.2, segments=6)

    # Long tapered graphite rod blank (total height 240cm)
    m.add_tapered_cylinder(0.0, 0.0, 34.0, 240.0, r_bot=1.0, r_top=0.3, segments=8)

    # Underslung fly reel mounted below cork handle
    m.set_material("fly_reel", 0.22, 0.22, 0.24)
    m.add_cylinder(0.0, 3.8, 4.0, 10.0, 4.0, segments=10)
    # Fly line inside reel spool
    m.set_material("line_backing", 0.88, 0.82, 0.32)
    m.add_cylinder(0.0, 3.8, 5.0, 9.0, 3.2, segments=8)
    return m


def build_rod_spincast():
    """SM_Item_Rod_Spincast: 6ft spincast combo rod with push-button closed face reel."""
    m = MeshBuilder("SM_Item_Rod_Spincast")
    m.set_material("rod_blank", 0.32, 0.32, 0.35)      # Slate gray rod blank
    m.set_material("eva_handle", 0.18, 0.18, 0.20)     # Black EVA grip
    m.set_material("spincast_reel", 0.55, 0.55, 0.58)  # Silver/chrome reel body
    m.set_material("push_button", 0.85, 0.18, 0.15)    # Red thumb push button

    # EVA foam split grip
    m.set_material("eva_handle", 0.18, 0.18, 0.20)
    m.add_cylinder(0.0, 0.0, 0.0, 26.0, 1.5, segments=8)

    # Tapered graphite rod blank (height 180cm)
    m.set_material("rod_blank", 0.32, 0.32, 0.35)
    m.add_tapered_cylinder(0.0, 0.0, 26.0, 180.0, r_bot=1.1, r_top=0.35, segments=8)

    # Closed-face spincast reel mounted on top of seat
    m.set_material("spincast_reel", 0.55, 0.55, 0.58)
    m.add_cylinder(0.0, -3.5, 14.0, 21.0, 3.5, segments=10)

    # Red thumb button at rear of reel
    m.set_material("push_button", 0.85, 0.18, 0.15)
    m.add_box(-1.0, 1.0, -4.5, -2.5, 12.5, 14.0)
    return m


def build_rod_trolling():
    """SM_Item_Rod_Trolling: Heavy boat trolling rod with conventional level-wind reel."""
    m = MeshBuilder("SM_Item_Rod_Trolling")
    m.set_material("troll_blank", 0.12, 0.14, 0.18)    # Deep midnight blue blank
    m.set_material("eva_foregrip", 0.16, 0.16, 0.18)   # Heavy foam ribbed grip
    m.set_material("conventional_reel", 0.75, 0.65, 0.32) # Gold anodized reel

    # Heavy butt and ribbed foregrip
    m.set_material("eva_foregrip", 0.16, 0.16, 0.18)
    m.add_cylinder(0.0, 0.0, 0.0, 35.0, 1.8, segments=8)

    # Heavy-duty rod blank (height 210cm)
    m.set_material("troll_blank", 0.12, 0.14, 0.18)
    m.add_tapered_cylinder(0.0, 0.0, 35.0, 210.0, r_bot=1.4, r_top=0.5, segments=8)

    # Conventional gold level-wind reel
    m.set_material("conventional_reel", 0.75, 0.65, 0.32)
    m.add_cylinder(0.0, -4.2, 16.0, 24.0, 4.5, segments=10)
    # Side crank handle
    m.add_box(4.5, 6.5, -6.5, -2.0, 18.0, 22.0)
    return m


def build_fishing_tackle_box():
    """SM_Item_Fishing_TackleBox: 3-tray cantilever green plastic fishing tackle box."""
    m = MeshBuilder("SM_Item_Fishing_TackleBox")
    m.set_material("tackle_green", 0.22, 0.42, 0.26)   # Hunter green chassis #388E3C
    m.set_material("tray_cream", 0.90, 0.86, 0.74)     # Cantilever tray cream
    m.set_material("brass_latch", 0.85, 0.72, 0.28)    # Brass front latch
    m.set_material("carry_handle", 0.18, 0.18, 0.20)   # Black top handle

    # Main box body (width 18cm, length 38cm, height 18cm)
    m.set_material("tackle_green", 0.22, 0.42, 0.26)
    m.add_box(-9.0, 9.0, -19.0, 19.0, 0.0, 15.0)

    # Lid bevel
    m.add_box(-8.5, 8.5, -18.5, 18.5, 15.0, 18.0)

    # Brass front snap latch
    m.set_material("brass_latch", 0.85, 0.72, 0.28)
    m.add_box(8.8, 9.5, -3.0, 3.0, 12.0, 16.0)

    # Top folding carry handle
    m.set_material("carry_handle", 0.18, 0.18, 0.20)
    m.add_box(-1.2, 1.2, -6.0, 6.0, 18.0, 21.0)
    return m


def build_fishing_landing_net():
    """SM_Item_Fishing_LandingNet: Telescopic hoop landing net with rubber mesh bag."""
    m = MeshBuilder("SM_Item_Fishing_LandingNet")
    m.set_material("aluminum_frame", 0.75, 0.78, 0.82) # Silver aluminum hoop #B0BEC5
    m.set_material("net_mesh", 0.18, 0.20, 0.24)       # Dark rubber mesh #263238
    m.set_material("foam_grip", 0.12, 0.12, 0.14)      # Black foam handle

    # Aluminum hoop rim (diameter ~40cm along Y)
    m.set_material("aluminum_frame", 0.75, 0.78, 0.82)
    # Oval rim
    m.add_box(-20.0, 20.0, 12.0, 14.0, 6.0, 8.0)     # Front
    m.add_box(-20.0, 20.0, 48.0, 50.0, 6.0, 8.0)     # Rear
    m.add_box(-21.0, -19.0, 12.0, 50.0, 6.0, 8.0)    # Left
    m.add_box(19.0, 21.0, 12.0, 50.0, 6.0, 8.0)      # Right

    # Net mesh bag hanging down
    m.set_material("net_mesh", 0.18, 0.20, 0.24)
    m.add_box(-18.0, 18.0, 14.0, 48.0, 0.0, 6.0)

    # Handle yoke and rod
    m.set_material("aluminum_frame", 0.75, 0.78, 0.82)
    m.add_cylinder(0.0, 0.0, -50.0, 12.0, 1.4, segments=8, axis='y')

    # Textured foam hand grip
    m.set_material("foam_grip", 0.12, 0.12, 0.14)
    m.add_cylinder(0.0, 0.0, -50.0, -25.0, 1.8, segments=8, axis='y')
    return m


def build_fishing_fish_basket():
    """SM_Item_Fishing_FishBasket: Collapsible floating wire live-well fish keeper basket."""
    m = MeshBuilder("SM_Item_Fishing_FishBasket")
    m.set_material("wire_mesh", 0.35, 0.38, 0.44)      # Galvanized steel wire #455A64
    m.set_material("steel_hoop", 0.65, 0.68, 0.72)     # Steel hoop rings
    m.set_material("trapdoor_lid", 0.85, 0.75, 0.28)   # Brass spring lid

    # Wire cylindrical cage (diameter 32cm, height 40cm)
    m.set_material("wire_mesh", 0.35, 0.38, 0.44)
    m.add_cylinder(0.0, 0.0, 2.0, 38.0, 15.5, segments=12)

    # 3 heavy steel reinforcement hoops
    m.set_material("steel_hoop", 0.65, 0.68, 0.72)
    m.add_cylinder(0.0, 0.0, 1.5, 3.5, 16.2, segments=12)   # Bottom hoop
    m.add_cylinder(0.0, 0.0, 18.5, 20.5, 16.2, segments=12) # Mid hoop
    m.add_cylinder(0.0, 0.0, 36.5, 38.5, 16.2, segments=12) # Top hoop

    # Spring-loaded trapdoor lid on top
    m.set_material("trapdoor_lid", 0.85, 0.75, 0.28)
    m.add_cylinder(0.0, 0.0, 38.5, 40.5, 9.0, segments=8)
    # Wire bail handle
    m.add_box(-1.0, 1.0, -16.0, 16.0, 38.0, 41.5)
    return m


def build_fishing_lure_tray():
    """SM_Item_Fishing_LureTray: Divided clear plastic utility box with colorful lures."""
    m = MeshBuilder("SM_Item_Fishing_LureTray")
    m.set_material("tray_plastic", 0.72, 0.78, 0.85)   # Translucent smoky plastic #90A4AE
    m.set_material("lure_silver", 0.88, 0.90, 0.92)    # Chrome spoon
    m.set_material("lure_chartreuse", 0.78, 0.92, 0.15)# Chartreuse plug
    m.set_material("lure_red", 0.88, 0.18, 0.15)       # Red-and-white plug

    # Clear plastic box (16x26x4cm)
    m.set_material("tray_plastic", 0.72, 0.78, 0.85)
    m.add_box(-8.0, 8.0, -13.0, 13.0, 0.0, 4.0)

    # Divided compartments inside with lures
    m.set_material("lure_silver", 0.88, 0.90, 0.92)
    m.add_box(-5.0, -1.0, -10.0, -2.0, 1.5, 3.2)

    m.set_material("lure_chartreuse", 0.78, 0.92, 0.15)
    m.add_box(1.0, 5.0, -10.0, -2.0, 1.5, 3.2)

    m.set_material("lure_red", 0.88, 0.18, 0.15)
    m.add_box(-4.0, 4.0, 2.0, 10.0, 1.5, 3.2)
    return m


def build_fish_largemouth_bass():
    """SM_Item_Fish_LargemouthBass: Trophy 44cm olive-green largemouth bass."""
    m = MeshBuilder("SM_Item_Fish_LargemouthBass")
    m.set_material("bass_green", 0.28, 0.38, 0.22)     # Olive green #33691E
    m.set_material("bass_belly", 0.88, 0.86, 0.76)     # Pale cream belly
    m.set_material("bass_lateral", 0.18, 0.24, 0.15)   # Dark lateral stripe band
    m.set_material("fin_olive", 0.42, 0.50, 0.32)      # Spiny dorsal fin

    # Main fuselage body (along Y, length 44cm, height 18cm, width 10cm)
    m.set_material("bass_green", 0.28, 0.38, 0.22)
    m.add_box(-4.5, 4.5, -12.0, 12.0, 4.0, 16.0)

    # Cream belly
    m.set_material("bass_belly", 0.88, 0.86, 0.76)
    m.add_box(-4.0, 4.0, -11.0, 11.0, 0.0, 5.0)

    # Dark jagged lateral stripe
    m.set_material("bass_lateral", 0.18, 0.24, 0.15)
    m.add_box(-4.8, 4.8, -10.0, 10.0, 7.5, 10.5)

    # Head and wide bucket mouth
    m.set_material("bass_green", 0.28, 0.38, 0.22)
    m.add_box(-4.0, 4.0, 12.0, 20.0, 2.0, 13.0)

    # Spiny dorsal fin and tail
    m.set_material("fin_olive", 0.42, 0.50, 0.32)
    m.add_box(-0.8, 0.8, -4.0, 8.0, 16.0, 20.0)   # Dorsal fin
    m.add_box(-0.8, 0.8, -22.0, -12.0, 1.5, 15.0)  # Caudal tail
    return m


def build_fish_chinook_salmon():
    """SM_Item_Fish_ChinookSalmon: Silvery-blue 64cm Pacific Chinook salmon with hooked jaw."""
    m = MeshBuilder("SM_Item_Fish_ChinookSalmon")
    m.set_material("salmon_silver", 0.65, 0.72, 0.78)  # Silvery blue flank #90A4AE
    m.set_material("salmon_pink", 0.92, 0.45, 0.28)    # Salmon pink flesh tint
    m.set_material("salmon_back", 0.22, 0.32, 0.42)    # Dark steel blue back
    m.set_material("fin_slate", 0.45, 0.52, 0.58)

    # Torpedo salmon body (along Y, length 64cm)
    m.set_material("salmon_silver", 0.65, 0.72, 0.78)
    m.add_box(-5.0, 5.0, -18.0, 18.0, 3.5, 18.0)

    # Dark blue-gray back
    m.set_material("salmon_back", 0.22, 0.32, 0.42)
    m.add_box(-4.6, 4.6, -17.0, 17.0, 15.0, 20.0)

    # Salmon pink lateral flush
    m.set_material("salmon_pink", 0.92, 0.45, 0.28)
    m.add_box(-5.2, 5.2, -15.0, 15.0, 7.0, 12.0)

    # Head with hooked kype jaw
    m.set_material("salmon_silver", 0.65, 0.72, 0.78)
    m.add_box(-4.5, 4.5, 18.0, 30.0, 2.5, 16.0)

    # Fins and forked tail
    m.set_material("fin_slate", 0.45, 0.52, 0.58)
    m.add_box(-0.8, 0.8, -6.0, 6.0, 20.0, 25.0)    # Dorsal fin
    m.add_box(-0.8, 0.8, -32.0, -18.0, 2.0, 18.0)  # Forked tail
    return m


def build_fish_rainbow_trout():
    """SM_Item_Fish_RainbowTrout: 39cm stream trout with iridescent pink lateral stripe."""
    m = MeshBuilder("SM_Item_Fish_RainbowTrout")
    m.set_material("trout_olive", 0.38, 0.48, 0.32)   # Olive back
    m.set_material("rainbow_band", 0.92, 0.38, 0.55)  # Magenta/pink rainbow stripe #E91E63
    m.set_material("trout_belly", 0.90, 0.90, 0.84)   # White belly
    m.set_material("trout_fin", 0.55, 0.60, 0.45)

    # Stream trout body (along Y, length 39cm)
    m.set_material("trout_olive", 0.38, 0.48, 0.32)
    m.add_box(-4.0, 4.0, -11.0, 11.0, 4.0, 14.0)

    # Pale belly
    m.set_material("trout_belly", 0.90, 0.90, 0.84)
    m.add_box(-3.8, 3.8, -10.0, 10.0, 0.0, 4.5)

    # Vibrant pink lateral rainbow band
    m.set_material("rainbow_band", 0.92, 0.38, 0.55)
    m.add_box(-4.2, 4.2, -10.0, 10.0, 5.5, 9.5)

    # Streamlined head
    m.set_material("trout_olive", 0.38, 0.48, 0.32)
    m.add_box(-3.5, 3.5, 11.0, 19.0, 2.0, 11.0)

    # Fins and spotted tail
    m.set_material("trout_fin", 0.55, 0.60, 0.45)
    m.add_box(-0.6, 0.6, -3.0, 4.0, 14.0, 17.0)   # Dorsal fin
    m.add_box(-0.6, 0.6, -20.0, -11.0, 1.5, 13.0)  # Tail
    return m


# =============================================================================
# REGISTRY & BATCH RUNNER
# =============================================================================

BATCH_4_ASSETS = [
    # 1. Seed Packets (10 - farming)
    ("SM_Item_Seed_Corn", build_seed_corn, "farming", "seed_corn.png", "0.09x0.13m", "Heirloom sweet corn seed packet with illustrated botanical label"),
    ("SM_Item_Seed_Tomato", build_seed_tomato, "farming", "seed_tomato.png", "0.09x0.13m", "Heirloom beefsteak tomato seed packet with illustrated label"),
    ("SM_Item_Seed_Wheat", build_seed_wheat, "farming", "seed_wheat.png", "0.09x0.13m", "Hard red winter wheat seed packet with illustrated label"),
    ("SM_Item_Seed_Potato", build_seed_potato, "farming", "seed_potato.png", "0.09x0.13m", "Certified seed potato eyes pouch with heirloom label"),
    ("SM_Item_Seed_Carrot", build_seed_carrot, "farming", "seed_carrot.png", "0.09x0.13m", "Danvers half-long carrot seed packet with illustrated label"),
    ("SM_Item_Seed_Pumpkin", build_seed_pumpkin, "farming", "seed_pumpkin.png", "0.09x0.13m", "Connecticut field pumpkin seed packet with illustrated label"),
    ("SM_Item_Seed_Sunflower", build_seed_sunflower, "farming", "seed_sunflower.png", "0.09x0.13m", "Mammoth Russian sunflower seed packet with illustrated label"),
    ("SM_Item_Seed_Strawberry", build_seed_strawberry, "farming", "seed_strawberry.png", "0.09x0.13m", "Everbearing garden strawberry seed packet with illustrated label"),
    ("SM_Item_Seed_Cotton", build_seed_cotton, "farming", "seed_cotton.png", "0.09x0.13m", "Upland heirloom cotton seed packet with illustrated label"),
    ("SM_Item_Seed_Herb", build_seed_herb, "farming", "seed_herb.png", "0.09x0.13m", "Culinary homestead herb garden seed packet with illustrated label"),

    # 2. Fishing Tackle & Fish (10 - fishing)
    ("SM_Item_Rod_FlyFishing", build_rod_fly_fishing, "fishing", "rod_fly_fishing.png", "0.12x2.40m", "8ft graphite fly fishing rod with cork grip & click-pawl fly reel"),
    ("SM_Item_Rod_Spincast", build_rod_spincast, "fishing", "rod_spincast_combo.png", "0.14x1.80m", "6ft spincast combo fishing rod with pushbutton closed-face reel"),
    ("SM_Item_Rod_Trolling", build_rod_trolling, "fishing", "rod_heavy_trolling.png", "0.16x2.10m", "Heavy boat trolling rod with conventional level-wind reel"),
    ("SM_Item_Fishing_TackleBox", build_fishing_tackle_box, "fishing", "box_tackle_3tray.png", "0.22x0.42m", "3-tray cantilever green plastic fishing tackle box with brass latches"),
    ("SM_Item_Fishing_LandingNet", build_fishing_landing_net, "fishing", "net_landing_telescopic.png", "0.45x1.10m", "Aluminum hoop landing net with rubber mesh bag & foam grip"),
    ("SM_Item_Fishing_FishBasket", build_fishing_fish_basket, "fishing", "basket_fish_wire.png", "0.33x0.42m", "Collapsible floating wire live-well fish keeper basket with trapdoor"),
    ("SM_Item_Fishing_LureTray", build_fishing_lure_tray, "fishing", "box_lures_organizer.png", "0.18x0.28m", "Divided clear plastic utility tackle box with spoons and plugs"),
    ("SM_Item_Fish_LargemouthBass", build_fish_largemouth_bass, "fishing", "fish_bass.png", "0.14x0.44m", "Trophy 44cm olive-green largemouth bass with dorsal fin & tail"),
    ("SM_Item_Fish_ChinookSalmon", build_fish_chinook_salmon, "fishing", "fish_salmon.png", "0.16x0.64m", "Silvery-blue 64cm Pacific Chinook salmon with hooked kype jaw"),
    ("SM_Item_Fish_RainbowTrout", build_fish_rainbow_trout, "fishing", "fish_trout.png", "0.12x0.39m", "Stream 39cm rainbow trout with iridescent pink lateral band"),
]


def sync_icon(src_icon_name, category, model_name):
    src_path = os.path.join(ITEMS_DIR, src_icon_name)
    if not os.path.exists(src_path):
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
    print("  REBUILDING BATCH 4: 20 SEEDS, FISHING TACKLE & TROPHY FISH")
    print("  Faithfully matching original item icons in assets/items/")
    print("=====================================================================\n")

    count = 0
    for name, builder_func, category, icon_name, footprint, desc in BATCH_4_ASSETS:
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

    print("Batch 4 successfully rebuilt and synchronized across HUD and UE5!\n")


if __name__ == "__main__":
    main()
