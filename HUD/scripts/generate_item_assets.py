#!/usr/bin/env python3
"""
Homesteader Comprehensive 3D Low-Poly Item Asset Generator
Generates 120+ specialized 3D low-poly item meshes (.obj + .mtl) and renders matching
128x128 transparent preview icons strictly adhering to Homesteader Item Icon Rules:
- Multi-size variants and attachments (hoses, cables, wires, fittings, tanks, power gear)
- 100% RIGHT SIDE UP (proper vertical camera projection)
- 3D Low-poly faceted aesthetic with 3-point cel-shaded lighting
- Crisp dark ink contour silhouette outlines (no internal CAD wireframe)
- Pure 32-bit transparent RGBA (outer perimeter alpha = 0, >= 14px safe margin)
- Zero frames, borders, or drop shadows
- Dual workspace synchronization (HUD and UE5 Content)
"""

import os
import math
import shutil
from PIL import Image, ImageDraw, ImageFilter

HUD_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UE5_ROOT = os.path.abspath(os.path.join(HUD_ROOT, "..", "Homesteader", "Content", "Homesteader"))

HUD_ASSETS_DIR = os.path.join(HUD_ROOT, "assets")
UE5_ICONS_DIR = os.path.join(UE5_ROOT, "UI", "Icons")
UE5_MODELS_DIR = os.path.join(UE5_ROOT, "Assets", "Items", "Meshes")

for d in [HUD_ASSETS_DIR, UE5_ICONS_DIR, UE5_MODELS_DIR]:
    os.makedirs(d, exist_ok=True)

# -----------------------------------------------------------------------------
# 3D Vector Math & Mesh Base
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

    def add_box(self, size, center=(0,0,0), mat="default"):
        dx, dy, dz = size[0]*0.5, size[1]*0.5, size[2]*0.5
        cx, cy, cz = center
        # 8 corners
        c = [
            Vec3(cx - dx, cy - dy, cz - dz),
            Vec3(cx + dx, cy - dy, cz - dz),
            Vec3(cx + dx, cy + dy, cz - dz),
            Vec3(cx - dx, cy + dy, cz - dz),
            Vec3(cx - dx, cy - dy, cz + dz),
            Vec3(cx + dx, cy - dy, cz + dz),
            Vec3(cx + dx, cy + dy, cz + dz),
            Vec3(cx - dx, cy + dy, cz + dz),
        ]
        # 6 faces
        self.add_quad(c[0], c[1], c[5], c[4], mat=mat) # Front (-Y)
        self.add_quad(c[2], c[3], c[7], c[6], mat=mat) # Back (+Y)
        self.add_quad(c[3], c[0], c[4], c[7], mat=mat) # Left (-X)
        self.add_quad(c[1], c[2], c[6], c[5], mat=mat) # Right (+X)
        self.add_quad(c[4], c[5], c[6], c[7], mat=mat) # Top (+Z)
        self.add_quad(c[3], c[2], c[1], c[0], mat=mat) # Bottom (-Z)

    def add_cylinder(self, r0, r1, h, z0=0.0, segs=10, mat="default", c0=(0,0), c1=(0,0), caps=True):
        cx0, cy0 = c0
        cx1, cy1 = c1
        b_pts, t_pts = [], []
        for i in range(segs):
            a = i * 2.0 * math.pi / segs
            b_pts.append(Vec3(cx0 + r0 * math.cos(a), cy0 + r0 * math.sin(a), z0))
            t_pts.append(Vec3(cx1 + r1 * math.cos(a), cy1 + r1 * math.sin(a), z0 + h))

        for i in range(segs):
            i_next = (i + 1) % segs
            self.add_quad(b_pts[i], b_pts[i_next], t_pts[i_next], t_pts[i], mat=mat)

        if caps:
            bc = Vec3(cx0, cy0, z0)
            tc = Vec3(cx1, cy1, z0 + h)
            for i in range(segs):
                i_next = (i + 1) % segs
                self.add_triangle(bc, b_pts[i_next], b_pts[i], mat=mat)
                self.add_triangle(tc, t_pts[i], t_pts[i_next], mat=mat)

    def add_cone(self, r, h, z0=0.0, segs=10, mat="default", c=(0,0), cap=True):
        cx, cy = c
        apex = Vec3(cx, cy, z0 + h)
        base_c = Vec3(cx, cy, z0)
        b_pts = [Vec3(cx + r * math.cos(i * 2.0 * math.pi / segs), cy + r * math.sin(i * 2.0 * math.pi / segs), z0) for i in range(segs)]
        for i in range(segs):
            i_next = (i + 1) % segs
            self.add_triangle(b_pts[i], b_pts[i_next], apex, mat=mat)
            if cap:
                self.add_triangle(base_c, b_pts[i_next], b_pts[i], mat=mat)

    def add_torus(self, r_major, r_minor, segs_major=16, segs_minor=8, z0=0.0, mat="default", c=(0,0)):
        cx, cy = c
        ring_pts = []
        for i in range(segs_major):
            theta = i * 2.0 * math.pi / segs_major
            center_ring = Vec3(cx + r_major * math.cos(theta), cy + r_major * math.sin(theta), z0)
            radial = Vec3(math.cos(theta), math.sin(theta), 0)
            up = Vec3(0, 0, 1)

            pts = []
            for j in range(segs_minor):
                phi = j * 2.0 * math.pi / segs_minor
                p = center_ring + radial * (r_minor * math.cos(phi)) + up * (r_minor * math.sin(phi))
                pts.append(p)
            ring_pts.append(pts)

        for i in range(segs_major):
            i_next = (i + 1) % segs_major
            for j in range(segs_minor):
                j_next = (j + 1) % segs_minor
                self.add_quad(ring_pts[i][j], ring_pts[i_next][j], ring_pts[i_next][j_next], ring_pts[i][j_next], mat=mat)

    def add_spool(self, r_flange, r_core, h, mat_flange="metal", mat_wire="copper", z0=0.0, c=(0,0)):
        # Bottom flange
        self.add_cylinder(r_flange, r_flange, h*0.12, z0=z0, segs=12, mat=mat_flange, c0=c, c1=c)
        # Wire core
        self.add_cylinder(r_core, r_core, h*0.76, z0=z0 + h*0.12, segs=12, mat=mat_wire, c0=c, c1=c)
        # Top flange
        self.add_cylinder(r_flange, r_flange, h*0.12, z0=z0 + h*0.88, segs=12, mat=mat_flange, c0=c, c1=c)

    def add_foliage_lobe(self, radius, center=(0,0,0), mat="default", flatten_z=1.0, subdivisions=1):
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
                    (i0, m01, m20), (i1, m12, m01), (i2, m20, m12), (m01, m12, m20)
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

    def save_obj(self, obj_path, mtl_path):
        mtl_filename = os.path.basename(mtl_path)
        with open(obj_path, "w", encoding="utf-8") as f:
            f.write(f"# Homesteader 3D Item Mesh\n")
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
                f.write(f"Ks 0.15 0.15 0.15\n")
                f.write(f"Ns 16.0\n")
                f.write(f"d 1.0\n")
                f.write(f"illum 2\n\n")

