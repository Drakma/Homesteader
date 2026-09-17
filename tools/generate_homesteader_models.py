import os
import math

_this_dir = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_this_dir)  # tools/ sits at the repo root (one level up)
HUD_MODELS_DIR = os.path.join(BASE_DIR, "assets", "models")
UNREAL_MESHES_DIR = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\Assets\Meshes"

# 16x16 Color Palette Coordinate Lookup
# Returns (u, v) center coordinate for swatch
def get_uv(col, row):
    u = (col + 0.5) / 16.0
    v = 1.0 - (row + 0.5) / 16.0
    return round(u, 5), round(v, 5)

PALETTE_UVS = {
    "Wood_LightOak": get_uv(0, 0),
    "Wood_MediumTimber": get_uv(1, 0),
    "Wood_DarkCedar": get_uv(2, 0),
    "Wood_BirchLight": get_uv(3, 0),
    "Bark_BirchDark": get_uv(0, 1),
    "Dirt_DrySoil": get_uv(2, 1),
    "Metal_SteelLight": get_uv(0, 2),
    "Metal_SteelMid": get_uv(1, 2),
    "Metal_GunmetalDark": get_uv(2, 2),
    "Metal_IronCast": get_uv(3, 2),
    "Metal_BrassGold": get_uv(4, 2),
    "Metal_GalvanizedNail": get_uv(7, 2),
    "Stone_GraniteLight": get_uv(0, 3),
    "Stone_GraniteMid": get_uv(1, 3),
    "Stone_SlateDark": get_uv(2, 3),
    "Crop_CornGold": get_uv(0, 4),
    "Crop_CornHusk": get_uv(1, 4),
    "Crop_CarrotOrange": get_uv(2, 4),
    "Crop_TomatoRed": get_uv(3, 4),
    "Crop_PotatoTan": get_uv(4, 4),
    "Crop_PumpkinOrange": get_uv(5, 4),
    "Leaf_LushGreen": get_uv(0, 6),
    "Leaf_DeepForest": get_uv(1, 6),
    "Leaf_StemLight": get_uv(3, 6),
    "Tech_DishWhite": get_uv(0, 9),
    "Tech_RouterBlack": get_uv(1, 9),
    "Tech_DarkCharcoal": get_uv(2, 9),
    "Tech_StatusGreenLED": get_uv(3, 9),
    "Tech_StatusBlueLED": get_uv(4, 9),
    "Cable_EthernetBlue": get_uv(0, 10),
    "Machine_ChainsawOrange": get_uv(0, 11),
    "Machine_GeneratorRed": get_uv(1, 11),
    "Machine_PumpBlue": get_uv(2, 11),
    "Machine_FilterCoreBlue": get_uv(3, 11),
    "Machine_SepticRibbedDark": get_uv(4, 11),
    "Machine_CompostSlats": get_uv(5, 11),
    "Machine_SolarCellNavy": get_uv(6, 11),
    "Machine_TurbineWhite": get_uv(7, 11),
    "Glass_FilterJarClear": get_uv(1, 12),
    "HUD_HealthRed": get_uv(0, 14),
    "Neutral_White": get_uv(0, 15),
    "Neutral_DarkGrey": get_uv(3, 15),
    "Neutral_PureBlack": get_uv(5, 15),
}

