"""
Homesteader 3D Utilities & Infrastructure Asset Generator
Creates 28 low-poly 3D models (.obj + .mtl) and 128x128 preview icons:
- Off-Grid Electricity: Solar arrays, wind turbines, generators, battery powerwalls, racks, inverters, power poles, wire reels
- Water Systems: Rain barrels, IBC totes, 1000gal cisterns, hand well pumps, pressure tanks, 3-stage filters, hose reels, stock troughs
- Sewage & Waste: 500gal ribbed septic tanks, D-boxes, 3-bay cedar composters, composting toilets
- Internet & Comms: Starlink dishes, high-perf mast dishes, Yagi antennas, cellular omni sticks, outdoor APs

All models feature watertight 360° geometry on all 4 sides and ground alignment at Z_min = 0.0.
Output directories:
  HUD/assets/utilities/models/ & icons/
  Homesteader/Content/Homesteader/Assets/Utilities/Meshes/ & UI/Icons/Utilities/
"""

import os
import math
import shutil
from PIL import Image, ImageDraw, ImageFilter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

HUD_MODELS = os.path.join(PROJECT_ROOT, "HUD", "assets", "utilities", "models")
HUD_ICONS  = os.path.join(PROJECT_ROOT, "HUD", "assets", "utilities", "icons")

UE5_MODELS = os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "Assets", "Utilities", "Meshes")
UE5_ICONS  = os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "UI", "Icons", "Utilities")

for p in [HUD_MODELS, HUD_ICONS, UE5_MODELS, UE5_ICONS]:
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
        self.faces.append(([(iv, iv, iv), (iv+1, iv+1, iv+1), (iv+2, iv+2, iv+2)], mat))

    def add_quad(self, v0, v1, v2, v3, uv0=(0,0), uv1=(1,0), uv2=(1,1), uv3=(0,1), mat="default"):
        self.add_triangle(v0, v1, v2, uv0, uv1, uv2, mat=mat)
        self.add_triangle(v0, v2, v3, uv0, uv2, uv3, mat=mat)

    def add_box(self, size, center=(0,0,0), mat="default", segs_y=1, top_cap=True):
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

        self.add_quad(p000, p010, p110, p100, mat=mat) # Bottom
        if top_cap:
            self.add_quad(p001, p101, p111, p011, mat=mat) # Top
        self.add_quad(p000, p100, p101, p001, mat=mat) # Front (-Y)
        self.add_quad(p110, p010, p011, p111, mat=mat) # Back (+Y)
        self.add_quad(p010, p000, p001, p011, mat=mat) # Left (-X)
        self.add_quad(p100, p110, p111, p101, mat=mat) # Right (+X)

    def add_cylinder(self, r0, r1, h, z0=0.0, segs=10, mat="default", c0=(0,0), c1=(0,0)):
        angles = [2.0 * math.pi * i / segs for i in range(segs)]
        ring0 = [Vec3(c0[0] + r0 * math.cos(a), c0[1] + r0 * math.sin(a), z0) for a in angles]
        ring1 = [Vec3(c1[0] + r1 * math.cos(a), c1[1] + r1 * math.sin(a), z0 + h) for a in angles]
        center_bot = Vec3(c0[0], c0[1], z0)
        center_top = Vec3(c1[0], c1[1], z0 + h)

        for i in range(segs):
            nxt = (i + 1) % segs
            self.add_quad(ring0[i], ring0[nxt], ring1[nxt], ring1[i], mat=mat)
            if r0 > 1e-4:
                self.add_triangle(center_bot, ring0[nxt], ring0[i], mat=mat)
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
# 3D Icon Renderer
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

        v0 = mesh.vertices[idx0]
        v1 = mesh.vertices[idx1]
        v2 = mesh.vertices[idx2]
        norm = (v1 - v0).cross(v2 - v0).normalized()

        if norm.dot(L) >= -0.01:
            continue

        c0 = cam_verts[idx0]
        c1 = cam_verts[idx1]
        c2 = cam_verts[idx2]

        sx0 = (c0[0] - center_x) * scale * ss + screen_c
        sy0 = screen_c - (c0[1] - center_y) * scale * ss
        sx1 = (c1[0] - center_x) * scale * ss + screen_c
        sy1 = screen_c - (c1[1] - center_y) * scale * ss
        sx2 = (c2[0] - center_x) * scale * ss + screen_c
        sy2 = screen_c - (c2[1] - center_y) * scale * ss

        depth = (c0[2] + c1[2] + c2[2]) / 3.0

        ndotl = max(0.0, norm.dot(key_light))
        ndotf = max(0.0, norm.dot(fill_light))

        if ndotl > 0.52: illum = 1.20
        elif ndotl > 0.20: illum = 0.98
        else: illum = 0.72 + 0.16 * ndotf

        base_color = mesh.materials.get(mat_name, (0.5, 0.5, 0.5))
        r = int(min(255, max(0, base_color[0] * illum * 255.0)))
        g = int(min(255, max(0, base_color[1] * illum * 255.0)))
        b = int(min(255, max(0, base_color[2] * illum * 255.0)))

        triangles.append((depth, [(sx0, sy0), (sx1, sy1), (sx2, sy2)], (r, g, b, 255)))

    triangles.sort(key=lambda t: t[0])
    for d, pts, fill in triangles:
        draw.polygon(pts, fill=fill, outline=fill)

    alpha = img_ss.split()[3]
    dilated = alpha.filter(ImageFilter.MaxFilter(5))
    ink = Image.new("RGBA", (canvas_size, canvas_size), (26, 22, 20, 255))
    ink.putalpha(dilated)
    final_ss = Image.alpha_composite(ink, img_ss)

    out = final_ss.resize((output_size, output_size), Image.Resampling.LANCZOS)
    px = out.load()
    for y in range(output_size):
        for x in range(output_size):
            if x < 12 or x >= (output_size - 12) or y < 12 or y >= (output_size - 12):
                px[x, y] = (0, 0, 0, 0)
    return out

# =============================================================================
# ELECTRICITY / POWER ASSETS (11)
# =============================================================================

def build_solar_panel_ground_1m():
    m = Mesh("SM_Electric_SolarPanel_Ground_1m")
    m.add_material("Metal_Frame", 0.60, 0.62, 0.65)
    m.add_material("Solar_Cells", 0.12, 0.18, 0.35)
    m.add_material("Hardware", 0.30, 0.30, 0.32)

    # 4 galvanized ground rack legs (1m x 1m base footprint)
    m.add_cylinder(r0=2.5, r1=2.5, h=25, z0=0, segs=6, mat="Metal_Frame", c0=(-45, -45), c1=(-45, -45))
    m.add_cylinder(r0=2.5, r1=2.5, h=25, z0=0, segs=6, mat="Metal_Frame", c0=( 45, -45), c1=( 45, -45))
    m.add_cylinder(r0=2.5, r1=2.5, h=70, z0=0, segs=6, mat="Metal_Frame", c0=(-45,  45), c1=(-45,  45))
    m.add_cylinder(r0=2.5, r1=2.5, h=70, z0=0, segs=6, mat="Metal_Frame", c0=( 45,  45), c1=( 45,  45))

    # Cross rails
    m.add_box((96, 4, 4), center=(0, -45, 25), mat="Metal_Frame")
    m.add_box((96, 4, 4), center=(0,  45, 70), mat="Metal_Frame")

    # Tilted solar panel frame (angle ~30 degrees facing -Y)
    p_bl = Vec3(-48, -48, 28)
    p_br = Vec3( 48, -48, 28)
    p_tr = Vec3( 48,  48, 75)
    p_tl = Vec3(-48,  48, 75)
    m.add_quad(p_bl, p_br, p_tr, p_tl, mat="Solar_Cells")

    # Aluminum edge frame borders
    w = 3.0
    m.add_box((100, w, 4), center=(0, -48, 28), mat="Metal_Frame")
    m.add_box((100, w, 4), center=(0,  48, 75), mat="Metal_Frame")
    m.add_box((w, 98, 4), center=(-48, 0, 51.5), mat="Metal_Frame")
    m.add_box((w, 98, 4), center=( 48, 0, 51.5), mat="Metal_Frame")
    return m

