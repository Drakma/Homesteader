#!/usr/bin/env python3
"""
Homesteader Livestock Animals 3D Asset Generator (Complete 3-Variety Suite)
==========================================================================
Faithfully generates 3D world models (.obj + .mtl) and syncs matching icons:
- Every animal has 3 distinct breed varieties + young/calf models:
    1. CATTLE (3 Adult + 2 Calf):
       - SM_Animal_Cow_Holstein   <--> livestock_cow_holstein.png (Classic dairy B&W)
       - SM_Animal_Cow_Jersey     <--> livestock_cow_jersey.png (Caramel tan, dark muzzle with cream ring)
       - SM_Animal_Cow_Highland   <--> livestock_cow_highland.png (Shaggy ginger fur, 110cm wide horns, bangs)
       - SM_Animal_Cow_Calf       <--> baby_calf.png (Warm chestnut with white star)
       - SM_Animal_Cow_Calf_Spotted <--> baby_calf_spotted.png (Holstein spotted calf)
    2. CHICKENS (3 Adult + 1 Chick):
       - SM_Animal_Chicken_Red    <--> livestock_chicken_red.png (Rhode Island Red)
       - SM_Animal_Chicken_White  <--> livestock_chicken_white.png (White Leghorn)
       - SM_Animal_Chicken_Barred <--> livestock_chicken_barred.png (Barred Rock zebra plumage)
       - SM_Animal_Chicken_Chick  <--> baby_chick.png (Golden-yellow chick)
    3. PIGS (3 Adult + 1 Piglet):
       - SM_Animal_Pig_Pink       <--> livestock_pig_pink.png (Classic pink Yorkshire)
       - SM_Animal_Pig_Hampshire  <--> livestock_pig_hampshire.png (Black with clean white belt & front legs)
       - SM_Animal_Pig_Duroc      <--> livestock_pig_duroc.png (Deep reddish-brown, drooping ears)
       - SM_Animal_Pig_Piglet     <--> baby_piglet.png (Chubby pink piglet)
    4. SHEEP (3 Adult + 1 Lamb):
       - SM_Animal_Sheep_Suffolk  <--> livestock_sheep_suffolk.png (White fleece, black face & legs)
       - SM_Animal_Sheep_White    <--> livestock_sheep_white.png (All-white fleece & pale face/legs)
       - SM_Animal_Sheep_Tan      <--> livestock_sheep_tan.png (Natural caramel tan fleece)
       - SM_Animal_Sheep_Lamb     <--> baby_lamb.png (Fluffy white lamb with black mask)
    5. GOATS (3 Adult + 1 Kid):
       - SM_Animal_Goat_Brown     <--> livestock_goat_brown.png (Brown with white stripes & belly)
       - SM_Animal_Goat_White     <--> livestock_goat_white.png (Pure white Saanen goat)
       - SM_Animal_Goat_BlackWhite<--> livestock_goat_blackwhite.png (High-contrast piebald black & white)
       - SM_Animal_Goat_Kid       <--> baby_kid.png (Spotted brown & white kid)
    6. BACKWARDS-COMPATIBILITY ALIASES (5 Generic Models):
       - SM_Animal_Cow_Adult      (= Holstein)
       - SM_Animal_Chicken_Hen    (= Red)
       - SM_Animal_Pig_Adult      (= Pink)
       - SM_Animal_Sheep_Adult    (= Suffolk)
       - SM_Animal_Goat_Adult     (= Brown)

Standards:
- Metric scale on Homesteader grid (1 grid tile = 1m x 1m = 100 UU x 100 UU).
- Watertight 360-degree geometry rotatable on all 4 sides.
- Strictly ground-aligned pivots (Z_min = 0.00cm).
- Dual workspace synchronization (HUD/assets/ and Homesteader/Content/Homesteader/).
"""

import os
import sys
import math
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

HUD_RANCH_MODELS = os.path.join(PROJECT_ROOT, "HUD", "assets", "ranching", "models")
HUD_RANCH_ICONS  = os.path.join(PROJECT_ROOT, "HUD", "assets", "ranching", "icons")
UE5_RANCH_MODELS = os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "Assets", "Ranching", "Meshes")
UE5_RANCH_ICONS  = os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "UI", "Icons", "ranching")
ITEMS_DIR        = os.path.join(PROJECT_ROOT, "HUD", "assets", "items")

for p in [HUD_RANCH_MODELS, HUD_RANCH_ICONS, UE5_RANCH_MODELS, UE5_RANCH_ICONS]:
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
        self.add_quad(v1, v2, v6, v5)  # Front (-Y)
        self.add_quad(v3, v4, v8, v7)  # Back (+Y)
        self.add_quad(v4, v1, v5, v8)  # Left (-X)
        self.add_quad(v2, v3, v7, v6)  # Right (+X)

    def add_sloped_box(self, x_min_b, x_max_b, x_min_t, x_max_t, y_min_b, y_max_b, y_min_t, y_max_t, z_min, z_max):
        """Frustum box with distinct top and bottom footprints."""
        v1 = self.add_vertex(x_min_b, y_min_b, z_min)
        v2 = self.add_vertex(x_max_b, y_min_b, z_min)
        v3 = self.add_vertex(x_max_b, y_max_b, z_min)
        v4 = self.add_vertex(x_min_b, y_max_b, z_min)
        v5 = self.add_vertex(x_min_t, y_min_t, z_max)
        v6 = self.add_vertex(x_max_t, y_min_t, z_max)
        v7 = self.add_vertex(x_max_t, y_max_t, z_max)
        v8 = self.add_vertex(x_min_t, y_max_t, z_max)
        self.add_quad(v1, v4, v3, v2)
        self.add_quad(v5, v6, v7, v8)
        self.add_quad(v1, v2, v6, v5)
        self.add_quad(v3, v4, v8, v7)
        self.add_quad(v4, v1, v5, v8)
        self.add_quad(v2, v3, v7, v6)

    def add_cylinder(self, cx, cy, z_min, z_max, radius, segments=6):
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

    def add_cylinder_y(self, cen_x, cen_z, y_min, y_max, radius, segments=8):
        """Horizontal cylinder along Y axis (e.g. pig snout)."""
        front_verts = []
        back_verts = []
        for i in range(segments):
            angle = 2.0 * math.pi * i / segments
            x = cen_x + radius * math.cos(angle)
            z = cen_z + radius * math.sin(angle)
            front_verts.append(self.add_vertex(x, y_min, z))
            back_verts.append(self.add_vertex(x, y_max, z))
        c_front = self.add_vertex(cen_x, y_min, cen_z)
        c_back  = self.add_vertex(cen_x, y_max, cen_z)
        for i in range(segments):
            nxt = (i + 1) % segments
            self.add_tri(c_front, front_verts[i], front_verts[nxt])
            self.add_tri(c_back, back_verts[nxt], back_verts[i])
            self.add_quad(front_verts[i], back_verts[i], back_verts[nxt], front_verts[nxt])

    def add_cylinder_x(self, cen_y, cen_z, x_min, x_max, radius, segments=6):
        """Horizontal cylinder along X axis."""
        left_verts = []
        right_verts = []
        for i in range(segments):
            angle = 2.0 * math.pi * i / segments
            y = cen_y + radius * math.cos(angle)
            z = cen_z + radius * math.sin(angle)
            left_verts.append(self.add_vertex(x_min, y, z))
            right_verts.append(self.add_vertex(x_max, y, z))
        c_left  = self.add_vertex(x_min, cen_y, cen_z)
        c_right = self.add_vertex(x_max, cen_y, cen_z)
        for i in range(segments):
            nxt = (i + 1) % segments
            self.add_tri(c_left, left_verts[nxt], left_verts[i])
            self.add_tri(c_right, right_verts[i], right_verts[nxt])
            self.add_quad(left_verts[i], left_verts[nxt], right_verts[nxt], right_verts[i])

    def add_tapered_cylinder(self, cx, cy, z_min, z_max, r_bot, r_top, segments=6):
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
                f.write(f"Ks 0.180 0.180 0.180\n")
                f.write("Ns 16.0\n")
                f.write("d 1.0\n")
                f.write("illum 2\n\n")


