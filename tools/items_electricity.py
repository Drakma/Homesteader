#!/usr/bin/env python3
"""
Homesteader 3D Item Builders: Electricity & Energy System
Covers generators, solar panels, wind turbines, batteries, wiring, cords, inverters, and panels.
"""

import math
from generate_item_assets import Vec3, Mesh

def build_generator_inverter_2000w():
    m = Mesh("generator_inverter_2000w")
    m.add_material("Case_Yellow", 0.94, 0.76, 0.16)
    m.add_material("Handle_Black", 0.20, 0.20, 0.22)
    m.add_material("Panel_Face", 0.28, 0.30, 0.32)
    m.add_material("Outlet_Red", 0.88, 0.18, 0.16)
    # Streamlined suitcase body
    m.add_box(size=(68, 38, 48), center=(0, 0, 26), mat="Case_Yellow")
    # Integrated carry handle
    m.add_box(size=(36, 12, 10), center=(0, 0, 55), mat="Handle_Black")
    # Side electrical control panel
    m.add_box(size=(34, 4, 30), center=(10, 19, 26), mat="Panel_Face")
    m.add_box(size=(8, 5, 8), center=(6, 19, 28), mat="Outlet_Red")
    m.add_box(size=(8, 5, 8), center=(18, 19, 28), mat="Handle_Black")
    # Rubber foot pads
    for x in [-24, 24]:
        for y in [-14, 14]:
            m.add_cylinder(r0=6, r1=6, h=4, z0=0, segs=6, mat="Handle_Black", c0=(x,y), c1=(x,y))
    return m

def build_generator_frame_7500w():
    m = Mesh("generator_frame_7500w")
    m.add_material("Frame_Steel", 0.88, 0.22, 0.18) # Red steel tube cage
    m.add_material("Engine_Cast", 0.30, 0.32, 0.34)
    m.add_material("Tank_Black", 0.20, 0.20, 0.22)
    m.add_material("Wheel_Tire", 0.18, 0.18, 0.20)
    # Steel tube roll cage outline
    for x in [-32, 32]:
        for y in [-24, 24]:
            m.add_cylinder(r0=3, r1=3, h=54, z0=0, segs=6, mat="Frame_Steel", c0=(x,y), c1=(x,y))
    m.add_box(size=(68, 52, 4), center=(0, 0, 54), mat="Frame_Steel")
    # Overhead gas tank
    m.add_box(size=(52, 42, 16), center=(0, 0, 44), mat="Tank_Black")
    # Engine block & alternator
    m.add_box(size=(46, 36, 28), center=(0, 0, 16), mat="Engine_Cast")
    # Rear transport wheels
    for y in [-27, 27]:
        m.add_cylinder(r0=11, r1=11, h=5, z0=11, segs=10, mat="Wheel_Tire", c0=(-28, y-2.5), c1=(-28, y+2.5))
    return m

def build_generator_standby_15kw():
    m = Mesh("generator_standby_15kw")
    m.add_material("Enclosure_Tan", 0.82, 0.78, 0.70)
    m.add_material("Base_Black", 0.22, 0.22, 0.24)
    m.add_material("Louver_Dark", 0.40, 0.38, 0.35)
    # Heavy mounting pad base
    m.add_box(size=(84, 52, 6), center=(0, 0, 3), mat="Base_Black")
    # Sound-attenuated acoustic cabinet
    m.add_box(size=(76, 44, 48), center=(0, 0, 30), mat="Enclosure_Tan")
    # Curved gull-wing roof lid
    m.add_box(size=(78, 46, 6), center=(0, 0, 56), mat="Enclosure_Tan")
    # Cooling air intake louvers
    m.add_box(size=(26, 45, 24), center=(20, 0, 30), mat="Louver_Dark")
    return m

def build_solar_panel_100w_rigid():
    m = Mesh("solar_panel_100w_rigid")
    m.add_material("Alum_Frame", 0.85, 0.86, 0.88)
    m.add_material("PV_Cells", 0.12, 0.20, 0.42) # Deep monocrystalline blue
    m.add_material("Grid_Silver", 0.70, 0.78, 0.90)
    # Tilted solar panel
    m.add_box(size=(52, 76, 5), center=(0, 0, 38), mat="Alum_Frame")
    m.add_box(size=(46, 70, 2), center=(0, 0, 40), mat="PV_Cells")
    # Silver busbars
    m.add_box(size=(46, 2, 2.5), center=(0, 15, 40), mat="Grid_Silver")
    m.add_box(size=(46, 2, 2.5), center=(0, -15, 40), mat="Grid_Silver")
    return m

