#!/usr/bin/env python3
"""
Homesteader 3D Item Builders: Sewage & Sanitation System
Covers septic tanks, leach field piping, RV sewer hoses, macerators, composting toilets, and aeration.
"""

import math
from generate_item_assets import Vec3, Mesh

def build_tank_septic_poly_500gal():
    m = Mesh("tank_septic_poly_500gal")
    m.add_material("Poly_Black", 0.18, 0.18, 0.20)
    m.add_material("Rib_Highlight", 0.26, 0.26, 0.28)
    m.add_material("Riser_Green", 0.20, 0.44, 0.22)
    # Horizontal ribbed cylinder
    r = 30
    for i in range(12):
        a0 = i * 2.0 * math.pi / 12
        a1 = (i + 1) * 2.0 * math.pi / 12
        y0, z0 = r * math.cos(a0), 30 + r * math.sin(a0)
        y1, z1 = r * math.cos(a1), 30 + r * math.sin(a1)
        m.add_quad(Vec3(-42, y0, z0), Vec3(42, y0, z0), Vec3(42, y1, z1), Vec3(-42, y1, z1), mat="Poly_Black")
    m.add_foliage_lobe(radius=30, center=(-42, 0, 30), mat="Poly_Black")
    m.add_foliage_lobe(radius=30, center=(42, 0, 30), mat="Poly_Black")
    # 4 External reinforcing ribs
    for x in [-25, -8, 8, 25]:
        m.add_torus(r_major=31.5, r_minor=2.5, segs_major=12, segs_minor=6, z0=30, mat="Rib_Highlight", c=(x, 0))
    # Dual access risers on top
    m.add_cylinder(r0=12, r1=12, h=16, z0=58, segs=10, mat="Riser_Green", c0=(-20, 0), c1=(-20, 0))
    m.add_cylinder(r0=12, r1=12, h=16, z0=58, segs=10, mat="Riser_Green", c0=(20, 0), c1=(20, 0))
    return m

def build_tank_septic_concrete_1000gal():
    m = Mesh("tank_septic_concrete_1000gal")
    m.add_material("Concrete_Gray", 0.65, 0.65, 0.66)
    m.add_material("Concrete_Seam", 0.48, 0.48, 0.50)
    m.add_material("Lid_CastIron", 0.28, 0.28, 0.30)
    # Heavy rectangular concrete vault
    m.add_box(size=(88, 54, 48), center=(0, 0, 24), mat="Concrete_Gray")
    # Mold seam center division
    m.add_box(size=(4, 56, 50), center=(0, 0, 24), mat="Concrete_Seam")
    # Dual round manhole access lids
    m.add_cylinder(r0=14, r1=14, h=4, z0=48, segs=12, mat="Lid_CastIron", c0=(-24, 0), c1=(-24, 0))
    m.add_cylinder(r0=14, r1=14, h=4, z0=48, segs=12, mat="Lid_CastIron", c0=(24, 0), c1=(24, 0))
    # Inlet & outlet pipe cutouts
    m.add_cylinder(r0=6, r1=6, h=8, z0=36, segs=8, mat="Concrete_Seam", c0=(-48, 0), c1=(-40, 0))
    m.add_cylinder(r0=6, r1=6, h=8, z0=32, segs=8, mat="Concrete_Seam", c0=(40, 0), c1=(48, 0))
    return m