# =============================================================================
# 1. CATTLE FAMILY (3 ADULTS + 2 CALVES)
# =============================================================================

def _build_cow_base(name, base_mat_name, base_rgb, muzzle_mat_name, muzzle_rgb, horns_mat_name, horns_rgb):
    """Core cow geometry builder with customizable base material and palette."""
    m = MeshBuilder(name)
    m.set_material(base_mat_name, *base_rgb)
    m.set_material(muzzle_mat_name, *muzzle_rgb)
    m.set_material(horns_mat_name, *horns_rgb)
    m.set_material("hooves_dark", 0.22, 0.20, 0.18)

    # Torso: Chest (-Y) and Rump (+Y)
    m.set_material(base_mat_name, *base_rgb)
    m.add_sloped_box(
        x_min_b=-34.0, x_max_b=34.0, x_min_t=-30.0, x_max_t=30.0,
        y_min_b=-50.0, y_max_b=0.0,   y_min_t=-45.0, y_max_t=-5.0,
        z_min=55.0, z_max=125.0
    )
    m.add_sloped_box(
        x_min_b=-32.0, x_max_b=32.0, x_min_t=-28.0, x_max_t=28.0,
        y_min_b=0.0,   y_max_b=55.0,  y_min_t=-5.0,  y_max_t=50.0,
        z_min=58.0, z_max=128.0
    )

    # Neck
    m.add_sloped_box(
        x_min_b=-18.0, x_max_b=18.0, x_min_t=-14.0, x_max_t=14.0,
        y_min_b=-68.0, y_max_b=-42.0, y_min_t=-75.0, y_max_t=-50.0,
        z_min=85.0, z_max=138.0
    )
    # Head crown
    m.add_box(-16.0, 16.0, -88.0, -68.0, 108.0, 138.0)

    # Muzzle
    m.set_material(muzzle_mat_name, *muzzle_rgb)
    m.add_box(-13.0, 13.0, -100.0, -86.0, 96.0, 118.0)

    # Ears
    for ex in [-16.0, 16.0]:
        sx = 1.0 if ex > 0 else -1.0
        m.set_material(base_mat_name, *base_rgb)
        m.add_box(ex, ex + sx * 14.0, -78.0, -70.0, 122.0, 132.0)
        m.set_material(muzzle_mat_name, *muzzle_rgb)
        m.add_box(ex + sx * 1.0, ex + sx * 12.0, -76.0, -72.0, 124.0, 130.0)

    # 4 Legs & Cloven Hooves
    for lx, ly in [(-22.0, -36.0), (22.0, -36.0), (-20.0, 38.0), (20.0, 38.0)]:
        m.set_material(base_mat_name, *base_rgb)
        m.add_box(lx - 7.5, lx + 7.5, ly - 7.5, ly + 7.5, 26.0, 58.0)
        m.add_box(lx - 5.5, lx + 5.5, ly - 5.5, ly + 5.5, 8.0, 26.0)
        m.set_material("hooves_dark", 0.22, 0.20, 0.18)
        m.add_box(lx - 6.5, lx + 6.5, ly - 7.5, ly + 6.5, 0.0, 8.0)

    # Udder
    m.set_material("muzzle_pink", 0.94, 0.72, 0.75)
    m.add_box(-12.0, 12.0, 10.0, 28.0, 48.0, 60.0)
    for tx in [-6.0, 6.0]:
        for ty in [14.0, 24.0]:
            m.add_cylinder(tx, ty, 42.0, 48.0, 1.4, segments=4)

    return m


def build_animal_cow_holstein(name="SM_Animal_Cow_Holstein"):
    """Classic black-and-white dairy Holstein cow with organic patches."""
    m = _build_cow_base(
        name,
        "cow_white", (0.94, 0.94, 0.95),
        "muzzle_pink", (0.94, 0.72, 0.75),
        "horns_cream", (0.88, 0.84, 0.72)
    )
    # Distinctive black patches
    m.set_material("cow_black", 0.16, 0.16, 0.18)
    m.add_box(-34.5, 34.5, -25.0, 15.0, 75.0, 126.0)     # Mid-body saddle patch
    m.add_box(-32.5, 32.5, 25.0, 52.0, 85.0, 128.5)      # Rump patch
    m.add_box(0.0, 16.5, -87.0, -69.0, 115.0, 138.5)     # Eye patch

    # Forward-curving dairy horns
    m.set_material("horns_cream", 0.88, 0.84, 0.72)
    for hx in [-14.0, 14.0]:
        m.add_tapered_cylinder(hx, -72.0, 136.0, 148.0, r_bot=3.2, r_top=1.0, segments=6)

    # Tail with black brush tuft
    m.set_material("cow_white", 0.94, 0.94, 0.95)
    m.add_box(-2.0, 2.0, 52.0, 56.0, 65.0, 120.0)
    m.set_material("cow_black", 0.16, 0.16, 0.18)
    m.add_box(-3.5, 3.5, 51.0, 57.0, 48.0, 65.0)
    return m