def build_solar_panel_400w_commercial():
    m = Mesh("solar_panel_400w_commercial")
    m.add_material("Alum_Black", 0.22, 0.22, 0.24)
    m.add_material("PV_Dark", 0.10, 0.14, 0.28)
    m.add_material("Busbars", 0.65, 0.72, 0.85)
    # Large format panel
    m.add_box(size=(58, 88, 5), center=(0, 0, 44), mat="Alum_Black")
    m.add_box(size=(54, 84, 2), center=(0, 0, 46), mat="PV_Dark")
    for y in [-25, 0, 25]:
        m.add_box(size=(54, 1.5, 2.5), center=(0, y, 46), mat="Busbars")
    return m

def build_solar_blanket_200w_folding():
    m = Mesh("solar_blanket_200w_folding")
    m.add_material("Canvas_Black", 0.18, 0.18, 0.20)
    m.add_material("PV_Cell", 0.14, 0.22, 0.45)
    m.add_material("Grommet_Brass", 0.86, 0.68, 0.24)
    # 4 Folded fabric panels in accordion step
    for i, x in enumerate([-30, -10, 10, 30]):
        z = 10 + i * 12
        m.add_box(size=(18, 64, 4), center=(x, 0, z), mat="Canvas_Black")
        m.add_box(size=(14, 58, 2), center=(x, 0, z+2), mat="PV_Cell")
    # Corner brass grommets
    for y in [-28, 28]:
        m.add_cylinder(r0=3, r1=3, h=5, z0=44, segs=6, mat="Grommet_Brass", c0=(36, y), c1=(36, y))
    return m

def build_turbine_wind_400w():
    m = Mesh("turbine_wind_400w")
    m.add_material("Body_White", 0.94, 0.94, 0.96)
    m.add_material("Blades_White", 0.90, 0.90, 0.92)
    m.add_material("Tail_Blue", 0.20, 0.48, 0.85)
    # Mast mount pipe
    m.add_cylinder(r0=6, r1=6, h=50, z0=0, segs=8, mat="Body_White")
    # Aerodynamic nacelle generator body
    m.add_cylinder(r0=10, r1=8, h=28, z0=50, segs=8, mat="Body_White", c0=(0, -14), c1=(0, 14))
    # Directional tail boom & fin
    m.add_cylinder(r0=3, r1=3, h=35, z0=55, segs=6, mat="Body_White", c0=(0, -14), c1=(0, -48))
    m.add_box(size=(2, 24, 28), center=(0, -48, 60), mat="Tail_Blue")
    # 3 Rotor blades
    for i in range(3):
        a = i * 2.0 * math.pi / 3.0
        bx = 28 * math.cos(a)
        bz = 55 + 28 * math.sin(a)
        m.add_cylinder(r0=4, r1=1.5, h=30, z0=55, segs=6, mat="Blades_White", c0=(0, 14), c1=(bx, 14))
    return m

def build_turbine_wind_3kw():
    m = Mesh("turbine_wind_3kw")
    m.add_material("Nacelle_Steel", 0.88, 0.88, 0.90)
    m.add_material("Blades_Carbon", 0.24, 0.26, 0.28)
    m.add_material("Tower_Galv", 0.75, 0.76, 0.78)
    # Heavy lattice tower collar
    m.add_cylinder(r0=12, r1=10, h=40, z0=0, segs=8, mat="Tower_Galv")
    # Large wind generator pod
    m.add_cylinder(r0=16, r1=12, h=42, z0=40, segs=10, mat="Nacelle_Steel", c0=(0, -20), c1=(0, 22))
    # 3 Heavy aerodynamic turbine blades
    for i in range(3):
        a = i * 2.0 * math.pi / 3.0
        bx = 44 * math.cos(a)
        bz = 48 + 44 * math.sin(a)
        m.add_cylinder(r0=6, r1=2, h=45, z0=48, segs=6, mat="Blades_Carbon", c0=(0, 22), c1=(bx, 22))
    return m

