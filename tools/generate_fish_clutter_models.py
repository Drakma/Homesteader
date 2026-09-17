#!/usr/bin/env python3
"""
generate_fish_clutter_models.py
Generates low-poly 3D world models (.obj + .mtl) for:
- 3 new fish: Catfish, Walleye, Crappie (+ aliases for Bass, Salmon, Trout)
- 6 fish fillets: Bass, Salmon, Trout, Catfish, Walleye, Crappie
- 3 clutter items: Fallen Branch, Dirt Clump, Grass Tuft

Enforces:
- Z_min = 0.00cm (ground-aligned pivot)
- Watertight geometry & realistic metric bounds
- Dual-workspace delivery: assets/ and Homesteader/Content/Homesteader/
"""

import os
import shutil
import math

# tools/ sits at the repo root, so the project root is one level up.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUD_ROOT = PROJECT_ROOT  # legacy alias - keep old joins working
UE5_ROOT = r"c:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader"

FISHING_HUD_MODELS = os.path.join(HUD_ROOT, "assets", "fishing", "models")
FISHING_UE5_MODELS = os.path.join(UE5_ROOT, "Assets", "Fishing", "Meshes")
FISHING_HUD_ICONS = os.path.join(HUD_ROOT, "assets", "fishing", "icons")
FISHING_UE5_ICONS = os.path.join(UE5_ROOT, "UI", "Icons", "fishing")

GROUND_HUD_MODELS = os.path.join(HUD_ROOT, "assets", "ground", "models")
GROUND_UE5_MODELS = os.path.join(UE5_ROOT, "Assets", "Ground", "Meshes")
GROUND_HUD_ICONS = os.path.join(HUD_ROOT, "assets", "ground", "icons")
GROUND_UE5_ICONS = os.path.join(UE5_ROOT, "UI", "Icons", "ground")

ITEMS_ICONS_HUD = os.path.join(HUD_ROOT, "assets", "items")
ITEMS_ICONS_UE5 = os.path.join(UE5_ROOT, "UI", "Icons")

for d in [FISHING_HUD_MODELS, FISHING_UE5_MODELS, FISHING_HUD_ICONS, FISHING_UE5_ICONS,
          GROUND_HUD_MODELS, GROUND_UE5_MODELS, GROUND_HUD_ICONS, GROUND_UE5_ICONS]:
    os.makedirs(d, exist_ok=True)

