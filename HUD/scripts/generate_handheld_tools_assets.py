#!/usr/bin/env python3
"""
Homesteader Handheld Player Tools & Wearables 3D Asset Generator
===============================================================
FAITHFULLY REBUILT TO MATCH ITEM ICONS:
1. SM_Tool_Axe_Felling         <- tool_axe_felling.png (Curved hickory handle, forged wedge head, silver bit)
2. SM_Tool_Hatchet_Camp        <- tool_hatchet_camp.png (Short carved wood handle, compact hatchet bit)
3. SM_Tool_Chainsaw_Gas_16     <- tool_chainsaw.png (Orange 16" gas chainsaw, wrap handle, chain bar)
4. SM_Tool_Chainsaw_Gas_20     <- tool_chainsaw_gas_20.png (Orange 20" timber chainsaw, long bar)
5. SM_Tool_CantHook_Peavey     <- tool_cant_hook_peavey.png (Wood lever, forged steel duckbill hook & pike)
6. SM_Tool_Maul_Splitting      <- tool_maul_splitting.png (Yellow handle, black grip, heavy sledge poll & maul bit)
7. SM_Tool_Shovel_RoundPoint   <- tool_shovel_round_point.png (Red D-handle, wood shaft, silver socket, pointed dish)
8. SM_Tool_Shovel_ScoopFlat    <- tool_shovel_scoop_flat.png (Black D-handle, wood shaft, wide aluminum scoop)
9. SM_Tool_Shovel_Trenching    <- tool_shovel_trenching.png (Red D-handle, wood shaft, narrow V-trench blade)
10. SM_Tool_Hoe                <- tool_hoe.png (Wood handle, silver ferrule, swan-neck shank, draw hoe blade)
11. SM_Tool_Pickaxe            <- tool_pickaxe.png (Faceted wood handle, collar, curved chisel adze & pointed pick)
12. SM_Tool_Sickle             <- tool_sickle.png (Turned wood grip, brass ferrule, curved crescent blade)
13. SM_Tool_Trowel_Hand        <- tool_trowel_hand.png (Black/orange rubber grip, cast aluminum scoop blade)
14. SM_Tool_Drill_Cordless_20V <- DeWalt style yellow/black 20V drill, battery on base, keyless chuck
15. SM_Tool_ImpactDriver_Cordless <- Yellow/black compact 20V impact driver, 1/4" hex collet
16. SM_Tool_CircularSaw_Cordless <- 7-1/4" circular saw, base shoe plate, blade guard, dual handles
17. SM_Tool_AngleGrinder_Cordless <- 4-1/2" grinder, 90-deg gearhead, safety guard, cutoff wheel
18. SM_Tool_MiterSaw           <- Sliding compound miter saw, turntable base, fence, 10" blade guard
19. SM_Tool_TableSaw           <- Contractor jobsite table saw on folding stand, rip fence, blade
20. SM_Tool_WateringCan        <- tool_watering_can.png (Galvanized steel can, top/rear handles, brass rose)
21. SM_Tool_Shears_Pruning     <- tool_shears_pruning.png (Red vinyl handles, curved bypass cutting blade)
22. SM_Tool_Loppers_Heavy      <- tool_loppers_heavy.png (Dual long arms, cushioned grips, bypass jaws)
23. SM_Tool_Sprayer_Backpack   <- sprayer_backpack_4gal.png (White poly tank, straps, pump lever, spray wand)
24. SM_Tool_Wand_Watering      <- wand_watering_brass.png (30" aluminum wand, brass valve, shower head)
25. SM_Tool_Pail_Milk_Stainless <- pail_milk_stainless.png (Seamless stainless pail, wire bail handle)
26. SM_Tool_Shears_SheepWool   <- shears_sheep_wool.png (Single-bow spring steel wool fleece shears)
27. SM_Tool_Paddle_Sorting     <- paddle_sorting_cattle.png (Red sorting paddle with rattle beads, grip shaft)
28. SM_Tool_Helmet_LoggingSafety <- helmet_logging_safety.png (Hi-vis orange helmet, ear muffs, mesh face shield)
"""

import os
import sys
import math
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

HUD_MODELS = os.path.join(PROJECT_ROOT, "HUD", "assets", "tools", "models")
HUD_ICONS  = os.path.join(PROJECT_ROOT, "HUD", "assets", "tools", "icons")
UE5_MODELS = os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "Assets", "Tools", "Meshes")
UE5_ICONS  = os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "UI", "Icons", "tools")
ITEMS_DIR  = os.path.join(PROJECT_ROOT, "HUD", "assets", "items")

for p in [HUD_MODELS, HUD_ICONS, UE5_MODELS, UE5_ICONS]:
    os.makedirs(p, exist_ok=True)

