#!/usr/bin/env python3
"""
Homesteader 3D Item Builders: Fishing Gear & Logging Operations System
Covers fishing rods, reels, tackle boxes, nets, felling wedges, cant hooks, skidding tongs, and safety gear.
"""

import math
from generate_item_assets import Vec3, Mesh

def build_rod_spincast_combo():
    m = Mesh("rod_spincast_combo")
    m.add_material("Blank_Graphite", 0.25, 0.28, 0.32)
    m.add_material("Grip_Cork", 0.86, 0.72, 0.48)
    m.add_material("Reel_Silver", 0.78, 0.80, 0.82)
    m.add_material("Guides_Steel", 0.70, 0.72, 0.74)
    # Cork handle
    m.add_cylinder(r0=5, r1=4.5, h=28, z0=0, segs=8, mat="Grip_Cork")
    # Spin-cast push-button closed-face reel
    m.add_cylinder(r0=12, r1=10, h=16, z0=22, segs=10, mat="Reel_Silver", c0=(0, 10), c1=(0, 10))
    # Tapered graphite rod blank
    m.add_cylinder(r0=4, r1=1.5, h=72, z0=28, segs=8, mat="Blank_Graphite")
    # Line guides
    for z in [48, 68, 88]:
        m.add_torus(r_major=4, r_minor=1, segs_major=8, segs_minor=4, z0=z, mat="Guides_Steel", c=(0, 4))
    return m

def build_rod_fly_fishing():
    m = Mesh("rod_fly_fishing")
    m.add_material("Blank_Olive", 0.30, 0.38, 0.28)
    m.add_material("Grip_Cork", 0.88, 0.74, 0.50)
    m.add_material("Fly_Reel", 0.22, 0.24, 0.26)
    m.add_material("Fly_Line", 0.94, 0.82, 0.20) # Bright chartreuse weight-forward line
    # Bottom machined aluminum fly reel
    m.add_torus(r_major=14, r_minor=4, segs_major=12, segs_minor=6, z0=6, mat="Fly_Reel", c=(0, -8))
    m.add_torus(r_major=11, r_minor=3, segs_major=10, segs_minor=4, z0=6, mat="Fly_Line", c=(0, -8))
    # Reverse half-wells cork grip
    m.add_cylinder(r0=5, r1=4.5, h=26, z0=10, segs=8, mat="Grip_Cork")
    # Slender 9ft fly rod blank
    m.add_cylinder(r0=3.5, r1=1.0, h=66, z0=36, segs=6, mat="Blank_Olive")
    return m

def build_rod_heavy_trolling():
    m = Mesh("rod_heavy_trolling")
    m.add_material("Blank_Heavy", 0.20, 0.20, 0.22)
    m.add_material("EVA_Foam", 0.18, 0.18, 0.20)
    m.add_material("Gold_Reel", 0.86, 0.70, 0.25)
    m.add_material("Roller_Guides", 0.78, 0.80, 0.82)
    # Heavy EVA foam foregrip and rear grip
    m.add_cylinder(r0=7, r1=7, h=18, z0=0, segs=8, mat="EVA_Foam")
    m.add_cylinder(r0=7, r1=7, h=16, z0=30, segs=8, mat="EVA_Foam")
    # Heavy lever-drag offshore trolling reel
    m.add_cylinder(r0=15, r1=15, h=18, z0=18, segs=10, mat="Gold_Reel", c0=(0, 12), c1=(0, 12))
    # Stout thick rod blank
    m.add_cylinder(r0=6, r1=3.5, h=62, z0=38, segs=8, mat="Blank_Heavy")
    # Heavy roller line guide
    m.add_box(size=(8, 10, 8), center=(0, 8, 92), mat="Roller_Guides")
    return m

def build_box_tackle_3tray():
    m = Mesh("box_tackle_3tray")
    m.add_material("Box_Green", 0.22, 0.48, 0.30)
    m.add_material("Lid_Beige", 0.88, 0.84, 0.76)
    m.add_material("Brass_Latch", 0.86, 0.68, 0.24)
    # Lower cantilever box base
    m.add_box(size=(72, 44, 26), center=(0, 0, 13), mat="Box_Green")
    # Hinged top lid
    m.add_box(size=(74, 46, 18), center=(0, 0, 35), mat="Lid_Beige")
    # Top carry handle
    m.add_cylinder(r0=2.5, r1=2.5, h=26, z0=44, segs=6, mat="Box_Green", c0=(-13, 0), c1=(13, 0))
    # Brass toggle latch
    m.add_box(size=(10, 3, 14), center=(0, 23, 24), mat="Brass_Latch")
    return m

