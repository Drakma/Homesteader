#!/usr/bin/env python3
"""
Homesteader Hardware, Fuel Cans & Small Utilities 3D Asset Generator
===================================================================
Faithfully generates 22 small utilities, hardware, fuel, and plumbing world models (.obj + .mtl):
- 10 Fuel Cans, Heavy Tanks & Fastener Hardware (building)
- 7 Electrical Controls & Cable Spools (utilities)
- 5 Plumbing Canisters, Hoses & Pipe Bundles (utilities)

Features:
- Directly replicates the visual appearance, shapes, components, and colors
  of each canonical item icon in HUD/assets/items/.
- Watertight 360-degree geometry rotatable on the Homesteader spatial grid.
- Ground-aligned pivots (Z_min = 0.0).
- Dual workspace synchronization across HUD/assets/ and Homesteader/Content/Homesteader/.
"""

import os
import sys
import math
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

CAT_DIRS = {
    "building": {
        "hud_models": os.path.join(PROJECT_ROOT, "HUD", "assets", "building", "models"),
        "hud_icons":  os.path.join(PROJECT_ROOT, "HUD", "assets", "building", "icons"),
        "ue5_models": os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "Assets", "Building", "Meshes"),
        "ue5_icons":  os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "UI", "Icons", "building"),
    },
    "utilities": {
        "hud_models": os.path.join(PROJECT_ROOT, "HUD", "assets", "utilities", "models"),
        "hud_icons":  os.path.join(PROJECT_ROOT, "HUD", "assets", "utilities", "icons"),
        "ue5_models": os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "Assets", "Utilities", "Meshes"),
        "ue5_icons":  os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "UI", "Icons", "Utilities"),
    }
}

ITEMS_DIR = os.path.join(PROJECT_ROOT, "HUD", "assets", "items")

for cat, paths in CAT_DIRS.items():
    for p in paths.values():
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
        self.add_quad(v1, v4, v3, v2)  # Bottom
        self.add_quad(v5, v6, v7, v8)  # Top
        self.add_quad(v1, v2, v6, v5)  # Front
        self.add_quad(v3, v4, v8, v7)  # Back
        self.add_quad(v4, v1, v5, v8)  # Left
        self.add_quad(v2, v3, v7, v6)  # Right

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
        elif axis == 'y':
            y_min, y_max, cen_x, cen_z = cx, cy, z_min, z_max
            f_verts = []
            r_verts = []
            for i in range(segments):
                angle = 2.0 * math.pi * i / segments
                x = cen_x + radius * math.cos(angle)
                z = cen_z + radius * math.sin(angle)
                f_verts.append(self.add_vertex(x, y_min, z))
                r_verts.append(self.add_vertex(x, y_max, z))
            cf = self.add_vertex(cen_x, y_min, cen_z)
            cr = self.add_vertex(cen_x, y_max, cen_z)
            for i in range(segments):
                nxt = (i + 1) % segments
                self.add_tri(cf, f_verts[i], f_verts[nxt])
                self.add_tri(cr, r_verts[nxt], r_verts[i])
                self.add_quad(f_verts[nxt], f_verts[i], r_verts[i], r_verts[nxt])
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

    def add_tapered_cylinder(self, cx, cy, z_min, z_max, r_bot, r_top, segments=8):
        bot_verts = []
        top_verts = []
        for i in range(segments):
            angle = 2.0 * math.pi * i / segments
            bot_verts.append(self.add_vertex(cx + r_bot * math.cos(angle), cy + r_bot * math.sin(angle), z_min))
            top_verts.append(self.add_vertex(cx + r_top * math.cos(angle), cy + r_top * math.sin(angle), z_max))
        c_bot = self.add_vertex(cx, cy, z_min)
        c_top = self.add_vertex(cx, cy, z_max)
        for i in range(segments):
            nxt = (i + 1) % segments
            self.add_tri(c_bot, bot_verts[nxt], bot_verts[i])
            self.add_tri(c_top, top_verts[i], top_verts[nxt])
            self.add_quad(bot_verts[i], bot_verts[nxt], top_verts[nxt], top_verts[i])

    def add_sphere(self, cx, cy, cz, radius, segs_lat=5, segs_lon=8):
        for i in range(segs_lat):
            lat0 = math.pi * (-0.5 + float(i) / segs_lat)
            lat1 = math.pi * (-0.5 + float(i + 1) / segs_lat)
            z0 = cz + radius * math.sin(lat0)
            z1 = cz + radius * math.sin(lat1)
            r0 = radius * math.cos(lat0)
            r1 = radius * math.cos(lat1)

            for j in range(segs_lon):
                lon0 = 2 * math.pi * float(j) / segs_lon
                lon1 = 2 * math.pi * float(j + 1) / segs_lon

                v0 = self.add_vertex(cx + r0 * math.cos(lon0), cy + r0 * math.sin(lon0), z0)
                v1 = self.add_vertex(cx + r0 * math.cos(lon1), cy + r0 * math.sin(lon1), z0)
                v2 = self.add_vertex(cx + r1 * math.cos(lon1), cy + r1 * math.sin(lon1), z1)
                v3 = self.add_vertex(cx + r1 * math.cos(lon0), cy + r1 * math.sin(lon0), z1)

                if i == 0:
                    self.add_tri(v0, v1, v2)
                elif i == segs_lat - 1:
                    self.add_tri(v0, v2, v3)
                else:
                    self.add_quad(v0, v1, v2, v3)

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