def build_battery_12v_agm_100ah():
    m = Mesh("battery_12v_agm_100ah")
    m.add_material("Case_Black", 0.20, 0.20, 0.22)
    m.add_material("Lid_Gray", 0.35, 0.36, 0.38)
    m.add_material("Terminal_Red", 0.88, 0.18, 0.16)
    m.add_material("Terminal_Black", 0.16, 0.16, 0.18)
    # Heavy rectangular SLA battery case
    m.add_box(size=(64, 38, 44), center=(0, 0, 22), mat="Case_Black")
    m.add_box(size=(66, 40, 6), center=(0, 0, 46), mat="Lid_Gray")
    # Lead post terminals with protective caps
    m.add_cylinder(r0=6, r1=5, h=8, z0=49, segs=8, mat="Terminal_Red", c0=(20, 0), c1=(20, 0))
    m.add_cylinder(r0=6, r1=5, h=8, z0=49, segs=8, mat="Terminal_Black", c0=(-20, 0), c1=(-20, 0))
    # Rope carry handles
    m.add_box(size=(8, 28, 4), center=(34, 0, 32), mat="Lid_Gray")
    m.add_box(size=(8, 28, 4), center=(-34, 0, 32), mat="Lid_Gray")
    return m

def build_battery_12v_lifepo4_100ah():
    m = Mesh("battery_12v_lifepo4_100ah")
    m.add_material("Case_White", 0.94, 0.94, 0.95)
    m.add_material("Case_Blue", 0.22, 0.52, 0.88)
    m.add_material("Brass_Lug", 0.88, 0.72, 0.25)
    # Sleek plastic lithium battery case
    m.add_box(size=(62, 36, 42), center=(0, 0, 21), mat="Case_White")
    m.add_box(size=(62, 36, 12), center=(0, 0, 36), mat="Case_Blue")
    # M8 Brass screw terminals
    m.add_cylinder(r0=6, r1=6, h=6, z0=42, segs=8, mat="Brass_Lug", c0=(18, 0), c1=(18, 0))
    m.add_cylinder(r0=6, r1=6, h=6, z0=42, segs=8, mat="Brass_Lug", c0=(-18, 0), c1=(-18, 0))
    return m

def build_battery_rack_48v_5kwh():
    m = Mesh("battery_rack_48v_5kwh")
    m.add_material("Chassis_Black", 0.18, 0.18, 0.20)
    m.add_material("Panel_Face", 0.28, 0.28, 0.30)
    m.add_material("LCD_Screen", 0.20, 0.65, 0.85)
    m.add_material("Breaker_Red", 0.88, 0.18, 0.16)
    m.add_material("Handles_Alum", 0.80, 0.82, 0.84)
    # Standard 19" 3U rackmount battery module
    m.add_box(size=(76, 56, 32), center=(0, 0, 16), mat="Chassis_Black")
    # Front faceplate
    m.add_box(size=(78, 4, 34), center=(0, 29, 17), mat="Panel_Face")
    # Digital status LCD
    m.add_box(size=(18, 2, 10), center=(0, 31, 20), mat="LCD_Screen")
    # DC Circuit breaker switch
    m.add_box(size=(8, 3, 12), center=(-22, 31, 18), mat="Breaker_Red")
    # Rack handles
    m.add_cylinder(r0=2.5, r1=2.5, h=24, z0=6, segs=6, mat="Handles_Alum", c0=(-36, 32), c1=(-36, 32))
    m.add_cylinder(r0=2.5, r1=2.5, h=24, z0=6, segs=6, mat="Handles_Alum", c0=( 36, 32), c1=( 36, 32))
    return m

def build_battery_wall_power_10kwh():
    m = Mesh("battery_wall_power_10kwh")
    m.add_material("Cabinet_White", 0.95, 0.95, 0.96)
    m.add_material("Trim_Silver", 0.80, 0.82, 0.85)
    m.add_material("LED_Glow", 0.35, 0.85, 0.45) # Green status light bar
    # Slim vertical wall cabinet
    m.add_box(size=(52, 18, 88), center=(0, 0, 44), mat="Cabinet_White")
    m.add_box(size=(54, 20, 4), center=(0, 0, 44), mat="Trim_Silver")
    # Glowing vertical power LED strip
    m.add_box(size=(3, 2, 60), center=(0, 9.5, 44), mat="LED_Glow")
    return m

