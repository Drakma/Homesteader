#!/usr/bin/env python3
"""
Homesteader 3D Item Builders: Tools & Equipment System
Covers hand tools, shovels, axes, hammers, wrenches, chainsaws, drills, and backpack sprayers.
"""

import math
from generate_item_assets import Vec3, Mesh

def build_tool_trowel_hand():
    m = Mesh("tool_trowel_hand")
    m.add_material("Steel_Shovel", 0.82, 0.85, 0.88)
    m.add_material("Wood_Hickory", 0.76, 0.58, 0.38)
    m.add_material("Collar_Brass", 0.86, 0.68, 0.24)
    # Turned wood handle
    m.add_cylinder(r0=6, r1=7, h=36, z0=0, segs=8, mat="Wood_Hickory")
    m.add_cylinder(r0=7, r1=6, h=6, z0=36, segs=8, mat="Collar_Brass")
    # Curved neck
    m.add_cylinder(r0=4, r1=4, h=20, z0=42, segs=6, mat="Steel_Shovel", c0=(0,0), c1=(8, 10))
    # Concave scoop blade
    m.add_box(size=(24, 40, 4), center=(14, 20, 68), mat="Steel_Shovel")
    m.add_cone(r=12, h=16, z0=88, segs=6, mat="Steel_Shovel", c=(14, 20))
    return m

def build_tool_shovel_trenching():
    m = Mesh("tool_shovel_trenching")
    m.add_material("Steel_Black", 0.22, 0.24, 0.26)
    m.add_material("Wood_Ash", 0.80, 0.64, 0.44)
    m.add_material("D_Grip", 0.85, 0.20, 0.16)
    # D-handle at top
    m.add_box(size=(22, 10, 6), center=(0, 0, 94), mat="D_Grip")
    m.add_cylinder(r0=5, r1=5, h=16, z0=80, segs=6, mat="Wood_Ash")
    # Long wood shaft
    m.add_cylinder(r0=5, r1=4.5, h=55, z0=25, segs=8, mat="Wood_Ash")
    # Narrow trenching blade with foot steps
    m.add_box(size=(14, 6, 32), center=(0, 0, 16), mat="Steel_Black")
    m.add_box(size=(20, 10, 4), center=(0, 0, 30), mat="Steel_Black") # Foot tread
    return m

def build_tool_shovel_round_point():
    m = Mesh("tool_shovel_round_point")
    m.add_material("Steel_Blade", 0.32, 0.34, 0.36)
    m.add_material("Edge_Shiny", 0.80, 0.82, 0.85)
    m.add_material("Wood_Shaft", 0.78, 0.60, 0.40)
    # Long handle
    m.add_cylinder(r0=5, r1=4.5, h=72, z0=28, segs=8, mat="Wood_Shaft")
    # Socket collar
    m.add_cylinder(r0=7, r1=6, h=15, z0=22, segs=8, mat="Steel_Blade")
    # Round-point scoop blade
    m.add_box(size=(28, 6, 26), center=(0, 0, 12), mat="Steel_Blade")
    m.add_cone(r=14, h=14, z0=0, segs=8, mat="Edge_Shiny") # Pointed tip
    return m

def build_tool_shovel_scoop_flat():
    m = Mesh("tool_shovel_scoop_flat")
    m.add_material("Alum_Scoop", 0.85, 0.88, 0.90)
    m.add_material("Wood_Shaft", 0.78, 0.60, 0.40)
    m.add_material("D_Grip", 0.22, 0.22, 0.24)
    # D-handle
    m.add_box(size=(24, 10, 6), center=(0, 0, 94), mat="D_Grip")
    m.add_cylinder(r0=5, r1=5, h=65, z0=28, segs=8, mat="Wood_Shaft")
    # Wide aluminum grain scoop
    m.add_box(size=(46, 12, 34), center=(0, 0, 16), mat="Alum_Scoop")
    m.add_box(size=(46, 2, 4), center=(0, 6, 0), mat="Alum_Scoop")
    return m

