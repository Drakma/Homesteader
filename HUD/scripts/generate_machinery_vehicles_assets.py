#!/usr/bin/env python3
"""
Homesteader Heavy Machinery, Vehicles & Structures 3D Asset Generator
====================================================================
FAITHFULLY REBUILT TO MATCH ITEM ICONS IN HUD/assets/items/:
1. SM_Machine_Tractor_Large    <- machine_tractor_large.png (Red cab tractor, curved hood, white pillars, red roof, black exhaust, silver hubs)
2. SM_Machine_Tractor_Small    <- machine_tractor_small.png (Red open-station tractor, 4-post red ROPS canopy, seat, vertical chrome exhaust)
3. SM_Machine_Combine_Large    <- machine_combine_large.png (Green combine, yellow grain hopper, angled cab, black front reel header)
4. SM_Machine_Combine_Small    <- machine_combine_small.png (Compact green combine, yellow hopper, cab, reel header)
5. SM_Machine_Excavator_Large  <- machine_excavator_large.png (CAT yellow excavator, black accent band, left cab, black tracks, yellow boom/stick, bucket)
6. SM_Machine_Excavator_Small  <- machine_excavator_small.png (Yellow mini excavator, white cab, black rubber tracks, dozer blade, bucket)
7. SM_Machine_Skidsteer_Large  <- machine_skidsteer_large.png (Orange skid steer, mesh cab, 4 offroad tires with orange hubs, front bucket)
8. SM_Machine_Skidsteer_Small  <- machine_skidsteer_small.png (Compact orange wheeled skid steer, ROPS cage, bucket)
9. SM_Machine_Sawmill_Portable <- machine_sawmill_portable.png (Orange trailer chassis, A-frame tongue, white wheels, log on bed, orange saw carriage)
10. SM_Machine_Sawmill_Stationary <- machine_sawmill_stationary.png (White/silver rail bed, green cross bunks, green saw carriage head)
11. SM_Struct_Camper_RV        <- struct_camper_rv.png (White travel trailer, blue stripe, blue deployed awning, front A-frame hitch with propane tank cover)
12. SM_Struct_Camper_Teardrop  <- struct_camper_teardrop.png (Two-tone cream/gray teardrop trailer, front tub, porthole windows, chrome fender)
13. SM_Struct_Silo             <- struct_silo.png (Corrugated galvanized hopper bin, conical bottom, 6 steel legs, round concrete footing)
14. SM_Struct_Stable           <- struct_stable.png (Timber stable barn, saltbox roof, open breezeway end, 3 stall bays with X-braced Dutch doors and stall bars)

Standards:
- 1 grid tile = 1m x 1m = 100 UU x 100 UU
- Ground-aligned pivot (Z_min = 0.0)
- Watertight 360-degree geometry (all 4 sides rotatable)
- Dual workspace sync: HUD/assets/ and Homesteader/Content/Homesteader/
"""

import os
import sys
import math
import shutil
from PIL import Image, ImageDraw

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

HUD_ASSETS = os.path.join(PROJECT_ROOT, "HUD", "assets")
UE5_ASSETS = os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader")

DESTINATIONS = {
    "farming": {
        "hud_models": os.path.join(HUD_ASSETS, "farming", "models"),
        "hud_icons":  os.path.join(HUD_ASSETS, "farming", "icons"),
        "ue5_models": os.path.join(UE5_ASSETS, "Assets", "Farming", "Meshes"),
        "ue5_icons":  os.path.join(UE5_ASSETS, "UI", "Icons", "farming"),
    },
    "tools": {
        "hud_models": os.path.join(HUD_ASSETS, "tools", "models"),
        "hud_icons":  os.path.join(HUD_ASSETS, "tools", "icons"),
        "ue5_models": os.path.join(UE5_ASSETS, "Assets", "Tools", "Meshes"),
        "ue5_icons":  os.path.join(UE5_ASSETS, "UI", "Icons", "tools"),
    },
    "logging": {
        "hud_models": os.path.join(HUD_ASSETS, "logging", "models"),
        "hud_icons":  os.path.join(HUD_ASSETS, "logging", "icons"),
        "ue5_models": os.path.join(UE5_ASSETS, "Assets", "Logging", "Meshes"),
        "ue5_icons":  os.path.join(UE5_ASSETS, "UI", "Icons", "logging"),
    },
    "building": {
        "hud_models": os.path.join(HUD_ASSETS, "building", "models"),
        "hud_icons":  os.path.join(HUD_ASSETS, "building", "icons"),
        "ue5_models": os.path.join(UE5_ASSETS, "Assets", "Building", "Meshes"),
        "ue5_icons":  os.path.join(UE5_ASSETS, "UI", "Icons", "building"),
    }
}

for cat in DESTINATIONS.values():
    for p in cat.values():
        os.makedirs(p, exist_ok=True)