class MeshBuilder:
    def __init__(self, name):
        self.name = name
        self.vertices = []
        self.uvs = []
        self.normals = []
        self.faces = [] # list of [(v_idx, uv_idx, n_idx), ...]

    def add_vertex(self, x, y, z):
        self.vertices.append((round(x, 4), round(y, 4), round(z, 4)))
        return len(self.vertices)

    def add_uv(self, u, v):
        self.uvs.append((round(u, 5), round(v, 5)))
        return len(self.uvs)

    def add_normal(self, nx, ny, nz):
        l = math.sqrt(nx*nx + ny*ny + nz*nz) or 1.0
        self.normals.append((round(nx/l, 4), round(ny/l, 4), round(nz/l, 4)))
        return len(self.normals)

    def add_box(self, cx, cy, cz, sx, sy, sz, color_name):
        # Adds an axis-aligned box with solid color UVs
        u, v = PALETTE_UVS.get(color_name, (0.5, 0.5))
        uv_idx = self.add_uv(u, v)

        hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5
        # 8 corners
        v1 = self.add_vertex(cx - hx, cy - hy, cz - hz)
        v2 = self.add_vertex(cx + hx, cy - hy, cz - hz)
        v3 = self.add_vertex(cx + hx, cy + hy, cz - hz)
        v4 = self.add_vertex(cx - hx, cy + hy, cz - hz)
        v5 = self.add_vertex(cx - hx, cy - hy, cz + hz)
        v6 = self.add_vertex(cx + hx, cy - hy, cz + hz)
        v7 = self.add_vertex(cx + hx, cy + hy, cz + hz)
        v8 = self.add_vertex(cx - hx, cy + hy, cz + hz)

        # 6 face normals
        n_down  = self.add_normal(0, 0, -1)
        n_up    = self.add_normal(0, 0, 1)
        n_south = self.add_normal(0, -1, 0)
        n_north = self.add_normal(0, 1, 0)
        n_west  = self.add_normal(-1, 0, 0)
        n_east  = self.add_normal(1, 0, 0)

        # Faces: Bottom, Top, Front, Back, Left, Right
        self.faces.append([(v1, uv_idx, n_down), (v2, uv_idx, n_down), (v3, uv_idx, n_down), (v4, uv_idx, n_down)])
        self.faces.append([(v5, uv_idx, n_up), (v8, uv_idx, n_up), (v7, uv_idx, n_up), (v6, uv_idx, n_up)])
        self.faces.append([(v1, uv_idx, n_south), (v5, uv_idx, n_south), (v6, uv_idx, n_south), (v2, uv_idx, n_south)])
        self.faces.append([(v3, uv_idx, n_north), (v7, uv_idx, n_north), (v8, uv_idx, n_north), (v4, uv_idx, n_north)])
        self.faces.append([(v4, uv_idx, n_west), (v8, uv_idx, n_west), (v5, uv_idx, n_west), (v1, uv_idx, n_west)])
        self.faces.append([(v2, uv_idx, n_east), (v6, uv_idx, n_east), (v7, uv_idx, n_east), (v3, uv_idx, n_east)])

    def add_cylinder(self, cx, cy, cz, radius, height, segments, color_name, axis='z'):
        u, v = PALETTE_UVS.get(color_name, (0.5, 0.5))
        uv_idx = self.add_uv(u, v)

        h_half = height * 0.5
        top_verts = []
        bot_verts = []
        normals = []

        for i in range(segments):
            ang = (i / segments) * 2.0 * math.pi
            cos_a, sin_a = math.cos(ang), math.sin(ang)

            if axis == 'z':
                b_idx = self.add_vertex(cx + cos_a * radius, cy + sin_a * radius, cz - h_half)
                t_idx = self.add_vertex(cx + cos_a * radius, cy + sin_a * radius, cz + h_half)
                n_idx = self.add_normal(cos_a, sin_a, 0)
            elif axis == 'y':
                b_idx = self.add_vertex(cx + cos_a * radius, cy - h_half, cz + sin_a * radius)
                t_idx = self.add_vertex(cx + cos_a * radius, cy + h_half, cz + sin_a * radius)
                n_idx = self.add_normal(cos_a, 0, sin_a)
            else: # axis == 'x'
                b_idx = self.add_vertex(cx - h_half, cy + cos_a * radius, cz + sin_a * radius)
                t_idx = self.add_vertex(cx + h_half, cy + cos_a * radius, cz + sin_a * radius)
                n_idx = self.add_normal(0, cos_a, sin_a)

            bot_verts.append(b_idx)
            top_verts.append(t_idx)
            normals.append(n_idx)

        # Side quads
        for i in range(segments):
            ni = (i + 1) % segments
            n_idx = normals[i]
            self.faces.append([
                (bot_verts[i], uv_idx, n_idx),
                (top_verts[i], uv_idx, n_idx),
                (top_verts[ni], uv_idx, normals[ni]),
                (bot_verts[ni], uv_idx, normals[ni])
            ])

        # Caps
        if axis == 'z':
            n_top = self.add_normal(0, 0, 1)
            n_bot = self.add_normal(0, 0, -1)
        elif axis == 'y':
            n_top = self.add_normal(0, 1, 0)
            n_bot = self.add_normal(0, -1, 0)
        else:
            n_top = self.add_normal(1, 0, 0)
            n_bot = self.add_normal(-1, 0, 0)

        # Top cap (triangle fan)
        c_top = self.add_vertex(cx if axis != 'x' else cx + h_half,
                                cy if axis != 'y' else cy + h_half,
                                cz if axis != 'z' else cz + h_half)
        for i in range(segments):
            ni = (i + 1) % segments
            self.faces.append([(c_top, uv_idx, n_top), (top_verts[i], uv_idx, n_top), (top_verts[ni], uv_idx, n_top)])

        # Bottom cap (triangle fan)
        c_bot = self.add_vertex(cx if axis != 'x' else cx - h_half,
                                cy if axis != 'y' else cy - h_half,
                                cz if axis != 'z' else cz - h_half)
        for i in range(segments):
            ni = (i + 1) % segments
            self.faces.append([(c_bot, uv_idx, n_bot), (bot_verts[ni], uv_idx, n_bot), (bot_verts[i], uv_idx, n_bot)])

    def write_obj(self, obj_path):
        os.makedirs(os.path.dirname(obj_path), exist_ok=True)
        mtl_filename = os.path.splitext(os.path.basename(obj_path))[0] + ".mtl"
        mtl_path = os.path.splitext(obj_path)[0] + ".mtl"

        with open(obj_path, "w", encoding="utf-8") as f:
            f.write(f"# Homesteader Low-Poly 3D Model: {self.name}\n")
            f.write(f"mtllib {mtl_filename}\n")
            f.write(f"o {self.name}\n\n")

            # Vertices
            for x, y, z in self.vertices:
                f.write(f"v {x:.4f} {y:.4f} {z:.4f}\n")
            f.write("\n")

            # UVs
            for u, v in self.uvs:
                f.write(f"vt {u:.5f} {v:.5f}\n")
            f.write("\n")

            # Normals
            for nx, ny, nz in self.normals:
                f.write(f"vn {nx:.4f} {ny:.4f} {nz:.4f}\n")
            f.write("\n")

            # Material reference
            f.write("usemtl M_Homesteader_Palette\n")
            f.write("s 1\n")

            # Faces
            for face in self.faces:
                face_str = " ".join([f"{v}/{vt}/{vn}" for v, vt, vn in face])
                f.write(f"f {face_str}\n")

        # Write accompanying MTL file
        with open(mtl_path, "w", encoding="utf-8") as mf:
            mf.write("# Homesteader Palette Material Definition\n")
            mf.write("newmtl M_Homesteader_Palette\n")
            mf.write("Ka 1.000 1.000 1.000\n")
            mf.write("Kd 1.000 1.000 1.000\n")
            mf.write("Ks 0.050 0.050 0.050\n")
            mf.write("Ns 10.0\n")
            mf.write("d 1.0\n")
            mf.write("illum 2\n")
            mf.write("map_Kd T_Homesteader_Palette.png\n")


