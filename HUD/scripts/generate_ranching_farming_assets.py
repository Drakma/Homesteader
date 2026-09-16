"""
Homesteader 3D Ranching, Livestock & Farming Asset Generator
Creates 33 low-poly 3D models (.obj + .mtl) and 128x128 preview icons:
- Livestock (Adults & Babies): Cow, Calf, Sheep, Lamb, Goat, Kid, Pig, Piglet, Hen, Chick
- Ranching Feed & Fencing: Round & square hay/straw/silage bales, feed pans, salt licks, wood & wire fence, metal gate, solar fence charger
- Crops & Farm Tools: Corn stalk, tomato vine cage, wheat bundle, potato plant, carrot patch, pumpkin patch, cabbage, sunflower, wheelbarrow, seed bag, produce crate, sprinkler riser

Output directories:
  HUD/assets/ranching/models/ & icons/
  HUD/assets/farming/models/ & icons/
  Homesteader/Content/Homesteader/Assets/Ranching/Meshes/ & UI/Icons/Ranching/
  Homesteader/Content/Homesteader/Assets/Farming/Meshes/ & UI/Icons/Farming/
"""

import os
import math
import shutil
from PIL import Image, ImageDraw, ImageFilter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

HUD_RANCH_MODELS = os.path.join(PROJECT_ROOT, "HUD", "assets", "ranching", "models")
HUD_RANCH_ICONS  = os.path.join(PROJECT_ROOT, "HUD", "assets", "ranching", "icons")
HUD_FARM_MODELS  = os.path.join(PROJECT_ROOT, "HUD", "assets", "farming", "models")
HUD_FARM_ICONS   = os.path.join(PROJECT_ROOT, "HUD", "assets", "farming", "icons")

UE5_RANCH_MODELS = os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "Assets", "Ranching", "Meshes")
UE5_RANCH_ICONS  = os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "UI", "Icons", "Ranching")
UE5_FARM_MODELS  = os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "Assets", "Farming", "Meshes")
UE5_FARM_ICONS   = os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "UI", "Icons", "Farming")

for p in [HUD_RANCH_MODELS, HUD_RANCH_ICONS, HUD_FARM_MODELS, HUD_FARM_ICONS,
          UE5_RANCH_MODELS, UE5_RANCH_ICONS, UE5_FARM_MODELS, UE5_FARM_ICONS]:
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

        self.add_quad(p000, p010, p110, p100, mat=mat)
        if top_cap:
            self.add_quad(p001, p101, p111, p011, mat=mat)
        self.add_quad(p000, p100, p101, p001, mat=mat)
        self.add_quad(p110, p010, p011, p111, mat=mat)
        self.add_quad(p010, p000, p001, p011, mat=mat)
        self.add_quad(p100, p110, p111, p101, mat=mat)

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

    def add_foliage_lobe(self, radius, center=(0,0,0), mat="leaves", flatten_z=0.85):
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
                f.write(f"Ks 0.12 0.12 0.12\nNs 12.0\nd 1.0\nillum 2\n\n")

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
# 1. LIVESTOCK ANIMALS (ADULTS & BABIES) (10)
# =============================================================================

def build_animal_cow_adult():
    m = Mesh("SM_Animal_Cow_Adult")
    m.add_material("Cow_Hide_White", 0.92, 0.92, 0.94)
    m.add_material("Cow_Spots_Black", 0.18, 0.18, 0.20)
    m.add_material("Muzzle_Pink", 0.90, 0.65, 0.65)
    m.add_material("Hooves_Horns", 0.75, 0.70, 0.55)

    # Barrel torso (85x150x80cm)
    m.add_box((75, 140, 75), center=(0, 0, 85), mat="Cow_Hide_White", segs_y=2)
    # Spotted patches
    m.add_box((77, 45, 45), center=(0, -20, 92), mat="Cow_Spots_Black")
    m.add_box((77, 40, 40), center=(0,  35, 80), mat="Cow_Spots_Black")

    # 4 stout legs with hooves (height 55cm)
    for lx in [-26, 26]:
        for ly in [-48, 48]:
            m.add_box((16, 16, 45), center=(lx, ly, 30), mat="Cow_Hide_White")
            m.add_box((17, 17, 10), center=(lx, ly, 5), mat="Hooves_Horns")

    # Head and neck (front is -Y)
    m.add_box((34, 42, 45), center=(0, -82, 110), mat="Cow_Hide_White")
    m.add_box((28, 20, 24), center=(0, -100, 98), mat="Muzzle_Pink")

    # Horns & ears
    for hx in [-20, 20]:
        m.add_cylinder(r0=3, r1=1, h=18, z0=125, segs=6, mat="Hooves_Horns", c0=(hx*0.6, -78), c1=(hx*1.3, -76))
        m.add_box((14, 6, 8), center=(hx * 1.5, -75, 115), mat="Cow_Hide_White")
    return m

def build_animal_cow_calf():
    m = Mesh("SM_Animal_Cow_Calf")
    m.add_material("Calf_Brown", 0.65, 0.42, 0.25)
    m.add_material("Muzzle_Pink", 0.90, 0.68, 0.68)
    m.add_material("Hooves", 0.25, 0.22, 0.20)

    # Compact torso (45x80x45cm)
    m.add_box((42, 75, 42), center=(0, 0, 52), mat="Calf_Brown")
    # 4 slender legs
    for lx in [-15, 15]:
        for ly in [-26, 26]:
            m.add_box((10, 10, 32), center=(lx, ly, 20), mat="Calf_Brown")
            m.add_box((11, 11, 6), center=(lx, ly, 3), mat="Hooves")

    # Cute calf head & ears
    m.add_box((24, 28, 28), center=(0, -48, 68), mat="Calf_Brown")
    m.add_box((18, 14, 16), center=(0, -60, 60), mat="Muzzle_Pink")
    m.add_box((12, 4, 6), center=(-16, -44, 72), mat="Calf_Brown")
    m.add_box((12, 4, 6), center=( 16, -44, 72), mat="Calf_Brown")
    return m