class MeshBuilder:
    def __init__(self, name):
        self.name = name
        self.vertices = []
        self.materials = {}  # mat_name -> list of faces (each face: list of 1-based vertex indices)
        self.mat_colors = {} # mat_name -> (r, g, b) floats in [0, 1]
        self.current_mat = "default"

    def set_material(self, mat_name, r, g, b):
        self.current_mat = mat_name
        if mat_name not in self.materials:
            self.materials[mat_name] = []
            self.mat_colors[mat_name] = (r, g, b)

    def add_vertex(self, x, y, z):
        self.vertices.append((round(x, 2), round(y, 2), round(z, 2)))
        return len(self.vertices)

    def add_quad(self, v1, v2, v3, v4):
        # Add as two triangles for clean triangulation
        self.materials[self.current_mat].append((v1, v2, v3))
        self.materials[self.current_mat].append((v1, v3, v4))

    def add_tri(self, v1, v2, v3):
        self.materials[self.current_mat].append((v1, v2, v3))

    def add_box(self, x_min, x_max, y_min, y_max, z_min, z_max):
        v1 = self.add_vertex(x_min, y_min, z_min)
        v2 = self.add_vertex(x_max, y_min, z_min)
        v3 = self.add_vertex(x_max, y_max, z_min)
        v4 = self.add_vertex(x_min, y_max, z_min)
        v5 = self.add_vertex(x_min, y_min, z_max)
        v6 = self.add_vertex(x_max, y_min, z_max)
        v7 = self.add_vertex(x_max, y_max, z_max)
        v8 = self.add_vertex(x_min, y_max, z_max)
        # Bottom
        self.add_quad(v1, v4, v3, v2)
        # Top
        self.add_quad(v5, v6, v7, v8)
        # Front (-Y)
        self.add_quad(v1, v2, v6, v5)
        # Back (+Y)
        self.add_quad(v3, v4, v8, v7)
        # Left (-X)
        self.add_quad(v4, v1, v5, v8)
        # Right (+X)
        self.add_quad(v2, v3, v7, v6)

    def add_sloped_hood(self, x_min, x_max, y_front, y_rear, z_front_bot, z_front_top, z_rear_bot, z_rear_top):
        # 8 vertices for a tapered box/hood
        v1 = self.add_vertex(x_min, y_front, z_front_bot)
        v2 = self.add_vertex(x_max, y_front, z_front_bot)
        v3 = self.add_vertex(x_max, y_rear, z_rear_bot)
        v4 = self.add_vertex(x_min, y_rear, z_rear_bot)
        v5 = self.add_vertex(x_min, y_front, z_front_top)
        v6 = self.add_vertex(x_max, y_front, z_front_top)
        v7 = self.add_vertex(x_max, y_rear, z_rear_top)
        v8 = self.add_vertex(x_min, y_rear, z_rear_top)
        self.add_quad(v1, v4, v3, v2) # bottom
        self.add_quad(v5, v6, v7, v8) # top (sloped)
        self.add_quad(v1, v2, v6, v5) # front
        self.add_quad(v3, v4, v8, v7) # rear
        self.add_quad(v4, v1, v5, v8) # left
        self.add_quad(v2, v3, v7, v6) # right

    def add_cylinder(self, cx, cy, z_min, z_max, radius, segments=12, axis='z'):
        """Generates cylinder along specified axis (x, y, or z)"""
        if axis == 'z':
            bot_verts = []
            top_verts = []
            for i in range(segments):
                angle = 2.0 * math.pi * i / segments
                x = cx + radius * math.cos(angle)
                y = cy + radius * math.sin(angle)
                bot_verts.append(self.add_vertex(x, y, z_min))
                top_verts.append(self.add_vertex(x, y, z_max))
            # Caps
            c_bot = self.add_vertex(cx, cy, z_min)
            c_top = self.add_vertex(cx, cy, z_max)
            for i in range(segments):
                nxt = (i + 1) % segments
                self.add_tri(c_bot, bot_verts[nxt], bot_verts[i])
                self.add_tri(c_top, top_verts[i], top_verts[nxt])
                self.add_quad(bot_verts[i], bot_verts[nxt], top_verts[nxt], top_verts[i])
        elif axis == 'x':
            # Cylinder along X (like wheel axle)
            # cx is min_x, cy is max_x, z_min is center Y, z_max is center Z
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
        elif axis == 'y':
            # Cylinder along Y (like horizontal log on bed)
            y_min, y_max, cen_x, cen_z = cy, z_min, cx, z_max
            f_verts = []
            b_verts = []
            for i in range(segments):
                angle = 2.0 * math.pi * i / segments
                x = cen_x + radius * math.cos(angle)
                z = cen_z + radius * math.sin(angle)
                f_verts.append(self.add_vertex(x, y_min, z))
                b_verts.append(self.add_vertex(x, y_max, z))
            cf = self.add_vertex(cen_x, y_min, cen_z)
            cb = self.add_vertex(cen_x, y_max, cen_z)
            for i in range(segments):
                nxt = (i + 1) % segments
                self.add_tri(cf, f_verts[nxt], f_verts[i])
                self.add_tri(cb, b_verts[i], b_verts[nxt])
                self.add_quad(f_verts[i], f_verts[nxt], b_verts[nxt], b_verts[i])

    def add_wheel(self, x_center, y_center, z_center, radius, width, is_left=True):
        """Builds detailed treaded wheel with rim and hub matching tractor/machine icons"""
        half_w = width / 2.0
        x_in = x_center - half_w if is_left else x_center + half_w
        x_out = x_center + half_w if is_left else x_center - half_w
        
        # Tire body (dark charcoal)
        self.set_material("mat_tire_rubber", 0.12, 0.13, 0.15)
        self.add_cylinder(min(x_in, x_out), max(x_in, x_out), y_center, z_center, radius, segments=14, axis='x')
        
        # Outer rim inset (silver or rim color)
        rim_r = radius * 0.58
        rim_out = x_out + (0.8 if is_left else -0.8)
        self.set_material("mat_wheel_rim", 0.72, 0.74, 0.78)
        self.add_cylinder(min(x_out, rim_out), max(x_out, rim_out), y_center, z_center, rim_r, segments=12, axis='x')

    def add_track(self, x_center, y_min, y_max, z_min, z_max, width):
        """Excavator track tread pair with rollers"""
        half_w = width / 2.0
        x1 = x_center - half_w
        x2 = x_center + half_w
        # Main rubber/steel track band
        self.set_material("mat_track_steel", 0.13, 0.14, 0.16)
        self.add_box(x1, x2, y_min, y_max, z_min, z_max)
        # Drive sprockets & idlers at ends
        r = (z_max - z_min) / 2.0
        zc = z_min + r
        self.set_material("mat_track_sprocket", 0.35, 0.37, 0.40)
        self.add_cylinder(x1 - 1, x2 + 1, y_min, zc, r, segments=10, axis='x')
        self.add_cylinder(x1 - 1, x2 + 1, y_max, zc, r, segments=10, axis='x')

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
                f.write(f"Ks 0.200 0.200 0.200\n")
                f.write("Ns 20.0\n")
                f.write("d 1.0\n")
                f.write("illum 2\n\n")

# =========================================================================
# 14 PRECISE ICON-MATCHING GENERATORS
# =========================================================================

def build_tractor_large():
    """
    Matches machine_tractor_large.png:
    - RED body & sloping hood (#d33626)
    - Front white/silver grille (#e0e4e8)
    - White cab frame pillars (#f0f2f5)
    - Dark tinted cab glass (#3a4856)
    - Red cab roof cap (#d33626) with amber roof lights (#e8a838)
    - Big rear tires (#1e2024) with silver wheel rims (#9ca3af)
    - Smaller front steer wheels (#1e2024) with silver rims
    - Vertical black exhaust pipe on left side of hood
    """
    m = MeshBuilder("SM_Machine_Tractor_Large")
    # Overall: W: 240cm, L: 420cm, H: 310cm
    # Chassis / Engine block
    m.set_material("mat_chassis_dark", 0.15, 0.16, 0.18)
    m.add_box(-55, 55, -170, 150, 45, 95)
    
    # Red Sloping Hood (Front -170 to 10, Height 95 to 175)
    m.set_material("mat_tractor_red", 0.82, 0.21, 0.15)
    m.add_sloped_hood(-50, 50, -170, 15, 60, 145, 75, 175)
    
    # Front Grille (White/silver mesh on front of hood)
    m.set_material("mat_grille_white", 0.90, 0.92, 0.95)
    m.add_box(-44, 44, -172, -170, 75, 138)
    # Headlight lenses
    m.set_material("mat_amber_light", 0.96, 0.80, 0.25)
    m.add_box(-42, -28, -173, -171, 120, 134)
    m.add_box(28, 42, -173, -171, 120, 134)

    # Vertical Exhaust Pipe on Left Side
    m.set_material("mat_exhaust_dark", 0.18, 0.19, 0.22)
    m.add_cylinder(-53, -60, 145, 275, 5.0, segments=8, axis='z')
    # Rain cap
    m.add_box(-58, -48, -65, -55, 275, 280)

    # Enclosed Operator Cab (Y: 15 to 160, Z: 95 to 295)
    # Cab Interior Floor & Seat
    m.set_material("mat_chassis_dark", 0.15, 0.16, 0.18)
    m.add_box(-60, 60, 15, 160, 95, 110)
    m.add_box(-22, 22, 50, 110, 110, 165) # seat
    m.add_cylinder(0, 35, 130, 155, 12, segments=8, axis='z') # steering wheel

    # Tinted Cab Glass
    m.set_material("mat_cab_glass", 0.25, 0.35, 0.45)
    m.add_box(-68, 68, 20, 155, 115, 275)

    # White Cab Structural Pillars & Door Frames (distinct in icon!)
    m.set_material("mat_cab_pillar_white", 0.92, 0.93, 0.96)
    # 4 corner pillars
    m.add_box(-72, -64, 16, 26, 110, 285) # front left
    m.add_box(64, 72, 16, 26, 110, 285)  # front right
    m.add_box(-72, -64, 145, 158, 110, 285) # rear left
    m.add_box(64, 72, 145, 158, 110, 285)  # rear right
    # Header rails
    m.add_box(-72, 72, 16, 24, 275, 285)
    m.add_box(-72, 72, 150, 158, 275, 285)

    # Red Cab Roof Cap with Overhang
    m.set_material("mat_tractor_red", 0.82, 0.21, 0.15)
    m.add_box(-76, 76, 10, 165, 285, 305)
    # Amber roof cab marker lights
    m.set_material("mat_amber_light", 0.96, 0.80, 0.25)
    m.add_box(-65, -45, 8, 11, 290, 298)
    m.add_box(45, 65, 8, 11, 290, 298)

    # Red Rear Curved Wheel Fenders
    m.add_box(-112, -72, 35, 175, 165, 185) # left fender
    m.add_box(72, 112, 35, 175, 165, 185)  # right fender

    # Big Rear Off-Road Wheels (Radius 78cm, Width 42cm)
    m.add_wheel(x_center=-92, y_center=105, z_center=78, radius=78, width=40, is_left=True)
    m.add_wheel(x_center=92,  y_center=105, z_center=78, radius=78, width=40, is_left=False)

    # Smaller Front Steer Wheels (Radius 50cm, Width 32cm)
    m.add_wheel(x_center=-78, y_center=-135, z_center=50, radius=50, width=30, is_left=True)
    m.add_wheel(x_center=78,  y_center=-135, z_center=50, radius=50, width=30, is_left=False)

    return m