def build_animal_cow_jersey(name="SM_Animal_Cow_Jersey"):
    """Fawn caramel dairy Jersey cow with pale underbelly and dark muzzle with cream ring."""
    m = _build_cow_base(
        name,
        "jersey_tan", (0.64, 0.44, 0.28),
        "muzzle_slate", (0.24, 0.24, 0.26),
        "horns_amber", (0.86, 0.78, 0.62)
    )
    # Cream underbelly and inner legs
    m.set_material("jersey_cream", 0.90, 0.85, 0.76)
    m.add_box(-28.0, 28.0, -40.0, 40.0, 54.0, 72.0)

    # Iconic Jersey pale cream ring around dark muzzle
    m.add_box(-13.5, 13.5, -88.0, -84.0, 95.0, 120.0)
    # Pale orbital eye rings
    for ex in [-16.2, 16.2]:
        m.add_box(ex - 0.2, ex + 0.2, -82.0, -74.0, 120.0, 128.0)

    # Slender curved amber horns with dark tips
    m.set_material("horns_amber", 0.86, 0.78, 0.62)
    for hx in [-13.0, 13.0]:
        m.add_tapered_cylinder(hx, -72.0, 136.0, 146.0, r_bot=2.6, r_top=0.8, segments=5)

    # Tail with dark brown switch
    m.set_material("jersey_tan", 0.64, 0.44, 0.28)
    m.add_box(-2.0, 2.0, 52.0, 56.0, 65.0, 120.0)
    m.set_material("jersey_dark", 0.24, 0.18, 0.14)
    m.add_box(-3.5, 3.5, 51.0, 57.0, 48.0, 65.0)
    return m


def build_animal_cow_highland(name="SM_Animal_Cow_Highland"):
    """Shaggy Scottish Highland cow with wide 110cm horns, heavy bangs, and fur fringe."""
    m = _build_cow_base(
        name,
        "highland_ginger", (0.50, 0.24, 0.12),
        "muzzle_dark", (0.28, 0.22, 0.20),
        "horns_highland", (0.86, 0.82, 0.72)
    )
    # Shaggy low flank fringe / skirt
    m.set_material("highland_skirt", 0.42, 0.18, 0.08)
    m.add_box(-35.5, 35.5, -45.0, 48.0, 46.0, 62.0)
    m.add_box(-20.0, 20.0, -65.0, -42.0, 72.0, 92.0)  # Shaggy chest bib

    # Shaggy forelock bangs ("dossan") over brow and eyes
    m.set_material("highland_ginger", 0.50, 0.24, 0.12)
    m.add_box(-15.0, 15.0, -92.0, -80.0, 110.0, 140.0)

    # Massive wide sweeping horns: out from sides, curving upward (110cm span!)
    m.set_material("horns_highland", 0.86, 0.82, 0.72)
    # Left horn
    m.add_cylinder_x(cen_y=-72.0, cen_z=138.0, x_min=-55.0, x_max=-14.0, radius=3.2, segments=6)
    m.add_tapered_cylinder(-53.0, -72.0, 138.0, 158.0, r_bot=3.2, r_top=1.0, segments=6)
    # Right horn
    m.add_cylinder_x(cen_y=-72.0, cen_z=138.0, x_min=14.0, x_max=55.0, radius=3.2, segments=6)
    m.add_tapered_cylinder(53.0, -72.0, 138.0, 158.0, r_bot=3.2, r_top=1.0, segments=6)

    # Shaggy bushy tail
    m.set_material("highland_ginger", 0.50, 0.24, 0.12)
    m.add_box(-3.0, 3.0, 52.0, 58.0, 46.0, 120.0)
    m.add_box(-4.5, 4.5, 50.0, 59.0, 42.0, 65.0)
    return m


def build_animal_cow_calf(name="SM_Animal_Cow_Calf"):
    """Warm chestnut calf with white diamond star blaze."""
    m = MeshBuilder(name)
    m.set_material("calf_brown", 0.68, 0.42, 0.24)
    m.set_material("blaze_white", 0.95, 0.94, 0.92)
    m.set_material("muzzle_pink", 0.94, 0.72, 0.75)
    m.set_material("hooves_dark", 0.25, 0.20, 0.18)

    m.add_sloped_box(
        x_min_b=-18.0, x_max_b=18.0, x_min_t=-16.0, x_max_t=16.0,
        y_min_b=-30.0, y_max_b=30.0, y_min_t=-28.0, y_max_t=28.0,
        z_min=32.0, z_max=72.0
    )
    m.add_sloped_box(
        x_min_b=-10.0, x_max_b=10.0, x_min_t=-8.5, x_max_t=8.5,
        y_min_b=-46.0, y_max_b=-25.0, y_min_t=-50.0, y_max_t=-32.0,
        z_min=48.0, z_max=82.0
    )
    m.add_box(-10.5, 10.5, -58.0, -42.0, 62.0, 82.0)
    # White diamond blaze
    m.set_material("blaze_white", 0.95, 0.94, 0.92)
    m.add_box(-3.5, 3.5, -58.2, -45.0, 70.0, 80.0)

    # Pink muzzle
    m.set_material("muzzle_pink", 0.94, 0.72, 0.75)
    m.add_box(-8.0, 8.0, -68.0, -56.0, 55.0, 68.0)

    # Wide ears
    m.set_material("calf_brown", 0.68, 0.42, 0.24)
    m.add_box(-19.0, -10.0, -48.0, -42.0, 72.0, 80.0)
    m.add_box( 10.0,  19.0, -48.0, -42.0, 72.0, 80.0)

    # 4 Legs
    for lx in [-12.0, 12.0]:
        for ly in [-20.0, 22.0]:
            m.set_material("calf_brown", 0.68, 0.42, 0.24)
            m.add_box(lx - 4.5, lx + 4.5, ly - 4.5, ly + 4.5, 5.0, 34.0)
            m.set_material("hooves_dark", 0.25, 0.20, 0.18)
            m.add_box(lx - 4.8, lx + 4.8, ly - 5.0, ly + 4.8, 0.0, 5.0)

    m.set_material("calf_brown", 0.68, 0.42, 0.24)
    m.add_box(-1.8, 1.8, 28.0, 31.0, 42.0, 68.0)
    return m