def build_spool_fishing_line_braid():
    m = Mesh("spool_fishing_line_braid")
    m.add_material("Plastic_Clear", 0.85, 0.88, 0.92)
    m.add_material("Line_HiVis", 0.25, 0.88, 0.45) # Neon chartreuse braid
    m.add_material("Label_Round", 0.92, 0.92, 0.94)
    # Retail spool
    m.add_spool(r_flange=36, r_core=18, h=24, mat_flange="Plastic_Clear", mat_wire="Line_HiVis", z0=0)
    m.add_cylinder(r0=16, r1=16, h=2, z0=24, segs=10, mat="Label_Round")
    return m

def build_box_lures_organizer():
    m = Mesh("box_lures_organizer")
    m.add_material("Box_Clear", 0.82, 0.86, 0.90)
    m.add_material("Lure_Gold", 0.88, 0.72, 0.25)
    m.add_material("Lure_Silver", 0.85, 0.86, 0.88)
    m.add_material("Lure_Red", 0.88, 0.20, 0.16)
    # Transparent divided utility lure tray
    m.add_box(size=(74, 48, 16), center=(0, 0, 8), mat="Box_Clear")
    # Spoons and spinners visible inside compartments
    m.add_cylinder(r0=4, r1=2, h=18, z0=5, segs=6, mat="Lure_Gold", c0=(-20, -12), c1=(-20, 12))
    m.add_cylinder(r0=4, r1=2, h=18, z0=5, segs=6, mat="Lure_Silver", c0=(0, -12), c1=(0, 12))
    m.add_cylinder(r0=4, r1=2, h=18, z0=5, segs=6, mat="Lure_Red", c0=(20, -12), c1=(20, 12))
    return m

def build_bobbers_clip_pack():
    m = Mesh("bobbers_clip_pack")
    m.add_material("Bobber_Red", 0.90, 0.18, 0.16)
    m.add_material("Bobber_White", 0.96, 0.96, 0.96)
    m.add_material("Hook_Brass", 0.86, 0.68, 0.24)
    # Trio of classic push-button red/white sphere floats
    positions = [(-16, -10, 18), (16, -8, 20), (0, 14, 22)]
    for bx, by, bz in positions:
        m.add_foliage_lobe(radius=15, center=(bx, by, bz), mat="Bobber_Red")
        m.add_cylinder(r0=15, r1=15, h=14, z0=bz-14, segs=10, mat="Bobber_White", c0=(bx, by), c1=(bx, by))
        m.add_cylinder(r0=2, r1=2, h=30, z0=bz-15, segs=6, mat="Hook_Brass", c0=(bx, by), c1=(bx, by))
    return m

def build_sinkers_lead_split_shot():
    m = Mesh("sinkers_lead_split_shot")
    m.add_material("Dial_Yellow", 0.92, 0.78, 0.18)
    m.add_material("Lead_Shot", 0.45, 0.46, 0.48)
    # Rotating selector dial box
    m.add_cylinder(r0=34, r1=34, h=16, z0=0, segs=14, mat="Dial_Yellow")
    # Split shot spheres inside selector window
    m.add_foliage_lobe(radius=5, center=(14, 14, 12), mat="Lead_Shot")
    m.add_foliage_lobe(radius=4, center=(18, 6, 12), mat="Lead_Shot")
    m.add_foliage_lobe(radius=6, center=(10, 20, 12), mat="Lead_Shot")
    return m

def build_net_landing_telescopic():
    m = Mesh("net_landing_telescopic")
    m.add_material("Alum_Handle", 0.82, 0.84, 0.86)
    m.add_material("Grip_Foam", 0.20, 0.20, 0.22)
    m.add_material("Net_Rubber", 0.18, 0.18, 0.20)
    # Telescoping handle
    m.add_cylinder(r0=4, r1=4, h=50, z0=0, segs=6, mat="Alum_Handle")
    m.add_cylinder(r0=5, r1=5, h=22, z0=0, segs=6, mat="Grip_Foam")
    # Teardrop landing net hoop
    m.add_torus(r_major=28, r_minor=3.5, segs_major=14, segs_minor=6, z0=72, mat="Alum_Handle")
    # Hanging soft mesh bag
    m.add_cylinder(r0=26, r1=18, h=25, z0=48, segs=12, mat="Net_Rubber")
    return m

def build_basket_fish_wire():
    m = Mesh("basket_fish_wire")
    m.add_material("Galv_Mesh", 0.76, 0.78, 0.80)
    m.add_material("Ring_Steel", 0.65, 0.68, 0.70)
    m.add_material("Door_Spring", 0.86, 0.22, 0.18)
    # Cylindrical collapsible wire mesh basket
    m.add_cylinder(r0=30, r1=30, h=65, z0=0, segs=14, mat="Galv_Mesh")
    # Structural hoop rings
    for z in [0, 22, 44, 65]:
        m.add_torus(r_major=30.5, r_minor=2, segs_major=14, segs_minor=4, z0=z, mat="Ring_Steel")
    # Spring trapdoor lid on top
    m.add_cylinder(r0=14, r1=14, h=2, z0=65, segs=8, mat="Door_Spring")
    return m

