#!/usr/bin/env python3
"""
Homesteader 3D Low-Poly Foliage & Vegetation System (v3 - Enhanced Poly Count)
Generates 28 high-quality stylized low-poly faceted 3D meshes (.obj + .mtl) and
renders matching 128x128 transparent preview icons strictly adhering to Homesteader rules:
- Poly counts increased from ultra-low (8-60 tris) to refined stylized game fidelity (80-900 tris)
- Smooth multi-segmented curved grass blades, ferns, and vines
- Refined 80-triangle icosphere canopy lobes with organic natural faceting
- Trunks and boughs with 8-12 radial segments for smooth organic contours
- 100% RIGHT SIDE UP (proper vertical camera projection)
- Beautiful stylized cel-shaded aesthetic matching existing game item icons
- Crisp dark ink contour silhouette outlines (no interior wireframe lines)
- Pure 32-bit transparent RGBA (outer perimeter alpha = 0, >= 15px safe margin)
- Synchronized dual workspaces (HUD and UE5 Content)
"""

import os
import math
import shutil
from PIL import Image, ImageDraw, ImageFilter

HUD_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UE5_ROOT = os.path.abspath(os.path.join(HUD_ROOT, "..", "Homesteader", "Content", "Homesteader"))

HUD_MODELS_DIR = os.path.join(HUD_ROOT, "assets", "foliage", "models")
HUD_ICONS_DIR = os.path.join(HUD_ROOT, "assets", "foliage", "icons")
UE5_MODELS_DIR = os.path.join(UE5_ROOT, "Assets", "Foliage", "Meshes")
UE5_ICONS_DIR = os.path.join(UE5_ROOT, "UI", "Icons", "Foliage")