# =============================================================================
# 1. FUEL & HEAVY TANKS (5 - BUILDING)
# =============================================================================

def build_fuel_gascan_5gal():
    """SM_Item_Fuel_GasCan_5gal: Red poly 5-gal gasoline jerry can with pour spout."""
    m = MeshBuilder("SM_Item_Fuel_GasCan_5gal")
    m.set_material("can_red", 0.82, 0.15, 0.14)        # Gasoline red #D32F2F
    m.set_material("spout_black", 0.16, 0.16, 0.18)    # Black pour spout
    m.set_material("vent_yellow", 0.95, 0.75, 0.15)    # Yellow vent cap

    # Jerry can body (18x30x34cm)
    m.set_material("can_red", 0.82, 0.15, 0.14)
    m.add_box(-9.0, 9.0, -15.0, 15.0, 0.0, 34.0)

    # Top center carry handle
    m.add_box(-2.0, 2.0, -11.0, 11.0, 34.0, 40.0)

    # Angled front pour spout
    m.set_material("spout_black", 0.16, 0.16, 0.18)
    m.add_cylinder(0.0, 12.0, 34.0, 40.0, 2.2, segments=8)

    # Rear yellow vent cap
    m.set_material("vent_yellow", 0.95, 0.75, 0.15)
    m.add_cylinder(0.0, -12.0, 34.0, 37.0, 1.4, segments=6)
    return m


def build_fuel_dieselcan_5gal():
    """SM_Item_Fuel_DieselCan_5gal: Yellow poly 5-gal diesel fuel can with spout."""
    m = MeshBuilder("SM_Item_Fuel_DieselCan_5gal")
    m.set_material("diesel_yellow", 0.96, 0.78, 0.12)  # Diesel yellow #FBC02D
    m.set_material("spout_black", 0.16, 0.16, 0.18)

    # Jerry can body (18x30x34cm)
    m.set_material("diesel_yellow", 0.96, 0.78, 0.12)
    m.add_box(-9.0, 9.0, -15.0, 15.0, 0.0, 34.0)

    # Top carry handle
    m.add_box(-2.0, 2.0, -11.0, 11.0, 34.0, 40.0)

    # Spout
    m.set_material("spout_black", 0.16, 0.16, 0.18)
    m.add_cylinder(0.0, 12.0, 34.0, 40.0, 2.2, segments=8)
    return m


def build_fuel_propanetank_20lb():
    """SM_Item_Fuel_PropaneTank_20lb: White 20lb BBQ LP propane cylinder with OPD valve."""
    m = MeshBuilder("SM_Item_Fuel_PropaneTank_20lb")
    m.set_material("tank_white", 0.95, 0.94, 0.92)     # White enamel
    m.set_material("valve_brass", 0.85, 0.70, 0.28)    # Brass OPD valve
    m.set_material("collar_gray", 0.80, 0.80, 0.82)

    # Bottom foot ring (diameter 22cm, height 4cm)
    m.set_material("collar_gray", 0.80, 0.80, 0.82)
    m.add_cylinder(0.0, 0.0, 0.0, 4.0, 11.0, segments=10)

    # Main cylindrical tank belly (diameter 29cm, height 28cm)
    m.set_material("tank_white", 0.95, 0.94, 0.92)
    m.add_cylinder(0.0, 0.0, 4.0, 32.0, 14.5, segments=12)

    # Top protective collar handle ring
    m.set_material("collar_gray", 0.80, 0.80, 0.82)
    m.add_cylinder(0.0, 0.0, 32.0, 43.0, 10.5, segments=10)

    # Brass triangular valve knob inside collar
    m.set_material("valve_brass", 0.85, 0.70, 0.28)
    m.add_cylinder(0.0, 0.0, 32.0, 39.0, 2.2, segments=6)
    return m


def build_tank_propane_1000gal():
    """SM_Item_Tank_Propane_1000gal: 1000-gallon horizontal white bullet tank on saddles."""
    m = MeshBuilder("SM_Item_Tank_Propane_1000gal")
    m.set_material("tank_white", 0.96, 0.95, 0.92)     # White steel bullet
    m.set_material("dome_red", 0.82, 0.18, 0.16)       # Red top bonnet dome
    m.set_material("saddle_steel", 0.24, 0.26, 0.28)   # Heavy steel saddles
    m.set_material("pier_concrete", 0.65, 0.65, 0.68)  # Concrete footings

    # 2 Concrete footings
    m.set_material("pier_concrete", 0.65, 0.65, 0.68)
    m.add_box(-48.0, 48.0, -160.0, -110.0, 0.0, 12.0)
    m.add_box(-48.0, 48.0, 110.0, 160.0, 0.0, 12.0)

    # 2 Steel support saddles
    m.set_material("saddle_steel", 0.24, 0.26, 0.28)
    m.add_box(-45.0, 45.0, -150.0, -120.0, 12.0, 38.0)
    m.add_box(-45.0, 45.0, 120.0, 150.0, 12.0, 38.0)

    # Main cylindrical bullet tank (diameter 100cm, length 420cm along Y)
    m.set_material("tank_white", 0.96, 0.95, 0.92)
    m.add_cylinder(-180.0, 180.0, 0.0, 88.0, 50.0, segments=12, axis='y')

    # Hemispherical end caps
    m.add_sphere(0.0, -180.0, 88.0, 50.0, segs_lat=4, segs_lon=8)
    m.add_sphere(0.0, 180.0, 88.0, 50.0, segs_lat=4, segs_lon=8)

    # Top dome bonnet cover
    m.set_material("dome_red", 0.82, 0.18, 0.16)
    m.add_cylinder(0.0, 0.0, 138.0, 142.0, 16.0, segments=8)
    return m


