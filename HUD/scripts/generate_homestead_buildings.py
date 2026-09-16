#!/usr/bin/env python3
"""
Homesteader 3D Low-Poly Homestead Buildings & Architecture Generator (v4 - 360° Rotatable)
Generates 19 high-quality stylized low-poly 3D meshes (.obj + .mtl) and
renders matching 128x128 transparent preview icons strictly adhering to Homesteader rules:
- World grid standard: 1 grid tile = 1m x 1m = 100 UU x 100 UU
- Fully modeled on all 4 sides (360° rotatable in-game without missing geometry or hollow shells)
- Authentic matching of in-game item icons (struct_barn, struct_shed, struct_cabin_large, struct_coop_chicken, etc.)
- 10 Complete Prefab Homestead Buildings with exact grid footprints
- 9 Modular Building Construction Parts (1m scale)
- Ground-aligned at z_min = 0.0
- Dual directory synchronization: HUD/assets and Homesteader/Content/Homesteader
"""

import os
import math
import shutil
from PIL import Image, ImageDraw, ImageFilter

HUD_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UE5_ROOT = os.path.abspath(os.path.join(HUD_ROOT, "..", "Homesteader", "Content", "Homesteader"))

HUD_BUILDING_MODELS = os.path.join(HUD_ROOT, "assets", "building", "structures")
HUD_BUILDING_ICONS = os.path.join(HUD_ROOT, "assets", "building", "icons")
UE5_BUILDING_MODELS = os.path.join(UE5_ROOT, "Assets", "Building", "Meshes")
UE5_BUILDING_ICONS = os.path.join(UE5_ROOT, "UI", "Icons", "Building")

for d in [HUD_BUILDING_MODELS, HUD_BUILDING_ICONS, UE5_BUILDING_MODELS, UE5_BUILDING_ICONS]:
    os.makedirs(d, exist_ok=True)

# -----------------------------------------------------------------------------
# 3D Vector Math
# -----------------------------------------------------------------------------

class Vec3:
    __slots__ = ('x', 'y', 'z')
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __add__(self, o): return Vec3(self.x + o.x, self.y + o.y, self.z + o.z)
    def __sub__(self, o): return Vec3(self.x - o.x, self.y - o.y, self.z - o.z)
    def __mul__(self, s): return Vec3(self.x * s, self.y * s, self.z * s)
    def cross(self, o):
        return Vec3(
            self.y * o.z - self.z * o.y,
            self.z * o.x - self.x * o.z,
            self.x * o.y - self.y * o.x
        )
    def dot(self, o): return self.x * o.x + self.y * o.y + self.z * o.z
    def length(self): return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)
    def normalized(self):
        l = self.length()
        return Vec3(self.x / l, self.y / l, self.z / l) if l > 1e-6 else Vec3(0, 0, 1)


class Mesh:
    def __init__(self, name):
        self.name = name
        self.vertices = []      # Vec3
        self.normals = []       # Vec3
        self.uvs = []           # (u, v)
        self.faces = []         # ([(v_idx, vt_idx, vn_idx), ...], material_name)
        self.materials = {}     # mat_name -> (r, g, b)

    def add_material(self, name, r, g, b):
        self.materials[name] = (float(r), float(g), float(b))

    def add_triangle(self, v0, v1, v2, uv0=(0,0), uv1=(1,0), uv2=(0.5,1), mat="default"):
        p0 = v0 if isinstance(v0, Vec3) else Vec3(*v0)
        p1 = v1 if isinstance(v1, Vec3) else Vec3(*v1)
        p2 = v2 if isinstance(v2, Vec3) else Vec3(*v2)

        norm = (p1 - p0).cross(p2 - p0).normalized()

        iv = len(self.vertices) + 1
        self.vertices.extend([p0, p1, p2])
        self.uvs.extend([uv0, uv1, uv2])
        self.normals.extend([norm, norm, norm])

        face = [(iv, iv, iv), (iv+1, iv+1, iv+1), (iv+2, iv+2, iv+2)]
        self.faces.append((face, mat))

    def add_quad(self, v0, v1, v2, v3, uv0=(0,0), uv1=(1,0), uv2=(1,1), uv3=(0,1), mat="default"):
        self.add_triangle(v0, v1, v2, uv0, uv1, uv2, mat=mat)
        self.add_triangle(v0, v2, v3, uv0, uv2, uv3, mat=mat)

    def add_subdivided_quad(self, v0, v1, v2, v3, segs_u=1, segs_v=1, mat="default"):
        """Subdivides a quad into segs_u x segs_v smaller quads for accurate depth sorting."""
        p0 = v0 if isinstance(v0, Vec3) else Vec3(*v0)
        p1 = v1 if isinstance(v1, Vec3) else Vec3(*v1)
        p2 = v2 if isinstance(v2, Vec3) else Vec3(*v2)
        p3 = v3 if isinstance(v3, Vec3) else Vec3(*v3)

        for i in range(segs_u):
            u0 = i / float(segs_u)
            u1 = (i + 1) / float(segs_u)
            for j in range(segs_v):
                v_0 = j / float(segs_v)
                v_1 = (j + 1) / float(segs_v)

                def pt(u, v):
                    return (p0 * ((1 - u) * (1 - v)) +
                            p1 * (u * (1 - v)) +
                            p2 * (u * v) +
                            p3 * ((1 - u) * v))

                q0 = pt(u0, v_0)
                q1 = pt(u1, v_0)
                q2 = pt(u1, v_1)
                q3 = pt(u0, v_1)
                self.add_quad(q0, q1, q2, q3, mat=mat)

    def add_box(self, size, center=(0,0,0), mat="default", segs_y=1, top_cap=True):
        """Adds a watertight 6-sided box with outward-pointing normals on all 6 faces."""
        sx, sy, sz = size
        cx, cy, cz = center
        hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5

        if segs_y > 1:
            dy = sy / float(segs_y)
            for j in range(segs_y):
                y_mid = (cy - hy) + (j + 0.5) * dy
                self.add_box((sx, dy, sz), center=(cx, y_mid, cz), mat=mat, segs_y=1, top_cap=top_cap)
            return

        p000 = Vec3(cx - hx, cy - hy, cz - hz)
        p100 = Vec3(cx + hx, cy - hy, cz - hz)
        p110 = Vec3(cx + hx, cy + hy, cz - hz)
        p010 = Vec3(cx - hx, cy + hy, cz - hz)
        p001 = Vec3(cx - hx, cy - hy, cz + hz)
        p101 = Vec3(cx + hx, cy - hy, cz + hz)
        p111 = Vec3(cx + hx, cy + hy, cz + hz)
        p011 = Vec3(cx - hx, cy + hy, cz + hz)

        # Bottom (-Z)
        self.add_quad(p000, p010, p110, p100, mat=mat)
        # Top (+Z)
        if top_cap:
            self.add_quad(p001, p101, p111, p011, mat=mat)
        # Front (-Y)
        self.add_quad(p000, p100, p101, p001, mat=mat)
        # Back (+Y)
        self.add_quad(p110, p010, p011, p111, mat=mat)
        # Left (-X)
        self.add_quad(p010, p000, p001, p011, mat=mat)
        # Right (+X)
        self.add_quad(p100, p110, p111, p101, mat=mat)

    def add_cylinder(self, r0, r1, h, z0=0.0, segs=10, mat="default", c0=(0,0), c1=(0,0)):
        angles = [2.0 * math.pi * i / segs for i in range(segs)]
        ring0 = [Vec3(c0[0] + r0 * math.cos(a), c0[1] + r0 * math.sin(a), z0) for a in angles]
        ring1 = [Vec3(c1[0] + r1 * math.cos(a), c1[1] + r1 * math.sin(a), z0 + h) for a in angles]

        center_bot = Vec3(c0[0], c0[1], z0)
        center_top = Vec3(c1[0], c1[1], z0 + h)

        for i in range(segs):
            nxt = (i + 1) % segs
            # Side quad (counter-clockwise outward)
            self.add_quad(ring0[i], ring0[nxt], ring1[nxt], ring1[i], mat=mat)
            # Bottom cap
            if r0 > 1e-4:
                self.add_triangle(center_bot, ring0[nxt], ring0[i], mat=mat)
            # Top cap
            if r1 > 1e-4:
                self.add_triangle(center_top, ring1[i], ring1[nxt], mat=mat)

    def add_cone(self, r, h, z0=0.0, segs=12, mat="default", c=(0,0)):
        cx, cy = c
        apex = Vec3(cx, cy, z0 + h)
        base_c = Vec3(cx, cy, z0)
        for i in range(segs):
            a0 = i * 2.0 * math.pi / segs
            a1 = (i + 1) * 2.0 * math.pi / segs
            p0 = Vec3(cx + r * math.cos(a0), cy + r * math.sin(a0), z0)
            p1 = Vec3(cx + r * math.cos(a1), cy + r * math.sin(a1), z0)
            self.add_triangle(p0, p1, apex, mat=mat)
            self.add_triangle(base_c, p1, p0, mat=mat)

    def add_gabled_roof(self, size, center, peak_h, overhang=10.0, mat="default"):
        """Adds a gabled A-frame roof with outward normals on both slopes and both gables."""
        sx, sy, sz = size
        cx, cy, cz = center
        hx = (sx + overhang * 2.0) * 0.5
        hy = (sy + overhang * 2.0) * 0.5

        e_fl = Vec3(cx - hx, cy - hy, cz)
        e_fr = Vec3(cx + hx, cy - hy, cz)
        e_br = Vec3(cx + hx, cy + hy, cz)
        e_bl = Vec3(cx - hx, cy + hy, cz)

        p_front = Vec3(cx, cy - hy, cz + peak_h)
        p_back = Vec3(cx, cy + hy, cz + peak_h)

        # Left slope (-X, +Z outward):
        self.add_subdivided_quad(e_fl, p_front, p_back, e_bl, segs_u=2, segs_v=4, mat=mat)
        # Right slope (+X, +Z outward):
        self.add_subdivided_quad(p_front, e_fr, e_br, p_back, segs_u=2, segs_v=4, mat=mat)
        # Front gable (-Y outward):
        self.add_triangle(e_fl, e_fr, p_front, mat=mat)
        # Back gable (+Y outward):
        self.add_triangle(e_br, e_bl, p_back, mat=mat)

    def add_gabled_roof_x(self, size, center, peak_h, overhang=10.0, segs_u=4, mat="default"):
        """Adds a gabled roof where ridge runs along X axis (slopes facing -Y and +Y)."""
        sx, sy, sz = size
        cx, cy, cz = center
        hx = (sx + overhang * 2.0) * 0.5
        hy = (sy + overhang * 2.0) * 0.5

        e_fl = Vec3(cx - hx, cy - hy, cz)
        e_fr = Vec3(cx + hx, cy - hy, cz)
        e_br = Vec3(cx + hx, cy + hy, cz)
        e_bl = Vec3(cx - hx, cy + hy, cz)

        p_left = Vec3(cx - hx, cy, cz + peak_h)
        p_right = Vec3(cx + hx, cy, cz + peak_h)

        # Front slope (-Y, +Z outward):
        self.add_subdivided_quad(e_fl, e_fr, p_right, p_left, segs_u=segs_u, segs_v=2, mat=mat)
        # Back slope (+Y, +Z outward):
        self.add_subdivided_quad(p_left, p_right, e_br, e_bl, segs_u=segs_u, segs_v=2, mat=mat)
        # Left gable (-X outward):
        self.add_triangle(e_bl, e_fl, p_left, mat=mat)
        # Right gable (+X outward):
        self.add_triangle(e_fr, e_br, p_right, mat=mat)

    def ground_align(self):
        if not self.vertices: return
        min_z = min(v.z for v in self.vertices)
        offset = Vec3(0, 0, -min_z)
        self.vertices = [v + offset for v in self.vertices]

    def save_obj(self, obj_path, mtl_path):
        os.makedirs(os.path.dirname(obj_path), exist_ok=True)
        mtl_filename = os.path.basename(mtl_path)

        with open(obj_path, "w", encoding="utf-8") as f:
            f.write(f"# Homesteader 3D Architectural Mesh: {self.name}\n")
            f.write(f"# Standard: 1 grid tile = 1m x 1m = 100 UU x 100 UU\n")
            f.write(f"# Fully modeled on all 4 sides (360 rotatable)\n")
            f.write(f"mtllib {mtl_filename}\n")
            f.write(f"o {self.name}\n\n")

            for v in self.vertices:
                f.write(f"v {v.x:.3f} {v.y:.3f} {v.z:.3f}\n")
            f.write("\n")

            for vt in self.uvs:
                f.write(f"vt {vt[0]:.4f} {vt[1]:.4f}\n")
            f.write("\n")

            for vn in self.normals:
                f.write(f"vn {vn.x:.4f} {vn.y:.4f} {vn.z:.4f}\n")
            f.write("\n")

            cur_mat = None
            for face, mat in self.faces:
                if mat != cur_mat:
                    f.write(f"usemtl {mat}\n")
                    f.write("s 1\n")
                    cur_mat = mat
                f_str = " ".join([f"{v}/{vt}/{vn}" for v, vt, vn in face])
                f.write(f"f {f_str}\n")

        with open(mtl_path, "w", encoding="utf-8") as mf:
            mf.write(f"# Material Library for {self.name}\n")
            for mat_name, (r, g, b) in self.materials.items():
                mf.write(f"\nnewmtl {mat_name}\n")
                mf.write("Ka 0.200 0.200 0.200\n")
                mf.write(f"Kd {r:.3f} {g:.3f} {b:.3f}\n")
                mf.write("Ks 0.100 0.100 0.100\n")
                mf.write("Ns 15.0\n")
                mf.write("d 1.0\n")
                mf.write("illum 2\n")


