#!/usr/bin/env python3
"""
Homesteader 3D Item Builders: Farming & Ranching Utilities & Attachments System
Covers fencing posts, wire spools, solar fence chargers, feed pans, stock tanks, float valves, and irrigation timers.
"""

import math
from generate_item_assets import Vec3, Mesh

def build_post_t_stake_metal():
    m = Mesh("post_t_stake_metal")
    m.add_material("Post_Green", 0.20, 0.44, 0.24)
    m.add_material("Tip_White", 0.94, 0.94, 0.95)
    m.add_material("Anchor_Plate", 0.18, 0.38, 0.20)
    # T-shaped vertical studded post
    m.add_box(size=(6, 12, 92), center=(0, 0, 46), mat="Post_Green")
    m.add_box(size=(14, 3, 92), center=(0, 4, 46), mat="Post_Green")
    # Painted white top tip (standard safety marking)
    m.add_box(size=(15, 13, 14), center=(0, 2, 85), mat="Tip_White")
    # Bottom spade anchor stabilization plate
    m.add_box(size=(28, 2, 22), center=(0, 0, 18), mat="Anchor_Plate")
    return m

def build_post_wood_round_6inch():
    m = Mesh("post_wood_round_6inch")
    m.add_material("Treated_Pine", 0.68, 0.52, 0.34)
    m.add_material("End_Grain", 0.58, 0.42, 0.26)
    # Heavy 6" round timber corner post
    m.add_cylinder(r0=18, r1=18, h=92, z0=0, segs=12, mat="Treated_Pine")
    m.add_cylinder(r0=18, r1=18, h=2, z0=92, segs=12, mat="End_Grain")
    return m

def build_spool_wire_woven_field():
    m = Mesh("spool_wire_woven_field")
    m.add_material("Galv_Mesh", 0.78, 0.80, 0.82)
    m.add_material("Band_Red", 0.88, 0.20, 0.16)
    # Tightly rolled field fence roll
    m.add_cylinder(r0=24, r1=24, h=88, z0=0, segs=14, mat="Galv_Mesh")
    # Red binding packaging tape bands
    m.add_cylinder(r0=24.5, r1=24.5, h=6, z0=20, segs=14, mat="Band_Red")
    m.add_cylinder(r0=24.5, r1=24.5, h=6, z0=68, segs=14, mat="Band_Red")
    return m

def build_spool_wire_barbed_4pt():
    m = Mesh("spool_wire_barbed_4pt")
    m.add_material("Galv_Wire", 0.75, 0.78, 0.80)
    m.add_material("Barb_Spur", 0.85, 0.86, 0.88)
    m.add_material("Spool_Wood", 0.72, 0.55, 0.36)
    # Wooden core spool with wire bundle
    m.add_spool(r_flange=38, r_core=22, h=42, mat_flange="Spool_Wood", mat_wire="Galv_Wire", z0=0)
    # Protruding sharp 4-point barbs
    for a in [0.4, 1.8, 3.2, 4.6]:
        bx = 36 * math.cos(a)
        by = 36 * math.sin(a)
        m.add_cone(r=3, h=6, z0=20, segs=4, mat="Barb_Spur", c=(bx, by))
    return m

def build_spool_electric_polywire():
    m = Mesh("spool_electric_polywire")
    m.add_material("Poly_Yellow", 0.94, 0.80, 0.18)
    m.add_material("Reel_Plastic", 0.20, 0.20, 0.22)
    m.add_material("Handle_Crank", 0.88, 0.18, 0.16)
    # Yellow braided wire spool with crank reel
    m.add_spool(r_flange=40, r_core=20, h=38, mat_flange="Reel_Plastic", mat_wire="Poly_Yellow", z0=10)
    # Carry handle & crank
    m.add_box(size=(8, 12, 35), center=(-28, 0, 48), mat="Reel_Plastic")
    m.add_cylinder(r0=3, r1=3, h=15, z0=29, segs=6, mat="Handle_Crank", c0=(0, 20), c1=(0, 35))
    return m