def build_tank_fuel_bulk_elevated():
    """SM_Item_Tank_FuelBulk_Elevated: 300-gal red farm bulk gravity tank on steel legs stand."""
    m = MeshBuilder("SM_Item_Tank_FuelBulk_Elevated")
    m.set_material("tank_red", 0.82, 0.16, 0.14)       # Red farm tank
    m.set_material("stand_steel", 0.22, 0.25, 0.28)    # Dark steel angle stand
    m.set_material("hose_black", 0.16, 0.16, 0.18)     # Black drain hose
    m.set_material("nozzle_metal", 0.75, 0.78, 0.82)   # Aluminum nozzle

    # 4-leg angle iron stand (width 90cm, length 140cm, height 120cm)
    m.set_material("stand_steel", 0.22, 0.25, 0.28)
    for lx in [-40.0, 40.0]:
        for ly in [-65.0, 65.0]:
            m.add_box(lx - 3.0, lx + 3.0, ly - 3.0, ly + 3.0, 0.0, 120.0)
    # Cross braces
    m.add_box(-43.0, 43.0, -68.0, 68.0, 50.0, 54.0)
    m.add_box(-43.0, 43.0, -68.0, 68.0, 116.0, 120.0)

    # Red horizontal cylindrical tank body (diameter 86cm, length 140cm along Y)
    m.set_material("tank_red", 0.82, 0.16, 0.14)
    m.add_cylinder(-65.0, 65.0, 0.0, 163.0, 43.0, segments=12, axis='y')

    # Top fill cap
    m.add_cylinder(0.0, 0.0, 206.0, 210.0, 6.0, segments=8)

    # Gravity drain hose hanging down
    m.set_material("hose_black", 0.16, 0.16, 0.18)
    m.add_cylinder(35.0, 60.0, 30.0, 120.0, 2.5, segments=6)

    # Dispensing nozzle
    m.set_material("nozzle_metal", 0.75, 0.78, 0.82)
    m.add_box(33.0, 42.0, 58.0, 64.0, 20.0, 32.0)
    return m


# =============================================================================
# 2. FASTENER & HARDWARE BOXES (5 - BUILDING)
# =============================================================================

def build_hardware_framing_nails():
    """SM_Item_Hardware_FramingNails_Box: 50lb box of 16d framing strip nails."""
    m = MeshBuilder("SM_Item_Hardware_FramingNails_Box")
    m.set_material("box_kraft", 0.65, 0.52, 0.38)      # Kraft cardboard #8D6E63
    m.set_material("label_yellow", 0.95, 0.82, 0.15)   # Yellow branding
    m.set_material("nails_silver", 0.75, 0.78, 0.82)   # Steel strip nails

    # Cardboard box (14.2x22x13cm)
    m.set_material("box_kraft", 0.65, 0.52, 0.38)
    m.add_box(-7.1, 7.1, -11.0, 11.0, 0.0, 13.0)

    # Front label stripe
    m.set_material("label_yellow", 0.95, 0.82, 0.15)
    m.add_box(-7.15, 7.15, 10.9, 11.05, 3.0, 10.0)

    # Collated nail strip accent on top
    m.set_material("nails_silver", 0.75, 0.78, 0.82)
    m.add_box(-4.0, 4.0, -8.0, 8.0, 12.8, 13.5)
    return m


def build_hardware_deck_screws():
    """SM_Item_Hardware_DeckScrews_Box: 5lb plastic tub of exterior Torx deck screws."""
    m = MeshBuilder("SM_Item_Hardware_DeckScrews_Box")
    m.set_material("tub_teal", 0.32, 0.68, 0.62)       # Translucent teal tub
    m.set_material("lid_green", 0.18, 0.52, 0.24)      # Green snap lid
    m.set_material("screws_bronze", 0.62, 0.48, 0.32)

    # Plastic tub (14x20x10cm)
    m.set_material("tub_teal", 0.32, 0.68, 0.62)
    m.add_box(-7.0, 7.0, -10.0, 10.0, 0.0, 9.5)

    # Green lid on top
    m.set_material("lid_green", 0.18, 0.52, 0.24)
    m.add_box(-7.2, 7.2, -10.2, 10.2, 9.5, 11.5)
    return m