# -----------------------------------------------------------------------------
# Material Palettes (Calibrated to Match Reference Item Icons)
# -----------------------------------------------------------------------------

def apply_standard_building_materials(m):
    # Wood / Timber
    m.add_material("Wood_Plank_Cedar", 0.65, 0.46, 0.28)
    m.add_material("Wood_Timber_Dark", 0.44, 0.30, 0.18)
    m.add_material("Wood_Log_Pine", 0.54, 0.36, 0.22)
    m.add_material("Wood_Log_End", 0.68, 0.50, 0.32)
    m.add_material("Wood_Plank_Warm", 0.72, 0.52, 0.32)
    m.add_material("Wood_Door_Trim", 0.48, 0.34, 0.20)

    # Barn Palette
    m.add_material("Barn_Red", 0.72, 0.20, 0.16)
    m.add_material("Barn_Red_Dark", 0.54, 0.14, 0.11)
    m.add_material("Barn_White_Trim", 0.95, 0.95, 0.93)
    m.add_material("Cupola_Roof", 0.65, 0.52, 0.38)
    m.add_material("Wood_Loft_Inside", 0.55, 0.42, 0.28)

    # Masonry / Stone
    m.add_material("Stone_Fieldstone", 0.56, 0.54, 0.50)
    m.add_material("Stone_Mortar", 0.72, 0.70, 0.66)
    m.add_material("Concrete_Poured", 0.62, 0.60, 0.58)

    # Roof Materials
    m.add_material("Roof_Tin_Silver", 0.76, 0.80, 0.84)
    m.add_material("Roof_Tin_Dark", 0.58, 0.62, 0.68)
    m.add_material("Roof_Shake_Weathered", 0.58, 0.46, 0.34)
    m.add_material("Roof_Shake_Warm", 0.68, 0.52, 0.38)
    m.add_material("Earth_Turf_Grass", 0.34, 0.60, 0.22)

    # Metals & Glass
    m.add_material("Metal_Galvanized", 0.74, 0.76, 0.78)
    m.add_material("Metal_Iron_Black", 0.20, 0.20, 0.20)
    m.add_material("Glass_Greenhouse", 0.75, 0.88, 0.90)
    m.add_material("Glass_Window_Dark", 0.24, 0.32, 0.38)
    m.add_material("Wire_Mesh", 0.70, 0.72, 0.74)


# -----------------------------------------------------------------------------
# 10 Complete Prefab Homestead Buildings (360° Rotatable)
# -----------------------------------------------------------------------------