class MeshBuilder:
    def __init__(self, name):
        self.name = name
        self.vertices = []
        self.materials = {}
        self.mat_colors = {}
        self.current_mat = "default"

    def set_material(self, mat_name, r, g, b):
        self.current_mat = mat_name
        if mat_name not in self.materials:
            self.materials[mat_name] = []
            self.mat_colors[mat_name] = (r, g, b)

    def add_vertex(self, x, y, z):
        self.vertices.append((round(x, 2), round(y, 2), round(z, 2)))
        return len(self.vertices)

    def add_tri(self, v1, v2, v3):
        self.materials[self.current_mat].append((v1, v2, v3))

    def add_quad(self, v1, v2, v3, v4):
        self.materials[self.current_mat].append((v1, v2, v3))
        self.materials[self.current_mat].append((v1, v3, v4))

    def add_box(self, x_min, x_max, y_min, y_max, z_min, z_max):
        v1 = self.add_vertex(x_min, y_min, z_min)
        v2 = self.add_vertex(x_max, y_min, z_min)
        v3 = self.add_vertex(x_max, y_max, z_min)
        v4 = self.add_vertex(x_min, y_max, z_min)
        v5 = self.add_vertex(x_min, y_min, z_max)
        v6 = self.add_vertex(x_max, y_min, z_max)
        v7 = self.add_vertex(x_max, y_max, z_max)
        v8 = self.add_vertex(x_min, y_max, z_max)
        self.add_quad(v1, v4, v3, v2) # Bottom
        self.add_quad(v5, v6, v7, v8) # Top
        self.add_quad(v1, v2, v6, v5) # Front
        self.add_quad(v3, v4, v8, v7) # Back
        self.add_quad(v4, v1, v5, v8) # Left
        self.add_quad(v2, v3, v7, v6) # Right

    def add_sloped_box(self, x_min, x_max, y_front, y_rear, z_front_bot, z_front_top, z_rear_bot, z_rear_top):
        v1 = self.add_vertex(x_min, y_front, z_front_bot)
        v2 = self.add_vertex(x_max, y_front, z_front_bot)
        v3 = self.add_vertex(x_max, y_rear, z_rear_bot)
        v4 = self.add_vertex(x_min, y_rear, z_rear_bot)
        v5 = self.add_vertex(x_min, y_front, z_front_top)
        v6 = self.add_vertex(x_max, y_front, z_front_top)
        v7 = self.add_vertex(x_max, y_rear, z_rear_top)
        v8 = self.add_vertex(x_min, y_rear, z_rear_top)
        self.add_quad(v1, v4, v3, v2)
        self.add_quad(v5, v6, v7, v8)
        self.add_quad(v1, v2, v6, v5)
        self.add_quad(v3, v4, v8, v7)
        self.add_quad(v4, v1, v5, v8)
        self.add_quad(v2, v3, v7, v6)

    def add_cylinder(self, cx, cy, z_min, z_max, radius, segments=10, axis='z'):
        if axis == 'z':
            bot_verts = []
            top_verts = []
            for i in range(segments):
                angle = 2.0 * math.pi * i / segments
                x = cx + radius * math.cos(angle)
                y = cy + radius * math.sin(angle)
                bot_verts.append(self.add_vertex(x, y, z_min))
                top_verts.append(self.add_vertex(x, y, z_max))
            c_bot = self.add_vertex(cx, cy, z_min)
            c_top = self.add_vertex(cx, cy, z_max)
            for i in range(segments):
                nxt = (i + 1) % segments
                self.add_tri(c_bot, bot_verts[nxt], bot_verts[i])
                self.add_tri(c_top, top_verts[i], top_verts[nxt])
                self.add_quad(bot_verts[i], bot_verts[nxt], top_verts[nxt], top_verts[i])
        elif axis == 'x':
            x_min, x_max, cen_y, cen_z = cx, cy, z_min, z_max
            l_verts = []
            r_verts = []
            for i in range(segments):
                angle = 2.0 * math.pi * i / segments
                y = cen_y + radius * math.cos(angle)
                z = cen_z + radius * math.sin(angle)
                l_verts.append(self.add_vertex(x_min, y, z))
                r_verts.append(self.add_vertex(x_max, y, z))
            cl = self.add_vertex(x_min, cen_y, cen_z)
            cr = self.add_vertex(x_max, cen_y, cen_z)
            for i in range(segments):
                nxt = (i + 1) % segments
                self.add_tri(cl, l_verts[i], l_verts[nxt])
                self.add_tri(cr, r_verts[nxt], r_verts[i])
                self.add_quad(l_verts[i], r_verts[i], r_verts[nxt], l_verts[nxt])

    def ground_align(self):
        if not self.vertices:
            return
        min_z = min(v[2] for v in self.vertices)
        if abs(min_z) > 0.001:
            self.vertices = [(v[0], v[1], round(v[2] - min_z, 2)) for v in self.vertices]

    def write_obj_and_mtl(self, obj_path, mtl_path):
        self.ground_align()
        mtl_filename = os.path.basename(mtl_path)
        with open(obj_path, "w", encoding="utf-8") as f:
            f.write(f"# Homesteader 3D Model: {self.name}\n")
            f.write(f"mtllib {mtl_filename}\n\n")
            for v in self.vertices:
                f.write(f"v {v[0]:.2f} {v[1]:.2f} {v[2]:.2f}\n")
            f.write("\n")
            for mat_name, faces in self.materials.items():
                if not faces:
                    continue
                f.write(f"usemtl {mat_name}\n")
                for face in faces:
                    f.write(f"f {' '.join(str(idx) for idx in face)}\n")

        with open(mtl_path, "w", encoding="utf-8") as f:
            f.write(f"# Material Library for {self.name}\n\n")
            for mat_name, color in self.mat_colors.items():
                r, g, b = color
                f.write(f"newmtl {mat_name}\n")
                f.write(f"Ka {r*0.4:.3f} {g*0.4:.3f} {b*0.4:.3f}\n")
                f.write(f"Kd {r:.3f} {g:.3f} {b:.3f}\n")
                f.write(f"Ks 0.250 0.250 0.250\n")
                f.write("Ns 25.0\n")
                f.write("d 1.0\n")
                f.write("illum 2\n\n")

# =========================================================================
# 28 INDIVIDUAL TOOL GENERATORS
# =========================================================================

def build_axe_felling():
    """tool_axe_felling.png: Curved hickory handle (#9c6838), wedged forged steel axe head (#4a5058) with silver cutting bit (#b8c0c8)"""
    m = MeshBuilder("SM_Tool_Axe_Felling")
    # Hickory Handle (L: 86cm, Curved ergonomic shape)
    m.set_material("mat_wood_hickory", 0.61, 0.41, 0.24)
    m.add_cylinder(0, 0, 0, 80, 2.2, segments=8, axis='z')
    # Flared grip knob at butt
    m.add_cylinder(0, -1, 0, 8, 3.2, segments=8, axis='z')
    # Lanyard hole
    m.set_material("mat_metal_dark", 0.20, 0.21, 0.24)
    m.add_box(-3, 3, -2, 0, 3, 5)

    # Forged Steel Axe Head (at Z: 70 to 86cm)
    m.set_material("mat_steel_axe", 0.32, 0.35, 0.38)
    # Eye collar around handle
    m.add_box(-3.5, 3.5, -4, 4, 70, 86)
    # Flat hammer poll on back (-Y)
    m.add_box(-3, 3, -10, -4, 71, 85)
    # Flared cutting bit on front (+Y)
    m.add_sloped_box(-2.5, 2.5, 4, 18, 70, 86, 68, 88)
    # Sharpened silver cutting bevel edge
    m.set_material("mat_silver_bevel", 0.78, 0.82, 0.86)
    m.add_sloped_box(-0.8, 0.8, 18, 22, 68, 88, 67, 89)

    return m

