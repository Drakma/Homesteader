#!/usr/bin/env python3
"""
Homesteader Props, Materials, Logging, Workshop & Camp 3D Asset Generator
========================================================================
Generates 23 world models (.obj + .mtl) and matching 128x128 preview icons:
- Logging & Fuel (5 models)
- Building Supplies & Materials (7 models)
- Workshop Tools (5 models)
- Waterfront & Camping (6 models)

Grid Standards:
- 1 grid tile = 1m x 1m = 100 UU x 100 UU = 512px texture
- Ground aligned pivot (Z_min = 0.0)
- Watertight 360-degree geometry (rotatable by 90/180/270 deg)
- Dual workspace sync: assets/ & Homesteader/Content/Homesteader/
"""

import os
import sys
import math
import shutil
from PIL import Image, ImageDraw

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

# Directories
CAT_DIRS = {
    "logging": {
        "hud_models": os.path.join(PROJECT_ROOT, "HUD", "assets", "logging", "models"),
        "hud_icons":  os.path.join(PROJECT_ROOT, "HUD", "assets", "logging", "icons"),
        "ue5_models": os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "Assets", "Logging", "Meshes"),
        "ue5_icons":  os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "UI", "Icons", "logging"),
    },
    "building": {
        "hud_models": os.path.join(PROJECT_ROOT, "HUD", "assets", "building", "models"),
        "hud_icons":  os.path.join(PROJECT_ROOT, "HUD", "assets", "building", "icons"),
        "ue5_models": os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "Assets", "Building", "Meshes"),
        "ue5_icons":  os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "UI", "Icons", "building"),
    },
    "tools": {
        "hud_models": os.path.join(PROJECT_ROOT, "HUD", "assets", "tools", "models"),
        "hud_icons":  os.path.join(PROJECT_ROOT, "HUD", "assets", "tools", "icons"),
        "ue5_models": os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "Assets", "Tools", "Meshes"),
        "ue5_icons":  os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "UI", "Icons", "tools"),
    },
    "fishing": {
        "hud_models": os.path.join(PROJECT_ROOT, "HUD", "assets", "fishing", "models"),
        "hud_icons":  os.path.join(PROJECT_ROOT, "HUD", "assets", "fishing", "icons"),
        "ue5_models": os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "Assets", "Fishing", "Meshes"),
        "ue5_icons":  os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "UI", "Icons", "fishing"),
    }
}

for cat, paths in CAT_DIRS.items():
    for p in paths.values():
        os.makedirs(p, exist_ok=True)

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
        self.vertices = []
        self.normals = []
        self.uvs = []
        self.faces = []
        self.materials = {}

    def add_material(self, name, r, g, b):
        self.materials[name] = (r, g, b)

    def add_triangle(self, v0, v1, v2, uv0=(0,0), uv1=(1,0), uv2=(0.5,1), mat="default"):
        edge1 = v1 - v0
        edge2 = v2 - v0
        n = edge1.cross(edge2).normalized()
        base_v = len(self.vertices) + 1
        base_vt = len(self.uvs) + 1
        base_vn = len(self.normals) + 1

        self.vertices.extend([v0, v1, v2])
        self.uvs.extend([uv0, uv1, uv2])
        self.normals.extend([n, n, n])

        self.faces.append((
            [(base_v, base_vt, base_vn),
             (base_v+1, base_vt+1, base_vn+1),
             (base_v+2, base_vt+2, base_vn+2)],
            mat
        ))

    def add_quad(self, v0, v1, v2, v3, mat="default"):
        self.add_triangle(v0, v1, v2, (0,0), (1,0), (1,1), mat=mat)
        self.add_triangle(v0, v2, v3, (0,0), (1,1), (0,1), mat=mat)

    def add_box(self, x0, y0, z0, dx, dy, dz, mat="default"):
        p0 = Vec3(x0, y0, z0)
        p1 = Vec3(x0 + dx, y0, z0)
        p2 = Vec3(x0 + dx, y0 + dy, z0)
        p3 = Vec3(x0, y0 + dy, z0)
        p4 = Vec3(x0, y0, z0 + dz)
        p5 = Vec3(x0 + dx, y0, z0 + dz)
        p6 = Vec3(x0 + dx, y0 + dy, z0 + dz)
        p7 = Vec3(x0, y0 + dy, z0 + dz)

        self.add_quad(p0, p3, p2, p1, mat=mat) # Bottom
        self.add_quad(p4, p5, p6, p7, mat=mat) # Top
        self.add_quad(p0, p1, p5, p4, mat=mat) # South (-Y)
        self.add_quad(p1, p2, p6, p5, mat=mat) # East (+X)
        self.add_quad(p2, p3, p7, p6, mat=mat) # North (+Y)
        self.add_quad(p3, p0, p4, p7, mat=mat) # West (-X)

    def add_cylinder(self, r, h, z0=0.0, segs=12, mat="default", c=(0,0)):
        cx, cy = c
        ring_bot = []
        ring_top = []
        for i in range(segs):
            ang = i * 2.0 * math.pi / segs
            vx = cx + r * math.cos(ang)
            vy = cy + r * math.sin(ang)
            ring_bot.append(Vec3(vx, vy, z0))
            ring_top.append(Vec3(vx, vy, z0 + h))

        c_bot = Vec3(cx, cy, z0)
        c_top = Vec3(cx, cy, z0 + h)

        for i in range(segs):
            nxt = (i + 1) % segs
            self.add_quad(ring_bot[i], ring_bot[nxt], ring_top[nxt], ring_top[i], mat=mat)
            self.add_triangle(c_bot, ring_bot[nxt], ring_bot[i], mat=mat)
            self.add_triangle(c_top, ring_top[i], ring_top[nxt], mat=mat)

    def add_horizontal_cylinder(self, r, length, c=(0,0,0), axis="y", segs=12, mat="default"):
        cx, cy, cz = c
        half = length * 0.5
        ring_a = []
        ring_b = []
        if axis == "y":
            for i in range(segs):
                ang = i * 2.0 * math.pi / segs
                vx = cx + r * math.cos(ang)
                vz = cz + r * math.sin(ang)
                ring_a.append(Vec3(vx, cy - half, vz))
                ring_b.append(Vec3(vx, cy + half, vz))
            c_a = Vec3(cx, cy - half, cz)
            c_b = Vec3(cx, cy + half, cz)
            for i in range(segs):
                nxt = (i + 1) % segs
                self.add_quad(ring_a[i], ring_b[i], ring_b[nxt], ring_a[nxt], mat=mat)
                self.add_triangle(c_a, ring_a[nxt], ring_a[i], mat=mat)
                self.add_triangle(c_b, ring_b[i], ring_b[nxt], mat=mat)
        elif axis == "x":
            for i in range(segs):
                ang = i * 2.0 * math.pi / segs
                vy = cy + r * math.cos(ang)
                vz = cz + r * math.sin(ang)
                ring_a.append(Vec3(cx - half, vy, vz))
                ring_b.append(Vec3(cx + half, vy, vz))
            c_a = Vec3(cx - half, cy, cz)
            c_b = Vec3(cx + half, cy, cz)
            for i in range(segs):
                nxt = (i + 1) % segs
                self.add_quad(ring_a[i], ring_a[nxt], ring_b[nxt], ring_b[i], mat=mat)
                self.add_triangle(c_a, ring_a[i], ring_a[nxt], mat=mat)
                self.add_triangle(c_b, ring_b[nxt], ring_b[i], mat=mat)

    def add_sphere(self, r, c=(0,0,0), segs_lat=6, segs_lon=10, mat="default"):
        cx, cy, cz = c
        for i in range(segs_lat):
            lat0 = math.pi * (-0.5 + float(i) / segs_lat)
            z0 = cz + r * math.sin(lat0)
            zr0 = r * math.cos(lat0)

            lat1 = math.pi * (-0.5 + float(i + 1) / segs_lat)
            z1 = cz + r * math.sin(lat1)
            zr1 = r * math.cos(lat1)

            for j in range(segs_lon):
                lon0 = 2 * math.pi * float(j) / segs_lon
                lon1 = 2 * math.pi * float(j + 1) / segs_lon

                p0 = Vec3(cx + zr0 * math.cos(lon0), cy + zr0 * math.sin(lon0), z0)
                p1 = Vec3(cx + zr0 * math.cos(lon1), cy + zr0 * math.sin(lon1), z0)
                p2 = Vec3(cx + zr1 * math.cos(lon1), cy + zr1 * math.sin(lon1), z1)
                p3 = Vec3(cx + zr1 * math.cos(lon0), cy + zr1 * math.sin(lon0), z1)

                if i == 0:
                    self.add_triangle(p0, p1, p2, mat=mat)
                elif i == segs_lat - 1:
                    self.add_triangle(p0, p2, p3, mat=mat)
                else:
                    self.add_quad(p0, p1, p2, p3, mat=mat)

    def add_wedge(self, x0, y0, z0, dx, dy, dz, slope_axis="x", mat="default"):
        """Triangular wedge. For firewood or chocks."""
        if slope_axis == "x":
            # Wedge slopes up along +X
            p0 = Vec3(x0, y0, z0)
            p1 = Vec3(x0 + dx, y0, z0)
            p2 = Vec3(x0 + dx, y0 + dy, z0)
            p3 = Vec3(x0, y0 + dy, z0)
            p4 = Vec3(x0 + dx, y0, z0 + dz)
            p5 = Vec3(x0 + dx, y0 + dy, z0 + dz)

            self.add_quad(p0, p3, p2, p1, mat=mat) # base
            self.add_quad(p1, p2, p5, p4, mat=mat) # vertical back
            self.add_quad(p0, p1, p4, p0, mat=mat) # front triangular slope
            self.add_triangle(p0, p4, p1, mat=mat) # side 1
            self.add_triangle(p3, p2, p5, mat=mat) # side 2
            self.add_quad(p0, p4, p5, p3, mat=mat) # sloped face
        elif slope_axis == "z":
            # Firewood log wedge with arc-like shape (triangular prism along Y)
            p0 = Vec3(x0, y0, z0)
            p1 = Vec3(x0 + dx, y0, z0)
            p2 = Vec3(x0 + dx*0.5, y0, z0 + dz)
            p3 = Vec3(x0, y0 + dy, z0)
            p4 = Vec3(x0 + dx, y0 + dy, z0)
            p5 = Vec3(x0 + dx*0.5, y0 + dy, z0 + dz)

            self.add_triangle(p0, p1, p2, mat=mat) # front
            self.add_triangle(p3, p5, p4, mat=mat) # back
            self.add_quad(p0, p3, p4, p1, mat=mat) # bottom
            self.add_quad(p0, p2, p5, p3, mat=mat) # left slope
            self.add_quad(p1, p4, p5, p2, mat=mat) # right slope

    def ground_align(self):
        if not self.vertices: return
        min_z = min(v.z for v in self.vertices)
        offset = Vec3(0, 0, -min_z)
        self.vertices = [v + offset for v in self.vertices]

    def save_obj(self, obj_path, mtl_path):
        mtl_filename = os.path.basename(mtl_path)
        with open(obj_path, "w", encoding="utf-8") as f:
            f.write(f"# Homesteader 3D World Model\nmtllib {mtl_filename}\no {self.name}\n\n")
            for v in self.vertices: f.write(f"v {v.x:.4f} {v.y:.4f} {v.z:.4f}\n")
            for vt in self.uvs: f.write(f"vt {vt[0]:.4f} {vt[1]:.4f}\n")
            for vn in self.normals: f.write(f"vn {vn.x:.4f} {vn.y:.4f} {vn.z:.4f}\n")
            cur_mat = None
            for face_verts, mat in self.faces:
                if mat != cur_mat:
                    f.write(f"usemtl {mat}\ns 1\n")
                    cur_mat = mat
                f.write("f " + " ".join([f"{v}/{vt}/{vn}" for v, vt, vn in face_verts]) + "\n")

        with open(mtl_path, "w", encoding="utf-8") as f:
            f.write("# Material Definition\n\n")
            for mat_name, (r, g, b) in self.materials.items():
                f.write(f"newmtl {mat_name}\n")
                f.write(f"Ka {r*0.4:.4f} {g*0.4:.4f} {b*0.4:.4f}\n")
                f.write(f"Kd {r:.4f} {g:.4f} {b:.4f}\n")
                f.write(f"Ks 0.15 0.15 0.15\nNs 16.0\nd 1.0\nillum 2\n\n")

