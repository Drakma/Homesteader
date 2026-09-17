#!/usr/bin/env python3
"""
Homesteader 3D Item Builders: Internet & Networking System
Covers satellite dishes, cellular antennas, routers, access points, PoE switches, and outdoor cabling.
"""

import math
from generate_item_assets import Vec3, Mesh

def build_dish_satellite_standard():
    m = Mesh("dish_satellite_standard")
    m.add_material("Dish_White", 0.94, 0.94, 0.95)
    m.add_material("Mast_Gray", 0.72, 0.74, 0.76)
    m.add_material("Base_Black", 0.22, 0.22, 0.24)
    # X-shaped ground base stand
    m.add_box(size=(64, 8, 4), center=(0, 0, 2), mat="Base_Black")
    m.add_box(size=(8, 64, 4), center=(0, 0, 2), mat="Base_Black")
    # Vertical mast tube
    m.add_cylinder(r0=5, r1=5, h=48, z0=2, segs=8, mat="Mast_Gray")
    # Rectangular phased array antenna dish (tilted at 40 degrees)
    m.add_box(size=(48, 72, 5), center=(0, 10, 62), mat="Dish_White")
    return m

def build_dish_satellite_high_perf():
    m = Mesh("dish_satellite_high_perf")
    m.add_material("Dish_White", 0.94, 0.94, 0.95)
    m.add_material("Mast_Galv", 0.72, 0.74, 0.76)
    m.add_material("Feed_Horn", 0.28, 0.30, 0.32)
    # Quad-pod roof mount
    m.add_box(size=(60, 60, 4), center=(0, 0, 2), mat="Mast_Galv")
    m.add_cylinder(r0=6, r1=6, h=45, z0=2, segs=8, mat="Mast_Galv")
    # Parabolic dish reflector (shallow cone)
    m.add_cone(r=38, h=12, z0=45, segs=14, mat="Dish_White", cap=True)
    # Feed horn boom arm & LNB receiver
    m.add_cylinder(r0=2.5, r1=2.5, h=30, z0=52, segs=6, mat="Mast_Galv", c0=(0, -25), c1=(0, 0))
    m.add_cylinder(r0=5, r1=4, h=10, z0=78, segs=8, mat="Feed_Horn")
    return m

def build_antenna_yagi_directional():
    m = Mesh("antenna_yagi_directional")
    m.add_material("Alum_Boom", 0.85, 0.86, 0.88)
    m.add_material("Elements", 0.80, 0.82, 0.84)
    m.add_material("Mount_Bracket", 0.65, 0.66, 0.68)
    # Main longitudinal boom bar
    m.add_box(size=(8, 88, 8), center=(0, 0, 50), mat="Alum_Boom")
    # Cross director elements of decreasing length
    lengths = [70, 62, 55, 48, 42, 36]
    for i, l in enumerate(lengths):
        y = -35 + i * 14
        m.add_cylinder(r0=2, r1=2, h=l, z0=50-l*0.5, segs=6, mat="Elements", c0=(-l*0.5, y), c1=(l*0.5, y))
    # Rear reflector screen
    m.add_box(size=(76, 4, 30), center=(0, -40, 50), mat="Elements")
    # Pole mounting bracket
    m.add_box(size=(22, 16, 24), center=(0, -20, 26), mat="Mount_Bracket")
    return m

def build_antenna_omni_cellular():
    m = Mesh("antenna_omni_cellular")
    m.add_material("Fiberglass_White", 0.95, 0.95, 0.96)
    m.add_material("Chrome_Base", 0.88, 0.90, 0.92)
    m.add_material("Mount_Clamp", 0.70, 0.72, 0.74)
    # Threaded chrome base ferrule
    m.add_cylinder(r0=9, r1=8, h=25, z0=0, segs=10, mat="Chrome_Base")
    m.add_box(size=(24, 20, 18), center=(0, 0, 10), mat="Mount_Clamp")
    # Slender vertical fiberglass antenna radome
    m.add_cylinder(r0=6, r1=4.5, h=85, z0=25, segs=10, mat="Fiberglass_White")
    # Top protective cap
    m.add_foliage_lobe(radius=5, center=(0, 0, 110), mat="Fiberglass_White")
    return m