def build_tool_hatchet_camp():
    m = Mesh("tool_hatchet_camp")
    m.add_material("Hickory_Wood", 0.80, 0.62, 0.42)
    m.add_material("Steel_Head", 0.42, 0.44, 0.46)
    m.add_material("Edge_Sharp", 0.88, 0.90, 0.92)
    # Curved short handle
    m.add_cylinder(r0=6, r1=5, h=65, z0=0, segs=8, mat="Hickory_Wood", c0=(0,0), c1=(6, 4))
    # Forged hatchet head
    m.add_box(size=(14, 34, 18), center=(6, 10, 60), mat="Steel_Head")
    # Cutting blade flare
    m.add_box(size=(4, 22, 24), center=(6, 26, 60), mat="Edge_Sharp")
    return m

def build_tool_axe_felling():
    m = Mesh("tool_axe_felling")
    m.add_material("Hickory_Wood", 0.78, 0.58, 0.38)
    m.add_material("Steel_Forged", 0.35, 0.37, 0.40)
    m.add_material("Blade_Edge", 0.88, 0.90, 0.94)
    # Long felling handle with fawn-foot curve
    m.add_cylinder(r0=6, r1=5, h=88, z0=0, segs=8, mat="Hickory_Wood", c0=(0,0), c1=(8, 6))
    # Heavy 3.5lb felling head
    m.add_box(size=(16, 40, 20), center=(8, 12, 82), mat="Steel_Forged")
    # Razor felling bit
    m.add_box(size=(4, 26, 28), center=(8, 32, 82), mat="Blade_Edge")
    return m

def build_tool_maul_splitting():
    m = Mesh("tool_maul_splitting")
    m.add_material("Fiberglass_Yellow", 0.92, 0.78, 0.18)
    m.add_material("Grip_Rubber", 0.18, 0.18, 0.20)
    m.add_material("Maul_Iron", 0.28, 0.28, 0.30)
    m.add_material("Wedge_Cheeks", 0.40, 0.42, 0.44)
    # High-visibility yellow handle with textured grip
    m.add_cylinder(r0=6, r1=5.5, h=86, z0=0, segs=8, mat="Fiberglass_Yellow")
    m.add_cylinder(r0=7, r1=7, h=30, z0=0, segs=8, mat="Grip_Rubber")
    # Heavy 8lb splitting wedge head (sledge hammer face on back, wide wedge on front)
    m.add_box(size=(20, 22, 22), center=(0, -10, 80), mat="Maul_Iron") # Sledge pole
    m.add_cone(r=16, h=26, z0=80, segs=6, mat="Wedge_Cheeks", c=(0, 16)) # Splitting wedge
    return m

def build_tool_hammer_claw():
    m = Mesh("tool_hammer_claw")
    m.add_material("Handle_Steel", 0.75, 0.78, 0.80)
    m.add_material("Grip_Blue", 0.20, 0.48, 0.85)
    m.add_material("Head_DropForged", 0.35, 0.36, 0.38)
    # Rubber shock-reduction grip
    m.add_cylinder(r0=6.5, r1=6, h=40, z0=0, segs=8, mat="Grip_Blue")
    m.add_cylinder(r0=5.5, r1=5, h=35, z0=40, segs=8, mat="Handle_Steel")
    # Striking poll face
    m.add_cylinder(r0=9, r1=9, h=18, z0=75, segs=10, mat="Head_DropForged", c0=(0, -8), c1=(0, -22))
    # Curved extraction claws
    m.add_box(size=(8, 20, 16), center=(0, 8, 77), mat="Head_DropForged")
    return m

def build_tool_hammer_club():
    m = Mesh("tool_hammer_club")
    m.add_material("Wood_Handle", 0.74, 0.54, 0.36)
    m.add_material("Steel_Head", 0.32, 0.34, 0.36)
    # Short stout handle
    m.add_cylinder(r0=7, r1=6.5, h=55, z0=0, segs=8, mat="Wood_Handle")
    # Heavy 4lb double-face square drilling head
    m.add_box(size=(26, 44, 26), center=(0, 0, 52), mat="Steel_Head")
    return m