# -------------------------------------------------------------
# SPECIFIC 3D ITEM GENERATORS (Real-World Unreal Scale in cm)
# -------------------------------------------------------------

def build_wood_axe():
    mb = MeshBuilder("SM_Tool_Axe")
    # Handle: curved shaft ~70cm long
    mb.add_box(0, 0, 30, 3.5, 4.5, 65, "Wood_MediumTimber")
    # Grip swell at base
    mb.add_box(0, -0.5, 2, 4.0, 5.2, 8, "Wood_DarkCedar")
    # Metal axe head socket
    mb.add_box(0, 2, 56, 4.2, 10.0, 12.0, "Metal_SteelMid")
    # Chopping blade bit
    mb.add_box(0, 9, 56, 1.2, 12.0, 16.0, "Metal_SteelLight")
    # Back hammer poll
    mb.add_box(0, -4, 56, 4.0, 5.0, 8.0, "Metal_GunmetalDark")
    return mb

def build_pickaxe():
    mb = MeshBuilder("SM_Tool_Pickaxe")
    # Ash wood handle 85cm
    mb.add_box(0, 0, 38, 3.8, 4.2, 80, "Wood_LightOak")
    # Central eye iron collar
    mb.add_box(0, 0, 75, 4.5, 7.0, 10, "Metal_IronCast")
    # Curved front pick spike (pointed)
    mb.add_box(0, 14, 73, 2.8, 22.0, 4.5, "Metal_SteelLight")
    # Chisel rear adze head
    mb.add_box(0, -12, 74, 3.5, 18.0, 3.8, "Metal_SteelMid")
    return mb

def build_garden_hoe():
    mb = MeshBuilder("SM_Tool_Hoe")
    # Long wooden pole 120cm
    mb.add_box(0, 0, 58, 3.2, 3.2, 120, "Wood_BirchLight")
    # Gooseneck steel shank
    mb.add_box(0, 3, 116, 2.5, 6.0, 4.0, "Metal_SteelMid")
    # Angled hoe blade
    mb.add_box(0, 7, 112, 14.0, 1.5, 8.0, "Metal_SteelLight")
    return mb