def build_hatchet_camp():
    """tool_hatchet_camp.png: Short carved wood handle, compact forged steel head"""
    m = MeshBuilder("SM_Tool_Hatchet_Camp")
    m.set_material("mat_wood_hickory", 0.65, 0.44, 0.26)
    m.add_cylinder(0, 0, 0, 38, 1.8, segments=8, axis='z')
    m.add_cylinder(0, -1, 0, 5, 2.6, segments=8, axis='z')
    # Head
    m.set_material("mat_steel_axe", 0.32, 0.35, 0.38)
    m.add_box(-2.5, 2.5, -3, 3, 30, 39)
    m.add_box(-2.2, 2.2, -7, -3, 31, 38)
    m.add_sloped_box(-1.8, 1.8, 3, 13, 30, 39, 28, 41)
    m.set_material("mat_silver_bevel", 0.78, 0.82, 0.86)
    m.add_sloped_box(-0.6, 0.6, 13, 16, 28, 41, 27, 42)
    return m

def build_chainsaw_gas_16():
    """tool_chainsaw.png: Orange 16\" gas chainsaw, wrap handle, chain bar"""
    m = MeshBuilder("SM_Tool_Chainsaw_Gas_16")
    # Orange Engine Body
    m.set_material("mat_saw_orange", 0.91, 0.42, 0.12)
    m.add_box(-11, 11, -18, 18, 0, 26)
    # Black top air filter shroud
    m.set_material("mat_metal_dark", 0.20, 0.21, 0.24)
    m.add_box(-9, 9, -15, 12, 26, 31)

    # Black Rear D-Handle with throttle trigger
    m.add_box(-3, 3, -34, -18, 4, 18)
    m.add_box(-3, 3, -34, -18, 18, 24)

    # Aluminum Wrap-Around Front Handlebar (Silver)
    m.set_material("mat_silver_bevel", 0.78, 0.82, 0.86)
    m.add_cylinder(-13, -2, 2, 28, 1.6, segments=6, axis='z')
    m.add_cylinder(13, -2, 2, 28, 1.6, segments=6, axis='z')
    m.add_cylinder(-13, 13, -2, 28, 1.6, segments=6, axis='x')

    # Black Chain Brake Hand Guard Lever
    m.set_material("mat_metal_dark", 0.20, 0.21, 0.24)
    m.add_box(-10, 10, 4, 8, 22, 34)

    # 16-Inch Silver Guide Bar (+Y: 18 to 65cm)
    m.set_material("mat_silver_bevel", 0.75, 0.78, 0.82)
    m.add_box(-0.8, 0.8, 18, 62, 7, 18)
    # Rounded bar nose
    m.add_cylinder(0, 62, 7, 18, 5.5, segments=8, axis='y')

    # Dark Toothed Cutting Chain Loop
    m.set_material("mat_metal_dark", 0.16, 0.17, 0.19)
    m.add_box(-1.2, 1.2, 18, 65, 17, 19.5)
    m.add_box(-1.2, 1.2, 18, 65, 5.5, 8)

    return m

def build_chainsaw_gas_20():
    """tool_chainsaw_gas_20.png: Heavy 20\" timber chainsaw with longer bar"""
    m = MeshBuilder("SM_Tool_Chainsaw_Gas_20")
    m.set_material("mat_saw_orange", 0.91, 0.42, 0.12)
    m.add_box(-13, 13, -22, 20, 0, 30)
    m.set_material("mat_metal_dark", 0.20, 0.21, 0.24)
    m.add_box(-10, 10, -18, 14, 30, 36)
    m.add_box(-3.5, 3.5, -40, -22, 5, 20)

    m.set_material("mat_silver_bevel", 0.78, 0.82, 0.86)
    m.add_cylinder(-15, -4, 3, 33, 1.8, segments=6, axis='z')
    m.add_cylinder(15, -4, 3, 33, 1.8, segments=6, axis='z')
    m.add_cylinder(-15, 15, -4, 33, 1.8, segments=6, axis='x')

    m.set_material("mat_metal_dark", 0.20, 0.21, 0.24)
    m.add_box(-12, 12, 6, 10, 26, 39)

    # 20-Inch Bar (+Y: 20 to 82cm)
    m.set_material("mat_silver_bevel", 0.75, 0.78, 0.82)
    m.add_box(-0.9, 0.9, 20, 78, 8, 21)
    m.set_material("mat_metal_dark", 0.16, 0.17, 0.19)
    m.add_box(-1.4, 1.4, 20, 82, 20, 22.5)
    m.add_box(-1.4, 1.4, 20, 82, 6.5, 9)

    return m

def build_cant_hook_peavey():
    """tool_cant_hook_peavey.png: Wood lever handle, forged steel duckbill cant hook and pike"""
    m = MeshBuilder("SM_Tool_CantHook_Peavey")
    # Heavy Ash Lever Handle (L: 120cm)
    m.set_material("mat_wood_hickory", 0.62, 0.42, 0.25)
    m.add_cylinder(0, 0, 15, 120, 2.5, segments=8, axis='z')
    # Forged Steel Tip Pike & Socket
    m.set_material("mat_metal_dark", 0.28, 0.30, 0.34)
    m.add_cylinder(0, 0, 5, 18, 3.2, segments=8, axis='z')
    m.add_cylinder(0, 0, 0, 6, 1.2, segments=6, axis='z') # sharp pike point

    # Pivoting Curved Duckbill Cant Hook Arm (Hooks outward +Y)
    m.add_box(-2.5, 2.5, 0, 5, 28, 36) # pivot bracket
    m.add_sloped_box(-1.8, 1.8, 4, 24, 30, 36, 10, 16) # curved arm
    m.add_box(-2, 2, 22, 26, 10, 16) # sharp duckbill toothed tip

    return m