# -----------------------------------------------------------------------------
# 3D Icon Software Rasterizer
# -----------------------------------------------------------------------------
def render_icon(mesh, output_size=128, max_dim=96):
    mesh.ground_align()
    pitch = math.radians(30.0)
    yaw = math.radians(315.0)

    E_x = math.cos(pitch) * math.cos(yaw)
    E_y = math.cos(pitch) * math.sin(yaw)
    E_z = math.sin(pitch)

    L = Vec3(-E_x, -E_y, -E_z)
    R = Vec3(0.7071, 0.7071, 0.0)
    U = Vec3(-0.3536, 0.3536, 0.8660)

    # Key light: Top-left front
    key_dir = Vec3(-0.55, -0.45, 0.70).normalized()
    fill_dir = Vec3(0.60, 0.30, 0.40).normalized()

    proj_pts = []
    for v in mesh.vertices:
        u = v.dot(R)
        w = v.dot(U)
        d = v.dot(L)
        proj_pts.append((u, w, d))

    min_u = min(p[0] for p in proj_pts)
    max_u = max(p[0] for p in proj_pts)
    min_w = min(p[1] for p in proj_pts)
    max_w = max(p[1] for p in proj_pts)

    span_u = max(1e-4, max_u - min_u)
    span_w = max(1e-4, max_w - min_w)
    scale = max_dim / max(span_u, span_w)

    mid_u = 0.5 * (min_u + max_u)
    mid_w = 0.5 * (min_w + max_w)
    cx = output_size * 0.5
    cy = output_size * 0.5

    # Project to screen coordinates
    screen_pts = []
    for u, w, d in proj_pts:
        sx = cx + (u - mid_u) * scale
        sy = cy - (w - mid_w) * scale
        screen_pts.append((sx, sy, d))

    img = Image.new("RGBA", (output_size, output_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    face_data = []
    for face_verts, mat in mesh.faces:
        idx0 = face_verts[0][0] - 1
        idx1 = face_verts[1][0] - 1
        idx2 = face_verts[2][0] - 1

        p0 = screen_pts[idx0]
        p1 = screen_pts[idx1]
        p2 = screen_pts[idx2]

        # 2D cross product for backface culling
        cross2d = (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0])
        if cross2d >= 0:
            continue

        avg_depth = (p0[2] + p1[2] + p2[2]) / 3.0

        v0 = mesh.vertices[idx0]
        v1 = mesh.vertices[idx1]
        v2 = mesh.vertices[idx2]
        face_norm = (v1 - v0).cross(v2 - v0).normalized()

        kd = max(0.0, face_norm.dot(key_dir))
        k_fill = max(0.0, face_norm.dot(fill_dir))
        ambient = 0.32
        light = min(1.0, ambient + 0.52 * kd + 0.20 * k_fill)

        base_color = mesh.materials.get(mat, (0.7, 0.7, 0.7))
        r = int(min(255, max(0, base_color[0] * light * 255)))
        g = int(min(255, max(0, base_color[1] * light * 255)))
        b = int(min(255, max(0, base_color[2] * light * 255)))

        face_data.append((avg_depth, [(p0[0], p0[1]), (p1[0], p1[1]), (p2[0], p2[1])], (r, g, b, 255)))

    # Sort faces back to front (Painter's algorithm)
    face_data.sort(key=lambda x: x[0], reverse=True)

    for _, poly, color in face_data:
        draw.polygon(poly, fill=color)

    return img

# =============================================================================
# 1. LOGGING & FUEL (5 MODELS)
# =============================================================================

def build_log_pile_large():
    """SM_Log_Pile_Large (120x240x110cm): Stack of 10 large logs in pyramid with side chocks."""
    m = Mesh("SM_Log_Pile_Large")
    m.add_material("log_bark", 0.38, 0.26, 0.16)
    m.add_material("log_end", 0.78, 0.68, 0.48)
    m.add_material("chock_wood", 0.48, 0.36, 0.22)

    # 10 logs along Y axis (length 220cm):
    # Bottom row: 4 logs at z=14cm, x = -42, -14, +14, +42
    # 2nd row: 3 logs at z=38cm, x = -28, 0, +28
    # 3rd row: 2 logs at z=62cm, x = -14, +14
    # Top row: 1 log at z=86cm, x = 0
    r = 13.0
    length = 220.0
    layers = [
        [(-42, 14), (-14, 14), (14, 14), (42, 14)],
        [(-28, 38), (0, 38), (28, 38)],
        [(-14, 62), (14, 62)],
        [(0, 86)]
    ]
    for layer in layers:
        for x, z in layer:
            m.add_horizontal_cylinder(r, length, c=(x, 0, z), axis="y", segs=10, mat="log_bark")
            # Cut ends
            m.add_cylinder(r - 0.5, 0.5, z0=z, segs=10, mat="log_end", c=(x, 0))

    # Support side stakes (4 vertical stakes pounded into ground)
    for sx in [-58, 58]:
        for sy in [-70, 70]:
            m.add_box(sx - 4, sy - 4, 0, 8, 8, 90, mat="chock_wood")
    # Ground wedge chocks
    m.add_box(-56, -90, 0, 112, 12, 10, mat="chock_wood")
    m.add_box(-56, 78, 0, 112, 12, 10, mat="chock_wood")
    return m

def build_log_pile_medium():
    """SM_Log_Pile_Medium (90x160x80cm): 6 cut logs stacked between stakes."""
    m = Mesh("SM_Log_Pile_Medium")
    m.add_material("log_bark", 0.35, 0.24, 0.15)
    m.add_material("log_end", 0.76, 0.65, 0.44)
    m.add_material("chock_wood", 0.46, 0.34, 0.20)

    # 6 logs along Y axis (length 150cm, r=12):
    # Bottom: 3 logs at x=-24, 0, +24, z=13
    # Mid: 2 logs at x=-12, +12, z=35
    # Top: 1 log at x=0, z=57
    r = 12.0
    length = 150.0
    layers = [
        [(-24, 13), (0, 13), (24, 13)],
        [(-12, 35), (12, 35)],
        [(0, 57)]
    ]
    for layer in layers:
        for x, z in layer:
            m.add_horizontal_cylinder(r, length, c=(x, 0, z), axis="y", segs=10, mat="log_bark")

    # 4 corner stakes
    for sx in [-38, 38]:
        for sy in [-50, 50]:
            m.add_box(sx - 3, sy - 3, 0, 6, 6, 65, mat="chock_wood")
    return m

def build_firewood_rack_cord():
    """SM_Firewood_Rack_Cord (50x240x120cm): Heavy steel rack stacked full of split firewood."""
    m = Mesh("SM_Firewood_Rack_Cord")
    m.add_material("frame_steel", 0.18, 0.18, 0.20)
    m.add_material("wood_split", 0.82, 0.72, 0.50)
    m.add_material("wood_bark", 0.32, 0.22, 0.14)

    # Tubular steel frame:
    # 2 bottom runners along Y (length 230cm)
    m.add_box(-20, -115, 6, 6, 230, 6, mat="frame_steel")
    m.add_box(14, -115, 6, 6, 230, 6, mat="frame_steel")
    # 4 support feet lifting frame off ground
    for fx in [-20, 14]:
        for fy in [-110, -35, 35, 105]:
            m.add_box(fx, fy, 0, 6, 8, 6, mat="frame_steel")
    # 4 vertical end posts
    for ex in [-20, 14]:
        for ey in [-115, 109]:
            m.add_box(ex, ey, 6, 6, 6, 110, mat="frame_steel")
    # Cross bars at top ends
    m.add_box(-20, -115, 110, 40, 6, 6, mat="frame_steel")
    m.add_box(-20, 109, 110, 40, 6, 6, mat="frame_steel")

    # Stack of split firewood wedges (length 40cm along X):
    # Multiple layers along Y and Z
    for iz in range(5):
        z_pos = 14 + iz * 18
        for iy in range(11):
            y_pos = -100 + iy * 19
            mat = "wood_split" if (iz + iy) % 2 == 0 else "wood_bark"
            m.add_box(-18, y_pos, z_pos, 36, 16, 15, mat=mat)
    return m

def build_firewood_bundle_wrapped():
    """SM_Firewood_Bundle_Wrapped (35x45x35cm): Plastic shrink-wrapped firewood bundle with handle."""
    m = Mesh("SM_Firewood_Bundle_Wrapped")
    m.add_material("split_grain", 0.80, 0.70, 0.48)
    m.add_material("bark_surface", 0.34, 0.24, 0.15)
    m.add_material("shrink_wrap", 0.70, 0.82, 0.88)
    m.add_material("strap_handle", 0.15, 0.15, 0.15)

    # 6 split firewood pieces arranged in hexagonal bundle along Y (length 42cm)
    pieces = [
        (-10, 8, "split_grain"), (10, 8, "bark_surface"),
        (-14, 20, "bark_surface"), (0, 18, "split_grain"), (14, 20, "split_grain"),
        (0, 30, "bark_surface")
    ]
    for px, pz, pmat in pieces:
        m.add_box(px - 6, -21, pz - 6, 12, 42, 12, mat=pmat)

    # Shrink wrap outer band
    m.add_box(-21, -12, 1, 42, 24, 34, mat="shrink_wrap")
    # Polypropylene carry strap on top
    m.add_box(-12, -4, 35, 24, 8, 4, mat="strap_handle")
    m.add_box(-4, -4, 39, 8, 8, 6, mat="strap_handle")
    return m

def build_chopping_block_maul():
    """SM_Chopping_Block_Maul (55x55x65cm): Round oak stump with splitting maul embedded."""
    m = Mesh("SM_Chopping_Block_Maul")
    m.add_material("stump_bark", 0.36, 0.25, 0.16)
    m.add_material("stump_top", 0.75, 0.64, 0.45)
    m.add_material("maul_steel", 0.25, 0.26, 0.28)
    m.add_material("maul_handle", 0.78, 0.58, 0.32)

    # Heavy round tree trunk stump (diameter 52cm, height 48cm)
    m.add_cylinder(26.0, 47.0, z0=0.0, segs=14, mat="stump_bark")
    m.add_cylinder(25.0, 1.0, z0=47.0, segs=14, mat="stump_top")

    # Splitting maul embedded in stump top:
    # Steel head: wedge embedded in center top
    m.add_box(-3, -12, 44, 6, 24, 12, mat="maul_steel")
    m.add_box(-5, -6, 48, 10, 12, 10, mat="maul_steel")
    # Wood handle sticking out at ~30 deg angle along +X
    for step in range(10):
        sx = step * 3.5
        sz = 52 + step * 4.0
        m.add_box(sx - 2, -2, sz - 2, 4, 4, 6, mat="maul_handle")
    return m

# =============================================================================
# 2. BUILDING SUPPLIES & MATERIALS (7 MODELS)
# =============================================================================

def build_mat_lumber_stack_2x4():
    """SM_Mat_Lumber_Stack_2x4 (80x240x60cm): Banded stack of 2x4 framing lumber."""
    m = Mesh("SM_Mat_Lumber_Stack_2x4")
    m.add_material("spf_wood", 0.84, 0.74, 0.52)
    m.add_material("wood_end", 0.72, 0.60, 0.40)
    m.add_material("steel_strap", 0.15, 0.15, 0.15)
    m.add_material("skid_timber", 0.45, 0.32, 0.18)

    # 3 dunnage skids on ground (crosswise along X)
    for sy in [-95, 0, 95]:
        m.add_box(-38, sy - 4, 0, 76, 8, 8, mat="skid_timber")

    # Stack of dimensional 2x4 boards (80cm wide, 230cm long, 48cm high)
    # 8 layers of 8 boards
    m.add_box(-36, -115, 8, 72, 230, 46, mat="spf_wood")
    # Cut end stamps on front & back (+Y / -Y)
    m.add_box(-35, -116, 9, 70, 1, 44, mat="wood_end")
    m.add_box(-35, 115, 9, 70, 1, 44, mat="wood_end")

    # 2 black steel banding straps
    for band_y in [-60, 60]:
        m.add_box(-37, band_y - 2, 7, 74, 4, 48, mat="steel_strap")
    return m

def build_mat_plywood_stack():
    """SM_Mat_Plywood_Stack (120x240x40cm): CDX 4x8 plywood sheets on 4x4 runners."""
    m = Mesh("SM_Mat_Plywood_Stack")
    m.add_material("ply_face", 0.82, 0.72, 0.50)
    m.add_material("ply_edge", 0.55, 0.42, 0.28)
    m.add_material("skid_wood", 0.40, 0.30, 0.18)

    # 3 bottom 4x4 skids
    for sy in [-95, 0, 95]:
        m.add_box(-55, sy - 5, 0, 110, 10, 9, mat="skid_wood")

    # Plywood sheets block (115cm wide, 235cm long, 28cm high)
    m.add_box(-57, -117, 9, 114, 234, 28, mat="ply_edge")
    # Top face veneer sheet
    m.add_box(-57, -117, 36, 114, 234, 1, mat="ply_face")
    return m

def build_mat_pallet_wood():
    """SM_Mat_Pallet_Wood (100x120x15cm): Standard Euro/GMA warehouse wooden pallet."""
    m = Mesh("SM_Mat_Pallet_Wood")
    m.add_material("pallet_wood", 0.68, 0.54, 0.36)

    # 3 bottom runner boards (along Y, 120cm)
    for bx in [-45, 0, 45]:
        m.add_box(bx - 5, -58, 0, 10, 116, 2.5, mat="pallet_wood")

    # 9 stringer spacer blocks (3 along each runner)
    for bx in [-45, 0, 45]:
        for by in [-52, 0, 52]:
            m.add_box(bx - 4.5, by - 5, 2.5, 9, 10, 9, mat="pallet_wood")

    # 3 stringer boards across spacer blocks
    for bx in [-45, 0, 45]:
        m.add_box(bx - 4.5, -58, 11.5, 9, 116, 2.5, mat="pallet_wood")

    # 7 top deck boards (along X, 100cm long)
    for i in range(7):
        dy = -55 + i * 18.3
        m.add_box(-48, dy - 5, 14, 96, 10, 2.5, mat="pallet_wood")
    return m

def build_mat_cinder_blocks_stack():
    """SM_Mat_CinderBlocks_Stack (80x120x80cm): Concrete cinder blocks stacked on wooden pallet."""
    m = Mesh("SM_Mat_CinderBlocks_Stack")
    m.add_material("pallet_wood", 0.65, 0.52, 0.34)
    m.add_material("cinder_block", 0.62, 0.64, 0.65)
    m.add_material("block_hole", 0.22, 0.23, 0.24)

    # Pallet base
    m.add_box(-38, -58, 0, 76, 116, 12, mat="pallet_wood")

    # 3 tiers of concrete cinder blocks (each block 20x40x20cm):
    # Tier 1 & 3: 3 rows along Y
    # Tier 2: interleaved
    for tier in range(3):
        z_pos = 12 + tier * 20
        for ix in [-20, 20]:
            for iy in [-38, 0, 38]:
                m.add_box(ix - 17, iy - 17, z_pos, 34, 34, 18, mat="cinder_block")
                # Top cavity holes (2 hollow core cells)
                m.add_box(ix - 12, iy - 12, z_pos + 17, 10, 24, 2, mat="block_hole")
                m.add_box(ix + 2, iy - 12, z_pos + 17, 10, 24, 2, mat="block_hole")
    return m

def build_mat_brick_pallet():
    """SM_Mat_Brick_Pallet (90x90x70cm): Clay red construction bricks strapped on pallet."""
    m = Mesh("SM_Mat_Brick_Pallet")
    m.add_material("pallet_wood", 0.65, 0.52, 0.34)
    m.add_material("clay_brick", 0.72, 0.28, 0.18)
    m.add_material("plastic_shroud", 0.85, 0.88, 0.90)
    m.add_material("band_yellow", 0.88, 0.78, 0.15)

    # Wooden pallet base
    m.add_box(-42, -42, 0, 84, 84, 12, mat="pallet_wood")

    # Brick cube block (76x76x54cm)
    m.add_box(-38, -38, 12, 76, 76, 52, mat="clay_brick")
    # Thin protective wrap with sheen
    m.add_box(-39, -39, 14, 78, 78, 48, mat="plastic_shroud")
    # Yellow strapping tape
    m.add_box(-40, -15, 12, 80, 4, 53, mat="band_yellow")
    m.add_box(-40, 15, 12, 80, 4, 53, mat="band_yellow")
    m.add_box(-15, -40, 12, 4, 80, 53, mat="band_yellow")
    m.add_box(15, -40, 12, 4, 80, 53, mat="band_yellow")
    return m

def build_mat_steel_drum_55gal():
    """SM_Mat_Steel_Drum_55gal (60x60x90cm): Industrial blue 55-gallon oil/fuel drum."""
    m = Mesh("SM_Mat_Steel_Drum_55gal")
    m.add_material("drum_blue", 0.12, 0.35, 0.65)
    m.add_material("drum_rim", 0.22, 0.25, 0.28)
    m.add_material("bung_zinc", 0.75, 0.75, 0.78)

    # Main cylindrical barrel (diameter 58cm, height 88cm)
    m.add_cylinder(28.0, 86.0, z0=2.0, segs=16, mat="drum_blue")
    # Bottom chime/rim
    m.add_cylinder(29.0, 4.0, z0=0.0, segs=16, mat="drum_rim")
    # Top chime/rim
    m.add_cylinder(29.0, 4.0, z0=86.0, segs=16, mat="drum_rim")
    # 2 rolling hoops around the waist
    m.add_cylinder(29.2, 3.0, z0=30.0, segs=16, mat="drum_blue")
    m.add_cylinder(29.2, 3.0, z0=58.0, segs=16, mat="drum_blue")
    # Top lid recessed surface
    m.add_cylinder(27.0, 1.0, z0=89.0, segs=14, mat="drum_blue")
    # 2" threaded bung plug
    m.add_cylinder(3.0, 2.0, z0=89.0, segs=8, mat="bung_zinc", c=(12, 0))
    # 3/4" vent bung plug
    m.add_cylinder(2.0, 2.0, z0=89.0, segs=8, mat="bung_zinc", c=(-12, 0))
    return m

def build_mat_propane_tank_500gal():
    """SM_Mat_PropaneTank_500gal (95x300x125cm): Horizontal torpedo LP gas propane tank."""
    m = Mesh("SM_Mat_PropaneTank_500gal")
    m.add_material("tank_white", 0.88, 0.89, 0.90)
    m.add_material("leg_steel", 0.24, 0.25, 0.28)
    m.add_material("hood_red", 0.78, 0.20, 0.18)
    m.add_material("brass_valve", 0.85, 0.72, 0.25)

    r = 46.0
    cyl_len = 200.0
    # Main horizontal cylinder along Y
    m.add_horizontal_cylinder(r, cyl_len, c=(0, 0, 62), axis="y", segs=14, mat="tank_white")
    # Front and rear spherical dome end caps
    m.add_sphere(r, c=(0, -cyl_len*0.5, 62), segs_lat=6, segs_lon=12, mat="tank_white")
    m.add_sphere(r, c=(0, cyl_len*0.5, 62), segs_lat=6, segs_lon=12, mat="tank_white")

    # 2 welded heavy steel saddle support legs
    for ly in [-65, 65]:
        m.add_box(-38, ly - 8, 0, 76, 16, 20, mat="leg_steel")
        # Concrete pad foot
        m.add_box(-42, ly - 12, 0, 84, 24, 4, mat="leg_steel")

    # Central service valve hood dome on top (+Z)
    m.add_box(-16, -18, 106, 32, 36, 16, mat="hood_red")
    # Brass regulator & fill fittings under hood
    m.add_cylinder(4.0, 8.0, z0=108.0, segs=8, mat="brass_valve", c=(0, 0))
    return m

# =============================================================================
# 3. WORKSHOP TOOLS (5 MODELS)
# =============================================================================

def build_tool_workbench_timber():
    """SM_Tool_Workbench_Timber (80x180x90cm): Woodworking workbench with vise & lower shelf."""
    m = Mesh("SM_Tool_Workbench_Timber")
    m.add_material("maple_top", 0.82, 0.68, 0.44)
    m.add_material("frame_wood", 0.58, 0.44, 0.28)
    m.add_material("vise_iron", 0.20, 0.22, 0.24)
    m.add_material("vise_screw", 0.75, 0.75, 0.78)

    # Thick laminated butcher-block maple top (80x176x9cm) at z=81cm
    m.add_box(-38, -86, 81, 76, 172, 9, mat="maple_top")

    # 4 sturdy 4x4 timber legs
    for lx in [-32, 24]:
        for ly in [-78, 70]:
            m.add_box(lx, ly, 0, 8, 8, 81, mat="frame_wood")

    # Lower stretchers and bottom tool shelf at z=18cm
    m.add_box(-30, -78, 18, 60, 156, 4, mat="frame_wood")
    # Upper leg apron rails
    m.add_box(-30, -78, 73, 60, 8, 8, mat="frame_wood")
    m.add_box(-30, 70, 73, 60, 8, 8, mat="frame_wood")
    m.add_box(-32, -78, 73, 8, 156, 8, mat="frame_wood")
    m.add_box(24, -78, 73, 8, 156, 8, mat="frame_wood")

    # Woodworking bench vise on front-left corner
    m.add_box(-44, -84, 75, 8, 26, 14, mat="vise_iron")
    m.add_cylinder(2.0, 16.0, z0=81.0, segs=8, mat="vise_screw", c=(-44, -71))
    return m

def build_tool_anvil_stump():
    """SM_Tool_Anvil_Stump (45x65x85cm): Blacksmith anvil on banded hardwood stump."""
    m = Mesh("SM_Tool_Anvil_Stump")
    m.add_material("stump_bark", 0.38, 0.28, 0.18)
    m.add_material("stump_top", 0.74, 0.62, 0.42)
    m.add_material("anvil_steel", 0.22, 0.23, 0.26)
    m.add_material("anvil_face", 0.65, 0.68, 0.72)
    m.add_material("band_steel", 0.16, 0.16, 0.18)

    # Large round hardwood stump block (diameter 44cm, height 50cm)
    m.add_cylinder(22.0, 48.0, z0=0.0, segs=14, mat="stump_bark")
    m.add_cylinder(21.0, 2.0, z0=48.0, segs=14, mat="stump_top")
    # Steel retention straps around stump
    m.add_cylinder(22.4, 4.0, z0=38.0, segs=14, mat="band_steel")
    m.add_cylinder(22.4, 4.0, z0=12.0, segs=14, mat="band_steel")

    # Cast steel blacksmith anvil on top (z=50 to 82cm, length 56cm along Y):
    # Anvil base foot
    m.add_box(-14, -22, 50, 28, 44, 8, mat="anvil_steel")
    # Anvil waist / waist pillar
    m.add_box(-8, -14, 58, 16, 28, 12, mat="anvil_steel")
    # Anvil body & flat working face
    m.add_box(-9, -18, 70, 18, 32, 11, mat="anvil_steel")
    # Top polished face plate
    m.add_box(-9, -16, 81, 18, 30, 1, mat="anvil_face")
    # Round horn tapering out along -Y
    for i in range(5):
        hy = -18 - i * 4.5
        hr = 7.0 - i * 1.1
        hz = 74.0 + i * 0.8
        m.add_sphere(hr, c=(0, hy, hz), segs_lat=4, segs_lon=8, mat="anvil_steel")
    # Square heel & hardy hole extending along +Y
    m.add_box(-8, 14, 70, 16, 12, 11, mat="anvil_steel")
    m.add_box(-3, 18, 80, 6, 6, 2, mat="band_steel") # Hardy hole cavity
    return m

def build_tool_cement_mixer_electric():
    """SM_Tool_CementMixer_Electric (85x120x135cm): Portable orange cement mixer on wheels."""
    m = Mesh("SM_Tool_CementMixer_Electric")
    m.add_material("mixer_orange", 0.90, 0.45, 0.10)
    m.add_material("frame_black", 0.18, 0.18, 0.20)
    m.add_material("motor_housing", 0.28, 0.30, 0.32)
    m.add_material("rubber_tire", 0.12, 0.12, 0.12)
    m.add_material("wheel_rim", 0.75, 0.75, 0.75)

    # Tubular A-frame stand:
    # Wheel axle at z=14cm along X
    m.add_box(-36, -35, 12, 72, 4, 4, mat="frame_black")
    # 2 rubber wheels on axle ends
    for wx in [-38, 34]:
        m.add_cylinder(13.0, 5.0, z0=2.0, segs=12, mat="rubber_tire", c=(wx, -35))
        m.add_cylinder(6.0, 5.2, z0=9.0, segs=8, mat="wheel_rim", c=(wx, -35))
    # Front support leg / skid
    m.add_box(-4, 38, 0, 8, 8, 45, mat="frame_black")
    m.add_box(-18, 38, 0, 36, 8, 4, mat="frame_black")

    # A-frame uprights to drum pivot at z=72cm
    m.add_box(-22, -35, 14, 6, 6, 62, mat="frame_black")
    m.add_box(16, -35, 14, 6, 6, 62, mat="frame_black")
    m.add_box(-22, -35, 74, 44, 6, 6, mat="frame_black")

    # Orange steel mixing drum (tilted barrel at ~35 deg):
    # Base cylinder of drum
    m.add_cylinder(28.0, 30.0, z0=65.0, segs=12, mat="mixer_orange", c=(0, -5))
    # Tapered conical cone top
    m.add_cylinder(20.0, 24.0, z0=95.0, segs=12, mat="mixer_orange", c=(0, 5))
    # Open drum rim lip
    m.add_cylinder(21.5, 3.0, z0=119.0, segs=12, mat="mixer_orange", c=(0, 5))

    # Electric motor housing box
    m.add_box(-12, -48, 55, 24, 16, 20, mat="motor_housing")
    # Tilt dump wheel handle on side
    m.add_cylinder(12.0, 2.0, z0=72.0, segs=10, mat="frame_black", c=(24, -5))
    return m

def build_tool_toolchest_rolling():
    """SM_Tool_ToolChest_Rolling (55x95x105cm): Red 6-drawer mechanic rolling cabinet."""
    m = Mesh("SM_Tool_ToolChest_Rolling")
    m.add_material("chest_red", 0.82, 0.16, 0.14)
    m.add_material("drawer_pull", 0.78, 0.80, 0.82)
    m.add_material("top_mat", 0.12, 0.12, 0.12)
    m.add_material("caster_steel", 0.20, 0.22, 0.24)
    m.add_material("handle_chrome", 0.75, 0.78, 0.80)

    # 4 heavy-duty caster wheels at bottom
    for cx in [-20, 20]:
        for cy in [-36, 36]:
            m.add_cylinder(5.0, 8.0, z0=0.0, segs=8, mat="caster_steel", c=(cx, cy))

    # Main red steel cabinet body (48x86x88cm) from z=8 to 96cm
    m.add_box(-24, -43, 8, 48, 86, 88, mat="chest_red")
    # Black rubberized worktop mat
    m.add_box(-23, -42, 96, 46, 84, 2, mat="top_mat")

    # 6 full-extension drawer fronts with aluminum pull handles (facing -X)
    drawer_heights = [10, 10, 12, 12, 16, 18]
    cur_z = 12
    for dh in drawer_heights:
        # Drawer gap border
        m.add_box(-24.5, -40, cur_z, 1, 80, dh - 2, mat="chest_red")
        # Aluminum trim handle
        m.add_box(-26.0, -36, cur_z + dh - 5, 2, 72, 2.5, mat="drawer_pull")
        cur_z += dh

    # Chrome side push handle on +Y end
    m.add_box(-4, 43, 80, 8, 12, 4, mat="handle_chrome")
    m.add_box(-20, 51, 80, 40, 4, 4, mat="handle_chrome")
    return m

def build_tool_sawhorse_pair():
    """SM_Tool_Sawhorse_Pair (60x95x75cm): Pair of wooden carpenters' sawhorses."""
    m = Mesh("SM_Tool_Sawhorse_Pair")
    m.add_material("pine_lumber", 0.80, 0.68, 0.44)
    m.add_material("gusset_ply", 0.65, 0.52, 0.32)

    # 2 identical sawhorses spaced 40cm apart along X
    for horse_x in [-18, 18]:
        # Top 2x6 rail (length 90cm along Y) at z=70cm
        m.add_box(horse_x - 3, -45, 68, 6, 90, 6, mat="pine_lumber")

        # 4 splayed A-frame legs
        for ly in [-38, 38]:
            # Left leg (-X)
            m.add_box(horse_x - 12, ly - 2.5, 0, 4, 5, 68, mat="pine_lumber")
            # Right leg (+X)
            m.add_box(horse_x + 8, ly - 2.5, 0, 4, 5, 68, mat="pine_lumber")
            # Plywood shelf / spreader gusset plate
            m.add_box(horse_x - 10, ly - 2, 28, 20, 4, 12, mat="gusset_ply")

        # Lower longitudinal stretcher board
        m.add_box(horse_x - 2, -38, 24, 4, 76, 4, mat="pine_lumber")
    return m

# =============================================================================
# 4. WATERFRONT & CAMPING (6 MODELS)
# =============================================================================

def build_water_dock_section_1x2m():
    """SM_Water_Dock_Section_1x2m (100x200x80cm): Modular cedar plank dock with cleats & pilings."""
    m = Mesh("SM_Water_Dock_Section_1x2m")
    m.add_material("cedar_plank", 0.76, 0.62, 0.42)
    m.add_material("fascia_wood", 0.55, 0.42, 0.28)
    m.add_material("piling_post", 0.38, 0.30, 0.20)
    m.add_material("cleat_alum", 0.72, 0.74, 0.76)

    # 4 round submerged timber pilings / posts at corners
    for px in [-44, 44]:
        for py in [-90, 90]:
            m.add_cylinder(5.0, 75.0, z0=0.0, segs=10, mat="piling_post", c=(px, py))

    # Perimeter fascia skirt frame (height 14cm) at z=60cm
    m.add_box(-48, -98, 60, 96, 5, 14, mat="fascia_wood")
    m.add_box(-48, 93, 60, 96, 5, 14, mat="fascia_wood")
    m.add_box(-48, -98, 60, 5, 196, 14, mat="fascia_wood")
    m.add_box(43, -98, 60, 5, 196, 14, mat="fascia_wood")

    # Cedar deck boards (crosswise along X, length 96cm, width 14cm) at z=74cm
    for i in range(13):
        by = -94 + i * 14.8
        m.add_box(-46, by, 74, 92, 13, 3, mat="cedar_plank")

    # 2 cast aluminum mooring cleats on outer edge (+X)
    for cy in [-55, 55]:
        m.add_box(40, cy - 8, 77, 6, 16, 4, mat="cleat_alum")
        m.add_box(38, cy - 14, 80, 8, 28, 3, mat="cleat_alum")
    return m

def build_water_rowboat_wood():
    """SM_Water_Rowboat_Wood (110x300x55cm): Classic 10ft cedar lapstrake wooden rowboat."""
    m = Mesh("SM_Water_Rowboat_Wood")
    m.add_material("hull_cedar", 0.78, 0.58, 0.35)
    m.add_material("interior_wood", 0.84, 0.70, 0.48)
    m.add_material("gunwale_trim", 0.45, 0.30, 0.16)
    m.add_material("oar_wood", 0.86, 0.76, 0.52)

    # Clinker/lapstrake hull shaped along Y (bow at +Y, stern at -Y):
    # Bottom flat keel plate
    m.add_box(-25, -130, 0, 50, 240, 4, mat="interior_wood")

    # Hull side segments (tapering to pointed bow at +Y=145)
    stations = [
        (-135, 42, 50),  # Flat stern transom
        (-70, 50, 52),   # Midships aft
        (0, 54, 52),     # Midships center
        (70, 48, 50),    # Midships forward
        (135, 20, 45),   # Bow shoulder
        (150, 4, 48)     # Bow stem post
    ]
    for i in range(len(stations) - 1):
        y0, w0, h0 = stations[i]
        y1, w1, h1 = stations[i+1]
        dy = y1 - y0

        # Left side panel
        m.add_quad(
            Vec3(-w0, y0, 4), Vec3(-w1, y1, 4),
            Vec3(-w1 - 4, y1, h1), Vec3(-w0 - 4, y0, h0),
            mat="hull_cedar"
        )
        # Right side panel
        m.add_quad(
            Vec3(w0 + 4, y0, h0), Vec3(w1 + 4, y1, h1),
            Vec3(w1, y1, 4), Vec3(w0, y0, 4),
            mat="hull_cedar"
        )

    # Transom stern board at -Y=-135
    m.add_box(-44, -137, 4, 88, 4, 48, mat="gunwale_trim")
    # Stem post at bow +Y=150
    m.add_box(-3, 147, 4, 6, 8, 48, mat="gunwale_trim")

    # 2 bench thwarts (seats):
    # Center rowing seat
    m.add_box(-46, -10, 26, 92, 22, 4, mat="interior_wood")
    # Stern passenger seat
    m.add_box(-40, -115, 26, 80, 20, 4, mat="interior_wood")

    # Pair of wooden oars resting inside across gunwales
    # Oar 1 (angled across boat)
    m.add_box(-42, -50, 44, 84, 4, 4, mat="oar_wood")
    m.add_box(-48, -52, 42, 12, 8, 2, mat="oar_wood") # blade
    # Oar 2
    m.add_box(-42, -20, 46, 84, 4, 4, mat="oar_wood")
    m.add_box(36, -22, 44, 12, 8, 2, mat="oar_wood") # blade
    return m

def build_camp_tent_canvas_wall():
    """SM_Camp_Tent_Canvas_Wall (240x300x210cm): Heavy canvas outfitter wall tent with chimney."""
    m = Mesh("SM_Camp_Tent_Canvas_Wall")
    m.add_material("canvas_khaki", 0.82, 0.76, 0.60)
    m.add_material("door_zipper", 0.35, 0.30, 0.22)
    m.add_material("stove_pipe", 0.22, 0.24, 0.26)
    m.add_material("frame_pole", 0.45, 0.35, 0.25)

    # Dimensions: X: +/-115 (width 230cm), Y: +/-145 (length 290cm)
    # Vertical side walls up to z=95cm:
    m.add_box(-115, -145, 0, 6, 290, 95, mat="canvas_khaki") # Left wall
    m.add_box(109, -145, 0, 6, 290, 95, mat="canvas_khaki")  # Right wall
    m.add_box(-115, 140, 0, 230, 6, 95, mat="canvas_khaki")  # Rear wall

    # Peaked gable roof: ridge along Y from y=-145 to +145 at z=205cm
    # Left roof sloped quad (subdivided 2x2 for clean rasterizer sorting)
    m.add_quad(Vec3(-115, -145, 95), Vec3(-115, 0, 95), Vec3(0, 0, 205), Vec3(0, -145, 205), mat="canvas_khaki")
    m.add_quad(Vec3(-115, 0, 95), Vec3(-115, 145, 95), Vec3(0, 145, 205), Vec3(0, 0, 205), mat="canvas_khaki")
    # Right roof sloped quad
    m.add_quad(Vec3(0, -145, 205), Vec3(0, 0, 205), Vec3(115, 0, 95), Vec3(115, -145, 95), mat="canvas_khaki")
    m.add_quad(Vec3(0, 0, 205), Vec3(0, 145, 205), Vec3(115, 145, 95), Vec3(115, 0, 95), mat="canvas_khaki")

    # Front gable triangle (at y=-145)
    m.add_triangle(Vec3(-115, -145, 95), Vec3(115, -145, 95), Vec3(0, -145, 205), mat="canvas_khaki")
    # Rear gable triangle (at y=+145)
    m.add_triangle(Vec3(115, 145, 95), Vec3(-115, 145, 95), Vec3(0, 145, 205), mat="canvas_khaki")

    # Front wall flaps with center zipper slit (y=-145)
    m.add_box(-115, -145, 0, 110, 4, 95, mat="canvas_khaki")
    m.add_box(5, -145, 0, 110, 4, 95, mat="canvas_khaki")
    m.add_box(-5, -146, 0, 10, 2, 95, mat="door_zipper")

    # Metal stovepipe flashing & chimney elbow on roof
    m.add_cylinder(6.0, 45.0, z0=170.0, segs=8, mat="stove_pipe", c=(45, -60))
    # Rain cap
    m.add_cylinder(9.0, 3.0, z0=215.0, segs=8, mat="stove_pipe", c=(45, -60))
    return m

def build_camp_tent_dome():
    """SM_Camp_Tent_Dome (200x200x130cm): Modern 2-person geodesic dome camping tent."""
    m = Mesh("SM_Camp_Tent_Dome")
    m.add_material("nylon_green", 0.22, 0.48, 0.28)
    m.add_material("nylon_orange", 0.90, 0.48, 0.12)
    m.add_material("tent_floor", 0.16, 0.18, 0.20)
    m.add_material("pole_black", 0.12, 0.12, 0.14)
    m.add_material("door_mesh", 0.28, 0.32, 0.34)

    # Bathtub floor base
    m.add_box(-95, -95, 0, 190, 190, 12, mat="tent_floor")

    # Geodesic dome structure: octagonal rings tapering up
    # Ring 1: z=12, r=92
    # Ring 2: z=60, r=80
    # Ring 3: z=100, r=55
    # Apex: z=125, r=10
    segs = 8
    rings = [
        (12, 92),
        (60, 80),
        (100, 55),
        (125, 12)
    ]
    ring_pts = []
    for rz, rr in rings:
        pts = []
        for i in range(segs):
            ang = i * 2.0 * math.pi / segs
            pts.append(Vec3(rr * math.cos(ang), rr * math.sin(ang), rz))
        ring_pts.append(pts)

    # Dome wall quads
    for level in range(len(rings) - 1):
        mat = "nylon_orange" if level == 1 else "nylon_green"
        for i in range(segs):
            nxt = (i + 1) % segs
            p0 = ring_pts[level][i]
            p1 = ring_pts[level][nxt]
            p2 = ring_pts[level+1][nxt]
            p3 = ring_pts[level+1][i]
            m.add_quad(p0, p1, p2, p3, mat=mat)

    # Top apex cap
    apex_center = Vec3(0, 0, 128)
    for i in range(segs):
        nxt = (i + 1) % segs
        m.add_triangle(ring_pts[-1][i], ring_pts[-1][nxt], apex_center, mat="nylon_orange")

    # Arched doorway vestibule on front (-Y)
    m.add_box(-30, -96, 12, 60, 4, 65, mat="door_mesh")

    # 2 crossed flexible pole ribs visible on outside
    # Diagonal 1: (-95, -95) to (95, 95)
    # Diagonal 2: (-95, 95) to (95, -95)
    for step in range(12):
        t = (step - 5.5) / 5.5
        pz = 126 * (1.0 - 0.75 * (t*t))
        pos1 = 92 * t
        m.add_sphere(3.0, c=(pos1, pos1, pz), segs_lat=3, segs_lon=6, mat="pole_black")
        m.add_sphere(3.0, c=(-pos1, pos1, pz), segs_lat=3, segs_lon=6, mat="pole_black")
    return m

def build_camp_campfire_ring():
    """SM_Camp_Campfire_Ring (80x80x25cm): Circular ring of fieldstones with glowing embers."""
    m = Mesh("SM_Camp_Campfire_Ring")
    m.add_material("stone_grey", 0.52, 0.50, 0.48)
    m.add_material("stone_dark", 0.38, 0.36, 0.34)
    m.add_material("ash_charcoal", 0.18, 0.17, 0.16)
    m.add_material("ember_glow", 0.95, 0.38, 0.08)
    m.add_material("log_charred", 0.28, 0.20, 0.12)

    # Central burnt ash & coal pit bed
    m.add_cylinder(32.0, 4.0, z0=0.0, segs=12, mat="ash_charcoal")
    # Glowing orange hot embers in center
    m.add_cylinder(16.0, 2.0, z0=4.0, segs=8, mat="ember_glow")

    # Ring of 12 natural boulders / stones (radius 36cm, stone size ~14cm)
    segs = 12
    for i in range(segs):
        ang = i * 2.0 * math.pi / segs
        sx = 35.0 * math.cos(ang)
        sy = 35.0 * math.sin(ang)
        mat = "stone_grey" if i % 2 == 0 else "stone_dark"
        # Irregular rounded stone
        m.add_sphere(8.0, c=(sx, sy, 8.0), segs_lat=4, segs_lon=6, mat=mat)

    # 4 crossed charred firewood logs in center
    m.add_box(-22, -4, 5, 44, 8, 7, mat="log_charred")
    m.add_box(-4, -22, 6, 8, 44, 7, mat="log_charred")
    m.add_box(-16, -16, 12, 32, 7, 6, mat="log_charred")
    return m

def build_camp_picnic_table_wood():
    """SM_Camp_PicnicTable_Wood (150x180x75cm): A-frame outdoor wooden picnic table."""
    m = Mesh("SM_Camp_PicnicTable_Wood")
    m.add_material("table_wood", 0.72, 0.56, 0.36)
    m.add_material("frame_wood", 0.56, 0.42, 0.26)

    # 2 heavy A-frame leg trusses (at y=-55 and y=+55):
    for fy in [-55, 55]:
        # Diagonal A-frame legs
        m.add_box(-52, fy - 3, 0, 6, 6, 68, mat="frame_wood")
        m.add_box(46, fy - 3, 0, 6, 6, 68, mat="frame_wood")
        # Bench seat support arm across entire width (width 140cm at z=40cm)
        m.add_box(-68, fy - 3, 38, 136, 6, 6, mat="frame_wood")
        # Table top support bearer (width 72cm at z=66cm)
        m.add_box(-36, fy - 3, 66, 72, 6, 6, mat="frame_wood")

    # Center longitudinal leg brace
    m.add_box(-3, -55, 34, 6, 110, 6, mat="frame_wood")

    # Tabletop planks: 5 planks along Y (length 175cm, total width 75cm) at z=72cm
    for i in range(5):
        tx = -35 + i * 14.5
        m.add_box(tx, -88, 72, 13, 176, 4, mat="table_wood")

    # Flanking bench seats: 2 planks on each side at z=44cm
    # Left bench (-X)
    m.add_box(-66, -88, 44, 12, 176, 4, mat="table_wood")
    m.add_box(-52, -88, 44, 12, 176, 4, mat="table_wood")
    # Right bench (+X)
    m.add_box(40, -88, 44, 12, 176, 4, mat="table_wood")
    m.add_box(54, -88, 44, 12, 176, 4, mat="table_wood")
    return m

# =============================================================================
# ASSET REGISTRY
# =============================================================================

PROPS_REGISTRY = [
    # 1. Logging & Fuel (5)
    ("SM_Log_Pile_Large", build_log_pile_large, "logging", "1.2x2.4m", "Pyramid stack of 10 large cut timber logs with support chocks"),
    ("SM_Log_Pile_Medium", build_log_pile_medium, "logging", "0.9x1.6m", "Stack of 6 cut firewood logs secured between side stakes"),
    ("SM_Firewood_Rack_Cord", build_firewood_rack_cord, "logging", "0.5x2.4m", "Tubular steel rack stacked full of split seasoned cordwood"),
    ("SM_Firewood_Bundle_Wrapped", build_firewood_bundle_wrapped, "logging", "0.35x0.45m", "Shrink-wrapped bundle of kiln-dried firewood with handle strap"),
    ("SM_Chopping_Block_Maul", build_chopping_block_maul, "logging", "0.55x0.55m", "Oak stump chopping block with heavy splitting maul embedded"),

    # 2. Building Supplies & Materials (7)
    ("SM_Mat_Lumber_Stack_2x4", build_mat_lumber_stack_2x4, "building", "0.8x2.4m", "Steel-banded bundle of dimensional 2x4 framing studs on skids"),
    ("SM_Mat_Plywood_Stack", build_mat_plywood_stack, "building", "1.2x2.4m", "Stack of 4x8 CDX plywood sheathing boards on 4x4 timber runners"),
    ("SM_Mat_Pallet_Wood", build_mat_pallet_wood, "building", "1.0x1.2m", "Standard GMA/Euro heavy wooden warehouse shipping pallet"),
    ("SM_Mat_CinderBlocks_Stack", build_mat_cinder_blocks_stack, "building", "0.8x1.2m", "Tiered stack of 2-core hollow concrete cinder blocks on pallet"),
    ("SM_Mat_Brick_Pallet", build_mat_brick_pallet, "building", "0.9x0.9m", "Banded pallet of red clay masonry construction bricks"),
    ("SM_Mat_Steel_Drum_55gal", build_mat_steel_drum_55gal, "building", "0.6x0.6m", "Blue 55-gallon steel fuel and chemical storage drum with bungs"),
    ("SM_Mat_PropaneTank_500gal", build_mat_propane_tank_500gal, "building", "0.95x3.0m", "500-gallon horizontal torpedo LP gas propane tank on saddles"),

    # 3. Workshop Tools (5)
    ("SM_Tool_Workbench_Timber", build_tool_workbench_timber, "tools", "0.8x1.8m", "Heavy-duty timber workbench with cast iron vise and tool shelf"),
    ("SM_Tool_Anvil_Stump", build_tool_anvil_stump, "tools", "0.45x0.65m", "Cast steel blacksmith anvil strapped to solid hardwood stump"),
    ("SM_Tool_CementMixer_Electric", build_tool_cement_mixer_electric, "tools", "0.85x1.2m", "Orange electric rotating drum cement mixer on wheeled A-frame"),
    ("SM_Tool_ToolChest_Rolling", build_tool_toolchest_rolling, "tools", "0.55x0.95m", "Red 6-drawer mechanic rolling tool chest with worktop mat"),
    ("SM_Tool_Sawhorse_Pair", build_tool_sawhorse_pair, "tools", "0.6x0.95m", "Pair of sturdy timber carpenters' A-frame sawhorses"),

    # 4. Waterfront & Camping (6)
    ("SM_Water_Dock_Section_1x2m", build_water_dock_section_1x2m, "fishing", "1.0x2.0m", "Modular cedar plank dock section with pilings and mooring cleats"),
    ("SM_Water_Rowboat_Wood", build_water_rowboat_wood, "fishing", "1.1x3.0m", "10-foot cedar lapstrake wooden rowing skiff with bench thwarts and oars"),
    ("SM_Camp_Tent_Canvas_Wall", build_camp_tent_canvas_wall, "building", "2.4x3.0m", "Heavy canvas outfitter wall tent with stovepipe flashing elbow"),
    ("SM_Camp_Tent_Dome", build_camp_tent_dome, "building", "2.0x2.0m", "Modern 2-person geodesic dome camping tent with crossed poles"),
    ("SM_Camp_Campfire_Ring", build_camp_campfire_ring, "building", "0.8x0.8m", "Circular stone campfire ring with glowing coals and charred logs"),
    ("SM_Camp_PicnicTable_Wood", build_camp_picnic_table_wood, "building", "1.5x1.8m", "Heavy timber A-frame park picnic table with attached bench seats"),
]

def main():
    print("=================================================================")
    print("HOMESTEADER PROPS, MATERIALS & CAMP 3D ASSET GENERATOR")
    print(f"Total Assets: {len(PROPS_REGISTRY)}")
    print("=================================================================\n")

    count = 0
    for name, func, category, footprint, desc in PROPS_REGISTRY:
        count += 1
        mesh = func()
        mesh.ground_align()
        tri_count = len(mesh.faces)

        paths = CAT_DIRS[category]
        hud_obj = os.path.join(paths["hud_models"], f"{name}.obj")
        hud_mtl = os.path.join(paths["hud_models"], f"{name}.mtl")
        mesh.save_obj(hud_obj, hud_mtl)

        ue5_obj = os.path.join(paths["ue5_models"], f"{name}.obj")
        ue5_mtl = os.path.join(paths["ue5_models"], f"{name}.mtl")
        shutil.copy2(hud_obj, ue5_obj)
        shutil.copy2(hud_mtl, ue5_mtl)

        icon_img = render_icon(mesh, output_size=128, max_dim=96)
        hud_icon = os.path.join(paths["hud_icons"], f"{name}.png")
        ue5_icon = os.path.join(paths["ue5_icons"], f"{name}.png")
        icon_img.save(hud_icon, "PNG")
        icon_img.save(ue5_icon, "PNG")

        print(f"[{count:02d}/{len(PROPS_REGISTRY)}] Generated {name} ({category}, {footprint}) - {tri_count} tris")

    print(f"\nSUCCESS: All {len(PROPS_REGISTRY)} Props, Materials, Logging, Workshop & Camp assets generated and synced!")

if __name__ == "__main__":
    main()