def build_tool_wrench_pipe():
    m = Mesh("tool_wrench_pipe")
    m.add_material("CastIron_Red", 0.86, 0.22, 0.18)
    m.add_material("Steel_Jaw", 0.40, 0.42, 0.45)
    m.add_material("Knurl_Nut", 0.75, 0.65, 0.25)
    # Heavy red I-beam handle
    m.add_box(size=(10, 18, 70), center=(0, 0, 35), mat="CastIron_Red")
    # Fixed heel jaw housing with knurled adjustment nut
    m.add_box(size=(16, 26, 20), center=(0, 4, 70), mat="CastIron_Red")
    m.add_cylinder(r0=8, r1=8, h=12, z0=65, segs=8, mat="Knurl_Nut", c0=(0, 10), c1=(0, 10))
    # Movable hook jaw with aggressive teeth
    m.add_box(size=(12, 12, 30), center=(0, 14, 82), mat="Steel_Jaw")
    m.add_box(size=(12, 24, 10), center=(0, 2, 94), mat="Steel_Jaw")
    return m

def build_tool_wrench_adjustable():
    m = Mesh("tool_wrench_adjustable")
    m.add_material("Chrome_Steel", 0.85, 0.88, 0.90)
    m.add_material("Knurl_Thumb", 0.70, 0.72, 0.74)
    # Handle with hang hole
    m.add_box(size=(8, 16, 65), center=(0, 0, 32), mat="Chrome_Steel")
    m.add_cylinder(r0=4, r1=4, h=10, z0=8, segs=8, mat="Knurl_Thumb") # Hang hole
    # Angled head with fixed jaw
    m.add_box(size=(12, 28, 26), center=(0, 6, 75), mat="Chrome_Steel")
    m.add_box(size=(10, 8, 16), center=(0, 18, 88), mat="Chrome_Steel") # Fixed jaw
    # Movable jaw
    m.add_box(size=(10, 8, 16), center=(0, 2, 88), mat="Chrome_Steel")
    return m

def build_tool_shears_pruning():
    m = Mesh("tool_shears_pruning")
    m.add_material("Grip_Red", 0.90, 0.18, 0.16)
    m.add_material("Blade_Steel", 0.85, 0.88, 0.90)
    m.add_material("Spring_Metal", 0.65, 0.66, 0.68)
    # Scissor handles
    m.add_cylinder(r0=5, r1=4.5, h=40, z0=0, segs=8, mat="Grip_Red", c0=(-12, 0), c1=(-4, 0))
    m.add_cylinder(r0=5, r1=4.5, h=40, z0=0, segs=8, mat="Grip_Red", c0=( 12, 0), c1=( 4, 0))
    # Central pivot bolt & volute spring
    m.add_cylinder(r0=5, r1=5, h=12, z0=40, segs=8, mat="Spring_Metal")
    # Curved bypass blade & hooked counter-blade
    m.add_box(size=(4, 18, 28), center=(-4, 6, 56), mat="Blade_Steel")
    m.add_box(size=(4, 18, 28), center=( 4, -4, 56), mat="Blade_Steel")
    return m

def build_tool_loppers_heavy():
    m = Mesh("tool_loppers_heavy")
    m.add_material("Arm_Steel", 0.78, 0.80, 0.82)
    m.add_material("Grip_Orange", 0.92, 0.44, 0.16)
    m.add_material("Jaw_Anvil", 0.35, 0.36, 0.38)
    # Long tubular handles
    m.add_cylinder(r0=5, r1=4.5, h=65, z0=0, segs=8, mat="Arm_Steel", c0=(-14, 0), c1=(-5, 0))
    m.add_cylinder(r0=5, r1=4.5, h=65, z0=0, segs=8, mat="Arm_Steel", c0=( 14, 0), c1=( 5, 0))
    m.add_cylinder(r0=6.5, r1=6.5, h=25, z0=0, segs=8, mat="Grip_Orange", c0=(-14, 0), c1=(-14, 0))
    m.add_cylinder(r0=6.5, r1=6.5, h=25, z0=0, segs=8, mat="Grip_Orange", c0=( 14, 0), c1=( 14, 0))
    # Compound action cutting jaws
    m.add_box(size=(8, 24, 26), center=(0, 0, 75), mat="Jaw_Anvil")
    return m