def build_solar_array_3m():
    m = Mesh("SM_Electric_SolarArray_3m")
    m.add_material("Metal_Frame", 0.58, 0.60, 0.64)
    m.add_material("Solar_Cells", 0.10, 0.16, 0.32)
    m.add_material("Concrete_Footing", 0.68, 0.66, 0.62)

    # 6 concrete pier footings (3x2m footprint)
    for x in [-120, 0, 120]:
        m.add_cylinder(r0=14, r1=12, h=18, z0=0, segs=8, mat="Concrete_Footing", c0=(x, -70), c1=(x, -70))
        m.add_cylinder(r0=14, r1=12, h=18, z0=0, segs=8, mat="Concrete_Footing", c0=(x,  70), c1=(x,  70))
        # Structural steel columns
        m.add_box((6, 6, 45), center=(x, -70, 40), mat="Metal_Frame")
        m.add_box((6, 6, 115), center=(x,  70, 75), mat="Metal_Frame")

    # 3 Commercial dual-panel rows tilted toward South (-Y)
    for x in [-100, 0, 100]:
        # Panel surface (92x160cm each, subdivided 2x4 for depth sorting)
        for u in range(2):
            for v in range(4):
                x0 = x - 46 + u * 46
                x1 = x - 46 + (u+1) * 46
                y0 = -80 + v * 40
                y1 = -80 + (v+1) * 40
                z0 = 65 + (y0 + 80) * (70.0 / 160.0)
                z1 = 65 + (y1 + 80) * (70.0 / 160.0)
                m.add_quad(Vec3(x0, y0, z0), Vec3(x1, y0, z0), Vec3(x1, y1, z1), Vec3(x0, y1, z1), mat="Solar_Cells")
        # Sloped side edge frames (following panel slope)
        p_l0 = Vec3(x - 48, -80, 65.5)
        p_l1 = Vec3(x - 44, -80, 65.5)
        p_l2 = Vec3(x - 44,  80, 135.5)
        p_l3 = Vec3(x - 48,  80, 135.5)
        m.add_quad(p_l0, p_l1, p_l2, p_l3, mat="Metal_Frame")

        p_r0 = Vec3(x + 44, -80, 65.5)
        p_r1 = Vec3(x + 48, -80, 65.5)
        p_r2 = Vec3(x + 48,  80, 135.5)
        p_r3 = Vec3(x + 44,  80, 135.5)
        m.add_quad(p_r0, p_r1, p_r2, p_r3, mat="Metal_Frame")

        m.add_box((96, 4, 4), center=(x, -80, 65), mat="Metal_Frame")
        m.add_box((96, 4, 4), center=(x,  80, 135), mat="Metal_Frame")
    return m

def build_wind_turbine_small():
    m = Mesh("SM_Electric_WindTurbine_Small")
    m.add_material("Galvanized_Steel", 0.72, 0.74, 0.76)
    m.add_material("Turbine_Body", 0.88, 0.90, 0.92)
    m.add_material("Blades", 0.95, 0.95, 0.95)
    m.add_material("Tail_Fin", 0.85, 0.20, 0.15)

    # 1x1m 4-post guyed anchor base + central mast (4.5m tall)
    m.add_box((80, 80, 8), center=(0, 0, 4), mat="Galvanized_Steel")
    m.add_cylinder(r0=9, r1=6, h=400, z0=8, segs=8, mat="Galvanized_Steel")

    # Nacelle body
    m.add_cylinder(r0=7, r1=7, h=35, z0=405, segs=8, mat="Turbine_Body", c0=(0, -10), c1=(0, 25))
    # Nose cone
    m.add_cone(r=8, h=16, z0=405, segs=8, mat="Turbine_Body", c=(0, -10))

    # Tail boom and red directional vane
    m.add_box((3, 40, 4), center=(0, 45, 412), mat="Galvanized_Steel")
    m.add_box((2, 25, 30), center=(0, 65, 418), mat="Tail_Fin")

    # 3 Aerodynamic blades (radius 60cm each, 120 deg apart)
    hub_z = 412
    for angle in [0, 120, 240]:
        rad = math.radians(angle)
        dx = math.cos(rad)
        dz = math.sin(rad)
        p0 = Vec3(0, -12, hub_z)
        p1 = Vec3(dx * 55, -12, hub_z + dz * 55)
        p2 = Vec3(dx * 52 + dz * 6, -11, hub_z + dz * 52 - dx * 6)
        m.add_triangle(p0, p1, p2, mat="Blades")
        m.add_triangle(p0, p2, p1, mat="Blades")
    return m

def build_wind_turbine_large():
    m = Mesh("SM_Electric_WindTurbine_Large")
    m.add_material("Steel_Lattice", 0.65, 0.68, 0.70)
    m.add_material("Turbine_White", 0.90, 0.92, 0.94)
    m.add_material("Blades", 0.96, 0.96, 0.96)
    m.add_material("Concrete_Pad", 0.70, 0.68, 0.65)

    # 1.2x1.2m concrete foundation pad
    m.add_box((120, 120, 15), center=(0, 0, 7.5), mat="Concrete_Pad")

    # 3-legged tapered lattice tower (8.0m tall)
    m.add_cylinder(r0=45, r1=14, h=720, z0=15, segs=6, mat="Steel_Lattice")
    for z in range(60, 720, 90):
        r_ring = 45 - (45 - 14) * (z / 720.0)
        m.add_cylinder(r0=r_ring, r1=r_ring, h=5, z0=z, segs=6, mat="Steel_Lattice")

    # Nacelle housing
    m.add_box((22, 60, 24), center=(0, 10, 745), mat="Turbine_White")
    m.add_cylinder(r0=11, r1=11, h=15, z0=745, segs=8, mat="Turbine_White", c0=(0, -20), c1=(0, -20))

    # 3 large airfoil blades (140cm length each)
    hub_z = 745
    for angle in [30, 150, 270]:
        rad = math.radians(angle)
        dx = math.cos(rad)
        dz = math.sin(rad)
        p0 = Vec3(0, -22, hub_z)
        p1 = Vec3(dx * 135, -21, hub_z + dz * 135)
        p2 = Vec3(dx * 130 + dz * 14, -20, hub_z + dz * 130 - dx * 14)
        m.add_triangle(p0, p1, p2, mat="Blades")
        m.add_triangle(p0, p2, p1, mat="Blades")
    return m