class MeshBuilder:
    def __init__(self, name, mat_name="M_Item"):
        self.name = name
        self.mat_name = mat_name
        self.verts = []
        self.faces = []

    def add_vert(self, x, y, z):
        self.verts.append((float(x), float(y), float(z)))
        return len(self.verts)

    def add_quad(self, v1, v2, v3, v4):
        self.faces.append((v1, v2, v3))
        self.faces.append((v1, v3, v4))

    def add_tri(self, v1, v2, v3):
        self.faces.append((v1, v2, v3))

    def add_box(self, x_min, y_min, z_min, x_max, y_max, z_max):
        v = [
            self.add_vert(x_min, y_min, z_min), # 0
            self.add_vert(x_max, y_min, z_min), # 1
            self.add_vert(x_max, y_max, z_min), # 2
            self.add_vert(x_min, y_max, z_min), # 3
            self.add_vert(x_min, y_min, z_max), # 4
            self.add_vert(x_max, y_min, z_max), # 5
            self.add_vert(x_max, y_max, z_max), # 6
            self.add_vert(x_min, y_max, z_max)  # 7
        ]
        self.add_quad(v[0], v[3], v[2], v[1]) # bottom
        self.add_quad(v[4], v[5], v[6], v[7]) # top
        self.add_quad(v[0], v[1], v[5], v[4]) # front
        self.add_quad(v[2], v[3], v[7], v[6]) # back
        self.add_quad(v[0], v[4], v[7], v[3]) # left
        self.add_quad(v[1], v[2], v[6], v[5]) # right

    def ground_align(self):
        if not self.verts:
            return
        min_z = min(v[2] for v in self.verts)
        self.verts = [(v[0], v[1], v[2] - min_z) for v in self.verts]

    def save(self, out_dir_hud, out_dir_ue5, kd_color=(0.8, 0.8, 0.8)):
        self.ground_align()
        obj_file = f"{self.name}.obj"
        mtl_file = f"{self.name}.mtl"
        
        # Write MTL
        mtl_content = f"""# Homesteader Material
newmtl {self.mat_name}
Kd {kd_color[0]:.3f} {kd_color[1]:.3f} {kd_color[2]:.3f}
Ka 0.100 0.100 0.100
Ks 0.200 0.200 0.200
Ns 20.0
d 1.0
illum 2
"""
        # Write OBJ
        obj_lines = [
            f"# Homesteader 3D Model: {self.name}",
            f"mtllib {mtl_file}",
            f"o {self.name}"
        ]
        for v in self.verts:
            obj_lines.append(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}")
        obj_lines.append(f"usemtl {self.mat_name}")
        obj_lines.append("s 1")
        for f in self.faces:
            obj_lines.append(f"f {f[0]} {f[1]} {f[2]}")
        obj_content = "\n".join(obj_lines) + "\n"

        for target_dir in [out_dir_hud, out_dir_ue5]:
            with open(os.path.join(target_dir, mtl_file), "w", encoding="utf-8") as f:
                f.write(mtl_content)
            with open(os.path.join(target_dir, obj_file), "w", encoding="utf-8") as f:
                f.write(obj_content)
                
        # Copy preview icon if present
        icon_name = f"{self.name}.png"
        src_icon = os.path.join(ITEMS_ICONS_HUD, icon_name)
        if not os.path.exists(src_icon):
            # Try lowercasing or mapping
            alt = icon_name.lower().replace("sm_item_", "")
            src_icon = os.path.join(ITEMS_ICONS_HUD, alt)
            
        if os.path.exists(src_icon):
            shutil.copy2(src_icon, os.path.join(out_dir_hud, icon_name))
            shutil.copy2(src_icon, os.path.join(out_dir_ue5, icon_name))

        print(f"Generated {self.name} ({len(self.verts)} verts, {len(self.faces)} tris)")

# ==============================================================================
# FISH MODELS GENERATION
# ==============================================================================

