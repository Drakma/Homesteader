import os
import math

_this_dir = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_this_dir) if os.path.basename(_this_dir) == "scripts" else _this_dir

HUD_GROUND_MODELS = os.path.join(BASE_DIR, "assets", "ground", "models")
UNREAL_GROUND_MESHES = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\Assets\Ground\Meshes"

# Standard Modular Tile Footprint: 100cm x 100cm (1m x 1m), height 20cm.
# Matches UGridSystemSubsystem::TileSize (100 Unreal Units = 1 grid cell = 1m)
# so one ground mesh tile always covers exactly one building-grid cell.
# See GRID_AND_GROUND_STANDARDS.md for the full standard.
TILE_SIZE = 100.0
TILE_HEIGHT = 20.0

class TileMeshBuilder:
    def __init__(self, name, ground_type):
        self.name = name
        self.ground_type = ground_type
        self.vertices = []
        self.uvs = []
        self.normals = []
        self.faces = []

    def add_vert(self, x, y, z):
        self.vertices.append((round(x, 3), round(y, 3), round(z, 3)))
        return len(self.vertices)

    def add_uv(self, u, v):
        self.uvs.append((round(u, 5), round(v, 5)))
        return len(self.uvs)

    def add_norm(self, nx, ny, nz):
        l = math.sqrt(nx*nx + ny*ny + nz*nz) or 1.0
        self.normals.append((round(nx/l, 4), round(ny/l, 4), round(nz/l, 4)))
        return len(self.normals)

    def write_obj(self, obj_path):
        os.makedirs(os.path.dirname(obj_path), exist_ok=True)
        mtl_filename = os.path.splitext(os.path.basename(obj_path))[0] + ".mtl"
        mtl_path = os.path.splitext(obj_path)[0] + ".mtl"

        with open(obj_path, "w", encoding="utf-8") as f:
            f.write(f"# Homesteader Modular Ground Tile: {self.name}\n")
            f.write(f"mtllib {mtl_filename}\n")
            f.write(f"o {self.name}\n\n")

            for x, y, z in self.vertices:
                f.write(f"v {x:.3f} {y:.3f} {z:.3f}\n")
            f.write("\n")

            for u, v in self.uvs:
                f.write(f"vt {u:.5f} {v:.5f}\n")
            f.write("\n")

            for nx, ny, nz in self.normals:
                f.write(f"vn {nx:.4f} {ny:.4f} {nz:.4f}\n")
            f.write("\n")

            mat_name = f"M_Ground_{self.ground_type}"
            f.write(f"usemtl {mat_name}\n")
            f.write("s 1\n")

            for face in self.faces:
                f_str = " ".join([f"{v}/{vt}/{vn}" for v, vt, vn in face])
                f.write(f"f {f_str}\n")

        # Accompanying MTL linking to the specific ground BaseColor texture
        tex_filename = f"T_Ground_{self.ground_type}_BaseColor.png"
        with open(mtl_path, "w", encoding="utf-8") as mf:
            mf.write(f"# Material Definition for {self.name}\n")
            mf.write(f"newmtl M_Ground_{self.ground_type}\n")
            mf.write("Ka 1.000 1.000 1.000\n")
            mf.write("Kd 1.000 1.000 1.000\n")
            mf.write("Ks 0.100 0.100 0.100\n")
            mf.write("Ns 15.0\n")
            mf.write("d 1.0\n")
            mf.write("illum 2\n")
            mf.write(f"map_Kd {tex_filename}\n")