def build_animal_cow_calf_spotted(name="SM_Animal_Cow_Calf_Spotted"):
    """Black-and-white spotted Holstein calf."""
    m = MeshBuilder(name)
    m.set_material("calf_white", 0.95, 0.95, 0.96)
    m.set_material("calf_black", 0.16, 0.16, 0.18)
    m.set_material("muzzle_pink", 0.94, 0.72, 0.75)
    m.set_material("hooves_dark", 0.22, 0.20, 0.18)

    # White base body
    m.add_sloped_box(
        x_min_b=-18.0, x_max_b=18.0, x_min_t=-16.0, x_max_t=16.0,
        y_min_b=-30.0, y_max_b=30.0, y_min_t=-28.0, y_max_t=28.0,
        z_min=32.0, z_max=72.0
    )
    # Black saddle patch
    m.set_material("calf_black", 0.16, 0.16, 0.18)
    m.add_box(-18.5, 18.5, -12.0, 12.0, 45.0, 72.5)

    # Neck
    m.set_material("calf_white", 0.95, 0.95, 0.96)
    m.add_sloped_box(
        x_min_b=-10.0, x_max_b=10.0, x_min_t=-8.5, x_max_t=8.5,
        y_min_b=-46.0, y_max_b=-25.0, y_min_t=-50.0, y_max_t=-32.0,
        z_min=48.0, z_max=82.0
    )
    # Head crown
    m.add_box(-10.5, 10.5, -58.0, -42.0, 62.0, 82.0)
    # Black eye patch
    m.set_material("calf_black", 0.16, 0.16, 0.18)
    m.add_box(0.0, 10.8, -57.0, -43.0, 65.0, 82.2)

    # Pink muzzle
    m.set_material("muzzle_pink", 0.94, 0.72, 0.75)
    m.add_box(-8.0, 8.0, -68.0, -56.0, 55.0, 68.0)

    # Ears
    m.set_material("calf_black", 0.16, 0.16, 0.18)
    m.add_box(-19.0, -10.0, -48.0, -42.0, 72.0, 80.0)
    m.set_material("calf_white", 0.95, 0.95, 0.96)
    m.add_box( 10.0,  19.0, -48.0, -42.0, 72.0, 80.0)

    # 4 Legs
    for lx, ly in [(-12.0, -20.0), (12.0, -20.0), (-12.0, 22.0), (12.0, 22.0)]:
        m.set_material("calf_white", 0.95, 0.95, 0.96)
        m.add_box(lx - 4.5, lx + 4.5, ly - 4.5, ly + 4.5, 5.0, 34.0)
        m.set_material("hooves_dark", 0.22, 0.20, 0.18)
        m.add_box(lx - 4.8, lx + 4.8, ly - 5.0, ly + 4.8, 0.0, 5.0)

    m.set_material("calf_white", 0.95, 0.95, 0.96)
    m.add_box(-1.8, 1.8, 28.0, 31.0, 42.0, 68.0)
    return m


# =============================================================================
# 2. CHICKEN FAMILY (3 ADULTS + 1 CHICK)
# =============================================================================

def _build_chicken_base(name, body_mat, body_rgb, comb_mat, comb_rgb, beak_mat, beak_rgb):
    """Core chicken geometry with configurable feathers, comb and feet."""
    m = MeshBuilder(name)
    m.set_material(body_mat, *body_rgb)
    m.set_material(comb_mat, *comb_rgb)
    m.set_material(beak_mat, *beak_rgb)

    # Body
    m.set_material(body_mat, *body_rgb)
    m.add_sloped_box(
        x_min_b=-12.0, x_max_b=12.0, x_min_t=-10.0, x_max_t=10.0,
        y_min_b=-18.0, y_max_b=18.0, y_min_t=-14.0, y_max_t=14.0,
        z_min=18.0, z_max=38.0
    )
    # Wings
    m.add_box(-13.5, -10.0, -12.0, 12.0, 22.0, 34.0)
    m.add_box( 10.0,  13.5, -12.0, 12.0, 22.0, 34.0)

    # Neck & head
    m.add_box(-5.5, 5.5, -24.0, -14.0, 28.0, 48.0)

    # Comb
    m.set_material(comb_mat, *comb_rgb)
    m.add_box(-1.8, 1.8, -26.0, -12.0, 47.0, 54.0)

    # Beak
    m.set_material(beak_mat, *beak_rgb)
    m.add_box(-2.5, 2.5, -30.0, -24.0, 38.0, 43.0)

    # Wattles
    m.set_material(comb_mat, *comb_rgb)
    m.add_box(-1.8, 1.8, -26.0, -20.0, 32.0, 38.0)

    # 2 Legs & Splayed Feet
    m.set_material(beak_mat, *beak_rgb)
    for lx in [-6.0, 6.0]:
        m.add_cylinder(lx, 0.0, 2.0, 18.0, 1.2, segments=5)
        m.add_box(lx - 5.0, lx + 5.0, -8.0, 3.0, 0.0, 2.5)

    return m


def build_animal_chicken_red(name="SM_Animal_Chicken_Red"):
    """Rhode Island Red chicken with red comb, wattles, and fan tail."""
    m = _build_chicken_base(
        name,
        "hen_red", (0.65, 0.22, 0.12),
        "comb_crimson", (0.88, 0.15, 0.14),
        "beak_yellow", (0.98, 0.78, 0.12)
    )
    # Dark fan tail plumes
    m.set_material("tail_dark", 0.20, 0.18, 0.16)
    m.add_box(-4.5, 4.5, 14.0, 28.0, 32.0, 52.0)
    return m


def build_animal_chicken_white(name="SM_Animal_Chicken_White"):
    """Pure white Leghorn chicken with bright red comb, yellow beak & legs."""
    m = _build_chicken_base(
        name,
        "hen_white", (0.95, 0.95, 0.96),
        "comb_bright_red", (0.92, 0.12, 0.12),
        "beak_yellow", (0.98, 0.78, 0.12)
    )
    # Pure white upright tail plumes
    m.set_material("hen_white", 0.95, 0.95, 0.96)
    m.add_box(-4.5, 4.5, 14.0, 28.0, 32.0, 53.0)
    return m


def build_animal_chicken_barred(name="SM_Animal_Chicken_Barred"):
    """Barred Rock chicken with alternating black & white feather stripes."""
    m = _build_chicken_base(
        name,
        "feather_barred_dark", (0.15, 0.15, 0.16),
        "comb_crimson", (0.88, 0.15, 0.14),
        "beak_yellow", (0.98, 0.78, 0.12)
    )
    # White barred stripes on body and wings
    m.set_material("feather_barred_light", 0.88, 0.88, 0.90)
    m.add_box(-12.5, 12.5, -15.0, 15.0, 24.0, 27.0)
    m.add_box(-12.5, 12.5, -15.0, 15.0, 31.0, 34.0)
    m.add_box(-14.0, -9.5, -9.0, 9.0, 26.0, 29.0)
    m.add_box(  9.5, 14.0, -9.0, 9.0, 26.0, 29.0)

    # Barred tail feathers
    m.set_material("feather_barred_dark", 0.15, 0.15, 0.16)
    m.add_box(-4.5, 4.5, 14.0, 28.0, 32.0, 52.0)
    m.set_material("feather_barred_light", 0.88, 0.88, 0.90)
    m.add_box(-4.6, 4.6, 17.0, 25.0, 38.0, 42.0)
    return m