def build_shovel():
    mb = MeshBuilder("SM_Tool_Shovel")
    # Ash pole 90cm
    mb.add_box(0, 0, 48, 3.2, 3.2, 85, "Wood_LightOak")
    # D-handle at top
    mb.add_box(0, 0, 92, 10.0, 3.5, 8.0, "Wood_DarkCedar")
    mb.add_box(0, 0, 95, 8.0, 3.0, 3.0, "Metal_SteelMid")
    # Curved scoop blade
    mb.add_box(0, 0, 10, 18.0, 2.5, 24.0, "Metal_SteelLight")
    mb.add_box(0, 0.5, 2, 12.0, 1.5, 8.0, "Metal_SteelLight")
    return mb

def build_chainsaw():
    mb = MeshBuilder("SM_Tool_Chainsaw")
    # Engine body housing (orange)
    mb.add_box(0, 0, 14, 18.0, 26.0, 18.0, "Machine_ChainsawOrange")
    # Recoil starter & cover (black)
    mb.add_box(-9.5, -2, 14, 2.0, 16.0, 14.0, "Neutral_DarkGrey")
    # Top wrap handle
    mb.add_box(0, 2, 24, 16.0, 3.0, 3.0, "Metal_SteelLight")
    mb.add_box(7, 2, 18, 3.0, 3.0, 12.0, "Metal_SteelLight")
    # Rear trigger grip
    mb.add_box(0, -18, 12, 4.0, 12.0, 6.0, "Neutral_DarkGrey")
    # Guide bar (silver steel, 45cm long)
    mb.add_box(0, 34, 13, 1.2, 44.0, 10.0, "Metal_SteelLight")
    # Chain teeth ridge (dark metal)
    mb.add_box(0, 34, 13, 1.6, 45.0, 11.2, "Metal_GunmetalDark")
    return mb

def build_fishing_rod():
    mb = MeshBuilder("SM_Tool_FishingRod")
    # Cork handle
    mb.add_cylinder(0, 0, 14, 2.0, 26, 8, "Wood_LightOak", axis='z')
    # Reel seat & graphite blank
    mb.add_cylinder(0, 0, 30, 1.6, 8, 8, "Metal_GunmetalDark", axis='z')
    mb.add_cylinder(0, 0, 110, 1.0, 160, 6, "Neutral_NearBlack", axis='z')
    # Spinning reel body
    mb.add_box(0, 5, 29, 6.0, 7.0, 7.0, "Metal_SteelMid")
    # Reel spool (gold aluminum)
    mb.add_cylinder(0, 6, 26, 3.2, 5.0, 8, "Metal_BrassGold", axis='y')
    # Line guides
    for z in [60, 100, 140, 175]:
        mb.add_box(0, 1.8, z, 0.8, 1.8, 1.2, "Metal_SteelLight")
    return mb

def build_pipe_wrench():
    mb = MeshBuilder("SM_Tool_Wrench")
    # Red/Gunmetal cast iron handle
    mb.add_box(0, 0, 16, 2.5, 4.0, 30.0, "HUD_HealthRed")
    # Fixed jaw housing
    mb.add_box(0, 1.5, 33, 4.0, 7.0, 8.0, "Metal_GunmetalDark")
    # Adjustable hook jaw with serrated teeth
    mb.add_box(0, 3.0, 40, 3.5, 9.0, 10.0, "Metal_SteelMid")
    # Knurled adjusting nut
    mb.add_cylinder(0, 0, 30, 2.5, 3.5, 8, "Metal_SteelLight", axis='z')
    return mb

def build_hammer():
    mb = MeshBuilder("SM_Tool_Hammer")
    # Hickory wooden handle
    mb.add_box(0, 0, 14, 2.8, 3.6, 30, "Wood_LightOak")
    # Rubber comfort grip base
    mb.add_box(0, 0, 3, 3.2, 4.0, 8, "Neutral_DarkGrey")
    # Steel head with face and curved claw
    mb.add_box(0, 1, 30, 3.6, 12.0, 4.0, "Metal_SteelLight")
    mb.add_box(0, 6.5, 30, 3.8, 3.0, 4.2, "Metal_SteelMid") # Striking face
    mb.add_box(0, -4.5, 29.5, 3.0, 5.0, 2.8, "Metal_SteelLight") # Curved claw
    return mb