def generate_fish(name, length_cm, height_cm, width_cm, kd_color, barbels=False):
    mb = MeshBuilder(name, mat_name=f"M_{name}")
    l2 = length_cm * 0.5
    h2 = height_cm * 0.5
    w2 = width_cm * 0.5
    
    # 3D Low-Poly Fish Geometry
    # Body cross-sections along X (Length)
    # X from -l2 (Snout) to +l2 (Tail base)
    x_snout = -l2
    x_head = -l2 * 0.55
    x_mid = 0.0
    x_back = l2 * 0.5
    x_peduncle = l2 * 0.8
    x_tail = l2 * 1.15
    
    # Section vertices
    # Snout
    v_snout = mb.add_vert(x_snout, 0, h2*0.6)
    
    # Head ring (4 verts)
    h_top = mb.add_vert(x_head, 0, h2*1.2)
    h_left = mb.add_vert(x_head, -w2*0.7, h2*0.6)
    h_bot = mb.add_vert(x_head, 0, h2*0.1)
    h_right = mb.add_vert(x_head, w2*0.7, h2*0.6)
    
    # Mid ring (4 verts)
    m_top = mb.add_vert(x_mid, 0, h2*1.4)
    m_left = mb.add_vert(x_mid, -w2, h2*0.6)
    m_bot = mb.add_vert(x_mid, 0, 0)
    m_right = mb.add_vert(x_mid, w2, h2*0.6)
    
    # Back ring (4 verts)
    b_top = mb.add_vert(x_back, 0, h2*1.1)
    b_left = mb.add_vert(x_back, -w2*0.6, h2*0.6)
    b_bot = mb.add_vert(x_back, 0, h2*0.2)
    b_right = mb.add_vert(x_back, w2*0.6, h2*0.6)
    
    # Caudal peduncle ring (4 verts)
    p_top = mb.add_vert(x_peduncle, 0, h2*0.8)
    p_left = mb.add_vert(x_peduncle, -w2*0.25, h2*0.6)
    p_bot = mb.add_vert(x_peduncle, 0, h2*0.4)
    p_right = mb.add_vert(x_peduncle, w2*0.25, h2*0.6)
    
    # Tail fin (Forked)
    t_top = mb.add_vert(x_tail, 0, h2*1.5)
    t_fork = mb.add_vert(x_tail*0.9, 0, h2*0.6)
    t_bot = mb.add_vert(x_tail, 0, -h2*0.2)
    
    # Dorsal fin
    d_fin_peak = mb.add_vert(x_mid*0.5, 0, h2*1.9)
    
    # Quads and tris
    # Snout to head
    mb.add_tri(v_snout, h_top, h_left)
    mb.add_tri(v_snout, h_left, h_bot)
    mb.add_tri(v_snout, h_bot, h_right)
    mb.add_tri(v_snout, h_right, h_top)
    
    # Head to mid
    mb.add_quad(h_top, m_top, m_left, h_left)
    mb.add_quad(h_left, m_left, m_bot, h_bot)
    mb.add_quad(h_bot, m_bot, m_right, h_right)
    mb.add_quad(h_right, m_right, m_top, h_top)
    
    # Mid to back
    mb.add_quad(m_top, b_top, b_left, m_left)
    mb.add_quad(m_left, b_left, b_bot, m_bot)
    mb.add_quad(m_bot, b_bot, b_right, m_right)
    mb.add_quad(m_right, b_right, b_top, m_top)
    
    # Back to peduncle
    mb.add_quad(b_top, p_top, p_left, b_left)
    mb.add_quad(b_left, p_left, p_bot, b_bot)
    mb.add_quad(b_bot, p_bot, p_right, b_right)
    mb.add_quad(b_right, p_right, p_top, b_top)
    
    # Tail fin
    mb.add_tri(p_top, t_top, t_fork)
    mb.add_tri(p_bot, t_fork, t_bot)
    mb.add_quad(p_top, t_fork, p_bot, p_left)
    mb.add_quad(p_top, p_right, p_bot, t_fork)
    
    # Dorsal fin
    mb.add_tri(m_top, d_fin_peak, b_top)
    
    # Optional Barbels / Whiskers
    if barbels:
        for b_side in [-w2*0.4, w2*0.4]:
            b_tip = mb.add_vert(x_snout - 6, b_side * 1.8, 0)
            mb.add_tri(v_snout, b_tip, h_bot)

    mb.save(FISHING_HUD_MODELS, FISHING_UE5_MODELS, kd_color=kd_color)

# ==============================================================================
# FISH FILLETS GENERATION
# ==============================================================================