def build_spool_wire_romex_12_2():
    m = Mesh("spool_wire_romex_12_2")
    m.add_material("Cardboard_Spool", 0.78, 0.62, 0.42)
    m.add_material("Jacket_Yellow", 0.94, 0.82, 0.18) # Yellow 12/2 NM-B Romex jacket
    m.add_spool(r_flange=42, r_core=22, h=40, mat_flange="Cardboard_Spool", mat_wire="Jacket_Yellow", z0=0)
    # Loose wire end popping out
    m.add_cylinder(r0=4, r1=4, h=24, z0=30, segs=6, mat="Jacket_Yellow", c0=(36, 0), c1=(48, 15))
    return m

def build_cable_solar_mc4_pair():
    m = Mesh("cable_solar_mc4_pair")
    m.add_material("Cable_Red", 0.88, 0.18, 0.16)
    m.add_material("Cable_Black", 0.20, 0.20, 0.22)
    m.add_material("MC4_Plug", 0.16, 0.16, 0.18)
    # Coiled pair of solar cables
    m.add_torus(r_major=40, r_minor=7, segs_major=16, segs_minor=8, z0=7, mat="Cable_Red")
    m.add_torus(r_major=36, r_minor=7, segs_major=16, segs_minor=8, z0=21, mat="Cable_Black")
    # MC4 Male and female pin connectors
    m.add_cylinder(r0=7, r1=6, h=24, z0=21, segs=8, mat="MC4_Plug", c0=(36, 0), c1=(54, 10))
    m.add_cylinder(r0=7, r1=6, h=24, z0=7, segs=8, mat="MC4_Plug", c0=(-40, 0), c1=(-56, -10))
    return m

def build_cord_generator_30a():
    m = Mesh("cord_generator_30a")
    m.add_material("Cord_Black", 0.22, 0.22, 0.24)
    m.add_material("Plug_Yellow", 0.92, 0.78, 0.20)
    m.add_material("Prongs_Brass", 0.88, 0.72, 0.25)
    # Heavy 10-gauge 4-wire cord coil
    m.add_torus(r_major=42, r_minor=10, segs_major=16, segs_minor=8, z0=10, mat="Cord_Black")
    m.add_torus(r_major=36, r_minor=10, segs_major=16, segs_minor=8, z0=28, mat="Cord_Black")
    # Molded yellow L14-30 twist-lock plug
    m.add_cylinder(r0=14, r1=14, h=24, z0=28, segs=10, mat="Plug_Yellow", c0=(36, 0), c1=(52, 12))
    # 4 curved brass prongs
    for a in [0.2, 1.6, 3.2, 4.8]:
        px = 52 + 7 * math.cos(a)
        py = 12 + 7 * math.sin(a)
        m.add_box(size=(3, 3, 8), center=(px, py, 43), mat="Prongs_Brass")
    return m

def build_cord_shore_power_50a():
    m = Mesh("cord_shore_power_50a")
    m.add_material("Cord_Yellow", 0.94, 0.82, 0.18)
    m.add_material("Plug_Molded", 0.22, 0.22, 0.24)
    m.add_material("Lock_Ring", 0.88, 0.78, 0.22)
    # Heavy thick 50-amp cord coil
    m.add_torus(r_major=44, r_minor=12, segs_major=16, segs_minor=8, z0=12, mat="Cord_Yellow")
    m.add_torus(r_major=38, r_minor=12, segs_major=16, segs_minor=8, z0=34, mat="Cord_Yellow")
    # Heavy molded 14-50P end with locking ring
    m.add_cylinder(r0=18, r1=18, h=26, z0=34, segs=10, mat="Plug_Molded", c0=(38, 0), c1=(55, 14))
    m.add_torus(r_major=19, r_minor=3, segs_major=10, segs_minor=6, z0=48, mat="Lock_Ring", c=(55, 14))
    return m

def build_conduit_pipe_emt():
    m = Mesh("conduit_pipe_emt")
    m.add_material("Steel_EMT", 0.82, 0.84, 0.86)
    m.add_material("Coupling_Zinc", 0.75, 0.76, 0.78)
    m.add_material("Screw_Steel", 0.65, 0.66, 0.68)
    # Metallic conduit tube
    m.add_cylinder(r0=14, r1=14, h=95, z0=0, segs=12, mat="Steel_EMT")
    # Set-screw coupling sleeve in center
    m.add_cylinder(r0=17, r1=17, h=24, z0=40, segs=12, mat="Coupling_Zinc")
    # Set screws
    m.add_box(size=(6, 6, 6), center=(17, 0, 46), mat="Screw_Steel")
    m.add_box(size=(6, 6, 6), center=(17, 0, 58), mat="Screw_Steel")
    return m

