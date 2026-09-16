#!/usr/bin/env python3
"""
generate_planted_saplings_and_stumps.py
Creates:
1. 7 Planted Saplings (without burlap root balls):
   - planted_sapling_oak, planted_sapling_pine, planted_sapling_birch,
   - planted_sapling_maple, planted_sapling_apple, planted_sapling_willow,
   - planted_sapling_poplar
2. 21 Multi-Age Tree Stumps (7 species x 3 age stages: small, medium, large):
   - stump_<species>_small, stump_<species>_medium, stump_<species>_large

Each item generates:
- Low-poly 3D Wavefront OBJ + MTL with metric scale and ground-aligned pivot
- 128x128 32-bit transparent RGBA cel-shaded faceted icon conforming to Homesteader standards
- <item_id>.json machine-readable manifest ready for the plugin system
- README.md human-readable preview
"""

import os
import math
import json
from PIL import Image, ImageDraw, ImageFilter

HOMESTEADER_DIR = r"C:\Users\casey\Desktop\Homesteader"
ASSETS_DIR = os.path.join(HOMESTEADER_DIR, "assets", "logging")
HUD_DIR = os.path.join(HOMESTEADER_DIR, "HUD")
UE_CONTENT_DIR = os.path.join(HOMESTEADER_DIR, "Homesteader", "Content", "Homesteader")