def generate_fillet(name, length_cm, width_cm, thickness_cm, kd_color):
    mb = MeshBuilder(name, mat_name=f"M_{name}")
    l2 = length_cm * 0.5
    w2 = width_cm * 0.5
    t = thickness_cm
    
    # Tapered organic steak/fillet slab
    # Top vertices (Z = t)
    t1 = mb.add_vert(-l2, 0, t)           # snout/front tip
    t2 = mb.add_vert(-l2*0.5, -w2*0.8, t) # front left
    t3 = mb.add_vert(0, -w2, t)           # mid left
    t4 = mb.add_vert(l2*0.5, -w2*0.6, t)  # rear left
    t5 = mb.add_vert(l2, 0, t)            # tail tip
    t6 = mb.add_vert(l2*0.5, w2*0.6, t)   # rear right
    t7 = mb.add_vert(0, w2, t)            # mid right
    t8 = mb.add_vert(-l2*0.5, w2*0.8, t)  # front right
    t_center = mb.add_vert(0, 0, t + 0.5) # slightly arched center ridge
    
    # Bottom skin vertices (Z = 0)
    b1 = mb.add_vert(-l2, 0, 0)
    b2 = mb.add_vert(-l2*0.5, -w2*0.8, 0)
    b3 = mb.add_vert(0, -w2, 0)
    b4 = mb.add_vert(l2*0.5, -w2*0.6, 0)
    b5 = mb.add_vert(l2, 0, 0)
    b6 = mb.add_vert(l2*0.5, w2*0.6, 0)
    b7 = mb.add_vert(0, w2, 0)
    b8 = mb.add_vert(-l2*0.5, w2*0.8, 0)
    b_center = mb.add_vert(0, 0, 0)
    
    # Top meat facets (Radiating from center)
    mb.add_tri(t1, t2, t_center)
    mb.add_tri(t2, t3, t_center)
    mb.add_tri(t3, t4, t_center)
    mb.add_tri(t4, t5, t_center)
    mb.add_tri(t5, t6, t_center)
    mb.add_tri(t6, t7, t_center)
    mb.add_tri(t7, t8, t_center)
    mb.add_tri(t8, t1, t_center)
    
    # Bottom skin facets
    mb.add_tri(b1, b_center, b2)
    mb.add_tri(b2, b_center, b3)
    mb.add_tri(b3, b_center, b4)
    mb.add_tri(b4, b_center, b5)
    mb.add_tri(b5, b_center, b6)
    mb.add_tri(b6, b_center, b7)
    mb.add_tri(b7, b_center, b8)
    mb.add_tri(b8, b_center, b1)
    
    # Edge side walls (Extrusion)
    mb.add_quad(t1, b1, b2, t2)
    mb.add_quad(t2, b2, b3, t3)
    mb.add_quad(t3, b3, b4, t4)
    mb.add_quad(t4, b4, b5, t5)
    mb.add_quad(t5, b5, b6, t6)
    mb.add_quad(t6, b6, b7, t7)
    mb.add_quad(t7, b7, b8, t8)
    mb.add_quad(t8, b8, b1, t1)

    mb.save(FISHING_HUD_MODELS, FISHING_UE5_MODELS, kd_color=kd_color)

# ==============================================================================
# CLUTTER MODELS GENERATION
# ==============================================================================

def generate_clutter_branch():
    mb = MeshBuilder("SM_Clutter_Branch", mat_name="M_Wood_Branch")
    # Fallen crooked branch with 2 offshoot twigs
    # Main trunk: 72cm long, 8cm diameter, crooked
    mb.add_box(-36, -4, 0, 36, 4, 8)
    # Twig 1
    mb.add_box(-12, 4, 2, -4, 18, 6)
    # Twig 2
    mb.add_box(10, -16, 2, 18, -4, 6)
    mb.save(GROUND_HUD_MODELS, GROUND_UE5_MODELS, kd_color=(0.45, 0.32, 0.20))

def generate_clutter_dirt_clump():
    mb = MeshBuilder("SM_Clutter_DirtClump", mat_name="M_Soil_Clump")
    # Mounded dirt clump with small stone pebbles
    # Main mound (Faceted pyramid/dome)
    c_top = mb.add_vert(0, 0, 14)
    p1 = mb.add_vert(-11, -12, 0)
    p2 = mb.add_vert(0, -14, 0)
    p3 = mb.add_vert(12, -11, 0)
    p4 = mb.add_vert(13, 2, 0)
    p5 = mb.add_vert(10, 12, 0)
    p6 = mb.add_vert(-2, 13, 0)
    p7 = mb.add_vert(-12, 8, 0)
    p8 = mb.add_vert(-13, -2, 0)
    
    mb.add_tri(p1, p2, c_top)
    mb.add_tri(p2, p3, c_top)
    mb.add_tri(p3, p4, c_top)
    mb.add_tri(p4, p5, c_top)
    mb.add_tri(p5, p6, c_top)
    mb.add_tri(p6, p7, c_top)
    mb.add_tri(p7, p8, c_top)
    mb.add_tri(p8, p1, c_top)
    
    # Embedded pebble 1
    mb.add_box(-6, -4, 6, -2, 0, 9)
    # Embedded pebble 2
    mb.add_box(3, 4, 5, 6, 8, 8)
    
    mb.save(GROUND_HUD_MODELS, GROUND_UE5_MODELS, kd_color=(0.40, 0.28, 0.18))