def build_corn():
    mb = MeshBuilder("SM_Crop_Corn")
    # Golden corn cob (faceted cylinder)
    mb.add_cylinder(0, 0, 11, 3.4, 18.0, 8, "Crop_CornGold", axis='z')
    # Tapered tip
    mb.add_cylinder(0, 0, 21, 2.2, 4.0, 6, "Crop_CornGold", axis='z')
    # Green husks wrap
    mb.add_box(0, 2.5, 7, 6.5, 2.0, 14.0, "Crop_CornHusk")
    mb.add_box(0, -2.5, 7, 6.5, 2.0, 14.0, "Crop_CornHusk")
    mb.add_box(2.5, 0, 7, 2.0, 6.5, 14.0, "Crop_CornHusk")
    # Stem base
    mb.add_cylinder(0, 0, 1, 1.2, 3.0, 6, "Leaf_StemLight", axis='z')
    return mb

def build_tomato():
    mb = MeshBuilder("SM_Crop_Tomato")
    # Plump faceted red fruit
    mb.add_cylinder(0, 0, 4.5, 4.5, 6.5, 8, "Crop_TomatoRed", axis='z')
    mb.add_box(0, 0, 4.5, 7.5, 7.5, 6.0, "Crop_TomatoRed")
    # Green calyx leaves (star)
    mb.add_box(0, 0, 8.2, 6.0, 1.2, 0.6, "Leaf_LushGreen")
    mb.add_box(0, 0, 8.2, 1.2, 6.0, 0.6, "Leaf_LushGreen")
    # Stem nub
    mb.add_cylinder(0, 0, 9.2, 0.6, 2.0, 5, "Leaf_StemLight", axis='z')
    return mb

def build_pumpkin():
    mb = MeshBuilder("SM_Crop_Pumpkin")
    # Large faceted squash
    mb.add_cylinder(0, 0, 14, 18.0, 22.0, 10, "Crop_PumpkinOrange", axis='z')
    mb.add_box(0, 0, 14, 32.0, 32.0, 18.0, "Crop_PumpkinOrange")
    # Ridged segments
    mb.add_box(0, 0, 14, 34.0, 24.0, 20.0, "Crop_PumpkinOrange")
    mb.add_box(0, 0, 14, 24.0, 34.0, 20.0, "Crop_PumpkinOrange")
    # Curved woody stem
    mb.add_cylinder(0, 0, 27, 2.2, 6.0, 6, "Leaf_DeepForest", axis='z')
    return mb

def build_wood_logs_stack():
    mb = MeshBuilder("SM_Resource_WoodLogs")
    L = 90.0
    R = 12.0
    # Bottom two birch logs
    mb.add_cylinder(-13, 0, 12, R, L, 8, "Wood_BirchLight", axis='y')
    mb.add_cylinder(13, 0, 12, R, L, 8, "Wood_BirchLight", axis='y')
    # Top center birch log
    mb.add_cylinder(0, 0, 32, R, L, 8, "Wood_BirchLight", axis='y')
    # Dark bark notches for realism
    mb.add_box(-13, 20, 24, 3.0, 8.0, 1.0, "Bark_BirchDark")
    mb.add_box(13, -15, 24, 3.0, 8.0, 1.0, "Bark_BirchDark")
    mb.add_box(0, 10, 44, 3.0, 8.0, 1.0, "Bark_BirchDark")
    return mb

def build_lumber_plank():
    mb = MeshBuilder("SM_Resource_LumberPlank")
    # Clean milled construction lumber 120cm x 20cm x 4cm
    mb.add_box(0, 0, 2, 20.0, 120.0, 4.0, "Wood_MediumTimber")
    mb.add_box(0, 0, 6.5, 20.0, 120.0, 4.0, "Wood_MediumTimber")
    mb.add_box(0, 0, 11.0, 20.0, 120.0, 4.0, "Wood_MediumTimber")
    return mb

def build_stone_block():
    mb = MeshBuilder("SM_Resource_StoneBlock")
    # Dressed quarried masonry stone 40x40x25cm
    mb.add_box(0, 0, 12.5, 40.0, 40.0, 25.0, "Stone_GraniteMid")
    # Beveled edges
    mb.add_box(0, 0, 12.5, 38.0, 38.0, 27.0, "Stone_GraniteLight")
    return mb