for d in [HUD_MODELS_DIR, HUD_ICONS_DIR, UE5_MODELS_DIR, UE5_ICONS_DIR]:
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

        self.faces.append(([
            (iv, iv, iv),
            (iv + 1, iv + 1, iv + 1),
            (iv + 2, iv + 2, iv + 2)
        ], mat))

    def add_quad(self, v0, v1, v2, v3, mat="default"):
        self.add_triangle(v0, v1, v2, (0,0), (1,0), (1,1), mat)
        self.add_triangle(v0, v2, v3, (0,0), (1,1), (0,1), mat)

    def add_cylinder(self, r0, r1, h, z0=0.0, segs=10, mat="trunk", c0=(0,0), c1=(0,0)):
        cx0, cy0 = c0
        cx1, cy1 = c1
        for i in range(segs):
            a0 = i * 2.0 * math.pi / segs
            a1 = (i + 1) * 2.0 * math.pi / segs
            b0 = Vec3(cx0 + r0 * math.cos(a0), cy0 + r0 * math.sin(a0), z0)
            b1 = Vec3(cx0 + r0 * math.cos(a1), cy0 + r0 * math.sin(a1), z0)
            t0 = Vec3(cx1 + r1 * math.cos(a0), cy1 + r1 * math.sin(a0), z0 + h)
            t1 = Vec3(cx1 + r1 * math.cos(a1), cy1 + r1 * math.sin(a1), z0 + h)
            self.add_quad(b0, b1, t1, t0, mat=mat)

    def add_cone(self, r, h, z0=0.0, segs=12, mat="leaves", c=(0,0)):
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

    def add_flared_roots(self, r_buttress, r_top, h, z0=0.0, num_roots=5, mat="bark", c=(0,0)):
        """Creates 3D sculptural flaring root buttresses grounding the trunk into the terrain."""
        cx, cy = c
        segs = num_roots * 2
        for i in range(segs):
            a0 = i * 2.0 * math.pi / segs
            a1 = (i + 1) * 2.0 * math.pi / segs
            r0 = r_buttress if (i % 2 == 0) else (r_buttress * 0.52)
            r1 = r_buttress if ((i + 1) % 2 == 0) else (r_buttress * 0.52)

            b0 = Vec3(cx + r0 * math.cos(a0), cy + r0 * math.sin(a0), z0)
            b1 = Vec3(cx + r1 * math.cos(a1), cy + r1 * math.sin(a1), z0)
            t0 = Vec3(cx + r_top * math.cos(a0), cy + r_top * math.sin(a0), z0 + h)
            t1 = Vec3(cx + r_top * math.cos(a1), cy + r_top * math.sin(a1), z0 + h)

            self.add_quad(b0, b1, t1, t0, mat=mat)

    def add_pine_tier(self, r_base, r_top, h, z0, segs=8, mat="Needles_Top", mat_under="Needles_Dark", c=(0,0)):
        """Creates a low-poly faceted conical umbrella skirt with broad polygon plates matching item icon."""
        cx, cy = c
        apex = Vec3(cx, cy, z0 + h)
        under_c = Vec3(cx, cy, z0 + h * 0.15)

        for i in range(segs):
            a0 = i * 2.0 * math.pi / segs
            a1 = (i + 1) * 2.0 * math.pi / segs
            amid = (a0 + a1) * 0.5

            t0 = Vec3(cx + r_top * math.cos(a0), cy + r_top * math.sin(a0), z0 + h)
            t1 = Vec3(cx + r_top * math.cos(a1), cy + r_top * math.sin(a1), z0 + h)

            b0 = Vec3(cx + r_base * 0.85 * math.cos(a0), cy + r_base * 0.85 * math.sin(a0), z0 + h * 0.18)
            b_tip = Vec3(cx + r_base * math.cos(amid), cy + r_base * math.sin(amid), z0)
            b1 = Vec3(cx + r_base * 0.85 * math.cos(a1), cy + r_base * 0.85 * math.sin(a1), z0 + h * 0.18)

            if r_top < 1e-3:
                self.add_triangle(b0, b_tip, apex, mat=mat)
                self.add_triangle(b_tip, b1, apex, mat=mat)
            else:
                self.add_triangle(t0, b0, b_tip, mat=mat)
                self.add_triangle(t0, b_tip, t1, mat=mat)
                self.add_triangle(t1, b_tip, b1, mat=mat)

            # Underside facing downward
            self.add_triangle(under_c, b1, b_tip, mat=mat_under)
            self.add_triangle(under_c, b_tip, b0, mat=mat_under)

    def add_foliage_lobe(self, radius, center=(0,0,0), mat="leaves", flatten_z=0.85, subdivisions=1):
        """
        Geodesic icosphere foliage lobe.
        subdivisions=1 generates 80 clean faceted triangles per lobe with subtle organic variation.
        subdivisions=0 generates 20 triangles (used for tiny detail dots like highlights).
        """
        cx, cy, cz = center
        c = Vec3(cx, cy, cz)
        phi = (1.0 + math.sqrt(5.0)) / 2.0
        raw = [
            Vec3(-1, phi, 0), Vec3(1, phi, 0), Vec3(-1, -phi, 0), Vec3(1, -phi, 0),
            Vec3(0, -1, phi), Vec3(0, 1, phi), Vec3(0, -1, -phi), Vec3(0, 1, -phi),
            Vec3(phi, 0, -1), Vec3(phi, 0, 1), Vec3(-phi, 0, -1), Vec3(-phi, 0, 1)
        ]
        verts = [v.normalized() for v in raw]
        faces = [
            (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
            (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
            (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
            (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)
        ]

        if subdivisions >= 1:
            midpoint_cache = {}
            def get_midpoint(i1, i2):
                edge = tuple(sorted((i1, i2)))
                if edge in midpoint_cache:
                    return midpoint_cache[edge]
                vm = (verts[i1] + verts[i2]).normalized()
                idx = len(verts)
                verts.append(vm)
                midpoint_cache[edge] = idx
                return idx

            new_faces = []
            for i0, i1, i2 in faces:
                m01 = get_midpoint(i0, i1)
                m12 = get_midpoint(i1, i2)
                m20 = get_midpoint(i2, i0)
                new_faces.extend([
                    (i0, m01, m20),
                    (i1, m12, m01),
                    (i2, m20, m12),
                    (m01, m12, m20)
                ])
            faces = new_faces

        for i0, i1, i2 in faces:
            v0, v1, v2 = verts[i0], verts[i1], verts[i2]
            # Subtle organic variation on vertex radii
            def bump(v):
                return 1.0 + 0.05 * math.sin(v.x * 3.5 + v.y * 2.5 + v.z * 1.5)
            r0 = radius * bump(v0)
            r1 = radius * bump(v1)
            r2 = radius * bump(v2)
            p0 = Vec3(c.x + v0.x * r0, c.y + v0.y * r0, c.z + v0.z * r0 * flatten_z)
            p1 = Vec3(c.x + v1.x * r1, c.y + v1.y * r1, c.z + v1.z * r1 * flatten_z)
            p2 = Vec3(c.x + v2.x * r2, c.y + v2.y * r2, c.z + v2.z * r2 * flatten_z)
            self.add_triangle(p0, p1, p2, mat=mat)

    def ground_align(self):
        if not self.vertices: return
        min_z = min(v.z for v in self.vertices)
        offset = Vec3(0, 0, -min_z)
        self.vertices = [v + offset for v in self.vertices]

    def save_obj(self, obj_path, mtl_path):
        mtl_filename = os.path.basename(mtl_path)
        with open(obj_path, "w", encoding="utf-8") as f:
            f.write(f"# Homesteader 3D Low-Poly Foliage Asset (v3 Enhanced)\n")
            f.write(f"mtllib {mtl_filename}\n")
            f.write(f"o {self.name}\n\n")

            for v in self.vertices:
                f.write(f"v {v.x:.4f} {v.y:.4f} {v.z:.4f}\n")
            for vt in self.uvs:
                f.write(f"vt {vt[0]:.4f} {vt[1]:.4f}\n")
            for vn in self.normals:
                f.write(f"vn {vn.x:.4f} {vn.y:.4f} {vn.z:.4f}\n")

            current_mat = None
            for face_verts, mat in self.faces:
                if mat != current_mat:
                    f.write(f"usemtl {mat}\n")
                    f.write(f"s 1\n")
                    current_mat = mat
                face_str = " ".join([f"{v}/{vt}/{vn}" for v, vt, vn in face_verts])
                f.write(f"f {face_str}\n")

        with open(mtl_path, "w", encoding="utf-8") as f:
            f.write(f"# Homesteader Material Definition\n\n")
            for mat_name, (r, g, b) in self.materials.items():
                f.write(f"newmtl {mat_name}\n")
                f.write(f"Ka {r*0.4:.4f} {g*0.4:.4f} {b*0.4:.4f}\n")
                f.write(f"Kd {r:.4f} {g:.4f} {b:.4f}\n")
                f.write(f"Ks 0.12 0.12 0.12\n")
                f.write(f"Ns 12.0\n")
                f.write(f"d 1.0\n")
                f.write(f"illum 2\n\n")


# -----------------------------------------------------------------------------
# 28 Stylized Mesh Builders (Enhanced Poly Count)
# -----------------------------------------------------------------------------

def build_oak_large():
    """6m x 6m canopy, 5.5m tall. Sculptural flared root buttresses in 360°, knot groove, 4 stout boughs, multi-lobed canopy matching tree_oak.png."""
    m = Mesh("SM_Tree_Oak_Large")
    m.add_material("Bark_Oak", 0.42, 0.28, 0.16)
    m.add_material("Bark_Branch", 0.46, 0.32, 0.18)
    m.add_material("Leaves_Top", 0.42, 0.72, 0.22)   # Sunlit lime
    m.add_material("Leaves_Mid", 0.24, 0.54, 0.18)   # Rich forest green
    m.add_material("Leaves_Dark", 0.15, 0.38, 0.14)  # Deep shadow crevice

    # 1. 5 Flared Root Buttresses in 360° grounding into the terrain
    m.add_flared_roots(r_buttress=85, r_top=46, h=65, z0=0, num_roots=5, mat="Bark_Oak")

    # 2. Main trunk (tapers from r=46 to 34, H=105)
    m.add_cylinder(r0=46, r1=34, h=105, z0=65, segs=10, mat="Bark_Oak")

    # 3. Low-poly knot / hollow groove detail on front (-Y)
    m.add_cylinder(r0=14, r1=10, h=25, z0=105, segs=6, mat="Bark_Oak", c0=(0, -30), c1=(0, -26))

    # 4. 4 Stout spreading boughs visible under canopy in all 4 quadrants (360°)
    m.add_cylinder(r0=20, r1=12, h=125, z0=160, segs=8, mat="Bark_Branch", c0=(0,0), c1=(-75, -75))
    m.add_cylinder(r0=20, r1=12, h=125, z0=160, segs=8, mat="Bark_Branch", c0=(0,0), c1=(75, 75))
    m.add_cylinder(r0=18, r1=11, h=120, z0=165, segs=8, mat="Bark_Branch", c0=(0,0), c1=(65, -55))
    m.add_cylinder(r0=18, r1=11, h=120, z0=165, segs=8, mat="Bark_Branch", c0=(0,0), c1=(-55, 65))

    # 5. Distinct multi-lobed spherical icosphere foliage clusters (80 tris each)
    # Lower skirt lobes (quadrants)
    m.add_foliage_lobe(radius=90, center=(-85, -85, 275), mat="Leaves_Mid")
    m.add_foliage_lobe(radius=90, center=(85, 85, 280), mat="Leaves_Mid")
    m.add_foliage_lobe(radius=85, center=(75, -65, 270), mat="Leaves_Dark")
    m.add_foliage_lobe(radius=85, center=(-65, 75, 285), mat="Leaves_Dark")

    # Mid crown lobes
    m.add_foliage_lobe(radius=115, center=(0, 0, 365), mat="Leaves_Top")
    m.add_foliage_lobe(radius=85, center=(15, 15, 415), mat="Leaves_Top")
    return m


def build_oak_medium():
    """4.5m x 4.5m canopy, 4m tall."""
    m = Mesh("SM_Tree_Oak_Medium")
    m.add_material("Bark_Oak", 0.42, 0.28, 0.16)
    m.add_material("Bark_Branch", 0.46, 0.32, 0.18)
    m.add_material("Leaves_Top", 0.42, 0.72, 0.22)
    m.add_material("Leaves_Mid", 0.24, 0.54, 0.18)

    m.add_flared_roots(r_buttress=65, r_top=36, h=50, z0=0, num_roots=5, mat="Bark_Oak")
    m.add_cylinder(r0=36, r1=26, h=90, z0=50, segs=10, mat="Bark_Oak")
    m.add_cylinder(r0=18, r1=11, h=105, z0=130, segs=8, mat="Bark_Branch", c0=(0,0), c1=(-55, -55))
    m.add_cylinder(r0=18, r1=11, h=105, z0=130, segs=8, mat="Bark_Branch", c0=(0,0), c1=(55, 55))
    m.add_cylinder(r0=16, r1=10, h=100, z0=135, segs=8, mat="Bark_Branch", c0=(0,0), c1=(45, -45))

    m.add_foliage_lobe(radius=75, center=(-65, -65, 235), mat="Leaves_Mid")
    m.add_foliage_lobe(radius=75, center=(65, 65, 240), mat="Leaves_Mid")
    m.add_foliage_lobe(radius=70, center=(50, -50, 230), mat="Leaves_Mid")
    m.add_foliage_lobe(radius=95, center=(0, 0, 310), mat="Leaves_Top")
    m.add_foliage_lobe(radius=68, center=(12, 12, 355), mat="Leaves_Top")
    return m


def build_oak_small():
    """3m x 3m canopy, 2.8m tall."""
    m = Mesh("SM_Tree_Oak_Small")
    m.add_material("Bark_Oak", 0.44, 0.30, 0.18)
    m.add_material("Leaves_Top", 0.44, 0.74, 0.24)
    m.add_material("Leaves_Mid", 0.26, 0.56, 0.20)

    m.add_flared_roots(r_buttress=45, r_top=24, h=40, z0=0, num_roots=4, mat="Bark_Oak")
    m.add_cylinder(r0=24, r1=16, h=70, z0=40, segs=8, mat="Bark_Oak")
    m.add_cylinder(r0=14, r1=9, h=75, z0=100, segs=8, mat="Bark_Oak", c0=(0,0), c1=(-35, -35))
    m.add_cylinder(r0=14, r1=9, h=75, z0=100, segs=8, mat="Bark_Oak", c0=(0,0), c1=(35, 35))

    m.add_foliage_lobe(radius=55, center=(-40, -40, 175), mat="Leaves_Mid")
    m.add_foliage_lobe(radius=55, center=(40, 40, 180), mat="Leaves_Mid")
    m.add_foliage_lobe(radius=70, center=(0, 0, 230), mat="Leaves_Top")
    return m


def build_oak_autumn():
    """Autumn oak with golden amber, orange, and ruby lobes."""
    m = Mesh("SM_Tree_Oak_Autumn")
    m.add_material("Bark_Oak", 0.42, 0.26, 0.15)
    m.add_material("Leaves_Gold", 0.94, 0.62, 0.15)
    m.add_material("Leaves_Orange", 0.88, 0.40, 0.12)
    m.add_material("Leaves_Ruby", 0.78, 0.22, 0.14)

    m.add_flared_roots(r_buttress=80, r_top=45, h=60, z0=0, num_roots=5, mat="Bark_Oak")
    m.add_cylinder(r0=45, r1=32, h=105, z0=60, segs=10, mat="Bark_Oak")
    m.add_cylinder(r0=20, r1=12, h=120, z0=155, segs=8, mat="Bark_Oak", c0=(0,0), c1=(-70, -70))
    m.add_cylinder(r0=20, r1=12, h=120, z0=155, segs=8, mat="Bark_Oak", c0=(0,0), c1=(70, 70))
    m.add_cylinder(r0=18, r1=11, h=115, z0=160, segs=8, mat="Bark_Oak", c0=(0,0), c1=(60, -50))

    m.add_foliage_lobe(radius=85, center=(-80, -80, 265), mat="Leaves_Ruby")
    m.add_foliage_lobe(radius=85, center=(80, 80, 270), mat="Leaves_Orange")
    m.add_foliage_lobe(radius=80, center=(65, -55, 260), mat="Leaves_Ruby")
    m.add_foliage_lobe(radius=115, center=(0, 0, 350), mat="Leaves_Gold")
    m.add_foliage_lobe(radius=80, center=(15, 15, 400), mat="Leaves_Gold")
    return m


def build_pine_tall():
    """Tall mountain evergreen pine (~7m tall). 6 stepped umbrella conical tiers matching tree_pine.png."""
    m = Mesh("SM_Tree_Pine_Tall")
    m.add_material("Bark_Pine", 0.36, 0.22, 0.14)
    m.add_material("Needles_Top", 0.36, 0.64, 0.28)
    m.add_material("Needles_Mid", 0.24, 0.50, 0.22)
    m.add_material("Needles_Dark", 0.14, 0.32, 0.16)

    # Exposed trunk at base (height 120)
    m.add_cylinder(r0=26, r1=20, h=120, z0=0, segs=8, mat="Bark_Pine")

    # 6 Tiered Umbrella Skirts (8 facets each, broad plates matching item icon)
    # Tier 0 (widest bottom skirt)
    m.add_pine_tier(r_base=165, r_top=30, h=95, z0=80, segs=8, mat="Needles_Mid", mat_under="Needles_Dark")
    # Tier 1
    m.add_pine_tier(r_base=140, r_top=25, h=95, z0=150, segs=8, mat="Needles_Mid", mat_under="Needles_Dark")
    # Tier 2
    m.add_pine_tier(r_base=115, r_top=20, h=90, z0=220, segs=8, mat="Needles_Top", mat_under="Needles_Dark")
    # Tier 3
    m.add_pine_tier(r_base=90, r_top=16, h=85, z0=285, segs=8, mat="Needles_Top", mat_under="Needles_Dark")
    # Tier 4
    m.add_pine_tier(r_base=68, r_top=12, h=80, z0=345, segs=8, mat="Needles_Top", mat_under="Needles_Dark")
    # Tier 5 (apex peak)
    m.add_pine_tier(r_base=44, r_top=0, h=85, z0=400, segs=8, mat="Needles_Top", mat_under="Needles_Dark")
    return m


def build_pine_medium():
    """Medium pine (~5m tall). 4 stepped umbrella tiers."""
    m = Mesh("SM_Tree_Pine_Medium")
    m.add_material("Bark_Pine", 0.36, 0.22, 0.14)
    m.add_material("Needles_Top", 0.36, 0.64, 0.28)
    m.add_material("Needles_Mid", 0.24, 0.50, 0.22)
    m.add_material("Needles_Dark", 0.14, 0.32, 0.16)

    m.add_cylinder(r0=22, r1=18, h=95, z0=0, segs=8, mat="Bark_Pine")

    m.add_pine_tier(r_base=140, r_top=26, h=90, z0=65, segs=8, mat="Needles_Mid", mat_under="Needles_Dark")
    m.add_pine_tier(r_base=112, r_top=20, h=85, z0=130, segs=8, mat="Needles_Mid", mat_under="Needles_Dark")
    m.add_pine_tier(r_base=82, r_top=14, h=80, z0=190, segs=8, mat="Needles_Top", mat_under="Needles_Dark")
    m.add_pine_tier(r_base=48, r_top=0, h=80, z0=245, segs=8, mat="Needles_Top", mat_under="Needles_Dark")
    return m


def build_pine_small():
    """Small pine (~3.6m tall). 3 stepped umbrella tiers."""
    m = Mesh("SM_Tree_Pine_Small")
    m.add_material("Bark_Pine", 0.36, 0.22, 0.14)
    m.add_material("Needles_Top", 0.36, 0.64, 0.28)
    m.add_material("Needles_Mid", 0.24, 0.50, 0.22)
    m.add_material("Needles_Dark", 0.14, 0.32, 0.16)

    m.add_cylinder(r0=18, r1=14, h=70, z0=0, segs=8, mat="Bark_Pine")

    m.add_pine_tier(r_base=110, r_top=22, h=75, z0=50, segs=8, mat="Needles_Mid", mat_under="Needles_Dark")
    m.add_pine_tier(r_base=78, r_top=14, h=70, z0=105, segs=8, mat="Needles_Top", mat_under="Needles_Dark")
    m.add_pine_tier(r_base=44, r_top=0, h=70, z0=155, segs=8, mat="Needles_Top", mat_under="Needles_Dark")
    return m

def build_birch_tall():
    """Tall birch (~6.2m tall). Slender white trunk with dark lenticels, 4 branching boughs, airy chartreuse puffs matching tree_birch.png."""
    m = Mesh("SM_Tree_Birch_Tall")
    m.add_material("Bark_BirchWhite", 0.92, 0.92, 0.88)
    m.add_material("Bark_BirchSpot", 0.22, 0.20, 0.18)
    m.add_material("Leaves_Birch", 0.50, 0.76, 0.28)
    m.add_material("Leaves_BirchTop", 0.58, 0.84, 0.34)

    # Slender tapering white trunk with dark lenticel rings (segs=8)
    m.add_cylinder(r0=20, r1=16, h=140, z0=0, segs=8, mat="Bark_BirchWhite")
    m.add_cylinder(r0=16.5, r1=16, h=10, z0=70, segs=8, mat="Bark_BirchSpot")

    m.add_cylinder(r0=16, r1=13, h=140, z0=140, segs=8, mat="Bark_BirchWhite", c0=(0,0), c1=(4, 3))
    m.add_cylinder(r0=13.5, r1=13, h=10, z0=200, segs=8, mat="Bark_BirchSpot", c0=(2,1), c1=(2,1))

    m.add_cylinder(r0=13, r1=10, h=140, z0=280, segs=8, mat="Bark_BirchWhite", c0=(4,3), c1=(8, 6))
    m.add_cylinder(r0=10.5, r1=10, h=10, z0=340, segs=8, mat="Bark_BirchSpot", c0=(6,4), c1=(6,4))

    m.add_cylinder(r0=10, r1=6, h=140, z0=420, segs=8, mat="Bark_BirchWhite", c0=(8,6), c1=(12, 9))

    # 4 distinct white branching boughs reaching outward (360°)
    # Branch 1 (Screen Right / +X, +Y):
    m.add_cylinder(r0=9, r1=5, h=120, z0=220, segs=6, mat="Bark_BirchWhite", c0=(3,2), c1=(55, 55))
    # Branch 2 (Screen Left / -X, -Y):
    m.add_cylinder(r0=8, r1=4.5, h=125, z0=300, segs=6, mat="Bark_BirchWhite", c0=(6,4), c1=(-55, -55))
    # Branch 3 (Screen Front / +X, -Y):
    m.add_cylinder(r0=7, r1=4, h=110, z0=370, segs=6, mat="Bark_BirchWhite", c0=(9,7), c1=(45, -35))
    # Branch 4 (Screen Back / -X, +Y):
    m.add_cylinder(r0=6, r1=3.5, h=105, z0=430, segs=6, mat="Bark_BirchWhite", c0=(11,8), c1=(-35, 45))

    # Airy ellipsoidal chartreuse foliage puffs sitting on each branch tip
    m.add_foliage_lobe(radius=65, center=(62, 62, 330), mat="Leaves_Birch", flatten_z=1.15)
    m.add_foliage_lobe(radius=68, center=(-62, -62, 410), mat="Leaves_Birch", flatten_z=1.15)
    m.add_foliage_lobe(radius=60, center=(52, -40, 470), mat="Leaves_Birch", flatten_z=1.15)
    m.add_foliage_lobe(radius=60, center=(-40, 52, 525), mat="Leaves_Birch", flatten_z=1.15)
    # Crown apex puff:
    m.add_foliage_lobe(radius=80, center=(12, 9, 550), mat="Leaves_BirchTop", flatten_z=1.20)
    return m


def build_birch_medium():
    """Medium birch (~4.5m tall). 3 branches, 4 airy puffs."""
    m = Mesh("SM_Tree_Birch_Medium")
    m.add_material("Bark_BirchWhite", 0.92, 0.92, 0.88)
    m.add_material("Bark_BirchSpot", 0.22, 0.20, 0.18)
    m.add_material("Leaves_Birch", 0.50, 0.76, 0.28)
    m.add_material("Leaves_BirchTop", 0.58, 0.84, 0.34)

    m.add_cylinder(r0=18, r1=13, h=100, z0=0, segs=8, mat="Bark_BirchWhite")
    m.add_cylinder(r0=14, r1=13.5, h=8, z0=50, segs=8, mat="Bark_BirchSpot")
    m.add_cylinder(r0=13, r1=8, h=160, z0=100, segs=8, mat="Bark_BirchWhite", c0=(0,0), c1=(10, 8))
    m.add_cylinder(r0=9, r1=8.5, h=8, z0=180, segs=8, mat="Bark_BirchSpot", c0=(5,4), c1=(5,4))

    # 3 branches
    # Branch 1 (Screen Right / +X, +Y):
    m.add_cylinder(r0=7, r1=4, h=95, z0=140, segs=6, mat="Bark_BirchWhite", c0=(2,2), c1=(45, 45))
    # Branch 2 (Screen Left / -X, -Y):
    m.add_cylinder(r0=7, r1=4, h=95, z0=180, segs=6, mat="Bark_BirchWhite", c0=(5,4), c1=(-45, -45))
    # Branch 3 (Screen Front / +X, -Y):
    m.add_cylinder(r0=6, r1=3.5, h=90, z0=220, segs=6, mat="Bark_BirchWhite", c0=(8,6), c1=(35, -30))

    m.add_foliage_lobe(radius=58, center=(50, 50, 230), mat="Leaves_Birch", flatten_z=1.15)
    m.add_foliage_lobe(radius=62, center=(-50, -50, 270), mat="Leaves_Birch", flatten_z=1.15)
    m.add_foliage_lobe(radius=55, center=(40, -35, 305), mat="Leaves_Birch", flatten_z=1.15)
    m.add_foliage_lobe(radius=75, center=(8, 6, 360), mat="Leaves_BirchTop", flatten_z=1.20)
    return m

def build_apple_tree():
    m = Mesh("SM_Tree_Apple")
    m.add_material("Bark_Oak", 0.44, 0.28, 0.16)
    m.add_material("Bark_Branch", 0.48, 0.32, 0.18)
    m.add_material("Leaves_Apple", 0.32, 0.68, 0.22)
    m.add_material("Leaves_Top", 0.42, 0.78, 0.24)
    m.add_material("Fruit_Apple", 0.94, 0.12, 0.16)
    m.add_material("Fruit_Highlight", 1.0, 0.85, 0.85)

    m.add_cylinder(r0=40, r1=26, h=70, z0=0, segs=10, mat="Bark_Oak")
    m.add_cylinder(r0=26, r1=18, h=80, z0=70, segs=10, mat="Bark_Oak")
    m.add_cylinder(r0=18, r1=12, h=90, z0=140, segs=8, mat="Bark_Branch", c0=(0,0), c1=(-40, -30))
    m.add_cylinder(r0=16, r1=11, h=90, z0=140, segs=8, mat="Bark_Branch", c0=(0,0), c1=(40, 30))
    m.add_cylinder(r0=15, r1=10, h=95, z0=140, segs=8, mat="Bark_Branch", c0=(0,0), c1=(-10, 45))

    m.add_foliage_lobe(radius=115, center=(0, 0, 255), mat="Leaves_Apple")
    m.add_foliage_lobe(radius=95, center=(25, 35, 290), mat="Leaves_Top")
    m.add_foliage_lobe(radius=85, center=(-35, 20, 260), mat="Leaves_Apple")

    # Front-facing apples placed proudly on the visible canopy surface
    R = 120.0
    Zmid = 265.0
    apple_offsets = [
        (-48, -15), (0, -30), (48, -15),
        (-56, 18), (-18, 10), (22, 12), (58, 20),
        (-30, 46), (12, 50), (42, 44)
    ]
    for dx, dz in apple_offsets:
        rx = dx
        rz = Zmid + dz
        rem = max(10.0, R*R - rx*rx - dz*dz)
        ry = math.sqrt(rem)
        vx = (rx + ry) * 0.7071
        vy = (ry - rx) * 0.7071
        vz = rz
        m.add_foliage_lobe(radius=18, center=(vx, vy, vz), mat="Fruit_Apple", subdivisions=0)
        m.add_foliage_lobe(radius=6, center=(vx-3, vy-3, vz+6), mat="Fruit_Highlight", subdivisions=0)
    return m

def build_willow_tree():
    m = Mesh("SM_Tree_Willow")
    m.add_material("Bark_Dark", 0.34, 0.22, 0.14)
    m.add_material("Leaves_Willow", 0.35, 0.62, 0.32)
    m.add_material("Leaves_WillowLight", 0.42, 0.72, 0.36)

    m.add_cylinder(r0=55, r1=36, h=100, z0=0, segs=10, mat="Bark_Dark")
    m.add_cylinder(r0=36, r1=24, h=120, z0=100, segs=10, mat="Bark_Dark")
    m.add_foliage_lobe(radius=145, center=(0, 0, 390), mat="Leaves_Willow")
    m.add_foliage_lobe(radius=110, center=(30, 20, 420), mat="Leaves_WillowLight")

    # 16 cascading weeping foliage ribbons with 4 curved segments each
    angles = [i * 2.0 * math.pi / 16 for i in range(16)]
    for i, a in enumerate(angles):
        r_dist = 105 + 15 * math.sin(i * 1.5)
        tx = r_dist * math.cos(a)
        ty = r_dist * math.sin(a)
        w = 14

        # Segment 0: Top attachment
        p0_l = Vec3(tx - w*0.5*math.sin(a), ty + w*0.5*math.cos(a), 350)
        p0_r = Vec3(tx + w*0.5*math.sin(a), ty - w*0.5*math.cos(a), 350)

        # Segment 1: Mid top
        p1_l = Vec3((tx*1.05) - w*0.45*math.sin(a), (ty*1.05) + w*0.45*math.cos(a), 280)
        p1_r = Vec3((tx*1.05) + w*0.45*math.sin(a), (ty*1.05) - w*0.45*math.cos(a), 280)

        # Segment 2: Mid low
        p2_l = Vec3((tx*0.95) - w*0.35*math.sin(a), (ty*0.95) + w*0.35*math.cos(a), 210)
        p2_r = Vec3((tx*0.95) + w*0.35*math.sin(a), (ty*0.95) - w*0.35*math.cos(a), 210)

        # Segment 3: Bottom tip
        p3_tip = Vec3(tx*0.9, ty*0.9, 150)

        m.add_quad(p0_l, p0_r, p1_r, p1_l, mat="Leaves_Willow")
        m.add_quad(p1_l, p1_r, p2_r, p2_l, mat="Leaves_WillowLight")
        m.add_triangle(p2_l, p2_r, p3_tip, mat="Leaves_WillowLight")
    return m

def build_dead_snag():
    m = Mesh("SM_Tree_Dead_Snag")
    m.add_material("Bark_Weathered", 0.44, 0.38, 0.32)
    m.add_material("Wood_Splinter", 0.56, 0.50, 0.42)

    m.add_cylinder(r0=52, r1=32, h=140, z0=0, segs=10, mat="Bark_Weathered")
    m.add_cylinder(r0=32, r1=18, h=160, z0=140, segs=10, mat="Bark_Weathered", c0=(0,0), c1=(15, -10))
    m.add_cylinder(r0=18, r1=8, h=110, z0=300, segs=8, mat="Wood_Splinter", c0=(15,-10), c1=(25, -15))
    # Snag branches
    m.add_cylinder(r0=16, r1=6, h=85, z0=220, segs=8, mat="Bark_Weathered", c0=(10,-5), c1=(-35, 25))
    m.add_cylinder(r0=14, r1=5, h=65, z0=250, segs=8, mat="Bark_Weathered", c0=(12,-8), c1=(45, 30))
    m.add_cylinder(r0=12, r1=4, h=55, z0=170, segs=8, mat="Bark_Weathered", c0=(5,0), c1=(-25, -35))
    return m

def build_maple_tree():
    m = Mesh("SM_Tree_Maple")
    m.add_material("Bark_Maple", 0.36, 0.24, 0.16)
    m.add_material("Bark_Branch", 0.40, 0.28, 0.18)
    m.add_material("Leaves_MapleCrimson", 0.70, 0.18, 0.12)
    m.add_material("Leaves_MapleRed", 0.84, 0.24, 0.12)
    m.add_material("Leaves_MapleOrange", 0.88, 0.32, 0.12)

    # Base flared root trunk (5 sculptural buttress roots grounding trunk in 360°)
    m.add_flared_roots(r_buttress=65, r_top=34, h=55, z0=0, num_roots=5, mat="Bark_Maple")
    m.add_cylinder(r0=34, r1=22, h=95, z0=55, segs=10, mat="Bark_Maple")

    # 4 stout spreading scaffold branches in 360° quadrants
    m.add_cylinder(r0=16, r1=11, h=110, z0=120, segs=8, mat="Bark_Branch", c0=(0,0), c1=(-65, -65))
    m.add_cylinder(r0=16, r1=11, h=110, z0=120, segs=8, mat="Bark_Branch", c0=(0,0), c1=(65, 65))
    m.add_cylinder(r0=15, r1=10, h=115, z0=125, segs=8, mat="Bark_Branch", c0=(0,0), c1=(55, -50))
    m.add_cylinder(r0=14, r1=9, h=115, z0=125, segs=8, mat="Bark_Branch", c0=(0,0), c1=(-50, 55))

    # Dense rounded autumn maple canopy matching tree_maple.png (~6.5m tall)
    # Lower skirt lobes (quadrants)
    m.add_foliage_lobe(radius=90, center=(-75, -75, 230), mat="Leaves_MapleCrimson")
    m.add_foliage_lobe(radius=90, center=(75, 75, 235), mat="Leaves_MapleCrimson")
    m.add_foliage_lobe(radius=85, center=(65, -60, 240), mat="Leaves_MapleRed")
    m.add_foliage_lobe(radius=85, center=(-60, 65, 240), mat="Leaves_MapleRed")

    # Mid crown lobes
    m.add_foliage_lobe(radius=105, center=(-45, -45, 310), mat="Leaves_MapleRed")
    m.add_foliage_lobe(radius=105, center=(45, 45, 315), mat="Leaves_MapleOrange")
    m.add_foliage_lobe(radius=95, center=(40, -40, 320), mat="Leaves_MapleOrange")
    m.add_foliage_lobe(radius=95, center=(-40, 40, 320), mat="Leaves_MapleRed")

    # Apex crown lobes
    m.add_foliage_lobe(radius=115, center=(0, 0, 390), mat="Leaves_MapleRed")
    m.add_foliage_lobe(radius=80, center=(15, 15, 430), mat="Leaves_MapleOrange")
    m.add_foliage_lobe(radius=75, center=(-15, -15, 425), mat="Leaves_MapleRed")
    return m

def build_poplar_columnar():
    m = Mesh("SM_Tree_Poplar_Columnar")
    m.add_material("Bark_Poplar", 0.48, 0.45, 0.38)
    m.add_material("Leaves_PoplarBright", 0.48, 0.78, 0.22)
    m.add_material("Leaves_PoplarMid", 0.36, 0.66, 0.20)
    m.add_material("Leaves_PoplarDark", 0.24, 0.50, 0.16)

    # Slender vertical trunk (~9.0m tall, diameter 40cm base)
    m.add_cylinder(r0=20, r1=16, h=180, z0=0, segs=10, mat="Bark_Poplar")
    m.add_cylinder(r0=16, r1=13, h=240, z0=180, segs=8, mat="Bark_Poplar")
    m.add_cylinder(r0=13, r1=10, h=240, z0=420, segs=8, mat="Bark_Poplar")
    m.add_cylinder(r0=10, r1=5, h=200, z0=660, segs=6, mat="Bark_Poplar")

    # Fastigiate (narrow columnar upright) canopy tiers
    # Tier 1 (Lowest)
    m.add_foliage_lobe(radius=55, center=(0, 0, 260), mat="Leaves_PoplarDark")
    m.add_foliage_lobe(radius=40, center=(25, 15, 270), mat="Leaves_PoplarDark")
    m.add_foliage_lobe(radius=40, center=(-20, -20, 275), mat="Leaves_PoplarDark")

    # Tier 2 (Lower-Mid)
    m.add_foliage_lobe(radius=68, center=(0, 0, 375), mat="Leaves_PoplarMid")
    m.add_foliage_lobe(radius=46, center=(-25, 20, 390), mat="Leaves_PoplarMid")
    m.add_foliage_lobe(radius=46, center=(22, -22, 390), mat="Leaves_PoplarMid")

    # Tier 3 (Mid widest)
    m.add_foliage_lobe(radius=76, center=(0, 0, 495), mat="Leaves_PoplarBright")
    m.add_foliage_lobe(radius=50, center=(24, 20, 510), mat="Leaves_PoplarBright")
    m.add_foliage_lobe(radius=50, center=(-22, -18, 510), mat="Leaves_PoplarMid")

    # Tier 4 (Upper-Mid)
    m.add_foliage_lobe(radius=70, center=(0, 0, 615), mat="Leaves_PoplarBright")
    m.add_foliage_lobe(radius=45, center=(-18, 18, 625), mat="Leaves_PoplarBright")
    m.add_foliage_lobe(radius=45, center=(18, -16, 625), mat="Leaves_PoplarBright")

    # Tier 5 (High)
    m.add_foliage_lobe(radius=58, center=(0, 0, 730), mat="Leaves_PoplarBright")
    m.add_foliage_lobe(radius=36, center=(12, 12, 740), mat="Leaves_PoplarBright")

    # Tier 6 (Spire Apex)
    m.add_foliage_lobe(radius=42, center=(0, 0, 830), mat="Leaves_PoplarBright")
    m.add_foliage_lobe(radius=25, center=(0, 0, 875), mat="Leaves_PoplarBright")
    return m


def build_bush_round_large():
    m = Mesh("SM_Bush_Round_Large")
    m.add_material("Leaves_Bush", 0.30, 0.66, 0.22)
    m.add_material("Leaves_Top", 0.40, 0.76, 0.26)
    m.add_material("Leaves_Dark", 0.22, 0.52, 0.18)

    m.add_foliage_lobe(radius=80, center=(0, 0, 75), mat="Leaves_Top")
    m.add_foliage_lobe(radius=65, center=(-40, -35, 60), mat="Leaves_Bush")
    m.add_foliage_lobe(radius=62, center=(45, 30, 65), mat="Leaves_Bush")
    m.add_foliage_lobe(radius=60, center=(-35, 35, 55), mat="Leaves_Dark")
    m.add_foliage_lobe(radius=58, center=(35, -35, 55), mat="Leaves_Dark")
    m.add_foliage_lobe(radius=50, center=(0, 0, 110), mat="Leaves_Top")
    return m

def build_bush_round_medium():
    m = Mesh("SM_Bush_Round_Medium")
    m.add_material("Leaves_Bush", 0.32, 0.68, 0.24)
    m.add_material("Leaves_Top", 0.42, 0.78, 0.28)

    m.add_foliage_lobe(radius=60, center=(0, 0, 52), mat="Leaves_Top")
    m.add_foliage_lobe(radius=45, center=(-28, 22, 44), mat="Leaves_Bush")
    m.add_foliage_lobe(radius=45, center=(28, -22, 44), mat="Leaves_Bush")
    m.add_foliage_lobe(radius=42, center=(0, -28, 42), mat="Leaves_Bush")
    return m

def build_bush_berry():
    m = Mesh("SM_Bush_Berry")
    m.add_material("Leaves_Bush", 0.28, 0.62, 0.20)
    m.add_material("Leaves_Top", 0.38, 0.74, 0.24)
    m.add_material("Fruit_Berry", 0.96, 0.14, 0.26)
    m.add_material("Berry_Highlight", 1.0, 0.85, 0.85)

    m.add_foliage_lobe(radius=65, center=(0, 0, 58), mat="Leaves_Top")
    m.add_foliage_lobe(radius=50, center=(-30, -25, 50), mat="Leaves_Bush")
    m.add_foliage_lobe(radius=48, center=(35, 25, 52), mat="Leaves_Bush")
    m.add_foliage_lobe(radius=44, center=(-25, 30, 48), mat="Leaves_Bush")

    # Front-facing ruby berry clusters
    R = 68.0
    Zmid = 58.0
    berry_offsets = [
        (-28, -12), (0, -22), (28, -12),
        (-38, 10), (-14, 5), (14, 8), (38, 12),
        (-22, 28), (8, 30), (28, 26), (0, 36)
    ]
    for dx, dz in berry_offsets:
        rx = dx
        rz = Zmid + dz
        rem = max(8.0, R*R - rx*rx - dz*dz)
        ry = math.sqrt(rem)
        vx = (rx + ry) * 0.7071
        vy = (ry - rx) * 0.7071
        vz = rz
        m.add_foliage_lobe(radius=9.5, center=(vx, vy, vz), mat="Fruit_Berry", subdivisions=0)
        m.add_foliage_lobe(radius=3.2, center=(vx-2, vy-2, vz+4), mat="Berry_Highlight", subdivisions=0)
    return m

def build_bush_flowering():
    m = Mesh("SM_Bush_Flowering")
    m.add_material("Leaves_Bush", 0.30, 0.65, 0.22)
    m.add_material("Leaves_Top", 0.40, 0.75, 0.26)
    m.add_material("Flower_Petal", 0.98, 0.70, 0.85)
    m.add_material("Flower_Center", 0.98, 0.90, 0.30)

    m.add_foliage_lobe(radius=62, center=(0, 0, 55), mat="Leaves_Top")
    m.add_foliage_lobe(radius=46, center=(-30, 25, 48), mat="Leaves_Bush")
    m.add_foliage_lobe(radius=44, center=(30, -25, 48), mat="Leaves_Bush")
    m.add_foliage_lobe(radius=42, center=(-25, -28, 46), mat="Leaves_Bush")

    # Front-facing 5-petal flower blossoms
    R = 66.0
    Zmid = 56.0
    blossom_offsets = [
        (-28, -10), (0, -20), (28, -10),
        (-35, 12), (-12, 6), (14, 8), (36, 12),
        (-20, 28), (8, 32), (25, 26)
    ]
    for dx, dz in blossom_offsets:
        rx = dx
        rz = Zmid + dz
        rem = max(8.0, R*R - rx*rx - dz*dz)
        ry = math.sqrt(rem)
        vx = (rx + ry) * 0.7071
        vy = (ry - rx) * 0.7071
        vz = rz

        center_pt = Vec3(vx, vy, vz)
        petal_r = 7.5
        for p_idx in range(5):
            p_ang = p_idx * 2.0 * math.pi / 5.0
            p_ang_next = (p_idx + 1) * 2.0 * math.pi / 5.0
            pt0 = Vec3(vx + petal_r * math.cos(p_ang), vy + petal_r * math.sin(p_ang), vz + 1)
            pt1 = Vec3(vx + petal_r * math.cos(p_ang_next), vy + petal_r * math.sin(p_ang_next), vz + 1)
            m.add_triangle(center_pt, pt0, pt1, mat="Flower_Petal")
        m.add_foliage_lobe(radius=3.0, center=(vx, vy, vz+2), mat="Flower_Center", subdivisions=0)
    return m

def build_bush_dry_scrub():
    m = Mesh("SM_Bush_DryScrub")
    m.add_material("Wood_Twig", 0.46, 0.38, 0.28)
    m.add_material("Scrub_Leaves", 0.55, 0.52, 0.34)
    m.add_material("Scrub_Light", 0.65, 0.60, 0.40)

    # Gnarled branch structure (8 segs)
    m.add_cylinder(r0=12, r1=7, h=35, z0=0, segs=8, mat="Wood_Twig")
    m.add_cylinder(r0=7, r1=4, h=40, z0=35, segs=6, mat="Wood_Twig", c0=(0,0), c1=(-20, 15))
    m.add_cylinder(r0=7, r1=4, h=42, z0=35, segs=6, mat="Wood_Twig", c0=(0,0), c1=(22, -18))

    m.add_foliage_lobe(radius=45, center=(0, 0, 52), mat="Scrub_Light")
    m.add_foliage_lobe(radius=34, center=(-28, -18, 42), mat="Scrub_Leaves")
    m.add_foliage_lobe(radius=32, center=(26, 22, 44), mat="Scrub_Leaves")
    m.add_foliage_lobe(radius=28, center=(-15, 25, 60), mat="Scrub_Light")
    return m

def build_bramble_large():
    m = Mesh("SM_Bramble_Patch_Large")
    m.add_material("Bramble_Vine", 0.42, 0.26, 0.18)
    m.add_material("Bramble_Thorns", 0.85, 0.22, 0.16)

    # 8 tangled arching loops with 8 radial segs and 3 curve steps each
    for i in range(8):
        angle = i * 2.0 * math.pi / 8
        r_max = 75
        x_arch = r_max * math.cos(angle)
        y_arch = r_max * math.sin(angle)

        # Step 1: Up from root
        m.add_cylinder(r0=7, r1=5.5, h=30, z0=0, segs=8, mat="Bramble_Vine", c0=(0,0), c1=(x_arch*0.35, y_arch*0.35))
        # Step 2: Arch peak
        m.add_cylinder(r0=5.5, r1=4.5, h=28, z0=30, segs=8, mat="Bramble_Vine", c0=(x_arch*0.35, y_arch*0.35), c1=(x_arch*0.75, y_arch*0.75))
        # Step 3: Loop descent
        m.add_cylinder(r0=4.5, r1=3.0, h=25, z0=40, segs=8, mat="Bramble_Vine", c0=(x_arch*0.75, y_arch*0.75), c1=(x_arch, y_arch))

        # Distinct conical thorn spikes
        p0 = Vec3(x_arch * 0.4, y_arch * 0.4, 34)
        p1 = Vec3(x_arch * 0.4 + 6, y_arch * 0.4, 34)
        p2 = Vec3(x_arch * 0.55, y_arch * 0.55, 48)
        m.add_triangle(p0, p1, p2, mat="Bramble_Thorns")

        q0 = Vec3(x_arch * 0.7, y_arch * 0.7, 42)
        q1 = Vec3(x_arch * 0.7 - 5, y_arch * 0.7 + 3, 42)
        q2 = Vec3(x_arch * 0.82, y_arch * 0.82, 54)
        m.add_triangle(q0, q1, q2, mat="Bramble_Thorns")
    return m

def build_bramble_small():
    m = Mesh("SM_Bramble_Patch_Small")
    m.add_material("Bramble_Vine", 0.42, 0.26, 0.18)
    m.add_material("Bramble_Thorns", 0.85, 0.22, 0.16)

    for i in range(5):
        angle = i * 2.0 * math.pi / 5
        r_max = 50
        x_arch = r_max * math.cos(angle)
        y_arch = r_max * math.sin(angle)

        m.add_cylinder(r0=6, r1=4.5, h=22, z0=0, segs=8, mat="Bramble_Vine", c0=(0,0), c1=(x_arch*0.4, y_arch*0.4))
        m.add_cylinder(r0=4.5, r1=3.0, h=20, z0=22, segs=8, mat="Bramble_Vine", c0=(x_arch*0.4, y_arch*0.4), c1=(x_arch*0.8, y_arch*0.8))

        p0 = Vec3(x_arch * 0.5, y_arch * 0.5, 26)
        p1 = Vec3(x_arch * 0.5 + 5, y_arch * 0.5, 26)
        p2 = Vec3(x_arch * 0.65, y_arch * 0.65, 36)
        m.add_triangle(p0, p1, p2, mat="Bramble_Thorns")
    return m

def build_bramble_arch():
    m = Mesh("SM_Bramble_Arch")
    m.add_material("Bramble_Vine", 0.40, 0.24, 0.16)
    m.add_material("Bramble_Thorns", 0.85, 0.22, 0.16)

    # Left & Right curved vertical posts (8 segs each, 3 height segments)
    m.add_cylinder(r0=12, r1=10, h=45, z0=0, segs=8, mat="Bramble_Vine", c0=(-48, 0), c1=(-46, 0))
    m.add_cylinder(r0=10, r1=8, h=45, z0=45, segs=8, mat="Bramble_Vine", c0=(-46, 0), c1=(-40, 0))
    m.add_cylinder(r0=8, r1=6, h=25, z0=90, segs=8, mat="Bramble_Vine", c0=(-40, 0), c1=(-28, 0))

    m.add_cylinder(r0=12, r1=10, h=45, z0=0, segs=8, mat="Bramble_Vine", c0=(48, 0), c1=(46, 0))
    m.add_cylinder(r0=10, r1=8, h=45, z0=45, segs=8, mat="Bramble_Vine", c0=(46, 0), c1=(40, 0))
    m.add_cylinder(r0=8, r1=6, h=25, z0=90, segs=8, mat="Bramble_Vine", c0=(40, 0), c1=(28, 0))

    # Arch keystone bridge
    m.add_cylinder(r0=7, r1=7, h=56, z0=105, segs=8, mat="Bramble_Vine", c0=(-28, 0), c1=(28, 0))

    # Thorns along the arch
    thorns = [(-42, 0, 80), (42, 0, 80), (-20, 0, 115), (20, 0, 115), (0, 0, 122)]
    for tx, ty, tz in thorns:
        m.add_triangle(Vec3(tx-3, ty-3, tz), Vec3(tx+3, ty+3, tz), Vec3(tx, ty, tz+10), mat="Bramble_Thorns")
    return m

def build_grass_meadow():
    m = Mesh("SM_Grass_Tuft_Meadow")
    m.add_material("Grass_Base", 0.24, 0.52, 0.16)
    m.add_material("Grass_Green", 0.36, 0.76, 0.22)
    m.add_material("Grass_Tip", 0.54, 0.85, 0.28)

    # 16 curved blades at diverse angles and spread (3 segments each = 5 tris/blade -> 80 tris total)
    blades = [
        (0, 42, 28, 3.4, 0),
        (25, 36, 22, 2.8, 6),
        (45, 48, 30, 3.2, 4),
        (70, 38, 24, 2.7, 8),
        (90, 44, 26, 3.0, 2),
        (115, 34, 20, 2.6, 7),
        (135, 46, 28, 3.1, 5),
        (160, 38, 22, 2.7, 8),
        (180, 43, 27, 3.0, 0),
        (205, 37, 21, 2.6, 6),
        (225, 49, 31, 3.3, 4),
        (250, 40, 23, 2.8, 7),
        (270, 45, 27, 3.0, 2),
        (295, 35, 19, 2.5, 8),
        (315, 47, 29, 3.2, 5),
        (340, 39, 22, 2.7, 7),
    ]

    for deg, h, spread, w, root_r in blades:
        rad = math.radians(deg)
        nx = -math.sin(rad)
        ny = math.cos(rad)
        fx = math.cos(rad)
        fy = math.sin(rad)

        rx = fx * root_r
        ry = fy * root_r

        # Base (z=0)
        b0 = Vec3(rx + nx * w * 0.5, ry + ny * w * 0.5, 0)
        b1 = Vec3(rx - nx * w * 0.5, ry - ny * w * 0.5, 0)

        # Mid segment 1 (z = h * 0.45)
        m1_spread = root_r + spread * 0.4
        m1_w = w * 0.75
        m1_z = h * 0.45
        m0 = Vec3(fx * m1_spread + nx * m1_w * 0.5, fy * m1_spread + ny * m1_w * 0.5, m1_z)
        m1 = Vec3(fx * m1_spread - nx * m1_w * 0.5, fy * m1_spread - ny * m1_w * 0.5, m1_z)

        # Mid segment 2 (z = h * 0.78)
        m2_spread = root_r + spread * 0.85
        m2_w = w * 0.45
        m2_z = h * 0.78
        u0 = Vec3(fx * m2_spread + nx * m2_w * 0.5, fy * m2_spread + ny * m2_w * 0.5, m2_z)
        u1 = Vec3(fx * m2_spread - nx * m2_w * 0.5, fy * m2_spread - ny * m2_w * 0.5, m2_z)

        # Tip
        tip = Vec3(fx * (root_r + spread * 1.15), fy * (root_r + spread * 1.15), h * 0.95)

        m.add_quad(b0, b1, m1, m0, mat="Grass_Base")
        m.add_quad(m0, m1, u1, u0, mat="Grass_Green")
        m.add_triangle(u0, u1, tip, mat="Grass_Tip")
    return m

def build_grass_tall_wild():
    m = Mesh("SM_Grass_Tall_Wild")
    m.add_material("Grass_Base", 0.26, 0.54, 0.18)
    m.add_material("Grass_Green", 0.36, 0.72, 0.24)
    m.add_material("Grass_Gold", 0.88, 0.76, 0.38)
    m.add_material("Seed_Plume", 0.94, 0.84, 0.48)

    # 12 tall segmented blades
    blades = [
        (15, 78, 22, 3.2), (45, 68, 18, 2.8), (75, 82, 24, 3.4),
        (105, 72, 19, 2.9), (135, 76, 21, 3.1), (165, 70, 18, 2.8),
        (195, 80, 23, 3.3), (225, 74, 20, 3.0), (255, 84, 25, 3.5),
        (285, 69, 17, 2.7), (315, 79, 22, 3.2), (345, 71, 19, 2.9)
    ]
    for deg, h, spread, w in blades:
        rad = math.radians(deg)
        nx = -math.sin(rad)
        ny = math.cos(rad)
        fx = math.cos(rad)
        fy = math.sin(rad)

        b0 = Vec3(nx * w * 0.5, ny * w * 0.5, 0)
        b1 = Vec3(-nx * w * 0.5, -ny * w * 0.5, 0)

        m0 = Vec3(fx * spread*0.35 + nx * w*0.75, fy * spread*0.35 + ny * w*0.75, h * 0.45)
        m1 = Vec3(fx * spread*0.35 - nx * w*0.75, fy * spread*0.35 - ny * w*0.75, h * 0.45)

        u0 = Vec3(fx * spread*0.8 + nx * w*0.4, fy * spread*0.8 + ny * w*0.4, h * 0.8)
        u1 = Vec3(fx * spread*0.8 - nx * w*0.4, fy * spread*0.8 - ny * w*0.4, h * 0.8)

        tip = Vec3(fx * spread * 1.1, fy * spread * 1.1, h * 0.95)

        m.add_quad(b0, b1, m1, m0, mat="Grass_Base")
        m.add_quad(m0, m1, u1, u0, mat="Grass_Green")
        m.add_triangle(u0, u1, tip, mat="Grass_Gold")

    # 4 wheat / seed plume heads
    stalks = [(0, 0, 92), (-8, 10, 88), (10, -6, 90), (6, 8, 86)]
    for sx, sy, sh in stalks:
        m.add_cylinder(r0=2.2, r1=1.6, h=sh*0.7, z0=0, segs=6, mat="Grass_Green", c0=(sx,sy), c1=(sx,sy))
        m.add_cylinder(r0=3.8, r1=2.0, h=sh*0.3, z0=sh*0.7, segs=8, mat="Seed_Plume", c0=(sx,sy), c1=(sx+4,sy+4))
    return m

def build_grass_short_lawn():
    m = Mesh("SM_Grass_Short_Lawn")
    m.add_material("Grass_Base", 0.22, 0.50, 0.16)
    m.add_material("Grass_Green", 0.32, 0.74, 0.22)
    m.add_material("Grass_Tip", 0.48, 0.82, 0.26)

    # 16 neat lawn blades (3 segments each)
    angles = [i * 22.5 for i in range(16)]
    for deg in angles:
        rad = math.radians(deg)
        nx = -math.sin(rad)
        ny = math.cos(rad)
        fx = math.cos(rad)
        fy = math.sin(rad)
        h = 24.0 + 4.0 * math.sin(deg * 0.1)
        spread = 16.0
        w = 2.8

        b0 = Vec3(nx * w * 0.5, ny * w * 0.5, 0)
        b1 = Vec3(-nx * w * 0.5, -ny * w * 0.5, 0)
        m0 = Vec3(fx * spread*0.4 + nx * w*0.7, fy * spread*0.4 + ny * w*0.7, h * 0.45)
        m1 = Vec3(fx * spread*0.4 - nx * w*0.7, fy * spread*0.4 - ny * w*0.7, h * 0.45)
        u0 = Vec3(fx * spread*0.8 + nx * w*0.4, fy * spread*0.8 + ny * w*0.4, h * 0.8)
        u1 = Vec3(fx * spread*0.8 - nx * w*0.4, fy * spread*0.8 - ny * w*0.4, h * 0.8)
        tip = Vec3(fx * spread * 1.1, fy * spread * 1.1, h * 0.95)

        m.add_quad(b0, b1, m1, m0, mat="Grass_Base")
        m.add_quad(m0, m1, u1, u0, mat="Grass_Green")
        m.add_triangle(u0, u1, tip, mat="Grass_Tip")
    return m

def build_reeds_cattail():
    m = Mesh("SM_Flora_Reeds_Cattail")
    m.add_material("Reed_Green", 0.32, 0.62, 0.24)
    m.add_material("Reed_Light", 0.42, 0.74, 0.28)
    m.add_material("Cattail_Brown", 0.44, 0.25, 0.16)

    # 3 stout cattail stalks (8 segs stem, 10 segs velvet cylinder)
    locs = [(0, 0, 142), (-18, 12, 128), (16, -14, 134)]
    for cx, cy, h in locs:
        # Stem
        m.add_cylinder(r0=3.2, r1=2.6, h=h*0.75, z0=0, segs=8, mat="Reed_Green", c0=(cx,cy), c1=(cx,cy))
        # Velvet brown cattail sausage (10 segs)
        cz = h * 0.75
        c_h = h * 0.18
        m.add_cylinder(r0=7.0, r1=7.0, h=c_h, z0=cz, segs=10, mat="Cattail_Brown", c0=(cx,cy), c1=(cx,cy))
        # Top spike
        m.add_cone(r=2.5, h=h*0.07, z0=cz+c_h, segs=8, mat="Reed_Green", c=(cx,cy))

    # 12 arching reed leaves with 3 curved segments each
    for deg in [15, 45, 75, 105, 135, 165, 195, 225, 255, 285, 315, 345]:
        rad = math.radians(deg)
        nx = -math.sin(rad)
        ny = math.cos(rad)
        fx = math.cos(rad)
        fy = math.sin(rad)
        lh = 95.0
        lw = 4.0
        spread = 32.0

        b0 = Vec3(nx * lw*0.5, ny * lw*0.5, 0)
        b1 = Vec3(-nx * lw*0.5, -ny * lw*0.5, 0)
        m0 = Vec3(fx * spread*0.35 + nx * lw*0.75, fy * spread*0.35 + ny * lw*0.75, lh * 0.45)
        m1 = Vec3(fx * spread*0.35 - nx * lw*0.75, fy * spread*0.35 - ny * lw*0.75, lh * 0.45)
        u0 = Vec3(fx * spread*0.8 + nx * lw*0.4, fy * spread*0.8 + ny * lw*0.4, lh * 0.8)
        u1 = Vec3(fx * spread*0.8 - nx * lw*0.4, fy * spread*0.8 - ny * lw*0.4, lh * 0.8)
        tip = Vec3(fx * spread * 1.15, fy * spread * 1.15, lh * 0.95)

        m.add_quad(b0, b1, m1, m0, mat="Reed_Green")
        m.add_quad(m0, m1, u1, u0, mat="Reed_Light")
        m.add_triangle(u0, u1, tip, mat="Reed_Light")
    return m

def build_fern_forest():
    m = Mesh("SM_Flora_Fern_Forest")
    m.add_material("Fern_Stem", 0.22, 0.48, 0.18)
    m.add_material("Fern_Green", 0.28, 0.68, 0.24)
    m.add_material("Fern_Light", 0.38, 0.78, 0.28)

    # 9 gracefully arching fronds radiating outward
    angles = [i * 2.0 * math.pi / 9 for i in range(9)]
    for a in angles:
        rx = math.cos(a)
        ry = math.sin(a)
        nx = -math.sin(a)
        ny = math.cos(a)

        # 4 spine points forming an arching curve
        p0 = Vec3(0, 0, 0)
        p1 = Vec3(25 * rx, 25 * ry, 36)
        p2 = Vec3(52 * rx, 52 * ry, 54)
        p3 = Vec3(75 * rx, 75 * ry, 40)
        p4 = Vec3(90 * rx, 90 * ry, 22)

        # Frond spine
        m.add_triangle(p0, p1, p2, mat="Fern_Stem")
        m.add_triangle(p2, p3, p4, mat="Fern_Stem")

        # 4 pairs of lateral leaflets along the frond
        pairs = [
            (p1, 16, "Fern_Green"),
            (p2, 22, "Fern_Green"),
            (p3, 18, "Fern_Light"),
            (p4, 10, "Fern_Light"),
        ]
        for pt, span, mat in pairs:
            # Left leaflet
            l0 = Vec3(pt.x + nx * span, pt.y + ny * span, pt.z + 4)
            m.add_triangle(pt, l0, Vec3(pt.x + nx * span*0.5 + rx*8, pt.y + ny * span*0.5 + ry*8, pt.z + 2), mat=mat)
            # Right leaflet
            r0 = Vec3(pt.x - nx * span, pt.y - ny * span, pt.z + 4)
            m.add_triangle(pt, Vec3(pt.x - nx * span*0.5 + rx*8, pt.y - ny * span*0.5 + ry*8, pt.z + 2), r0, mat=mat)
    return m

def build_mushroom_cluster():
    m = Mesh("SM_Flora_Mushroom_Cluster")
    m.add_material("Shroom_Cap", 0.90, 0.16, 0.14)
    m.add_material("Shroom_CapLight", 0.98, 0.28, 0.22)
    m.add_material("Shroom_Stem", 0.94, 0.92, 0.86)
    m.add_material("Shroom_Spot", 0.98, 0.98, 0.96)

    shroom_defs = [
        (0, 0, 14, 38, 52),
        (-28, 16, 9, 24, 34),
        (24, -18, 8, 20, 26)
    ]
    for cx, cy, r_stem, r_cap, h in shroom_defs:
        # Stem (10 segs)
        m.add_cylinder(r0=r_stem*1.3, r1=r_stem, h=h*0.4, z0=0, segs=10, mat="Shroom_Stem", c0=(cx,cy), c1=(cx,cy))
        m.add_cylinder(r0=r_stem, r1=r_stem*0.85, h=h*0.35, z0=h*0.4, segs=10, mat="Shroom_Stem", c0=(cx,cy), c1=(cx,cy))

        # Dome Cap: 14 radial segments with 2 height tiers (forming a rounded low-poly hemisphere)
        cz = h * 0.75
        cap_segs = 14
        r_mid = r_cap * 0.75
        z_mid = cz + h * 0.28
        apex = Vec3(cx, cy, cz + h * 0.48)

        for i in range(cap_segs):
            a0 = i * 2.0 * math.pi / cap_segs
            a1 = (i + 1) * 2.0 * math.pi / cap_segs

            # Lower rim
            p0 = Vec3(cx + r_cap * math.cos(a0), cy + r_cap * math.sin(a0), cz)
            p1 = Vec3(cx + r_cap * math.cos(a1), cy + r_cap * math.sin(a1), cz)

            # Mid latitude ring
            m0 = Vec3(cx + r_mid * math.cos(a0), cy + r_mid * math.sin(a0), z_mid)
            m1 = Vec3(cx + r_mid * math.cos(a1), cy + r_mid * math.sin(a1), z_mid)

            # Lower skirt quad
            m.add_quad(p0, p1, m1, m0, mat="Shroom_Cap")
            # Upper dome triangle to apex
            m.add_triangle(m0, m1, apex, mat="Shroom_CapLight")
            # Underside gills
            m.add_triangle(Vec3(cx, cy, cz+2), p1, p0, mat="Shroom_Stem")

        # White toadstool spots
        for sa in [0.4, 1.2, 2.0, 2.8, 3.6, 4.4, 5.2]:
            sx = cx + r_cap * 0.55 * math.cos(sa)
            sy = cy + r_cap * 0.55 * math.sin(sa)
            sz = cz + h * 0.32
            sr = r_cap * 0.14
            m.add_triangle(Vec3(sx-sr, sy, sz), Vec3(sx+sr, sy, sz), Vec3(sx, sy+sr, sz+1), mat="Shroom_Spot")
    return m

def build_tree_stump():
    m = Mesh("SM_Flora_Tree_Stump")
    m.add_material("Bark_Old", 0.42, 0.28, 0.18)
    m.add_material("Bark_Dark", 0.32, 0.20, 0.12)
    m.add_material("Wood_Rings", 0.75, 0.62, 0.44)
    m.add_material("Wood_Core", 0.62, 0.50, 0.34)
    m.add_material("Moss_Green", 0.35, 0.65, 0.24)

    # 12-segment bark trunk with flare
    m.add_cylinder(r0=56, r1=44, h=65, z0=0, segs=12, mat="Bark_Old")

    # 4 root buttresses sprawling on the ground
    for deg in [30, 120, 210, 300]:
        rad = math.radians(deg)
        rx = math.cos(rad)
        ry = math.sin(rad)
        p0 = Vec3(48 * rx, 48 * ry, 0)
        p1 = Vec3(72 * rx, 72 * ry, 0)
        p2 = Vec3(42 * rx, 42 * ry, 28)
        m.add_triangle(p0, p1, p2, mat="Bark_Dark")

    # Cut top cross-section with concentric growth rings (12 segs)
    top_c = Vec3(0, 0, 65)
    inner_c = Vec3(0, 0, 64.5)
    segs = 12
    for i in range(segs):
        a0 = i * 2.0 * math.pi / segs
        a1 = (i + 1) * 2.0 * math.pi / segs
        p0 = Vec3(44 * math.cos(a0), 44 * math.sin(a0), 65)
        p1 = Vec3(44 * math.cos(a1), 44 * math.sin(a1), 65)
        m0 = Vec3(22 * math.cos(a0), 22 * math.sin(a0), 64.5)
        m1 = Vec3(22 * math.cos(a1), 22 * math.sin(a1), 64.5)
        m.add_quad(p0, p1, m1, m0, mat="Wood_Rings")
        m.add_triangle(inner_c, m0, m1, mat="Wood_Core")

    m.add_foliage_lobe(radius=18, center=(-38, 22, 12), mat="Moss_Green")
    m.add_foliage_lobe(radius=14, center=(32, -28, 10), mat="Moss_Green")
    return m

def build_fallen_log():
    m = Mesh("SM_Flora_Fallen_Log")
    m.add_material("Bark_Old", 0.40, 0.26, 0.16)
    m.add_material("Bark_Dark", 0.30, 0.18, 0.12)
    m.add_material("Wood_Core", 0.62, 0.48, 0.32)
    m.add_material("Wood_Splinter", 0.72, 0.58, 0.40)
    m.add_material("Moss_Green", 0.34, 0.64, 0.22)

    # 12-segment horizontal log cylinder
    r = 24
    segs = 12
    angles = [i * 2.0 * math.pi / segs for i in range(segs)]
    for i in range(segs):
        a0 = angles[i]
        a1 = angles[(i+1)%segs]
        y0 = r * math.cos(a0)
        z0 = 24 + r * math.sin(a0)
        y1 = r * math.cos(a1)
        z1 = 24 + r * math.sin(a1)
        v0 = Vec3(-125, y0, z0)
        v1 = Vec3( 125, y0, z0)
        v2 = Vec3( 125, y1, z1)
        v3 = Vec3(-125, y1, z1)
        mat = "Bark_Old" if (i % 2 == 0) else "Bark_Dark"
        m.add_quad(v0, v1, v2, v3, mat=mat)

    # End cut caps with growth rings
    c_left = Vec3(-125, 0, 24)
    c_right = Vec3(125, 0, 24)
    for i in range(segs):
        a0 = angles[i]
        a1 = angles[(i+1)%segs]
        p0 = Vec3(-125, r * math.cos(a0), 24 + r * math.sin(a0))
        p1 = Vec3(-125, r * math.cos(a1), 24 + r * math.sin(a1))
        m.add_triangle(c_left, p1, p0, mat="Wood_Core")
        q0 = Vec3(125, r * math.cos(a0), 24 + r * math.sin(a0))
        q1 = Vec3(125, r * math.cos(a1), 24 + r * math.sin(a1))
        m.add_triangle(c_right, q0, q1, mat="Wood_Splinter")

    # Moss cushions on top
    m.add_foliage_lobe(radius=18, center=(25, 10, 44), mat="Moss_Green")
    m.add_foliage_lobe(radius=15, center=(-45, -8, 43), mat="Moss_Green")
    return m


# -----------------------------------------------------------------------------
# 3D Icon Renderer (Stylized Cel-Shaded 128x128 Transparent RGBA)
# -----------------------------------------------------------------------------

def render_mesh_to_icon(mesh, output_size=128, max_dim=96):
    """
    Renders 3D foliage mesh into a strictly compliant 128x128 32-bit transparent RGBA icon:
    - Authentic 3/4 South-East isometric view (+X, -Y, +Z) matching building icons and item standards
    - Backface culling to eliminate interior/reverse polygon artifacts
    - Directional warm key light (-0.6, -0.6, 0.75) + cool fill light
    - Stylized cel-shading tonal ramps
    - Crisp dark ink contour outline (1-2px)
    - Clean faceted faces without internal CAD wireframe lines
    - Scaled into <= max_dim (96px) with >= 12px clean transparent margin
    - 100% outer perimeter pixels alpha == 0
    - NO frames, NO drop shadows, NO borders
    """
    mesh.ground_align()

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

        # Stylized tonal lighting
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

    # Stylized dark ink silhouette contour outline (2px stroke on 128x128)
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
# Main Generation Orchestrator
# -----------------------------------------------------------------------------

GENERATORS = [
    # Trees (14)
    ("SM_Tree_Oak_Large", build_oak_large),
    ("SM_Tree_Oak_Medium", build_oak_medium),
    ("SM_Tree_Oak_Small", build_oak_small),
    ("SM_Tree_Oak_Autumn", build_oak_autumn),
    ("SM_Tree_Pine_Tall", build_pine_tall),
    ("SM_Tree_Pine_Medium", build_pine_medium),
    ("SM_Tree_Pine_Small", build_pine_small),
    ("SM_Tree_Birch_Tall", build_birch_tall),
    ("SM_Tree_Birch_Medium", build_birch_medium),
    ("SM_Tree_Apple", build_apple_tree),
    ("SM_Tree_Willow", build_willow_tree),
    ("SM_Tree_Dead_Snag", build_dead_snag),
    ("SM_Tree_Maple", build_maple_tree),
    ("SM_Tree_Poplar_Columnar", build_poplar_columnar),
    # Bushes & Shrubs (5)
    ("SM_Bush_Round_Large", build_bush_round_large),
    ("SM_Bush_Round_Medium", build_bush_round_medium),
    ("SM_Bush_Berry", build_bush_berry),
    ("SM_Bush_Flowering", build_bush_flowering),
    ("SM_Bush_DryScrub", build_bush_dry_scrub),
    # Brambles (3)
    ("SM_Bramble_Patch_Large", build_bramble_large),
    ("SM_Bramble_Patch_Small", build_bramble_small),
    ("SM_Bramble_Arch", build_bramble_arch),
    # Grasses & Reeds (4)
    ("SM_Grass_Tuft_Meadow", build_grass_meadow),
    ("SM_Grass_Tall_Wild", build_grass_tall_wild),
    ("SM_Grass_Short_Lawn", build_grass_short_lawn),
    ("SM_Flora_Reeds_Cattail", build_reeds_cattail),
    # Forest Floor & Features (4)
    ("SM_Flora_Fern_Forest", build_fern_forest),
    ("SM_Flora_Mushroom_Cluster", build_mushroom_cluster),
    ("SM_Flora_Tree_Stump", build_tree_stump),
    ("SM_Flora_Fallen_Log", build_fallen_log),
]

def main():
    print(f"=== Homesteader 3D Low-Poly Foliage & Icon Generator (v3 Enhanced Poly) ===")
    print(f"Target Assets: {len(GENERATORS)} items")
    print(f"Models Target: {HUD_MODELS_DIR}")
    print(f"Icons Target:  {HUD_ICONS_DIR}")

    success_count = 0
    for name, gen_func in GENERATORS:
        mesh = gen_func()
        mesh.ground_align()
        tri_count = len(mesh.faces)
        print(f"--> Generating {name} ({tri_count} tris)...")

        # 1. Save OBJ and MTL to HUD workspace
        hud_obj = os.path.join(HUD_MODELS_DIR, f"{name}.obj")
        hud_mtl = os.path.join(HUD_MODELS_DIR, f"{name}.mtl")
        mesh.save_obj(hud_obj, hud_mtl)

        # 2. Copy to UE5 project folder
        ue5_obj = os.path.join(UE5_MODELS_DIR, f"{name}.obj")
        ue5_mtl = os.path.join(UE5_MODELS_DIR, f"{name}.mtl")
        shutil.copy2(hud_obj, ue5_obj)
        shutil.copy2(hud_mtl, ue5_mtl)

        # 3. Render matching 128x128 transparent icon (RIGHT SIDE UP, CEL-SHADED)
        icon_img = render_mesh_to_icon(mesh, output_size=128, max_dim=94)
        hud_icon = os.path.join(HUD_ICONS_DIR, f"{name}.png")
        ue5_icon = os.path.join(UE5_ICONS_DIR, f"{name}.png")
        icon_img.save(hud_icon, "PNG")
        icon_img.save(ue5_icon, "PNG")

        success_count += 1

    print(f"\nSuccessfully generated {success_count}/{len(GENERATORS)} foliage assets!")
    print(f"All meshes and 128x128 icons synchronized to HUD and UE5 directories.")

if __name__ == "__main__":
    main()