def build_maul_splitting():
    """tool_maul_splitting.png: Yellow fiberglass handle with black grip, heavy sledge poll & splitting wedge bit"""
    m = MeshBuilder("SM_Tool_Maul_Splitting")
    # Yellow Fiberglass Handle
    m.set_material("mat_handle_yellow", 0.93, 0.82, 0.16)
    m.add_cylinder(0, 0, 0, 86, 2.4, segments=8, axis='z')
    # Black Molded Rubber Ergonomic Grip
    m.set_material("mat_metal_dark", 0.15, 0.16, 0.18)
    m.add_cylinder(0, 0, 0, 36, 2.8, segments=8, axis='z')
    # Yellow Lanyard Hole at butt
    m.set_material("mat_handle_yellow", 0.93, 0.82, 0.16)
    m.add_cylinder(0, 0, 2, 6, 1.2, segments=6, axis='x')

    # Massive Forged Steel Head (Z: 75 to 91cm)
    m.set_material("mat_steel_axe", 0.32, 0.35, 0.38)
    # Center collar
    m.add_box(-4.5, 4.5, -4.5, 4.5, 75, 91)
    # Massive Flat Sledge Hammer Poll on back (-Y)
    m.add_box(-4, 4, -14, -4.5, 76, 90)
    # Heavy Flared Splitting Wedge Bit on front (+Y)
    m.add_sloped_box(-4, 4, 4.5, 17, 76, 90, 74, 92)
    m.set_material("mat_silver_bevel", 0.78, 0.82, 0.86)
    m.add_sloped_box(-1.2, 1.2, 17, 21, 74, 92, 73, 93)

    return m

def build_shovel_round_point():
    """tool_shovel_round_point.png: Red D-handle, wood shaft, silver socket, pointed dish blade"""
    m = MeshBuilder("SM_Tool_Shovel_RoundPoint")
    # Red Molded D-Handle Grip at top (Z: 130 to 145cm)
    m.set_material("mat_handle_red", 0.82, 0.20, 0.16)
    m.add_box(-8, 8, -2.5, 2.5, 138, 145) # top bar
    m.add_box(-8, -5, -2, 2, 130, 140)   # left leg
    m.add_box(5, 8, -2, 2, 130, 140)     # right leg
    # Wooden grip tube inside D
    m.set_material("mat_wood_hickory", 0.62, 0.42, 0.25)
    m.add_cylinder(0, 0, 139, 144, 1.4, segments=6, axis='x')

    # Turned Ash Wood Shaft (Z: 42 to 132cm)
    m.add_cylinder(0, 0, 42, 132, 1.8, segments=8, axis='z')

    # Silver Steel Socket Sleeve (Z: 30 to 45cm)
    m.set_material("mat_silver_bevel", 0.75, 0.78, 0.82)
    m.add_cylinder(0, 0.5, 30, 45, 2.2, segments=8, axis='z')

    # Curved Round Point Dish Blade (Z: 0 to 32cm, W: 22cm)
    m.add_sloped_box(-11, 11, -3, 3, 10, 32, 8, 30) # upper dished blade
    # Forward-turned foot steps at top
    m.set_material("mat_metal_dark", 0.28, 0.30, 0.34)
    m.add_box(-11, 11, -5, -2, 29, 32)
    # Pointed shovel tip
    m.set_material("mat_silver_bevel", 0.75, 0.78, 0.82)
    m.add_sloped_box(-7, 7, -2, 2, 0, 12, 0, 10)

    return m

def build_shovel_scoop_flat():
    """tool_shovel_scoop_flat.png: Black D-handle, wood shaft, wide aluminum grain scoop"""
    m = MeshBuilder("SM_Tool_Shovel_ScoopFlat")
    m.set_material("mat_metal_dark", 0.18, 0.20, 0.22)
    m.add_box(-7, 7, -2.5, 2.5, 135, 142)
    m.add_box(-7, -4.5, -2, 2, 128, 136)
    m.add_box(4.5, 7, -2, 2, 128, 136)
    m.set_material("mat_wood_hickory", 0.62, 0.42, 0.25)
    m.add_cylinder(0, 0, 38, 130, 1.9, segments=8, axis='z')

    # Large Wide Aluminum Scoop Blade (W: 32cm, Z: 0 to 40cm)
    m.set_material("mat_silver_bevel", 0.82, 0.85, 0.89)
    m.add_box(-16, 16, -15, 6, 0, 36) # flat bottom
    # Flared side walls
    m.add_box(-16, -14, -15, 6, 0, 16)
    m.add_box(14, 16, -15, 6, 0, 16)

    return m

def build_shovel_trenching():
    """tool_shovel_trenching.png: Red D-handle, wood shaft, narrow V-trench cleanout blade"""
    m = MeshBuilder("SM_Tool_Shovel_Trenching")
    m.set_material("mat_handle_red", 0.82, 0.20, 0.16)
    m.add_box(-6, 6, -2, 2, 133, 140)
    m.add_box(-6, -4, -1.8, 1.8, 126, 134)
    m.add_box(4, 6, -1.8, 1.8, 126, 134)
    m.set_material("mat_wood_hickory", 0.62, 0.42, 0.25)
    m.add_cylinder(0, 0, 36, 128, 1.8, segments=8, axis='z')

    # Narrow 4-Inch V-Trench Blade (Z: 0 to 38cm, W: 10cm)
    m.set_material("mat_metal_dark", 0.28, 0.30, 0.34)
    m.add_sloped_box(-5, 5, -3, 3, 0, 38, 0, 36)
    # Forward foot step
    m.add_box(-5, 5, -6, -2, 34, 38)
    return m

def build_hoe():
    """tool_hoe.png: Wood handle, silver ferrule, swan-neck shank, draw hoe blade"""
    m = MeshBuilder("SM_Tool_Hoe")
    # Smooth Ash Handle (L: 135cm)
    m.set_material("mat_wood_hickory", 0.62, 0.42, 0.25)
    m.add_cylinder(0, 0, 12, 145, 1.6, segments=8, axis='z')
    # Silver Ferrule Socket Collar
    m.set_material("mat_silver_bevel", 0.78, 0.82, 0.86)
    m.add_cylinder(0, 0, 8, 14, 2.0, segments=8, axis='z')

    # Swan-Neck Goose Neck Curved Steel Shank
    m.set_material("mat_steel_axe", 0.35, 0.38, 0.42)
    m.add_sloped_box(-1, 1, 0, 12, 6, 10, 14, 18)
    m.add_sloped_box(-1, 1, 10, 14, 0, 6, 14, 18)

    # Trapezoidal Drop Hoe Blade (W: 18cm, angled back)
    m.set_material("mat_silver_bevel", 0.72, 0.76, 0.80)
    m.add_sloped_box(-9, 9, 10, 15, 0, 14, 0, 12)

    return m