def build_insulators_tpost_pack():
    m = Mesh("insulators_tpost_pack")
    m.add_material("Poly_Yellow", 0.94, 0.82, 0.18)
    m.add_material("Bag_Clear", 0.80, 0.88, 0.92)
    # Clustered snap-on electric fence insulators
    positions = [(-16, -10, 15), (14, -8, 18), (0, 14, 20), (-12, 12, 28), (12, 10, 30)]
    for px, py, pz in positions:
        m.add_cylinder(r0=8, r1=8, h=14, z0=pz-7, segs=8, mat="Poly_Yellow", c0=(px, py), c1=(px, py))
        m.add_box(size=(6, 12, 6), center=(px+7, py, pz), mat="Poly_Yellow")
    return m

def build_energizer_fence_solar():
    m = Mesh("energizer_fence_solar")
    m.add_material("Case_Red", 0.88, 0.20, 0.16)
    m.add_material("PV_Top", 0.12, 0.20, 0.45)
    m.add_material("Knob_Black", 0.20, 0.20, 0.22)
    m.add_material("Terminal_Brass", 0.88, 0.72, 0.24)
    # Weatherproof solar energizer housing with tilted panel
    m.add_box(size=(52, 42, 55), center=(0, 0, 28), mat="Case_Red")
    m.add_box(size=(46, 36, 3), center=(0, 0, 56), mat="PV_Top")
    # Fence and ground output terminals
    m.add_cylinder(r0=5, r1=5, h=10, z0=22, segs=8, mat="Knob_Black", c0=(-14, 21), c1=(-14, 30))
    m.add_cylinder(r0=5, r1=5, h=10, z0=22, segs=8, mat="Case_Red", c0=( 14, 21), c1=( 14, 30))
    return m

def build_pan_feed_rubber_15gal():
    m = Mesh("pan_feed_rubber_15gal")
    m.add_material("Rubber_Black", 0.22, 0.22, 0.24)
    m.add_material("Grain_Oats", 0.88, 0.78, 0.48) # Livestock sweet feed inside
    # Shallow heavy rubber trough pan
    m.add_cylinder(r0=44, r1=48, h=26, z0=0, segs=16, mat="Rubber_Black")
    # Feed grain fill inside
    m.add_cylinder(r0=42, r1=42, h=18, z0=4, segs=14, mat="Grain_Oats")
    return m

def build_trough_stock_tank_100gal():
    m = Mesh("trough_stock_tank_100gal")
    m.add_material("Galv_Steel", 0.78, 0.80, 0.82)
    m.add_material("Steel_Rim", 0.70, 0.72, 0.74)
    m.add_material("Water_Blue", 0.22, 0.55, 0.88)
    # Oval galvanized stock tank
    m.add_box(size=(86, 52, 34), center=(0, 0, 17), mat="Galv_Steel")
    m.add_box(size=(90, 56, 4), center=(0, 0, 34), mat="Steel_Rim") # Rolled top rim
    # Water surface
    m.add_box(size=(80, 46, 2), center=(0, 0, 28), mat="Water_Blue")
    return m

def build_valve_stock_float():
    m = Mesh("valve_stock_float")
    m.add_material("Brass_Valve", 0.86, 0.68, 0.24)
    m.add_material("Arm_Stainless", 0.80, 0.82, 0.85)
    m.add_material("Float_Blue", 0.22, 0.52, 0.88)
    # Brass inlet valve & mounting clamp
    m.add_box(size=(24, 20, 26), center=(-24, 0, 25), mat="Brass_Valve")
    # Stainless steel float lever arm
    m.add_cylinder(r0=3, r1=3, h=45, z0=25, segs=6, mat="Arm_Stainless", c0=(-12, 0), c1=(30, 0))
    # Plastic float ball
    m.add_foliage_lobe(radius=16, center=(36, 0, 25), mat="Float_Blue")
    return m

def build_salt_lick_mineral_50lb():
    m = Mesh("salt_lick_mineral_50lb")
    m.add_material("Salt_RedBrown", 0.72, 0.38, 0.24) # Trace mineral red salt
    m.add_material("Holder_Blue", 0.20, 0.44, 0.80)
    # Blue plastic mounting pan/tray
    m.add_box(size=(52, 52, 8), center=(0, 0, 4), mat="Holder_Blue")
    # 50lb square mineral block with beveled edges & center hole
    m.add_box(size=(42, 42, 42), center=(0, 0, 25), mat="Salt_RedBrown")
    m.add_cylinder(r0=6, r1=6, h=44, z0=4, segs=8, mat="Holder_Blue")
    return m