def build_generator_portable():
    m = Mesh("SM_Electric_Generator_Portable")
    m.add_material("Yellow_Paint", 0.92, 0.72, 0.12)
    m.add_material("Black_Steel", 0.20, 0.20, 0.22)
    m.add_material("Engine_Block", 0.38, 0.40, 0.42)
    m.add_material("Control_Panel", 0.15, 0.15, 0.16)

    # Steel tube roll cage frame (60x50x55cm)
    m.add_box((58, 48, 4), center=(0, 0, 4), mat="Black_Steel")
    # 4 perimeter top rails
    m.add_box((58, 4, 4), center=(0, -21, 52), mat="Black_Steel")
    m.add_box((58, 4, 4), center=(0,  21, 52), mat="Black_Steel")
    m.add_box((4, 42, 4), center=(-26, 0, 52), mat="Black_Steel")
    m.add_box((4, 42, 4), center=( 26, 0, 52), mat="Black_Steel")
    for cx in [-26, 26]:
        for cy in [-21, 21]:
            m.add_cylinder(r0=2, r1=2, h=48, z0=4, segs=6, mat="Black_Steel", c0=(cx, cy), c1=(cx, cy))

    # Engine block & alternator
    m.add_box((28, 30, 28), center=(-6, 0, 20), mat="Engine_Block")
    m.add_cylinder(r0=10, r1=10, h=18, z0=20, segs=8, mat="Black_Steel", c0=(12, 0), c1=(12, 0))

    # Yellow top fuel tank with black cap
    m.add_box((46, 36, 12), center=(0, 0, 44), mat="Yellow_Paint")
    m.add_cylinder(r0=4, r1=4, h=3, z0=50, segs=8, mat="Black_Steel", c0=(0, 0), c1=(0, 0))

    # Front control panel with outlets
    m.add_box((2, 28, 20), center=(-27, 0, 26), mat="Control_Panel")
    # Wheels at rear
    for cy in [-24, 24]:
        m.add_cylinder(r0=8, r1=8, h=5, z0=8, segs=8, mat="Black_Steel", c0=(24, cy), c1=(24, cy))
    return m

def build_generator_standby():
    m = Mesh("SM_Electric_Generator_Standby")
    m.add_material("Tan_Enclosure", 0.78, 0.75, 0.68)
    m.add_material("Louver_Grill", 0.25, 0.26, 0.28)
    m.add_material("Concrete_Pad", 0.65, 0.64, 0.62)
    m.add_material("Lock_Latch", 0.40, 0.40, 0.42)

    # Concrete foundation slab (120x80cm, H=12cm)
    m.add_box((120, 80, 12), center=(0, 0, 6), mat="Concrete_Pad")

    # Weatherproof acoustic canopy cabinet (105x68x75cm)
    m.add_box((105, 68, 70), center=(0, 0, 47), mat="Tan_Enclosure")

    # Domed lid / roof
    m.add_box((108, 71, 6), center=(0, 0, 84), mat="Tan_Enclosure")

    # Front air intake louvers
    m.add_box((4, 45, 30), center=(-53, 0, 48), mat="Louver_Grill")
    # Exhaust louvers at side
    m.add_box((35, 4, 25), center=(15, 34, 52), mat="Louver_Grill")
    # Access door latches
    m.add_box((6, 2, 8), center=(-15, -34.5, 50), mat="Lock_Latch")
    m.add_box((6, 2, 8), center=( 25, -34.5, 50), mat="Lock_Latch")
    return m

def build_battery_powerwall():
    m = Mesh("SM_Electric_Battery_Powerwall")
    m.add_material("White_Gloss", 0.94, 0.94, 0.95)
    m.add_material("Glass_Face", 0.22, 0.25, 0.30)
    m.add_material("LED_Green", 0.20, 0.85, 0.35)
    m.add_material("Dark_Bezel", 0.18, 0.20, 0.22)

    # Sleek home battery cabinet (75x24x115cm)
    m.add_box((75, 24, 115), center=(0, 0, 57.5), mat="White_Gloss")

    # Front glass panel recess
    m.add_box((71, 2, 108), center=(0, -11.5, 57.5), mat="Glass_Face")

    # Dark perimeter accent bezel
    m.add_box((73, 1, 3), center=(0, -12, 112), mat="Dark_Bezel")
    m.add_box((73, 1, 3), center=(0, -12, 4), mat="Dark_Bezel")

    # Glowing vertical state-of-charge LED strip
    m.add_box((2, 1, 60), center=(-28, -12.2, 58), mat="LED_Green")
    return m

def build_battery_rack_48v():
    m = Mesh("SM_Electric_Battery_Rack_48V")
    m.add_material("Rack_Black", 0.18, 0.18, 0.20)
    m.add_material("Module_Face", 0.28, 0.30, 0.34)
    m.add_material("LED_Blue", 0.20, 0.55, 0.95)
    m.add_material("Handle_Silver", 0.75, 0.76, 0.78)

    # 19-inch steel server rack frame (60x60x160cm)
    m.add_box((60, 60, 8), center=(0, 0, 4), mat="Rack_Black")
    m.add_box((60, 60, 8), center=(0, 0, 156), mat="Rack_Black")
    for cx in [-27, 27]:
        for cy in [-27, 27]:
            m.add_box((6, 6, 144), center=(cx, cy, 80), mat="Rack_Black")

    # 4 Slide-in 48V 5kWh server battery modules
    for i in range(4):
        bz = 24 + i * 32
        m.add_box((52, 54, 26), center=(0, 0, bz), mat="Module_Face")
        # Dual handles on front (-Y)
        m.add_box((12, 3, 4), center=(-18, -27.5, bz), mat="Handle_Silver")
        m.add_box((12, 3, 4), center=( 18, -27.5, bz), mat="Handle_Silver")
        # LED display indicators
        m.add_box((16, 2, 4), center=(0, -27.2, bz + 5), mat="LED_Blue")
    return m

def build_inverter_wall():
    m = Mesh("SM_Electric_Inverter_Wall")
    m.add_material("Inverter_White", 0.88, 0.89, 0.90)
    m.add_material("Heatsink_Black", 0.16, 0.16, 0.18)
    m.add_material("LCD_Screen", 0.15, 0.35, 0.40)
    m.add_material("Conduit_Knockout", 0.45, 0.46, 0.48)

    # Main wall-mount chassis (45x22x65cm)
    m.add_box((45, 20, 65), center=(0, 0, 32.5), mat="Inverter_White")

    # Aluminum heatsink cooling fins on back (+Y)
    m.add_box((41, 4, 60), center=(0, 11, 32.5), mat="Heatsink_Black")

    # Front LCD display screen & status buttons
    m.add_box((18, 2, 14), center=(0, -10.5, 42), mat="LCD_Screen")
    m.add_box((14, 2, 4), center=(0, -10.5, 30), mat="Heatsink_Black")

    # Bottom conduit wire gland knockouts
    for kx in [-12, 0, 12]:
        m.add_cylinder(r0=3, r1=3, h=6, z0=-6, segs=6, mat="Conduit_Knockout", c0=(kx, 0), c1=(kx, 0))
    return m