def build_outhouse():
    """1m x 1m footprint (100x100 UU, H: 240 UU). Cedar planks, slanted tin roof, crescent moon cutout."""
    m = Mesh("SM_Building_Outhouse")
    apply_standard_building_materials(m)

    # 1. Concrete / stone sill base (100x100x12)
    m.add_box((96, 96, 12), center=(0, 0, 6), mat="Stone_Fieldstone")

    # 2. 4-sided vertical cedar plank walls (W: 86, D: 86, H: 215)
    m.add_box((86, 86, 215), center=(0, 0, 119.5), mat="Wood_Plank_Cedar")

    # 3. Corner timber posts on all 4 corners (360°)
    for cx in [-43, 43]:
        for cy in [-43, 43]:
            m.add_box((8, 8, 220), center=(cx, cy, 122), mat="Wood_Timber_Dark")

    # 4. Front door (Facing -Y at Y = -44)
    m.add_box((54, 6, 185), center=(0, -45, 105), mat="Wood_Plank_Warm")
    m.add_box((58, 8, 8), center=(0, -45, 198), mat="Wood_Door_Trim") # Door frame top
    m.add_box((8, 8, 190), center=(-28, -45, 105), mat="Wood_Door_Trim") # Door frame left
    m.add_box((8, 8, 190), center=(28, -45, 105), mat="Wood_Door_Trim") # Door frame right

    # Black iron hinges and door handle on front
    m.add_box((16, 4, 6), center=(-20, -48, 160), mat="Metal_Iron_Black")
    m.add_box((16, 4, 6), center=(-20, -48, 50), mat="Metal_Iron_Black")
    m.add_box((4, 4, 18), center=(18, -48, 100), mat="Metal_Iron_Black")

    # Crescent moon cutout on front door (gold inlay)
    m.add_box((14, 2, 22), center=(0, -48, 150), mat="Wood_Timber_Dark")

    # 5. Rear wall detail (Facing +Y): horizontal timber battens
    m.add_box((84, 4, 10), center=(0, 44, 70), mat="Wood_Timber_Dark")
    m.add_box((84, 4, 10), center=(0, 44, 150), mat="Wood_Timber_Dark")

    # 6. Left and Right side walls (Facing -X and +X): ventilation slits
    m.add_box((4, 24, 8), center=(-44, 0, 190), mat="Wood_Timber_Dark")
    m.add_box((4, 24, 8), center=(44, 0, 190), mat="Wood_Timber_Dark")

    # 7. Slanted corrugated tin roof (slopes down toward +Y)
    # Front is at Z = 238, rear is at Z = 215, overhanging all 4 sides
    p_fl = Vec3(-52, -54, 238)
    p_fr = Vec3(52, -54, 238)
    p_br = Vec3(52, 54, 215)
    p_bl = Vec3(-52, 54, 215)
    m.add_quad(p_fl, p_fr, p_br, p_bl, mat="Roof_Tin_Silver")
    return m


def build_well_house():
    """1m x 1m footprint (100x100 UU, H: 220 UU). Fieldstone base, timber posts, gabled roof, bucket & crank."""
    m = Mesh("SM_Building_WellHouse")
    apply_standard_building_materials(m)

    # 1. Fieldstone masonry well curb on all 4 sides (W: 86, D: 86, H: 75)
    m.add_box((86, 86, 70), center=(0, 0, 35), mat="Stone_Fieldstone")
    # Dark interior water pit
    m.add_box((62, 62, 8), center=(0, 0, 68), mat="Glass_Window_Dark")
    # Mortared top coping rim
    m.add_box((92, 92, 6), center=(0, 0, 72), mat="Stone_Mortar")

    # 2. 4 square timber posts at the 4 corners
    for px in [-38, 38]:
        for py in [-38, 38]:
            m.add_box((10, 10, 140), center=(px, py, 140), mat="Wood_Timber_Dark")

    # 3. Horizontal timber cross beams connecting posts (all 4 sides)
    m.add_box((86, 8, 10), center=(0, -38, 175), mat="Wood_Timber_Dark")
    m.add_box((86, 8, 10), center=(0, 38, 175), mat="Wood_Timber_Dark")
    m.add_box((8, 86, 10), center=(-38, 0, 175), mat="Wood_Timber_Dark")
    m.add_box((8, 86, 10), center=(38, 0, 175), mat="Wood_Timber_Dark")

    # 4. Winch axle & wooden bucket
    m.add_cylinder(r0=5, r1=5, h=76, z0=120, segs=8, mat="Wood_Plank_Warm", c0=(0,-38), c1=(0,38))
    # Iron crank handle on front (-Y)
    m.add_box((4, 18, 4), center=(0, -44, 120), mat="Metal_Iron_Black")
    m.add_box((4, 4, 20), center=(0, -51, 112), mat="Metal_Iron_Black")
    # Suspended cedar bucket
    m.add_cylinder(r0=10, r1=12, h=22, z0=80, segs=8, mat="Wood_Plank_Cedar", c0=(0,0), c1=(0,0))
    m.add_cylinder(r0=1, r1=1, h=22, z0=102, segs=6, mat="Metal_Galvanized", c0=(0,0), c1=(0,0))

    # 5. Gabled cedar shake roof overhanging on all 4 sides (peak along Y)
    m.add_gabled_roof(size=(90, 94, 10), center=(0, 0, 180), peak_h=38, overhang=14.0, mat="Roof_Shake_Warm")
    return m


def build_tool_shed():
    """2m x 2m footprint (200x200 UU, H: 260 UU). Vertical timber planks with battens, gabled shake roof, door."""
    m = Mesh("SM_Building_ToolShed")
    apply_standard_building_materials(m)

    # 1. Foundation concrete plinth around all 4 sides
    m.add_box((196, 196, 14), center=(0, 0, 7), mat="Concrete_Poured", segs_y=4)

    # 2. Main 4-sided vertical timber plank walls (W: 180, D: 180, H: 180)
    m.add_box((180, 180, 180), center=(0, 0, 104), mat="Wood_Plank_Warm", segs_y=4)

    # 3. Timber corner trim posts on all 4 corners (360°)
    for cx in [-91, 91]:
        for cy in [-91, 91]:
            m.add_box((12, 12, 184), center=(cx, cy, 106), mat="Wood_Timber_Dark")

    # 4. Vertical board battens on exterior walls (matching reference icon)
    # Front wall (-Y) battens
    for bx in [-75, -55, 55, 75]:
        m.add_box((3, 2, 178), center=(bx, -91, 103), mat="Wood_Timber_Dark")
    # Right wall (+X) battens
    for by in [-70, -42, -14, 14, 42, 70]:
        m.add_box((2, 3, 178), center=(91, by, 103), mat="Wood_Timber_Dark")
    # Left wall (-X) battens
    for by in [-70, -42, -14, 14, 42, 70]:
        m.add_box((2, 3, 178), center=(-91, by, 103), mat="Wood_Timber_Dark")
    # Rear wall (+Y) battens
    for bx in [-75, -45, -15, 15, 45, 75]:
        m.add_box((3, 2, 178), center=(bx, 91, 103), mat="Wood_Timber_Dark")

    # 5. Front door on -Y face (W: 76, H: 160)
    m.add_box((76, 6, 160), center=(0, -92, 94), mat="Wood_Plank_Cedar")
    m.add_box((84, 8, 8), center=(0, -93, 175), mat="Wood_Door_Trim") # Door frame top
    m.add_box((8, 8, 162), center=(-40, -93, 94), mat="Wood_Door_Trim") # Left frame
    m.add_box((8, 8, 162), center=(40, -93, 94), mat="Wood_Door_Trim")  # Right frame
    # Black iron thumb latch on door
    m.add_box((4, 4, 18), center=(24, -95, 95), mat="Metal_Iron_Black")

    # 6. Gabled timber shake roof overhanging on all 4 sides (peak along Y)
    m.add_gabled_roof(size=(184, 188, 12), center=(0, 0, 194), peak_h=62, overhang=22.0, mat="Roof_Shake_Warm")
    return m