def build_animal_chicken_chick(name="SM_Animal_Chicken_Chick"):
    """Downy golden-yellow baby chick."""
    m = MeshBuilder(name)
    m.set_material("chick_yellow", 0.98, 0.84, 0.20)
    m.set_material("beak_orange", 0.96, 0.52, 0.08)
    m.set_material("eye_black", 0.12, 0.12, 0.12)

    m.add_sphere(0.0, 0.0, 10.0, 5.5, segs_lat=4, segs_lon=6)
    m.add_sphere(0.0, -3.5, 13.5, 3.8, segs_lat=4, segs_lon=6)
    m.add_box(-6.5, -4.5, -3.0, 3.0, 8.0, 12.0)
    m.add_box( 4.5,  6.5, -3.0, 3.0, 8.0, 12.0)

    m.set_material("beak_orange", 0.96, 0.52, 0.08)
    m.add_box(-1.2, 1.2, -8.5, -6.5, 12.0, 14.2)

    m.set_material("eye_black", 0.12, 0.12, 0.12)
    m.add_box(-3.2, -2.2, -6.5, -5.0, 14.0, 15.2)
    m.add_box( 2.2,  3.2, -6.5, -5.0, 14.0, 15.2)

    m.set_material("beak_orange", 0.96, 0.52, 0.08)
    for fx in [-2.5, 2.5]:
        m.add_cylinder(fx, 0.0, 1.0, 5.0, 0.6, segments=4)
        m.add_box(fx - 2.0, fx + 2.0, -3.5, 1.5, 0.0, 1.2)
    return m


# =============================================================================
# 3. PIG FAMILY (3 ADULTS + 1 PIGLET)
# =============================================================================

def _build_pig_base(name, coat_mat, coat_rgb, snout_mat, snout_rgb):
    """Core pig geometry with barrel torso, low belly, disc snout, and trotters."""
    m = MeshBuilder(name)
    m.set_material(coat_mat, *coat_rgb)
    m.set_material(snout_mat, *snout_rgb)
    m.set_material("hooves_pork", 0.45, 0.35, 0.32)

    # Torso
    m.set_material(coat_mat, *coat_rgb)
    m.add_sloped_box(
        x_min_b=-28.0, x_max_b=28.0, x_min_t=-25.0, x_max_t=25.0,
        y_min_b=-48.0, y_max_b=48.0, y_min_t=-42.0, y_max_t=42.0,
        z_min=24.0, z_max=72.0
    )
    # Low belly
    m.add_box(-22.0, 22.0, -32.0, 32.0, 18.0, 30.0)

    # Head & Neck
    m.add_sloped_box(
        x_min_b=-16.0, x_max_b=16.0, x_min_t=-13.0, x_max_t=13.0,
        y_min_b=-75.0, y_max_b=-45.0, y_min_t=-70.0, y_max_t=-45.0,
        z_min=32.0, z_max=66.0
    )

    # Disc snout
    m.set_material(snout_mat, *snout_rgb)
    m.add_cylinder_y(cen_x=0.0, cen_z=46.0, y_min=-82.0, y_max=-74.0, radius=7.5, segments=8)

    # Ears
    m.set_material(coat_mat, *coat_rgb)
    for ex in [-14.0, 14.0]:
        m.add_box(ex - 4.0, ex + 4.0, -68.0, -56.0, 60.0, 72.0)
        m.add_box(ex - 3.0, ex + 3.0, -72.0, -66.0, 52.0, 62.0)

    # 4 Legs
    for lx in [-18.0, 18.0]:
        for ly in [-32.0, 34.0]:
            m.set_material(coat_mat, *coat_rgb)
            m.add_box(lx - 6.0, lx + 6.0, ly - 6.0, ly + 6.0, 6.0, 28.0)
            m.set_material("hooves_pork", 0.45, 0.35, 0.32)
            m.add_box(lx - 6.5, lx + 6.5, ly - 6.5, ly + 6.5, 0.0, 6.0)

    # Curly corkscrew tail
    m.set_material(coat_mat, *coat_rgb)
    m.add_box(-2.5, 2.5, 48.0, 58.0, 55.0, 65.0)
    m.add_box( 1.0, 6.0, 56.0, 62.0, 62.0, 70.0)
    return m


def build_animal_pig_pink(name="SM_Animal_Pig_Pink"):
    """Healthy rosy-pink homestead pig."""
    return _build_pig_base(
        name,
        "pig_pink", (0.95, 0.74, 0.76),
        "snout_dark", (0.92, 0.58, 0.64)
    )


def build_animal_pig_hampshire(name="SM_Animal_Pig_Hampshire"):
    """Hampshire pig: black with solid white belt over shoulders and front legs."""
    m = _build_pig_base(
        name,
        "pig_black", (0.14, 0.14, 0.16),
        "snout_black", (0.18, 0.18, 0.20)
    )
    # Solid white belt wrapping over shoulders & down both front legs
    m.set_material("belt_white", 0.94, 0.94, 0.96)
    m.add_box(-28.5, 28.5, -45.0, -15.0, 23.5, 72.5)  # Shoulder belt
    m.add_box(-22.5, 22.5, -32.0, -15.0, 17.5, 30.5)  # Belly belt
    # Front white legs & hooves
    for lx in [-18.0, 18.0]:
        m.add_box(lx - 6.2, lx + 6.2, -38.2, -25.8, 0.0, 28.5)
    return m


def build_animal_pig_duroc(name="SM_Animal_Pig_Duroc"):
    """Duroc pig: solid rich reddish-brown mahogany with forward-drooping ears."""
    m = _build_pig_base(
        name,
        "duroc_red", (0.52, 0.24, 0.14),
        "snout_red", (0.45, 0.20, 0.12)
    )
    # Heavy forward-drooping Duroc ears covering brow
    m.set_material("duroc_red", 0.52, 0.24, 0.14)
    for ex in [-14.0, 14.0]:
        m.add_box(ex - 4.5, ex + 4.5, -76.0, -62.0, 48.0, 64.0)
    return m


def build_animal_pig_piglet(name="SM_Animal_Pig_Piglet"):
    """Chubby compact pink piglet with button snout."""
    m = MeshBuilder(name)
    m.set_material("piglet_pink", 0.96, 0.78, 0.80)
    m.set_material("snout_pink", 0.92, 0.60, 0.68)

    m.add_box(-11.0, 11.0, -22.0, 22.0, 12.0, 32.0)
    m.add_box(-8.5, 8.5, -38.0, -20.0, 16.0, 34.0)

    m.set_material("snout_pink", 0.92, 0.60, 0.68)
    m.add_cylinder_y(cen_x=0.0, cen_z=24.0, y_min=-42.0, y_max=-37.0, radius=4.2, segments=6)

    m.set_material("piglet_pink", 0.96, 0.78, 0.80)
    m.add_box(-14.0, -7.0, -32.0, -24.0, 28.0, 37.0)
    m.add_box(  7.0, 14.0, -32.0, -24.0, 28.0, 37.0)

    for lx in [-8.0, 8.0]:
        for ly in [-14.0, 14.0]:
            m.add_box(lx - 3.0, lx + 3.0, ly - 3.0, ly + 3.0, 0.0, 14.0)

    m.add_box(-1.5, 1.5, 22.0, 28.0, 24.0, 30.0)
    return m


# =============================================================================
# 4. SHEEP FAMILY (3 ADULTS + 1 LAMB)
# =============================================================================