def build_tank_rv_waste_tote():
    m = Mesh("tank_rv_waste_tote")
    m.add_material("Tote_Blue", 0.18, 0.44, 0.82)
    m.add_material("Tire_Black", 0.18, 0.18, 0.20)
    m.add_material("Hub_Metal", 0.75, 0.75, 0.78)
    m.add_material("Handle_Steel", 0.82, 0.82, 0.84)
    # Low-profile flat waste tank body with contoured ribs
    m.add_box(size=(72, 44, 22), center=(0, 0, 18), mat="Tote_Blue")
    m.add_box(size=(64, 46, 6), center=(0, 0, 22), mat="Tote_Blue")
    # Rear heavy rubber wheels
    for y in [-25, 25]:
        m.add_cylinder(r0=12, r1=12, h=6, z0=12, segs=10, mat="Tire_Black", c0=(-26, y-3), c1=(-26, y+3))
        m.add_cylinder(r0=5, r1=5, h=7, z0=12, segs=8, mat="Hub_Metal", c0=(-26, y-3.5), c1=(-26, y+3.5))
    # Towing tow-handle bracket
    m.add_cylinder(r0=3, r1=3, h=35, z0=18, segs=6, mat="Handle_Steel", c0=(36, 0), c1=(60, 0))
    # Discharge dump bayonet port
    m.add_cylinder(r0=9, r1=9, h=8, z0=29, segs=10, mat="Tire_Black", c0=(-10, 0), c1=(-10, 0))
    return m

def build_toilet_composting_rustic():
    m = Mesh("toilet_composting_rustic")
    m.add_material("Wood_Cedar", 0.72, 0.52, 0.34)
    m.add_material("Wood_Dark", 0.55, 0.38, 0.22)
    m.add_material("Seat_White", 0.95, 0.95, 0.95)
    m.add_material("Vent_Pipe", 0.22, 0.22, 0.24)
    # Box base cabinet
    m.add_box(size=(52, 46, 42), center=(0, 0, 21), mat="Wood_Cedar")
    m.add_box(size=(54, 48, 4), center=(0, 0, 42), mat="Wood_Dark")
    # Toilet seat lid
    m.add_torus(r_major=16, r_minor=4, segs_major=12, segs_minor=6, z0=46, mat="Seat_White", c=(0, -4))
    # Rear vertical exhaust ventilation pipe
    m.add_cylinder(r0=6, r1=6, h=55, z0=30, segs=8, mat="Vent_Pipe", c0=(-16, 16), c1=(-16, 16))
    m.add_cone(r=10, h=8, z0=85, segs=8, mat="Vent_Pipe", c=(-16, 16))
    # Crank agitation handle on side
    m.add_cylinder(r0=3, r1=3, h=15, z0=25, segs=6, mat="Wood_Dark", c0=(26, 0), c1=(38, 0))
    return m

def build_pipe_sewer_solid_4inch():
    m = Mesh("pipe_sewer_solid_4inch")
    m.add_material("PVC_Green", 0.24, 0.58, 0.32) # Standard green SDR-35 sewer pipe
    m.add_material("Gasket_Bell", 0.18, 0.44, 0.25)
    m.add_cylinder(r0=24, r1=24, h=90, z0=0, segs=12, mat="PVC_Green")
    m.add_cylinder(r0=28, r1=28, h=22, z0=90, segs=12, mat="Gasket_Bell")
    return m

def build_pipe_leach_perforated_4inch():
    m = Mesh("pipe_leach_perforated_4inch")
    m.add_material("PVC_White", 0.92, 0.92, 0.90)
    m.add_material("Hole_Black", 0.15, 0.15, 0.18)
    m.add_cylinder(r0=24, r1=24, h=95, z0=0, segs=12, mat="PVC_White")
    # Rows of perforated drain holes
    for z in [20, 38, 56, 74]:
        for ang in [math.pi*0.25, math.pi*0.75]:
            hx = 24.2 * math.cos(ang)
            hy = 24.2 * math.sin(ang)
            m.add_box(size=(4, 4, 6), center=(hx, hy, z), mat="Hole_Black")
    return m