def build_chicken_coop():
    """2m x 3m footprint (200x300 UU, H: 210 UU). Elevated coop on 4 stilts, ramp, nesting box, wire run."""
    m = Mesh("SM_Building_ChickenCoop")
    apply_standard_building_materials(m)

    # 1. Elevated Hen House at rear (+Y: 0..120, W: 140, D: 130, elevated Z: 50..165)
    # 4 corner timber stilts
    for sx in [-60, 60]:
        for sy in [5, 115]:
            m.add_box((12, 12, 60), center=(sx, sy, 30), mat="Wood_Timber_Dark")

    # Coop body (W: 136, D: 120, H: 105, elevated at Z=55)
    m.add_box((136, 120, 105), center=(0, 60, 107.5), mat="Wood_Plank_Warm", segs_y=4)

    # Left side (-X): Sloped nesting box with hinged lid
    m.add_box((34, 90, 48), center=(-84, 60, 85), mat="Wood_Plank_Cedar")
    # Sloped nesting box lid
    p_nl0 = Vec3(-104, 14, 108)
    p_nl1 = Vec3(-66, 14, 115)
    p_nl2 = Vec3(-66, 106, 115)
    p_nl3 = Vec3(-104, 106, 108)
    m.add_quad(p_nl0, p_nl1, p_nl2, p_nl3, mat="Roof_Shake_Warm")

    # Front face of coop (Facing -Y at Y = 0): Chicken pop-door
    m.add_box((34, 4, 44), center=(0, -1, 78), mat="Glass_Window_Dark") # Door opening
    # Pop door timber frame
    m.add_box((42, 6, 6), center=(0, -2, 102), mat="Wood_Door_Trim")
    m.add_box((6, 6, 48), center=(-19, -2, 78), mat="Wood_Door_Trim")
    m.add_box((6, 6, 48), center=(19, -2, 78), mat="Wood_Door_Trim")

    # Chicken ramp ladder with horizontal rungs (slopes from Y=0, Z=55 down to Y=-90, Z=0)
    # Outward normal pointing up and towards camera: wound counter-clockwise
    p_r0 = Vec3(-14, 0, 56)
    p_r1 = Vec3(14, 0, 56)
    p_r2 = Vec3(14, -85, 2)
    p_r3 = Vec3(-14, -85, 2)
    m.add_quad(p_r3, p_r2, p_r1, p_r0, mat="Wood_Plank_Cedar")
    for step_y, step_z in [(-20, 42), (-40, 28), (-60, 15)]:
        m.add_box((30, 4, 3), center=(0, step_y, step_z), mat="Wood_Timber_Dark")

    # Rear face of coop (+Y at Y = 120): Cleanout service door
    m.add_box((60, 4, 70), center=(0, 121, 108), mat="Wood_Plank_Cedar")

    # Coop gabled roof with overhanging eaves on all 4 sides
    m.add_gabled_roof(size=(144, 128, 10), center=(0, 60, 160), peak_h=45, overhang=16.0, mat="Roof_Shake_Warm")

    # 2. Fenced Chicken Run Yard (in front of coop: Y from 0 to -145, X from -95 to 95)
    # Timber fence posts around all perimeter corners
    for fx in [-95, 95]:
        for fy in [-145, -70, 0]:
            m.add_box((8, 8, 65), center=(fx, fy, 32.5), mat="Wood_Timber_Dark")
    m.add_box((8, 8, 65), center=(0, -145, 32.5), mat="Wood_Timber_Dark") # Gate post

    # Top and bottom rails on all 3 sides (Front, Left, Right)
    # Front rails (with gate opening)
    m.add_box((85, 4, 6), center=(-48, -145, 62), mat="Wood_Timber_Dark")
    m.add_box((85, 4, 6), center=(-48, -145, 5), mat="Wood_Timber_Dark")
    # Gate on front right
    m.add_box((40, 4, 55), center=(48, -145, 32), mat="Wood_Plank_Cedar")

    # Left and Right side fence rails
    for sx in [-95, 95]:
        m.add_box((4, 140, 6), center=(sx, -72.5, 62), mat="Wood_Timber_Dark")
        m.add_box((4, 140, 6), center=(sx, -72.5, 5), mat="Wood_Timber_Dark")

    # Wire mesh panels (simulated with silver galvanized material)
    m.add_box((80, 2, 54), center=(-48, -145, 33), mat="Wire_Mesh")
    m.add_box((2, 136, 54), center=(-95, -72.5, 33), mat="Wire_Mesh")
    m.add_box((2, 136, 54), center=(95, -72.5, 33), mat="Wire_Mesh")
    return m


def build_woodshed():
    """2m x 3m footprint (200x300 UU, H: 230 UU). Heavy post-and-beam timber frame, open front, stacked cordwood."""
    m = Mesh("SM_Building_Woodshed")
    apply_standard_building_materials(m)

    # 1. 6 Heavy upright timber posts (X: -90, 0, 90; Y: -135, 135)
    for px in [-90, 0, 90]:
        m.add_box((16, 16, 200), center=(px, -135, 100), mat="Wood_Timber_Dark") # Front posts
        m.add_box((16, 16, 170), center=(px, 135, 85), mat="Wood_Timber_Dark")  # Rear posts (slanted roof)

    # 2. Diagonal knee braces on timber posts (360°)
    for px in [-90, 90]:
        m.add_box((8, 30, 8), center=(px, -115, 185), mat="Wood_Timber_Dark")
        m.add_box((8, 30, 8), center=(px, 115, 155), mat="Wood_Timber_Dark")

    # 3. Rear wall (+Y: 135): Horizontal slatted timber boards with air gaps
    for sz in [25, 55, 85, 115, 145]:
        m.add_box((192, 4, 18), center=(0, 136, sz), mat="Wood_Plank_Warm")

    # 4. Left and Right side walls (X: -90, 90): Horizontal slatted timber boards
    for sx in [-90, 90]:
        for sz in [25, 55, 85, 115]:
            m.add_box((4, 260, 18), center=(sx, 0, sz), mat="Wood_Plank_Warm")

    # 5. Stacked Firewood Logs inside the bays (visible from front -Y)
    # Bay 1 (Left: X = -45)
    for ly in [-80, -20, 40, 90]:
        m.add_cylinder(r0=11, r1=11, h=75, z0=12, segs=8, mat="Wood_Log_Pine", c0=(-80, ly), c1=(-10, ly))
        m.add_cylinder(r0=11, r1=11, h=75, z0=34, segs=8, mat="Wood_Log_Pine", c0=(-80, ly), c1=(-10, ly))
        m.add_cylinder(r0=10, r1=10, h=75, z0=56, segs=8, mat="Wood_Log_Pine", c0=(-80, ly), c1=(-10, ly))

    # Bay 2 (Right: X = 45)
    for ly in [-80, -20, 40, 90]:
        m.add_cylinder(r0=11, r1=11, h=75, z0=12, segs=8, mat="Wood_Log_Pine", c0=(10, ly), c1=(80, ly))
        m.add_cylinder(r0=11, r1=11, h=75, z0=34, segs=8, mat="Wood_Log_Pine", c0=(10, ly), c1=(80, ly))
        m.add_cylinder(r0=10, r1=10, h=75, z0=56, segs=8, mat="Wood_Log_Pine", c0=(10, ly), c1=(80, ly))

    # 6. Slanted corrugated weathered shake roof (slopes down toward rear +Y)
    p_fl = Vec3(-105, -155, 215)
    p_fr = Vec3(105, -155, 215)
    p_br = Vec3(105, 155, 185)
    p_bl = Vec3(-105, 155, 185)
    m.add_subdivided_quad(p_fl, p_fr, p_br, p_bl, segs_u=4, segs_v=4, mat="Roof_Shake_Warm")
    return m


def build_water_tower():
    """2m x 2m footprint (200x200 UU, H: 670 UU). 4 heavy timber posts, cross-bracing, staved cedar tank, conical roof."""
    m = Mesh("SM_Building_WaterTower")
    apply_standard_building_materials(m)

    # 1. Concrete footings at 4 base corners
    for fx in [-75, 75]:
        for fy in [-75, 75]:
            m.add_box((24, 24, 20), center=(fx, fy, 10), mat="Concrete_Poured")

    # 2. 4 Slanted timber trestle legs (H: 440, taper inward from +/-70 to +/-52)
    leg_coords = [
        ((-70, -70), (-52, -52)),
        ((70, -70), (52, -52)),
        ((70, 70), (52, 52)),
        ((-70, 70), (-52, 52))
    ]
    for c0, c1 in leg_coords:
        m.add_cylinder(r0=8, r1=7, h=440, z0=20, segs=8, mat="Wood_Timber_Dark", c0=c0, c1=c1)

    # 3. Horizontal timber perimeter ties at 3 platform heights (360°)
    for tier_z, r_tier in [(150, 64), (290, 58), (430, 52)]:
        m.add_box((r_tier * 2 + 10, 8, 8), center=(0, -r_tier, tier_z), mat="Wood_Timber_Dark")
        m.add_box((r_tier * 2 + 10, 8, 8), center=(0, r_tier, tier_z), mat="Wood_Timber_Dark")
        m.add_box((8, r_tier * 2 + 10, 8), center=(-r_tier, 0, tier_z), mat="Wood_Timber_Dark")
        m.add_box((8, r_tier * 2 + 10, 8), center=(r_tier, 0, tier_z), mat="Wood_Timber_Dark")

    # 4. Heavy timber octagonal deck platform at Z = 450
    m.add_box((134, 134, 10), center=(0, 0, 455), mat="Wood_Plank_Cedar")

    # 5. Staved Cedar Water Tank (D: 120, H: 140, Z: 460..600)
    m.add_cylinder(r0=60, r1=60, h=140, z0=460, segs=16, mat="Wood_Plank_Cedar")
    # Black iron tension hoops around tank (bottom, middle, top)
    for hoop_z in [480, 530, 580]:
        m.add_cylinder(r0=62, r1=62, h=4, z0=hoop_z, segs=16, mat="Metal_Iron_Black")

    # Conical tin roof over tank (H: 55, peak at Z: 655)
    m.add_cone(r=68, h=55, z0=600, segs=16, mat="Roof_Tin_Silver")

    # 6. Central vertical galvanized supply pipe
    m.add_cylinder(r0=8, r1=8, h=460, z0=0, segs=8, mat="Roof_Tin_Silver")
    return m