def build_hardware_lag_bolts():
    """SM_Item_Hardware_LagBolts_Box: Box of galvanized hex head lag bolts."""
    m = MeshBuilder("SM_Item_Hardware_LagBolts_Box")
    m.set_material("box_blue", 0.18, 0.45, 0.78)       # Industrial blue box
    m.set_material("label_white", 0.95, 0.95, 0.96)
    m.set_material("bolt_silver", 0.78, 0.80, 0.84)    # Galvanized bolts

    # Heavy box (14x20x12cm)
    m.set_material("box_blue", 0.18, 0.45, 0.78)
    m.add_box(-7.0, 7.0, -10.0, 10.0, 0.0, 12.0)

    # White label
    m.set_material("label_white", 0.95, 0.95, 0.96)
    m.add_box(-6.0, 6.0, 9.9, 10.05, 3.0, 9.0)
    return m


def build_hardware_gate_hinges():
    """SM_Item_Hardware_GateHinges_Pair: Pair of heavy 12-inch black steel strap hinges."""
    m = MeshBuilder("SM_Item_Hardware_GateHinges_Pair")
    m.set_material("hinge_black", 0.16, 0.16, 0.18)    # Black powder-coat steel
    m.set_material("pin_steel", 0.45, 0.48, 0.52)      # Steel pivot pin

    # Pair stacked together (width 7cm, length 32cm, height 7cm)
    m.set_material("hinge_black", 0.16, 0.16, 0.18)
    # Tapered strap leaf
    m.add_box(-3.5, 3.5, -12.0, 16.0, 0.0, 1.8)
    m.add_box(-3.5, 3.5, -12.0, 16.0, 3.5, 5.3)

    # Hinge barrel knuckles
    m.set_material("pin_steel", 0.45, 0.48, 0.52)
    m.add_cylinder(-3.5, 3.5, -14.0, 2.5, 2.0, segments=8, axis='x')
    m.add_cylinder(-3.5, 3.5, -14.0, 6.0, 2.0, segments=8, axis='x')
    return m


def build_hardware_rebar_bundle():
    """SM_Item_Hardware_RebarBundle: Banded bundle of #4 concrete reinforcement rebar."""
    m = MeshBuilder("SM_Item_Hardware_RebarBundle")
    m.set_material("rebar_steel", 0.28, 0.32, 0.36)    # Dark ribbed rebar
    m.set_material("tie_silver", 0.78, 0.80, 0.84)     # Steel tie bands

    # Bundle of 7 rebar rods (diameter ~14cm, length 280cm along Y)
    m.set_material("rebar_steel", 0.28, 0.32, 0.36)
    rods = [
        (0.0, 7.0),
        (-3.8, 4.8), (3.8, 4.8),
        (-3.8, 9.2), (3.8, 9.2),
        (0.0, 2.6), (0.0, 11.4)
    ]
    for rx, rz in rods:
        m.add_cylinder(-140.0, 140.0, rx, rz, 1.6, segments=6, axis='y')

    # Steel tie wire bands
    m.set_material("tie_silver", 0.78, 0.80, 0.84)
    for by in [-100.0, 0.0, 100.0]:
        m.add_cylinder(by - 1.5, by + 1.5, 0.0, 7.0, 6.8, segments=8, axis='y')
    return m


# =============================================================================
# 3. ELECTRICAL & CABLE REELS (7 - UTILITIES)
# =============================================================================

def build_spool_romex_12_2():
    """SM_Item_Spool_Romex_12_2: 250ft coil of canary yellow NM-B 12/2 electrical wire."""
    m = MeshBuilder("SM_Item_Spool_Romex_12_2")
    m.set_material("romex_yellow", 0.98, 0.85, 0.12)  # Canary yellow #FFEB3B
    m.set_material("core_cardboard", 0.72, 0.62, 0.48)
    m.set_material("shrink_wrap", 0.88, 0.88, 0.90)

    # Donut coil (outer diameter 28cm, inner 12cm, height 10cm)
    m.set_material("romex_yellow", 0.98, 0.85, 0.12)
    m.add_cylinder(0.0, 0.0, 0.0, 10.0, 14.0, segments=12)

    # Center hole / cardboard disc
    m.set_material("core_cardboard", 0.72, 0.62, 0.48)
    m.add_cylinder(0.0, 0.0, 0.0, 10.2, 6.0, segments=10)
    return m


def build_spool_cat6_500ft():
    """SM_Item_Spool_Cat6_500ft: Wooden reel of 500ft blue Cat6 outdoor Ethernet cable."""
    m = MeshBuilder("SM_Item_Spool_Cat6_500ft")
    m.set_material("cat6_blue", 0.12, 0.42, 0.82)      # Royal blue #1976D2
    m.set_material("wood_flange", 0.78, 0.68, 0.52)    # Plywood spool flanges
    m.set_material("spool_hole", 0.18, 0.18, 0.20)

    # 2 circular wooden flanges (diameter 32cm, thickness 1.5cm)
    m.set_material("wood_flange", 0.78, 0.68, 0.52)
    m.add_cylinder(0.0, 0.0, 0.0, 1.5, 16.0, segments=12)
    m.add_cylinder(0.0, 0.0, 24.5, 26.0, 16.0, segments=12)

    # Central blue cable winding (outer diameter 28cm, height 23cm)
    m.set_material("cat6_blue", 0.12, 0.42, 0.82)
    m.add_cylinder(0.0, 0.0, 1.5, 24.5, 14.0, segments=12)

    # Spool arbor hole
    m.set_material("spool_hole", 0.18, 0.18, 0.20)
    m.add_cylinder(0.0, 0.0, 0.0, 26.2, 3.0, segments=8)
    return m