def build_power_pole_wood():
    m = Mesh("SM_Electric_PowerPole_Wood")
    m.add_material("Creosote_Wood", 0.38, 0.28, 0.20)
    m.add_material("Galvanized_Hardware", 0.65, 0.66, 0.68)
    m.add_material("Ceramic_Insulator", 0.25, 0.45, 0.35)

    # Main utility pole (diameter 26cm -> 18cm, height 6.5m)
    m.add_cylinder(r0=13, r1=9, h=650, z0=0, segs=8, mat="Creosote_Wood")

    # Crossarm timber at top (2.2m wide)
    m.add_box((220, 12, 12), center=(0, 0, 620), mat="Creosote_Wood")
    # Diagonal steel crossarm braces
    m.add_box((55, 3, 3), center=(-35, 0, 605), mat="Galvanized_Hardware")
    m.add_box((55, 3, 3), center=( 35, 0, 605), mat="Galvanized_Hardware")

    # 3 Bell-shaped ceramic high-voltage insulators
    for ix in [-95, 0, 95]:
        m.add_cylinder(r0=5, r1=3.5, h=16, z0=626, segs=6, mat="Ceramic_Insulator", c0=(ix, 0), c1=(ix, 0))
        m.add_cylinder(r0=7, r1=7, h=3, z0=632, segs=6, mat="Ceramic_Insulator", c0=(ix, 0), c1=(ix, 0))
    return m

def build_wire_spool_wood():
    m = Mesh("SM_Electric_WireSpool_Wood")
    m.add_material("Wood_Spool", 0.62, 0.48, 0.32)
    m.add_material("Copper_Wire", 0.85, 0.45, 0.20)
    m.add_material("Steel_Bolts", 0.40, 0.40, 0.42)

    # Heavy round wooden cable spool (diameter 80cm, width 65cm)
    # Flange 1 (-X)
    m.add_cylinder(r0=40, r1=40, h=5, z0=0, segs=12, mat="Wood_Spool", c0=(-28, 0), c1=(-28, 0))
    # Flange 2 (+X)
    m.add_cylinder(r0=40, r1=40, h=5, z0=0, segs=12, mat="Wood_Spool", c0=( 28, 0), c1=( 28, 0))

    # Core barrel wound with heavy copper / black Romex wire
    m.add_cylinder(r0=24, r1=24, h=50, z0=0, segs=10, mat="Copper_Wire", c0=(-25, 0), c1=(-25, 0))

    # Center arbor hole & tie rods
    m.add_cylinder(r0=6, r1=6, h=62, z0=0, segs=8, mat="Steel_Bolts", c0=(-31, 0), c1=(-31, 0))
    return m

# =============================================================================
# WATER INFRASTRUCTURE ASSETS (8)
# =============================================================================

def build_rain_barrel_55gal():
    m = Mesh("SM_Water_RainBarrel_55gal")
    m.add_material("Blue_Poly", 0.16, 0.42, 0.68)
    m.add_material("Black_Lid", 0.18, 0.18, 0.20)
    m.add_material("Brass_Spigot", 0.85, 0.70, 0.25)
    m.add_material("Cinder_Pedestal", 0.65, 0.63, 0.60)

    # Cinder block pedestal stand (H=20cm)
    m.add_box((52, 52, 20), center=(0, 0, 10), mat="Cinder_Pedestal")

    # 55-gallon ribbed blue barrel drum (D=58cm, H=90cm)
    m.add_cylinder(r0=28, r1=30, h=30, z0=20, segs=12, mat="Blue_Poly")
    m.add_cylinder(r0=30, r1=29, h=30, z0=50, segs=12, mat="Blue_Poly")
    m.add_cylinder(r0=29, r1=28, h=30, z0=80, segs=12, mat="Blue_Poly")

    # Top removable lid with mesh gutter screen
    m.add_cylinder(r0=29, r1=29, h=4, z0=110, segs=12, mat="Black_Lid")
    m.add_cylinder(r0=12, r1=12, h=2, z0=114, segs=8, mat="Black_Lid")

    # Front brass spigot faucet
    m.add_cylinder(r0=2, r1=2, h=10, z0=28, segs=6, mat="Brass_Spigot", c0=(0, -28), c1=(0, -38))
    m.add_box((6, 2, 4), center=(0, -38, 30), mat="Brass_Spigot")
    return m

def build_ibc_tote_275gal():
    m = Mesh("SM_Water_IBC_Tote_275gal")
    m.add_material("Poly_Translucent", 0.82, 0.86, 0.88)
    m.add_material("Galvanized_Cage", 0.68, 0.70, 0.72)
    m.add_material("Pallet_Base", 0.22, 0.22, 0.24)
    m.add_material("Red_Valve", 0.85, 0.18, 0.15)

    # Steel / plastic composite pallet base (100x120cm, H=12cm)
    m.add_box((100, 120, 12), center=(0, 0, 6), mat="Pallet_Base")

    # Translucent polyethylene bottle tank (92x112x96cm)
    m.add_box((92, 112, 96), center=(0, 0, 60), mat="Poly_Translucent")

    # Galvanized tubular steel cage grid
    m.add_box((98, 118, 4), center=(0, 0, 15), mat="Galvanized_Cage")
    m.add_box((98, 118, 4), center=(0, 0, 62), mat="Galvanized_Cage")
    m.add_box((98, 118, 4), center=(0, 0, 108), mat="Galvanized_Cage")
    for cx in [-48, 48]:
        for cy in [-58, -20, 20, 58]:
            m.add_cylinder(r0=1.8, r1=1.8, h=95, z0=14, segs=6, mat="Galvanized_Cage", c0=(cx, cy), c1=(cx, cy))

    # Top 6" fill port & cap
    m.add_cylinder(r0=10, r1=10, h=6, z0=108, segs=8, mat="Red_Valve")
    # Bottom 2" discharge camlock ball valve on front (-Y)
    m.add_cylinder(r0=5, r1=5, h=10, z0=18, segs=6, mat="Red_Valve", c0=(0, -56), c1=(0, -66))
    return m

def build_cistern_poly_1000gal():
    m = Mesh("SM_Water_Cistern_Poly_1000gal")
    m.add_material("Dark_Green_Poly", 0.18, 0.35, 0.22)
    m.add_material("Manhole_Lid", 0.12, 0.12, 0.14)
    m.add_material("Brass_Fitting", 0.82, 0.68, 0.24)

    # Large 1000-gallon vertical storage tank (Diameter 180cm, Height 190cm)
    # Heavy ribbed cylinder walls
    for z in range(0, 160, 20):
        m.add_cylinder(r0=90, r1=92, h=10, z0=z, segs=16, mat="Dark_Green_Poly")
        m.add_cylinder(r0=92, r1=90, h=10, z0=z+10, segs=16, mat="Dark_Green_Poly")

    # Domed top cap
    m.add_cylinder(r0=90, r1=50, h=25, z0=160, segs=16, mat="Dark_Green_Poly")
    # Center 16" inspection manhole lid
    m.add_cylinder(r0=25, r1=25, h=8, z0=185, segs=12, mat="Manhole_Lid")

    # Lower 2" brass bulkhead drain fitting on front (-Y)
    m.add_cylinder(r0=5, r1=5, h=12, z0=15, segs=8, mat="Brass_Fitting", c0=(0, -90), c1=(0, -102))
    return m