def build_box_distribution_septic():
    m = Mesh("box_distribution_septic")
    m.add_material("Poly_Green", 0.22, 0.46, 0.26)
    m.add_material("Lid_Green", 0.26, 0.52, 0.30)
    m.add_material("Seal_Black", 0.18, 0.18, 0.20)
    # Square D-box body
    m.add_box(size=(58, 58, 40), center=(0, 0, 20), mat="Poly_Green")
    # Top lid with handle
    m.add_box(size=(62, 62, 6), center=(0, 0, 43), mat="Lid_Green")
    m.add_box(size=(16, 6, 6), center=(0, 0, 48), mat="Lid_Green")
    # 4 Outflow ports with rubber seals
    m.add_cylinder(r0=8, r1=8, h=10, z0=15, segs=8, mat="Seal_Black", c0=(0, 29), c1=(0, 38))
    m.add_cylinder(r0=8, r1=8, h=10, z0=15, segs=8, mat="Seal_Black", c0=(0, -29), c1=(0, -38))
    m.add_cylinder(r0=8, r1=8, h=10, z0=15, segs=8, mat="Seal_Black", c0=(29, 0), c1=(38, 0))
    m.add_cylinder(r0=8, r1=8, h=10, z0=22, segs=8, mat="Seal_Black", c0=(-29, 0), c1=(-38, 0)) # Inlet higher
    return m

def build_riser_septic_lid():
    m = Mesh("riser_septic_lid")
    m.add_material("Riser_Green", 0.24, 0.50, 0.28)
    m.add_material("Rib_Dark", 0.18, 0.38, 0.22)
    m.add_material("Bolt_Steel", 0.82, 0.82, 0.84)
    # Ribbed circular riser ring
    m.add_cylinder(r0=40, r1=40, h=45, z0=0, segs=14, mat="Riser_Green")
    m.add_torus(r_major=41, r_minor=3, segs_major=14, segs_minor=6, z0=15, mat="Rib_Dark")
    m.add_torus(r_major=41, r_minor=3, segs_major=14, segs_minor=6, z0=30, mat="Rib_Dark")
    # Heavy green locking lid
    m.add_cylinder(r0=42, r1=42, h=8, z0=45, segs=14, mat="Riser_Green")
    # Lock bolts
    for i in range(4):
        a = i * math.pi * 0.5
        m.add_cylinder(r0=3, r1=3, h=4, z0=53, segs=6, mat="Bolt_Steel", c0=(34*math.cos(a), 34*math.sin(a)), c1=(34*math.cos(a), 34*math.sin(a)))
    return m

def build_drain_french_sock():
    m = Mesh("drain_french_sock")
    m.add_material("Fabric_Black", 0.24, 0.24, 0.26)
    m.add_material("Core_Yellow", 0.88, 0.78, 0.22) # Slotted yellow corrugated inside
    # French drain coil wrapped in geotextile sock
    m.add_torus(r_major=40, r_minor=12, segs_major=16, segs_minor=8, z0=12, mat="Fabric_Black")
    m.add_torus(r_major=34, r_minor=12, segs_major=16, segs_minor=8, z0=30, mat="Fabric_Black")
    # Cut end showing yellow core
    m.add_cylinder(r0=11, r1=11, h=10, z0=30, segs=8, mat="Core_Yellow", c0=(34, 0), c1=(44, 0))
    return m

def build_hose_sewer_rv_10ft():
    m = Mesh("hose_sewer_rv_10ft")
    m.add_material("Hose_Orange", 0.90, 0.44, 0.16)
    m.add_material("Rib_Black", 0.18, 0.18, 0.20)
    m.add_material("Bayonet_Lug", 0.85, 0.40, 0.14)
    # Accordion collapsible hose coil
    m.add_torus(r_major=38, r_minor=10, segs_major=16, segs_minor=8, z0=10, mat="Hose_Orange")
    m.add_torus(r_major=34, r_minor=10, segs_major=16, segs_minor=8, z0=26, mat="Hose_Orange")
    # Accordion ribs
    m.add_torus(r_major=38.5, r_minor=3, segs_major=16, segs_minor=6, z0=14, mat="Rib_Black")
    m.add_torus(r_major=34.5, r_minor=3, segs_major=16, segs_minor=6, z0=30, mat="Rib_Black")
    # Bayonet connector
    m.add_cylinder(r0=14, r1=14, h=18, z0=26, segs=10, mat="Bayonet_Lug", c0=(34, 0), c1=(48, 8))
    return m