def build_spool_barbed_wire():
    """SM_Item_Spool_BarbedWire: Steel reel of 1320ft 4-point galvanized barbed wire."""
    m = MeshBuilder("SM_Item_Spool_BarbedWire")
    m.set_material("wire_galvanized", 0.72, 0.76, 0.80) # Silver galvanized wire
    m.set_material("spool_frame", 0.26, 0.28, 0.32)

    # Steel wire spool cage (diameter 35cm, height 30cm)
    m.set_material("spool_frame", 0.26, 0.28, 0.32)
    m.add_cylinder(0.0, 0.0, 0.0, 2.0, 17.5, segments=12)
    m.add_cylinder(0.0, 0.0, 28.0, 30.0, 17.5, segments=12)

    # Woven spiky barbed wire core
    m.set_material("wire_galvanized", 0.72, 0.76, 0.80)
    m.add_cylinder(0.0, 0.0, 2.0, 28.0, 15.0, segments=12)
    return m


def build_electric_breaker_subpanel():
    """SM_Item_Electric_BreakerSubpanel: Indoor gray electrical distribution subpanel."""
    m = MeshBuilder("SM_Item_Electric_BreakerSubpanel")
    m.set_material("panel_gray", 0.48, 0.55, 0.60)     # Gray enamel #78909C
    m.set_material("door_latch", 0.22, 0.25, 0.28)
    m.set_material("danger_label", 0.95, 0.80, 0.15)

    # Steel enclosure box (14x36x52cm)
    m.set_material("panel_gray", 0.48, 0.55, 0.60)
    m.add_box(-7.0, 7.0, -18.0, 18.0, 0.0, 52.0)

    # Flush latch
    m.set_material("door_latch", 0.22, 0.25, 0.28)
    m.add_box(6.9, 7.2, 10.0, 14.0, 24.0, 28.0)

    # Warning label
    m.set_material("danger_label", 0.95, 0.80, 0.15)
    m.add_box(6.9, 7.15, -6.0, 6.0, 34.0, 42.0)
    return m


def build_electric_disconnect_switch():
    """SM_Item_Electric_DisconnectSwitch: Weatherproof AC/DC solar safety knife disconnect."""
    m = MeshBuilder("SM_Item_Electric_DisconnectSwitch")
    m.set_material("nema_gray", 0.55, 0.62, 0.68)      # NEMA 3R gray
    m.set_material("handle_red", 0.85, 0.16, 0.14)     # Red throw handle
    m.set_material("handle_shaft", 0.24, 0.26, 0.28)

    # Rainproof box (12x24x36cm)
    m.set_material("nema_gray", 0.55, 0.62, 0.68)
    m.add_box(-6.0, 6.0, -12.0, 12.0, 0.0, 36.0)

    # Drip shield overhang on top
    m.add_box(-7.0, 7.0, -13.0, 13.0, 35.0, 37.0)

    # Side-mounted red disconnect throw handle
    m.set_material("handle_shaft", 0.24, 0.26, 0.28)
    m.add_box(5.8, 9.5, 0.0, 3.0, 16.0, 19.0)

    m.set_material("handle_red", 0.85, 0.16, 0.14)
    m.add_box(8.5, 11.5, -2.0, 5.0, 14.0, 28.0)
    return m


def build_electric_mppt_controller():
    """SM_Item_Electric_MPPTController: 60A solar MPPT charge controller with LCD screen."""
    m = MeshBuilder("SM_Item_Electric_MPPTController")
    m.set_material("mppt_blue", 0.12, 0.38, 0.72)      # Solar controller blue
    m.set_material("heatsink_fin", 0.24, 0.26, 0.28)   # Finned aluminum
    m.set_material("screen_lcd", 0.15, 0.85, 0.45)     # Green backlit LCD screen

    # Extruded heatsink base on back
    m.set_material("heatsink_fin", 0.24, 0.26, 0.28)
    m.add_box(-5.0, -2.0, -13.0, 13.0, 0.0, 34.0)

    # Main blue controller body (10x26x34cm)
    m.set_material("mppt_blue", 0.12, 0.38, 0.72)
    m.add_box(-2.0, 5.0, -13.0, 13.0, 0.0, 34.0)

    # LCD screen on front face
    m.set_material("screen_lcd", 0.15, 0.85, 0.45)
    m.add_box(4.9, 5.2, -6.0, 6.0, 18.0, 26.0)
    return m