def build_animal_sheep_adult():
    m = Mesh("SM_Animal_Sheep_Adult")
    m.add_material("Wool_Cream", 0.90, 0.88, 0.82)
    m.add_material("Face_Black", 0.20, 0.18, 0.18)
    m.add_material("Hooves", 0.15, 0.15, 0.15)

    # Fluffy wool body (60x100x60cm)
    m.add_box((56, 95, 55), center=(0, 0, 58), mat="Wool_Cream", segs_y=2)
    # Wool texture tufts on back
    m.add_box((52, 85, 12), center=(0, 0, 88), mat="Wool_Cream")

    # 4 slender black legs
    for lx in [-18, 18]:
        for ly in [-32, 32]:
            m.add_box((9, 9, 32), center=(lx, ly, 18), mat="Face_Black")
            m.add_box((10, 10, 6), center=(lx, ly, 3), mat="Hooves")

    # Black face & drooping ears (front -Y)
    m.add_box((22, 28, 26), center=(0, -56, 75), mat="Face_Black")
    m.add_box((10, 16, 6), center=(-14, -50, 72), mat="Face_Black")
    m.add_box((10, 16, 6), center=( 14, -50, 72), mat="Face_Black")
    return m

def build_animal_sheep_lamb():
    m = Mesh("SM_Animal_Sheep_Lamb")
    m.add_material("Wool_Cream", 0.92, 0.90, 0.85)
    m.add_material("Face_Black", 0.22, 0.20, 0.20)
    m.add_material("Hooves", 0.15, 0.15, 0.15)

    # Small rounded lamb body
    m.add_box((32, 50, 32), center=(0, 0, 35), mat="Wool_Cream")
    for lx in [-11, 11]:
        for ly in [-18, 18]:
            m.add_box((6, 6, 20), center=(lx, ly, 11), mat="Face_Black")

    # Lamb head
    m.add_box((16, 18, 18), center=(0, -30, 46), mat="Face_Black")
    m.add_box((8, 10, 4), center=(-10, -26, 44), mat="Face_Black")
    m.add_box((8, 10, 4), center=( 10, -26, 44), mat="Face_Black")
    return m

def build_animal_goat_adult():
    m = Mesh("SM_Animal_Goat_Adult")
    m.add_material("Goat_Brown", 0.62, 0.45, 0.32)
    m.add_material("Goat_Belly_White", 0.88, 0.86, 0.82)
    m.add_material("Horns", 0.35, 0.32, 0.28)
    m.add_material("Beard", 0.85, 0.82, 0.78)

    # Angular lean body (48x85x55cm)
    m.add_box((44, 80, 48), center=(0, 0, 55), mat="Goat_Brown")
    m.add_box((40, 65, 12), center=(0, 0, 34), mat="Goat_Belly_White")

    # 4 agile legs
    for lx in [-15, 15]:
        for ly in [-28, 28]:
            m.add_box((8, 8, 35), center=(lx, ly, 18), mat="Goat_Brown")

    # Head and erect ears
    m.add_box((18, 26, 26), center=(0, -48, 75), mat="Goat_Brown")
    # Chin beard
    m.add_box((8, 12, 16), center=(0, -52, 58), mat="Beard")

    # Curved horns arching back (+Y)
    for hx in [-6, 6]:
        m.add_cylinder(r0=2.5, r1=1, h=22, z0=85, segs=6, mat="Horns", c0=(hx, -44), c1=(hx*1.2, -30))
    return m

def build_animal_goat_kid():
    m = Mesh("SM_Animal_Goat_Kid")
    m.add_material("Kid_Spotted", 0.65, 0.48, 0.35)
    m.add_material("Kid_White", 0.90, 0.88, 0.85)

    m.add_box((26, 46, 28), center=(0, 0, 32), mat="Kid_Spotted")
    for lx in [-9, 9]:
        for ly in [-16, 16]:
            m.add_box((5, 5, 20), center=(lx, ly, 10), mat="Kid_White")
    m.add_box((14, 18, 18), center=(0, -28, 44), mat="Kid_Spotted")
    return m

def build_animal_pig_adult():
    m = Mesh("SM_Animal_Pig_Adult")
    m.add_material("Pig_Pink", 0.92, 0.68, 0.68)
    m.add_material("Snout_Dark", 0.88, 0.58, 0.58)
    m.add_material("Hooves", 0.35, 0.28, 0.28)

    # Stout barrel torso (62x120x62cm)
    m.add_box((58, 110, 55), center=(0, 0, 48), mat="Pig_Pink", segs_y=2)

    # 4 short stout legs
    for lx in [-20, 20]:
        for ly in [-38, 38]:
            m.add_box((12, 12, 24), center=(lx, ly, 13), mat="Pig_Pink")
            m.add_box((13, 13, 5), center=(lx, ly, 3), mat="Hooves")

    # Head and disc snout (front -Y)
    m.add_box((32, 34, 32), center=(0, -64, 52), mat="Pig_Pink")
    m.add_cylinder(r0=7, r1=7, h=10, z0=48, segs=8, mat="Snout_Dark", c0=(0, -78), c1=(0, -88))

    # Floppy triangular ears
    m.add_triangle(Vec3(-14, -60, 68), Vec3(-22, -68, 55), Vec3(-6, -68, 55), mat="Pig_Pink")
    m.add_triangle(Vec3( 14, -60, 68), Vec3(  6, -68, 55), Vec3(22, -68, 55), mat="Pig_Pink")
    return m