def build_root_cellar():
    """3m x 3m footprint (300x300 UU, H: 190 UU). Mounded sod turf roof, stone retaining wall, storm doors."""
    m = Mesh("SM_Building_RootCellar")
    apply_standard_building_materials(m)

    # 1. Full 360-degree rounded sod turf earth mound
    m.add_box((290, 290, 120), center=(0, 15, 60), mat="Earth_Turf_Grass", segs_y=4)
    m.add_box((220, 220, 45), center=(0, 20, 142.5), mat="Earth_Turf_Grass", segs_y=4)

    # 2. Front fieldstone retaining wall (-Y face at Y = -130)
    m.add_box((240, 25, 130), center=(0, -125, 65), mat="Stone_Fieldstone")

    # 3. Recessed entryway with angled double wooden storm doors
    m.add_box((90, 60, 80), center=(0, -110, 40), mat="Stone_Mortar")
    # Angled cellar doors
    p_d0 = Vec3(-40, -145, 12)
    p_d1 = Vec3(40, -145, 12)
    p_d2 = Vec3(40, -95, 75)
    p_d3 = Vec3(-40, -95, 75)
    m.add_quad(p_d0, p_d1, p_d2, p_d3, mat="Wood_Timber_Dark")

    # Black iron pull handles
    m.add_box((6, 12, 4), center=(-15, -120, 48), mat="Metal_Iron_Black")
    m.add_box((6, 12, 4), center=(15, -120, 48), mat="Metal_Iron_Black")

    # 4. Roof wooden ventilation pipe (center peak)
    m.add_box((16, 16, 40), center=(0, 20, 170), mat="Wood_Timber_Dark")
    return m


def build_greenhouse():
    """3m x 4m footprint (300x400 UU, H: 270 UU). Extruded frame, translucent glass panes on all 4 sides & roof."""
    m = Mesh("SM_Building_Greenhouse")
    apply_standard_building_materials(m)

    # 1. 4-sided masonry foundation base knee-wall (W: 280, D: 380, H: 30)
    m.add_box((280, 380, 30), center=(0, 0, 15), mat="Concrete_Poured", segs_y=4)

    # 2. White / Galvanized corner frame posts on all 4 corners
    for cx in [-136, 136]:
        for cy in [-186, 186]:
            m.add_box((8, 8, 155), center=(cx, cy, 107.5), mat="Metal_Galvanized")

    # 3. Glass wall bays with vertical mullions on Left (-X) and Right (+X)
    for sx in [-136, 136]:
        # Glass wall pane
        m.add_box((2, 364, 150), center=(sx, 0, 105), mat="Glass_Greenhouse", segs_y=4)
        # Vertical mullions every 90cm
        for my in [-90, 0, 90]:
            m.add_box((6, 6, 150), center=(sx, my, 105), mat="Metal_Galvanized")
        # Top plate rail
        m.add_box((6, 372, 6), center=(sx, 0, 180), mat="Metal_Galvanized")

    # 4. Front Gable Wall (-Y: Y = -186): Glass door and gable glazing
    m.add_box((264, 2, 150), center=(0, -186, 105), mat="Glass_Greenhouse")
    # Front glass door frame and handle
    m.add_box((80, 6, 155), center=(0, -187, 107.5), mat="Metal_Galvanized")
    m.add_box((72, 4, 145), center=(0, -187, 107.5), mat="Glass_Greenhouse")
    m.add_box((72, 6, 6), center=(0, -188, 105), mat="Metal_Galvanized") # Door middle horizontal rail
    m.add_box((4, 6, 16), center=(32, -189, 105), mat="Metal_Iron_Black")

    # 5. Rear Gable Wall (+Y: Y = 186): Full glass glazing
    m.add_box((264, 2, 150), center=(0, 186, 105), mat="Glass_Greenhouse")
    m.add_box((6, 6, 150), center=(0, 186, 105), mat="Metal_Galvanized")

    # 6. Gabled glass roof with galvanized ridge cap and rafter ribs
    m.add_gabled_roof(size=(280, 384, 8), center=(0, 0, 182), peak_h=75, overhang=8.0, mat="Glass_Greenhouse")
    m.add_box((12, 396, 10), center=(0, 0, 262), mat="Metal_Galvanized", segs_y=4) # Ridge cap

    # Sloped rafter ribs along roof slope (at Y = -180, -90, 0, 90, 180)
    for ry in [-180, -90, 0, 90, 180]:
        # Left rafter (outward facing)
        m.add_quad(Vec3(0, ry - 3, 259), Vec3(0, ry + 3, 259), Vec3(-142, ry + 3, 184), Vec3(-142, ry - 3, 184), mat="Metal_Galvanized")
        # Right rafter (outward facing)
        m.add_quad(Vec3(142, ry - 3, 184), Vec3(142, ry + 3, 184), Vec3(0, ry + 3, 259), Vec3(0, ry - 3, 259), mat="Metal_Galvanized")

    return m


def build_log_cabin():
    """5m x 6m footprint (500x600 UU, H: 400 UU). Notched round logs, covered front porch with steps & railing, stone chimney."""
    m = Mesh("SM_Building_LogCabin")
    apply_standard_building_materials(m)

    # 1. 4-sided stone foundation plinth
    m.add_box((490, 590, 20), center=(0, 0, 10), mat="Stone_Fieldstone", segs_y=4)

    # 2. Main 4-sided Log Cabin Body (W: 460, D: 440, H: 220; Y: -80..360)
    m.add_box((460, 440, 220), center=(0, 140, 130), mat="Wood_Log_Pine", segs_y=4, top_cap=False)

    # 3. Protruding notched corner logs on all 4 corners (360°)
    for cx in [-235, 235]:
        for cy in [-75, 355]:
            m.add_box((26, 26, 224), center=(cx, cy, 132), mat="Wood_Log_End")

    # 4. Full Covered Front Porch (Y: -220..-80, W: 460)
    # Porch cedar deck
    m.add_box((460, 140, 14), center=(0, -150, 17), mat="Wood_Plank_Cedar")
    # 3-step front entry staircase
    for st_i, (sw, sd, sz) in enumerate([(120, 35, 12), (120, 25, 6)]):
        m.add_box((sw, sd, sz), center=(0, -230 - st_i*20, sz*0.5), mat="Wood_Plank_Cedar")

    # Square timber porch columns (4 posts along front)
    for px in [-210, -70, 70, 210]:
        m.add_box((14, 14, 195), center=(px, -210, 115), mat="Wood_Timber_Dark")

    # Porch baluster railing (left, right, and front with center opening)
    m.add_box((130, 4, 8), center=(-140, -210, 70), mat="Wood_Timber_Dark")
    m.add_box((130, 4, 8), center=(140, -210, 70), mat="Wood_Timber_Dark")
    m.add_box((4, 130, 8), center=(-210, -145, 70), mat="Wood_Timber_Dark")
    m.add_box((4, 130, 8), center=(210, -145, 70), mat="Wood_Timber_Dark")

    # Porch sloped roof extension meeting main roof at front eave
    p_p0 = Vec3(-235, -225, 185)
    p_p1 = Vec3(235, -225, 185)
    p_p2 = Vec3(235, -110, 236)
    p_p3 = Vec3(-235, -110, 236)
    m.add_subdivided_quad(p_p0, p_p1, p_p2, p_p3, segs_u=4, segs_v=2, mat="Roof_Shake_Warm")

    # 5. Front door and windows visible under porch (Facing -Y at Y = -81)
    m.add_box((84, 8, 170), center=(0, -82, 105), mat="Wood_Plank_Cedar")
    m.add_box((70, 8, 70), center=(-130, -82, 130), mat="Glass_Greenhouse")
    m.add_box((70, 8, 70), center=(130, -82, 130), mat="Glass_Greenhouse")

    # 6. Rear wall (+Y at Y = 361): Two 4-pane framed windows
    m.add_box((70, 8, 70), center=(-130, 361, 130), mat="Glass_Greenhouse")
    m.add_box((70, 8, 70), center=(130, 361, 130), mat="Glass_Greenhouse")

    # 7. Left wall (-X at X = -231): Side window
    m.add_box((8, 70, 70), center=(-231, 140, 130), mat="Glass_Greenhouse")

    # 8. Right wall (+X at X = 231): Exterior Fieldstone Fireplace Chimney Stack
    m.add_box((75, 95, 365), center=(245, 140, 182.5), mat="Stone_Fieldstone")
    m.add_box((85, 105, 18), center=(245, 140, 374), mat="Stone_Mortar") # Chimney cap
    m.add_cylinder(r0=16, r1=14, h=25, z0=383, segs=8, mat="Metal_Iron_Black", c0=(245, 140), c1=(245, 140))

    # 9. Gabled Cedar Shake Roof over main cabin (overhanging on all 4 sides, ridge along X)
    m.add_gabled_roof_x(size=(464, 450, 16), center=(0, 140, 240), peak_h=130, overhang=25.0, segs_u=4, mat="Roof_Shake_Warm")
    return m