def build_electric_network_switch_poe():
    """SM_Item_Electric_NetworkSwitch_PoE: 8-port gigabit outdoor PoE hardened network switch."""
    m = MeshBuilder("SM_Item_Electric_NetworkSwitch_PoE")
    m.set_material("chassis_black", 0.18, 0.20, 0.22)  # Black steel chassis
    m.set_material("rj45_ports", 0.35, 0.38, 0.42)     # Metal shielded ports
    m.set_material("led_green", 0.15, 0.90, 0.45)      # Activity LEDs

    # Metal switch chassis (18x32x5cm)
    m.set_material("chassis_black", 0.18, 0.20, 0.22)
    m.add_box(-9.0, 9.0, -16.0, 16.0, 0.0, 5.0)

    # 8 RJ45 ports on front face
    m.set_material("rj45_ports", 0.35, 0.38, 0.42)
    m.add_box(-8.5, -7.0, -12.0, 12.0, 1.0, 4.0)

    # Green link LEDs
    m.set_material("led_green", 0.15, 0.90, 0.45)
    m.add_box(-9.1, -8.8, -11.0, 11.0, 4.0, 4.6)
    return m


# =============================================================================
# 4. PLUMBING SUPPLIES (5 - UTILITIES)
# =============================================================================

def build_plumbing_pvc_bundle():
    """SM_Item_Plumbing_PVC_Bundle: Banded bundle of 1-inch schedule 40 PVC pipes."""
    m = MeshBuilder("SM_Item_Plumbing_PVC_Bundle")
    m.set_material("pvc_white", 0.96, 0.96, 0.97)      # Clean white PVC #FAFAFA
    m.set_material("tape_blue", 0.12, 0.42, 0.82)      # Blue strapping tape

    # Bundle of 7 pipes (diameter ~22cm, length 280cm along Y)
    m.set_material("pvc_white", 0.96, 0.96, 0.97)
    pipes = [
        (0.0, 11.0),
        (-5.5, 7.8), (5.5, 7.8),
        (-5.5, 14.2), (5.5, 14.2),
        (0.0, 4.6), (0.0, 17.4)
    ]
    for px, pz in pipes:
        m.add_cylinder(-140.0, 140.0, px, pz, 3.2, segments=8, axis='y')

    # Blue strapping tape bands
    m.set_material("tape_blue", 0.12, 0.42, 0.82)
    for ty in [-100.0, 0.0, 100.0]:
        m.add_cylinder(ty - 2.5, ty + 2.5, 0.0, 11.0, 10.5, segments=10, axis='y')
    return m


def build_plumbing_filter_bigblue():
    """SM_Item_Plumbing_Filter_BigBlue: 20-inch Big Blue whole-house filter canister."""
    m = MeshBuilder("SM_Item_Plumbing_Filter_BigBlue")
    m.set_material("sump_blue", 0.08, 0.28, 0.65)      # Deep blue sump #0D47A1
    m.set_material("cap_black", 0.16, 0.16, 0.18)      # Black valve cap
    m.set_material("relief_red", 0.85, 0.16, 0.14)     # Red pressure relief button

    # Blue sump cylinder (diameter 20cm, height 48cm)
    m.set_material("sump_blue", 0.08, 0.28, 0.65)
    m.add_cylinder(0.0, 0.0, 0.0, 48.0, 10.0, segments=12)

    # Black composite cap head (height 12cm)
    m.set_material("cap_black", 0.16, 0.16, 0.18)
    m.add_cylinder(0.0, 0.0, 48.0, 58.0, 10.5, segments=12)
    # Side inlet/outlet ports
    m.add_cylinder(0.0, 0.0, -12.0, 12.0, 2.5, segments=8, axis='y')

    # Red pressure relief button on top
    m.set_material("relief_red", 0.85, 0.16, 0.14)
    m.add_cylinder(0.0, 0.0, 58.0, 60.0, 1.5, segments=6)
    return m


def build_plumbing_gardenhose_reel():
    """SM_Item_Plumbing_GardenHose_Reel: Hose reel with 100ft coiled green contractor hose."""
    m = MeshBuilder("SM_Item_Plumbing_GardenHose_Reel")
    m.set_material("frame_steel", 0.24, 0.28, 0.32)    # Steel frame
    m.set_material("hose_green", 0.18, 0.52, 0.22)     # Emerald hose #2E7D32
    m.set_material("brass_fitting", 0.85, 0.72, 0.28)  # Brass nozzle

    # Steel base frame (45x48x45cm)
    m.set_material("frame_steel", 0.24, 0.28, 0.32)
    m.add_box(-22.0, 22.0, -24.0, 24.0, 0.0, 4.0)

    # 2 Drum side discs
    m.add_cylinder(-16.0, -14.0, 0.0, 24.0, 20.0, segments=12, axis='x')
    m.add_cylinder(14.0, 16.0, 0.0, 24.0, 20.0, segments=12, axis='x')

    # Coiled green garden hose between flanges
    m.set_material("hose_green", 0.18, 0.52, 0.22)
    m.add_cylinder(-14.0, 14.0, 0.0, 24.0, 17.5, segments=12, axis='x')

    # Brass nozzle
    m.set_material("brass_fitting", 0.85, 0.72, 0.28)
    m.add_cylinder(14.0, 22.0, 12.0, 36.0, 1.8, segments=6, axis='x')
    return m