def build_animal_pig_piglet():
    m = Mesh("SM_Animal_Pig_Piglet")
    m.add_material("Pig_Pink", 0.94, 0.72, 0.72)
    m.add_material("Snout", 0.88, 0.62, 0.62)

    m.add_box((26, 46, 24), center=(0, 0, 22), mat="Pig_Pink")
    for lx in [-9, 9]:
        for ly in [-15, 15]:
            m.add_box((6, 6, 12), center=(lx, ly, 6), mat="Pig_Pink")
    m.add_box((16, 16, 16), center=(0, -28, 25), mat="Pig_Pink")
    m.add_cylinder(r0=3.5, r1=3.5, h=5, z0=22, segs=6, mat="Snout", c0=(0, -36), c1=(0, -41))
    return m

def build_animal_chicken_hen():
    m = Mesh("SM_Animal_Chicken_Hen")
    m.add_material("Feather_Brown", 0.68, 0.35, 0.18)
    m.add_material("Comb_Red", 0.88, 0.18, 0.18)
    m.add_material("Beak_Legs_Yellow", 0.95, 0.75, 0.15)
    m.add_material("Tail_Feather", 0.25, 0.22, 0.20)

    # Rounded feathery body (28x36x28cm)
    m.add_box((26, 34, 26), center=(0, 0, 26), mat="Feather_Brown")

    # Tail plumage arching up & back (+Y)
    m.add_box((12, 16, 18), center=(0, 18, 36), mat="Tail_Feather")

    # Neck, head & red crown comb
    m.add_box((12, 14, 20), center=(0, -16, 36), mat="Feather_Brown")
    m.add_box((4, 12, 8), center=(0, -16, 48), mat="Comb_Red")
    m.add_cone(r=4, h=8, z0=36, segs=6, mat="Beak_Legs_Yellow", c=(0, -24))

    # Two spindly legs and splayed claw feet
    for lx in [-6, 6]:
        m.add_cylinder(r0=1.2, r1=1.2, h=14, z0=0, segs=6, mat="Beak_Legs_Yellow", c0=(lx, 0), c1=(lx, 0))
        m.add_box((8, 8, 2), center=(lx, -2, 1), mat="Beak_Legs_Yellow")
    return m

def build_animal_chicken_chick():
    m = Mesh("SM_Animal_Chicken_Chick")
    m.add_material("Downy_Yellow", 0.96, 0.85, 0.25)
    m.add_material("Beak_Orange", 0.95, 0.50, 0.15)

    m.add_box((12, 14, 12), center=(0, 0, 10), mat="Downy_Yellow")
    m.add_cone(r=2, h=4, z0=10, segs=6, mat="Beak_Orange", c=(0, -8))
    m.add_cylinder(r0=0.8, r1=0.8, h=5, z0=0, segs=6, mat="Beak_Orange", c0=(-2.5, 0), c1=(-2.5, 0))
    m.add_cylinder(r0=0.8, r1=0.8, h=5, z0=0, segs=6, mat="Beak_Orange", c0=( 2.5, 0), c1=( 2.5, 0))
    return m

# =============================================================================
# 2. RANCHING FEED & FENCING (11)
# =============================================================================

def build_hay_bale_round():
    m = Mesh("SM_Ranch_HayBale_Round")
    m.add_material("Hay_Gold", 0.85, 0.68, 0.28)
    m.add_material("Twine_Wrap", 0.72, 0.55, 0.22)

    # 5-foot standard round hay bale (Diameter 150cm, Length 120cm along Y)
    m.add_cylinder(r0=75, r1=75, h=120, z0=0, segs=16, mat="Hay_Gold", c0=(0, -60), c1=(0, 60))

    # 3 twine net wrap compression bands
    for y in [-35, 0, 35]:
        m.add_cylinder(r0=76, r1=76, h=4, z0=0, segs=16, mat="Twine_Wrap", c0=(0, y), c1=(0, y))
    return m

def build_hay_bale_square():
    m = Mesh("SM_Ranch_HayBale_Square")
    m.add_material("Hay_Gold", 0.86, 0.70, 0.30)
    m.add_material("Baling_Twine", 0.20, 0.55, 0.85) # Blue polypropylene twine

    # Standard 2-string rectangular field bale (50x100x40cm)
    m.add_box((50, 100, 40), center=(0, 0, 20), mat="Hay_Gold", segs_y=2)

    # Dual blue twine bands cinching bale at 30% and 70% length
    for y in [-25, 25]:
        m.add_box((52, 2, 42), center=(0, y, 20), mat="Baling_Twine")
    return m

def build_silage_bale_round():
    m = Mesh("SM_Ranch_SilageBale_Round")
    m.add_material("Silage_Wrap_White", 0.94, 0.94, 0.95)
    m.add_material("Wrap_Seam", 0.84, 0.84, 0.86)

    # Heavy white plastic stretch-wrapped round silage bale (D=150cm, L=120cm)
    m.add_cylinder(r0=75, r1=75, h=120, z0=0, segs=16, mat="Silage_Wrap_White", c0=(0, -60), c1=(0, 60))
    for y in [-40, -10, 20]:
        m.add_cylinder(r0=75.5, r1=75.5, h=6, z0=0, segs=16, mat="Wrap_Seam", c0=(0, y), c1=(0, y))
    return m

def build_straw_bale_round():
    m = Mesh("SM_Ranch_StrawBale_Round")
    m.add_material("Straw_Pale", 0.92, 0.80, 0.42)
    m.add_material("Twine", 0.75, 0.65, 0.30)
    m.add_cylinder(r0=75, r1=75, h=120, z0=0, segs=16, mat="Straw_Pale", c0=(0, -60), c1=(0, 60))
    for y in [-35, 35]:
        m.add_cylinder(r0=76, r1=76, h=4, z0=0, segs=16, mat="Twine", c0=(0, y), c1=(0, y))
    return m