def build_halter_lead_rope():
    m = Mesh("halter_lead_rope")
    m.add_material("Webbing_Red", 0.88, 0.20, 0.16)
    m.add_material("Buckle_Brass", 0.86, 0.68, 0.24)
    m.add_material("Rope_Cotton", 0.88, 0.86, 0.80)
    # Noseband and cheek straps
    m.add_torus(r_major=24, r_minor=4, segs_major=14, segs_minor=6, z0=30, mat="Webbing_Red")
    # Brass hardware rings
    m.add_torus(r_major=8, r_minor=2, segs_major=10, segs_minor=4, z0=30, mat="Buckle_Brass", c=(24, 0))
    # Coiled 10ft lead rope
    m.add_torus(r_major=28, r_minor=6, segs_major=14, segs_minor=6, z0=8, mat="Rope_Cotton")
    return m

def build_paddle_sorting_cattle():
    m = Mesh("paddle_sorting_cattle")
    m.add_material("Paddle_Red", 0.90, 0.22, 0.18)
    m.add_material("Shaft_Fiberglass", 0.94, 0.94, 0.95)
    m.add_material("Grip_Golf", 0.20, 0.20, 0.22)
    # Long white fiberglass shaft
    m.add_cylinder(r0=4, r1=4, h=70, z0=15, segs=8, mat="Shaft_Fiberglass")
    m.add_cylinder(r0=5, r1=5, h=25, z0=0, segs=8, mat="Grip_Golf")
    # Red hollow rattle paddle head
    m.add_box(size=(26, 12, 32), center=(0, 0, 80), mat="Paddle_Red")
    return m

def build_shears_sheep_wool():
    m = Mesh("shears_sheep_wool")
    m.add_material("Spring_Steel", 0.78, 0.80, 0.84)
    m.add_material("Edge_Sharp", 0.88, 0.90, 0.94)
    # Double-bow spring loop at base
    m.add_torus(r_major=15, r_minor=3.5, segs_major=12, segs_minor=6, z0=8, mat="Spring_Steel")
    # Dual wide shearing blades
    m.add_box(size=(6, 16, 52), center=(-7, 0, 45), mat="Spring_Steel")
    m.add_box(size=(6, 16, 52), center=( 7, 0, 45), mat="Spring_Steel")
    m.add_cone(r=10, h=18, z0=71, segs=4, mat="Edge_Sharp", c=(-7, 0))
    m.add_cone(r=10, h=18, z0=71, segs=4, mat="Edge_Sharp", c=( 7, 0))
    return m

def build_pail_milk_stainless():
    m = Mesh("pail_milk_stainless")
    m.add_material("Stainless_Polished", 0.88, 0.90, 0.92)
    m.add_material("Milk_White", 0.96, 0.96, 0.98)
    m.add_material("Bail_Wire", 0.72, 0.74, 0.76)
    # Tapered seamless milking pail
    m.add_cylinder(r0=26, r1=34, h=55, z0=0, segs=14, mat="Stainless_Polished")
    # Milk level inside
    m.add_cylinder(r0=30, r1=30, h=2, z0=45, segs=12, mat="Milk_White")
    # Arched wire bail carry handle
    m.add_torus(r_major=35, r_minor=2.5, segs_major=14, segs_minor=6, z0=55, mat="Bail_Wire")
    return m

def build_tape_drip_roll_1000ft():
    m = Mesh("tape_drip_roll_1000ft")
    m.add_material("Tape_Black", 0.20, 0.20, 0.22)
    m.add_material("Stripe_Blue", 0.22, 0.55, 0.88)
    m.add_material("Cardboard_Core", 0.78, 0.62, 0.42)
    # Wide roll of flat drip tape
    m.add_spool(r_flange=44, r_core=20, h=35, mat_flange="Tape_Black", mat_wire="Tape_Black", z0=0)
    # Identification blue line stripe
    m.add_torus(r_major=44.2, r_minor=2, segs_major=16, segs_minor=6, z0=18, mat="Stripe_Blue")
    return m