def build_cables_battery_interconnect():
    m = Mesh("cables_battery_interconnect")
    m.add_material("Jacket_Red", 0.88, 0.18, 0.16)
    m.add_material("Jacket_Black", 0.20, 0.20, 0.22)
    m.add_material("Copper_Lug", 0.88, 0.54, 0.22)
    # Red jumper cable arch
    m.add_cylinder(r0=7, r1=7, h=55, z0=0, segs=8, mat="Jacket_Red", c0=(-24, -12), c1=(24, -12))
    m.add_cylinder(r0=11, r1=11, h=4, z0=0, segs=8, mat="Copper_Lug", c0=(-24, -12), c1=(-24, -12))
    m.add_cylinder(r0=11, r1=11, h=4, z0=0, segs=8, mat="Copper_Lug", c0=( 24, -12), c1=( 24, -12))
    # Black jumper cable arch
    m.add_cylinder(r0=7, r1=7, h=55, z0=0, segs=8, mat="Jacket_Black", c0=(-24, 12), c1=(24, 12))
    m.add_cylinder(r0=11, r1=11, h=4, z0=0, segs=8, mat="Copper_Lug", c0=(-24, 12), c1=(-24, 12))
    m.add_cylinder(r0=11, r1=11, h=4, z0=0, segs=8, mat="Copper_Lug", c0=( 24, 12), c1=( 24, 12))
    return m

def build_rod_grounding_copper():
    m = Mesh("rod_grounding_copper")
    m.add_material("Solid_Copper", 0.88, 0.54, 0.22)
    m.add_material("Bronze_Clamp", 0.72, 0.52, 0.24)
    m.add_material("Ground_Wire", 0.85, 0.50, 0.20)
    # Long solid copper driven ground rod
    m.add_cylinder(r0=6, r1=6, h=95, z0=0, segs=8, mat="Solid_Copper")
    m.add_cone(r=6, h=10, z0=0, segs=8, mat="Solid_Copper") # Driven point
    # Bronze acorn ground clamp
    m.add_box(size=(22, 18, 16), center=(0, 0, 75), mat="Bronze_Clamp")
    # Ground wire lead clamped
    m.add_cylinder(r0=3, r1=3, h=30, z0=75, segs=6, mat="Ground_Wire", c0=(0, 0), c1=(24, 20))
    return m

def build_inverter_hybrid_3000w():
    m = Mesh("inverter_hybrid_3000w")
    m.add_material("Inverter_Blue", 0.18, 0.44, 0.82)
    m.add_material("Face_Black", 0.20, 0.20, 0.22)
    m.add_material("LCD_Screen", 0.20, 0.75, 0.88)
    m.add_material("Heatsink_Gray", 0.65, 0.68, 0.70)
    # Vertical wall-hung hybrid inverter
    m.add_box(size=(54, 26, 78), center=(0, 0, 39), mat="Inverter_Blue")
    m.add_box(size=(46, 2, 45), center=(0, 14, 45), mat="Face_Black")
    # Digital LCD display screen
    m.add_box(size=(24, 2, 16), center=(0, 15, 52), mat="LCD_Screen")
    # Bottom wire connection bay with conduit knockouts
    m.add_box(size=(50, 24, 14), center=(0, 0, 7), mat="Face_Black")
    return m

def build_controller_mppt_60a():
    m = Mesh("controller_mppt_60a")
    m.add_material("Alum_Fins", 0.35, 0.38, 0.42)
    m.add_material("Front_Blue", 0.22, 0.54, 0.88)
    m.add_material("Screen_LCD", 0.20, 0.70, 0.85)
    # Heatsink finned backplate
    m.add_box(size=(48, 22, 64), center=(0, 0, 32), mat="Alum_Fins")
    # Front cover housing
    m.add_box(size=(44, 12, 58), center=(0, 7, 32), mat="Front_Blue")
    # Backlit LCD screen
    m.add_box(size=(22, 2, 14), center=(0, 14, 40), mat="Screen_LCD")
    # Terminal block connections at bottom
    m.add_box(size=(38, 6, 8), center=(0, 10, 8), mat="Alum_Fins")
    return m