def build_straw_bale_square():
    m = Mesh("SM_Ranch_StrawBale_Square")
    m.add_material("Straw_Pale", 0.92, 0.80, 0.42)
    m.add_material("Twine_Orange", 0.95, 0.45, 0.15)
    m.add_box((50, 100, 40), center=(0, 0, 20), mat="Straw_Pale", segs_y=2)
    for y in [-25, 25]:
        m.add_box((52, 2, 42), center=(0, y, 20), mat="Twine_Orange")
    return m

def build_feed_pan_rubber():
    m = Mesh("SM_Ranch_FeedPan_Rubber")
    m.add_material("Heavy_Rubber", 0.16, 0.16, 0.18)
    m.add_material("Grain_Pellets", 0.65, 0.52, 0.32)

    # 15-gallon flexible rubber feed pan (Diameter 55cm, Height 22cm)
    m.add_cylinder(r0=24, r1=28, h=22, z0=0, segs=12, mat="Heavy_Rubber")
    # Rolled rim lip
    m.add_cylinder(r0=28, r1=29, h=3, z0=20, segs=12, mat="Heavy_Rubber")
    # Feed pellet grain inside
    m.add_cylinder(r0=24, r1=24, h=2, z0=14, segs=10, mat="Grain_Pellets")
    return m

def build_salt_lick_block():
    m = Mesh("SM_Ranch_SaltLick_Block")
    m.add_material("Mineral_Salt_Red", 0.78, 0.28, 0.22)
    m.add_material("Timber_Pedestal", 0.52, 0.38, 0.24)

    # 4x4 timber post pedestal (H=45cm)
    m.add_box((16, 16, 45), center=(0, 0, 22.5), mat="Timber_Pedestal")
    m.add_box((32, 32, 5), center=(0, 0, 47.5), mat="Timber_Pedestal")

    # 50lb pressed mineral salt lick cube (26x26x26cm)
    m.add_box((26, 26, 26), center=(0, 0, 63), mat="Mineral_Salt_Red")
    # Center mounting peg
    m.add_cylinder(r0=2.5, r1=2.5, h=30, z0=45, segs=6, mat="Timber_Pedestal")
    return m

def build_fence_wood_1m():
    m = Mesh("SM_Ranch_Fence_Wood_1m")
    m.add_material("Cedar_Plank", 0.58, 0.42, 0.28)

    # 1-meter span post & 3-board ranch fence (H=120cm)
    # Right end post
    m.add_box((12, 12, 130), center=(44, 0, 65), mat="Cedar_Plank")
    # 3 horizontal fence rails
    for z in [35, 70, 105]:
        m.add_box((100, 4, 14), center=(0, -6, z), mat="Cedar_Plank")
    return m

def build_fence_wire_1m():
    m = Mesh("SM_Ranch_Fence_Wire_1m")
    m.add_material("T_Post_Green", 0.20, 0.45, 0.25)
    m.add_material("Barbed_Wire", 0.75, 0.76, 0.78)

    # Steel T-post with spade anchor plate (H=130cm)
    m.add_box((4, 6, 130), center=(45, 0, 65), mat="T_Post_Green")
    m.add_box((14, 4, 16), center=(45, 0, 10), mat="T_Post_Green")

    # 4 strands of barbed wire running across 1m span
    for z in [30, 60, 90, 120]:
        m.add_cylinder(r0=0.8, r1=0.8, h=100, z0=z, segs=4, mat="Barbed_Wire", c0=(-50, 0), c1=(50, 0))
    return m

def build_gate_metal_2m():
    m = Mesh("SM_Ranch_Gate_Metal_2m")
    m.add_material("Gate_Red", 0.82, 0.22, 0.18)
    m.add_material("Hinge_Steel", 0.30, 0.32, 0.35)

    # 2m span 6-bar tubular farm gate (200x120cm)
    # Vertical end stiles
    m.add_cylinder(r0=2.5, r1=2.5, h=120, z0=0, segs=6, mat="Gate_Red", c0=(-95, 0), c1=(-95, 0))
    m.add_cylinder(r0=2.5, r1=2.5, h=120, z0=0, segs=6, mat="Gate_Red", c0=( 95, 0), c1=( 95, 0))
    m.add_cylinder(r0=2.5, r1=2.5, h=120, z0=0, segs=6, mat="Gate_Red", c0=(  0, 0), c1=(  0, 0))

    # 6 horizontal rails
    for z in range(12, 120, 20):
        m.add_cylinder(r0=2, r1=2, h=190, z0=z, segs=6, mat="Gate_Red", c0=(-95, 0), c1=(95, 0))

    # Heavy strap hinges on left stile (-X)
    m.add_box((8, 8, 8), center=(-95, 0, 25), mat="Hinge_Steel")
    m.add_box((8, 8, 8), center=(-95, 0, 105), mat="Hinge_Steel")
    return m

def build_fence_energizer_solar():
    m = Mesh("SM_Ranch_Fence_Energizer_Solar")
    m.add_material("Energizer_Red", 0.85, 0.20, 0.15)
    m.add_material("Solar_Cap", 0.12, 0.18, 0.35)
    m.add_material("T_Post", 0.22, 0.42, 0.25)
    m.add_material("Terminal_Knobs", 0.15, 0.15, 0.16)

    # Mounting T-post
    m.add_box((4, 6, 110), center=(0, 0, 55), mat="T_Post")

    # Solar fence charger box (30x25x35cm)
    m.add_box((28, 24, 32), center=(0, -12, 90), mat="Energizer_Red")

    # Angled top solar panel
    p_bl = Vec3(-13, -23, 106)
    p_br = Vec3( 13, -23, 106)
    p_tr = Vec3( 13,  -1, 118)
    p_tl = Vec3(-13,  -1, 118)
    m.add_quad(p_bl, p_br, p_tr, p_tl, mat="Solar_Cap")

    # Red positive and black ground terminal knobs
    m.add_cylinder(r0=2, r1=2, h=5, z0=78, segs=6, mat="Terminal_Knobs", c0=(-6, -24), c1=(-6, -29))
    m.add_cylinder(r0=2, r1=2, h=5, z0=78, segs=6, mat="Terminal_Knobs", c0=( 6, -24), c1=( 6, -29))
    return m