# -----------------------------------------------------------------------------
# 3D Icon Renderer (128x128 32-bit Transparent RGBA)
# -----------------------------------------------------------------------------

def render_item_icon(mesh, output_size=128, max_dim=94):
    mesh.ground_align()

    yaw = math.radians(45.0)
    pitch = math.radians(35.0)

    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)

    cam_verts = []
    min_x, max_x = 1e9, -1e9
    min_y, max_y = 1e9, -1e9

    for v in mesh.vertices:
        rx = cy * v.x - sy * v.y
        ry = sy * v.x + cy * v.y
        rz = v.z
        cx = rx
        cy_p = cp * rz - sp * ry
        cz = sp * rz + cp * ry
        cam_verts.append((cx, cy_p, cz))
        if cx < min_x: min_x = cx
        if cx > max_x: max_x = cx
        if cy_p < min_y: min_y = cy_p
        if cy_p > max_y: max_y = cy_p

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
        depth = (c0[2] + c1[2] + c2[2]) / 3.0

        sx0 = (c0[0] - center_x) * scale * ss + screen_c
        sy0 = screen_c - (c0[1] - center_y) * scale * ss
        sx1 = (c1[0] - center_x) * scale * ss + screen_c
        sy1 = screen_c - (c1[1] - center_y) * scale * ss
        sx2 = (c2[0] - center_x) * scale * ss + screen_c
        sy2 = screen_c - (c2[1] - center_y) * scale * ss

        v0 = mesh.vertices[idx0]
        v1 = mesh.vertices[idx1]
        v2 = mesh.vertices[idx2]
        norm = (v1 - v0).cross(v2 - v0).normalized()

        ndotl = max(0.0, norm.dot(key_light))
        ndotf = max(0.0, norm.dot(fill_light))

        if ndotl > 0.52:
            illum = 1.22
        elif ndotl > 0.20:
            illum = 0.98
        else:
            illum = 0.70 + 0.16 * ndotf

        base_color = mesh.materials.get(mat_name, (0.5, 0.5, 0.5))
        r = int(min(255, max(0, base_color[0] * illum * 255.0)))
        g = int(min(255, max(0, base_color[1] * illum * 255.0)))
        b = int(min(255, max(0, base_color[2] * illum * 255.0)))

        fill = (r, g, b, 255)
        triangles.append((depth, [(sx0, sy0), (sx1, sy1), (sx2, sy2)], fill))

    triangles.sort(key=lambda t: t[0])
    for d, pts, fill in triangles:
        draw.polygon(pts, fill=fill, outline=fill)

    # Stylized dark ink silhouette contour (2px)
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

# -----------------------------------------------------------------------------
# Asset Generation Runner & Exporter
# -----------------------------------------------------------------------------