def build_mount_j_mast_bracket():
    m = Mesh("mount_j_mast_bracket")
    m.add_material("Galv_Steel", 0.78, 0.80, 0.82)
    m.add_material("Bolts_Zinc", 0.68, 0.70, 0.72)
    # Foot mounting base plate with screw holes
    m.add_box(size=(46, 36, 6), center=(0, 0, 3), mat="Galv_Steel")
    # Pivot bracket ears
    m.add_box(size=(12, 28, 24), center=(0, 0, 15), mat="Galv_Steel")
    # J-pole curved tube
    m.add_cylinder(r0=6, r1=6, h=40, z0=15, segs=8, mat="Galv_Steel", c0=(0, 0), c1=(0, 25))
    m.add_cylinder(r0=6, r1=6, h=55, z0=45, segs=8, mat="Galv_Steel", c0=(0, 25), c1=(0, 25))
    # Adjustment locking bolts
    m.add_box(size=(18, 10, 8), center=(0, 0, 20), mat="Bolts_Zinc")
    return m

def build_router_mesh_wifi6():
    m = Mesh("router_mesh_wifi6")
    m.add_material("Chassis_White", 0.95, 0.95, 0.96)
    m.add_material("Base_Gray", 0.35, 0.36, 0.38)
    m.add_material("LED_Ring", 0.20, 0.65, 0.95) # Glowing blue LED ring
    # Elegant upright cylindrical mesh tower
    m.add_cylinder(r0=24, r1=22, h=75, z0=6, segs=14, mat="Chassis_White")
    # Rounded top cap
    m.add_foliage_lobe(radius=22, center=(0, 0, 81), mat="Chassis_White")
    # Bottom base ring with glowing cyan status indicator
    m.add_cylinder(r0=25, r1=25, h=6, z0=0, segs=14, mat="Base_Gray")
    m.add_cylinder(r0=24.5, r1=24.5, h=2.5, z0=6, segs=14, mat="LED_Ring")
    return m

def build_ap_outdoor_weatherproof():
    m = Mesh("ap_outdoor_weatherproof")
    m.add_material("Body_White", 0.94, 0.94, 0.95)
    m.add_material("Antenna_Black", 0.20, 0.20, 0.22)
    m.add_material("Pole_Mount", 0.72, 0.74, 0.76)
    # Slim oval weatherproof AP enclosure
    m.add_box(size=(38, 18, 60), center=(0, 0, 30), mat="Body_White")
    # Dual omnidirectional rubber duck antennas on top
    m.add_cylinder(r0=3, r1=2.5, h=35, z0=60, segs=6, mat="Antenna_Black", c0=(-12, 0), c1=(-16, 0))
    m.add_cylinder(r0=3, r1=2.5, h=35, z0=60, segs=6, mat="Antenna_Black", c0=( 12, 0), c1=( 16, 0))
    # Rear pole mounting bracket
    m.add_box(size=(24, 10, 32), center=(0, -12, 30), mat="Pole_Mount")
    return m

def build_switch_poe_8port():
    m = Mesh("switch_poe_8port")
    m.add_material("Chassis_Black", 0.18, 0.18, 0.20)
    m.add_material("RJ45_Metal", 0.75, 0.78, 0.80)
    m.add_material("LED_Green", 0.35, 0.88, 0.35)
    # Compact metal desktop switch chassis
    m.add_box(size=(74, 46, 20), center=(0, 0, 10), mat="Chassis_Black")
    # 8 RJ45 Gigabit Ethernet Ports in a row
    for i in range(8):
        x = -28 + i * 8
        m.add_box(size=(6, 3, 7), center=(x, 23, 10), mat="RJ45_Metal")
        m.add_box(size=(2, 2, 2), center=(x, 23.5, 16), mat="LED_Green")
    return m

def build_switch_rackmount_16port():
    m = Mesh("switch_rackmount_16port")
    m.add_material("Chassis_Dark", 0.22, 0.24, 0.26)
    m.add_material("Rack_Ears", 0.65, 0.68, 0.70)
    m.add_material("RJ45_Shield", 0.78, 0.80, 0.82)
    m.add_material("LED_Link", 0.30, 0.85, 0.40)
    # 1U Rackmount switch
    m.add_box(size=(80, 52, 16), center=(0, 0, 8), mat="Chassis_Dark")
    # Side rack ears with mounting holes
    m.add_box(size=(8, 12, 18), center=(-44, 18, 8), mat="Rack_Ears")
    m.add_box(size=(8, 12, 18), center=( 44, 18, 8), mat="Rack_Ears")
    # Dual rows of 8 RJ45 ports (16 total)
    for i in range(8):
        x = -24 + i * 7
        m.add_box(size=(5, 3, 5), center=(x, 26, 6), mat="RJ45_Shield")
        m.add_box(size=(5, 3, 5), center=(x, 26, 12), mat="RJ45_Shield")
        m.add_box(size=(1.5, 1.5, 1.5), center=(x, 26.5, 15), mat="LED_Link")
    return m