# =============================================================================
# 3. CROPS & FARMING PROPS (12)
# =============================================================================

def build_crop_corn_stalk():
    m = Mesh("SM_Crop_Corn_Stalk")
    m.add_material("Stalk_Green", 0.35, 0.65, 0.22)
    m.add_material("Corn_Husk", 0.55, 0.75, 0.28)
    m.add_material("Corn_Silk", 0.78, 0.65, 0.30)
    m.add_material("Corn_Tassel", 0.85, 0.75, 0.35)

    # Central segmented corn stalk (H=210cm)
    m.add_cylinder(r0=3, r1=1.8, h=210, z0=0, segs=6, mat="Stalk_Green")

    # Broad arching corn leaves radiating outward
    for a in [20, 110, 200, 290]:
        rad = math.radians(a)
        dx, dy = math.cos(rad), math.sin(rad)
        p0 = Vec3(0, 0, 75)
        p1 = Vec3(dx * 45, dy * 45, 65)
        p2 = Vec3(dx * 35 - dy * 8, dy * 35 + dx * 8, 55)
        m.add_triangle(p0, p1, p2, mat="Stalk_Green")
        m.add_triangle(p0, p2, p1, mat="Stalk_Green")

        q0 = Vec3(0, 0, 135)
        q1 = Vec3(-dx * 42, -dy * 42, 125)
        q2 = Vec3(-dx * 32 + dy * 8, -dy * 32 - dx * 8, 115)
        m.add_triangle(q0, q1, q2, mat="Stalk_Green")
        m.add_triangle(q0, q2, q1, mat="Stalk_Green")

    # 2 mature ears of corn with silks on sides
    m.add_cylinder(r0=4, r1=2.5, h=20, z0=95, segs=6, mat="Corn_Husk", c0=(0, 0), c1=(12, 10))
    m.add_box((3, 3, 6), center=(13, 11, 116), mat="Corn_Silk")

    m.add_cylinder(r0=4, r1=2.5, h=20, z0=115, segs=6, mat="Corn_Husk", c0=(0, 0), c1=(-12, -8))
    m.add_box((3, 3, 6), center=(-13, -9, 136), mat="Corn_Silk")

    # Feathery tassel cluster on top
    m.add_cone(r=8, h=22, z0=210, segs=6, mat="Corn_Tassel")
    return m

def build_crop_tomato_vine():
    m = Mesh("SM_Crop_Tomato_Vine")
    m.add_material("Tomato_Wire_Cage", 0.70, 0.72, 0.74)
    m.add_material("Vine_Foliage", 0.22, 0.52, 0.18)
    m.add_material("Ripe_Tomato", 0.88, 0.18, 0.14)

    # 3-ring galvanized wire tomato cage (H=130cm, spread 60cm)
    for a in [0, 120, 240]:
        rad = math.radians(a)
        m.add_cylinder(r0=1.2, r1=1.2, h=130, z0=0, segs=4, mat="Tomato_Wire_Cage",
                       c0=(math.cos(rad)*20, math.sin(rad)*20),
                       c1=(math.cos(rad)*28, math.sin(rad)*28))
    # 3 horizontal wire rings
    m.add_cylinder(r0=22, r1=22, h=2, z0=35, segs=12, mat="Tomato_Wire_Cage")
    m.add_cylinder(r0=25, r1=25, h=2, z0=75, segs=12, mat="Tomato_Wire_Cage")
    m.add_cylinder(r0=28, r1=28, h=2, z0=115, segs=12, mat="Tomato_Wire_Cage")

    # Dense lush vine lobes filling the cage
    m.add_foliage_lobe(radius=28, center=(0, 0, 50), mat="Vine_Foliage")
    m.add_foliage_lobe(radius=26, center=(5, -5, 85), mat="Vine_Foliage")
    m.add_foliage_lobe(radius=22, center=(-4, 6, 110), mat="Vine_Foliage")

    # 6 Ripe red heirloom tomatoes peeking through foliage
    tom_locs = [(-16, -14, 45), (14, -15, 52), (18, 12, 60), (-14, 15, 78), (2, -18, 88), (-8, -12, 105)]
    for tx, ty, tz in tom_locs:
        m.add_foliage_lobe(radius=5.5, center=(tx, ty, tz), mat="Ripe_Tomato", flatten_z=1.0)
    return m

def build_crop_wheat_bundle():
    m = Mesh("SM_Crop_Wheat_Bundle")
    m.add_material("Wheat_Gold", 0.90, 0.74, 0.32)
    m.add_material("Wheat_Amber", 0.82, 0.62, 0.24)

    # Clump of 12 splayed golden wheat stems with grain heads (H=95cm)
    for a in range(0, 360, 30):
        rad = math.radians(a)
        dx = math.cos(rad) * 16
        dy = math.sin(rad) * 16
        m.add_cylinder(r0=1, r1=0.8, h=75, z0=0, segs=4, mat="Wheat_Amber", c0=(0, 0), c1=(dx, dy))
        # Beaded grain spikelet head with beard awns
        m.add_cylinder(r0=3, r1=1.5, h=20, z0=75, segs=6, mat="Wheat_Gold", c0=(dx, dy), c1=(dx * 1.2, dy * 1.2))
    return m