def build_tractor_small():
    """
    Matches machine_tractor_small.png:
    - RED curved sloping hood (#d33626) with white grille
    - Open-station platform with black seat & steering wheel
    - 4-post steel ROPS canopy with RED roof cap
    - Vertical chrome exhaust pipe on left side of hood
    - Red rear curved fenders
    - Big rear wheels with silver rims, smaller front wheels
    """
    m = MeshBuilder("SM_Machine_Tractor_Small")
    # Overall: W: 165cm, L: 310cm, H: 225cm
    m.set_material("mat_chassis_dark", 0.15, 0.16, 0.18)
    m.add_box(-38, 38, -125, 95, 36, 75)

    # Red Hood
    m.set_material("mat_tractor_red", 0.82, 0.21, 0.15)
    m.add_sloped_hood(-36, 36, -125, 0, 50, 110, 60, 130)

    # Front Grille & Lights
    m.set_material("mat_grille_white", 0.90, 0.92, 0.95)
    m.add_box(-30, 30, -127, -125, 62, 102)
    m.set_material("mat_amber_light", 0.96, 0.80, 0.25)
    m.add_box(-28, -16, -128, -126, 88, 98)
    m.add_box(16, 28, -128, -126, 88, 98)

    # Chrome Vertical Exhaust
    m.set_material("mat_chrome_pipe", 0.85, 0.88, 0.92)
    m.add_cylinder(-39, -40, 105, 205, 3.8, segments=8, axis='z')

    # Operator Station & Seat
    m.set_material("mat_seat_black", 0.14, 0.15, 0.16)
    m.add_box(-18, 18, 25, 65, 75, 125) # seat
    m.add_cylinder(0, 12, 95, 115, 10, segments=8, axis='z') # steering wheel

    # 4-Post Steel ROPS Canopy Frame
    m.set_material("mat_chassis_dark", 0.20, 0.21, 0.24)
    m.add_cylinder(-44, 8, 75, 210, 2.5, segments=6, axis='z') # front left post
    m.add_cylinder(44, 8, 75, 210, 2.5, segments=6, axis='z')  # front right post
    m.add_cylinder(-44, 75, 75, 210, 2.5, segments=6, axis='z') # rear left post
    m.add_cylinder(44, 75, 75, 210, 2.5, segments=6, axis='z')  # rear right post

    # Red Canopy Roof
    m.set_material("mat_tractor_red", 0.82, 0.21, 0.15)
    m.add_box(-48, 48, -2, 85, 210, 224)

    # Red Rear Fenders
    m.add_box(-74, -42, 15, 105, 115, 130)
    m.add_box(42, 74, 15, 105, 115, 130)

    # Wheels: Rear (Radius 56cm, Width 30cm)
    m.add_wheel(x_center=-60, y_center=62, z_center=56, radius=56, width=28, is_left=True)
    m.add_wheel(x_center=60,  y_center=62, z_center=56, radius=56, width=28, is_left=False)

    # Front Wheels (Radius 36cm, Width 22cm)
    m.add_wheel(x_center=-52, y_center=-95, z_center=36, radius=36, width=22, is_left=True)
    m.add_wheel(x_center=52,  y_center=-95, z_center=36, radius=36, width=22, is_left=False)

    return m

def build_combine_large():
    """
    Matches machine_combine_large.png:
    - GREEN main body (#3a8a3a) with yellow horizontal side decal (#f2c838)
    - Yellow open grain hopper on top filled with golden grain (#e8b838)
    - Forward-slanted cab overhang with glass windshield (#4a6274)
    - Front grain platform header with rotating black/gray reel bars
    - Side unloading auger pipe arm
    - 4 large wheels with yellow rims (#f2c838)
    """
    m = MeshBuilder("SM_Machine_Combine_Large")
    # Overall: W: 360cm (header), Body W: 220cm, L: 650cm, H: 380cm
    # Main Body Housing (Green)
    m.set_material("mat_jd_green", 0.22, 0.54, 0.22)
    m.add_box(-100, 100, -120, 280, 85, 275)

    # Yellow Horizontal Decal Stripe along side
    m.set_material("mat_jd_yellow", 0.95, 0.78, 0.18)
    m.add_box(-102, 102, -120, 280, 195, 207)

    # Top Grain Hopper Bin (Flared open yellow hopper filled with golden grain)
    m.add_sloped_hood(-95, 95, -60, 180, 275, 335, 275, 335)
    # Grain pile inside hopper
    m.set_material("mat_grain_gold", 0.92, 0.75, 0.25)
    m.add_box(-85, 85, -50, 170, 315, 332)

    # Forward-Slanted Cab Overhang (Front Y: -180 to -115, Z: 140 to 285)
    m.set_material("mat_jd_green", 0.22, 0.54, 0.22)
    m.add_box(-80, 80, -170, -115, 130, 150) # cab base
    m.add_box(-85, 85, -195, -110, 275, 295) # cab roof overhang
    # Cab Glass Windshield (slanted forward)
    m.set_material("mat_cab_glass", 0.30, 0.42, 0.52)
    m.add_sloped_hood(-78, 78, -188, -115, 150, 275, 150, 275)

    # Front Grain Reel Header Platform (W: 340cm, Y: -280 to -175)
    # Green header feeder housing
    m.set_material("mat_jd_green", 0.22, 0.54, 0.22)
    m.add_box(-170, 170, -280, -180, 25, 85)
    # Left and right side crop dividers (pointed tips)
    m.add_box(-175, -165, -310, -180, 25, 115)
    m.add_box(165, 175, -280, -180, 25, 115)
    # Rotating reel center pipe & slats (dark steel)
    m.set_material("mat_chassis_dark", 0.18, 0.20, 0.22)
    m.add_cylinder(-160, 160, -240, 85, 7.0, segments=8, axis='x')
    for angle_deg in [0, 60, 120, 180, 240, 300]:
        rad = math.radians(angle_deg)
        ry = -240 + 32 * math.cos(rad)
        rz = 85 + 32 * math.sin(rad)
        m.add_cylinder(-158, 158, ry, rz, 2.5, segments=6, axis='x')

    # Side Unloading Auger Tube (Right side, angled upward/backward)
    m.set_material("mat_jd_green", 0.22, 0.54, 0.22)
    m.add_cylinder(110, -40, 180, 310, 12.0, segments=8, axis='z') # pivot
    m.add_box(105, 125, -40, 360, 305, 325) # long auger arm

    # Wheels: Large Front Drive Wheels (Radius 82cm, Width 48cm, Yellow Rim)
    m.set_material("mat_jd_yellow", 0.95, 0.78, 0.18)
    m.add_wheel(x_center=-108, y_center=-50, z_center=82, radius=82, width=48, is_left=True)
    m.add_wheel(x_center=108,  y_center=-50, z_center=82, radius=82, width=48, is_left=False)

    # Rear Steer Wheels (Radius 55cm, Width 34cm)
    m.add_wheel(x_center=-90, y_center=210, z_center=55, radius=55, width=34, is_left=True)
    m.add_wheel(x_center=90,  y_center=210, z_center=55, radius=55, width=34, is_left=False)

    return m

