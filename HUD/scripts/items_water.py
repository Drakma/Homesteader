#!/usr/bin/env python3
"""
Homesteader 3D Item Builders: Water & Plumbing System
Covers pipes, fittings, valves, hoses, reels, tanks, pumps, and filtration.
"""

import math
from generate_item_assets import Vec3, Mesh

def build_pipe_pvc_half_inch():
    m = Mesh("pipe_pvc_half_inch")
    m.add_material("PVC_White", 0.94, 0.94, 0.92)
    m.add_material("PVC_Bell", 0.88, 0.88, 0.86)
    m.add_material("PVC_Print", 0.20, 0.40, 0.75) # Blue text line
    # Main pipe
    m.add_cylinder(r0=10, r1=10, h=90, z0=0, segs=12, mat="PVC_White")
    # Bell coupling at top
    m.add_cylinder(r0=13, r1=13, h=20, z0=90, segs=12, mat="PVC_Bell")
    m.add_cylinder(r0=11, r1=11, h=10, z0=110, segs=12, mat="PVC_White")
    # Blue stripe / lettering
    m.add_cylinder(r0=10.2, r1=10.2, h=6, z0=45, segs=12, mat="PVC_Print")
    return m

def build_pipe_pvc_one_inch():
    m = Mesh("pipe_pvc_one_inch")
    m.add_material("PVC_White", 0.94, 0.94, 0.92)
    m.add_material("PVC_Bell", 0.88, 0.88, 0.86)
    m.add_material("PVC_Print", 0.20, 0.40, 0.75)
    m.add_cylinder(r0=18, r1=18, h=90, z0=0, segs=12, mat="PVC_White")
    m.add_cylinder(r0=22, r1=22, h=22, z0=90, segs=12, mat="PVC_Bell")
    m.add_cylinder(r0=18.2, r1=18.2, h=8, z0=45, segs=12, mat="PVC_Print")
    return m

def build_pipe_pvc_two_inch():
    m = Mesh("pipe_pvc_two_inch")
    m.add_material("PVC_White", 0.94, 0.94, 0.92)
    m.add_material("PVC_Bell", 0.88, 0.88, 0.86)
    m.add_material("PVC_Print", 0.20, 0.40, 0.75)
    m.add_cylinder(r0=30, r1=30, h=95, z0=0, segs=12, mat="PVC_White")
    m.add_cylinder(r0=35, r1=35, h=25, z0=95, segs=12, mat="PVC_Bell")
    m.add_cylinder(r0=30.3, r1=30.3, h=12, z0=45, segs=12, mat="PVC_Print")
    return m

def build_pipe_pvc_elbow():
    m = Mesh("pipe_pvc_elbow")
    m.add_material("PVC_White", 0.94, 0.94, 0.92)
    m.add_material("PVC_Rim", 0.88, 0.88, 0.86)
    # Vertical leg
    m.add_cylinder(r0=18, r1=18, h=45, z0=0, segs=12, mat="PVC_White")
    m.add_cylinder(r0=22, r1=22, h=15, z0=0, segs=12, mat="PVC_Rim")
    # Corner elbow joint
    m.add_foliage_lobe(radius=24, center=(0, 0, 50), mat="PVC_White")
    # Horizontal leg
    for i in range(12):
        a0 = i * 2.0 * math.pi / 12
        a1 = (i + 1) * 2.0 * math.pi / 12
        r = 18
        p0 = Vec3(0, r * math.cos(a0), 50 + r * math.sin(a0))
        p1 = Vec3(0, r * math.cos(a1), 50 + r * math.sin(a1))
        q0 = Vec3(45, r * math.cos(a0), 50 + r * math.sin(a0))
        q1 = Vec3(45, r * math.cos(a1), 50 + r * math.sin(a1))
        m.add_quad(p0, p1, q1, q0, mat="PVC_White")
    # Horizontal collar
    m.add_box(size=(15, 44, 44), center=(40, 0, 50), mat="PVC_Rim")
    return m