def build_crop_potato_plant():
    m = Mesh("SM_Crop_Potato_Plant")
    m.add_material("Potato_Leaf_Dark", 0.20, 0.48, 0.18)
    m.add_material("Potato_Leaf_Light", 0.32, 0.62, 0.22)
    m.add_material("Dirt_Mound", 0.45, 0.32, 0.20)

    # Hilled dirt mound (55x55x15cm)
    m.add_cylinder(r0=28, r1=20, h=15, z0=0, segs=10, mat="Dirt_Mound")

    # Lush spreading compound leaves (H=45cm)
    m.add_foliage_lobe(radius=24, center=(0, 0, 26), mat="Potato_Leaf_Dark", flatten_z=0.7)
    m.add_foliage_lobe(radius=18, center=(-12, 10, 32), mat="Potato_Leaf_Light", flatten_z=0.7)
    m.add_foliage_lobe(radius=18, center=( 12, -8, 32), mat="Potato_Leaf_Light", flatten_z=0.7)
    return m

def build_crop_carrot_patch():
    m = Mesh("SM_Crop_Carrot_Patch")
    m.add_material("Carrot_Orange", 0.95, 0.48, 0.12)
    m.add_material("Fronds_Lace", 0.28, 0.68, 0.22)
    m.add_material("Soil", 0.42, 0.30, 0.18)

    # Garden bed soil patch
    m.add_box((45, 45, 8), center=(0, 0, 4), mat="Soil")

    # 4 Carrots in a row with orange root crowns crowned at surface
    offsets = [(-14, -14), (-14, 14), (14, -14), (14, 14)]
    for ox, oy in offsets:
        # Orange carrot shoulder poking above ground
        m.add_cylinder(r0=4, r1=3.5, h=5, z0=8, segs=6, mat="Carrot_Orange", c0=(ox, oy), c1=(ox, oy))
        # Feathery lacy foliage fronds
        m.add_cone(r=10, h=24, z0=12, segs=6, mat="Fronds_Lace", c=(ox, oy))
    return m

def build_crop_pumpkin_patch():
    m = Mesh("SM_Crop_Pumpkin_Patch")
    m.add_material("Pumpkin_Orange", 0.94, 0.42, 0.10)
    m.add_material("Stem_Wood", 0.45, 0.38, 0.20)
    m.add_material("Vine_Leaf", 0.24, 0.52, 0.18)

    # Large ribbed orange pumpkin (D=48cm, H=34cm)
    m.add_cylinder(r0=20, r1=24, h=14, z0=0, segs=12, mat="Pumpkin_Orange")
    m.add_cylinder(r0=24, r1=18, h=18, z0=14, segs=12, mat="Pumpkin_Orange")
    # Twisted woody stem handle
    m.add_cylinder(r0=3, r1=2, h=10, z0=30, segs=6, mat="Stem_Wood", c0=(0, 0), c1=(4, -3))

    # Trailing vine runners and broad fan leaves
    m.add_cylinder(r0=2, r1=2, h=65, z0=2, segs=4, mat="Vine_Leaf", c0=(-30, -25), c1=(25, 30))
    m.add_foliage_lobe(radius=15, center=(-28, -22, 10), mat="Vine_Leaf", flatten_z=0.4)
    m.add_foliage_lobe(radius=16, center=( 26,  24, 10), mat="Vine_Leaf", flatten_z=0.4)
    return m

def build_crop_cabbage_head():
    m = Mesh("SM_Crop_Cabbage_Head")
    m.add_material("Cabbage_Heart", 0.72, 0.88, 0.55)
    m.add_material("Cabbage_Outer", 0.40, 0.70, 0.35)

    # Dense layered head of homestead cabbage (D=45cm, H=28cm)
    m.add_foliage_lobe(radius=18, center=(0, 0, 16), mat="Cabbage_Heart", flatten_z=0.85)

    # Crinkled rosette outer collar leaves spreading outward
    for a in [0, 60, 120, 180, 240, 300]:
        rad = math.radians(a)
        cx = math.cos(rad) * 16
        cy = math.sin(rad) * 16
        m.add_foliage_lobe(radius=12, center=(cx, cy, 6), mat="Cabbage_Outer", flatten_z=0.35)
    return m

def build_crop_sunflower_stalk():
    m = Mesh("SM_Crop_Sunflower_Stalk")
    m.add_material("Stalk_Green", 0.32, 0.62, 0.20)
    m.add_material("Petals_Yellow", 0.96, 0.82, 0.15)
    m.add_material("Seed_Center", 0.28, 0.20, 0.12)

    # Stout vertical hairy stalk (H=240cm)
    m.add_cylinder(r0=4, r1=2.5, h=230, z0=0, segs=8, mat="Stalk_Green")

    # Broad spade-shaped heart leaves
    for z, angle in [(80, 45), (130, 225), (180, 135)]:
        rad = math.radians(angle)
        dx, dy = math.cos(rad) * 28, math.sin(rad) * 28
        m.add_triangle(Vec3(0,0,z), Vec3(dx, dy, z-10), Vec3(dx+dy*0.3, dy-dx*0.3, z-15), mat="Stalk_Green")
        m.add_triangle(Vec3(0,0,z), Vec3(dx+dy*0.3, dy-dx*0.3, z-15), Vec3(dx, dy, z-10), mat="Stalk_Green")

    # Huge disc flower facing South (-Y) tilted slightly upward
    # Dark brown seed center
    m.add_cylinder(r0=18, r1=18, h=6, z0=220, segs=12, mat="Seed_Center", c0=(0, -5), c1=(0, -11))

    # Radiating golden ray petals
    m.add_cylinder(r0=28, r1=28, h=2, z0=220, segs=16, mat="Petals_Yellow", c0=(0, -7), c1=(0, -9))
    return m