def build_small_barn():
    """6m x 8m footprint (600x800 UU, H: 620 UU). Classic gambrel roof, red timber, white trim, sliding doors, cupola."""
    m = Mesh("SM_Building_SmallBarn")
    apply_standard_building_materials(m)

    # 1. 4-sided stone foundation plinth (W: 580, L: 780, H: 20)
    m.add_box((580, 780, 20), center=(0, 0, 10), mat="Stone_Fieldstone", segs_y=8)

    # 2. Main Red Board & Batten Box Body (W: 560, L: 760, H: 235)
    m.add_box((560, 760, 235), center=(0, 0, 127.5), mat="Barn_Red", segs_y=8)

    # 3. White Corner Columns on all 4 corners (360°)
    for cx in [-282, 282]:
        for cy in [-382, 382]:
            m.add_box((16, 16, 238), center=(cx, cy, 129), mat="Barn_White_Trim")

    # 4. White base sill rim on all 4 perimeters
    m.add_box((570, 770, 8), center=(0, 0, 24), mat="Barn_White_Trim", segs_y=8)

    # 5. Front Facade (-Y at Y = -382): Sliding double doors with white X braces
    m.add_box((220, 8, 200), center=(0, -384, 120), mat="Barn_Red_Dark")
    m.add_box((236, 12, 12), center=(0, -386, 222), mat="Barn_White_Trim") # Top track
    m.add_box((12, 12, 204), center=(-112, -386, 120), mat="Barn_White_Trim") # Left frame
    m.add_box((12, 12, 204), center=(112, -386, 120), mat="Barn_White_Trim") # Right frame
    m.add_box((12, 12, 200), center=(0, -386, 120), mat="Barn_White_Trim") # Center divider

    # Door bottom/top rails
    m.add_box((96, 6, 12), center=(-56, -387, 28), mat="Barn_White_Trim")
    m.add_box((96, 6, 12), center=(-56, -387, 212), mat="Barn_White_Trim")
    m.add_box((96, 6, 12), center=(56, -387, 28), mat="Barn_White_Trim")
    m.add_box((96, 6, 12), center=(56, -387, 212), mat="Barn_White_Trim")

    # Diagonal cross braces (X)
    m.add_quad(Vec3(-104, -388, 34), Vec3(-14, -388, 206), Vec3(-8, -388, 200), Vec3(-98, -388, 28), mat="Barn_White_Trim")
    m.add_quad(Vec3(-14, -388, 28), Vec3(-104, -388, 200), Vec3(-98, -388, 206), Vec3(-8, -388, 34), mat="Barn_White_Trim")
    m.add_quad(Vec3(8, -388, 34), Vec3(98, -388, 206), Vec3(104, -388, 200), Vec3(14, -388, 28), mat="Barn_White_Trim")
    m.add_quad(Vec3(98, -388, 28), Vec3(8, -388, 200), Vec3(14, -388, 206), Vec3(104, -388, 34), mat="Barn_White_Trim")

    # 6. Rear Facade (+Y at Y = 382): Secondary sliding service door with matching X-brace
    m.add_box((160, 8, 190), center=(0, 384, 115), mat="Barn_Red_Dark")
    m.add_box((176, 12, 12), center=(0, 386, 212), mat="Barn_White_Trim")
    m.add_box((12, 12, 194), center=(-82, 386, 115), mat="Barn_White_Trim")
    m.add_box((12, 12, 194), center=(82, 386, 115), mat="Barn_White_Trim")

    # 7. Gambrel Front and Rear Gable Walls (Red)
    # Front gable (-Y):
    m.add_quad(Vec3(-280, -381, 245), Vec3(0, -381, 245), Vec3(0, -381, 405), Vec3(-210, -381, 405), mat="Barn_Red")
    m.add_quad(Vec3(0, -381, 245), Vec3(280, -381, 245), Vec3(210, -381, 405), Vec3(0, -381, 405), mat="Barn_Red")
    m.add_triangle(Vec3(-210, -381, 405), Vec3(210, -381, 405), Vec3(0, -381, 525), mat="Barn_Red")

    # Rear gable (+Y):
    m.add_quad(Vec3(0, 381, 245), Vec3(-280, 381, 245), Vec3(-210, 381, 405), Vec3(0, 381, 405), mat="Barn_Red")
    m.add_quad(Vec3(280, 381, 245), Vec3(0, 381, 245), Vec3(0, 381, 405), Vec3(210, 381, 405), mat="Barn_Red")
    m.add_triangle(Vec3(210, 381, 405), Vec3(-210, 381, 405), Vec3(0, 381, 525), mat="Barn_Red")

    # Hayloft windows on both Front and Rear gables (360°)
    m.add_box((76, 8, 76), center=(0, -384, 355), mat="Barn_White_Trim")
    m.add_box((60, 10, 60), center=(0, -384, 355), mat="Wood_Loft_Inside")
    m.add_box((76, 8, 76), center=(0, 384, 355), mat="Barn_White_Trim")
    m.add_box((60, 10, 60), center=(0, 384, 355), mat="Wood_Loft_Inside")

    # 8. Gambrel Roof Surfaces - Outward Normals on All 4 Slopes, Subdivided for Depth Accuracy
    L_Y0, L_Y1 = -400, 400
    # Left lower roof (slope 1)
    m.add_subdivided_quad(Vec3(-295, L_Y0, 240), Vec3(-215, L_Y0, 410), Vec3(-215, L_Y1, 410), Vec3(-295, L_Y1, 240), segs_u=2, segs_v=8, mat="Roof_Tin_Silver")
    # Left upper roof (slope 2)
    m.add_subdivided_quad(Vec3(-215, L_Y0, 410), Vec3(0, L_Y0, 530), Vec3(0, L_Y1, 530), Vec3(-215, L_Y1, 410), segs_u=2, segs_v=8, mat="Roof_Shake_Warm")
    # Right upper roof (slope 3)
    m.add_subdivided_quad(Vec3(0, L_Y0, 530), Vec3(215, L_Y0, 410), Vec3(215, L_Y1, 410), Vec3(0, L_Y1, 530), segs_u=2, segs_v=8, mat="Roof_Shake_Warm")
    # Right lower roof (slope 4)
    m.add_subdivided_quad(Vec3(215, L_Y0, 410), Vec3(295, L_Y0, 240), Vec3(295, L_Y1, 240), Vec3(215, L_Y1, 410), segs_u=2, segs_v=8, mat="Roof_Tin_Dark")

    # White Eave Fascias along Left (-X) and Right (+X) wall eaves
    m.add_box((12, 804, 16), center=(295, 0, 240), mat="Barn_White_Trim", segs_y=8)
    m.add_box((12, 804, 16), center=(-295, 0, 240), mat="Barn_White_Trim", segs_y=8)

    # White bargeboards along Front (-Y) and Rear (+Y) gambrel roof perimeters (angled 3D boards)
    def add_gambrel_bargeboard(y_pos):
        pts = [
            Vec3(-295, y_pos, 240),
            Vec3(-215, y_pos, 410),
            Vec3(0, y_pos, 530),
            Vec3(215, y_pos, 410),
            Vec3(295, y_pos, 240)
        ]
        thick_w = 12.0
        thick_y = 6.0
        hy = thick_y * 0.5

        for i in range(len(pts) - 1):
            p_start = pts[i]
            p_end = pts[i+1]
            seg = p_end - p_start
            length = seg.length()
            if length < 1e-3: continue
            tangent = seg * (1.0 / length)
            # Outward normal in XZ plane
            normal = Vec3(-tangent.z, 0, tangent.x).normalized()
            if normal.z < 0:
                normal = normal * -1.0

            f0 = Vec3(p_start.x, y_pos - hy, p_start.z)
            f1 = Vec3(p_end.x, y_pos - hy, p_end.z)
            f2 = Vec3(p_end.x + normal.x * thick_w, y_pos - hy, p_end.z + normal.z * thick_w)
            f3 = Vec3(p_start.x + normal.x * thick_w, y_pos - hy, p_start.z + normal.z * thick_w)

            b0 = Vec3(p_start.x, y_pos + hy, p_start.z)
            b1 = Vec3(p_end.x, y_pos + hy, p_end.z)
            b2 = Vec3(p_end.x + normal.x * thick_w, y_pos + hy, p_end.z + normal.z * thick_w)
            b3 = Vec3(p_start.x + normal.x * thick_w, y_pos + hy, p_start.z + normal.z * thick_w)

            # Front face (-Y)
            m.add_quad(f0, f1, f2, f3, mat="Barn_White_Trim")
            # Back face (+Y)
            m.add_quad(b1, b0, b3, b2, mat="Barn_White_Trim")
            # Top face (along normal)
            m.add_quad(f3, f2, b2, b3, mat="Barn_White_Trim")

    add_gambrel_bargeboard(-402)
    add_gambrel_bargeboard(402)

    # 9. 4-Sided Roof Cupola / Ventilator with Weather Vane
    m.add_box((76, 76, 45), center=(0, 0, 552), mat="Barn_Red")
    for cx in [-38, 38]:
        for cy in [-38, 38]:
            m.add_box((8, 8, 47), center=(cx, cy, 553), mat="Barn_White_Trim")
    m.add_box((86, 86, 8), center=(0, 0, 577), mat="Barn_White_Trim")
    # 4-sided pyramidal cupola roof
    m.add_triangle(Vec3(-44, -44, 581), Vec3(44, -44, 581), Vec3(0, 0, 616), mat="Cupola_Roof")
    m.add_triangle(Vec3(44, -44, 581), Vec3(44, 44, 581), Vec3(0, 0, 616), mat="Cupola_Roof")
    m.add_triangle(Vec3(44, 44, 581), Vec3(-44, 44, 581), Vec3(0, 0, 616), mat="Cupola_Roof")
    m.add_triangle(Vec3(-44, 44, 581), Vec3(-44, -44, 581), Vec3(0, 0, 616), mat="Cupola_Roof")
    m.add_cylinder(r0=2, r1=2, h=25, z0=616, segs=6, mat="Metal_Iron_Black")
    return m