def build_plumbing_waterjug_5gal():
    """SM_Item_Plumbing_WaterJug_5gal: 5-gallon blue polycarbonate drinking water jug."""
    m = MeshBuilder("SM_Item_Plumbing_WaterJug_5gal")
    m.set_material("poly_blue", 0.28, 0.62, 0.92)      # Aqua blue polycarbonate
    m.set_material("cap_blue", 0.12, 0.38, 0.78)       # Sealed cap

    # Cylindrical jug body (diameter 28cm, height 40cm)
    m.set_material("poly_blue", 0.28, 0.62, 0.92)
    m.add_cylinder(0.0, 0.0, 0.0, 38.0, 14.0, segments=12)

    # Tapered shoulder and neck
    m.add_tapered_cylinder(0.0, 0.0, 38.0, 46.0, r_bot=14.0, r_top=3.5, segments=10)
    m.add_cylinder(0.0, 0.0, 46.0, 49.0, 3.5, segments=8)

    # Dark blue sealed cap
    m.set_material("cap_blue", 0.12, 0.38, 0.78)
    m.add_cylinder(0.0, 0.0, 47.5, 49.2, 3.8, segments=8)
    return m


def build_plumbing_drainsock_roll():
    """SM_Item_Plumbing_DrainSock_Roll: Rolled coil of 4-inch polyester drainage sock."""
    m = MeshBuilder("SM_Item_Plumbing_DrainSock_Roll")
    m.set_material("sock_white", 0.92, 0.94, 0.95)     # White geotextile sock
    m.set_material("core_kraft", 0.65, 0.52, 0.38)     # Cardboard tube

    # Donut roll (outer diameter 30cm, inner 10cm, height 22cm)
    m.set_material("sock_white", 0.92, 0.94, 0.95)
    m.add_cylinder(0.0, 0.0, 0.0, 22.0, 15.0, segments=12)

    # Cardboard center core
    m.set_material("core_kraft", 0.65, 0.52, 0.38)
    m.add_cylinder(0.0, 0.0, 0.0, 22.5, 5.0, segments=8)
    return m


# =============================================================================
# REGISTRY & BATCH RUNNER
# =============================================================================

BATCH_5_ASSETS = [
    # 1. Fuel & Heavy Tanks (5 - building)
    ("SM_Item_Fuel_GasCan_5gal", build_fuel_gascan_5gal, "building", "fuel_gasoline.png", "0.22x0.34m", "Red poly 5-gallon gasoline jerry can with pour spout & handle"),
    ("SM_Item_Fuel_DieselCan_5gal", build_fuel_dieselcan_5gal, "building", "fuel_diesel_small.png", "0.22x0.34m", "High-visibility yellow poly 5-gallon diesel fuel can"),
    ("SM_Item_Fuel_PropaneTank_20lb", build_fuel_propanetank_20lb, "building", "fuel_propane_small.png", "0.30x0.30m", "Standard white 20lb BBQ grill LP propane cylinder with OPD valve"),
    ("SM_Item_Tank_Propane_1000gal", build_tank_propane_1000gal, "building", "tank_propane_1000gal.png", "1.10x4.80m", "Massive 1000-gallon horizontal torpedo bullet propane tank on saddles"),
    ("SM_Item_Tank_FuelBulk_Elevated", build_tank_fuel_bulk_elevated, "building", "tank_fuel_bulk_large.png", "1.20x1.80m", "300-gallon red farm gravity bulk fuel tank on steel angle stand"),

    # 2. Fastener & Hardware Boxes (5 - building)
    ("SM_Item_Hardware_FramingNails_Box", build_hardware_framing_nails, "building", "hardware_framing_nails.png", "0.16x0.24m", "50lb box of 16d 3-1/2-inch collated framing strip nails"),
    ("SM_Item_Hardware_DeckScrews_Box", build_hardware_deck_screws, "building", "hardware_deck_screws.png", "0.14x0.20m", "5lb plastic tub of 3-inch coated exterior Torx deck screws"),
    ("SM_Item_Hardware_LagBolts_Box", build_hardware_lag_bolts, "building", "hardware_lag_bolts.png", "0.15x0.22m", "Box of 1/2-inch x 6-inch hot-dipped galvanized hex lag bolts"),
    ("SM_Item_Hardware_GateHinges_Pair", build_hardware_gate_hinges, "building", "hardware_gate_hinges.png", "0.08x0.35m", "Heavy pair of 12-inch black steel strap gate hinges with pintles"),
    ("SM_Item_Hardware_RebarBundle", build_hardware_rebar_bundle, "building", "rebar_steel_bundle.png", "0.18x2.80m", "Banded bundle of #4 (1/2-inch) steel concrete reinforcement rebar"),

    # 3. Electrical & Cable Reels (7 - utilities)
    ("SM_Item_Spool_Romex_12_2", build_spool_romex_12_2, "utilities", "spool_wire_romex_12_2.png", "0.28x0.28m", "250ft coil of yellow NM-B 12/2 residential building electrical wire"),
    ("SM_Item_Spool_Cat6_500ft", build_spool_cat6_500ft, "utilities", "spool_cable_cat6_500ft.png", "0.32x0.32m", "Wooden reel of 500ft blue Cat6 outdoor direct-burial Ethernet cable"),
    ("SM_Item_Spool_BarbedWire", build_spool_barbed_wire, "utilities", "spool_wire_barbed_4pt.png", "0.35x0.35m", "Steel reel of 1320ft 4-point galvanized high-tensile barbed wire"),
    ("SM_Item_Electric_BreakerSubpanel", build_electric_breaker_subpanel, "utilities", "panel_breaker_subpanel.png", "0.14x0.36m", "Indoor grey steel electrical distribution subpanel enclosure"),
    ("SM_Item_Electric_DisconnectSwitch", build_electric_disconnect_switch, "utilities", "switch_disconnect_safety.png", "0.12x0.24m", "Weatherproof outdoor AC/DC solar safety knife disconnect switch"),
    ("SM_Item_Electric_MPPTController", build_electric_mppt_controller, "utilities", "controller_mppt_60a.png", "0.10x0.26m", "60A solar MPPT charge controller with finned aluminum heat sink"),
    ("SM_Item_Electric_NetworkSwitch_PoE", build_electric_network_switch_poe, "utilities", "switch_poe_8port.png", "0.18x0.32m", "8-port gigabit outdoor PoE hardened network switch with port LEDs"),

    # 4. Plumbing Supplies (5 - utilities)
    ("SM_Item_Plumbing_PVC_Bundle", build_plumbing_pvc_bundle, "utilities", "pipe_pvc_two_inch.png", "0.22x2.80m", "Banded bundle of 1-inch schedule 40 PVC pressure pipes"),
    ("SM_Item_Plumbing_Filter_BigBlue", build_plumbing_filter_bigblue, "utilities", "filter_canister_big_blue.png", "0.20x0.20m", "20-inch Big Blue whole-house water filter canister housing"),
    ("SM_Item_Plumbing_GardenHose_Reel", build_plumbing_gardenhose_reel, "utilities", "hose_garden_reel.png", "0.45x0.48m", "Heavy-duty hose reel with 100ft coiled green contractor hose"),
    ("SM_Item_Plumbing_WaterJug_5gal", build_plumbing_waterjug_5gal, "utilities", "water_jug_5gal.png", "0.28x0.28m", "5-gallon blue polycarbonate bottled drinking water jug with cap"),
    ("SM_Item_Plumbing_DrainSock_Roll", build_plumbing_drainsock_roll, "utilities", "drain_french_sock.png", "0.30x0.30m", "Rolled coil of 4-inch polyester drainage sock for French drains"),
]