def build_farm_wheelbarrow():
    m = Mesh("SM_Farm_Wheelbarrow")
    m.add_material("Steel_Tray_Blue", 0.22, 0.42, 0.68)
    m.add_material("Timber_Handles", 0.55, 0.38, 0.22)
    m.add_material("Rubber_Tire", 0.16, 0.16, 0.18)
    m.add_material("Steel_Hardware", 0.40, 0.40, 0.42)

    # Front pneumatic wheel (D=36cm)
    m.add_cylinder(r0=18, r1=18, h=8, z0=18, segs=10, mat="Rubber_Tire", c0=(0, -60), c1=(0, -60))

    # Dual wooden handle beams extending to user (+Y)
    for hx in [-18, 18]:
        m.add_cylinder(r0=2.5, r1=2.5, h=140, z0=22, segs=6, mat="Timber_Handles",
                       c0=(hx*0.4, -60), c1=(hx*1.4, 75))

    # Front wheel axle & tray support brackets
    m.add_cylinder(r0=1.5, r1=1.5, h=22, z0=18, segs=6, mat="Steel_Hardware", c0=(-11, -60), c1=(11, -60))
    # Two rear support legs
    for lx in [-22, 22]:
        m.add_box((3, 3, 28), center=(lx, 20, 14), mat="Steel_Hardware")

    # Flared contractor steel hopper tray (65x90x32cm)
    m.add_box((58, 80, 28), center=(0, -10, 42), mat="Steel_Tray_Blue")
    return m

def build_farm_seed_bag():
    m = Mesh("SM_Farm_SeedBag_Burlap")
    m.add_material("Burlap_Jute", 0.72, 0.60, 0.42)
    m.add_material("Tied_Rope", 0.88, 0.80, 0.60)
    m.add_material("Stamp_Ink", 0.25, 0.40, 0.25)

    # Bulging burlap sack of heirloom grain (40x55x30cm)
    m.add_cylinder(r0=18, r1=19, h=25, z0=0, segs=10, mat="Burlap_Jute")
    m.add_cylinder(r0=19, r1=15, h=20, z0=25, segs=10, mat="Burlap_Jute")

    # Cinched neck with tied hemp twine
    m.add_cylinder(r0=8, r1=8, h=5, z0=44, segs=8, mat="Tied_Rope")
    # Flared ruffled burlap top
    m.add_cylinder(r0=8, r1=12, h=8, z0=48, segs=8, mat="Burlap_Jute")

    # Green stencil logo stamp on front
    m.add_box((16, 2, 16), center=(0, -18.5, 24), mat="Stamp_Ink")
    return m

def build_farm_produce_crate():
    m = Mesh("SM_Farm_ProduceCrate_Wood")
    m.add_material("Cedar_Slats", 0.62, 0.48, 0.32)
    m.add_material("Produce_Apples", 0.88, 0.20, 0.16)

    # Slotted cedar harvesting bushel crate (40x60x30cm)
    # 4 Corner triangular cleats
    for cx in [-18, 18]:
        for cy in [-28, 28]:
            m.add_box((4, 4, 28), center=(cx, cy, 14), mat="Cedar_Slats")

    # Bottom solid floor
    m.add_box((38, 58, 2), center=(0, 0, 2), mat="Cedar_Slats")

    # Side wall ventilation slats
    for z in [6, 15, 24]:
        m.add_box((40, 2, 6), center=(0, -29, z), mat="Cedar_Slats")
        m.add_box((40, 2, 6), center=(0,  29, z), mat="Cedar_Slats")
        m.add_box((2, 60, 6), center=(-19, 0, z), mat="Cedar_Slats")
        m.add_box((2, 60, 6), center=( 19, 0, z), mat="Cedar_Slats")

    # Heaped freshly harvested red apples inside
    for ax in [-10, 0, 10]:
        for ay in [-18, 0, 18]:
            m.add_foliage_lobe(radius=5.5, center=(ax, ay, 20), mat="Produce_Apples")
    return m

def build_irrigation_sprinkler_riser():
    m = Mesh("SM_Farm_Irrigation_Sprinkler_Riser")
    m.add_material("PVC_Pipe_White", 0.90, 0.90, 0.92)
    m.add_material("Brass_Impact_Head", 0.85, 0.70, 0.25)
    m.add_material("Ground_Spike", 0.25, 0.25, 0.28)

    # Galvanized ground step-in stabilizer spike
    m.add_cylinder(r0=2, r1=0.5, h=25, z0=-25, segs=6, mat="Ground_Spike")
    m.add_box((18, 4, 4), center=(0, 0, 0), mat="Ground_Spike")

    # Vertical 1-inch schedule 40 PVC riser pipe (H=90cm)
    m.add_cylinder(r0=2, r1=2, h=85, z0=0, segs=6, mat="PVC_Pipe_White")

    # Pulsating brass impact sprinkler head & trip lever on top
    m.add_cylinder(r0=3, r1=3, h=10, z0=85, segs=6, mat="Brass_Impact_Head")
    m.add_cylinder(r0=1.5, r1=1, h=14, z0=90, segs=6, mat="Brass_Impact_Head", c0=(0, 0), c1=(0, -14))
    m.add_box((8, 2, 6), center=(0, -10, 95), mat="Brass_Impact_Head")
    return m

# =============================================================================
# REGISTRY & BATCH RUNNER
# =============================================================================