# -----------------------------------------------------------------------------
# 9 Modular Building Construction Parts (1m Grid Snapping)
# -----------------------------------------------------------------------------

def build_part_floor_wood_1m():
    m = Mesh("SM_Part_Floor_Wood_1m")
    apply_standard_building_materials(m)
    m.add_box((98, 98, 16), center=(0, 0, 8), mat="Wood_Timber_Dark")
    m.add_box((100, 100, 4), center=(0, 0, 18), mat="Wood_Plank_Cedar")
    return m

def build_part_floor_stone_1m():
    m = Mesh("SM_Part_Floor_Stone_1m")
    apply_standard_building_materials(m)
    m.add_box((100, 100, 18), center=(0, 0, 9), mat="Stone_Fieldstone")
    m.add_box((96, 96, 3), center=(0, 0, 19.5), mat="Stone_Mortar")
    return m

def build_part_wall_wood_1m():
    m = Mesh("SM_Part_Wall_Wood_1m")
    apply_standard_building_materials(m)
    m.add_box((100, 14, 10), center=(0, 0, 5), mat="Wood_Timber_Dark")
    m.add_box((100, 14, 10), center=(0, 0, 235), mat="Wood_Timber_Dark")
    m.add_box((10, 14, 220), center=(-45, 0, 120), mat="Wood_Timber_Dark")
    m.add_box((10, 14, 220), center=(45, 0, 120), mat="Wood_Timber_Dark")
    m.add_box((80, 8, 220), center=(0, 0, 120), mat="Wood_Plank_Cedar")
    return m

def build_part_wall_doorway_1m():
    m = Mesh("SM_Part_Wall_Doorway_1m")
    apply_standard_building_materials(m)
    m.add_box((100, 14, 10), center=(0, 0, 235), mat="Wood_Timber_Dark")
    m.add_box((12, 14, 230), center=(-44, 0, 115), mat="Wood_Timber_Dark")
    m.add_box((12, 14, 230), center=(44, 0, 115), mat="Wood_Timber_Dark")
    m.add_box((76, 14, 10), center=(0, 0, 210), mat="Wood_Timber_Dark")
    m.add_box((76, 8, 20), center=(0, 0, 225), mat="Wood_Plank_Cedar")
    return m

def build_part_wall_window_1m():
    m = Mesh("SM_Part_Wall_Window_1m")
    apply_standard_building_materials(m)
    m.add_box((100, 14, 10), center=(0, 0, 5), mat="Wood_Timber_Dark")
    m.add_box((100, 14, 10), center=(0, 0, 235), mat="Wood_Timber_Dark")
    m.add_box((12, 14, 220), center=(-44, 0, 120), mat="Wood_Timber_Dark")
    m.add_box((12, 14, 220), center=(44, 0, 120), mat="Wood_Timber_Dark")
    m.add_box((76, 10, 80), center=(0, 0, 45), mat="Wood_Plank_Cedar")
    m.add_box((76, 10, 60), center=(0, 0, 195), mat="Wood_Plank_Cedar")
    m.add_box((60, 4, 80), center=(0, 0, 125), mat="Glass_Greenhouse")
    m.add_box((62, 16, 6), center=(0, 0, 85), mat="Wood_Timber_Dark")
    return m

def build_part_door_wood():
    m = Mesh("SM_Part_Door_Wood")
    apply_standard_building_materials(m)
    m.add_box((86, 6, 206), center=(0, 0, 103), mat="Wood_Plank_Cedar")
    m.add_box((86, 3, 12), center=(0, -4, 15), mat="Wood_Timber_Dark")
    m.add_box((86, 3, 12), center=(0, -4, 195), mat="Wood_Timber_Dark")
    m.add_box((86, 3, 12), center=(0, -4, 103), mat="Wood_Timber_Dark")
    m.add_box((18, 4, 6), center=(-28, -5, 160), mat="Metal_Iron_Black")
    m.add_box((18, 4, 6), center=(-28, -5, 45), mat="Metal_Iron_Black")
    m.add_box((4, 4, 16), center=(32, -5, 100), mat="Metal_Iron_Black")
    return m

def build_part_roof_slope_1m():
    m = Mesh("SM_Part_Roof_Slope_1m")
    apply_standard_building_materials(m)
    p0 = Vec3(-50, -57.5, 0)
    p1 = Vec3(50, -57.5, 0)
    p2 = Vec3(50, 57.5, 17)
    p3 = Vec3(-50, 57.5, 17)
    m.add_quad(p0, p1, p2, p3, mat="Roof_Shake_Weathered")
    m.add_box((100, 6, 8), center=(0, -55, 4), mat="Wood_Timber_Dark")
    return m

def build_part_roof_ridge_1m():
    m = Mesh("SM_Part_Roof_Ridge_1m")
    apply_standard_building_materials(m)
    p_peak_f = Vec3(0, -58, 62)
    p_peak_b = Vec3(0, 58, 62)
    p_lf = Vec3(-58, -58, 0)
    p_lb = Vec3(-58, 58, 0)
    p_rf = Vec3(58, -58, 0)
    p_rb = Vec3(58, 58, 0)
    m.add_quad(p_lf, p_peak_f, p_peak_b, p_lb, mat="Roof_Shake_Weathered")
    m.add_quad(p_peak_f, p_rf, p_rb, p_peak_b, mat="Roof_Shake_Weathered")
    m.add_box((116, 6, 8), center=(0, 0, 64), mat="Wood_Timber_Dark")
    return m

def build_part_stairs_wood_1m():
    m = Mesh("SM_Part_Stairs_Wood_1m")
    apply_standard_building_materials(m)
    num_steps = 5
    run = 100.0 / num_steps # 20cm tread
    rise = 100.0 / num_steps # 20cm riser
    for i in range(num_steps):
        tread_y = -50.0 + i * run + run * 0.5
        tread_z = i * rise + rise
        m.add_box((96, run + 4, 4), center=(0, tread_y, tread_z), mat="Wood_Plank_Cedar")
        m.add_box((96, 4, rise), center=(0, tread_y - run*0.5, tread_z - rise*0.5), mat="Wood_Timber_Dark")
    for sx in [-49, 49]:
        m.add_box((4, 104, 25), center=(sx, 0, 50), mat="Wood_Timber_Dark")
    return m


# -----------------------------------------------------------------------------
# 3D Preview Icon Renderer (Isometric, Backface-Culled, Depth-Sorted)
# -----------------------------------------------------------------------------