def build_tool_sickle_grass():
    m = Mesh("tool_sickle_grass")
    m.add_material("Wood_Turned", 0.74, 0.54, 0.34)
    m.add_material("Blade_Steel", 0.85, 0.88, 0.90)
    m.add_material("Collar_Iron", 0.25, 0.25, 0.28)
    # Turned wooden handle
    m.add_cylinder(r0=6, r1=5.5, h=35, z0=0, segs=8, mat="Wood_Turned")
    m.add_cylinder(r0=6.5, r1=6.5, h=8, z0=35, segs=8, mat="Collar_Iron")
    # Deep crescent curved cutting blade
    angles = [i * math.pi / 8.0 for i in range(9)]
    for i in range(8):
        a0 = angles[i]
        a1 = angles[i+1]
        r = 35
        p0 = Vec3(r * math.cos(a0), 0, 42 + r * math.sin(a0))
        p1 = Vec3(r * math.cos(a1), 0, 42 + r * math.sin(a1))
        p0_inner = Vec3((r-8) * math.cos(a0), 0, 42 + (r-8) * math.sin(a0))
        p1_inner = Vec3((r-8) * math.cos(a1), 0, 42 + (r-8) * math.sin(a1))
        m.add_quad(p0, p1, p1_inner, p0_inner, mat="Blade_Steel")
    return m

def build_tool_chainsaw_gas_16():
    m = Mesh("tool_chainsaw_gas_16")
    m.add_material("Case_Orange", 0.92, 0.42, 0.16)
    m.add_material("Handle_Black", 0.20, 0.20, 0.22)
    m.add_material("Bar_Steel", 0.80, 0.82, 0.85)
    m.add_material("Chain_Cutter", 0.30, 0.32, 0.34)
    # Powerhead body
    m.add_box(size=(42, 32, 28), center=(-15, 0, 18), mat="Case_Orange")
    # Top wrap-around handle
    m.add_cylinder(r0=3, r1=3, h=30, z0=25, segs=6, mat="Handle_Black", c0=(-15, -16), c1=(-15, 16))
    # 16" Guide bar
    m.add_box(size=(52, 2, 14), center=(32, 0, 18), mat="Bar_Steel")
    m.add_box(size=(54, 3, 16), center=(32, 0, 18), mat="Chain_Cutter")
    return m

def build_tool_chainsaw_gas_20():
    m = Mesh("tool_chainsaw_gas_20")
    m.add_material("Case_Orange", 0.92, 0.42, 0.16)
    m.add_material("Handle_Black", 0.20, 0.20, 0.22)
    m.add_material("Bar_Steel", 0.80, 0.82, 0.85)
    m.add_material("Chain_Cutter", 0.30, 0.32, 0.34)
    m.add_material("Spikes_Iron", 0.25, 0.26, 0.28)
    # Heavy pro logging powerhead
    m.add_box(size=(46, 36, 30), center=(-18, 0, 20), mat="Case_Orange")
    # Wrap-around full handlebar
    m.add_cylinder(r0=3.5, r1=3.5, h=34, z0=28, segs=6, mat="Handle_Black", c0=(-18, -18), c1=(-18, 18))
    # Heavy bucking spikes
    m.add_box(size=(6, 4, 18), center=(6, 0, 20), mat="Spikes_Iron")
    # Long 20" guide bar
    m.add_box(size=(64, 2, 14), center=(40, 0, 20), mat="Bar_Steel")
    m.add_box(size=(66, 3, 16), center=(40, 0, 20), mat="Chain_Cutter")
    return m