def build_pipe_pvc_tee():
    m = Mesh("pipe_pvc_tee")
    m.add_material("PVC_White", 0.94, 0.94, 0.92)
    m.add_material("PVC_Rim", 0.88, 0.88, 0.86)
    # Main straight run (vertical)
    m.add_cylinder(r0=18, r1=18, h=90, z0=0, segs=12, mat="PVC_White")
    m.add_cylinder(r0=22, r1=22, h=14, z0=0, segs=12, mat="PVC_Rim")
    m.add_cylinder(r0=22, r1=22, h=14, z0=76, segs=12, mat="PVC_Rim")
    # T center hub
    m.add_foliage_lobe(radius=23, center=(0, 0, 45), mat="PVC_White")
    # Side branch
    for i in range(12):
        a0 = i * 2.0 * math.pi / 12
        a1 = (i + 1) * 2.0 * math.pi / 12
        r = 18
        p0 = Vec3(0, r * math.cos(a0), 45 + r * math.sin(a0))
        p1 = Vec3(0, r * math.cos(a1), 45 + r * math.sin(a1))
        q0 = Vec3(42, r * math.cos(a0), 45 + r * math.sin(a0))
        q1 = Vec3(42, r * math.cos(a1), 45 + r * math.sin(a1))
        m.add_quad(p0, p1, q1, q0, mat="PVC_White")
    m.add_box(size=(14, 44, 44), center=(38, 0, 45), mat="PVC_Rim")
    return m

def build_valve_ball_brass():
    m = Mesh("valve_ball_brass")
    m.add_material("Brass_Gold", 0.86, 0.68, 0.24)
    m.add_material("Brass_Hex", 0.78, 0.60, 0.20)
    m.add_material("Lever_Red", 0.92, 0.18, 0.16)
    m.add_material("Grip_Vinyl", 0.80, 0.12, 0.12)
    # Brass body cylinder
    m.add_cylinder(r0=22, r1=22, h=70, z0=0, segs=12, mat="Brass_Gold")
    # Hex threaded ends
    m.add_cylinder(r0=25, r1=25, h=15, z0=0, segs=6, mat="Brass_Hex")
    m.add_cylinder(r0=25, r1=25, h=15, z0=55, segs=6, mat="Brass_Hex")
    # Center ball bulge
    m.add_foliage_lobe(radius=26, center=(0, 0, 35), mat="Brass_Gold")
    # Valve stem neck
    m.add_cylinder(r0=10, r1=10, h=25, z0=35, segs=8, mat="Brass_Hex", c0=(0,0), c1=(0,20))
    # Red Lever handle
    m.add_box(size=(60, 14, 6), center=(24, 20, 60), mat="Lever_Red")
    m.add_box(size=(35, 16, 8), center=(38, 20, 60), mat="Grip_Vinyl")
    return m

def build_valve_gate_brass():
    m = Mesh("valve_gate_brass")
    m.add_material("Brass_Gold", 0.86, 0.68, 0.24)
    m.add_material("Brass_Dark", 0.72, 0.54, 0.18)
    m.add_material("Wheel_Red", 0.88, 0.18, 0.16)
    # Body
    m.add_cylinder(r0=20, r1=20, h=65, z0=0, segs=12, mat="Brass_Gold")
    m.add_cylinder(r0=24, r1=24, h=14, z0=0, segs=6, mat="Brass_Dark")
    m.add_cylinder(r0=24, r1=24, h=14, z0=51, segs=6, mat="Brass_Dark")
    # Bonnet stem
    m.add_cylinder(r0=12, r1=10, h=40, z0=32, segs=8, mat="Brass_Gold", c0=(0,0), c1=(0,0))
    # Round handwheel (torus)
    m.add_torus(r_major=28, r_minor=5, segs_major=12, segs_minor=6, z0=72, mat="Wheel_Red")
    # Handwheel spokes
    m.add_box(size=(54, 6, 4), center=(0, 0, 72), mat="Wheel_Red")
    m.add_box(size=(6, 54, 4), center=(0, 0, 72), mat="Wheel_Red")
    return m