def build_pickaxe():
    """tool_pickaxe.png: Faceted wood handle, central collar, curved chisel adze & pointed pick"""
    m = MeshBuilder("SM_Tool_Pickaxe")
    # Faceted Hickory Handle (L: 88cm)
    m.set_material("mat_wood_hickory", 0.62, 0.42, 0.25)
    m.add_cylinder(0, 0, 0, 85, 2.2, segments=8, axis='z')
    # Wood top protruding through collar
    m.add_cylinder(0, 0, 83, 88, 2.0, segments=8, axis='z')

    # Central Cast Steel Collar
    m.set_material("mat_steel_axe", 0.35, 0.38, 0.42)
    m.add_box(-4, 4, -4, 4, 70, 84)

    # Left: Curved Horizontal Chisel / Adze Blade (X: -42 to -4cm)
    m.set_material("mat_silver_bevel", 0.68, 0.72, 0.76)
    m.add_sloped_box(-38, -4, -3, 3, 68, 76, 70, 82)
    # Chisel cutting edge (broad horizontal flat)
    m.add_box(-44, -38, -5, 5, 66, 72)

    # Right: Curved Pointed Mining Pick Spike (X: 4 to 45cm)
    m.add_sloped_box(4, 38, -3, 3, 70, 82, 65, 75)
    # Pointed pick tip
    m.add_sloped_box(38, 45, -1.5, 1.5, 65, 75, 62, 66)

    return m

def build_sickle():
    """tool_sickle.png: Turned wood grip, brass ferrule, curved crescent blade"""
    m = MeshBuilder("SM_Tool_Sickle")
    # Wood Grip Handle
    m.set_material("mat_wood_hickory", 0.58, 0.38, 0.22)
    m.add_cylinder(0, 0, 0, 16, 1.8, segments=8, axis='z')
    # Brass Ferrule
    m.set_material("mat_handle_yellow", 0.85, 0.72, 0.24)
    m.add_cylinder(0, 0, 15, 18, 2.2, segments=8, axis='z')

    # Curved Crescent Steel Blade (Curving in XY plane)
    m.set_material("mat_silver_bevel", 0.78, 0.82, 0.86)
    # Segments approximating crescent arch
    pts = [(0, 18), (6, 26), (14, 34), (24, 38), (34, 34), (40, 24), (42, 10)]
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i+1]
        m.add_box(min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2), 16, 19)

    return m

def build_trowel_hand():
    """tool_trowel_hand.png: Rubber grip, cast aluminum cupped scoop blade"""
    m = MeshBuilder("SM_Tool_Trowel_Hand")
    m.set_material("mat_metal_dark", 0.18, 0.20, 0.22)
    m.add_cylinder(0, 0, 15, 30, 1.6, segments=8, axis='z')
    m.set_material("mat_silver_bevel", 0.82, 0.85, 0.89)
    m.add_cylinder(0, 0, 12, 16, 1.8, segments=8, axis='z')
    # Cupped Scoop Blade
    m.add_sloped_box(-4, 4, -2, 2, 0, 14, 2, 14)
    m.add_sloped_box(-2, 2, -1, 1, 0, 4, 0, 3) # point
    return m

def build_drill_cordless_20v():
    """DeWalt style yellow/black 20V cordless drill, battery on base, keyless chuck"""
    m = MeshBuilder("SM_Tool_Drill_Cordless_20V")
    # Flat 20V Battery Pack on Base
    m.set_material("mat_metal_dark", 0.15, 0.16, 0.18)
    m.add_box(-4, 4, -7, 7, 0, 6)

    # Yellow Pistol Grip Handle
    m.set_material("mat_handle_yellow", 0.92, 0.72, 0.14)
    m.add_sloped_box(-2.5, 2.5, -3, 3, 6, 18, 4, 18)
    # Red Trigger
    m.set_material("mat_handle_red", 0.82, 0.20, 0.16)
    m.add_box(-1, 1, 3, 5, 14, 17)

    # Yellow Main Motor Housing & Barrel
    m.set_material("mat_handle_yellow", 0.92, 0.72, 0.14)
    m.add_box(-4, 4, -8, 10, 17, 24)
    # Black rubber overmolding
    m.set_material("mat_metal_dark", 0.15, 0.16, 0.18)
    m.add_box(-4.2, 4.2, -8, -3, 17, 24)

    # Keyless Black Drill Chuck at front (+Y)
    m.add_cylinder(0, 10, 20.5, 20.5, 3.2, segments=8, axis='y')
    m.set_material("mat_silver_bevel", 0.78, 0.82, 0.86)
    m.add_cylinder(0, 15, 20.5, 20.5, 1.8, segments=8, axis='y')

    return m

def build_impact_driver_cordless():
    """Compact 20V impact driver with short nose and 1/4\" hex collet"""
    m = MeshBuilder("SM_Tool_ImpactDriver_Cordless")
    m.set_material("mat_metal_dark", 0.15, 0.16, 0.18)
    m.add_box(-3.5, 3.5, -6, 6, 0, 5.5)

    m.set_material("mat_handle_yellow", 0.92, 0.72, 0.14)
    m.add_sloped_box(-2.2, 2.2, -2.5, 2.5, 5.5, 16, 3.5, 16)
    m.set_material("mat_handle_red", 0.82, 0.20, 0.16)
    m.add_box(-1, 1, 2.5, 4.5, 13, 15.5)

    m.set_material("mat_handle_yellow", 0.92, 0.72, 0.14)
    m.add_box(-3.5, 3.5, -6, 6, 15, 22)

    # Hex Collet
    m.set_material("mat_silver_bevel", 0.78, 0.82, 0.86)
    m.add_cylinder(0, 6, 18.5, 18.5, 1.8, segments=6, axis='y')
    return m

