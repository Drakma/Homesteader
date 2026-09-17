#!/usr/bin/env python3
"""
Homesteader 3D Item Builders: Building Materials & Hardware System
Covers framing lumber, plywood sheets, steel roofing, shingles, concrete, rebar, and fasteners.
"""

import math
from generate_item_assets import Vec3, Mesh

def build_lumber_stud_2x4():
    m = Mesh("lumber_stud_2x4")
    m.add_material("Pine_Light", 0.88, 0.72, 0.48)
    m.add_material("Pine_End", 0.76, 0.60, 0.38)
    # Stack of three 2x4 studs
    for z in [6, 18, 30]:
        m.add_box(size=(22, 88, 10), center=(0, 0, z), mat="Pine_Light")
        m.add_box(size=(22, 2, 10), center=(0, 44, z), mat="Pine_End")
    return m

def build_lumber_post_4x4():
    m = Mesh("lumber_post_4x4")
    m.add_material("Treated_Green", 0.62, 0.68, 0.46) # Olive-green pressure treated wood
    m.add_material("Wood_End", 0.52, 0.58, 0.36)
    # Heavy 4x4 post
    m.add_box(size=(28, 28, 92), center=(0, 0, 46), mat="Treated_Green")
    m.add_box(size=(28, 28, 2), center=(0, 0, 92), mat="Wood_End")
    return m

def build_lumber_joist_2x8():
    m = Mesh("lumber_joist_2x8")
    m.add_material("Fir_Wood", 0.82, 0.64, 0.42)
    m.add_material("Wood_End", 0.70, 0.52, 0.32)
    # Wide 2x8 structural joist beam
    m.add_box(size=(14, 92, 42), center=(0, 0, 21), mat="Fir_Wood")
    m.add_box(size=(14, 2, 42), center=(0, 46, 21), mat="Wood_End")
    return m

def build_sheet_plywood_cdx():
    m = Mesh("sheet_plywood_cdx")
    m.add_material("Plywood_Face", 0.84, 0.68, 0.44)
    m.add_material("Layer_Edge", 0.68, 0.50, 0.30)
    m.add_material("CDX_Stamp", 0.20, 0.20, 0.20)
    # Stack of 3 plywood sheets
    m.add_box(size=(58, 86, 12), center=(0, 0, 6), mat="Plywood_Face")
    m.add_box(size=(58, 86, 2), center=(0, 0, 12), mat="Plywood_Face")
    # Black CDX APA grade stamp
    m.add_box(size=(14, 22, 1), center=(10, 10, 13), mat="CDX_Stamp")
    return m

def build_roofing_steel_corrugated():
    m = Mesh("roofing_steel_corrugated")
    m.add_material("Galv_Steel", 0.82, 0.84, 0.86)
    m.add_material("Steel_Shadow", 0.68, 0.70, 0.72)
    # Corrugated sheet with wave folds
    for i in range(5):
        x = -32 + i * 16
        m.add_box(size=(14, 88, 4), center=(x, 0, 12), mat="Galv_Steel")
        m.add_box(size=(4, 88, 8), center=(x+7, 0, 8), mat="Steel_Shadow")
    return m

def build_roofing_shingles_bundle():
    m = Mesh("roofing_shingles_bundle")
    m.add_material("Asphalt_Slate", 0.32, 0.34, 0.36)
    m.add_material("Granule_Speck", 0.42, 0.44, 0.46)
    m.add_material("Band_Strap", 0.88, 0.78, 0.22)
    # Heavy bundle of asphalt shingles
    m.add_box(size=(48, 82, 24), center=(0, 0, 12), mat="Asphalt_Slate")
    m.add_box(size=(48, 82, 2), center=(0, 0, 24), mat="Granule_Speck")
    # Yellow paper binding band strap
    m.add_box(size=(50, 14, 26), center=(0, 0, 12), mat="Band_Strap")
    return m

def build_masonry_concrete_bag():
    m = Mesh("masonry_concrete_bag")
    m.add_material("Kraft_Paper", 0.75, 0.60, 0.40)
    m.add_material("Logo_Yellow", 0.94, 0.78, 0.18)
    m.add_material("Fold_Dark", 0.55, 0.42, 0.28)
    # 80lb cement sack with pillow bulge
    m.add_box(size=(54, 42, 24), center=(0, 0, 12), mat="Kraft_Paper")
    m.add_foliage_lobe(radius=22, center=(0, 0, 12), mat="Kraft_Paper")
    # Yellow manufacturer brand label
    m.add_box(size=(38, 28, 2), center=(0, 0, 24.5), mat="Logo_Yellow")
    # Valve sack sewn end
    m.add_box(size=(56, 4, 18), center=(0, 21, 10), mat="Fold_Dark")
    return m