def build_flat_tile(ground_type):
    """Builds a standardized 100x100x20cm beveled modular ground tile (1 grid cell)."""
    mb = TileMeshBuilder(f"SM_Tile_{ground_type.capitalize()}", ground_type)
    H = TILE_SIZE * 0.5 # 50cm
    Z_TOP = 0.0
    Z_BOT = -TILE_HEIGHT # -20cm

    # Top surface UVs (0 to 1)
    uv_00 = mb.add_uv(0.0, 0.0)
    uv_10 = mb.add_uv(1.0, 0.0)
    uv_11 = mb.add_uv(1.0, 1.0)
    uv_01 = mb.add_uv(0.0, 1.0)

    # Top 4 vertices
    v1 = mb.add_vert(-H, -H, Z_TOP)
    v2 = mb.add_vert(H, -H, Z_TOP)
    v3 = mb.add_vert(H, H, Z_TOP)
    v4 = mb.add_vert(-H, H, Z_TOP)

    # Bottom 4 vertices (slight bevel: 2cm inset)
    B_IN = 2.0
    v5 = mb.add_vert(-H + B_IN, -H + B_IN, Z_BOT)
    v6 = mb.add_vert(H - B_IN, -H + B_IN, Z_BOT)
    v7 = mb.add_vert(H - B_IN, H - B_IN, Z_BOT)
    v8 = mb.add_vert(-H + B_IN, H - B_IN, Z_BOT)

    # Normals
    n_up = mb.add_norm(0, 0, 1)
    n_dn = mb.add_norm(0, 0, -1)
    n_s  = mb.add_norm(0, -1, -0.1)
    n_e  = mb.add_norm(1, 0, -0.1)
    n_n  = mb.add_norm(0, 1, -0.1)
    n_w  = mb.add_norm(-1, 0, -0.1)

    # Top face
    mb.faces.append([(v1, uv_00, n_up), (v2, uv_10, n_up), (v3, uv_11, n_up), (v4, uv_01, n_up)])
    # Bottom face
    mb.faces.append([(v5, uv_00, n_dn), (v8, uv_01, n_dn), (v7, uv_11, n_dn), (v6, uv_10, n_dn)])
    # Side skirts
    mb.faces.append([(v1, uv_00, n_s), (v5, uv_00, n_s), (v6, uv_10, n_s), (v2, uv_10, n_s)])
    mb.faces.append([(v2, uv_10, n_e), (v6, uv_10, n_e), (v7, uv_11, n_e), (v3, uv_11, n_e)])
    mb.faces.append([(v3, uv_11, n_n), (v7, uv_11, n_n), (v8, uv_01, n_n), (v4, uv_01, n_n)])
    mb.faces.append([(v4, uv_01, n_w), (v8, uv_01, n_w), (v5, uv_00, n_w), (v1, uv_00, n_w)])

    return mb

def build_farmland_furrows():
    """Builds a 3D tilled farmland plot tile with 4 physical plowed furrow mounds."""
    mb = TileMeshBuilder("SM_Tile_Farmland_Furrows", "farmland")
    H = TILE_SIZE * 0.5
    Z_BASE = -20.0
    n_up = mb.add_norm(0, 0, 1)

    # Grid of ridges running along Y
    steps_x = 16
    steps_y = 4
    dx = TILE_SIZE / steps_x
    dy = TILE_SIZE / steps_y

    for iy in range(steps_y):
        y0 = -H + iy * dy
        y1 = -H + (iy + 1) * dy
        v_0 = iy / float(steps_y)
        v_1 = (iy + 1) / float(steps_y)

        for ix in range(steps_x):
            x0 = -H + ix * dx
            x1 = -H + (ix + 1) * dx
            u_0 = ix / float(steps_x)
            u_1 = (ix + 1) / float(steps_x)

            # 4 sinusoidal ridges
            z00 = math.sin((x0 / TILE_SIZE) * 8.0 * math.pi) * 4.5
            z10 = math.sin((x1 / TILE_SIZE) * 8.0 * math.pi) * 4.5
            z11 = z10
            z01 = z00

            v1 = mb.add_vert(x0, y0, z00)
            v2 = mb.add_vert(x1, y0, z10)
            v3 = mb.add_vert(x1, y1, z11)
            v4 = mb.add_vert(x0, y1, z01)

            uv1 = mb.add_uv(u_0, v_0)
            uv2 = mb.add_uv(u_1, v_0)
            uv3 = mb.add_uv(u_1, v_1)
            uv4 = mb.add_uv(u_0, v_1)

            # Normal vector from slope
            slope = math.cos((x0 / TILE_SIZE) * 8.0 * math.pi) * 0.5
            norm = mb.add_norm(-slope, 0, 1)

            mb.faces.append([(v1, uv1, norm), (v2, uv2, norm), (v3, uv3, norm), (v4, uv4, norm)])

    # Flat bottom skirt
    v_b1 = mb.add_vert(-H, -H, Z_BASE)
    v_b2 = mb.add_vert(H, -H, Z_BASE)
    v_b3 = mb.add_vert(H, H, Z_BASE)
    v_b4 = mb.add_vert(-H, H, Z_BASE)
    n_dn = mb.add_norm(0, 0, -1)
    uv_c = mb.add_uv(0.5, 0.5)
    mb.faces.append([(v_b1, uv_c, n_dn), (v_b4, uv_c, n_dn), (v_b3, uv_c, n_dn), (v_b2, uv_c, n_dn)])
    return mb