def build_hose_sewer_rv_20ft():
    m = Mesh("hose_sewer_rv_20ft")
    m.add_material("Hose_Black", 0.22, 0.22, 0.24)
    m.add_material("Elbow_Clear", 0.55, 0.75, 0.85) # Transparent dump station elbow
    m.add_material("Adapter_Orange", 0.90, 0.42, 0.16)
    m.add_torus(r_major=42, r_minor=10, segs_major=16, segs_minor=8, z0=10, mat="Hose_Black")
    m.add_torus(r_major=38, r_minor=10, segs_major=16, segs_minor=8, z0=25, mat="Hose_Black")
    m.add_torus(r_major=34, r_minor=10, segs_major=16, segs_minor=8, z0=40, mat="Hose_Black")
    # 90° Clear dump station elbow
    m.add_cylinder(r0=13, r1=13, h=22, z0=40, segs=10, mat="Elbow_Clear", c0=(34, 0), c1=(48, 12))
    m.add_cylinder(r0=15, r1=12, h=16, z0=24, segs=10, mat="Adapter_Orange", c0=(48, 12), c1=(48, 12))
    return m

def build_fitting_camlock_coupler():
    m = Mesh("fitting_camlock_coupler")
    m.add_material("Aluminum_Cast", 0.80, 0.82, 0.84)
    m.add_material("Brass_Arm", 0.86, 0.68, 0.24)
    m.add_material("Gasket_Black", 0.20, 0.20, 0.22)
    # 3" Main coupler socket body
    m.add_cylinder(r0=24, r1=24, h=45, z0=0, segs=12, mat="Aluminum_Cast")
    m.add_cylinder(r0=28, r1=28, h=16, z0=25, segs=12, mat="Aluminum_Cast")
    m.add_cylinder(r0=20, r1=20, h=4, z0=45, segs=12, mat="Gasket_Black")
    # Dual brass cam arms
    m.add_box(size=(8, 18, 30), center=(-28, 0, 26), mat="Brass_Arm")
    m.add_box(size=(8, 18, 30), center=( 28, 0, 26), mat="Brass_Arm")
    m.add_torus(r_major=6, r_minor=2, segs_major=8, segs_minor=4, z0=12, mat="Brass_Arm", c=(-28, 0))
    m.add_torus(r_major=6, r_minor=2, segs_major=8, segs_minor=4, z0=12, mat="Brass_Arm", c=( 28, 0))
    return m

def build_pump_macerator_waste():
    m = Mesh("pump_macerator_waste")
    m.add_material("Motor_Black", 0.22, 0.22, 0.24)
    m.add_material("Head_Blue", 0.18, 0.44, 0.78)
    m.add_material("Brass_Outlet", 0.86, 0.68, 0.24)
    # Cylindrical 12V motor
    m.add_cylinder(r0=18, r1=18, h=45, z0=0, segs=10, mat="Motor_Black")
    # Macerator cutter pump head
    m.add_cylinder(r0=22, r1=22, h=30, z0=45, segs=12, mat="Head_Blue")
    # 3" RV waste bayonet inlet flange
    m.add_cylinder(r0=26, r1=26, h=12, z0=75, segs=12, mat="Head_Blue")
    # Garden hose discharge port on side
    m.add_cylinder(r0=6, r1=6, h=18, z0=55, segs=8, mat="Brass_Outlet", c0=(0, 22), c1=(0, 40))
    return m

def build_treatment_septic_packets():
    m = Mesh("treatment_septic_packets")
    m.add_material("Box_Cardboard", 0.82, 0.65, 0.42)
    m.add_material("Label_Green", 0.22, 0.58, 0.30)
    m.add_material("Packet_Foil", 0.88, 0.90, 0.92)
    # Retail packet box
    m.add_box(size=(48, 36, 60), center=(0, 0, 30), mat="Box_Cardboard")
    m.add_box(size=(50, 28, 42), center=(0, 0, 30), mat="Label_Green")
    # Packets spilling out
    m.add_box(size=(22, 14, 4), center=(15, 20, 15), mat="Packet_Foil")
    m.add_box(size=(22, 14, 4), center=(-12, 22, 8), mat="Packet_Foil")
    return m