def build_hose_garden_reel():
    m = Mesh("hose_garden_reel")
    m.add_material("Frame_Green", 0.22, 0.44, 0.22)
    m.add_material("Hose_Green", 0.28, 0.68, 0.24)
    m.add_material("Brass_Fitting", 0.85, 0.68, 0.22)
    m.add_material("Handle_Black", 0.18, 0.18, 0.20)
    # A-frame stand
    m.add_cylinder(r0=4, r1=4, h=65, z0=0, segs=6, mat="Frame_Green", c0=(-28, -20), c1=(-28, 0))
    m.add_cylinder(r0=4, r1=4, h=65, z0=0, segs=6, mat="Frame_Green", c0=(-28,  20), c1=(-28, 0))
    m.add_cylinder(r0=4, r1=4, h=65, z0=0, segs=6, mat="Frame_Green", c0=( 28, -20), c1=( 28, 0))
    m.add_cylinder(r0=4, r1=4, h=65, z0=0, segs=6, mat="Frame_Green", c0=( 28,  20), c1=( 28, 0))
    # Reel spool drum
    m.add_spool(r_flange=38, r_core=22, h=48, mat_flange="Frame_Green", mat_wire="Hose_Green", z0=25)
    # Crank handle
    m.add_cylinder(r0=3, r1=3, h=18, z0=48, segs=6, mat="Frame_Green", c0=(0, 24), c1=(0, 42))
    m.add_cylinder(r0=4, r1=4, h=14, z0=48, segs=6, mat="Handle_Black", c0=(0, 42), c1=(12, 42))
    # Spurt hose lead with brass nozzle
    m.add_cylinder(r0=5, r1=5, h=25, z0=15, segs=6, mat="Hose_Green", c0=(-18, -18), c1=(-32, -32))
    m.add_cylinder(r0=6, r1=5, h=12, z0=10, segs=8, mat="Brass_Fitting", c0=(-32, -32), c1=(-40, -40))
    return m

def build_hose_contractor_heavy():
    m = Mesh("hose_contractor_heavy")
    m.add_material("Rubber_Black", 0.20, 0.20, 0.22)
    m.add_material("Brass_Fitting", 0.85, 0.68, 0.22)
    m.add_material("Stripe_Yellow", 0.92, 0.80, 0.20)
    # Triple coil of heavy black hose
    m.add_torus(r_major=44, r_minor=8, segs_major=16, segs_minor=8, z0=8, mat="Rubber_Black")
    m.add_torus(r_major=40, r_minor=8, segs_major=16, segs_minor=8, z0=22, mat="Rubber_Black")
    m.add_torus(r_major=36, r_minor=8, segs_major=16, segs_minor=8, z0=36, mat="Rubber_Black")
    # Yellow reinforcement stripe ring
    m.add_torus(r_major=44.2, r_minor=2, segs_major=16, segs_minor=6, z0=12, mat="Stripe_Yellow")
    # Brass male coupling sticking out
    m.add_cylinder(r0=9, r1=8, h=22, z0=36, segs=8, mat="Brass_Fitting", c0=(36, 0), c1=(54, 12))
    # Brass female coupling
    m.add_cylinder(r0=10, r1=9, h=20, z0=8, segs=8, mat="Brass_Fitting", c0=(-42, 0), c1=(-58, -10))
    return m

def build_nozzle_spray_quick():
    m = Mesh("nozzle_spray_quick")
    m.add_material("Brass_Body", 0.86, 0.68, 0.24)
    m.add_material("Rubber_Grip", 0.22, 0.22, 0.24)
    m.add_material("Brass_Tip", 0.92, 0.74, 0.28)
    # Base quick connector
    m.add_cylinder(r0=14, r1=12, h=20, z0=0, segs=10, mat="Brass_Body")
    m.add_cylinder(r0=16, r1=16, h=10, z0=12, segs=10, mat="Brass_Body")
    # Textured black rubber barrel grip
    m.add_cylinder(r0=15, r1=13, h=35, z0=22, segs=10, mat="Rubber_Grip")
    # Adjustable spray tip
    m.add_cylinder(r0=13, r1=16, h=25, z0=57, segs=10, mat="Brass_Body")
    m.add_cylinder(r0=16, r1=12, h=15, z0=82, segs=10, mat="Brass_Tip")
    return m