def build_road_asphalt():
    """Builds a crowned asphalt road tile with drainage slopes."""
    mb = TileMeshBuilder("SM_Tile_Road_Asphalt", "black_top")
    H = TILE_SIZE * 0.5
    # Crowned profile: Center X=0 is +3cm, edges X=±H are 0cm
    steps = 8
    dx = TILE_SIZE / steps

    for ix in range(steps):
        x0 = -H + ix * dx
        x1 = -H + (ix + 1) * dx
        u0 = ix / float(steps)
        u1 = (ix + 1) / float(steps)

        z0 = 3.0 * (1.0 - (x0 / H)**2)
        z1 = 3.0 * (1.0 - (x1 / H)**2)

        v1 = mb.add_vert(x0, -H, z0)
        v2 = mb.add_vert(x1, -H, z1)
        v3 = mb.add_vert(x1, H, z1)
        v4 = mb.add_vert(x0, H, z0)

        uv1 = mb.add_uv(u0, 0.0)
        uv2 = mb.add_uv(u1, 0.0)
        uv3 = mb.add_uv(u1, 1.0)
        uv4 = mb.add_uv(u0, 1.0)

        slope = -6.0 * (x0 / (H * H))
        n = mb.add_norm(slope, 0, 1)

        mb.faces.append([(v1, uv1, n), (v2, uv2, n), (v3, uv3, n), (v4, uv4, n)])

    # Base skirt
    v_b1 = mb.add_vert(-H, -H, -20)
    v_b2 = mb.add_vert(H, -H, -20)
    v_b3 = mb.add_vert(H, H, -20)
    v_b4 = mb.add_vert(-H, H, -20)
    n_dn = mb.add_norm(0, 0, -1)
    uv_c = mb.add_uv(0.5, 0.5)
    mb.faces.append([(v_b1, uv_c, n_dn), (v_b4, uv_c, n_dn), (v_b3, uv_c, n_dn), (v_b2, uv_c, n_dn)])
    return mb

def build_wood_planks_tile():
    """Builds a raised wooden deck tile with individual 3D boards."""
    mb = TileMeshBuilder("SM_Tile_WoodPlanks", "wood_planks")
    H = TILE_SIZE * 0.5
    num_planks = 8
    plank_w = TILE_SIZE / num_planks # 12.5cm
    gap = 0.8
    n_up = mb.add_norm(0, 0, 1)

    for i in range(num_planks):
        y0 = -H + i * plank_w + gap * 0.5
        y1 = -H + (i + 1) * plank_w - gap * 0.5
        v_0 = (y0 + H) / TILE_SIZE
        v_1 = (y1 + H) / TILE_SIZE

        # Plank top
        v1 = mb.add_vert(-H, y0, 0.0)
        v2 = mb.add_vert(H, y0, 0.0)
        v3 = mb.add_vert(H, y1, 0.0)
        v4 = mb.add_vert(-H, y1, 0.0)

        uv1 = mb.add_uv(0.0, v_0)
        uv2 = mb.add_uv(1.0, v_0)
        uv3 = mb.add_uv(1.0, v_1)
        uv4 = mb.add_uv(0.0, v_1)

        mb.faces.append([(v1, uv1, n_up), (v2, uv2, n_up), (v3, uv3, n_up), (v4, uv4, n_up)])

    # Base support slab
    v_b1 = mb.add_vert(-H, -H, -20)
    v_b2 = mb.add_vert(H, -H, -20)
    v_b3 = mb.add_vert(H, H, -20)
    v_b4 = mb.add_vert(-H, H, -20)
    n_dn = mb.add_norm(0, 0, -1)
    uv_c = mb.add_uv(0.5, 0.5)
    mb.faces.append([(v_b1, uv_c, n_dn), (v_b4, uv_c, n_dn), (v_b3, uv_c, n_dn), (v_b2, uv_c, n_dn)])
    return mb