def build_circular_saw_cordless():
    """Cordless 7-1/4\" circular saw, base shoe plate, blade guard, dual handles"""
    m = MeshBuilder("SM_Tool_CircularSaw_Cordless")
    # Base Shoe Plate (Silver flat plate on ground)
    m.set_material("mat_silver_bevel", 0.80, 0.83, 0.87)
    m.add_box(-11, 11, -14, 14, 0, 1.5)

    # Blade Guard & 7-1/4\" Blade
    m.set_material("mat_metal_dark", 0.25, 0.27, 0.30)
    m.add_box(3, 7, -10, 10, 1.5, 18)
    m.set_material("mat_silver_bevel", 0.82, 0.85, 0.89)
    m.add_cylinder(5, 0, 9, 9, 9.2, segments=12, axis='x') # circular blade

    # Motor Housing & Dual Handles
    m.set_material("mat_handle_yellow", 0.92, 0.72, 0.14)
    m.add_box(-10, 3, -6, 6, 6, 16)
    # Rear D-handle
    m.add_box(-7, -2, -18, -6, 8, 22)
    # Front auxiliary pommel grip
    m.set_material("mat_metal_dark", 0.18, 0.20, 0.22)
    m.add_cylinder(-4, 8, 12, 17, 1.8, segments=6, axis='z')

    return m

def build_angle_grinder_cordless():
    """4-1/2\" angle grinder, 90-degree gearhead, safety guard, cutoff wheel"""
    m = MeshBuilder("SM_Tool_AngleGrinder_Cordless")
    # Long Barrel Body with rear battery
    m.set_material("mat_handle_yellow", 0.92, 0.72, 0.14)
    m.add_cylinder(0, 0, 8, 28, 3.2, segments=8, axis='z')
    m.set_material("mat_metal_dark", 0.15, 0.16, 0.18)
    m.add_box(-3.5, 3.5, -3.5, 3.5, 24, 31) # battery

    # 90-Degree Cast Aluminum Gearhead
    m.set_material("mat_silver_bevel", 0.75, 0.78, 0.82)
    m.add_box(-4, 4, -4, 4, 3, 8)
    # Side Auxiliary Handle
    m.set_material("mat_metal_dark", 0.18, 0.20, 0.22)
    m.add_box(4, 15, -1.8, 1.8, 4, 7)

    # Steel Wheel Guard & Abrasive Cutoff Disc (Radius 5.7cm)
    m.set_material("mat_metal_dark", 0.25, 0.27, 0.30)
    m.add_cylinder(0, 0, 2, 4, 6.2, segments=10, axis='z')
    m.set_material("mat_chassis_dark", 0.15, 0.15, 0.15)
    m.add_cylinder(0, 0, 0, 1.5, 5.7, segments=12, axis='z')

    return m

def build_miter_saw():
    """Sliding compound miter saw on turntable base with fence and blade guard"""
    m = MeshBuilder("SM_Tool_MiterSaw")
    # Turntable Base & Table Wings
    m.set_material("mat_silver_bevel", 0.75, 0.78, 0.82)
    m.add_box(-25, 25, -22, 22, 0, 6) # base
    m.set_material("mat_handle_yellow", 0.92, 0.72, 0.14)
    m.add_cylinder(0, 0, 6, 7.5, 14, segments=12, axis='z') # turntable

    # Back Fence
    m.set_material("mat_silver_bevel", 0.72, 0.75, 0.80)
    m.add_box(-24, 24, 6, 10, 6, 16)

    # Pivot Arm & 10\" Blade Housing
    m.set_material("mat_silver_bevel", 0.80, 0.83, 0.87)
    m.add_box(-4, 4, -8, 8, 16, 36)
    m.set_material("mat_handle_yellow", 0.92, 0.72, 0.14)
    m.add_box(-12, -4, -6, 6, 22, 32) # motor
    # Top Trigger Handle
    m.add_box(-3, 3, -16, -6, 34, 42)

    return m

def build_table_saw():
    """Jobsite contractor table saw on folding stand with rip fence and blade"""
    m = MeshBuilder("SM_Tool_TableSaw")
    # Steel Tubular Folding Stand Legs
    m.set_material("mat_metal_dark", 0.20, 0.22, 0.25)
    m.add_box(-32, -28, -32, 32, 0, 65)
    m.add_box(28, 32, -32, 32, 0, 65)

    # Yellow Table Saw Body Cabinet
    m.set_material("mat_handle_yellow", 0.92, 0.72, 0.14)
    m.add_box(-28, 28, -28, 28, 45, 78)

    # Precision Aluminum Table Top (Ground level Z: 78 to 82cm)
    m.set_material("mat_silver_bevel", 0.82, 0.85, 0.89)
    m.add_box(-35, 35, -36, 36, 78, 82)

    # Rip Fence (Runs front to back)
    m.set_material("mat_metal_dark", 0.22, 0.24, 0.26)
    m.add_box(14, 18, -36, 36, 82, 88)

    # 10\" Circular Saw Blade & Guard
    m.set_material("mat_silver_bevel", 0.75, 0.78, 0.82)
    m.add_box(-0.8, 0.8, -12, 12, 82, 92)

    return m

def build_watering_can():
    """tool_watering_can.png: Galvanized steel can, top/rear handles, angled spout with brass rose"""
    m = MeshBuilder("SM_Tool_WateringCan")
    # Cylindrical Galvanized Steel Body (Radius 11cm, H: 28cm)
    m.set_material("mat_silver_bevel", 0.72, 0.76, 0.80)
    m.add_cylinder(0, 0, 0, 28, 11, segments=12, axis='z')

    # Arched Overhead Carry Handle
    m.add_box(-1.5, 1.5, -9, 9, 28, 42)

    # Rear Pouring Loop Handle
    m.add_box(-1.5, 1.5, -18, -11, 8, 26)

    # Angled Front Spout Tube (Spouts outward +Y)
    m.add_sloped_box(-2, 2, 9, 24, 6, 10, 24, 28)

    # Brass Perforated Rose Head Sprinkler Disc
    m.set_material("mat_handle_yellow", 0.85, 0.72, 0.24)
    m.add_cylinder(0, 25, 27, 31, 4.5, segments=10, axis='z')

    return m