def build_combine_small():
    """
    Matches machine_combine_small.png:
    - Compact green grain combine harvester
    """
    m = MeshBuilder("SM_Machine_Combine_Small")
    # Overall: W: 260cm (header), Body W: 160cm, L: 480cm, H: 295cm
    m.set_material("mat_jd_green", 0.22, 0.54, 0.22)
    m.add_box(-75, 75, -90, 200, 65, 215)
    m.set_material("mat_jd_yellow", 0.95, 0.78, 0.18)
    m.add_box(-77, 77, -90, 200, 150, 160)

    # Top Grain Hopper
    m.add_sloped_hood(-70, 70, -40, 130, 215, 265, 215, 265)
    m.set_material("mat_grain_gold", 0.92, 0.75, 0.25)
    m.add_box(-62, 62, -32, 122, 250, 263)

    # Cab
    m.set_material("mat_jd_green", 0.22, 0.54, 0.22)
    m.add_box(-65, 65, -145, -85, 105, 120)
    m.add_box(-68, 68, -165, -80, 215, 235)
    m.set_material("mat_cab_glass", 0.30, 0.42, 0.52)
    m.add_sloped_hood(-62, 62, -160, -85, 120, 215, 120, 215)

    # Front Header (W: 240cm)
    m.set_material("mat_jd_green", 0.22, 0.54, 0.22)
    m.add_box(-120, 120, -210, -140, 20, 68)
    m.set_material("mat_chassis_dark", 0.18, 0.20, 0.22)
    m.add_cylinder(-110, 110, -180, 68, 5.0, segments=8, axis='x')

    # Auger Arm
    m.set_material("mat_jd_green", 0.22, 0.54, 0.22)
    m.add_box(78, 92, -30, 260, 240, 256)

    # Wheels
    m.set_material("mat_jd_yellow", 0.95, 0.78, 0.18)
    m.add_wheel(x_center=-82, y_center=-35, z_center=65, radius=65, width=38, is_left=True)
    m.add_wheel(x_center=82,  y_center=-35, z_center=65, radius=65, width=38, is_left=False)
    m.add_wheel(x_center=-68, y_center=150, z_center=44, radius=44, width=26, is_left=True)
    m.add_wheel(x_center=68,  y_center=150, z_center=44, radius=44, width=26, is_left=False)

    return m

def build_excavator_large():
    """
    Matches machine_excavator_large.png:
    - CAT yellow main rotating house (#e5a924) with black side accent band & dark roof
    - Left-side operator cab with glass windows and white/silver frame
    - Dual heavy black track undercarriage (#202226) with sprockets
    - Two-piece yellow articulated boom and stick with hydraulic cylinders
    - Heavy dark steel toothed digging bucket
    """
    m = MeshBuilder("SM_Machine_Excavator_Large")
    # Overall: W: 270cm, L: 620cm, H: 320cm
    # Track Undercarriage: Left & Right Tracks (L: 420cm, W: 60cm, H: 85cm)
    m.add_track(x_center=-105, y_min=-190, y_max=190, z_min=0, z_max=82, width=58)
    m.add_track(x_center=105,  y_min=-190, y_max=190, z_min=0, z_max=82, width=58)
    # Center Carbody frame
    m.set_material("mat_chassis_dark", 0.15, 0.16, 0.18)
    m.add_box(-80, 80, -110, 110, 30, 75)

    # Rotating House (CAT Yellow with black side band)
    m.set_material("mat_cat_yellow", 0.90, 0.66, 0.14)
    m.add_box(-115, 115, -120, 185, 82, 195)
    # Dark engine hood/counterweight at rear
    m.set_material("mat_chassis_dark", 0.22, 0.23, 0.26)
    m.add_box(-112, 112, 80, 185, 190, 205)
    # Black accent band along right side
    m.add_box(113, 117, -115, 180, 115, 155)

    # Left-Side Operator Cab (X: -115 to -35, Y: -120 to 45, Z: 82 to 240)
    # Cab base/seat
    m.set_material("mat_chassis_dark", 0.15, 0.16, 0.18)
    m.add_box(-110, -40, -115, 40, 82, 110)
    # White cab pillars/frame
    m.set_material("mat_cab_pillar_white", 0.92, 0.93, 0.96)
    m.add_box(-112, -104, -118, -110, 110, 235)
    m.add_box(-46, -38, -118, -110, 110, 235)
    m.add_box(-112, -104, 32, 40, 110, 235)
    m.add_box(-46, -38, 32, 40, 110, 235)
    m.add_box(-115, -35, -120, 45, 235, 246) # cab roof
    # Glass windows
    m.set_material("mat_cab_glass", 0.30, 0.42, 0.52)
    m.add_box(-108, -42, -115, 38, 110, 235)

    # Excavator Arm: Boom (Yellow, arched forward)
    m.set_material("mat_cat_yellow", 0.90, 0.66, 0.14)
    # Boom pivot foot on center-right (X: 0 to 45)
    m.add_box(5, 45, -110, -70, 120, 175)
    # Main arched boom segment extending up and forward
    m.add_sloped_hood(8, 42, -260, -85, 160, 205, 245, 305)
    # Stick (Arm) extending down from boom tip
    m.add_sloped_hood(12, 38, -370, -250, 45, 95, 235, 275)

    # Hydraulic Cylinder Rams (Silver)
    m.set_material("mat_chrome_pipe", 0.82, 0.85, 0.88)
    m.add_cylinder(25, -160, 155, 245, 5.5, segments=8, axis='z')

    # Toothed Digging Bucket (Dark Steel)
    m.set_material("mat_chassis_dark", 0.18, 0.20, 0.22)
    m.add_box(2, 48, -430, -350, 0, 75)
    # Bucket teeth (5 pointed wedge teeth)
    for tx in [4, 13, 22, 31, 40]:
        m.add_box(tx, tx + 6, -445, -428, 2, 14)

    return m