def _build_sheep_base(name, wool_mat, wool_rgb, face_mat, face_rgb, legs_mat, legs_rgb):
    """Core sheep fleece blanket, head, and legs."""
    m = MeshBuilder(name)
    m.set_material(wool_mat, *wool_rgb)
    m.set_material(face_mat, *face_rgb)
    m.set_material(legs_mat, *legs_rgb)
    m.set_material("hooves_dark", 0.16, 0.16, 0.16)

    # Wool torso
    m.set_material(wool_mat, *wool_rgb)
    m.add_sloped_box(
        x_min_b=-26.0, x_max_b=26.0, x_min_t=-24.0, x_max_t=24.0,
        y_min_b=-38.0, y_max_b=38.0, y_min_t=-34.0, y_max_t=34.0,
        z_min=35.0, z_max=82.0
    )
    # Fleece puffs
    for py in [-25.0, 0.0, 25.0]:
        m.add_sphere(-24.0, py, 60.0, 9.5, segs_lat=4, segs_lon=6)
        m.add_sphere( 24.0, py, 60.0, 9.5, segs_lat=4, segs_lon=6)
        m.add_sphere(  0.0, py, 78.0, 9.5, segs_lat=4, segs_lon=6)

    # Head and neck
    m.set_material(face_mat, *face_rgb)
    m.add_box(-11.0, 11.0, -52.0, -32.0, 52.0, 85.0)
    m.add_box(-9.5, 9.5, -68.0, -48.0, 60.0, 86.0)

    # Drooping ears
    for ex in [-9.5, 9.5]:
        sx = 1.0 if ex > 0 else -1.0
        m.add_box(ex, ex + sx * 12.0, -56.0, -48.0, 64.0, 75.0)

    # Wool cap on crown
    m.set_material(wool_mat, *wool_rgb)
    m.add_box(-8.5, 8.5, -56.0, -44.0, 84.0, 94.0)

    # 4 Legs
    for lx in [-16.0, 16.0]:
        for ly in [-24.0, 26.0]:
            m.set_material(legs_mat, *legs_rgb)
            m.add_box(lx - 4.2, lx + 4.2, ly - 4.2, ly + 4.2, 5.0, 36.0)
            m.set_material("hooves_dark", 0.16, 0.16, 0.16)
            m.add_box(lx - 4.5, lx + 4.5, ly - 4.5, ly + 4.5, 0.0, 5.0)

    # Short dock tail
    m.set_material(wool_mat, *wool_rgb)
    m.add_box(-4.0, 4.0, 36.0, 42.0, 62.0, 74.0)
    return m


def build_animal_sheep_suffolk(name="SM_Animal_Sheep_Suffolk"):
    """Suffolk sheep: thick cream fleece blanket with black face, ears & legs."""
    return _build_sheep_base(
        name,
        "wool_cream", (0.94, 0.92, 0.88),
        "face_black", (0.16, 0.16, 0.17),
        "legs_black", (0.16, 0.16, 0.17)
    )


def build_animal_sheep_white(name="SM_Animal_Sheep_White"):
    """All-white sheep: full white fleece, pale pinkish face and white legs."""
    return _build_sheep_base(
        name,
        "wool_white", (0.95, 0.94, 0.92),
        "face_pale", (0.90, 0.82, 0.80),
        "legs_pale", (0.86, 0.82, 0.76)
    )


def build_animal_sheep_tan(name="SM_Animal_Sheep_Tan"):
    """Tan sheep: warm caramel tan fleece with brown face and legs."""
    return _build_sheep_base(
        name,
        "wool_tan", (0.64, 0.46, 0.32),
        "face_brown", (0.48, 0.32, 0.22),
        "legs_brown", (0.48, 0.32, 0.22)
    )


def build_animal_sheep_lamb(name="SM_Animal_Sheep_Lamb"):
    """Fluffy white spring lamb with dark Suffolk face."""
    m = MeshBuilder(name)
    m.set_material("lamb_white", 0.96, 0.95, 0.92)
    m.set_material("face_black", 0.18, 0.18, 0.20)

    m.add_box(-14.0, 14.0, -22.0, 22.0, 22.0, 48.0)
    m.add_sphere(0.0, -10.0, 38.0, 8.0, segs_lat=4, segs_lon=6)
    m.add_sphere(0.0,  10.0, 38.0, 8.0, segs_lat=4, segs_lon=6)

    m.set_material("face_black", 0.18, 0.18, 0.20)
    m.add_box(-7.0, 7.0, -36.0, -20.0, 32.0, 52.0)
    m.add_box(-14.0, -6.5, -28.0, -22.0, 38.0, 46.0)
    m.add_box(  6.5, 14.0, -28.0, -22.0, 38.0, 46.0)

    m.set_material("lamb_white", 0.96, 0.95, 0.92)
    m.add_box(-6.0, 6.0, -28.0, -18.0, 49.0, 54.0)

    m.set_material("face_black", 0.18, 0.18, 0.20)
    for lx in [-9.0, 9.0]:
        for ly in [-14.0, 14.0]:
            m.add_box(lx - 2.8, lx + 2.8, ly - 2.8, ly + 2.8, 0.0, 24.0)
    return m


# =============================================================================
# 5. GOAT FAMILY (3 ADULTS + 1 KID)
# =============================================================================

def _build_goat_base(name, coat_mat, coat_rgb, horns_mat, horns_rgb, beard_mat, beard_rgb):
    """Core goat geometry with athletic body, upright neck, horns, beard & flipped tail."""
    m = MeshBuilder(name)
    m.set_material(coat_mat, *coat_rgb)
    m.set_material(horns_mat, *horns_rgb)
    m.set_material(beard_mat, *beard_rgb)
    m.set_material("hooves_dark", 0.20, 0.18, 0.16)

    # Torso
    m.set_material(coat_mat, *coat_rgb)
    m.add_sloped_box(
        x_min_b=-18.0, x_max_b=18.0, x_min_t=-15.0, x_max_t=15.0,
        y_min_b=-34.0, y_max_b=34.0, y_min_t=-30.0, y_max_t=30.0,
        z_min=42.0, z_max=82.0
    )

    # Upright neck
    m.add_sloped_box(
        x_min_b=-9.0, x_max_b=9.0, x_min_t=-7.5, x_max_t=7.5,
        y_min_b=-48.0, y_max_b=-28.0, y_min_t=-54.0, y_max_t=-38.0,
        z_min=65.0, z_max=102.0
    )
    # Wedge-shaped head
    m.add_box(-8.5, 8.5, -66.0, -48.0, 84.0, 102.0)

    # Chin beard tuft
    m.set_material(beard_mat, *beard_rgb)
    m.add_box(-3.5, 3.5, -64.0, -56.0, 72.0, 85.0)

    # Perky upright ears
    m.set_material(coat_mat, *coat_rgb)
    m.add_box(-18.0, -8.0, -52.0, -46.0, 95.0, 104.0)
    m.add_box(  8.0, 18.0, -52.0, -46.0, 95.0, 104.0)

    # Arching backward horns
    m.set_material(horns_mat, *horns_rgb)
    for hx in [-5.0, 5.0]:
        m.add_cylinder(hx, -44.0, 98.0, 118.0, 2.2, segments=6)
        m.add_cylinder(hx, -36.0, 110.0, 126.0, 1.5, segments=5)

    # 4 Agile legs
    for lx in [-12.0, 12.0]:
        for ly in [-22.0, 24.0]:
            m.set_material(coat_mat, *coat_rgb)
            m.add_box(lx - 3.8, lx + 3.8, ly - 3.8, ly + 3.8, 6.0, 44.0)
            m.set_material("hooves_dark", 0.20, 0.18, 0.16)
            m.add_box(lx - 4.0, lx + 4.0, ly - 4.0, ly + 4.0, 0.0, 6.0)

    # Short flipped upturned tail
    m.set_material(coat_mat, *coat_rgb)
    m.add_box(-2.5, 2.5, 32.0, 44.0, 74.0, 88.0)
    return m