def build_shears_pruning():
    """tool_shears_pruning.png: Red vinyl handles, curved bypass cutting blade"""
    m = MeshBuilder("SM_Tool_Shears_Pruning")
    # Red Handles
    m.set_material("mat_handle_red", 0.82, 0.20, 0.16)
    m.add_box(-3, -0.5, -12, 0, 0, 3)
    m.add_box(0.5, 3, -12, 0, 0, 3)

    # Bypass Steel Jaws (Z: 0 to 9cm)
    m.set_material("mat_silver_bevel", 0.78, 0.82, 0.86)
    m.add_box(-2, 0, 0, 9, 0.5, 2.5) # anvil hook
    m.add_box(0, 2, 0, 9, 0.5, 2.5)  # cutting blade
    # Brass pivot bolt
    m.set_material("mat_handle_yellow", 0.85, 0.72, 0.24)
    m.add_cylinder(0, 1, 0, 3, 1.2, segments=6, axis='z')

    return m

def build_loppers_heavy():
    """tool_loppers_heavy.png: Dual long arms, cushioned grips, heavy bypass jaws"""
    m = MeshBuilder("SM_Tool_Loppers_Heavy")
    # Dual Tubular Arms (L: 55cm)
    m.set_material("mat_silver_bevel", 0.75, 0.78, 0.82)
    m.add_cylinder(-5, 0, 15, 70, 1.4, segments=6, axis='z')
    m.add_cylinder(5,  0, 15, 70, 1.4, segments=6, axis='z')
    # Black Cushioned Handgrips
    m.set_material("mat_metal_dark", 0.18, 0.20, 0.22)
    m.add_cylinder(-5, 0, 45, 74, 1.8, segments=6, axis='z')
    m.add_cylinder(5,  0, 45, 74, 1.8, segments=6, axis='z')

    # Heavy Forged Bypass Jaws (Z: 0 to 18cm)
    m.set_material("mat_steel_axe", 0.35, 0.38, 0.42)
    m.add_box(-6, 6, -2, 2, 0, 16)

    return m

def build_sprayer_backpack():
    """sprayer_backpack_4gal.png: White poly tank, straps, pump lever, spray wand"""
    m = MeshBuilder("SM_Tool_Sprayer_Backpack")
    # Translucent White Poly Tank (W: 34cm, H: 48cm)
    m.set_material("mat_silver_bevel", 0.90, 0.92, 0.94)
    m.add_box(-16, 16, -10, 10, 8, 48)
    # Dark Base Stand
    m.set_material("mat_metal_dark", 0.18, 0.20, 0.22)
    m.add_box(-17, 17, -11, 11, 0, 8)
    # Screw-on Cap
    m.add_cylinder(0, 0, 48, 52, 6, segments=8, axis='z')

    # Steel Pump Lever on side
    m.add_box(-20, -16, -12, 12, 4, 8)
    # Brass Wand clipped to side
    m.set_material("mat_handle_yellow", 0.85, 0.72, 0.24)
    m.add_cylinder(18, 0, 4, 52, 0.8, segments=6, axis='z')

    return m

def build_wand_watering():
    """wand_watering_brass.png: 30\" aluminum wand, brass valve, shower head"""
    m = MeshBuilder("SM_Tool_Wand_Watering")
    # Aluminum Wand Tube (L: 75cm)
    m.set_material("mat_silver_bevel", 0.80, 0.83, 0.87)
    m.add_cylinder(0, 0, 12, 80, 0.9, segments=6, axis='z')

    # Pistol-Grip Handle & Brass Valve (Z: 0 to 14cm)
    m.set_material("mat_metal_dark", 0.18, 0.20, 0.22)
    m.add_box(-2, 2, -4, 4, 0, 12)
    m.set_material("mat_handle_yellow", 0.85, 0.72, 0.24)
    m.add_box(-1.5, 1.5, 2, 5, 8, 14) # brass valve lever

    # Angled Multi-Pattern Shower Head at tip
    m.set_material("mat_handle_red", 0.82, 0.20, 0.16)
    m.add_cylinder(0, 2, 78, 84, 4.0, segments=10, axis='z')

    return m

def build_pail_milk_stainless():
    """pail_milk_stainless.png: Seamless stainless steel pail, wire bail handle"""
    m = MeshBuilder("SM_Tool_Pail_Milk_Stainless")
    # Flared Stainless Pail Body (Bottom R: 11cm, Top R: 14cm, H: 30cm)
    m.set_material("mat_silver_bevel", 0.82, 0.85, 0.89)
    m.add_cylinder(0, 0, 0, 30, 13, segments=12, axis='z')
    # Rim bead
    m.add_cylinder(0, 0, 28, 31, 14.2, segments=12, axis='z')

    # Heavy Wire Bail Handle (Arched over top)
    m.add_cylinder(0, 0, 30, 42, 12.5, segments=10, axis='y')

    return m

def build_shears_sheep_wool():
    """shears_sheep_wool.png: Single-bow spring steel wool fleece shears"""
    m = MeshBuilder("SM_Tool_Shears_SheepWool")
    # Single Bow Spring Loop at bottom (Z: 0 to 8cm)
    m.set_material("mat_steel_axe", 0.35, 0.38, 0.42)
    m.add_cylinder(0, 0, 0, 8, 3.2, segments=8, axis='x')

    # Dual Scissor Blades (Z: 8 to 30cm)
    m.set_material("mat_silver_bevel", 0.78, 0.82, 0.86)
    m.add_sloped_box(-3, -0.5, -1, 1, 8, 30, 8, 28)
    m.add_sloped_box(0.5, 3, -1, 1, 8, 30, 8, 28)

    return m

def build_paddle_sorting():
    """paddle_sorting_cattle.png: Red sorting rattle paddle with grip shaft"""
    m = MeshBuilder("SM_Tool_Paddle_Sorting")
    # Grip Shaft (L: 80cm)
    m.set_material("mat_metal_dark", 0.20, 0.22, 0.25)
    m.add_cylinder(0, 0, 0, 80, 1.4, segments=6, axis='z')

    # Red Vinyl Sorting Paddle Head (Z: 75 to 112cm, W: 14cm)
    m.set_material("mat_handle_red", 0.85, 0.18, 0.14)
    m.add_box(-7, 7, -2, 2, 75, 112)

    return m