def build_excavator_small():
    """
    Matches machine_excavator_small.png:
    - Yellow mini excavator, white enclosed cab, black rubber tracks, dozer push blade, digging bucket
    """
    m = MeshBuilder("SM_Machine_Excavator_Small")
    # Overall: W: 145cm, L: 340cm, H: 220cm
    m.add_track(x_center=-52, y_min=-110, y_max=110, z_min=0, z_max=52, width=32)
    m.add_track(x_center=52,  y_min=-110, y_max=110, z_min=0, z_max=52, width=32)
    # Front Dozer Push Blade
    m.set_material("mat_grille_white", 0.88, 0.90, 0.93)
    m.add_box(-68, 68, -138, -122, 2, 36)

    # Yellow House Body
    m.set_material("mat_cat_yellow", 0.90, 0.66, 0.14)
    m.add_box(-58, 58, -75, 105, 52, 125)

    # White Operator Cab with Glass
    m.set_material("mat_cab_pillar_white", 0.92, 0.93, 0.96)
    m.add_box(-56, 12, -70, 35, 120, 215)
    m.set_material("mat_cab_glass", 0.30, 0.42, 0.52)
    m.add_box(-54, 10, -68, 32, 125, 205)

    # Yellow Swing Boom & Stick
    m.set_material("mat_cat_yellow", 0.90, 0.66, 0.14)
    m.add_sloped_hood(18, 42, -175, -60, 95, 135, 155, 205)
    m.add_sloped_hood(20, 40, -245, -165, 18, 55, 145, 185)
    # Bucket
    m.set_material("mat_chassis_dark", 0.18, 0.20, 0.22)
    m.add_box(16, 44, -285, -235, 0, 48)

    return m

def build_skidsteer_large():
    """
    Matches machine_skidsteer_large.png:
    - Vivid ORANGE chassis (#e87324)
    - Four wide black offroad tires with orange hub centers (#e87324)
    - Black/gray ROPS cab with wire mesh side grilles & dark brown roof panel
    - Side lift arms supporting front dirt bucket on the ground
    """
    m = MeshBuilder("SM_Machine_Skidsteer_Large")
    # Overall: W: 185cm, L: 295cm, H: 205cm
    # Main Orange Chassis Body
    m.set_material("mat_bobcat_orange", 0.91, 0.45, 0.14)
    m.add_box(-68, 68, -75, 120, 35, 140)
    # Rear Engine Uprights (Orange side towers)
    m.add_box(-72, -45, 45, 125, 100, 185)
    m.add_box(45, 72, 45, 125, 100, 185)

    # ROPS Operator Cab (Centered, angled front glass/mesh)
    m.set_material("mat_chassis_dark", 0.18, 0.20, 0.22)
    m.add_box(-44, 44, -55, 65, 75, 195)
    # Cab Roof Panel (Brownish dark gray)
    m.set_material("mat_cab_roof_brown", 0.42, 0.32, 0.26)
    m.add_box(-46, 46, -58, 68, 195, 205)
    # Wire mesh side window texture
    m.set_material("mat_mesh_screen", 0.65, 0.68, 0.72)
    m.add_box(-45, -43, -40, 50, 115, 185)
    m.add_box(43, 45, -40, 50, 115, 185)

    # Lift Arms & Hydraulic Cylinders (Orange side arms extending forward)
    m.set_material("mat_bobcat_orange", 0.91, 0.45, 0.14)
    m.add_sloped_hood(-66, -52, -125, 85, 30, 65, 155, 185)
    m.add_sloped_hood(52, 66, -125, 85, 30, 65, 155, 185)
    # Hydraulic cylinder rams (Silver)
    m.set_material("mat_chrome_pipe", 0.85, 0.88, 0.92)
    m.add_cylinder(-59, -15, 85, 145, 4.0, segments=6, axis='z')
    m.add_cylinder(59, -15, 85, 145, 4.0, segments=6, axis='z')

    # Front Material Bucket (Dark brown/gray steel, scooped forward)
    m.set_material("mat_bucket_dark", 0.35, 0.28, 0.24)
    m.add_sloped_hood(-85, 85, -170, -115, 0, 55, 0, 75)
    # Cutting edge blade at front
    m.set_material("mat_grille_white", 0.85, 0.88, 0.92)
    m.add_box(-86, 86, -175, -168, 0, 8)

    # 4 Wide Tires with Orange Hub Centers (Radius 45cm, Width 28cm)
    m.set_material("mat_bobcat_orange", 0.91, 0.45, 0.14)
    m.add_wheel(x_center=-76, y_center=-45, z_center=45, radius=45, width=28, is_left=True)
    m.add_wheel(x_center=76,  y_center=-45, z_center=45, radius=45, width=28, is_left=False)
    m.add_wheel(x_center=-76, y_center=65,  z_center=45, radius=45, width=28, is_left=True)
    m.add_wheel(x_center=76,  y_center=65,  z_center=45, radius=45, width=28, is_left=False)

    return m

def build_skidsteer_small():
    """Matches machine_skidsteer_small.png: Compact orange wheeled skid steer"""
    m = MeshBuilder("SM_Machine_Skidsteer_Small")
    # Overall: W: 155cm, L: 235cm, H: 185cm
    m.set_material("mat_bobcat_orange", 0.91, 0.45, 0.14)
    m.add_box(-54, 54, -55, 95, 30, 115)
    m.add_box(-58, -38, 35, 100, 80, 155)
    m.add_box(38, 58, 35, 100, 80, 155)

    # Cab & Roof
    m.set_material("mat_chassis_dark", 0.18, 0.20, 0.22)
    m.add_box(-36, 36, -42, 50, 65, 165)
    m.set_material("mat_cab_roof_brown", 0.42, 0.32, 0.26)
    m.add_box(-38, 38, -45, 54, 165, 175)

    # Arms & Bucket
    m.set_material("mat_bobcat_orange", 0.91, 0.45, 0.14)
    m.add_sloped_hood(-52, -42, -95, 65, 24, 52, 125, 155)
    m.add_sloped_hood(42, 52, -95, 65, 24, 52, 125, 155)
    m.set_material("mat_bucket_dark", 0.35, 0.28, 0.24)
    m.add_sloped_hood(-68, 68, -135, -90, 0, 45, 0, 60)

    # Wheels
    m.set_material("mat_bobcat_orange", 0.91, 0.45, 0.14)
    m.add_wheel(x_center=-60, y_center=-35, z_center=38, radius=38, width=24, is_left=True)
    m.add_wheel(x_center=60,  y_center=-35, z_center=38, radius=38, width=24, is_left=False)
    m.add_wheel(x_center=-60, y_center=50,  z_center=38, radius=38, width=24, is_left=True)
    m.add_wheel(x_center=60,  y_center=50,  z_center=38, radius=38, width=24, is_left=False)

    return m