def build_wedge_felling_abs_pack():
    m = Mesh("wedge_felling_abs_pack")
    m.add_material("ABS_Orange", 0.94, 0.44, 0.15)
    m.add_material("Cleat_Dark", 0.82, 0.35, 0.12)
    # Stack of three high-impact logging wedges
    for i in range(3):
        z = i * 14
        m.add_box(size=(22, 45, 10), center=(0, 0, z+5), mat="ABS_Orange")
        m.add_cone(r=11, h=20, z0=z, segs=4, mat="ABS_Orange", c=(0, 22))
        # Non-slip gripping barbs
        m.add_box(size=(18, 4, 3), center=(0, 0, z+10), mat="Cleat_Dark")
        m.add_box(size=(18, 4, 3), center=(0, 15, z+10), mat="Cleat_Dark")
    return m

def build_tool_cant_hook_peavey():
    m = Mesh("tool_cant_hook_peavey")
    m.add_material("Ash_Wood", 0.80, 0.64, 0.42)
    m.add_material("Forged_Iron", 0.25, 0.26, 0.28)
    m.add_material("Hook_Duckbill", 0.35, 0.36, 0.38)
    # 48" Heavy wooden lever handle
    m.add_cylinder(r0=6, r1=5, h=88, z0=0, segs=8, mat="Ash_Wood")
    # Cast iron socket clasp & duckbill toe
    m.add_cylinder(r0=8, r1=7, h=25, z0=0, segs=8, mat="Forged_Iron")
    # Large pivoting swinging log dog hook
    m.add_torus(r_major=18, r_minor=4, segs_major=10, segs_minor=4, z0=22, mat="Hook_Duckbill", c=(14, 0))
    return m

def build_tongs_skidding_logging():
    m = Mesh("tongs_skidding_logging")
    m.add_material("Steel_Forged", 0.32, 0.34, 0.36)
    m.add_material("Point_Sharp", 0.85, 0.88, 0.90)
    m.add_material("Swivel_Ring", 0.72, 0.74, 0.76)
    # Top hoist swivel shackle ring
    m.add_torus(r_major=12, r_minor=3, segs_major=10, segs_minor=4, z0=78, mat="Swivel_Ring")
    # Scissor crossing heavy forged arms
    m.add_cylinder(r0=5, r1=4, h=55, z0=22, segs=6, mat="Steel_Forged", c0=(0, 0), c1=(-26, 0))
    m.add_cylinder(r0=5, r1=4, h=55, z0=22, segs=6, mat="Steel_Forged", c0=(0, 0), c1=( 26, 0))
    # Sharp gripping log grab points
    m.add_cone(r=5, h=14, z0=8, segs=4, mat="Point_Sharp", c=(-26, 0))
    m.add_cone(r=5, h=14, z0=8, segs=4, mat="Point_Sharp", c=( 26, 0))
    return m

def build_chain_choker_logging():
    m = Mesh("chain_choker_logging")
    m.add_material("Chain_Gold", 0.78, 0.62, 0.28) # Grade 70 transport gold chromate
    m.add_material("Hook_Clevis", 0.88, 0.22, 0.18) # Red forged grab hook
    # Heavy coiled logging chain links
    m.add_torus(r_major=40, r_minor=7, segs_major=14, segs_minor=6, z0=7, mat="Chain_Gold")
    m.add_torus(r_major=32, r_minor=7, segs_major=14, segs_minor=6, z0=21, mat="Chain_Gold")
    # Forged red clevis choker hook
    m.add_torus(r_major=15, r_minor=5, segs_major=10, segs_minor=6, z0=35, mat="Hook_Clevis", c=(30, 0))
    return m

def build_kit_chainsaw_file_pouch():
    m = Mesh("kit_chainsaw_file_pouch")
    m.add_material("Pouch_Orange", 0.92, 0.44, 0.16)
    m.add_material("Handle_Wood", 0.78, 0.60, 0.40)
    m.add_material("File_Steel", 0.82, 0.84, 0.86)
    # Roll-up tool pouch
    m.add_box(size=(64, 42, 14), center=(0, 0, 7), mat="Pouch_Orange")
    # Round files protruding with turned wooden handles
    for x in [-18, 0, 18]:
        m.add_cylinder(r0=4, r1=4, h=22, z0=7, segs=6, mat="Handle_Wood", c0=(x, -15), c1=(x, -30))
        m.add_cylinder(r0=2.5, r1=2.5, h=30, z0=7, segs=6, mat="File_Steel", c0=(x, 0), c1=(x, 30))
    return m