def build_wand_watering_brass():
    m = Mesh("wand_watering_brass")
    m.add_material("Brass_Wand", 0.86, 0.68, 0.24)
    m.add_material("Grip_Foam", 0.18, 0.20, 0.22)
    m.add_material("Valve_Lever", 0.24, 0.58, 0.85) # Blue thumb valve
    m.add_material("Shower_Head", 0.82, 0.82, 0.84) # Perforated face
    # Handle & thumb valve
    m.add_cylinder(r0=9, r1=8, h=35, z0=0, segs=8, mat="Grip_Foam")
    m.add_box(size=(16, 8, 12), center=(0, 8, 30), mat="Valve_Lever")
    # Long slender brass tube
    m.add_cylinder(r0=5, r1=4.5, h=65, z0=35, segs=8, mat="Brass_Wand")
    # Curved top neck
    m.add_cylinder(r0=4.5, r1=4.5, h=20, z0=100, segs=8, mat="Brass_Wand", c0=(0,0), c1=(12, 10))
    # Shower spray rosette head
    m.add_cylinder(r0=12, r1=24, h=14, z0=112, segs=12, mat="Brass_Wand", c0=(12,10), c1=(18,15))
    m.add_cylinder(r0=24, r1=24, h=4, z0=126, segs=12, mat="Shower_Head", c0=(18,15), c1=(18,15))
    return m

def build_tubing_drip_irrigation():
    m = Mesh("tubing_drip_irrigation")
    m.add_material("Poly_Black", 0.18, 0.18, 0.20)
    m.add_material("Emitter_Red", 0.90, 0.20, 0.16)
    m.add_material("Tie_Tape", 0.25, 0.55, 0.85)
    # Double coil of 1/2" drip tubing
    m.add_torus(r_major=42, r_minor=6, segs_major=16, segs_minor=8, z0=8, mat="Poly_Black")
    m.add_torus(r_major=38, r_minor=6, segs_major=16, segs_minor=8, z0=20, mat="Poly_Black")
    # Packaging binding tape
    m.add_box(size=(14, 18, 22), center=(0, 40, 14), mat="Tie_Tape")
    m.add_box(size=(14, 18, 22), center=(0, -40, 14), mat="Tie_Tape")
    # Barbed drip emitters inserted along coil
    emitters = [(30, 28, 24), (-25, 30, 12), (32, -26, 12), (-28, -28, 24)]
    for ex, ey, ez in emitters:
        m.add_box(size=(6, 6, 8), center=(ex, ey, ez), mat="Emitter_Red")
    return m

def build_hose_soaker_flat():
    m = Mesh("hose_soaker_flat")
    m.add_material("Porous_Black", 0.24, 0.24, 0.26)
    m.add_material("Brass_Fitting", 0.85, 0.68, 0.22)
    # Flat porous rubber hose coil
    m.add_torus(r_major=40, r_minor=7, segs_major=16, segs_minor=6, z0=7, mat="Porous_Black")
    m.add_torus(r_major=34, r_minor=7, segs_major=16, segs_minor=6, z0=20, mat="Porous_Black")
    # Brass coupling
    m.add_cylinder(r0=8, r1=7, h=18, z0=20, segs=8, mat="Brass_Fitting", c0=(34, 0), c1=(48, 10))
    return m

def build_water_jug_5gal():
    m = Mesh("water_jug_5gal")
    m.add_material("Poly_Blue", 0.28, 0.60, 0.88)
    m.add_material("Rib_Dark", 0.22, 0.50, 0.78)
    m.add_material("Cap_White", 0.94, 0.94, 0.96)
    # Main cylindrical jug body
    m.add_cylinder(r0=34, r1=34, h=75, z0=0, segs=14, mat="Poly_Blue")
    # Structural rib indentations
    m.add_cylinder(r0=35, r1=35, h=6, z0=22, segs=14, mat="Rib_Dark")
    m.add_cylinder(r0=35, r1=35, h=6, z0=48, segs=14, mat="Rib_Dark")
    # Tapered shoulder
    m.add_cone(r=34, h=18, z0=75, segs=14, mat="Poly_Blue")
    # Molded carry handle
    m.add_cylinder(r0=5, r1=5, h=25, z0=45, segs=6, mat="Poly_Blue", c0=(28, 0), c1=(28, 0))
    # Bottle neck & snap cap
    m.add_cylinder(r0=12, r1=12, h=15, z0=93, segs=10, mat="Cap_White")
    return m