def build_sawmill_portable():
    """
    Matches machine_sawmill_portable.png:
    - Orange trailer chassis (#d85a28) with A-frame hitch tongue and jack wheel
    - Dual white trailer wheels (#e8eaed) with black tires and orange fenders
    - Horizontal steel track bed rails with log support bunks
    - Natural bark timber log resting on bed
    - Orange band saw carriage head (#d85a28) with engine, handles, horizontal blade guard
    """
    m = MeshBuilder("SM_Machine_Sawmill_Portable")
    # Overall: W: 160cm, L: 620cm, H: 165cm
    # Trailer A-frame Hitch Tongue at front (-Y: -310 to -230)
    m.set_material("mat_sawmill_orange", 0.85, 0.35, 0.16)
    m.add_box(-12, 12, -310, -290, 38, 48) # coupler
    m.add_box(-45, -12, -290, -230, 38, 48) # left tongue rail
    m.add_box(12, 45, -290, -230, 38, 48)  # right tongue rail
    # Front tongue jack wheel
    m.set_material("mat_chassis_dark", 0.20, 0.22, 0.25)
    m.add_cylinder(0, -295, 0, 42, 3.5, segments=6, axis='z')
    m.add_cylinder(-4, 4, -295, 8, 8.0, segments=8, axis='x')

    # Main Bed Rails (Two long structural C-channels)
    m.set_material("mat_sawmill_orange", 0.85, 0.35, 0.16)
    m.add_box(-48, -40, -230, 270, 42, 58) # left rail
    m.add_box(40, 48, -230, 270, 42, 58)   # right rail
    # Bed Cross Bunks (every 60cm)
    for yb in [-210, -140, -70, 0, 70, 140, 210, 260]:
        m.add_box(-44, 44, yb - 4, yb + 4, 45, 62)

    # Natural Timber Log on Bed (Y: -180 to 120, Radius 26cm, Center Z: 88cm)
    m.set_material("mat_log_bark", 0.43, 0.29, 0.19)
    m.add_cylinder(0, -180, 120, 88, 26, segments=12, axis='y')
    # Cut end face of log
    m.set_material("mat_log_cut", 0.78, 0.60, 0.41)
    m.add_cylinder(0, -181, -180, 88, 25, segments=12, axis='y')

    # Band Saw Carriage Head (at Y: 120 to 165, Orange)
    m.set_material("mat_sawmill_orange", 0.85, 0.35, 0.16)
    # Carriage upright posts
    m.add_box(-52, -44, 120, 140, 58, 165)
    m.add_box(44, 52, 120, 140, 58, 165)
    m.add_box(-52, 52, 120, 135, 155, 165) # top crossbar
    # Horizontal Bandsaw Blade Housing & Guide (Orange arched cover)
    m.add_box(-65, 65, 130, 150, 75, 125)
    # Gas Engine on Top of Carriage
    m.set_material("mat_chassis_dark", 0.22, 0.24, 0.28)
    m.add_box(-18, 18, 115, 145, 125, 155)

    # Tandem Axle Wheels & Orange Fenders (at Y: 80 to 220)
    m.set_material("mat_sawmill_orange", 0.85, 0.35, 0.16)
    m.add_box(-62, -48, 80, 220, 48, 62) # left fender
    m.add_box(48, 62, 80, 220, 48, 62)  # right fender

    # Dual White Trailer Wheels on each side (Radius 28cm)
    m.set_material("mat_grille_white", 0.90, 0.92, 0.95)
    for yw in [110, 180]:
        m.add_wheel(x_center=-58, y_center=yw, z_center=28, radius=28, width=16, is_left=True)
        m.add_wheel(x_center=58,  y_center=yw, z_center=28, radius=28, width=16, is_left=False)

    return m

def build_sawmill_stationary():
    """Matches machine_sawmill_stationary.png: White/silver rail bed, green bunks, green saw carriage"""
    m = MeshBuilder("SM_Machine_Sawmill_Stationary")
    # Overall: W: 180cm, L: 650cm, H: 220cm
    # White/Silver Structural Steel Bed Rails on Leveling Feet
    m.set_material("mat_grille_white", 0.86, 0.88, 0.92)
    m.add_box(-55, -45, -300, 300, 35, 52) # left rail
    m.add_box(45, 55, -300, 300, 35, 52)   # right rail
    # Leveling support legs with base pads
    for yl in [-280, -140, 0, 140, 280]:
        m.add_box(-53, -47, yl - 5, yl + 5, 0, 35)
        m.add_box(47, 53, yl - 5, yl + 5, 0, 35)
        m.add_box(-58, -42, yl - 10, yl + 10, 0, 4)
        m.add_box(42, 58, yl - 10, yl + 10, 0, 4)

    # Green Cross Bunks
    m.set_material("mat_jd_green", 0.28, 0.52, 0.32)
    for yb in [-260, -180, -100, -20, 60, 140, 220]:
        m.add_box(-48, 48, yb - 6, yb + 6, 38, 56)

    # Green Bandsaw Carriage Head (at Y: 140 to 190)
    m.set_material("mat_jd_green", 0.28, 0.52, 0.32)
    m.add_box(-60, -50, 150, 170, 52, 210)
    m.add_box(50, 60, 150, 170, 52, 210)
    m.add_box(-60, 60, 150, 165, 195, 215) # top crossbeam
    m.add_box(-72, 72, 155, 175, 110, 165) # horizontal blade guard
    # Motor
    m.set_material("mat_chassis_dark", 0.22, 0.24, 0.28)
    m.add_box(-22, 22, 145, 175, 165, 195)

    return m

def build_camper_rv():
    """
    Matches struct_camper_rv.png:
    - White travel trailer body (#e8eaed)
    - Blue horizontal accent stripe (#3d6898)
    - Blue deployed roll-out patio awning (#6286b2)
    - Front A-frame tongue hitch with white propane tank cover and front jack
    - Single axle with white/silver wheel
    - Front tinted window, entry door, side windows, roof A/C
    """
    m = MeshBuilder("SM_Struct_Camper_RV")
    # Overall: W: 240cm (with awning: 310cm), L: 580cm, H: 265cm
    # Front A-Frame Hitch (-Y: -280 to -190)
    m.set_material("mat_chassis_dark", 0.20, 0.22, 0.25)
    m.add_box(-8, 8, -280, -260, 42, 52) # hitch coupler
    m.add_box(-35, -8, -260, -190, 42, 52)
    m.add_box(8, 35, -260, -190, 42, 52)
    # Front tongue jack
    m.add_cylinder(0, -265, 0, 46, 3.5, segments=6, axis='z')
    # White Double Propane Tank Shroud / Cover
    m.set_material("mat_grille_white", 0.90, 0.92, 0.95)
    m.add_box(-24, 24, -240, -195, 48, 92)

    # Main Camper Body (White)
    m.set_material("mat_grille_white", 0.92, 0.93, 0.95)
    # Tapered front cap and rear box
    m.add_sloped_hood(-110, 110, -190, -135, 48, 175, 48, 245)
    m.add_box(-110, 110, -135, 230, 48, 245)

    # Blue Horizontal Side Accent Stripe (Height 105 to 125)
    m.set_material("mat_camper_blue", 0.24, 0.41, 0.60)
    m.add_box(-112, 112, -190, 230, 105, 125)

    # Front Angled Window (Dark Tint)
    m.set_material("mat_cab_glass", 0.28, 0.32, 0.38)
    m.add_box(-75, 75, -172, -170, 125, 175)

    # Curbside Entry Door (Right side, Y: -80 to -20)
    m.set_material("mat_grille_white", 0.86, 0.88, 0.90)
    m.add_box(110, 113, -80, -20, 52, 205)
    # Door window & handle
    m.set_material("mat_cab_glass", 0.28, 0.32, 0.38)
    m.add_box(111, 114, -65, -35, 135, 185)

    # Curbside Rear Window (Y: 50 to 160)
    m.add_box(111, 114, 50, 160, 140, 185)

    # Deployed Blue Roll-Out Patio Awning (extending out on right side)
    m.set_material("mat_camper_blue", 0.38, 0.52, 0.70)
    # Sloped canvas awning sheet from roofline down
    m.add_sloped_hood(110, 210, -95, 185, 195, 200, 235, 240)
    # Awning support arms (Silver metal)
    m.set_material("mat_chrome_pipe", 0.82, 0.85, 0.88)
    m.add_cylinder(110, 208, -90, 200, 2.5, segments=6, axis='x')
    m.add_cylinder(110, 208, 180, 200, 2.5, segments=6, axis='x')

    # Roof A/C Shroud
    m.set_material("mat_grille_white", 0.92, 0.93, 0.95)
    m.add_box(-42, 42, 10, 95, 245, 265)

    # Wheels & Wheel Well (at Y: 70, Radius 36cm)
    m.set_material("mat_chrome_pipe", 0.85, 0.88, 0.92)
    m.add_wheel(x_center=-108, y_center=70, z_center=36, radius=36, width=22, is_left=True)
    m.add_wheel(x_center=108,  y_center=70, z_center=36, radius=36, width=22, is_left=False)

    return m