def build_helmet_logging_safety():
    m = Mesh("helmet_logging_safety")
    m.add_material("Hardhat_Orange", 0.94, 0.44, 0.15)
    m.add_material("Visor_Mesh", 0.25, 0.25, 0.28)
    m.add_material("Earmuffs_Black", 0.18, 0.18, 0.20)
    # Hard hat shell dome with brim
    m.add_foliage_lobe(radius=28, center=(0, 0, 36), mat="Hardhat_Orange")
    m.add_cylinder(r0=34, r1=34, h=4, z0=24, segs=12, mat="Hardhat_Orange")
    # Protective wire mesh face shield
    m.add_cylinder(r0=30, r1=28, h=28, z0=2, segs=10, mat="Visor_Mesh", c0=(0, 10), c1=(0, 10))
    # Integrated hearing protection earmuffs
    m.add_foliage_lobe(radius=10, center=(-30, 0, 22), mat="Earmuffs_Black")
    m.add_foliage_lobe(radius=10, center=( 30, 0, 22), mat="Earmuffs_Black")
    return m

def build_bundle_firewood_wrapped():
    m = Mesh("bundle_firewood_wrapped")
    m.add_material("Bark_Birch", 0.92, 0.90, 0.85)
    m.add_material("Wood_Heart", 0.75, 0.58, 0.38)
    m.add_material("Twine_Jute", 0.82, 0.72, 0.48)
    # Bundle of 6 split birch firewood logs
    positions = [(-16, -10), (0, -12), (16, -10), (-12, 10), (12, 10), (0, 6)]
    for px, py in positions:
        m.add_cylinder(r0=10, r1=10, h=75, z0=0, segs=8, mat="Bark_Birch", c0=(px, py), c1=(px, py))
        m.add_cylinder(r0=9, r1=9, h=2, z0=75, segs=8, mat="Wood_Heart", c0=(px, py), c1=(px, py))
    # Rustic jute twine wraps
    m.add_box(size=(52, 42, 4), center=(0, 0, 20), mat="Twine_Jute")
    m.add_box(size=(52, 42, 4), center=(0, 0, 55), mat="Twine_Jute")
    return m

def build_wedge_splitting_diamond():
    m = Mesh("wedge_splitting_diamond")
    m.add_material("Steel_DropForged", 0.32, 0.34, 0.36)
    m.add_material("Striking_Face", 0.48, 0.50, 0.52)
    # 4-directional diamond cross splitting wedge
    # Striking cap
    m.add_box(size=(28, 28, 14), center=(0, 0, 60), mat="Striking_Face")
    # 4-way tapered splitting body
    m.add_cone(r=20, h=60, z0=0, segs=4, mat="Steel_DropForged")
    return m

FISHING_LOGGING_BUILDERS = [
    ("rod_spincast_combo", build_rod_spincast_combo, "fishing", "tackle"),
    ("rod_fly_fishing", build_rod_fly_fishing, "fishing", "tackle"),
    ("rod_heavy_trolling", build_rod_heavy_trolling, "fishing", "tackle"),
    ("box_tackle_3tray", build_box_tackle_3tray, "fishing", "equipment"),
    ("spool_fishing_line_braid", build_spool_fishing_line_braid, "fishing", "tackle"),
    ("box_lures_organizer", build_box_lures_organizer, "fishing", "tackle"),
    ("bobbers_clip_pack", build_bobbers_clip_pack, "fishing", "tackle"),
    ("sinkers_lead_split_shot", build_sinkers_lead_split_shot, "fishing", "tackle"),
    ("net_landing_telescopic", build_net_landing_telescopic, "fishing", "equipment"),
    ("basket_fish_wire", build_basket_fish_wire, "fishing", "equipment"),
    ("wedge_felling_abs_pack", build_wedge_felling_abs_pack, "logging", "wood"),
    ("tool_cant_hook_peavey", build_tool_cant_hook_peavey, "logging", "wood"),
    ("tongs_skidding_logging", build_tongs_skidding_logging, "logging", "wood"),
    ("chain_choker_logging", build_chain_choker_logging, "logging", "wood"),
    ("kit_chainsaw_file_pouch", build_kit_chainsaw_file_pouch, "logging", "wood"),
    ("helmet_logging_safety", build_helmet_logging_safety, "logging", "wood"),
    ("bundle_firewood_wrapped", build_bundle_firewood_wrapped, "logging", "fuel"),
    ("wedge_splitting_diamond", build_wedge_splitting_diamond, "logging", "wood"),
]