def build_aerator_septic_air_pump():
    m = Mesh("aerator_septic_air_pump")
    m.add_material("Cast_Housing", 0.72, 0.74, 0.76)
    m.add_material("Base_Black", 0.20, 0.20, 0.22)
    m.add_material("Nozzle_Brass", 0.86, 0.68, 0.24)
    # Aluminum pump body with cooling fins
    m.add_box(size=(56, 42, 34), center=(0, 0, 22), mat="Cast_Housing")
    m.add_box(size=(58, 44, 4), center=(0, 0, 38), mat="Cast_Housing")
    # Rubber isolation vibration feet
    for x in [-22, 22]:
        for y in [-16, 16]:
            m.add_cylinder(r0=5, r1=5, h=6, z0=0, segs=6, mat="Base_Black", c0=(x, y), c1=(x, y))
    # Air outlet barb
    m.add_cylinder(r0=6, r1=5, h=14, z0=22, segs=8, mat="Nozzle_Brass", c0=(28, 0), c1=(42, 0))
    return m

def build_bin_compost_3bay():
    m = Mesh("bin_compost_3bay")
    m.add_material("Cedar_Wood", 0.72, 0.48, 0.28)
    m.add_material("Slats_Dark", 0.58, 0.38, 0.22)
    m.add_material("Compost_Soil", 0.25, 0.18, 0.14)
    # 3-bay compost bin framing
    m.add_box(size=(88, 46, 50), center=(0, 0, 25), mat="Cedar_Wood")
    # Interior compost pile visible
    m.add_box(size=(26, 38, 30), center=(-28, 0, 15), mat="Compost_Soil")
    m.add_box(size=(26, 38, 42), center=(0, 0, 21), mat="Compost_Soil")
    # Dividing posts
    for x in [-44, -15, 15, 44]:
        m.add_box(size=(6, 48, 54), center=(x, 0, 27), mat="Slats_Dark")
    return m

SEWAGE_BUILDERS = [
    ("tank_septic_poly_500gal", build_tank_septic_poly_500gal, "sewage", "drainage"),
    ("tank_septic_concrete_1000gal", build_tank_septic_concrete_1000gal, "sewage", "drainage"),
    ("tank_rv_waste_tote", build_tank_rv_waste_tote, "sewage", "waste"),
    ("toilet_composting_rustic", build_toilet_composting_rustic, "sewage", "treatment"),
    ("pipe_sewer_solid_4inch", build_pipe_sewer_solid_4inch, "sewage", "drainage"),
    ("pipe_leach_perforated_4inch", build_pipe_leach_perforated_4inch, "sewage", "drainage"),
    ("box_distribution_septic", build_box_distribution_septic, "sewage", "drainage"),
    ("riser_septic_lid", build_riser_septic_lid, "sewage", "drainage"),
    ("drain_french_sock", build_drain_french_sock, "sewage", "drainage"),
    ("hose_sewer_rv_10ft", build_hose_sewer_rv_10ft, "sewage", "waste"),
    ("hose_sewer_rv_20ft", build_hose_sewer_rv_20ft, "sewage", "waste"),
    ("fitting_camlock_coupler", build_fitting_camlock_coupler, "sewage", "waste"),
    ("pump_macerator_waste", build_pump_macerator_waste, "sewage", "waste"),
    ("treatment_septic_packets", build_treatment_septic_packets, "sewage", "treatment"),
    ("aerator_septic_air_pump", build_aerator_septic_air_pump, "sewage", "treatment"),
    ("bin_compost_3bay", build_bin_compost_3bay, "sewage", "treatment"),
]