def build_nails_box():
    mb = MeshBuilder("SM_Resource_NailsBox")
    # Cardboard crate
    mb.add_box(0, 0, 9, 20.0, 24.0, 18.0, "Wood_LightOak")
    # Open top spilling silver nails
    mb.add_box(0, 0, 17.5, 18.0, 22.0, 2.0, "Metal_GalvanizedNail")
    # Spilled nails on ground
    mb.add_box(12, 4, 1, 6.0, 1.0, 1.0, "Metal_GalvanizedNail")
    mb.add_box(14, -2, 1, 1.0, 6.0, 1.0, "Metal_GalvanizedNail")
    return mb

def build_solar_panel():
    mb = MeshBuilder("SM_Electric_SolarPanel")
    # Ground metal frame legs (30 deg tilt)
    mb.add_box(-45, 0, 30, 4.0, 4.0, 60.0, "Metal_SteelMid")
    mb.add_box(45, 0, 30, 4.0, 4.0, 60.0, "Metal_SteelMid")
    mb.add_box(0, 0, 10, 95.0, 4.0, 4.0, "Metal_SteelMid")
    # Photovoltaic panel slab 140cm x 90cm
    mb.add_box(0, 10, 65, 130.0, 85.0, 5.0, "Metal_SteelLight")
    # Dark blue silicon solar cells
    mb.add_box(0, 10, 67.5, 124.0, 79.0, 1.0, "Machine_SolarCellNavy")
    return mb

def build_wind_turbine():
    mb = MeshBuilder("SM_Electric_WindTurbine")
    # Mast tower (white steel, 280cm tall)
    mb.add_cylinder(0, 0, 140, 7.0, 280.0, 8, "Machine_TurbineWhite", axis='z')
    # Base flange
    mb.add_cylinder(0, 0, 4, 16.0, 8.0, 8, "Metal_SteelMid", axis='z')
    # Generator nacelle at top
    mb.add_cylinder(0, 8, 280, 8.0, 24.0, 8, "Machine_TurbineWhite", axis='y')
    # Nose cone spinner
    mb.add_cylinder(0, 22, 280, 5.0, 6.0, 8, "Metal_SteelLight", axis='y')
    # 3 Aerodynamic blades (100cm each)
    mb.add_box(0, 21, 335, 1.8, 6.0, 95.0, "Machine_TurbineWhite")
    mb.add_box(82, 21, 235, 1.8, 6.0, 95.0, "Machine_TurbineWhite")
    mb.add_box(-82, 21, 235, 1.8, 6.0, 95.0, "Machine_TurbineWhite")
    return mb

def build_generator():
    mb = MeshBuilder("SM_Electric_Generator")
    # Red tubular roll-cage
    mb.add_box(0, 0, 28, 56.0, 44.0, 54.0, "Machine_GeneratorRed")
    # Interior engine & stator block
    mb.add_box(0, 0, 26, 46.0, 36.0, 42.0, "Metal_IronCast")
    # Gas fuel tank on top
    mb.add_box(0, 0, 48, 42.0, 32.0, 10.0, "HUD_HealthRed")
    # Front control panel with electrical outlets
    mb.add_box(0, 19, 30, 36.0, 2.0, 22.0, "Neutral_DarkGrey")
    mb.add_box(-8, 20.2, 34, 6.0, 0.5, 6.0, "Neutral_NearBlack") # Duplex outlet
    mb.add_box(8, 20.2, 34, 6.0, 0.5, 6.0, "Neutral_NearBlack")
    # Pull cord handle
    mb.add_cylinder(-24, 0, 32, 2.5, 6.0, 6, "Neutral_NearBlack", axis='x')
    return mb

def build_well_pump():
    mb = MeshBuilder("SM_Water_WellPump")
    # Blue electric cast iron motor body
    mb.add_cylinder(0, -8, 22, 12.0, 30.0, 8, "Machine_PumpBlue", axis='y')
    # Centrifugal pump impeller casing
    mb.add_cylinder(0, 14, 22, 15.0, 14.0, 8, "Machine_PumpBlue", axis='y')
    # Cast iron base plate
    mb.add_box(0, 0, 3, 30.0, 44.0, 6.0, "Metal_IronCast")
    # Suction and discharge threaded pipe flanges
    mb.add_cylinder(0, 22, 22, 5.0, 8.0, 8, "Metal_BrassGold", axis='y')
    mb.add_cylinder(0, 14, 38, 5.0, 8.0, 8, "Metal_BrassGold", axis='z')
    return mb