def build_injector_poe_adapter():
    m = Mesh("injector_poe_adapter")
    m.add_material("Plastic_Black", 0.20, 0.20, 0.22)
    m.add_material("RJ45_Jack", 0.75, 0.78, 0.80)
    m.add_material("LED_Power", 0.88, 0.78, 0.20)
    m.add_material("IEC_Socket", 0.15, 0.15, 0.16)
    # Power brick body
    m.add_box(size=(42, 28, 22), center=(0, 0, 11), mat="Plastic_Black")
    # Dual LAN + PoE RJ45 jacks
    m.add_box(size=(9, 3, 8), center=(-10, 14, 11), mat="RJ45_Jack")
    m.add_box(size=(9, 3, 8), center=( 10, 14, 11), mat="RJ45_Jack")
    m.add_box(size=(3, 2, 3), center=(0, 14, 17), mat="LED_Power")
    # Rear AC power inlet
    m.add_box(size=(16, 3, 10), center=(0, -14, 11), mat="IEC_Socket")
    return m

def build_spool_cable_cat6_500ft():
    m = Mesh("spool_cable_cat6_500ft")
    m.add_material("Wood_Plywood", 0.78, 0.62, 0.42)
    m.add_material("Cable_Black", 0.18, 0.18, 0.20) # Heavy direct burial jacket
    m.add_material("Core_Blue", 0.22, 0.52, 0.88)
    m.add_spool(r_flange=42, r_core=22, h=44, mat_flange="Wood_Plywood", mat_wire="Cable_Black", z0=0)
    # Cable lead extending out
    m.add_cylinder(r0=4, r1=4, h=25, z0=34, segs=6, mat="Cable_Black", c0=(36, 0), c1=(48, 16))
    m.add_cylinder(r0=3, r1=3, h=5, z0=34, segs=6, mat="Core_Blue", c0=(48, 16), c1=(51, 18))
    return m

def build_cable_ethernet_cat6_50ft():
    m = Mesh("cable_ethernet_cat6_50ft")
    m.add_material("Cable_Blue", 0.22, 0.54, 0.88)
    m.add_material("Boot_Black", 0.20, 0.20, 0.22)
    m.add_material("RJ45_Clear", 0.82, 0.85, 0.88)
    m.add_material("Gold_Pins", 0.90, 0.75, 0.25)
    # Coiled 50ft blue patch cable
    m.add_torus(r_major=40, r_minor=6, segs_major=16, segs_minor=8, z0=6, mat="Cable_Blue")
    m.add_torus(r_major=35, r_minor=6, segs_major=16, segs_minor=8, z0=18, mat="Cable_Blue")
    # Molded snagless boot & RJ45 modular plug
    m.add_cylinder(r0=6, r1=5.5, h=16, z0=18, segs=8, mat="Boot_Black", c0=(35, 0), c1=(48, 10))
    m.add_box(size=(9, 14, 7), center=(55, 14, 25), mat="RJ45_Clear")
    m.add_box(size=(7, 2, 2), center=(55, 20, 27), mat="Gold_Pins")
    return m

def build_cable_ethernet_cat6_100ft():
    m = Mesh("cable_ethernet_cat6_100ft")
    m.add_material("Cable_Black", 0.20, 0.20, 0.22)
    m.add_material("Shield_Metal", 0.78, 0.80, 0.82)
    m.add_material("Tie_Velcro", 0.88, 0.22, 0.18)
    # Heavy 100ft black cable triple coil
    m.add_torus(r_major=44, r_minor=7, segs_major=16, segs_minor=8, z0=7, mat="Cable_Black")
    m.add_torus(r_major=38, r_minor=7, segs_major=16, segs_minor=8, z0=21, mat="Cable_Black")
    m.add_torus(r_major=32, r_minor=7, segs_major=16, segs_minor=8, z0=35, mat="Cable_Black")
    # Red velcro binding strap
    m.add_box(size=(12, 18, 38), center=(0, 38, 20), mat="Tie_Velcro")
    m.add_box(size=(12, 18, 38), center=(0, -38, 20), mat="Tie_Velcro")
    # Shielded metal RJ45 connector
    m.add_box(size=(10, 16, 8), center=(42, 10, 42), mat="Shield_Metal")
    return m