def build_clutter_tall_grass():
    """3D crossed-quad foliage grass clump (55cm tall)."""
    mb = TileMeshBuilder("SM_Clutter_TallGrass", "tall_grass")
    W = 40.0 # 40cm clump spread
    T_H = 55.0 # 55cm tall

    # Quad 1 (along X)
    v1 = mb.add_vert(-W*0.5, 0, 0)
    v2 = mb.add_vert(W*0.5, 0, 0)
    v3 = mb.add_vert(W*0.5, 0, T_H)
    v4 = mb.add_vert(-W*0.5, 0, T_H)

    # Quad 2 (along Y)
    v5 = mb.add_vert(0, -W*0.5, 0)
    v6 = mb.add_vert(0, W*0.5, 0)
    v7 = mb.add_vert(0, W*0.5, T_H)
    v8 = mb.add_vert(0, -W*0.5, T_H)

    uv1 = mb.add_uv(0.0, 0.0)
    uv2 = mb.add_uv(1.0, 0.0)
    uv3 = mb.add_uv(1.0, 1.0)
    uv4 = mb.add_uv(0.0, 1.0)

    n_f = mb.add_norm(0, 1, 0)
    n_s = mb.add_norm(1, 0, 0)

    # Double sided
    mb.faces.append([(v1, uv1, n_f), (v2, uv2, n_f), (v3, uv3, n_f), (v4, uv4, n_f)])
    mb.faces.append([(v4, uv4, n_f), (v3, uv3, n_f), (v2, uv2, n_f), (v1, uv1, n_f)])
    mb.faces.append([(v5, uv1, n_s), (v6, uv2, n_s), (v7, uv3, n_s), (v8, uv4, n_s)])
    mb.faces.append([(v8, uv4, n_s), (v7, uv3, n_s), (v6, uv2, n_s), (v5, uv1, n_s)])

    return mb

def build_clutter_pebbles():
    """Scattered low-poly river stones and gravel cluster."""
    mb = TileMeshBuilder("SM_Clutter_Pebbles", "gravel")
    n_up = mb.add_norm(0, 0, 1)
    uv_c = mb.add_uv(0.5, 0.5)

    # 12 scattered faceted rocks
    stones = [
        (0, 0, 6, 8, 4), (-35, 20, 4, 6, 3), (40, -30, 8, 10, 5),
        (-20, -40, 5, 5, 3), (25, 45, 6, 8, 4), (55, 10, 4, 5, 2),
        (-50, -15, 5, 7, 3), (10, -55, 6, 6, 3), (-15, 50, 4, 6, 2)
    ]
    for sx, sy, rx, ry, rz in stones:
        v1 = mb.add_vert(sx - rx, sy - ry, 0)
        v2 = mb.add_vert(sx + rx, sy - ry, 0)
        v3 = mb.add_vert(sx + rx, sy + ry, 0)
        v4 = mb.add_vert(sx - rx, sy + ry, 0)
        v_top = mb.add_vert(sx, sy, rz)

        mb.faces.append([(v1, uv_c, n_up), (v2, uv_c, n_up), (v_top, uv_c, n_up)])
        mb.faces.append([(v2, uv_c, n_up), (v3, uv_c, n_up), (v_top, uv_c, n_up)])
        mb.faces.append([(v3, uv_c, n_up), (v4, uv_c, n_up), (v_top, uv_c, n_up)])
        mb.faces.append([(v4, uv_c, n_up), (v1, uv_c, n_up), (v_top, uv_c, n_up)])

    return mb