def build_well_pump_manual():
    m = Mesh("SM_Water_WellPump_Manual")
    m.add_material("Cast_Iron", 0.22, 0.30, 0.26)
    m.add_material("Oak_Well_Cover", 0.52, 0.38, 0.24)
    m.add_material("Steel_Rod", 0.65, 0.65, 0.68)

    # Octagonal wooden well cap platform
    m.add_cylinder(r0=38, r1=38, h=10, z0=0, segs=8, mat="Oak_Well_Cover")

    # Pitcher pump base flange & barrel
    m.add_cylinder(r0=12, r1=7, h=30, z0=10, segs=8, mat="Cast_Iron")
    m.add_cylinder(r0=7, r1=7, h=55, z0=40, segs=8, mat="Cast_Iron")
    m.add_cylinder(r0=9, r1=9, h=15, z0=95, segs=8, mat="Cast_Iron")

    # Curved discharge spout pointing front (-Y)
    m.add_cylinder(r0=4, r1=3.5, h=22, z0=65, segs=6, mat="Cast_Iron", c0=(0, -7), c1=(0, -29))

    # Heavy pump handle lever
    m.add_cylinder(r0=2.5, r1=2, h=55, z0=100, segs=6, mat="Cast_Iron", c0=(0, 6), c1=(0, 55))
    m.add_cylinder(r0=3.5, r1=3.5, h=8, z0=96, segs=6, mat="Cast_Iron", c0=(0, 52), c1=(0, 52))
    return m

def build_pressure_tank_well():
    m = Mesh("SM_Water_PressureTank_Well")
    m.add_material("Tank_Blue", 0.20, 0.45, 0.72)
    m.add_material("Jet_Pump_Cast", 0.25, 0.32, 0.35)
    m.add_material("Brass_Manifold", 0.85, 0.70, 0.25)
    m.add_material("Pressure_Gauge", 0.95, 0.95, 0.95)

    # 3 steel tank stand legs
    for a in [0, 120, 240]:
        rad = math.radians(a)
        m.add_cylinder(r0=2, r1=2, h=15, z0=0, segs=6, mat="Tank_Blue",
                       c0=(math.cos(rad)*20, math.sin(rad)*20),
                       c1=(math.cos(rad)*20, math.sin(rad)*20))

    # Domed vertical pressure tank (D=48cm, H=85cm)
    m.add_cylinder(r0=20, r1=24, h=12, z0=15, segs=12, mat="Tank_Blue")
    m.add_cylinder(r0=24, r1=24, h=55, z0=27, segs=12, mat="Tank_Blue")
    m.add_cylinder(r0=24, r1=18, h=12, z0=82, segs=12, mat="Tank_Blue")

    # Mounted shallow-well jet pump on top shelf
    m.add_box((22, 34, 18), center=(0, 0, 102), mat="Jet_Pump_Cast")
    m.add_cylinder(r0=7, r1=7, h=18, z0=102, segs=8, mat="Jet_Pump_Cast", c0=(0, 12), c1=(0, 12))

    # Brass 5-way tee manifold & round pressure dial gauge
    m.add_box((6, 6, 14), center=(0, -16, 104), mat="Brass_Manifold")
    m.add_cylinder(r0=4, r1=4, h=3, z0=114, segs=8, mat="Pressure_Gauge", c0=(0, -16), c1=(0, -16))
    return m

def build_filter_rack_3stage():
    m = Mesh("SM_Water_FilterRack_3Stage")
    m.add_material("Steel_Bracket", 0.90, 0.90, 0.92)
    m.add_material("Big_Blue_Housing", 0.12, 0.32, 0.65)
    m.add_material("Black_Filter_Head", 0.18, 0.18, 0.20)
    m.add_material("Copper_Plumbing", 0.82, 0.45, 0.25)
    m.add_material("Pressure_Gauge", 0.95, 0.95, 0.95)

    # Steel wall-mount hanging bracket (60x22cm)
    m.add_box((60, 4, 16), center=(0, 8, 65), mat="Steel_Bracket")

    # 3 "Big Blue" 20-inch filter housings (Sediment, Carbon, Lead/Iron)
    for x in [-18, 0, 18]:
        # Filter head with pressure release red button
        m.add_box((16, 16, 10), center=(x, 0, 60), mat="Black_Filter_Head")
        # Sump canister bowl
        m.add_cylinder(r0=7.5, r1=6.5, h=48, z0=12, segs=10, mat="Big_Blue_Housing", c0=(x, 0), c1=(x, 0))

    # Top connecting copper manifold pipe (1-inch)
    m.add_cylinder(r0=2, r1=2, h=66, z0=62, segs=6, mat="Copper_Plumbing", c0=(-33, 0), c1=(33, 0))
    # Inlet & outlet pressure gauges
    for gx in [-20, 20]:
        m.add_cylinder(r0=3, r1=3, h=3, z0=70, segs=8, mat="Pressure_Gauge", c0=(gx, 0), c1=(gx, 0))
    return m

def build_hose_reel_cart():
    m = Mesh("SM_Water_HoseReel_Cart")
    m.add_material("Steel_Cart_Frame", 0.35, 0.58, 0.42)
    m.add_material("Garden_Hose_Green", 0.22, 0.68, 0.32)
    m.add_material("Reel_Drum", 0.20, 0.22, 0.24)
    m.add_material("Rubber_Tires", 0.15, 0.15, 0.16)
    m.add_material("Brass_Handle", 0.85, 0.70, 0.25)

    # 2 pneumatic rubber wheels & axle
    for y in [-24, 24]:
        m.add_cylinder(r0=10, r1=10, h=6, z0=10, segs=8, mat="Rubber_Tires", c0=(12, y), c1=(12, y))
    m.add_cylinder(r0=1.8, r1=1.8, h=52, z0=10, segs=6, mat="Steel_Cart_Frame", c0=(12, -26), c1=(12, 26))

    # Front foot stand
    m.add_box((4, 38, 20), center=(-16, 0, 10), mat="Steel_Cart_Frame")

    # U-shaped handle bars rising to 85cm
    m.add_cylinder(r0=2, r1=2, h=75, z0=10, segs=6, mat="Steel_Cart_Frame", c0=(10, -18), c1=(-10, -18))
    m.add_cylinder(r0=2, r1=2, h=75, z0=10, segs=6, mat="Steel_Cart_Frame", c0=(10,  18), c1=(-10,  18))
    m.add_box((4, 40, 4), center=(-10, 0, 85), mat="Steel_Cart_Frame")

    # Centered rotating hose reel with 100ft coiled green garden hose
    m.add_cylinder(r0=22, r1=22, h=28, z0=45, segs=12, mat="Garden_Hose_Green", c0=(0, -14), c1=(0, 14))
    m.add_cylinder(r0=24, r1=24, h=3, z0=45, segs=12, mat="Reel_Drum", c0=(0, -16), c1=(0, -16))
    m.add_cylinder(r0=24, r1=24, h=3, z0=45, segs=12, mat="Reel_Drum", c0=(0,  16), c1=(0,  16))

    # Crank handle on side
    m.add_box((4, 12, 3), center=(0, 22, 45), mat="Brass_Handle")
    return m