def run_asset_generation():
    print("=================================================================")
    print("HOMESTEADER 3D ITEM ASSET & 128x128 ICON GENERATOR")
    print("=================================================================")

    from items_water import WATER_BUILDERS
    from items_sewage import SEWAGE_BUILDERS
    from items_electricity import ELECTRICITY_BUILDERS
    from items_internet import INTERNET_BUILDERS
    from items_building import BUILDING_BUILDERS
    from items_tools import TOOLS_BUILDERS
    from items_farming_ranching import FARMING_RANCHING_BUILDERS
    from items_fishing_logging import FISHING_LOGGING_BUILDERS

    builders = [
        ("Water", WATER_BUILDERS),
        ("Sewage", SEWAGE_BUILDERS),
        ("Electricity", ELECTRICITY_BUILDERS),
        ("Internet", INTERNET_BUILDERS),
        ("Building", BUILDING_BUILDERS),
        ("Tools", TOOLS_BUILDERS),
        ("Farming & Ranching", FARMING_RANCHING_BUILDERS),
        ("Fishing & Logging", FISHING_LOGGING_BUILDERS)
    ]

    total_items = sum(len(b_list) for _, b_list in builders)
    print(f"Loaded {len(builders)} modules containing {total_items} item definitions.\n")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    hud_dir = os.path.dirname(script_dir)
    hud_assets_dir = os.path.join(hud_dir, "assets")
    hud_models_dir = os.path.join(hud_assets_dir, "models")
    hud_items_dir = os.path.join(hud_assets_dir, "items")

    homesteader_dir = os.path.abspath(os.path.join(hud_dir, "..", "Homesteader"))
    ue5_icons_dir = os.path.join(homesteader_dir, "Content", "Homesteader", "UI", "Icons")
    ue5_meshes_dir = os.path.join(homesteader_dir, "Content", "Homesteader", "Assets", "Meshes")

    count = 0
    for mod_name, b_list in builders:
        print(f"--- Processing Module: {mod_name} ({len(b_list)} items) ---")
        for item_id, builder_func, category, subcategory in b_list:
            count += 1
            # 1. Build 3D Mesh
            mesh = builder_func()
            mesh.ground_align()

            # Target directory paths
            hud_cat_sub = os.path.join(hud_assets_dir, category, subcategory)
            hud_model_sub = os.path.join(hud_models_dir, category, subcategory)
            hud_items_sub = os.path.join(hud_items_dir, category, subcategory)
            ue5_mesh_sub = os.path.join(ue5_meshes_dir, category, subcategory)
            ue5_icon_sub = os.path.join(ue5_icons_dir, category, subcategory)

            for d in [hud_cat_sub, hud_model_sub, hud_items_sub, ue5_mesh_sub, ue5_icon_sub]:
                os.makedirs(d, exist_ok=True)

            # Save OBJ & MTL
            # In HUD/assets/<cat>/<subcat>/
            mesh.save_obj(os.path.join(hud_cat_sub, f"{item_id}.obj"), os.path.join(hud_cat_sub, f"{item_id}.mtl"))
            # In HUD/assets/models/<cat>/<subcat>/
            mesh.save_obj(os.path.join(hud_model_sub, f"{item_id}.obj"), os.path.join(hud_model_sub, f"{item_id}.mtl"))
            # In Homesteader/Content/Homesteader/Assets/Meshes/<cat>/<subcat>/
            mesh.save_obj(os.path.join(ue5_mesh_sub, f"{item_id}.obj"), os.path.join(ue5_mesh_sub, f"{item_id}.mtl"))

            # 2. Render 128x128 Icon
            icon = render_item_icon(mesh, output_size=128, max_dim=94)

            # Save Icon to all locations
            # HUD/assets/<cat>/<subcat>/<id>.png
            icon.save(os.path.join(hud_cat_sub, f"{item_id}.png"), "PNG")
            # HUD/assets/items/<cat>/<subcat>/<id>.png & HUD/assets/items/<id>.png
            icon.save(os.path.join(hud_items_sub, f"{item_id}.png"), "PNG")
            icon.save(os.path.join(hud_items_dir, f"{item_id}.png"), "PNG")
            # Homesteader/Content/Homesteader/UI/Icons/<cat>/<subcat>/<id>.png
            icon.save(os.path.join(ue5_icon_sub, f"{item_id}.png"), "PNG")
            # Homesteader/Content/Homesteader/UI/Icons/<id>.png (flat lookup for UE5 DataTable)
            icon.save(os.path.join(ue5_icons_dir, f"{item_id}.png"), "PNG")

            print(f"[{count:03d}/{total_items}] Generated {item_id} ({category}/{subcategory}) - {len(mesh.vertices)} verts, {len(mesh.faces)} faces")

    print(f"\nSUCCESS: Generated all {count} items across HUD and UE5 directories!")

if __name__ == "__main__":
    run_asset_generation()