def build_camper_teardrop():
    """
    Matches struct_camper_teardrop.png:
    - Two-tone cream/ivory top cap (#ede9e1) and cool gray lower body (#78808a) with white trim
    - Front A-frame hitch tongue with curved front storage tub
    - Front rectangular tinted window
    - Side arched entry door with circular porthole window
    - Rear circular porthole window
    - Chrome curved fender with baby moon wheel hub
    """
    m = MeshBuilder("SM_Machine_Camper_Teardrop")
    # Overall: W: 185cm, L: 340cm, H: 175cm
    # Front Hitch Tongue (-Y: -170 to -110)
    m.set_material("mat_chassis_dark", 0.20, 0.22, 0.25)
    m.add_box(-8, 8, -170, -150, 32, 42)
    m.add_box(-28, -8, -150, -110, 32, 42)
    m.add_box(8, 28, -150, -110, 32, 42)
    m.add_cylinder(0, -155, 0, 36, 2.5, segments=6, axis='z') # jack
    # Front curved storage box (gray)
    m.set_material("mat_camper_gray", 0.52, 0.55, 0.58)
    m.add_cylinder(0, -110, 38, 82, 28, segments=12, axis='z')

    # Lower Body: Cool Gray
    m.set_material("mat_camper_gray", 0.48, 0.51, 0.55)
    m.add_box(-68, 68, -110, 140, 36, 95)

    # Upper Body: Cream / Off-White Aerodynamic Curved Shell
    m.set_material("mat_camper_cream", 0.93, 0.91, 0.88)
    # Front rounded curve
    m.add_sloped_hood(-68, 68, -110, -40, 95, 148, 95, 172)
    # Top & rear slope
    m.add_sloped_hood(-68, 68, -40, 140, 95, 172, 95, 115)

    # Front Tinted Rectangular Window
    m.set_material("mat_cab_glass", 0.28, 0.32, 0.38)
    m.add_box(-48, 48, -100, -96, 105, 142)

    # Curbside Arched Door with Circular Porthole Window
    m.set_material("mat_grille_white", 0.95, 0.95, 0.96)
    m.add_box(68, 70, -35, 35, 42, 148)
    # Circular Porthole window in door
    m.set_material("mat_cab_glass", 0.28, 0.32, 0.38)
    m.add_cylinder(69, 71, 0, 115, 12, segments=10, axis='x')

    # Rear Circular Porthole Window
    m.add_cylinder(69, 71, 85, 125, 14, segments=10, axis='x')

    # Chrome Curved Fender & Wheels (at Y: 35, Radius 30cm)
    m.set_material("mat_chrome_pipe", 0.88, 0.90, 0.94)
    m.add_box(-88, -68, 5, 65, 52, 68) # left fender
    m.add_box(68, 88, 5, 65, 52, 68)   # right fender
    m.add_wheel(x_center=-78, y_center=35, z_center=30, radius=30, width=18, is_left=True)
    m.add_wheel(x_center=78,  y_center=35, z_center=30, radius=30, width=18, is_left=False)

    return m

def build_silo():
    """
    Matches struct_silo.png:
    - Octagonal corrugated galvanized cylinder (#a8b0b8)
    - Conical roof with top vent cap
    - Conical hopper discharge bottom
    - 6 heavy structural steel legs (#687078)
    - Round/octagonal concrete footing base pad (#909498)
    """
    m = MeshBuilder("SM_Struct_Silo")
    # Overall: W: 350cm, L: 350cm, H: 880cm
    # Octagonal Concrete Foundation Pad
    m.set_material("mat_concrete_pad", 0.60, 0.62, 0.65)
    m.add_cylinder(0, 0, 0, 18, 175, segments=8, axis='z')

    # 6 Heavy Structural Steel Legs
    m.set_material("mat_steel_legs", 0.42, 0.45, 0.48)
    leg_r = 145
    for i in range(6):
        ang = 2.0 * math.pi * i / 6.0
        lx = leg_r * math.cos(ang)
        ly = leg_r * math.sin(ang)
        m.add_box(lx - 7, lx + 7, ly - 7, ly + 7, 18, 235)
    # Cross-tie bracing between legs
    for i in range(6):
        ang1 = 2.0 * math.pi * i / 6.0
        ang2 = 2.0 * math.pi * ((i + 1) % 6) / 6.0
        x1, y1 = leg_r * math.cos(ang1), leg_r * math.sin(ang1)
        x2, y2 = leg_r * math.cos(ang2), leg_r * math.sin(ang2)
        m.add_box(min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2), 120, 128)

    # Conical Hopper Bottom (Tapering from R: 155 at Z: 235 down to R: 35 at Z: 95)
    m.set_material("mat_galv_dark", 0.65, 0.68, 0.72)
    # Build tapered cone rings
    for iz, (z_b, z_t, r_b, r_t) in enumerate([(95, 140, 35, 75), (140, 190, 75, 115), (190, 235, 115, 155)]):
        m.add_cylinder(0, 0, z_b, z_t, (r_b + r_t)/2.0, segments=8, axis='z')

    # Main Corrugated Galvanized Silo Barrel Cylinder (Z: 235 to 680, Radius 155cm)
    m.set_material("mat_galv_steel", 0.72, 0.75, 0.78)
    m.add_cylinder(0, 0, 235, 680, 155, segments=8, axis='z')
    # Horizontal tier seam rings
    m.set_material("mat_galv_dark", 0.58, 0.62, 0.66)
    for zr in [345, 455, 565, 675]:
        m.add_cylinder(0, 0, zr - 3, zr + 3, 158, segments=8, axis='z')

    # Conical Galvanized Roof (Z: 680 to 850, Tapering from R: 160 to 0)
    m.set_material("mat_galv_steel", 0.75, 0.78, 0.82)
    for z_b, z_t, r_avg in [(680, 740, 135), (740, 800, 85), (800, 850, 35)]:
        m.add_cylinder(0, 0, z_b, z_t, r_avg, segments=8, axis='z')
    # Top Peak Vent Cap
    m.set_material("mat_galv_dark", 0.55, 0.58, 0.62)
    m.add_cylinder(0, 0, 850, 880, 38, segments=8, axis='z')

    return m