def build_trough_stock_100gal():
    m = Mesh("SM_Water_Trough_Stock_100gal")
    m.add_material("Galvanized_Zinc", 0.72, 0.74, 0.76)
    m.add_material("Water_Surface", 0.20, 0.55, 0.75)
    m.add_material("Brass_Float_Valve", 0.85, 0.70, 0.25)

    # Galvanized oval corrugated stock tank (140cm long, 70cm wide, 60cm deep)
    m.add_box((68, 138, 58), center=(0, 0, 29), mat="Galvanized_Zinc")
    # Rolled rim lip
    m.add_box((72, 142, 4), center=(0, 0, 58), mat="Galvanized_Zinc")

    # Clear blue water surface filling trough to 50cm
    m.add_box((62, 132, 2), center=(0, 0, 50), mat="Water_Surface")

    # Protected corner float valve assembly & float ball
    m.add_box((16, 16, 20), center=(24, 56, 48), mat="Galvanized_Zinc")
    m.add_cylinder(r0=5, r1=5, h=6, z0=46, segs=8, mat="Brass_Float_Valve", c0=(20, 42), c1=(20, 42))
    return m

# =============================================================================
# SEWAGE & COMPOST ASSETS (4)
# =============================================================================

def build_septic_tank_poly_500gal():
    m = Mesh("SM_Sewage_SepticTank_Poly_500gal")
    m.add_material("Septic_Poly_Yellow", 0.75, 0.65, 0.20)
    m.add_material("Riser_Lid_Green", 0.22, 0.50, 0.25)
    m.add_material("PVC_Inlet", 0.90, 0.90, 0.92)

    # 1.2m x 2.2m x 1.3m ribbed structural polyethylene septic tank
    # 7 heavy structural reinforcement ribs along Y axis
    for y in range(-90, 100, 30):
        m.add_cylinder(r0=58, r1=60, h=14, z0=0, segs=12, mat="Septic_Poly_Yellow", c0=(0, y), c1=(0, y))
        m.add_cylinder(r0=60, r1=58, h=14, z0=14, segs=12, mat="Septic_Poly_Yellow", c0=(0, y), c1=(0, y))

    # Dual 24-inch green inspection riser collars & lids
    m.add_cylinder(r0=30, r1=30, h=25, z0=85, segs=12, mat="Riser_Lid_Green", c0=(0, -60), c1=(0, -60))
    m.add_cylinder(r0=32, r1=32, h=4, z0=110, segs=12, mat="Riser_Lid_Green", c0=(0, -60), c1=(0, -60))

    m.add_cylinder(r0=30, r1=30, h=25, z0=85, segs=12, mat="Riser_Lid_Green", c0=(0,  60), c1=(0,  60))
    m.add_cylinder(r0=32, r1=32, h=4, z0=110, segs=12, mat="Riser_Lid_Green", c0=(0,  60), c1=(0,  60))

    # 4" Sanitary PVC inlet (-Y) and outlet (+Y) tees
    m.add_cylinder(r0=5, r1=5, h=16, z0=65, segs=6, mat="PVC_Inlet", c0=(0, -105), c1=(0, -121))
    m.add_cylinder(r0=5, r1=5, h=16, z0=58, segs=6, mat="PVC_Inlet", c0=(0,  105), c1=(0,  121))
    return m

def build_distribution_box():
    m = Mesh("SM_Sewage_DistributionBox")
    m.add_material("Concrete_Grey", 0.65, 0.64, 0.62)
    m.add_material("Plastic_Baffles", 0.90, 0.88, 0.85)

    # 50x50x45cm precast concrete septic distribution box
    m.add_box((50, 50, 38), center=(0, 0, 19), mat="Concrete_Grey")
    # Beveled concrete inspection lid with center lift handle
    m.add_box((52, 52, 6), center=(0, 0, 41), mat="Concrete_Grey")
    m.add_box((12, 3, 4), center=(0, 0, 46), mat="Concrete_Grey")

    # 1 Inlet hole (-Y) and 3 outlet holes (+Y, -X, +X) with flow levelers
    m.add_cylinder(r0=5, r1=5, h=6, z0=20, segs=6, mat="Plastic_Baffles", c0=(0, -25), c1=(0, -29))
    m.add_cylinder(r0=5, r1=5, h=6, z0=15, segs=6, mat="Plastic_Baffles", c0=(0,  25), c1=(0,  29))
    m.add_cylinder(r0=5, r1=5, h=6, z0=15, segs=6, mat="Plastic_Baffles", c0=(-25, 0), c1=(-29, 0))
    m.add_cylinder(r0=5, r1=5, h=6, z0=15, segs=6, mat="Plastic_Baffles", c0=( 25, 0), c1=( 29, 0))
    return m

def build_compost_bin_3bay():
    m = Mesh("SM_Sewage_CompostBin_3Bay")
    m.add_material("Cedar_Wood", 0.58, 0.40, 0.26)
    m.add_material("Compost_Fresh", 0.35, 0.45, 0.20)
    m.add_material("Compost_Active", 0.32, 0.24, 0.16)
    m.add_material("Compost_Finished", 0.22, 0.18, 0.14)

    # 1x2.8m 3-Bay cedar compost enclosure (110cm tall)
    # 4 Vertical corner/divider posts (4x4 treated)
    for x in [-135, -45, 45, 135]:
        m.add_box((10, 10, 110), center=(x, -45, 55), mat="Cedar_Wood")
        m.add_box((10, 10, 110), center=(x,  45, 55), mat="Cedar_Wood")
        # Side wall slats
        for z in range(10, 110, 18):
            m.add_box((6, 90, 12), center=(x, 0, z), mat="Cedar_Wood")

    # Rear slatted wall across all 3 bays
    for z in range(10, 110, 18):
        m.add_box((270, 6, 12), center=(0, 45, z), mat="Cedar_Wood")

    # Bay 1 (Fresh green waste)
    m.add_box((80, 80, 65), center=(-90, 0, 32.5), mat="Compost_Fresh")
    # Bay 2 (Active cooking heap)
    m.add_box((80, 80, 50), center=(  0, 0, 25), mat="Compost_Active")
    # Bay 3 (Finished rich black humus)
    m.add_box((80, 80, 35), center=( 90, 0, 17.5), mat="Compost_Finished")
    return m