def sync_icon(src_icon_name, category, model_name):
    src_path = os.path.join(ITEMS_DIR, src_icon_name)
    if not os.path.exists(src_path):
        for root, dirs, files in os.walk(ITEMS_DIR):
            if src_icon_name in files:
                src_path = os.path.join(root, src_icon_name)
                break

    if os.path.exists(src_path):
        paths = CAT_DIRS[category]
        hud_icon = os.path.join(paths["hud_icons"], f"{model_name}.png")
        ue5_icon = os.path.join(paths["ue5_icons"], f"{model_name}.png")
        shutil.copy2(src_path, hud_icon)
        shutil.copy2(src_path, ue5_icon)
        # Also ensure lowercase or uppercase variants if folder exists
        ue5_alt = os.path.join(PROJECT_ROOT, "Homesteader", "Content", "Homesteader", "UI", "Icons", category.lower(), f"{model_name}.png")
        if os.path.exists(os.path.dirname(ue5_alt)):
            shutil.copy2(src_path, ue5_alt)
        return True
    return False


def main():
    print("=====================================================================")
    print("  REBUILDING BATCH 5: 22 HARDWARE, FUEL & SMALL UTILITIES")
    print("  Faithfully matching original item icons in HUD/assets/items/")
    print("=====================================================================\n")

    count = 0
    for name, builder_func, category, icon_name, footprint, desc in BATCH_5_ASSETS:
        count += 1
        print(f"--> Generating {name} ({category})...")

        # 1. Build watertight 3D geometry matching icon
        mesh = builder_func()
        mesh.ground_align()

        paths = CAT_DIRS[category]
        hud_obj = os.path.join(paths["hud_models"], f"{name}.obj")
        hud_mtl = os.path.join(paths["hud_models"], f"{name}.mtl")
        mesh.write_obj_and_mtl(hud_obj, hud_mtl)

        # 2. Sync to UE5 workspace
        ue5_obj = os.path.join(paths["ue5_models"], f"{name}.obj")
        ue5_mtl = os.path.join(paths["ue5_models"], f"{name}.mtl")
        shutil.copy2(hud_obj, ue5_obj)
        shutil.copy2(hud_mtl, ue5_mtl)

        # 3. Synchronize canonical icon
        synced = sync_icon(icon_name, category, name)
        icon_status = f"Synced matching icon from {icon_name}" if synced else f"WARNING: Icon {icon_name} not found"

        total_faces = sum(len(f) for f in mesh.materials.values())
        print(f"    [ICON] {icon_status}")
        print(f"    [DONE] {name}: {len(mesh.vertices)} verts, {total_faces} faces/tris.\n")

    print("Batch 5 successfully rebuilt and synchronized across HUD and UE5!\n")


if __name__ == "__main__":
    main()