RANCH_FARM_REGISTRY = [
    # 1. Ranching Feed & Fencing (11)
    ("SM_Ranch_HayBale_Round", build_hay_bale_round, "ranching", "1.5x1.5m", "5-foot round field hay bale with twine wrapping"),
    ("SM_Ranch_HayBale_Square", build_hay_bale_square, "ranching", "0.5x1.0m", "Standard 2-string rectangular field hay bale"),
    ("SM_Ranch_SilageBale_Round", build_silage_bale_round, "ranching", "1.5x1.5m", "White stretch-wrapped fermented silage round bale"),
    ("SM_Ranch_StrawBale_Round", build_straw_bale_round, "ranching", "1.5x1.5m", "Golden animal bedding straw round bale"),
    ("SM_Ranch_StrawBale_Square", build_straw_bale_square, "ranching", "0.5x1.0m", "Rectangular bedding straw square bale"),
    ("SM_Ranch_FeedPan_Rubber", build_feed_pan_rubber, "ranching", "0.6x0.6m", "15-gallon heavy-duty rubber feed pan with grain pellets"),
    ("SM_Ranch_SaltLick_Block", build_salt_lick_block, "ranching", "0.3x0.3m", "50lb mineral red salt lick block on timber stand"),
    ("SM_Ranch_Fence_Wood_1m", build_fence_wood_1m, "ranching", "1x0.15m", "1-meter 3-rail cedar board ranch fence section"),
    ("SM_Ranch_Fence_Wire_1m", build_fence_wire_1m, "ranching", "1x0.1m", "Steel T-post with 4 strands of barbed wire"),
    ("SM_Ranch_Gate_Metal_2m", build_gate_metal_2m, "ranching", "2x0.1m", "2-meter red tubular steel 6-bar farm gate with hinges"),
    ("SM_Ranch_Fence_Energizer_Solar", build_fence_energizer_solar, "ranching", "0.3x0.3m", "Solar electric fence energizer charger on T-post"),

    # 3. Crops & Farming Props (12)
    ("SM_Crop_Corn_Stalk", build_crop_corn_stalk, "farming", "0.6x0.6m", "Tall 2.1m mature corn stalk with ripe ears & tassels"),
    ("SM_Crop_Tomato_Vine", build_crop_tomato_vine, "farming", "0.6x0.6m", "Wire tomato cage with lush vine and ripe red fruit"),
    ("SM_Crop_Wheat_Bundle", build_crop_wheat_bundle, "farming", "0.5x0.5m", "Dense clump of golden ripe wheat seed heads"),
    ("SM_Crop_Potato_Plant", build_crop_potato_plant, "farming", "0.6x0.6m", "Hilled soil mound with dark green leafy potato foliage"),
    ("SM_Crop_Carrot_Patch", build_crop_carrot_patch, "farming", "0.5x0.5m", "Soil bed with feathery carrot fronds and orange crowns"),
    ("SM_Crop_Pumpkin_Patch", build_crop_pumpkin_patch, "farming", "0.9x0.9m", "Trailing vine runner with broad leaves and large ribbed pumpkin"),
    ("SM_Crop_Cabbage_Head", build_crop_cabbage_head, "farming", "0.5x0.5m", "Dense crinkled green head of homestead garden cabbage"),
    ("SM_Crop_Sunflower_Stalk", build_crop_sunflower_stalk, "farming", "0.6x0.6m", "2.4m tall sunflower stalk with massive blooming ray disc"),
    ("SM_Farm_Wheelbarrow", build_farm_wheelbarrow, "farming", "0.6x1.4m", "Single-wheel steel hopper contractor wheelbarrow"),
    ("SM_Farm_SeedBag_Burlap", build_farm_seed_bag, "farming", "0.4x0.6m", "Tied burlap grain sack with heirloom stamp"),
    ("SM_Farm_ProduceCrate_Wood", build_farm_produce_crate, "farming", "0.4x0.6m", "Slotted cedar bushel crate heaped with red apples"),
    ("SM_Farm_Irrigation_Sprinkler_Riser", build_irrigation_sprinkler_riser, "farming", "0.3x0.3m", "PVC riser pipe with brass pulsating impact sprinkler head"),
]

def main():
    print("--> 1. Running dedicated Livestock Animals generator...")
    import generate_livestock_animals_assets
    generate_livestock_animals_assets.main()

    print(f"--> 2. Generating {len(RANCH_FARM_REGISTRY)} Feed, Fencing & Crop Assets...")
    count = 0
    for name, func, category, footprint, desc in RANCH_FARM_REGISTRY:
        count += 1
        mesh = func()
        mesh.ground_align()
        tri_count = len(mesh.faces)

        # Select target paths
        if category == "ranching":
            hud_models_dir = HUD_RANCH_MODELS
            hud_icons_dir  = HUD_RANCH_ICONS
            ue5_models_dir = UE5_RANCH_MODELS
            ue5_icons_dir  = UE5_RANCH_ICONS
        else:
            hud_models_dir = HUD_FARM_MODELS
            hud_icons_dir  = HUD_FARM_ICONS
            ue5_models_dir = UE5_FARM_MODELS
            ue5_icons_dir  = UE5_FARM_ICONS

        hud_obj = os.path.join(hud_models_dir, f"{name}.obj")
        hud_mtl = os.path.join(hud_models_dir, f"{name}.mtl")
        mesh.save_obj(hud_obj, hud_mtl)

        ue5_obj = os.path.join(ue5_models_dir, f"{name}.obj")
        ue5_mtl = os.path.join(ue5_models_dir, f"{name}.mtl")
        shutil.copy2(hud_obj, ue5_obj)
        shutil.copy2(hud_mtl, ue5_mtl)

        icon_img = render_icon(mesh, output_size=128, max_dim=96)
        hud_icon = os.path.join(hud_icons_dir, f"{name}.png")
        ue5_icon = os.path.join(ue5_icons_dir, f"{name}.png")
        icon_img.save(hud_icon, "PNG")
        icon_img.save(ue5_icon, "PNG")

        print(f"[{count:02d}/{len(RANCH_FARM_REGISTRY)}] Generated {name} ({category}, {footprint}) - {tri_count} tris")

    print(f"\nSUCCESS: All {len(RANCH_FARM_REGISTRY)} Ranching & Farming models and icons generated and synced!")

if __name__ == "__main__":
    main()