def build_arrestor_lightning_ethernet():
    m = Mesh("arrestor_lightning_ethernet")
    m.add_material("Cast_Alum", 0.80, 0.82, 0.84)
    m.add_material("RJ45_Shield", 0.70, 0.72, 0.74)
    m.add_material("Ground_Copper", 0.88, 0.55, 0.22)
    # Heavy shielded metal block
    m.add_box(size=(46, 28, 22), center=(0, 0, 11), mat="Cast_Alum")
    # In / Out shielded RJ45 ports
    m.add_box(size=(10, 3, 9), center=(-14, 0, 11), mat="RJ45_Shield")
    m.add_box(size=(10, 3, 9), center=( 14, 0, 11), mat="RJ45_Shield")
    # Heavy ground wire attachment terminal & green-yellow pigtail
    m.add_cylinder(r0=4, r1=4, h=10, z0=22, segs=8, mat="Ground_Copper", c0=(0, 0), c1=(0, 0))
    m.add_cylinder(r0=2.5, r1=2.5, h=25, z0=26, segs=6, mat="Ground_Copper", c0=(0, 0), c1=(18, 12))
    return m

def build_gland_cable_entry_wall():
    m = Mesh("gland_cable_entry_wall")
    m.add_material("Silicone_White", 0.92, 0.93, 0.94)
    m.add_material("Nut_Poly", 0.80, 0.82, 0.84)
    m.add_material("Rubber_Seal", 0.22, 0.22, 0.24)
    # Weatherproof wall flange sleeve
    m.add_cylinder(r0=24, r1=24, h=6, z0=0, segs=12, mat="Nut_Poly")
    m.add_cylinder(r0=16, r1=16, h=40, z0=6, segs=12, mat="Silicone_White")
    # Threaded compression nut
    m.add_cylinder(r0=20, r1=18, h=18, z0=46, segs=6, mat="Nut_Poly")
    # Black rubber inner compression bushing with dual cable ports
    m.add_cylinder(r0=12, r1=12, h=4, z0=64, segs=10, mat="Rubber_Seal")
    m.add_cylinder(r0=3, r1=3, h=15, z0=58, segs=6, mat="Rubber_Seal", c0=(-5, 0), c1=(-5, 0))
    m.add_cylinder(r0=3, r1=3, h=15, z0=58, segs=6, mat="Rubber_Seal", c0=( 5, 0), c1=( 5, 0))
    return m

INTERNET_BUILDERS = [
    ("dish_satellite_standard", build_dish_satellite_standard, "internet", "satellite_antennas"),
    ("dish_satellite_high_perf", build_dish_satellite_high_perf, "internet", "satellite_antennas"),
    ("antenna_yagi_directional", build_antenna_yagi_directional, "internet", "satellite_antennas"),
    ("antenna_omni_cellular", build_antenna_omni_cellular, "internet", "satellite_antennas"),
    ("mount_j_mast_bracket", build_mount_j_mast_bracket, "internet", "satellite_antennas"),
    ("router_mesh_wifi6", build_router_mesh_wifi6, "internet", "routers_networking"),
    ("ap_outdoor_weatherproof", build_ap_outdoor_weatherproof, "internet", "routers_networking"),
    ("switch_poe_8port", build_switch_poe_8port, "internet", "routers_networking"),
    ("switch_rackmount_16port", build_switch_rackmount_16port, "internet", "routers_networking"),
    ("injector_poe_adapter", build_injector_poe_adapter, "internet", "routers_networking"),
    ("spool_cable_cat6_500ft", build_spool_cable_cat6_500ft, "internet", "cabling"),
    ("cable_ethernet_cat6_50ft", build_cable_ethernet_cat6_50ft, "internet", "cabling"),
    ("cable_ethernet_cat6_100ft", build_cable_ethernet_cat6_100ft, "internet", "cabling"),
    ("arrestor_lightning_ethernet", build_arrestor_lightning_ethernet, "internet", "cabling"),
    ("gland_cable_entry_wall", build_gland_cable_entry_wall, "internet", "cabling"),
]