os.makedirs(ASSETS_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# Vector Math & Mesh Core
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

    def add_cylinder(self, r0, r1, h, z0=0.0, segs=8, mat="trunk", c0=(0,0), c1=(0,0)):
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

    def add_cone(self, r, h, z0=0.0, segs=8, mat="cone", c=(0,0)):
        cx, cy = c
        apex = Vec3(cx, cy, z0 + h)
        for i in range(segs):
            a0 = i * 2.0 * math.pi / segs
            a1 = (i + 1) * 2.0 * math.pi / segs
            p0 = Vec3(cx + r * math.cos(a0), cy + r * math.sin(a0), z0)
            p1 = Vec3(cx + r * math.cos(a1), cy + r * math.sin(a1), z0)
            self.add_triangle(p0, p1, apex, mat=mat)

    def add_icosphere_lobe(self, radius, center=(0,0,0), subdivisions=1, mat="foliage", flatten_z=0.9):
        c = Vec3(*center) if not isinstance(center, Vec3) else center
        phi = (1.0 + math.sqrt(5.0)) / 2.0
        raw_verts = [
            Vec3(-1,  phi, 0), Vec3( 1,  phi, 0), Vec3(-1, -phi, 0), Vec3( 1, -phi, 0),
            Vec3( 0, -1,  phi), Vec3( 0,  1,  phi), Vec3( 0, -1, -phi), Vec3( 0,  1, -phi),
            Vec3( phi, 0, -1), Vec3( phi, 0,  1), Vec3(-phi, 0, -1), Vec3(-phi, 0,  1),
        ]
        verts = [v.normalized() for v in raw_verts]
        faces = [
            (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
            (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
            (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
            (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)
        ]

        mid_cache = {}
        def get_midpoint(i1, i2):
            key = (min(i1, i2), max(i1, i2))
            if key in mid_cache: return mid_cache[key]
            m = (verts[i1] + verts[i2]) * 0.5
            mid_idx = len(verts)
            verts.append(m.normalized())
            mid_cache[key] = mid_idx
            return mid_idx

        for _ in range(subdivisions):
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
            p0 = Vec3(c.x + v0.x * radius, c.y + v0.y * radius, c.z + v0.z * radius * flatten_z)
            p1 = Vec3(c.x + v1.x * radius, c.y + v1.y * radius, c.z + v1.z * radius * flatten_z)
            p2 = Vec3(c.x + v2.x * radius, c.y + v2.y * radius, c.z + v2.z * radius * flatten_z)
            self.add_triangle(p0, p1, p2, mat=mat)

    def ground_align(self):
        if not self.vertices: return
        min_z = min(v.z for v in self.vertices)
        offset = Vec3(0, 0, -min_z)
        self.vertices = [v + offset for v in self.vertices]

    def compute_bounds(self):
        if not self.vertices:
            return {"width_x_cm": 0, "depth_y_cm": 0, "height_z_cm": 0,
                    "width_x_m": 0, "depth_y_m": 0, "height_z_m": 0,
                    "vertices": 0, "faces": 0, "bounds": [0,0,0,0,0,0]}
        xs = [v.x for v in self.vertices]
        ys = [v.y for v in self.vertices]
        zs = [v.z for v in self.vertices]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        min_z, max_z = min(zs), max(zs)
        dx = max_x - min_x
        dy = max_y - min_y
        dz = max_z - min_z
        return {
            "width_x_cm": round(dx, 1),
            "depth_y_cm": round(dy, 1),
            "height_z_cm": round(dz, 1),
            "width_x_m": round(dx / 100.0, 2),
            "depth_y_m": round(dy / 100.0, 2),
            "height_z_m": round(dz / 100.0, 2),
            "vertices": len(self.vertices),
            "faces": len(self.faces),
            "bounds": [round(min_x, 1), round(max_x, 1), round(min_y, 1), round(max_y, 1), round(min_z, 1), round(max_z, 1)]
        }

    def save_obj_and_mtl(self, obj_path, mtl_path):
        mtl_filename = os.path.basename(mtl_path)
        with open(obj_path, "w", encoding="utf-8") as f:
            f.write(f"# Homesteader 3D Asset - {self.name}\n")
            f.write(f"mtllib {mtl_filename}\n")
            f.write(f"o {self.name}\n\n")
            for v in self.vertices:
                f.write(f"v {v.x:.4f} {v.y:.4f} {v.z:.4f}\n")
            for vt in self.uvs:
                f.write(f"vt {vt[0]:.4f} {vt[1]:.4f}\n")
            for vn in self.normals:
                f.write(f"vn {vn.x:.4f} {vn.y:.4f} {vn.z:.4f}\n")

            cur_mat = None
            for face_verts, mat in self.faces:
                if mat != cur_mat:
                    f.write(f"usemtl {mat}\ns 1\n")
                    cur_mat = mat
                face_str = " ".join([f"{v}/{vt}/{vn}" for v, vt, vn in face_verts])
                f.write(f"f {face_str}\n")

        with open(mtl_path, "w", encoding="utf-8") as f:
            f.write("# Homesteader Material Definition\n\n")
            for mat_name, (r, g, b) in self.materials.items():
                f.write(f"newmtl {mat_name}\n")
                f.write(f"Ka {r*0.4:.4f} {g*0.4:.4f} {b*0.4:.4f}\n")
                f.write(f"Kd {r:.4f} {g:.4f} {b:.4f}\n")
                f.write(f"Ks 0.12 0.12 0.12\n")
                f.write(f"Ns 12.0\nd 1.0\nillum 2\n\n")

# -----------------------------------------------------------------------------
# 3D Software Icon Renderer (Homesteader Cel-Shaded Faceted Standard)
# -----------------------------------------------------------------------------

def render_mesh_to_icon(mesh, output_size=128, max_dim=96, pitch_deg=30.0, yaw_deg=315.0):
    """Renders 128x128 32-bit transparent RGBA icon matching Homesteader icon standards."""
    mesh.ground_align()

    pitch = math.radians(pitch_deg)
    yaw = math.radians(yaw_deg)

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

    triangles.sort(key=lambda t: t[0])
    for d, pts, fill in triangles:
        draw.polygon(pts, fill=fill, outline=fill)

    # Ink contour silhouette
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
# Planted Saplings Builders (No burlap bags on bottom)
# -----------------------------------------------------------------------------

def build_planted_sapling(species_name, bark_color, foliage_colors, foliage_style="broadleaf"):
    """
    Creates a young sapling planted directly into the ground (Z=0)
    with a small soil collar/root flare, NO burlap nursery bag!
    """
    m = Mesh(f"SM_Planted_Sapling_{species_name.capitalize()}")
    m.add_material("Soil_Bed", 0.22, 0.16, 0.12)
    m.add_material("Bark", *bark_color)
    for i, fc in enumerate(foliage_colors):
        m.add_material(f"Foliage_{i}", *fc)

    # Soil base mound (subtle ring where sapling is firmly planted)
    m.add_cylinder(r0=14, r1=7, h=5, z0=0, segs=8, mat="Soil_Bed")

    # Slender sapling stem/trunk (tapers from r=3.8 to 2.2 cm, height ~115 cm)
    m.add_cylinder(r0=4.2, r1=3.0, h=45, z0=4, segs=7, mat="Bark")
    m.add_cylinder(r0=3.0, r1=2.0, h=45, z0=49, segs=7, mat="Bark", c0=(0,0), c1=(1.5, 1.0))
    m.add_cylinder(r0=2.0, r1=1.2, h=35, z0=94, segs=6, mat="Bark", c0=(1.5,1.0), c1=(3.0, 2.0))

    # Little branches
    m.add_cylinder(r0=1.4, r1=0.8, h=25, z0=65, segs=5, mat="Bark", c0=(1,0.5), c1=(-18, -12))
    m.add_cylinder(r0=1.4, r1=0.8, h=25, z0=80, segs=5, mat="Bark", c0=(2,1.5), c1=(16, 14))

    if foliage_style == "conifer":
        # Stepped 3-tier conical needle whorls for Pine
        m.add_cone(r=26, h=34, z0=45, segs=7, mat="Foliage_1", c=(0,0))
        m.add_cone(r=20, h=30, z0=72, segs=7, mat="Foliage_0", c=(1,1))
        m.add_cone(r=14, h=28, z0=96, segs=6, mat="Foliage_0", c=(2,2))
    elif foliage_style == "columnar":
        # Slender compact lobes for Poplar
        m.add_icosphere_lobe(radius=15, center=(-2, -2, 70), subdivisions=1, mat="Foliage_1", flatten_z=1.4)
        m.add_icosphere_lobe(radius=16, center=(2, 2, 95), subdivisions=1, mat="Foliage_0", flatten_z=1.4)
        m.add_icosphere_lobe(radius=14, center=(1, 1, 120), subdivisions=1, mat="Foliage_0", flatten_z=1.3)
    elif foliage_style == "weeping":
        # Soft cascading lobes for Willow
        m.add_icosphere_lobe(radius=20, center=(-12, -10, 75), subdivisions=1, mat="Foliage_1", flatten_z=1.1)
        m.add_icosphere_lobe(radius=22, center=(12, 10, 85), subdivisions=1, mat="Foliage_0", flatten_z=1.1)
        m.add_icosphere_lobe(radius=18, center=(0, 0, 105), subdivisions=1, mat="Foliage_0", flatten_z=0.9)
    else:
        # Standard broadleaf clusters (Oak, Birch, Maple, Apple)
        m.add_icosphere_lobe(radius=20, center=(-18, -12, 85), subdivisions=1, mat="Foliage_1", flatten_z=0.9)
        m.add_icosphere_lobe(radius=20, center=(16, 14, 95), subdivisions=1, mat="Foliage_0", flatten_z=0.9)
        m.add_icosphere_lobe(radius=22, center=(3, 2, 115), subdivisions=1, mat="Foliage_0", flatten_z=0.9)
        if len(foliage_colors) > 2:
            m.add_icosphere_lobe(radius=14, center=(0, 0, 130), subdivisions=1, mat="Foliage_2", flatten_z=0.85)

    return m

# -----------------------------------------------------------------------------
# Multi-Age Tree Stumps Builders (Small, Medium, Large)
# -----------------------------------------------------------------------------

def build_tree_stump(species_name, age_stage, bark_color, wood_ring_color, wood_core_color, is_birch=False):
    """
    Builds a tree stump tailored to exact species and age stage:
    - small: slender trunk (r~14cm, h~28cm), light roots
    - medium: mid-size trunk (r~25cm, h~42cm), 4 flared root buttresses
    - large: massive mature stump (r~40cm, h~60cm), heavy root buttresses, moss accents
    """
    m = Mesh(f"SM_Stump_{species_name.capitalize()}_{age_stage.capitalize()}")
    m.add_material("Bark", *bark_color)
    m.add_material("Wood_Rings", *wood_ring_color)
    m.add_material("Wood_Core", *wood_core_color)
    if is_birch:
        m.add_material("Birch_Notch", 0.20, 0.18, 0.16)
    m.add_material("Moss", 0.32, 0.60, 0.22)

    if age_stage == "small":
        r0 = 16.0
        r1 = 13.0
        h = 28.0
        segs = 8
        num_roots = 3
        r_buttress = 25.0
        ring_cut = 0.50
    elif age_stage == "medium":
        r0 = 27.0
        r1 = 22.0
        h = 42.0
        segs = 10
        num_roots = 4
        r_buttress = 42.0
        ring_cut = 0.48
    else:  # large
        r0 = 42.0
        r1 = 34.0
        h = 58.0
        segs = 12
        num_roots = 5
        r_buttress = 65.0
        ring_cut = 0.45

    # Main trunk cylinder
    m.add_cylinder(r0=r0, r1=r1, h=h, z0=0, segs=segs, mat="Bark")

    # Flared root buttresses anchored to ground
    for i in range(num_roots):
        deg = i * (360.0 / num_roots) + 18.0
        rad = math.radians(deg)
        rx = math.cos(rad)
        ry = math.sin(rad)
        p0 = Vec3(r0 * 0.95 * rx, r0 * 0.95 * ry, 0)
        p1 = Vec3(r_buttress * rx, r_buttress * ry, 0)
        p2 = Vec3(r0 * 0.75 * rx, r0 * 0.75 * ry, h * 0.45)
        m.add_triangle(p0, p1, p2, mat="Bark")

    # Cut top surface with concentric growth rings
    inner_c = Vec3(0, 0, h - 0.4)
    for i in range(segs):
        a0 = i * 2.0 * math.pi / segs
        a1 = (i + 1) * 2.0 * math.pi / segs
        p0 = Vec3(r1 * math.cos(a0), r1 * math.sin(a0), h)
        p1 = Vec3(r1 * math.cos(a1), r1 * math.sin(a1), h)
        m0 = Vec3(r1 * ring_cut * math.cos(a0), r1 * ring_cut * math.sin(a0), h - 0.4)
        m1 = Vec3(r1 * ring_cut * math.cos(a1), r1 * ring_cut * math.sin(a1), h - 0.4)
        m.add_quad(p0, p1, m1, m0, mat="Wood_Rings")
        m.add_triangle(inner_c, m0, m1, mat="Wood_Core")

    # Birch bark lenticels / notches
    if is_birch:
        for b_z in [h * 0.3, h * 0.65]:
            m.add_cylinder(r0=r0*0.99, r1=r0*0.98, h=2.5, z0=b_z, segs=segs, mat="Birch_Notch")

    # Small moss accents on medium and large stumps
    if age_stage in ["medium", "large"]:
        moss_r = 8.0 if age_stage == "medium" else 14.0
        m.add_icosphere_lobe(radius=moss_r, center=(-r0*0.75, r0*0.4, 6), subdivisions=1, mat="Moss", flatten_z=0.7)
        if age_stage == "large":
            m.add_icosphere_lobe(radius=10.0, center=(r0*0.65, -r0*0.5, 8), subdivisions=1, mat="Moss", flatten_z=0.6)

    return m

# -----------------------------------------------------------------------------
# Asset Definition Tables
# -----------------------------------------------------------------------------

PLANTED_SAPLINGS = [
    ("planted_sapling_oak", "Planted Oak Sapling", "oak", (0.42, 0.28, 0.16), [(0.42, 0.72, 0.22), (0.24, 0.54, 0.18)], "broadleaf"),
    ("planted_sapling_pine", "Planted Pine Sapling", "pine", (0.36, 0.22, 0.14), [(0.36, 0.64, 0.28), (0.24, 0.50, 0.22)], "conifer"),
    ("planted_sapling_birch", "Planted Birch Sapling", "birch", (0.92, 0.92, 0.88), [(0.58, 0.84, 0.34), (0.50, 0.76, 0.28)], "broadleaf"),
    ("planted_sapling_maple", "Planted Maple Sapling", "maple", (0.44, 0.30, 0.20), [(0.82, 0.22, 0.15), (0.88, 0.44, 0.14)], "broadleaf"),
    ("planted_sapling_apple", "Planted Apple Sapling", "apple", (0.38, 0.25, 0.16), [(0.40, 0.70, 0.22), (0.32, 0.58, 0.18)], "broadleaf"),
    ("planted_sapling_willow", "Planted Willow Sapling", "willow", (0.40, 0.34, 0.24), [(0.46, 0.70, 0.32), (0.36, 0.56, 0.26)], "weeping"),
    ("planted_sapling_poplar", "Planted Poplar Sapling", "poplar", (0.48, 0.44, 0.32), [(0.44, 0.72, 0.26), (0.36, 0.60, 0.20)], "columnar"),
]

STUMP_SPECIES = [
    ("oak", "Oak", (0.42, 0.26, 0.15), (0.78, 0.64, 0.42), (0.64, 0.50, 0.32), False),
    ("pine", "Pine", (0.36, 0.22, 0.14), (0.82, 0.60, 0.36), (0.70, 0.48, 0.28), False),
    ("birch", "Birch", (0.92, 0.92, 0.88), (0.88, 0.82, 0.68), (0.78, 0.70, 0.54), True),
    ("maple", "Maple", (0.44, 0.30, 0.20), (0.80, 0.68, 0.46), (0.66, 0.52, 0.34), False),
    ("apple", "Apple", (0.38, 0.25, 0.16), (0.76, 0.56, 0.40), (0.62, 0.44, 0.30), False),
    ("willow", "Willow", (0.40, 0.34, 0.24), (0.74, 0.66, 0.50), (0.60, 0.52, 0.38), False),
    ("poplar", "Poplar", (0.48, 0.44, 0.32), (0.84, 0.78, 0.62), (0.72, 0.64, 0.48), False),
]

# -----------------------------------------------------------------------------
# Generation Pipeline
# -----------------------------------------------------------------------------

def main():
    print("=== STARTING GENERATION OF PLANTED SAPLINGS & MULTI-AGE STUMPS ===")
    
    created_items = []
    
    # 1. Generate Planted Saplings (7)
    for item_id, display_name, species, bark_c, fol_c, style in PLANTED_SAPLINGS:
        print(f"Generating planted sapling: {item_id}...")
        item_dir = os.path.join(ASSETS_DIR, item_id)
        os.makedirs(item_dir, exist_ok=True)
        
        mesh = build_planted_sapling(species, bark_c, fol_c, style)
        mesh.ground_align()
        
        obj_name = f"SM_{item_id.title().replace('_', '')}.obj"
        mtl_name = f"SM_{item_id.title().replace('_', '')}.mtl"
        obj_path = os.path.join(item_dir, obj_name)
        mtl_path = os.path.join(item_dir, mtl_name)
        mesh.save_obj_and_mtl(obj_path, mtl_path)
        
        # Render icon
        icon_name = f"{item_id}.png"
        icon_path = os.path.join(item_dir, icon_name)
        icon_img = render_mesh_to_icon(mesh, output_size=128, max_dim=96, pitch_deg=25.0, yaw_deg=315.0)
        icon_img.save(icon_path, "PNG")
        
        bounds = mesh.compute_bounds()
        
        # JSON manifest
        manifest = {
            "$schema": "https://homesteader.game/schemas/item_v1.json",
            "id": item_id,
            "name": display_name,
            "category": "logging",
            "description": f"A freshly planted {species.capitalize()} sapling rooted firmly in homestead soil, free of burlap wrapping.",
            "icon": icon_name,
            "properties": {
                "weight_kg": 2.5,
                "max_stack_size": 1,
                "base_value": 15.0,
                "is_consumable": False,
                "footprint": "1x1"
            },
            "models": [
                {
                    "file": mtl_name,
                    "format": "mtl"
                },
                {
                    "file": obj_name,
                    "format": "obj",
                    "dimensions_cm": {
                        "x": bounds["width_x_cm"],
                        "y": bounds["depth_y_cm"],
                        "z": bounds["height_z_cm"]
                    },
                    "dimensions_m": {
                        "x": bounds["width_x_m"],
                        "y": bounds["depth_y_m"],
                        "z": bounds["height_z_m"]
                    },
                    "vertices": bounds["vertices"],
                    "faces": bounds["faces"],
                    "bounding_box": {
                        "min": [bounds["bounds"][0], bounds["bounds"][2], bounds["bounds"][4]],
                        "max": [bounds["bounds"][1], bounds["bounds"][3], bounds["bounds"][5]]
                    }
                }
            ],
            "utilities": {
                "water": { "metric": "Requires 2.0 L/day soil moisture during early root establishment", "details": "Requires 2.0 L/day soil moisture" },
                "electricity": { "metric": "None (passive / unpowered)", "details": "None (passive / unpowered)" },
                "sewage": { "metric": "None (no waste discharge)", "details": "None (no waste discharge)" },
                "battery": { "metric": "None (no internal battery)", "details": "None (no internal battery)" },
                "internet": { "metric": "None (offline / non-networked)", "details": "None (offline / non-networked)" }
            },
            "growth": {
                "is_growable": True,
                "growth_type": "tree",
                "species": species,
                "max_age": 100 if species not in ["apple", "poplar", "willow"] else (80 if species != "willow" else 90),
                "time_unit": "days",
                "total_stages": 4,
                "current_stage": {
                    "stage": 1,
                    "name": "sapling",
                    "age_min": 0,
                    "age_max": 15
                },
                "stages": [
                    { "stage": 1, "name": "sapling", "item_id": item_id, "age_min": 0, "age_max": 15 },
                    { "stage": 2, "name": "small", "item_id": f"tree_{species}_small", "age_min": 15, "age_max": 40 },
                    { "stage": 3, "name": "medium", "item_id": f"tree_{species}_medium", "age_min": 40, "age_max": 75 },
                    { "stage": 4, "name": "large (mature)", "item_id": f"tree_{species}_large" if species != "pine" and species != "birch" else f"tree_{species}_tall", "age_min": 75, "age_max": 100 }
                ]
            },
            "plugin_metadata": {
                "version": "1.0.0",
                "author": "Homesteader Core",
                "compatible_api": "v1"
            }
        }
        with open(os.path.join(item_dir, f"{item_id}.json"), "w", encoding="utf-8") as jf:
            json.dump(manifest, jf, indent=2)
            
        # Human-readable README.md
        readme = [
            f"# {display_name} (`{item_id}`)\n",
            f"![{display_name} Icon]({icon_name})\n",
            "## Overview",
            "- **Category**: `logging`",
            f"- **Item Identifier**: `{item_id}`",
            "- **Footprint**: `1x1`",
            "- **Max Stack Size**: 1",
            "- **Weight**: 2.5 kg",
            "- **Base Economic Value**: $15.0",
            "- **Consumable**: False\n",
            "## Description",
            f"A young {species.capitalize()} tree sapling planted firmly into the ground with natural root flare and bare stem (free of nursery burlap wrapping).\n",
            "## Growth & Lifecycle (Stage 1 of 4)",
            f"- **Growth Type**: `tree` (`{species}`)",
            f"- **Stage 1 (Current)**: `0 – 15 days` (Planted Sapling)",
            f"- **Stage 2**: `15 – 40 days` (`tree_{species}_small`)",
            f"- **Stage 3**: `40 – 75 days` (`tree_{species}_medium`)",
            f"- **Stage 4**: `75 – 100 days` (`tree_{species}_large` / mature)\n",
            "## 3D Model & Mesh Specifications",
            f"- **Physical Dimensions (X × Y × Z)**: `{bounds['width_x_cm']} cm × {bounds['depth_y_cm']} cm × {bounds['height_z_cm']} cm` (`{bounds['width_x_m']}m × {bounds['depth_y_m']}m × {bounds['height_z_m']}m`)",
            f"- **Mesh Complexity**: {bounds['vertices']} vertices, {bounds['faces']} polygon faces",
            "- **Shading Aesthetic**: 3D Low-Poly Faceted, Metric Scale (cm), Ground-Aligned Pivot ($Z_{min} = 0$).\n",
            "## Asset Files & Links",
            f"- **Plugin Manifest (JSON)**: [{item_id}.json]({item_id}.json)",
            f"- **Icon (PNG)**: [{icon_name}]({icon_name})",
            f"- **3D Mesh (OBJ)**: [{obj_name}]({obj_name})",
            f"- **Material (MTL)**: [{mtl_name}]({mtl_name})\n"
        ]
        with open(os.path.join(item_dir, "README.md"), "w", encoding="utf-8") as rf:
            rf.write("\n".join(readme))
            
        created_items.append((item_id, display_name))

    # 2. Generate Multi-Age Tree Stumps (21: 7 species x 3 ages)
    for sp_id, sp_name, bark_c, ring_c, core_c, is_birch in STUMP_SPECIES:
        for age in ["small", "medium", "large"]:
            item_id = f"stump_{sp_id}_{age}"
            display_name = f"{sp_name} Tree Stump ({age.capitalize()})"
            print(f"Generating stump: {item_id}...")
            
            item_dir = os.path.join(ASSETS_DIR, item_id)
            os.makedirs(item_dir, exist_ok=True)
            
            mesh = build_tree_stump(sp_id, age, bark_c, ring_c, core_c, is_birch)
            mesh.ground_align()
            
            obj_name = f"SM_Stump_{sp_id.capitalize()}_{age.capitalize()}.obj"
            mtl_name = f"SM_Stump_{sp_id.capitalize()}_{age.capitalize()}.mtl"
            obj_path = os.path.join(item_dir, obj_name)
            mtl_path = os.path.join(item_dir, mtl_name)
            mesh.save_obj_and_mtl(obj_path, mtl_path)
            
            icon_name = f"{item_id}.png"
            icon_path = os.path.join(item_dir, icon_name)
            icon_img = render_mesh_to_icon(mesh, output_size=128, max_dim=96, pitch_deg=35.0, yaw_deg=315.0)
            icon_img.save(icon_path, "PNG")
            
            bounds = mesh.compute_bounds()
            
            weight_val = 15.0 if age == "small" else (45.0 if age == "medium" else 120.0)
            val_val = 2.0 if age == "small" else (5.0 if age == "medium" else 12.0)
            
            manifest = {
                "$schema": "https://homesteader.game/schemas/item_v1.json",
                "id": item_id,
                "name": display_name,
                "category": "logging",
                "description": f"The remaining cut stump of a {age} {sp_name} tree, with visible bark and annular growth rings.",
                "icon": icon_name,
                "properties": {
                    "weight_kg": weight_val,
                    "max_stack_size": 1,
                    "base_value": val_val,
                    "is_consumable": False,
                    "footprint": "1x1" if age == "small" else ("2x2" if age == "medium" else "3x3")
                },
                "models": [
                    {
                        "file": mtl_name,
                        "format": "mtl"
                    },
                    {
                        "file": obj_name,
                        "format": "obj",
                        "dimensions_cm": {
                            "x": bounds["width_x_cm"],
                            "y": bounds["depth_y_cm"],
                            "z": bounds["height_z_cm"]
                        },
                        "dimensions_m": {
                            "x": bounds["width_x_m"],
                            "y": bounds["depth_y_m"],
                            "z": bounds["height_z_m"]
                        },
                        "vertices": bounds["vertices"],
                        "faces": bounds["faces"],
                        "bounding_box": {
                            "min": [bounds["bounds"][0], bounds["bounds"][2], bounds["bounds"][4]],
                            "max": [bounds["bounds"][1], bounds["bounds"][3], bounds["bounds"][5]]
                        }
                    }
                ],
                "utilities": {
                    "water": { "metric": "None (unplumbed / dry)", "details": "None (unplumbed / dry)" },
                    "electricity": { "metric": "None (passive / unpowered)", "details": "None (passive / unpowered)" },
                    "sewage": { "metric": "None (no waste discharge)", "details": "None (no waste discharge)" },
                    "battery": { "metric": "None (no internal battery)", "details": "None (no internal battery)" },
                    "internet": { "metric": "None (offline / non-networked)", "details": "None (offline / non-networked)" }
                },
                "growth": {
                    "is_growable": False,
                    "growth_type": None,
                    "species": sp_id,
                    "max_age": None,
                    "time_unit": None,
                    "total_stages": 0,
                    "current_stage": None,
                    "stages": []
                },
                "plugin_metadata": {
                    "version": "1.0.0",
                    "author": "Homesteader Core",
                    "compatible_api": "v1"
                }
            }
            with open(os.path.join(item_dir, f"{item_id}.json"), "w", encoding="utf-8") as jf:
                json.dump(manifest, jf, indent=2)
                
            readme = [
                f"# {display_name} (`{item_id}`)\n",
                f"![{display_name} Icon]({icon_name})\n",
                "## Overview",
                "- **Category**: `logging`",
                f"- **Item Identifier**: `{item_id}`",
                f"- **Footprint**: `{manifest['properties']['footprint']}`",
                "- **Max Stack Size**: 1",
                f"- **Weight**: {weight_val} kg",
                f"- **Base Economic Value**: ${val_val}",
                "- **Consumable**: False\n",
                "## Description",
                f"The remaining ground-anchored cut stump of a {age} {sp_name} timber tree. Can be excavated with a backhoe, split with wedges for kindling/root wood, or ground down with a stump grinder.\n",
                "## 3D Model & Mesh Specifications",
                f"- **Physical Dimensions (X × Y × Z)**: `{bounds['width_x_cm']} cm × {bounds['depth_y_cm']} cm × {bounds['height_z_cm']} cm` (`{bounds['width_x_m']}m × {bounds['depth_y_m']}m × {bounds['height_z_m']}m`)",
                f"- **Mesh Complexity**: {bounds['vertices']} vertices, {bounds['faces']} polygon faces",
                f"- **Annular Growth Rings**: Concentric wood grain (`Wood_Rings` and `Wood_Core`).",
                "- **Shading Aesthetic**: 3D Low-Poly Faceted, Metric Scale (cm), Ground-Aligned Pivot ($Z_{min} = 0$).\n",
                "## Asset Files & Links",
                f"- **Plugin Manifest (JSON)**: [{item_id}.json]({item_id}.json)",
                f"- **Icon (PNG)**: [{icon_name}]({icon_name})",
                f"- **3D Mesh (OBJ)**: [{obj_name}]({obj_name})",
                f"- **Material (MTL)**: [{mtl_name}]({mtl_name})\n"
            ]
            with open(os.path.join(item_dir, "README.md"), "w", encoding="utf-8") as rf:
                rf.write("\n".join(readme))
                
            created_items.append((item_id, display_name))
            
    print(f"\n>>> SUCCESSFULLY GENERATED {len(created_items)} NEW ASSETS IN {ASSETS_DIR} <<<")

if __name__ == "__main__":
    main()