def build_masonry_cinder_block():
    m = Mesh("masonry_cinder_block")
    m.add_material("CMU_Gray", 0.68, 0.68, 0.70)
    m.add_material("Void_Dark", 0.25, 0.25, 0.26)
    # Standard 8x8x16 concrete block
    m.add_box(size=(46, 82, 42), center=(0, 0, 21), mat="CMU_Gray")
    # Dual hollow structural voids on top
    m.add_box(size=(30, 24, 6), center=(0, -22, 40), mat="Void_Dark")
    m.add_box(size=(30, 24, 6), center=(0,  22, 40), mat="Void_Dark")
    return m

def build_masonry_brick_red():
    m = Mesh("masonry_brick_red")
    m.add_material("Clay_Red", 0.78, 0.32, 0.22)
    m.add_material("Brick_Dark", 0.62, 0.24, 0.16)
    m.add_material("Hole_Void", 0.35, 0.16, 0.12)
    # Standard red clay construction brick
    m.add_box(size=(42, 78, 26), center=(0, 0, 13), mat="Clay_Red")
    # 3 Core holes through brick
    for y in [-22, 0, 22]:
        m.add_cylinder(r0=6, r1=6, h=6, z0=22, segs=8, mat="Hole_Void", c0=(0, y), c1=(0, y))
    return m

def build_rebar_steel_bundle():
    m = Mesh("rebar_steel_bundle")
    m.add_material("Rebar_Rust", 0.52, 0.42, 0.36)
    m.add_material("Rebar_Steel", 0.42, 0.44, 0.46)
    m.add_material("Wire_Tie", 0.78, 0.68, 0.35)
    # Bundle of 6 #4 rebar stakes with rib rings
    positions = [(-12, -7), (0, -7), (12, -7), (-6, 7), (6, 7)]
    for px, py in positions:
        m.add_cylinder(r0=4.5, r1=4.5, h=92, z0=0, segs=8, mat="Rebar_Steel", c0=(px,py), c1=(px,py))
        for z in range(10, 90, 15):
            m.add_torus(r_major=5.2, r_minor=1.2, segs_major=8, segs_minor=4, z0=z, mat="Rebar_Rust", c=(px,py))
    # Galvanized wire ties wrapping bundle
    for z in [22, 68]:
        m.add_box(size=(34, 26, 4), center=(0, 0, z), mat="Wire_Tie")
    return m

def build_hardware_framing_nails():
    m = Mesh("hardware_framing_nails")
    m.add_material("Box_Cardboard", 0.80, 0.64, 0.42)
    m.add_material("Steel_Nail", 0.82, 0.84, 0.86)
    m.add_material("Nail_Head", 0.72, 0.74, 0.76)
    # Open cardboard nail box
    m.add_box(size=(46, 46, 32), center=(0, 0, 16), mat="Box_Cardboard")
    # Nails spilling and bundled inside
    for i in range(8):
        a = i * math.pi / 4.0
        nx = 14 * math.cos(a)
        ny = 14 * math.sin(a)
        m.add_cylinder(r0=2, r1=2, h=30, z0=20, segs=6, mat="Steel_Nail", c0=(nx, ny), c1=(nx*1.4, ny*1.4))
        m.add_cylinder(r0=4, r1=4, h=2, z0=48, segs=8, mat="Nail_Head", c0=(nx*1.4, ny*1.4), c1=(nx*1.4, ny*1.4))
    return m

def build_hardware_deck_screws():
    m = Mesh("hardware_deck_screws")
    m.add_material("Tub_Green", 0.22, 0.58, 0.32) # Star-drive screw green plastic container
    m.add_material("Screw_Coated", 0.44, 0.52, 0.42) # Ceramic exterior coating
    m.add_material("Drive_Bit", 0.78, 0.80, 0.82)
    # Clear green plastic tub
    m.add_box(size=(44, 44, 38), center=(0, 0, 19), mat="Tub_Green")
    m.add_cylinder(r0=20, r1=20, h=4, z0=38, segs=12, mat="Tub_Green")
    # Included T25 star drive bit on top
    m.add_cylinder(r0=3, r1=3, h=22, z0=40, segs=6, mat="Drive_Bit", c0=(-8, 0), c1=(8, 0))
    # Screws inside
    m.add_cylinder(r0=2.5, r1=2.5, h=28, z0=20, segs=6, mat="Screw_Coated", c0=(6, 6), c1=(12, 12))
    return m