def build_helmet_logging_safety():
    """helmet_logging_safety.png: Hi-vis orange logging helmet, hearing muffs, mesh face shield"""
    m = MeshBuilder("SM_Tool_Helmet_LoggingSafety")
    # Orange Hard Hat Dome (Z: 6 to 22cm)
    m.set_material("mat_saw_orange", 0.94, 0.45, 0.10)
    m.add_cylinder(0, 0, 8, 22, 14, segments=12, axis='z')
    # Brim visor at front
    m.add_box(-12, 12, -18, -12, 8, 10)

    # Black Hearing Protection Ear Muffs (Left & Right)
    m.set_material("mat_metal_dark", 0.18, 0.20, 0.22)
    m.add_cylinder(-16, 0, 1, 11, 4.5, segments=8, axis='x')
    m.add_cylinder(16, 0, 1, 11, 4.5, segments=8, axis='x')

    # Steel Mesh Face Shield Visor (Curved in front)
    m.set_material("mat_steel_axe", 0.40, 0.44, 0.48)
    m.add_box(-12, 12, -16, -14, 0, 10)

    return m

# =========================================================================
# MAIN
# =========================================================================

def main():
    print("=====================================================================")
    print("  REBUILDING BATCH 2: 28 HANDHELD TOOLS & WEARABLES MODELS")
    print("  Faithfully matching original item icons in HUD/assets/items/")
    print("=====================================================================")

    tools = [
        # Forestry
        ("SM_Tool_Axe_Felling", build_axe_felling, "tool_axe_felling.png"),
        ("SM_Tool_Hatchet_Camp", build_hatchet_camp, "tool_hatchet_camp.png"),
        ("SM_Tool_Chainsaw_Gas_16", build_chainsaw_gas_16, "tool_chainsaw.png"),
        ("SM_Tool_Chainsaw_Gas_20", build_chainsaw_gas_20, "tool_chainsaw_gas_20.png"),
        ("SM_Tool_CantHook_Peavey", build_cant_hook_peavey, "tool_cant_hook_peavey.png"),
        ("SM_Tool_Maul_Splitting", build_maul_splitting, "tool_maul_splitting.png"),

        # Digging & Garden
        ("SM_Tool_Shovel_RoundPoint", build_shovel_round_point, "tool_shovel_round_point.png"),
        ("SM_Tool_Shovel_ScoopFlat", build_shovel_scoop_flat, "tool_shovel_scoop_flat.png"),
        ("SM_Tool_Shovel_Trenching", build_shovel_trenching, "tool_shovel_trenching.png"),
        ("SM_Tool_Hoe", build_hoe, "tool_hoe.png"),
        ("SM_Tool_Pickaxe", build_pickaxe, "tool_pickaxe.png"),
        ("SM_Tool_Sickle", build_sickle, "tool_sickle.png"),
        ("SM_Tool_Trowel_Hand", build_trowel_hand, "tool_trowel_hand.png"),

        # Power Tools
        ("SM_Tool_Drill_Cordless_20V", build_drill_cordless_20v, "tool_drill_cordless_20v.png"),
        ("SM_Tool_ImpactDriver_Cordless", build_impact_driver_cordless, "tool_impact_driver_cordless.png"),
        ("SM_Tool_CircularSaw_Cordless", build_circular_saw_cordless, "tool_circular_saw_cordless.png"),
        ("SM_Tool_AngleGrinder_Cordless", build_angle_grinder_cordless, "tool_angle_grinder_cordless.png"),
        ("SM_Tool_MiterSaw", build_miter_saw, "tool_miter_saw.png"),
        ("SM_Tool_TableSaw", build_table_saw, "tool_table_saw.png"),

        # Care, Livestock & Safety
        ("SM_Tool_WateringCan", build_watering_can, "tool_watering_can.png"),
        ("SM_Tool_Shears_Pruning", build_shears_pruning, "tool_shears_pruning.png"),
        ("SM_Tool_Loppers_Heavy", build_loppers_heavy, "tool_loppers_heavy.png"),
        ("SM_Tool_Sprayer_Backpack", build_sprayer_backpack, "sprayer_backpack_4gal.png"),
        ("SM_Tool_Wand_Watering", build_wand_watering, "wand_watering_brass.png"),
        ("SM_Tool_Pail_Milk_Stainless", build_pail_milk_stainless, "pail_milk_stainless.png"),
        ("SM_Tool_Shears_SheepWool", build_shears_sheep_wool, "shears_sheep_wool.png"),
        ("SM_Tool_Paddle_Sorting", build_paddle_sorting, "paddle_sorting_cattle.png"),
        ("SM_Tool_Helmet_LoggingSafety", build_helmet_logging_safety, "helmet_logging_safety.png"),
    ]

    for model_name, gen_func, source_icon_file in tools:
        print(f"\n--> Generating {model_name}...")
        builder = gen_func()

        hud_obj = os.path.join(HUD_MODELS, f"{model_name}.obj")
        hud_mtl = os.path.join(HUD_MODELS, f"{model_name}.mtl")
        ue5_obj = os.path.join(UE5_MODELS, f"{model_name}.obj")
        ue5_mtl = os.path.join(UE5_MODELS, f"{model_name}.mtl")

        builder.write_obj_and_mtl(hud_obj, hud_mtl)
        shutil.copy2(hud_obj, ue5_obj)
        shutil.copy2(hud_mtl, ue5_mtl)

        # Sync Preview Icon from source icon in assets/items/
        src_icon_path = os.path.join(ITEMS_DIR, source_icon_file)
        hud_icon = os.path.join(HUD_ICONS, f"{model_name}.png")
        ue5_icon = os.path.join(UE5_ICONS, f"{model_name}.png")

        if os.path.exists(src_icon_path):
            shutil.copy2(src_icon_path, hud_icon)
            shutil.copy2(src_icon_path, ue5_icon)
            print(f"    [ICON] Synced matching icon from {source_icon_file}")
        else:
            print(f"    [WARN] Source icon not found at {src_icon_path}")

        num_faces = sum(len(f) for f in builder.materials.values())
        print(f"    [DONE] {model_name}: {len(builder.vertices)} verts, {num_faces} tris.")

    print("\nBatch 2 successfully rebuilt and synchronized across HUD and UE5!")

if __name__ == "__main__":
    main()