def build_water_filter():
    mb = MeshBuilder("SM_Water_FilterCanister")
    # Translucent filter bowl canister
    mb.add_cylinder(0, 0, 24, 8.5, 38.0, 8, "Glass_FilterJarClear", axis='z')
    # Inner pleated sediment core (blue)
    mb.add_cylinder(0, 0, 24, 4.5, 34.0, 8, "Machine_FilterCoreBlue", axis='z')
    # Heavy duty black/brass manifold cap
    mb.add_box(0, 0, 46, 24.0, 18.0, 10.0, "Neutral_DarkGrey")
    # Threaded brass inlet & outlet ports
    mb.add_cylinder(-14, 0, 46, 3.8, 6.0, 8, "Metal_BrassGold", axis='x')
    mb.add_cylinder(14, 0, 46, 3.8, 6.0, 8, "Metal_BrassGold", axis='x')
    # Pressure relief button
    mb.add_cylinder(0, 0, 52, 1.8, 2.5, 6, "HUD_HealthRed", axis='z')
    return mb

def build_pipe_valve():
    mb = MeshBuilder("SM_Water_PipeValve")
    # Brass run pipe (30cm)
    mb.add_cylinder(0, 0, 10, 4.5, 36.0, 8, "Metal_BrassGold", axis='x')
    # Central valve ball body
    mb.add_box(0, 0, 10, 11.0, 11.0, 11.0, "Metal_BrassGold")
    # Valve stem collar
    mb.add_cylinder(0, 0, 18, 2.5, 6.0, 8, "Metal_BrassGold", axis='z')
    # Quarter-turn shutoff lever handle (red)
    mb.add_box(8, 0, 22, 20.0, 4.0, 2.0, "HUD_HealthRed")
    return mb

def build_septic_tank():
    mb = MeshBuilder("SM_Sewage_SepticTank")
    # Heavy duty dark polyethylene ribbed cylinder (180cm x 110cm)
    mb.add_cylinder(0, 0, 55, 52.0, 160.0, 10, "Machine_SepticRibbedDark", axis='y')
    # Reinforcing rib hoops
    for y in [-60, -30, 0, 30, 60]:
        mb.add_cylinder(0, y, 55, 55.0, 8.0, 10, "Neutral_DarkGrey", axis='y')
    # Dual access risers on top with green manhole lids
    mb.add_cylinder(0, -45, 112, 18.0, 14.0, 8, "Leaf_DeepForest", axis='z')
    mb.add_cylinder(0, 45, 112, 18.0, 14.0, 8, "Leaf_DeepForest", axis='z')
    # Inlet & outlet pipe stubs
    mb.add_cylinder(0, -90, 75, 7.0, 20.0, 8, "Stone_SlateDark", axis='y')
    mb.add_cylinder(0, 90, 65, 7.0, 20.0, 8, "Stone_SlateDark", axis='y')
    return mb

def build_compost_bin():
    mb = MeshBuilder("SM_Sewage_CompostBin")
    W, H = 85.0, 75.0
    # 4 Corner posts
    for x in [-38, 38]:
        for y in [-38, 38]:
            mb.add_box(x, y, H*0.5, 8.0, 8.0, H, "Wood_DarkCedar")
    # Horizontal wooden slats with aeration gaps
    for z in [12, 26, 40, 54, 68]:
        mb.add_box(0, -38, z, W, 3.0, 9.0, "Machine_CompostSlats")
        mb.add_box(0, 38, z, W, 3.0, 9.0, "Machine_CompostSlats")
        mb.add_box(-38, 0, z, 3.0, W, 9.0, "Machine_CompostSlats")
        mb.add_box(38, 0, z, 3.0, W, 9.0, "Machine_CompostSlats")
    # Rich organic compost mulch inside
    mb.add_box(0, 0, 28, 70.0, 70.0, 48.0, "Dirt_DrySoil")
    mb.add_box(0, 0, 52, 66.0, 66.0, 4.0, "Leaf_DeepForest")
    return mb

def build_satellite_dish():
    mb = MeshBuilder("SM_Internet_SatelliteDish")
    # Metal tripod legs
    mb.add_box(0, 0, 25, 4.0, 4.0, 50.0, "Metal_GunmetalDark")
    mb.add_box(18, 0, 12, 38.0, 4.0, 4.0, "Metal_GunmetalDark")
    mb.add_box(-9, 15, 12, 22.0, 22.0, 4.0, "Metal_GunmetalDark")
    mb.add_box(-9, -15, 12, 22.0, 22.0, 4.0, "Metal_GunmetalDark")
    # Dish mast & pivot joint
    mb.add_cylinder(0, 0, 52, 3.0, 14.0, 8, "Metal_SteelMid", axis='z')
    # Phased-array rectangular dish antenna (tilted 35 deg, 65cm x 45cm)
    mb.add_box(0, 6, 68, 65.0, 45.0, 4.0, "Tech_DishWhite")
    # Receiver feed arm
    mb.add_box(0, 16, 78, 2.0, 20.0, 2.0, "Metal_SteelLight")
    return mb