def build_hardware_lag_bolts():
    m = Mesh("hardware_lag_bolts")
    m.add_material("Box_Gray", 0.65, 0.66, 0.68)
    m.add_material("Bolt_Galv", 0.82, 0.84, 0.86)
    m.add_material("Washer_Steel", 0.75, 0.78, 0.80)
    # Box
    m.add_box(size=(46, 38, 28), center=(0, 0, 14), mat="Box_Gray")
    # Heavy 1/2" hex head lag bolt lying across box
    m.add_cylinder(r0=5, r1=5, h=55, z0=28, segs=8, mat="Bolt_Galv", c0=(-20, 0), c1=(25, 0))
    m.add_cylinder(r0=10, r1=10, h=8, z0=28, segs=6, mat="Bolt_Galv", c0=(-24, 0), c1=(-18, 0)) # Hex head
    # Heavy flat washer
    m.add_cylinder(r0=12, r1=12, h=3, z0=28, segs=10, mat="Washer_Steel", c0=(-16, 0), c1=(-14, 0))
    return m

def build_hardware_hurricane_ties():
    m = Mesh("hardware_hurricane_ties")
    m.add_material("Steel_Stamped", 0.85, 0.86, 0.88)
    m.add_material("Hole_Punch", 0.30, 0.32, 0.34)
    # Pair of stamped steel hurricane rafter brackets
    for x in [-14, 14]:
        # Vertical flange
        m.add_box(size=(3, 26, 48), center=(x, 0, 24), mat="Steel_Stamped")
        # Horizontal seat flange
        m.add_box(size=(18, 26, 3), center=(x+8, 0, 2), mat="Steel_Stamped")
        # Nail holes
        m.add_box(size=(4, 6, 6), center=(x, 0, 36), mat="Hole_Punch")
        m.add_box(size=(4, 6, 6), center=(x, 0, 16), mat="Hole_Punch")
    return m

def build_hardware_gate_hinges():
    m = Mesh("hardware_gate_hinges")
    m.add_material("Iron_Forged", 0.22, 0.22, 0.24)
    m.add_material("Pin_Steel", 0.35, 0.36, 0.38)
    # Heavy strap T-hinge
    # Rectangular post plate
    m.add_box(size=(6, 36, 44), center=(-18, 0, 22), mat="Iron_Forged")
    # Central barrel knuckle pin
    m.add_cylinder(r0=5, r1=5, h=48, z0=0, segs=8, mat="Pin_Steel", c0=(-14, 0), c1=(-14, 0))
    # Tapered heavy strap leaf extending onto gate
    m.add_box(size=(48, 14, 4), center=(12, 0, 22), mat="Iron_Forged")
    m.add_cone(r=12, h=18, z0=22, segs=6, mat="Iron_Forged", c=(36, 0))
    return m

BUILDING_BUILDERS = [
    ("lumber_stud_2x4", build_lumber_stud_2x4, "building", "materials"),
    ("lumber_post_4x4", build_lumber_post_4x4, "building", "materials"),
    ("lumber_joist_2x8", build_lumber_joist_2x8, "building", "materials"),
    ("sheet_plywood_cdx", build_sheet_plywood_cdx, "building", "materials"),
    ("roofing_steel_corrugated", build_roofing_steel_corrugated, "building", "materials"),
    ("roofing_shingles_bundle", build_roofing_shingles_bundle, "building", "materials"),
    ("masonry_concrete_bag", build_masonry_concrete_bag, "building", "materials"),
    ("masonry_cinder_block", build_masonry_cinder_block, "building", "materials"),
    ("masonry_brick_red", build_masonry_brick_red, "building", "materials"),
    ("rebar_steel_bundle", build_rebar_steel_bundle, "building", "materials"),
    ("hardware_framing_nails", build_hardware_framing_nails, "building", "hardware"),
    ("hardware_deck_screws", build_hardware_deck_screws, "building", "hardware"),
    ("hardware_lag_bolts", build_hardware_lag_bolts, "building", "hardware"),
    ("hardware_hurricane_ties", build_hardware_hurricane_ties, "building", "hardware"),
    ("hardware_gate_hinges", build_hardware_gate_hinges, "building", "hardware"),
]