def build_tool_drill_cordless_20v():
    m = Mesh("tool_drill_cordless_20v")
    m.add_material("Tool_Yellow", 0.94, 0.78, 0.18)
    m.add_material("Grip_Rubber", 0.20, 0.20, 0.22)
    m.add_material("Chuck_Steel", 0.35, 0.36, 0.38)
    m.add_material("Battery_Black", 0.22, 0.22, 0.24)
    # Slide-on bottom battery pack
    m.add_box(size=(34, 26, 16), center=(-4, 0, 8), mat="Battery_Black")
    # Ergonomic pistol grip
    m.add_cylinder(r0=7, r1=6, h=38, z0=16, segs=8, mat="Grip_Rubber", c0=(-4, 0), c1=(4, 0))
    # Motor housing
    m.add_box(size=(46, 20, 24), center=(8, 0, 60), mat="Tool_Yellow")
    # Keyless ratcheting metal chuck
    m.add_cylinder(r0=9, r1=7, h=22, z0=60, segs=10, mat="Chuck_Steel", c0=(28, 0), c1=(50, 0))
    return m

def build_sprayer_backpack_4gal():
    m = Mesh("sprayer_backpack_4gal")
    m.add_material("Tank_White", 0.92, 0.93, 0.94)
    m.add_material("Base_Blue", 0.20, 0.48, 0.85)
    m.add_material("Hose_Black", 0.22, 0.22, 0.24)
    m.add_material("Wand_Brass", 0.86, 0.68, 0.24)
    # 4-Gallon contoured vertical tank
    m.add_box(size=(48, 32, 64), center=(0, 0, 36), mat="Tank_White")
    m.add_box(size=(52, 36, 8), center=(0, 0, 4), mat="Base_Blue") # Stand base
    # Large top fill cap
    m.add_cylinder(r0=14, r1=14, h=6, z0=68, segs=10, mat="Base_Blue")
    # Pumping lever arm
    m.add_cylinder(r0=3, r1=3, h=45, z0=20, segs=6, mat="Base_Blue", c0=(-24, 0), c1=(-24, -30))
    # Spray hose & brass wand
    m.add_cylinder(r0=3, r1=3, h=35, z0=10, segs=6, mat="Hose_Black", c0=(24, 0), c1=(36, 15))
    m.add_cylinder(r0=2.5, r1=2.5, h=60, z0=30, segs=6, mat="Wand_Brass", c0=(36, 15), c1=(36, 15))
    return m

TOOLS_BUILDERS = [
    ("tool_trowel_hand", build_tool_trowel_hand, "tools", "hand_tools"),
    ("tool_shovel_trenching", build_tool_shovel_trenching, "tools", "hand_tools"),
    ("tool_shovel_round_point", build_tool_shovel_round_point, "tools", "hand_tools"),
    ("tool_shovel_scoop_flat", build_tool_shovel_scoop_flat, "tools", "hand_tools"),
    ("tool_hatchet_camp", build_tool_hatchet_camp, "tools", "hand_tools"),
    ("tool_axe_felling", build_tool_axe_felling, "tools", "hand_tools"),
    ("tool_maul_splitting", build_tool_maul_splitting, "tools", "hand_tools"),
    ("tool_hammer_claw", build_tool_hammer_claw, "tools", "hand_tools"),
    ("tool_hammer_club", build_tool_hammer_club, "tools", "hand_tools"),
    ("tool_wrench_pipe", build_tool_wrench_pipe, "tools", "hand_tools"),
    ("tool_wrench_adjustable", build_tool_wrench_adjustable, "tools", "hand_tools"),
    ("tool_shears_pruning", build_tool_shears_pruning, "tools", "hand_tools"),
    ("tool_loppers_heavy", build_tool_loppers_heavy, "tools", "hand_tools"),
    ("tool_sickle_grass", build_tool_sickle_grass, "tools", "hand_tools"),
    ("tool_chainsaw_gas_16", build_tool_chainsaw_gas_16, "tools", "equipment"),
    ("tool_chainsaw_gas_20", build_tool_chainsaw_gas_20, "tools", "equipment"),
    ("tool_drill_cordless_20v", build_tool_drill_cordless_20v, "tools", "equipment"),
    ("sprayer_backpack_4gal", build_sprayer_backpack_4gal, "tools", "equipment"),
]