def build_barrel_rain_55gal():
    m = Mesh("barrel_rain_55gal")
    m.add_material("Poly_Blue", 0.18, 0.42, 0.72)
    m.add_material("Rib_Blue", 0.14, 0.35, 0.62)
    m.add_material("Lid_Black", 0.18, 0.18, 0.20)
    m.add_material("Brass_Spigot", 0.86, 0.68, 0.24)
    # Barrel body with bulged ribs
    m.add_cylinder(r0=36, r1=40, h=45, z0=0, segs=14, mat="Poly_Blue")
    m.add_cylinder(r0=40, r1=36, h=45, z0=45, segs=14, mat="Poly_Blue")
    m.add_cylinder(r0=41.5, r1=41.5, h=6, z0=30, segs=14, mat="Rib_Blue")
    m.add_cylinder(r0=41.5, r1=41.5, h=6, z0=60, segs=14, mat="Rib_Blue")
    # Top lid & inlet screen
    m.add_cylinder(r0=37, r1=37, h=5, z0=90, segs=14, mat="Lid_Black")
    m.add_cylinder(r0=18, r1=18, h=2, z0=95, segs=10, mat="Lid_Black")
    # Brass drain spigot near bottom
    m.add_cylinder(r0=5, r1=4, h=16, z0=15, segs=8, mat="Brass_Spigot", c0=(0, 36), c1=(0, 52))
    m.add_box(size=(6, 14, 4), center=(0, 48, 20), mat="Brass_Spigot")
    return m

def build_tank_ibc_tote_275gal():
    m = Mesh("tank_ibc_tote_275gal")
    m.add_material("Poly_White", 0.92, 0.93, 0.90)
    m.add_material("Cage_Galv", 0.72, 0.74, 0.76)
    m.add_material("Pallet_Black", 0.22, 0.22, 0.24)
    m.add_material("Valve_Red", 0.88, 0.18, 0.16)
    # Bottom shipping pallet
    m.add_box(size=(76, 76, 10), center=(0, 0, 5), mat="Pallet_Black")
    # Internal white translucent blow-molded bottle
    m.add_box(size=(66, 66, 70), center=(0, 0, 45), mat="Poly_White")
    # Top fill cap
    m.add_cylinder(r0=12, r1=12, h=6, z0=80, segs=10, mat="Pallet_Black")
    # Bottom discharge butterfly valve with red handle
    m.add_cylinder(r0=8, r1=8, h=14, z0=16, segs=8, mat="Pallet_Black", c0=(0, 33), c1=(0, 47))
    m.add_box(size=(14, 6, 6), center=(0, 44, 22), mat="Valve_Red")
    # External steel cage grid posts
    for x in [-35, 0, 35]:
        for y in [-35, 35]:
            m.add_box(size=(3, 3, 72), center=(x, y, 46), mat="Cage_Galv")
    for y in [-35, 0, 35]:
        for x in [-35, 35]:
            m.add_box(size=(3, 3, 72), center=(x, y, 46), mat="Cage_Galv")
    # Horizontal cage rings
    for z in [25, 45, 65, 80]:
        m.add_box(size=(72, 4, 3), center=(0, 35, z), mat="Cage_Galv")
        m.add_box(size=(72, 4, 3), center=(0, -35, z), mat="Cage_Galv")
        m.add_box(size=(4, 72, 3), center=(35, 0, z), mat="Cage_Galv")
        m.add_box(size=(4, 72, 3), center=(-35, 0, z), mat="Cage_Galv")
    return m

def build_cistern_poly_1000gal():
    m = Mesh("cistern_poly_1000gal")
    m.add_material("Poly_Green", 0.18, 0.38, 0.22)
    m.add_material("Rib_Dark", 0.14, 0.30, 0.18)
    m.add_material("Lid_Black", 0.18, 0.18, 0.20)
    # Heavy vertical cistern body
    m.add_cylinder(r0=42, r1=42, h=80, z0=0, segs=16, mat="Poly_Green")
    # Reinforcing structural hoop ribs
    for z in [18, 38, 58]:
        m.add_cylinder(r0=44, r1=44, h=6, z0=z, segs=16, mat="Rib_Dark")
    # Domed roof
    m.add_cone(r=42, h=15, z0=80, segs=16, mat="Poly_Green")
    # Manway access inspection hatch
    m.add_cylinder(r0=16, r1=16, h=6, z0=95, segs=12, mat="Lid_Black")
    return m