def build_panel_breaker_subpanel():
    m = Mesh("panel_breaker_subpanel")
    m.add_material("Steel_Gray", 0.68, 0.70, 0.72)
    m.add_material("Door_Latch", 0.85, 0.85, 0.88)
    m.add_material("Breaker_Black", 0.20, 0.20, 0.22)
    # Weatherproof NEMA 3R outdoor subpanel
    m.add_box(size=(52, 22, 74), center=(0, 0, 37), mat="Steel_Gray")
    # Top rain hood drip shield
    m.add_box(size=(56, 26, 4), center=(0, 0, 74), mat="Steel_Gray")
    # Front door panel with padlock latch
    m.add_box(size=(48, 2, 68), center=(0, 12, 36), mat="Steel_Gray")
    m.add_box(size=(6, 4, 12), center=(22, 12, 36), mat="Door_Latch")
    return m

def build_switch_disconnect_safety():
    m = Mesh("switch_disconnect_safety")
    m.add_material("Steel_Gray", 0.68, 0.70, 0.72)
    m.add_material("Lever_Red", 0.88, 0.18, 0.16)
    m.add_material("Handle_Grip", 0.20, 0.20, 0.22)
    # Exterior fusible safety disconnect enclosure
    m.add_box(size=(42, 24, 65), center=(0, 0, 32), mat="Steel_Gray")
    # Side external safety disconnect throw lever
    m.add_cylinder(r0=4, r1=4, h=30, z0=35, segs=6, mat="Lever_Red", c0=(21, 0), c1=(35, 15))
    m.add_cylinder(r0=6, r1=6, h=14, z0=46, segs=8, mat="Handle_Grip", c0=(35, 15), c1=(42, 22))
    return m

ELECTRICITY_BUILDERS = [
    ("generator_inverter_2000w", build_generator_inverter_2000w, "electricity", "generation"),
    ("generator_frame_7500w", build_generator_frame_7500w, "electricity", "generation"),
    ("generator_standby_15kw", build_generator_standby_15kw, "electricity", "generation"),
    ("solar_panel_100w_rigid", build_solar_panel_100w_rigid, "electricity", "generation"),
    ("solar_panel_400w_commercial", build_solar_panel_400w_commercial, "electricity", "generation"),
    ("solar_blanket_200w_folding", build_solar_blanket_200w_folding, "electricity", "generation"),
    ("turbine_wind_400w", build_turbine_wind_400w, "electricity", "generation"),
    ("turbine_wind_3kw", build_turbine_wind_3kw, "electricity", "generation"),
    ("battery_12v_agm_100ah", build_battery_12v_agm_100ah, "electricity", "storage"),
    ("battery_12v_lifepo4_100ah", build_battery_12v_lifepo4_100ah, "electricity", "storage"),
    ("battery_rack_48v_5kwh", build_battery_rack_48v_5kwh, "electricity", "storage"),
    ("battery_wall_power_10kwh", build_battery_wall_power_10kwh, "electricity", "storage"),
    ("spool_wire_romex_12_2", build_spool_wire_romex_12_2, "electricity", "wiring"),
    ("cable_solar_mc4_pair", build_cable_solar_mc4_pair, "electricity", "wiring"),
    ("cord_generator_30a", build_cord_generator_30a, "electricity", "wiring"),
    ("cord_shore_power_50a", build_cord_shore_power_50a, "electricity", "wiring"),
    ("conduit_pipe_emt", build_conduit_pipe_emt, "electricity", "wiring"),
    ("cables_battery_interconnect", build_cables_battery_interconnect, "electricity", "wiring"),
    ("rod_grounding_copper", build_rod_grounding_copper, "electricity", "wiring"),
    ("inverter_hybrid_3000w", build_inverter_hybrid_3000w, "electricity", "generation"),
    ("controller_mppt_60a", build_controller_mppt_60a, "electricity", "generation"),
    ("panel_breaker_subpanel", build_panel_breaker_subpanel, "electricity", "wiring"),
    ("switch_disconnect_safety", build_switch_disconnect_safety, "electricity", "wiring"),
]