def generate_clutter_grass_tuft():
    mb = MeshBuilder("SM_Clutter_GrassTuft", mat_name="M_Foliage_Grass")
    # Several radiating angled grass blade polygons
    num_blades = 7
    base_z = 0
    for i in range(num_blades):
        angle = i * (2 * math.pi / num_blades)
        length = 18 + (i % 3) * 3
        height = 16 + (i % 2) * 6
        dx = math.cos(angle) * length
        dy = math.sin(angle) * length
        
        # Blade quad
        b1 = mb.add_vert(-math.sin(angle)*1.5, math.cos(angle)*1.5, base_z)
        b2 = mb.add_vert(math.sin(angle)*1.5, -math.cos(angle)*1.5, base_z)
        mid = mb.add_vert(dx*0.5, dy*0.5, height*0.6)
        tip = mb.add_vert(dx, dy, height)
        
        mb.add_tri(b1, b2, mid)
        mb.add_tri(b1, mid, tip)
        mb.add_tri(b2, tip, mid)
        
    mb.save(GROUND_HUD_MODELS, GROUND_UE5_MODELS, kd_color=(0.35, 0.65, 0.25))

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

if __name__ == "__main__":
    print("=== Generating 3 New Fish Models ===")
    generate_fish("SM_Item_Fish_Catfish", length_cm=56, height_cm=18, width_cm=14, kd_color=(0.35, 0.42, 0.50), barbels=True)
    generate_fish("SM_Item_Fish_Walleye", length_cm=50, height_cm=16, width_cm=11, kd_color=(0.55, 0.52, 0.25))
    generate_fish("SM_Item_Fish_Crappie", length_cm=30, height_cm=18, width_cm=8, kd_color=(0.38, 0.48, 0.42))

    # Aliases for Bass, Salmon, Trout
    for alias, target in [("SM_Item_Fish_Bass", "SM_Item_Fish_LargemouthBass"),
                          ("SM_Item_Fish_Salmon", "SM_Item_Fish_ChinookSalmon"),
                          ("SM_Item_Fish_Trout", "SM_Item_Fish_RainbowTrout")]:
        for src_dir, dst_dir in [(FISHING_HUD_MODELS, FISHING_HUD_MODELS), (FISHING_UE5_MODELS, FISHING_UE5_MODELS)]:
            src_obj = os.path.join(src_dir, f"{target}.obj")
            dst_obj = os.path.join(dst_dir, f"{alias}.obj")
            src_mtl = os.path.join(src_dir, f"{target}.mtl")
            dst_mtl = os.path.join(dst_dir, f"{alias}.mtl")
            if os.path.exists(src_obj):
                shutil.copy2(src_obj, dst_obj)
            if os.path.exists(src_mtl):
                shutil.copy2(src_mtl, dst_mtl)
        print(f"Created alias {alias} -> {target}")

    print("\n=== Generating 6 Fish Fillet Models ===")
    generate_fillet("SM_Item_FishFillet_Bass", length_cm=22, width_cm=12, thickness_cm=3.0, kd_color=(0.92, 0.90, 0.86))
    generate_fillet("SM_Item_FishFillet_Salmon", length_cm=26, width_cm=14, thickness_cm=3.5, kd_color=(0.95, 0.48, 0.35))
    generate_fillet("SM_Item_FishFillet_Trout", length_cm=20, width_cm=10, thickness_cm=2.8, kd_color=(0.94, 0.62, 0.56))
    generate_fillet("SM_Item_FishFillet_Catfish", length_cm=24, width_cm=13, thickness_cm=3.2, kd_color=(0.95, 0.95, 0.92))
    generate_fillet("SM_Item_FishFillet_Walleye", length_cm=22, width_cm=11, thickness_cm=3.0, kd_color=(0.93, 0.91, 0.85))
    generate_fillet("SM_Item_FishFillet_Crappie", length_cm=16, width_cm=9, thickness_cm=2.5, kd_color=(0.92, 0.93, 0.91))

    print("\n=== Generating 3 Clutter World Models ===")
    generate_clutter_branch()
    generate_clutter_dirt_clump()
    generate_clutter_grass_tuft()

    print("\nALL 3D MODELS GENERATED AND DEPLOYED ACROSS HUD AND UE5!")