def build_pump_pitcher_manual():
    m = Mesh("pump_pitcher_manual")
    m.add_material("CastIron_Dark", 0.26, 0.28, 0.30)
    m.add_material("CastIron_Highlight", 0.36, 0.38, 0.40)
    # Flanged mounting base
    m.add_cylinder(r0=24, r1=20, h=10, z0=0, segs=10, mat="CastIron_Dark")
    # Lower cylinder column
    m.add_cylinder(r0=14, r1=12, h=45, z0=10, segs=10, mat="CastIron_Dark")
    # Upper pump cylinder with spout
    m.add_cylinder(r0=16, r1=16, h=30, z0=55, segs=10, mat="CastIron_Dark")
    # Discharge pitcher spout
    m.add_cylinder(r0=8, r1=6, h=25, z0=60, segs=8, mat="CastIron_Highlight", c0=(0, 12), c1=(0, 35))
    # Curved manual pump handle lever
    m.add_cylinder(r0=4, r1=3.5, h=55, z0=75, segs=6, mat="CastIron_Highlight", c0=(0, -12), c1=(0, -55))
    m.add_foliage_lobe(radius=6, center=(0, -55, 75), mat="CastIron_Dark")
    return m

def build_pump_jet_shallow_well():
    m = Mesh("pump_jet_shallow_well")
    m.add_material("Tank_Blue", 0.22, 0.48, 0.82)
    m.add_material("Pump_CastIron", 0.25, 0.26, 0.28)
    m.add_material("Brass_Switch", 0.84, 0.68, 0.22)
    # Horizontal cylindrical pressure tank
    r = 24
    for i in range(12):
        a0 = i * 2.0 * math.pi / 12
        a1 = (i + 1) * 2.0 * math.pi / 12
        y0, z0 = r * math.cos(a0), 24 + r * math.sin(a0)
        y1, z1 = r * math.cos(a1), 24 + r * math.sin(a1)
        m.add_quad(Vec3(-35, y0, z0), Vec3(35, y0, z0), Vec3(35, y1, z1), Vec3(-35, y1, z1), mat="Tank_Blue")
    m.add_foliage_lobe(radius=24, center=(-35, 0, 24), mat="Tank_Blue")
    m.add_foliage_lobe(radius=24, center=(35, 0, 24), mat="Tank_Blue")
    # Stand feet
    m.add_box(size=(10, 56, 8), center=(-20, 0, 4), mat="Pump_CastIron")
    m.add_box(size=(10, 56, 8), center=(20, 0, 4), mat="Pump_CastIron")
    # Top-mounted electric jet pump motor
    m.add_cylinder(r0=14, r1=14, h=35, z0=48, segs=10, mat="Pump_CastIron", c0=(-12, 0), c1=(-12, 0))
    # Pressure switch box & gauge
    m.add_box(size=(14, 14, 16), center=(16, 10, 60), mat="Brass_Switch")
    return m

def build_pump_submersible_deep():
    m = Mesh("pump_submersible_deep")
    m.add_material("Stainless_Steel", 0.85, 0.88, 0.90)
    m.add_material("Stainless_Dark", 0.68, 0.70, 0.72)
    m.add_material("Cable_Black", 0.18, 0.18, 0.20)
    # Long polished stainless steel well tube
    m.add_cylinder(r0=16, r1=16, h=85, z0=0, segs=12, mat="Stainless_Steel")
    # Intake suction screen grill
    m.add_cylinder(r0=16.5, r1=16.5, h=15, z0=45, segs=12, mat="Stainless_Dark")
    # Top discharge brass head with check valve
    m.add_cylinder(r0=14, r1=12, h=18, z0=85, segs=10, mat="Stainless_Dark")
    # Submersible motor drop cable running along side
    m.add_cylinder(r0=3, r1=3, h=100, z0=0, segs=6, mat="Cable_Black", c0=(16, 0), c1=(16, 0))
    return m

def build_pump_sump_float():
    m = Mesh("pump_sump_float")
    m.add_material("Poly_Black", 0.20, 0.22, 0.24)
    m.add_material("Discharge_PVC", 0.90, 0.90, 0.88)
    m.add_material("Float_Blue", 0.25, 0.55, 0.90)
    m.add_material("Handle_Metal", 0.75, 0.75, 0.78)
    # Base suction strainer base
    m.add_cylinder(r0=28, r1=25, h=20, z0=0, segs=12, mat="Poly_Black")
    # Motor body housing
    m.add_cylinder(r0=20, r1=16, h=45, z0=20, segs=10, mat="Poly_Black")
    # Top carry handle
    m.add_cylinder(r0=3, r1=3, h=18, z0=65, segs=6, mat="Handle_Metal", c0=(0, -12), c1=(0, 12))
    # Vertical discharge pipe adapter
    m.add_cylinder(r0=9, r1=9, h=35, z0=25, segs=8, mat="Discharge_PVC", c0=(18, 0), c1=(18, 0))
    # Tethered float switch
    m.add_cylinder(r0=2, r1=2, h=30, z0=30, segs=6, mat="Poly_Black", c0=(-16, 0), c1=(-32, 10))
    m.add_foliage_lobe(radius=10, center=(-34, 12, 45), mat="Float_Blue")
    return m