def build_clutter_cattails():
    """Marsh reeds and cattails (120cm tall)."""
    mb = TileMeshBuilder("SM_Clutter_Cattails", "swamp")
    T_H = 120.0
    W = 18.0
    v1 = mb.add_vert(-W*0.5, 0, 0)
    v2 = mb.add_vert(W*0.5, 0, 0)
    v3 = mb.add_vert(W*0.5, 0, T_H)
    v4 = mb.add_vert(-W*0.5, 0, T_H)

    v5 = mb.add_vert(0, -W*0.5, 0)
    v6 = mb.add_vert(0, W*0.5, 0)
    v7 = mb.add_vert(0, W*0.5, T_H)
    v8 = mb.add_vert(0, -W*0.5, T_H)

    uv1 = mb.add_uv(0.0, 0.0)
    uv2 = mb.add_uv(1.0, 0.0)
    uv3 = mb.add_uv(1.0, 1.0)
    uv4 = mb.add_uv(0.0, 1.0)

    n_f = mb.add_norm(0, 1, 0)
    n_s = mb.add_norm(1, 0, 0)

    mb.faces.append([(v1, uv1, n_f), (v2, uv2, n_f), (v3, uv3, n_f), (v4, uv4, n_f)])
    mb.faces.append([(v4, uv4, n_f), (v3, uv3, n_f), (v2, uv2, n_f), (v1, uv1, n_f)])
    mb.faces.append([(v5, uv1, n_s), (v6, uv2, n_s), (v7, uv3, n_s), (v8, uv4, n_s)])
    mb.faces.append([(v8, uv4, n_s), (v7, uv3, n_s), (v6, uv2, n_s), (v5, uv1, n_s)])
    return mb

GROUND_TYPES = [
    "gravel", "dirt", "road", "path", "grass", 
    "tall_grass", "farmland", "trampled_grass", "concrete", "black_top", 
    "bricks", "mud", "swamp", "pond", "deep_water", 
    "sand", "wood_planks", "snow", "forest_floor", "flagstone"
]

def main():
    print("=== HOMESTEADER MODULAR GROUND MESH GENERATOR ===")
    print(f"Generating 20 standard flat ground tiles (100x100cm = 1 grid cell) + specialized variants...\n")

    targets = [HUD_GROUND_MODELS, UNREAL_GROUND_MESHES]

    # 1. Standard flat modular tiles for all 20 types
    for gt in GROUND_TYPES:
        mb = build_flat_tile(gt)
        for t_root in targets:
            out_file = os.path.join(t_root, f"SM_Tile_{gt.capitalize()}.obj")
            mb.write_obj(out_file)
        print(f"  [OK] Standard Tile: SM_Tile_{gt.capitalize()}.obj")

    # 2. Specialized 3D variants
    specialized = [
        ("SM_Tile_Farmland_Furrows.obj", build_farmland_furrows()),
        ("SM_Tile_Road_Asphalt.obj", build_road_asphalt()),
        ("SM_Tile_WoodPlanks.obj", build_wood_planks_tile()),
        ("SM_Clutter_TallGrass.obj", build_clutter_tall_grass()),
        ("SM_Clutter_Pebbles.obj", build_clutter_pebbles()),
        ("SM_Clutter_Cattails.obj", build_clutter_cattails()),
    ]

    for fname, mb in specialized:
        for t_root in targets:
            out_file = os.path.join(t_root, fname)
            mb.write_obj(out_file)
        print(f"  [OK] Specialized Mesh: {fname}")

    print(f"\nSUCCESS: Generated 26 3D ground tile models across HUD and Unreal directories.")

if __name__ == "__main__":
    main()