def build_timer_hose_digital():
    m = Mesh("timer_hose_digital")
    m.add_material("Housing_Green", 0.22, 0.52, 0.28)
    m.add_material("Dial_Black", 0.20, 0.20, 0.22)
    m.add_material("Screen_LCD", 0.70, 0.85, 0.75)
    m.add_material("Brass_Nut", 0.86, 0.68, 0.24)
    # Main timer body
    m.add_box(size=(46, 32, 54), center=(0, 0, 35), mat="Housing_Green")
    # Top brass female hose faucet swivel nut
    m.add_cylinder(r0=14, r1=14, h=14, z0=62, segs=8, mat="Brass_Nut")
    # Dual bottom outlets with male threads
    m.add_cylinder(r0=9, r1=9, h=14, z0=0, segs=8, mat="Brass_Nut", c0=(-12, 0), c1=(-12, 0))
    m.add_cylinder(r0=9, r1=9, h=14, z0=0, segs=8, mat="Brass_Nut", c0=( 12, 0), c1=( 12, 0))
    # Digital LCD programming display
    m.add_box(size=(26, 2, 18), center=(0, 17, 44), mat="Screen_LCD")
    return m

def build_sprinkler_micro_riser():
    m = Mesh("sprinkler_micro_riser")
    m.add_material("Stake_Black", 0.20, 0.20, 0.22)
    m.add_material("Nozzle_Blue", 0.22, 0.54, 0.88)
    m.add_material("Tubing_Black", 0.18, 0.18, 0.20)
    # Fluted ground stake
    m.add_cylinder(r0=5, r1=2, h=45, z0=0, segs=6, mat="Stake_Black")
    # Rigid riser tube
    m.add_cylinder(r0=3, r1=3, h=35, z0=45, segs=6, mat="Stake_Black")
    # 360° Micro-spray head nozzle on top
    m.add_cylinder(r0=6, r1=6, h=10, z0=80, segs=8, mat="Nozzle_Blue")
    # Flexible 1/4" feed tube lead
    m.add_cylinder(r0=2, r1=2, h=30, z0=50, segs=6, mat="Tubing_Black", c0=(0,0), c1=(22, 15))
    return m

FARMING_RANCHING_BUILDERS = [
    ("post_t_stake_metal", build_post_t_stake_metal, "ranching", "feed"),
    ("post_wood_round_6inch", build_post_wood_round_6inch, "ranching", "feed"),
    ("spool_wire_woven_field", build_spool_wire_woven_field, "ranching", "feed"),
    ("spool_wire_barbed_4pt", build_spool_wire_barbed_4pt, "ranching", "feed"),
    ("spool_electric_polywire", build_spool_electric_polywire, "ranching", "feed"),
    ("insulators_tpost_pack", build_insulators_tpost_pack, "ranching", "feed"),
    ("energizer_fence_solar", build_energizer_fence_solar, "ranching", "feed"),
    ("pan_feed_rubber_15gal", build_pan_feed_rubber_15gal, "ranching", "feed"),
    ("trough_stock_tank_100gal", build_trough_stock_tank_100gal, "ranching", "feed"),
    ("valve_stock_float", build_valve_stock_float, "ranching", "feed"),
    ("salt_lick_mineral_50lb", build_salt_lick_mineral_50lb, "ranching", "feed"),
    ("halter_lead_rope", build_halter_lead_rope, "ranching", "byproducts"),
    ("paddle_sorting_cattle", build_paddle_sorting_cattle, "ranching", "byproducts"),
    ("shears_sheep_wool", build_shears_sheep_wool, "ranching", "byproducts"),
    ("pail_milk_stainless", build_pail_milk_stainless, "ranching", "byproducts"),
    ("tape_drip_roll_1000ft", build_tape_drip_roll_1000ft, "farming", "irrigation"),
    ("timer_hose_digital", build_timer_hose_digital, "farming", "irrigation"),
    ("sprinkler_micro_riser", build_sprinkler_micro_riser, "farming", "irrigation"),
]