def build_filter_spin_down_sediment():
    m = Mesh("filter_spin_down_sediment")
    m.add_material("Brass_Head", 0.86, 0.68, 0.24)
    m.add_material("Clear_Bowl", 0.50, 0.75, 0.85) # Semi-translucent cyan
    m.add_material("Mesh_Screen", 0.85, 0.85, 0.88)
    m.add_material("Flush_Valve", 0.88, 0.20, 0.16)
    # Top brass mounting manifold
    m.add_box(size=(64, 24, 20), center=(0, 0, 80), mat="Brass_Head")
    # Internal stainless steel filter screen
    m.add_cylinder(r0=14, r1=12, h=55, z0=20, segs=10, mat="Mesh_Screen")
    # Outer transparent sump bowl
    m.add_cylinder(r0=22, r1=18, h=60, z0=15, segs=12, mat="Clear_Bowl")
    # Bottom purge flush ball valve
    m.add_cylinder(r0=6, r1=6, h=15, z0=0, segs=8, mat="Brass_Head")
    m.add_box(size=(20, 6, 6), center=(0, 0, 5), mat="Flush_Valve")
    return m

def build_filter_canister_big_blue():
    m = Mesh("filter_canister_big_blue")
    m.add_material("Canister_Blue", 0.18, 0.42, 0.82)
    m.add_material("Cap_Black", 0.20, 0.20, 0.22)
    m.add_material("Button_Red", 0.90, 0.18, 0.16)
    # Black top manifold cap with pressure relief button
    m.add_cylinder(r0=28, r1=28, h=22, z0=68, segs=12, mat="Cap_Black")
    m.add_box(size=(66, 26, 16), center=(0, 0, 78), mat="Cap_Black")
    m.add_cylinder(r0=4, r1=4, h=6, z0=90, segs=8, mat="Button_Red", c0=(0, 10), c1=(0, 10))
    # Big Blue ribbed filter housing sump
    m.add_cylinder(r0=26, r1=24, h=68, z0=0, segs=12, mat="Canister_Blue")
    for z in [18, 38, 56]:
        m.add_cylinder(r0=27, r1=27, h=4, z0=z, segs=12, mat="Canister_Blue")
    return m

def build_filter_rack_3stage():
    m = Mesh("filter_rack_3stage")
    m.add_material("Steel_Bracket", 0.92, 0.92, 0.94) # White powdercoat frame
    m.add_material("Canister_Blue", 0.18, 0.42, 0.82)
    m.add_material("Gauge_Face", 0.95, 0.95, 0.95)
    m.add_material("Brass_Fittings", 0.85, 0.68, 0.22)
    # Heavy mounting bracket
    m.add_box(size=(88, 26, 16), center=(0, 0, 78), mat="Steel_Bracket")
    # 3 filtration canisters
    for cx in [-28, 0, 28]:
        m.add_cylinder(r0=12, r1=11, h=68, z0=0, segs=10, mat="Canister_Blue", c0=(cx,0), c1=(cx,0))
    # Dual pressure gauges on top
    for gx in [-28, 28]:
        m.add_cylinder(r0=7, r1=7, h=5, z0=88, segs=10, mat="Gauge_Face", c0=(gx, 6), c1=(gx, 6))
        m.add_cylinder(r0=3, r1=3, h=6, z0=82, segs=6, mat="Brass_Fittings", c0=(gx, 6), c1=(gx, 6))
    return m