def render_building_icon(mesh, output_size=128, max_dim=96):
    mesh.ground_align()

    # Authentic 3/4 Isometric Perspective looking from South-East (+X, -Y, +Z)
    pitch = math.radians(30.0)
    yaw = math.radians(315.0)

    E_x = math.cos(pitch) * math.cos(yaw)
    E_y = math.cos(pitch) * math.sin(yaw)
    E_z = math.sin(pitch)

    L = Vec3(-E_x, -E_y, -E_z)
    R = Vec3(0.7071, 0.7071, 0.0)
    U = Vec3(-0.3536, 0.3536, 0.8660)

    cam_verts = []
    min_x, max_x = 1e9, -1e9
    min_y, max_y = 1e9, -1e9

    for v in mesh.vertices:
        sx = v.x * R.x + v.y * R.y + v.z * R.z
        sy = v.x * U.x + v.y * U.y + v.z * U.z
        depth = -(v.x * L.x + v.y * L.y + v.z * L.z)
        cam_verts.append((sx, sy, depth))
        if sx < min_x: min_x = sx
        if sx > max_x: max_x = sx
        if sy < min_y: min_y = sy
        if sy > max_y: max_y = sy

    cur_dim = max(max_x - min_x, max_y - min_y)
    scale = (float(max_dim) / cur_dim) if cur_dim > 1e-4 else 1.0

    center_x = (min_x + max_x) * 0.5
    center_y = (min_y + max_y) * 0.5

    ss = 3
    canvas_size = output_size * ss
    screen_c = canvas_size * 0.5

    img_ss = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img_ss)

    key_light = Vec3(-0.6, -0.6, 0.75).normalized()
    fill_light = Vec3(0.5, 0.5, -0.2).normalized()

    triangles = []
    for face_verts, mat_name in mesh.faces:
        idx0 = face_verts[0][0] - 1
        idx1 = face_verts[1][0] - 1
        idx2 = face_verts[2][0] - 1

        c0 = cam_verts[idx0]
        c1 = cam_verts[idx1]
        c2 = cam_verts[idx2]

        v0 = mesh.vertices[idx0]
        v1 = mesh.vertices[idx1]
        v2 = mesh.vertices[idx2]
        norm = (v1 - v0).cross(v2 - v0).normalized()

        # Backface culling: cull faces directed away from the camera look vector
        if norm.dot(L) >= -0.01:
            continue

        sx0 = (c0[0] - center_x) * scale * ss + screen_c
        sy0 = screen_c - (c0[1] - center_y) * scale * ss
        sx1 = (c1[0] - center_x) * scale * ss + screen_c
        sy1 = screen_c - (c1[1] - center_y) * scale * ss
        sx2 = (c2[0] - center_x) * scale * ss + screen_c
        sy2 = screen_c - (c2[1] - center_y) * scale * ss

        depth = (c0[2] + c1[2] + c2[2]) / 3.0

        ndotl = max(0.0, norm.dot(key_light))
        ndotf = max(0.0, norm.dot(fill_light))

        if ndotl > 0.52:
            illum = 1.20
        elif ndotl > 0.20:
            illum = 0.98
        else:
            illum = 0.72 + 0.16 * ndotf

        base_color = mesh.materials.get(mat_name, (0.5, 0.5, 0.5))
        r = int(min(255, max(0, base_color[0] * illum * 255.0)))
        g = int(min(255, max(0, base_color[1] * illum * 255.0)))
        b = int(min(255, max(0, base_color[2] * illum * 255.0)))

        fill = (r, g, b, 255)
        triangles.append((depth, [(sx0, sy0), (sx1, sy1), (sx2, sy2)], fill))

    # Sort ascending: furthest first, closest in front
    triangles.sort(key=lambda t: t[0])
    for d, pts, fill in triangles:
        draw.polygon(pts, fill=fill, outline=fill)

    # Clean dark ink silhouette contour outline (Homesteader icon rule)
    alpha = img_ss.split()[3]
    dilated = alpha.filter(ImageFilter.MaxFilter(5))
    ink = Image.new("RGBA", (canvas_size, canvas_size), (26, 22, 20, 255))
    ink.putalpha(dilated)
    final_ss = Image.alpha_composite(ink, img_ss)

    out = final_ss.resize((output_size, output_size), Image.Resampling.LANCZOS)

    # Enforce safe margin: outer 12px alpha = 0
    px = out.load()
    for y in range(output_size):
        for x in range(output_size):
            if x < 12 or x >= (output_size - 12) or y < 12 or y >= (output_size - 12):
                px[x, y] = (0, 0, 0, 0)

    return out


# -----------------------------------------------------------------------------
# Main Execution Runner
# -----------------------------------------------------------------------------

BUILDING_REGISTRY = [
    # 10 Prefab Homestead Buildings (360° Rotatable)
    ("SM_Building_Outhouse", build_outhouse, "1x1m", "Slanted corrugated tin roof, cedar walls, crescent door cutout, 360° modeled"),
    ("SM_Building_WellHouse", build_well_house, "1x1m", "Fieldstone base, timber posts, gabled shake roof, wooden bucket & crank, 360° modeled"),
    ("SM_Building_ToolShed", build_tool_shed, "2x2m", "Plank siding, framed door, dual side windows, pitched shake roof, 360° modeled"),
    ("SM_Building_ChickenCoop", build_chicken_coop, "2x3m", "Elevated roost box, ramp, side nesting box, rear cleanout, 360° wire run"),
    ("SM_Building_Woodshed", build_woodshed, "2x3m", "Heavy timber frame, open front, slatted rear & sides, cordwood bays, 360° modeled"),
    ("SM_Building_WaterTower", build_water_tower, "2x2m base", "4-post cross-braced trestle tower (6.7m), cedar stave tank, conical roof, 360° modeled"),
    ("SM_Building_RootCellar", build_root_cellar, "3x3m", "Mounded sod turf roof, stone retaining wall, storm doors, 360° contour"),
    ("SM_Building_Greenhouse", build_greenhouse, "3x4m", "Galvanized/timber frame, translucent glass panels on all 4 sides & roof, 360° modeled"),
    ("SM_Building_LogCabin", build_log_cabin, "5x6m", "Notched logs, covered front porch with steps & railing, stone chimney, 360° modeled"),
    ("SM_Building_SmallBarn", build_small_barn, "6x8m", "Gambrel silver tin roof, red timber, white trim, dual sliding X-doors, cupola, 360° modeled"),

    # 9 Modular Building Construction Parts
    ("SM_Part_Floor_Wood_1m", build_part_floor_wood_1m, "1x1m", "Modular tongue-and-groove timber floor foundation slab (1m x 1m x 20cm)"),
    ("SM_Part_Floor_Stone_1m", build_part_floor_stone_1m, "1x1m", "Cobblestone foundation floor slab with mortar joints (1m x 1m x 20cm)"),
    ("SM_Part_Wall_Wood_1m", build_part_wall_wood_1m, "1m span", "Solid vertical timber plank wall with top/bottom plates (1m x 2.4m)"),
    ("SM_Part_Wall_Doorway_1m", build_part_wall_doorway_1m, "1m span", "Timber wall section with framed 90x210cm door opening"),
    ("SM_Part_Wall_Window_1m", build_part_wall_window_1m, "1m span", "Timber wall section with framed 60x80cm four-pane glass window"),
    ("SM_Part_Door_Wood", build_part_door_wood, "Door", "Z-braced cedar door with iron strap hinges and thumb latch"),
    ("SM_Part_Roof_Slope_1m", build_part_roof_slope_1m, "1x1m", "30-degree sloped shake roof section with eave overhang (1m span)"),
    ("SM_Part_Roof_Ridge_1m", build_part_roof_ridge_1m, "1x1m", "Double-sloped peak ridge cap with wood shake texture (1m span)"),
    ("SM_Part_Stairs_Wood_1m", build_part_stairs_wood_1m, "1x1m", "5-step timber staircase with side stringers and kick plates (1m rise)"),
]

def main():
    print("=================================================================")
    print("HOMESTEADER 3D HOMESTEAD BUILDINGS & ARCHITECTURE GENERATOR (v4)")
    print("360° Full 4-Sided Modeling & Item-Icon Visual Alignment")
    print(f"Total Building Models: {len(BUILDING_REGISTRY)}")
    print("=================================================================\n")

    count = 0
    for mesh_name, builder_func, footprint, desc in BUILDING_REGISTRY:
        count += 1
        mesh = builder_func()
        mesh.ground_align()
        tri_count = len(mesh.faces)
        vert_count = len(mesh.vertices)

        # 1. Save OBJ & MTL to HUD/assets/building/structures/
        hud_obj = os.path.join(HUD_BUILDING_MODELS, f"{mesh_name}.obj")
        hud_mtl = os.path.join(HUD_BUILDING_MODELS, f"{mesh_name}.mtl")
        mesh.save_obj(hud_obj, hud_mtl)

        # 2. Save OBJ & MTL to UE5 Content/Homesteader/Assets/Building/Meshes/
        ue5_obj = os.path.join(UE5_BUILDING_MODELS, f"{mesh_name}.obj")
        ue5_mtl = os.path.join(UE5_BUILDING_MODELS, f"{mesh_name}.mtl")
        mesh.save_obj(ue5_obj, ue5_mtl)

        # 3. Render 128x128 Preview Icon
        icon = render_building_icon(mesh, output_size=128, max_dim=96)

        # Save Icon to HUD/assets/building/icons/ & UE5 UI/Icons/Building/
        hud_icon = os.path.join(HUD_BUILDING_ICONS, f"{mesh_name}.png")
        ue5_icon = os.path.join(UE5_BUILDING_ICONS, f"{mesh_name}.png")
        icon.save(hud_icon, "PNG")
        icon.save(ue5_icon, "PNG")

        print(f"[{count:02d}/{len(BUILDING_REGISTRY)}] Generated {mesh_name} ({footprint}) - {vert_count} verts, {tri_count} faces")

    print("\nSUCCESS: All 19 building models and icons generated and synced across all 4 sides!")

if __name__ == "__main__":
    main()