def build_animal_goat_brown(name="SM_Animal_Goat_Brown"):
    """Brown goat with white belly, white throat and facial stripes, dark horns."""
    m = _build_goat_base(
        name,
        "goat_brown", (0.58, 0.38, 0.24),
        "horns_dark", (0.28, 0.28, 0.30),
        "beard_white", (0.95, 0.94, 0.92)
    )
    # White belly & throat accents
    m.set_material("belly_white", 0.95, 0.94, 0.92)
    m.add_box(-14.0, 14.0, -22.0, 22.0, 41.5, 52.0)
    m.add_box(-2.5, 2.5, -66.2, -50.0, 92.0, 101.0)  # Nose bridge stripe
    return m


def build_animal_goat_white(name="SM_Animal_Goat_White"):
    """Pure white Saanen goat with cream horns and white chin beard."""
    return _build_goat_base(
        name,
        "goat_white", (0.95, 0.95, 0.96),
        "horns_ivory", (0.88, 0.84, 0.72),
        "beard_white", (0.95, 0.95, 0.96)
    )


def build_animal_goat_blackwhite(name="SM_Animal_Goat_BlackWhite"):
    """Piebald black-and-white goat with black head/rump and white belly band."""
    m = _build_goat_base(
        name,
        "goat_black", (0.16, 0.16, 0.18),
        "horns_dark", (0.28, 0.28, 0.30),
        "beard_dark", (0.18, 0.18, 0.20)
    )
    # White saddle / belly band
    m.set_material("goat_white", 0.94, 0.94, 0.95)
    m.add_box(-18.5, 18.5, -18.0, 12.0, 41.5, 82.5)
    # White facial blaze
    m.add_box(-2.5, 2.5, -66.2, -50.0, 92.0, 101.0)
    return m


def build_animal_goat_kid(name="SM_Animal_Goat_Kid"):
    """Playful brown-and-white spotted goat kid."""
    m = MeshBuilder(name)
    m.set_material("kid_brown", 0.62, 0.42, 0.28)
    m.set_material("kid_white", 0.95, 0.94, 0.92)
    m.set_material("kid_horns", 0.32, 0.30, 0.28)

    m.add_box(-11.0, 11.0, -18.0, 18.0, 22.0, 42.0)
    m.set_material("kid_white", 0.95, 0.94, 0.92)
    m.add_box(-8.0, 8.0, -18.2, -6.0, 24.0, 38.0)

    m.set_material("kid_brown", 0.62, 0.42, 0.28)
    m.add_box(-6.5, 6.5, -34.0, -18.0, 36.0, 52.0)
    m.add_box(-14.0, -6.0, -28.0, -22.0, 46.0, 53.0)
    m.add_box(  6.0, 14.0, -28.0, -22.0, 46.0, 53.0)

    m.set_material("kid_horns", 0.32, 0.30, 0.28)
    m.add_box(-3.5, -1.5, -26.0, -22.0, 51.0, 55.0)
    m.add_box( 1.5,  3.5, -26.0, -22.0, 51.0, 55.0)

    m.set_material("kid_brown", 0.62, 0.42, 0.28)
    for lx in [-8.0, 8.0]:
        for ly in [-12.0, 12.0]:
            m.add_box(lx - 2.5, lx + 2.5, ly - 2.5, ly + 2.5, 0.0, 24.0)

    m.add_box(-1.8, 1.8, 16.0, 24.0, 38.0, 46.0)
    return m


# =============================================================================
# REGISTRY OF ALL 26 LIVESTOCK MODELS
# =============================================================================