def build_filter_reverse_osmosis():
    m = Mesh("filter_reverse_osmosis")
    m.add_material("Canister_White", 0.94, 0.94, 0.92)
    m.add_material("Membrane_Vessel", 0.88, 0.90, 0.92)
    m.add_material("Tubing_Color", 0.20, 0.55, 0.88)
    m.add_material("Bracket_Metal", 0.75, 0.78, 0.80)
    # 3 vertical pre-filters
    for cx in [-24, 0, 24]:
        m.add_cylinder(r0=10, r1=9.5, h=55, z0=0, segs=10, mat="Canister_White", c0=(cx,0), c1=(cx,0))
    # Top horizontal RO membrane pressure vessel
    m.add_cylinder(r0=11, r1=11, h=65, z0=65, segs=10, mat="Membrane_Vessel", c0=(-32, 0), c1=(32, 0))
    # Interconnecting blue 1/4" tubing loop
    m.add_torus(r_major=18, r_minor=2.5, segs_major=10, segs_minor=6, z0=45, mat="Tubing_Color", c=(0, 10))
    return m

def build_sterilizer_uv_chamber():
    m = Mesh("sterilizer_uv_chamber")
    m.add_material("Stainless_Chamber", 0.88, 0.90, 0.92)
    m.add_material("Ballast_Black", 0.20, 0.20, 0.22)
    m.add_material("Lamp_Glow", 0.60, 0.85, 1.0) # Violet-cyan quartz glow
    # Polished stainless steel cylindrical reactor chamber
    m.add_cylinder(r0=16, r1=16, h=80, z0=0, segs=12, mat="Stainless_Chamber")
    # Inlet & outlet threaded water ports
    m.add_cylinder(r0=7, r1=7, h=14, z0=15, segs=8, mat="Stainless_Chamber", c0=(0, 16), c1=(0, 30))
    m.add_cylinder(r0=7, r1=7, h=14, z0=65, segs=8, mat="Stainless_Chamber", c0=(0, 16), c1=(0, 30))
    # Electronic ballast power controller with green indicator LED
    m.add_box(size=(22, 16, 32), center=(0, -22, 40), mat="Ballast_Black")
    m.add_foliage_lobe(radius=3, center=(0, -30, 48), mat="Lamp_Glow")
    return m

WATER_BUILDERS = [
    ("pipe_pvc_half_inch", build_pipe_pvc_half_inch, "water", "piping"),
    ("pipe_pvc_one_inch", build_pipe_pvc_one_inch, "water", "piping"),
    ("pipe_pvc_two_inch", build_pipe_pvc_two_inch, "water", "piping"),
    ("pipe_pvc_elbow", build_pipe_pvc_elbow, "water", "piping"),
    ("pipe_pvc_tee", build_pipe_pvc_tee, "water", "piping"),
    ("valve_ball_brass", build_valve_ball_brass, "water", "piping"),
    ("valve_gate_brass", build_valve_gate_brass, "water", "piping"),
    ("hose_garden_reel", build_hose_garden_reel, "water", "piping"),
    ("hose_contractor_heavy", build_hose_contractor_heavy, "water", "piping"),
    ("nozzle_spray_quick", build_nozzle_spray_quick, "water", "piping"),
    ("wand_watering_brass", build_wand_watering_brass, "water", "piping"),
    ("tubing_drip_irrigation", build_tubing_drip_irrigation, "water", "piping"),
    ("hose_soaker_flat", build_hose_soaker_flat, "water", "piping"),
    ("water_jug_5gal", build_water_jug_5gal, "water", "sources"),
    ("barrel_rain_55gal", build_barrel_rain_55gal, "water", "sources"),
    ("tank_ibc_tote_275gal", build_tank_ibc_tote_275gal, "water", "sources"),
    ("cistern_poly_1000gal", build_cistern_poly_1000gal, "water", "sources"),
    ("pump_pitcher_manual", build_pump_pitcher_manual, "water", "sources"),
    ("pump_jet_shallow_well", build_pump_jet_shallow_well, "water", "sources"),
    ("pump_submersible_deep", build_pump_submersible_deep, "water", "sources"),
    ("pump_sump_float", build_pump_sump_float, "water", "sources"),
    ("filter_spin_down_sediment", build_filter_spin_down_sediment, "water", "treatment"),
    ("filter_canister_big_blue", build_filter_canister_big_blue, "water", "treatment"),
    ("filter_rack_3stage", build_filter_rack_3stage, "water", "treatment"),
    ("filter_reverse_osmosis", build_filter_reverse_osmosis, "water", "treatment"),
    ("sterilizer_uv_chamber", build_sterilizer_uv_chamber, "water", "treatment"),
]