def build_toilet_composting():
    m = Mesh("SM_Sewage_Toilet_Composting")
    m.add_material("White_Porcelain", 0.95, 0.95, 0.96)
    m.add_material("Rustic_Cedar", 0.55, 0.38, 0.25)
    m.add_material("Exhaust_Vent", 0.35, 0.35, 0.38)
    m.add_material("Agitator_Handle", 0.70, 0.70, 0.72)

    # Rustic cedar cabinet pedestal (55x65x45cm)
    m.add_box((55, 65, 45), center=(0, 0, 22.5), mat="Rustic_Cedar")

    # Ergonomic molded toilet bowl and closed lid
    m.add_cylinder(r0=18, r1=20, h=30, z0=45, segs=10, mat="White_Porcelain")
    m.add_cylinder(r0=20, r1=20, h=4, z0=75, segs=10, mat="Rustic_Cedar")

    # Side peat moss crank agitator handle
    m.add_cylinder(r0=2, r1=2, h=10, z0=25, segs=6, mat="Agitator_Handle", c0=(27, 0), c1=(37, 0))
    m.add_box((3, 14, 3), center=(38, 0, 30), mat="Agitator_Handle")

    # Rear 12V ventilation fan duct pipe
    m.add_cylinder(r0=3.5, r1=3.5, h=55, z0=30, segs=8, mat="Exhaust_Vent", c0=(0, 28), c1=(0, 28))
    return m

# =============================================================================
# INTERNET & TELECOM ASSETS (5)
# =============================================================================

def build_dish_starlink_tripod():
    m = Mesh("SM_Internet_Dish_Starlink_Tripod")
    m.add_material("Dish_White", 0.96, 0.96, 0.97)
    m.add_material("Tripod_Grey", 0.30, 0.32, 0.35)
    m.add_material("Ethernet_Cable", 0.15, 0.15, 0.16)

    # 4-legged aluminum ground tripod base (60x60cm spread)
    for a in [45, 135, 225, 315]:
        rad = math.radians(a)
        m.add_cylinder(r0=2, r1=1.5, h=25, z0=0, segs=6, mat="Tripod_Grey",
                       c0=(math.cos(rad)*30, math.sin(rad)*30), c1=(0, 0))
    # Center collar & mast
    m.add_cylinder(r0=3, r1=3, h=35, z0=20, segs=8, mat="Tripod_Grey")

    # Rectangular phased-array satellite dish antenna (50x30cm tilted ~40 deg toward North +Y)
    p_bl = Vec3(-25, -12, 55)
    p_br = Vec3( 25, -12, 55)
    p_tr = Vec3( 25,  12, 75)
    p_tl = Vec3(-25,  12, 75)
    m.add_quad(p_bl, p_br, p_tr, p_tl, mat="Dish_White")
    m.add_box((52, 26, 4), center=(0, 0, 65), mat="Dish_White")

    # Coiled high-speed Cat6 router cable
    m.add_cylinder(r0=8, r1=8, h=4, z0=2, segs=8, mat="Ethernet_Cable", c0=(12, 10), c1=(12, 10))
    return m

def build_dish_highperf_mast():
    m = Mesh("SM_Internet_Dish_HighPerf_Mast")
    m.add_material("Mast_Galvanized", 0.65, 0.68, 0.70)
    m.add_material("HighPerf_Dish", 0.94, 0.95, 0.96)
    m.add_material("Mount_Brackets", 0.25, 0.28, 0.30)

    # J-mast wall/roof mount bracket
    m.add_box((20, 20, 6), center=(0, 0, 3), mat="Mount_Brackets")
    m.add_cylinder(r0=3.5, r1=3.5, h=200, z0=3, segs=8, mat="Mast_Galvanized")

    # Heavy-duty parabolic round dish (Diameter 75cm, depth 15cm)
    m.add_cone(r=37.5, h=-12, z0=200, segs=12, mat="HighPerf_Dish", c=(0, -8))

    # Feed horn sub-reflector support arms
    m.add_cylinder(r0=1.2, r1=1.2, h=25, z0=190, segs=6, mat="Mount_Brackets", c0=(0, -8), c1=(0, -32))
    m.add_box((8, 8, 8), center=(0, -32, 190), mat="Mount_Brackets")
    return m

def build_antenna_yagi_mast():
    m = Mesh("SM_Internet_Antenna_Yagi_Mast")
    m.add_material("Mast_Steel", 0.60, 0.62, 0.65)
    m.add_material("Aluminum_Elements", 0.85, 0.86, 0.88)
    m.add_material("Enclosure_Box", 0.90, 0.90, 0.92)

    # 3.5m telescoping galvanized pipe mast
    m.add_cylinder(r0=4.5, r1=3, h=330, z0=0, segs=8, mat="Mast_Steel")

    # Horizontal directional Yagi boom (85cm long along Y)
    m.add_box((3, 85, 3), center=(0, 0, 330), mat="Aluminum_Elements")

    # 7 graduated cross director/reflector elements
    element_lengths = [40, 36, 32, 28, 26, 24, 22]
    for idx, el_w in enumerate(element_lengths):
        y_pos = -38 + idx * 12
        m.add_box((el_w, 2, 2), center=(0, y_pos, 330), mat="Aluminum_Elements")

    # Weatherproof junction box & mast clamps
    m.add_box((12, 14, 16), center=(0, 0, 315), mat="Enclosure_Box")
    return m

def build_antenna_omni_cellular():
    m = Mesh("SM_Internet_Antenna_Omni_Cellular")
    m.add_material("Fiberglass_White", 0.92, 0.92, 0.94)
    m.add_material("Stainless_Bracket", 0.75, 0.76, 0.78)
    m.add_material("Coaxial_Cable", 0.15, 0.15, 0.16)

    # Heavy U-bolt mounting bracket
    m.add_box((18, 18, 25), center=(0, 0, 45), mat="Stainless_Bracket")
    m.add_cylinder(r0=3, r1=3, h=60, z0=0, segs=6, mat="Stainless_Bracket")

    # Long vertical high-gain omnidirectional stick antenna (Diameter 5cm, Height 220cm)
    m.add_cylinder(r0=2.5, r1=2.2, h=220, z0=60, segs=8, mat="Fiberglass_White")
    m.add_cone(r=2.2, h=5, z0=280, segs=8, mat="Fiberglass_White")

    # LMR-400 black low-loss coaxial pigtail line
    m.add_cylinder(r0=1, r1=1, h=35, z0=15, segs=6, mat="Coaxial_Cable", c0=(0, -4), c1=(6, -15))
    return m

def build_outdoor_ap_pole():
    m = Mesh("SM_Internet_Outdoor_AP_Pole")
    m.add_material("Weatherproof_UV", 0.94, 0.94, 0.95)
    m.add_material("Steel_Mount", 0.55, 0.58, 0.60)
    m.add_material("Dual_Antennas", 0.18, 0.20, 0.22)
    m.add_material("LED_Blue", 0.20, 0.65, 0.95)

    # Treated timber pole stub / fence post mount
    m.add_cylinder(r0=6, r1=6, h=140, z0=0, segs=8, mat="Steel_Mount")

    # Weatherproof outdoor PoE access point enclosure (18x12x25cm)
    m.add_box((18, 12, 25), center=(0, -8, 145), mat="Weatherproof_UV")

    # Dual omni dipole tilt antennas on top
    m.add_cylinder(r0=1.2, r1=1, h=28, z0=157, segs=6, mat="Dual_Antennas", c0=(-6, -8), c1=(-10, -8))
    m.add_cylinder(r0=1.2, r1=1, h=28, z0=157, segs=6, mat="Dual_Antennas", c0=( 6, -8), c1=( 10, -8))

    # Center LED status light on front (-Y)
    m.add_cylinder(r0=1.5, r1=1.5, h=2, z0=145, segs=6, mat="LED_Blue", c0=(0, -14), c1=(0, -14))
    return m