def build_stable():
    """
    Matches struct_stable.png:
    - Long timber horse barn stable with asymmetrical saltbox wood shake roof (#846858)
    - Open central breezeway arch on left end
    - Three horse stall bays along front/side:
      - Dark wood Dutch half-doors (#584236) with 'X' cross-bracing
      - Vertical white/silver metal stall bars (#d8dce0) above doors
      - Light cedar wall framing posts (#a07850)
    """
    m = MeshBuilder("SM_Struct_Stable")
    # Overall: W: 380cm, L: 620cm, H: 315cm
    # Cedar Timber Framing Posts & Base
    m.set_material("mat_cedar_posts", 0.63, 0.47, 0.31)
    m.add_box(-180, 180, -300, 300, 0, 18) # ground sill

    # Back wall & Right End Wall (Solid cedar timber planks)
    m.add_box(-175, 175, 285, 300, 18, 235) # back wall
    m.add_box(165, 180, -300, 300, 18, 235) # right wall

    # Left End Wall with Open Breezeway Arch (-X side, Y: -300 to -160)
    m.add_box(-180, -170, -300, -240, 18, 220) # front arch pillar
    m.add_box(-180, -170, -160, 300, 18, 220)  # rear arch pillar
    m.add_box(-180, -170, -300, -160, 185, 235) # breezeway header beam

    # Front Wall: 3 Horse Stall Bays (Y: -160 to 280, divided into 3 bays)
    bay_y = [(-150, -10), (0, 140), (150, 290)]
    for by_start, by_end in bay_y:
        mid_y = (by_start + by_end) / 2.0
        # Dividing post
        m.set_material("mat_cedar_posts", 0.63, 0.47, 0.31)
        m.add_box(-180, -170, by_start - 8, by_start + 8, 18, 225)
        m.add_box(-180, -170, by_end - 8, by_end + 8, 18, 225)
        # Header beam over stall
        m.add_box(-180, -170, by_start, by_end, 210, 225)

        # Lower Dutch Door (Dark Wood with 'X' cross bracing)
        m.set_material("mat_dutch_door", 0.35, 0.26, 0.21)
        m.add_box(-174, -168, by_start + 4, by_end - 4, 18, 115)
        # 'X' bracing relief
        m.set_material("mat_cedar_posts", 0.58, 0.43, 0.28)
        m.add_box(-175, -173, by_start + 8, by_end - 8, 22, 112)

        # Upper Open Stall Bay with Vertical Metal Stall Bars
        m.set_material("mat_grille_white", 0.88, 0.90, 0.93)
        num_bars = 6
        step_y = (by_end - by_start - 16) / float(num_bars - 1)
        for ib in range(num_bars):
            bar_y = by_start + 8 + ib * step_y
            m.add_cylinder(-171, bar_y, 115, 210, 1.8, segments=6, axis='z')

    # Interior stall partitions
    m.set_material("mat_cedar_posts", 0.55, 0.40, 0.26)
    m.add_box(-170, 165, -10, 5, 18, 165)
    m.add_box(-170, 165, 140, 155, 18, 165)

    # Saltbox Asymmetrical Wood Shake Roof (Brown/cedar shingle tone)
    m.set_material("mat_roof_shake", 0.52, 0.41, 0.35)
    # Peak at X: -20, Z: 315
    # Front slope: X: -195 to -20, Z: 220 to 315
    m.add_sloped_hood(-195, -15, -315, 315, 215, 230, 305, 320)
    # Back slope: X: -20 to 195, Z: 315 to 215
    m.add_sloped_hood(-15, 195, -315, 315, 305, 320, 215, 230)

    return m

# =========================================================================
# MAIN EXECUTION & PREVIEW ICON EXTRACTION
# =========================================================================

def main():
    print("=====================================================================")
    print("  REBUILDING BATCH 1: 14 MACHINERY, VEHICLES & STRUCTURES MODELS")
    print("  Faithfully matching original item icons in HUD/assets/items/")
    print("=====================================================================")

    generators = [
        # 1. Tractors & Combines (farming)
        ("SM_Machine_Tractor_Large", build_tractor_large, "farming", "machine_tractor_large.png"),
        ("SM_Machine_Tractor_Small", build_tractor_small, "farming", "machine_tractor_small.png"),
        ("SM_Machine_Combine_Large", build_combine_large, "farming", "machine_combine_large.png"),
        ("SM_Machine_Combine_Small", build_combine_small, "farming", "machine_combine_small.png"),

        # 2. Excavators & Skid Steers (tools)
        ("SM_Machine_Excavator_Large", build_excavator_large, "tools", "machine_excavator_large.png"),
        ("SM_Machine_Excavator_Small", build_excavator_small, "tools", "machine_excavator_small.png"),
        ("SM_Machine_Skidsteer_Large", build_skidsteer_large, "tools", "machine_skidsteer_large.png"),
        ("SM_Machine_Skidsteer_Small", build_skidsteer_small, "tools", "machine_skidsteer_small.png"),

        # 3. Sawmills (logging)
        ("SM_Machine_Sawmill_Portable", build_sawmill_portable, "logging", "machine_sawmill_portable.png"),
        ("SM_Machine_Sawmill_Stationary", build_sawmill_stationary, "logging", "machine_sawmill_stationary.png"),

        # 4. Campers & Structures (building)
        ("SM_Struct_Camper_RV", build_camper_rv, "building", "struct_camper_rv.png"),
        ("SM_Struct_Camper_Teardrop", build_camper_teardrop, "building", "struct_camper_teardrop.png"),
        ("SM_Struct_Silo", build_silo, "building", "struct_silo.png"),
        ("SM_Struct_Stable", build_stable, "building", "struct_stable.png"),
    ]

    for model_name, gen_func, cat, source_icon_file in generators:
        print(f"\n--> Generating {model_name}...")
        builder = gen_func()
        
        paths = DESTINATIONS[cat]
        hud_obj = os.path.join(paths["hud_models"], f"{model_name}.obj")
        hud_mtl = os.path.join(paths["hud_models"], f"{model_name}.mtl")
        ue5_obj = os.path.join(paths["ue5_models"], f"{model_name}.obj")
        ue5_mtl = os.path.join(paths["ue5_models"], f"{model_name}.mtl")

        # Write HUD OBJ/MTL
        builder.write_obj_and_mtl(hud_obj, hud_mtl)
        # Sync to UE5
        shutil.copy2(hud_obj, ue5_obj)
        shutil.copy2(hud_mtl, ue5_mtl)

        # Sync Preview Icon from source icon in assets/items/
        src_icon_path = os.path.join(HUD_ASSETS, "items", source_icon_file)
        hud_icon = os.path.join(paths["hud_icons"], f"{model_name}.png")
        ue5_icon = os.path.join(paths["ue5_icons"], f"{model_name}.png")

        if os.path.exists(src_icon_path):
            shutil.copy2(src_icon_path, hud_icon)
            shutil.copy2(src_icon_path, ue5_icon)
            print(f"    [ICON] Synced matching icon from {source_icon_file}")
        else:
            print(f"    [WARN] Source icon not found at {src_icon_path}")

        # Check vertex & face count
        num_faces = sum(len(f) for f in builder.materials.values())
        print(f"    [DONE] {model_name}: {len(builder.vertices)} verts, {num_faces} tris.")

    print("\nBatch 1 successfully rebuilt and synchronized across HUD and UE5!")

if __name__ == "__main__":
    main()