LIVESTOCK_ANIMALS_REGISTRY = [
    # 1. Cattle Family (3 Adults + 2 Calves)
    ("SM_Animal_Cow_Holstein",     lambda: build_animal_cow_holstein("SM_Animal_Cow_Holstein"),     "livestock_cow_holstein.png",  "0.8x1.8m", "Classic black & white Holstein dairy cow"),
    ("SM_Animal_Cow_Jersey",       lambda: build_animal_cow_jersey("SM_Animal_Cow_Jersey"),         "livestock_cow_jersey.png",    "0.8x1.8m", "Caramel tan Jersey dairy cow with cream muzzle ring"),
    ("SM_Animal_Cow_Highland",     lambda: build_animal_cow_highland("SM_Animal_Cow_Highland"),     "livestock_cow_highland.png",  "1.1x2.1m", "Shaggy Scottish Highland cow with 110cm wide horns & fringe"),
    ("SM_Animal_Cow_Calf",         lambda: build_animal_cow_calf("SM_Animal_Cow_Calf"),             "baby_calf.png",               "0.5x1.1m", "Young chestnut calf with white forehead star"),
    ("SM_Animal_Cow_Calf_Spotted", lambda: build_animal_cow_calf_spotted("SM_Animal_Cow_Calf_Spotted"), "baby_calf_spotted.png", "0.5x1.1m", "Black & white spotted Holstein calf"),

    # 2. Chicken Family (3 Adults + 1 Chick)
    ("SM_Animal_Chicken_Red",      lambda: build_animal_chicken_red("SM_Animal_Chicken_Red"),       "livestock_chicken_red.png",   "0.3x0.5m", "Rhode Island Red laying hen"),
    ("SM_Animal_Chicken_White",    lambda: build_animal_chicken_white("SM_Animal_Chicken_White"),   "livestock_chicken_white.png", "0.3x0.5m", "White Leghorn egg-laying hen with upright tail"),
    ("SM_Animal_Chicken_Barred",   lambda: build_animal_chicken_barred("SM_Animal_Chicken_Barred"), "livestock_chicken_barred.png","0.3x0.5m", "Barred Rock chicken with black & white plumage stripes"),
    ("SM_Animal_Chicken_Chick",    lambda: build_animal_chicken_chick("SM_Animal_Chicken_Chick"),   "baby_chick.png",              "0.1x0.2m", "Downy golden-yellow baby chick"),

    # 3. Pig Family (3 Adults + 1 Piglet)
    ("SM_Animal_Pig_Pink",         lambda: build_animal_pig_pink("SM_Animal_Pig_Pink"),             "livestock_pig_pink.png",      "0.6x1.5m", "Rosy pink Yorkshire homestead pig"),
    ("SM_Animal_Pig_Hampshire",    lambda: build_animal_pig_hampshire("SM_Animal_Pig_Hampshire"),   "livestock_pig_hampshire.png", "0.6x1.5m", "Hampshire pig: black with solid white shoulder belt"),
    ("SM_Animal_Pig_Duroc",        lambda: build_animal_pig_duroc("SM_Animal_Pig_Duroc"),           "livestock_pig_duroc.png",     "0.6x1.5m", "Duroc pig: deep reddish-brown with drooping ears"),
    ("SM_Animal_Pig_Piglet",       lambda: build_animal_pig_piglet("SM_Animal_Pig_Piglet"),         "baby_piglet.png",             "0.3x0.7m", "Chubby pink piglet with button snout"),

    # 4. Sheep Family (3 Adults + 1 Lamb)
    ("SM_Animal_Sheep_Suffolk",    lambda: build_animal_sheep_suffolk("SM_Animal_Sheep_Suffolk"),   "livestock_sheep_suffolk.png", "0.6x1.2m", "Suffolk sheep: white wool with black face & legs"),
    ("SM_Animal_Sheep_White",      lambda: build_animal_sheep_white("SM_Animal_Sheep_White"),       "livestock_sheep_white.png",   "0.6x1.2m", "White sheep: full white fleece and pale face"),
    ("SM_Animal_Sheep_Tan",        lambda: build_animal_sheep_tan("SM_Animal_Sheep_Tan"),           "livestock_sheep_tan.png",     "0.6x1.2m", "Tan sheep: natural caramel tan fleece"),
    ("SM_Animal_Sheep_Lamb",       lambda: build_animal_sheep_lamb("SM_Animal_Sheep_Lamb"),         "baby_lamb.png",               "0.3x0.6m", "Fluffy white lamb with dark face mask"),

    # 5. Goat Family (3 Adults + 1 Kid)
    ("SM_Animal_Goat_Brown",       lambda: build_animal_goat_brown("SM_Animal_Goat_Brown"),         "livestock_goat_brown.png",    "0.5x1.0m", "Brown goat with white stripes & belly"),
    ("SM_Animal_Goat_White",       lambda: build_animal_goat_white("SM_Animal_Goat_White"),         "livestock_goat_white.png",    "0.5x1.0m", "White Saanen dairy goat with ivory horns"),
    ("SM_Animal_Goat_BlackWhite",  lambda: build_animal_goat_blackwhite("SM_Animal_Goat_BlackWhite"), "livestock_goat_blackwhite.png", "0.5x1.0m", "Piebald black & white goat with arching horns"),
    ("SM_Animal_Goat_Kid",         lambda: build_animal_goat_kid("SM_Animal_Goat_Kid"),             "baby_kid.png",                "0.3x0.6m", "Spotted brown and white kid"),

    # 6. Backwards-Compatible Generic Models (5)
    ("SM_Animal_Cow_Adult",        lambda: build_animal_cow_holstein("SM_Animal_Cow_Adult"),       "livestock_cow_holstein.png",  "0.8x1.8m", "Adult dairy/beef cow (Holstein variety)"),
    ("SM_Animal_Chicken_Hen",      lambda: build_animal_chicken_red("SM_Animal_Chicken_Hen"),       "livestock_chicken_red.png",   "0.3x0.5m", "Adult laying hen (Rhode Island Red variety)"),
    ("SM_Animal_Pig_Adult",        lambda: build_animal_pig_pink("SM_Animal_Pig_Adult"),           "livestock_pig_pink.png",      "0.6x1.5m", "Adult homestead pig (Pink variety)"),
    ("SM_Animal_Sheep_Adult",      lambda: build_animal_sheep_suffolk("SM_Animal_Sheep_Adult"),     "livestock_sheep_suffolk.png", "0.6x1.2m", "Adult wool sheep (Suffolk variety)"),
    ("SM_Animal_Goat_Adult",       lambda: build_animal_goat_brown("SM_Animal_Goat_Adult"),         "livestock_goat_brown.png",    "0.5x1.0m", "Adult dairy goat (Brown variety)"),
]


def sync_animal_icon(src_icon_name, model_name):
    src_path = os.path.join(ITEMS_DIR, src_icon_name)
    if not os.path.exists(src_path):
        for root, dirs, files in os.walk(ITEMS_DIR):
            if src_icon_name in files:
                src_path = os.path.join(root, src_icon_name)
                break

    if os.path.exists(src_path):
        hud_icon = os.path.join(HUD_RANCH_ICONS, f"{model_name}.png")
        ue5_icon = os.path.join(UE5_RANCH_ICONS, f"{model_name}.png")
        shutil.copy2(src_path, hud_icon)
        shutil.copy2(src_path, ue5_icon)
        return True
    return False


def main():
    print("=====================================================================")
    print(f"  GENERATING {len(LIVESTOCK_ANIMALS_REGISTRY)} LIVESTOCK ANIMAL MODELS (3 VARIETIES PER ANIMAL)")
    print("  Directly replicating canonical item icons in HUD/assets/items/")
    print("=====================================================================\n")

    count = 0
    for name, builder_func, icon_name, footprint, desc in LIVESTOCK_ANIMALS_REGISTRY:
        count += 1
        mesh = builder_func()
        mesh.ground_align()

        # 1. Save HUD files
        hud_obj = os.path.join(HUD_RANCH_MODELS, f"{name}.obj")
        hud_mtl = os.path.join(HUD_RANCH_MODELS, f"{name}.mtl")
        mesh.write_obj_and_mtl(hud_obj, hud_mtl)

        # 2. Sync to UE5 workspace
        ue5_obj = os.path.join(UE5_RANCH_MODELS, f"{name}.obj")
        ue5_mtl = os.path.join(UE5_RANCH_MODELS, f"{name}.mtl")
        shutil.copy2(hud_obj, ue5_obj)
        shutil.copy2(hud_mtl, ue5_mtl)

        # 3. Synchronize canonical icon
        synced = sync_animal_icon(icon_name, name)
        icon_status = f"Synced {icon_name}" if synced else f"MISSING {icon_name}"

        total_faces = sum(len(f) for f in mesh.materials.values())
        print(f"[{count:02d}/{len(LIVESTOCK_ANIMALS_REGISTRY)}] {name:<28} -> {icon_status} ({total_faces} tris)")

    print(f"\nSUCCESS: All {len(LIVESTOCK_ANIMALS_REGISTRY)} livestock models & icons generated and synchronized!\n")


if __name__ == "__main__":
    main()