def build_mesh_router():
    mb = MeshBuilder("SM_Internet_Router")
    # Sleek matte black router box 26x18x5cm
    mb.add_box(0, 0, 2.5, 26.0, 18.0, 5.0, "Tech_RouterBlack")
    mb.add_box(0, 0, 5.2, 24.0, 16.0, 0.8, "Tech_DarkCharcoal")
    # Front status LED strip
    mb.add_box(0, 9.1, 2.5, 12.0, 0.4, 0.8, "Tech_StatusBlueLED")
    # 4 Fold-out antennas (24cm tall)
    for x in [-11, -4, 4, 11]:
        mb.add_cylinder(x, -9, 14, 1.0, 24.0, 6, "Neutral_NearBlack", axis='z')
    # Rear RJ45 Ethernet ports
    mb.add_box(0, -9.1, 2.5, 16.0, 0.4, 2.2, "Cable_EthernetBlue")
    return mb

# Registry of models to build and their category mapping
MODEL_REGISTRY = [
    # Tools
    ("tools/hand_tools", "SM_Tool_Axe", build_wood_axe),
    ("tools/hand_tools", "SM_Tool_Pickaxe", build_pickaxe),
    ("tools/hand_tools", "SM_Tool_Hoe", build_garden_hoe),
    ("tools/hand_tools", "SM_Tool_Shovel", build_shovel),
    ("tools/hand_tools", "SM_Tool_Hammer", build_hammer),
    ("tools/hand_tools", "SM_Tool_Wrench", build_pipe_wrench),
    ("tools/equipment", "SM_Tool_Chainsaw", build_chainsaw),
    ("fishing/tackle", "SM_Tool_FishingRod", build_fishing_rod),

    # Crops & Food
    ("farming/crops", "SM_Crop_Corn", build_corn),
    ("farming/crops", "SM_Crop_Tomato", build_tomato),
    ("farming/crops", "SM_Crop_Pumpkin", build_pumpkin),

    # Building & Resources
    ("logging/wood", "SM_Resource_WoodLogs", build_wood_logs_stack),
    ("building/materials", "SM_Resource_LumberPlank", build_lumber_plank),
    ("building/materials", "SM_Resource_StoneBlock", build_stone_block),
    ("building/hardware", "SM_Resource_NailsBox", build_nails_box),

    # Electricity
    ("electricity/generation", "SM_Electric_SolarPanel", build_solar_panel),
    ("electricity/generation", "SM_Electric_WindTurbine", build_wind_turbine),
    ("electricity/generation", "SM_Electric_Generator", build_generator),

    # Water & Sewage
    ("water/sources", "SM_Water_WellPump", build_well_pump),
    ("water/treatment", "SM_Water_FilterCanister", build_water_filter),
    ("water/piping", "SM_Water_PipeValve", build_pipe_valve),
    ("sewage/drainage", "SM_Sewage_SepticTank", build_septic_tank),
    ("sewage/treatment", "SM_Sewage_CompostBin", build_compost_bin),

    # Internet
    ("internet/satellite_antennas", "SM_Internet_SatelliteDish", build_satellite_dish),
    ("internet/routers_networking", "SM_Internet_Router", build_mesh_router),
]

def main():
    print("=== HOMESTEADER 3D STATIC MESH GENERATOR ===")
    print(f"Generating {len(MODEL_REGISTRY)} low-poly models with Color Palette UVs...\n")

    targets = [
        HUD_MODELS_DIR,
        UNREAL_MESHES_DIR
    ]

    for rel_cat, mesh_name, builder_func in MODEL_REGISTRY:
        mb = builder_func()
        print(f"[{rel_cat}] Building {mesh_name}.obj: {len(mb.vertices)} verts, {len(mb.faces)} faces")

        for target_root in targets:
            out_dir = os.path.join(target_root, rel_cat)
            obj_path = os.path.join(out_dir, f"{mesh_name}.obj")
            mb.write_obj(obj_path)

    print(f"\nSUCCESS: Generated {len(MODEL_REGISTRY)} 3D models across {len(targets)} targets.")

if __name__ == "__main__":
    main()