# =============================================================================
# REGISTRY & BATCH RUNNER
# =============================================================================

UTILITIES_REGISTRY = [
    # Electricity (11)
    ("SM_Electric_SolarPanel_Ground_1m", build_solar_panel_ground_1m, "1x1m", "100W ground-mount tilted solar panel on galvanized frame"),
    ("SM_Electric_SolarArray_3m", build_solar_array_3m, "3x2m", "Commercial 3-panel off-grid solar array on concrete piers"),
    ("SM_Electric_WindTurbine_Small", build_wind_turbine_small, "1x1m", "400W 3-blade wind turbine with tail vane on 4.5m guyed mast"),
    ("SM_Electric_WindTurbine_Large", build_wind_turbine_large, "1.2x1.2m", "3kW heavy-duty wind turbine on 8m lattice steel tower"),
    ("SM_Electric_Generator_Portable", build_generator_portable, "0.6x0.5m", "Gas portable inverter generator with steel roll cage"),
    ("SM_Electric_Generator_Standby", build_generator_standby, "1.2x0.8m", "Commercial diesel backup genset on concrete pad"),
    ("SM_Electric_Battery_Powerwall", build_battery_powerwall, "0.8x0.3m", "Wall-mounted 10kWh home energy storage battery"),
    ("SM_Electric_Battery_Rack_48V", build_battery_rack_48v, "0.6x0.6m", "4-module 48V server rack lithium battery bank"),
    ("SM_Electric_Inverter_Wall", build_inverter_wall, "0.5x0.2m", "Pure sine wave off-grid hybrid inverter charger"),
    ("SM_Electric_PowerPole_Wood", build_power_pole_wood, "0.3x0.3m", "Creosote utility power pole with crossarm & insulators (6.5m)"),
    ("SM_Electric_WireSpool_Wood", build_wire_spool_wood, "0.8x0.8m", "Heavy wooden electrical cable reel with copper wiring"),

    # Water (8)
    ("SM_Water_RainBarrel_55gal", build_rain_barrel_55gal, "0.6x0.6m", "55-gallon blue poly rain barrel on cinder pedestal"),
    ("SM_Water_IBC_Tote_275gal", build_ibc_tote_275gal, "1x1.2m", "275-gallon caged IBC water tote on pallet base"),
    ("SM_Water_Cistern_Poly_1000gal", build_cistern_poly_1000gal, "1.8x1.8m", "1000-gallon heavy ribbed dark green poly water cistern"),
    ("SM_Water_WellPump_Manual", build_well_pump_manual, "0.8x0.8m", "Cast-iron pitcher pump on octagonal timber well cover"),
    ("SM_Water_PressureTank_Well", build_pressure_tank_well, "0.5x0.5m", "Vertical bladder pressure tank with mounted jet pump"),
    ("SM_Water_FilterRack_3Stage", build_filter_rack_3stage, "0.6x0.3m", "3-stage Big Blue sediment and carbon filtration rack"),
    ("SM_Water_HoseReel_Cart", build_hose_reel_cart, "0.6x0.5m", "Portable wheeled hose reel cart with 100ft green hose"),
    ("SM_Water_Trough_Stock_100gal", build_trough_stock_100gal, "0.7x1.4m", "Galvanized oval livestock drinking trough with float valve"),

    # Sewage & Waste (4)
    ("SM_Sewage_SepticTank_Poly_500gal", build_septic_tank_poly_500gal, "1.2x2.2m", "500-gallon ribbed polyethylene septic tank with dual risers"),
    ("SM_Sewage_DistributionBox", build_distribution_box, "0.5x0.5m", "Precast concrete septic distribution box with inspection lid"),
    ("SM_Sewage_CompostBin_3Bay", build_compost_bin_3bay, "1x2.8m", "3-bay cedar timber homestead compost station"),
    ("SM_Sewage_Toilet_Composting", build_toilet_composting, "0.6x0.7m", "Self-contained rustic cedar composting toilet with agitator"),

    # Internet & Telecom (5)
    ("SM_Internet_Dish_Starlink_Tripod", build_dish_starlink_tripod, "0.6x0.6m", "Rectangular phased-array satellite dish on ground tripod"),
    ("SM_Internet_Dish_HighPerf_Mast", build_dish_highperf_mast, "0.8x0.8m", "High-performance round satellite dish on tall galvanized J-mast"),
    ("SM_Internet_Antenna_Yagi_Mast", build_antenna_yagi_mast, "0.4x0.9m", "Directional cellular Yagi antenna array on 3.5m mast"),
    ("SM_Internet_Antenna_Omni_Cellular", build_antenna_omni_cellular, "0.3x0.3m", "Vertical fiberglass high-gain cellular omni antenna"),
    ("SM_Internet_Outdoor_AP_Pole", build_outdoor_ap_pole, "0.3x0.3m", "Weatherproof outdoor dual-antenna PoE Wi-Fi access point"),
]

def main():
    print("=================================================================")
    print(f"HOMESTEADER UTILITIES & INFRASTRUCTURE 3D ASSET GENERATOR")
    print(f"Total Assets: {len(UTILITIES_REGISTRY)}")
    print(f"Models: {HUD_MODELS}")
    print(f"Icons:  {HUD_ICONS}")
    print("=================================================================\n")

    count = 0
    for name, func, footprint, desc in UTILITIES_REGISTRY:
        count += 1
        mesh = func()
        mesh.ground_align()
        tri_count = len(mesh.faces)
        vert_count = len(mesh.vertices)

        # 1. Save HUD models
        hud_obj = os.path.join(HUD_MODELS, f"{name}.obj")
        hud_mtl = os.path.join(HUD_MODELS, f"{name}.mtl")
        mesh.save_obj(hud_obj, hud_mtl)

        # 2. Sync to UE5
        ue5_obj = os.path.join(UE5_MODELS, f"{name}.obj")
        ue5_mtl = os.path.join(UE5_MODELS, f"{name}.mtl")
        shutil.copy2(hud_obj, ue5_obj)
        shutil.copy2(hud_mtl, ue5_mtl)

        # 3. Render 128x128 Preview Icon
        icon_img = render_icon(mesh, output_size=128, max_dim=96)
        hud_icon = os.path.join(HUD_ICONS, f"{name}.png")
        ue5_icon = os.path.join(UE5_ICONS, f"{name}.png")
        icon_img.save(hud_icon, "PNG")
        icon_img.save(ue5_icon, "PNG")

        print(f"[{count:02d}/{len(UTILITIES_REGISTRY)}] Generated {name} ({footprint}) - {tri_count} tris")

    print("\nSUCCESS: All 28 Utilities models and icons generated and synced across workspaces!")

if __name__ == "__main__":
    main()
