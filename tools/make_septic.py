#!/usr/bin/env python3
"""
make_septic.py
Builds, in code (no paid generation), the sewage system (docs/SEPTIC.md):

  structures (buried; only their risers and lids, or the mounded lines, show above the ground), three stages each (excavate, set, backfill):
    waste_septic_tank_concrete   precast concrete septic tank (3800 L)
    waste_septic_tank_poly       ribbed poly septic tank (1900 L)
    waste_leach_field_small      a leach field of two gravel trenches
    waste_leach_field_large      a leach field of four gravel trenches
  items:
    pipe_abs_waste_three_inch    black 3" waste pipe (wire_kind sewer), 3 m a length
    waste_outlet_house           the building's waste outlet: through the wall, like the water inlet (wire_role sewer_outlet)
    waste_pump_macerator         the macerator pump (wire_role sewer_pump), stands on the floor inside
    waste_box_distribution_septic  the distribution box: its lid at the ground (wire_role septic_dbox)
    waste_riser_septic_lid       a riser ring and lid (the tank stage asks for two)
    appliance_toilet_flush       a flush toilet, and models for the sinks, the shower stall, the washers and the dishwashers (the fixtures: they use water
                                 and send it down the drain)
  the honey pot truck is tools/make_septic_truck.py; its service (waste_service_septic_pumpout) is written here.

Run:  python tools/make_septic.py [--install]
"""
import copy
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "assets")
STRUCT = os.path.join(A, "structures")
WORK = os.path.join(A, "_scratch", "septic")

SHOVELS = ["tool_shovel", "tool_shovel_round_point", "tool_shovel_trenching", "tool_pickaxe"]
SAWS = ["tool_saw_hand", "tool_circular_saw_corded", "tool_circular_saw_cordless", "tool_miter_saw"]
WRENCHES = ["tool_wrench_pipe", "tool_wrench_adjustable"]
RAKES = ["tool_rake_garden", "tool_rake_leaf", "tool_hoe"] + SHOVELS
STAGES = ["excavate", "set", "backfill"]
AGES = [(0, 33), (33, 66), (66, 100)]

# id: (name, kind, width, depth, capacity L or (absorb L/day, storage L), price, description)
TANKS = {
    "waste_septic_tank_concrete": ("Septic Tank (Concrete)", "concrete", 2.4, 3.2, 3800, 1450,
                                   "A precast concrete septic tank, buried with two green risers and lids showing just above the ground for the cleanout. Pipe a building's "
                                   "waste outlet to it with black waste pipe (a macerator pump on the way is optional); pipe it on to a distribution box and leach fields. "
                                   "Solids settle and build up in it: order a pump-out in the Tank You app before it fills."),
    "waste_septic_tank_poly": ("Septic Tank (Poly)", "poly", 2.0, 2.6, 1900, 1100,
                               "A ribbed poly septic tank, buried with two green risers and lids showing just above the ground for the cleanout. Pipe a building's waste "
                               "outlet to it with black waste pipe (a macerator pump on the way is optional); pipe it on to a distribution box and leach fields. Solids "
                               "settle and build up in it: order a pump-out in the Tank You app before it fills."),
}
FIELDS = {
    "waste_leach_field_small": ("Small Leach Field", 2, 4.0, 10.0, (500, 1200), 180,
                                "Two gravel trenches with perforated pipe, buried: the liquid from a septic tank soaks away into the ground here. Pipe it from a distribution "
                                "box. It takes so much a day; more than that and the system backs up."),
    "waste_leach_field_large": ("Large Leach Field", 4, 7.0, 14.0, (1200, 3000), 320,
                                "Four gravel trenches with perforated pipe, buried: the liquid from a septic tank soaks away into the ground here. Pipe it from a distribution "
                                "box. It takes so much a day; more than that and the system backs up."),
}
PIPE = "pipe_abs_waste_three_inch"
OUTLET = "waste_outlet_house"
MACERATOR = "waste_pump_macerator"
DBOX = "waste_box_distribution_septic"
RISER = "waste_riser_septic_lid"
TOILET = "appliance_toilet_flush"
SERVICE = "waste_service_septic_pumpout"
FIXTURES = ["appliance_sink_budget", "appliance_sink_premium", "appliance_shower_stall", "appliance_washer_budget", "appliance_washer_premium",
            "appliance_dishwasher_budget", "appliance_dishwasher_premium", TOILET]
# liters one use of a fixture takes (and sends down the drain)
PER_USE = {"appliance_sink_budget": 4, "appliance_sink_premium": 4, "appliance_shower_stall": 60, "appliance_washer_budget": 120, "appliance_washer_premium": 50,
           "appliance_dishwasher_budget": 20, "appliance_dishwasher_premium": 12, TOILET: 6}
OLD = ["waste_tank_septic_concrete_3800l", "waste_tank_septic_poly_1900l"]


def stage_plan(kind, lines=2):
    if kind in ("concrete", "poly"):
        return [
            ([], [SHOVELS], ["Dig", "Hoe"]),
            ([{"item_id": "~bedding_stone", "quantity": 0.6 if kind == "concrete" else 0.4},
              {"item_id": RISER, "quantity": 2},
              {"item_id": "~pipe_sewer_solid_4inch", "quantity": 2},
              {"item_id": "~pvc_cement_can", "quantity": 1}], [SHOVELS, SAWS], ["Fixing_Kneeling_RT", "Dig"]),
            ([], [SHOVELS], ["Dig", "Hoe"]),
        ]
    gravel = 0.75 * lines
    return [
        ([], [SHOVELS], ["Dig", "Hoe"]),
        ([{"item_id": "~gravel", "quantity": gravel},
          {"item_id": "~pipe_leach_perforated_4inch", "quantity": 3 * lines if lines <= 2 else 4 * lines},
          {"item_id": "~pipe_sewer_solid_4inch", "quantity": lines},
          {"item_id": "~pvc_cement_can", "quantity": 1}], [SHOVELS, SAWS], ["Fixing_Kneeling_RT", "Dig"]),
        ([], [RAKES], ["Dig", "Hoe"]),
    ]


# ------------------------------------------------------------------ Blender

def blender_main(out_dir):
    import math
    import random
    import bpy
    from mathutils import Matrix
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import make_simple_props as props

    T = Matrix.Translation
    results = {}

    def reset():
        bpy.ops.wm.read_factory_settings(use_empty=True)

    def M(name, rgb, rough=0.6):
        return props.mat(name, rgb, rough)

    def tris():
        return sum(len(p.vertices) - 2 for o in bpy.context.scene.objects if o.type == 'MESH' for p in o.data.polygons)

    def export(key):
        bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, key + ".glb"), export_format='GLB', use_selection=False, export_apply=True, export_yup=True)
        results[key] = tris()

    def soil_mats():
        return (M("Spoil", (0.36, 0.27, 0.18), 0.95), M("Hole", (0.12, 0.09, 0.06), 1.0), M("Backfill", (0.33, 0.3, 0.2), 0.95))

    def berm(K, size, at, m, seed):
        K.rock(size, m, random.Random(seed), 0.18, 2, at)

    def lid(K, x, y, top, green, dark):
        # a green riser ring and its ribbed lid, the top `top` above the ground
        K.lathe([(0.31, 0.0), (0.31, top - 0.02), (0.3, top), (0.0, top)], green, 20, T((x, y, 0)))   # (nothing below the ground: the game sets the model's lowest point on it)
        for k in range(6):
            a = math.pi * k / 6
            K.bx((0.5, 0.025, 0.012), (x, y, top + 0.004), green, Matrix.Rotation(a, 4, 'Z'))
        K.bx((0.06, 0.03, 0.015), (x + 0.2, y, top + 0.006), dark)       # a screw lock

    # ---------------------------------------------------------------- the septic tanks
    for tid, (_n, kind, W, D, cap, _p, _d) in TANKS.items():
        for si in range(3):
            reset()
            spoil, hole, back = soil_mats()
            green = M("LidGreen", (0.12, 0.38, 0.16), 0.55)
            dark = M("Dark", (0.08, 0.08, 0.09), 0.6)
            conc = M("Concrete", (0.62, 0.61, 0.58), 0.9)
            poly = M("PolyTank", (0.1, 0.1, 0.11), 0.6)
            stone = M("BeddingStone", (0.55, 0.54, 0.5), 0.95)
            K = props.Kit()
            tw, td = W - 0.5, D - 0.6
            ly = td * 0.3
            if si < 2:
                K.bx((tw + 0.2, td + 0.2, 0.01), (0, 0, 0.005), hole)                      # the pit
                berm(K, (0.7, D * 0.9, 0.55), (W / 2 + 0.05, 0), spoil, 3)
                berm(K, (0.6, D * 0.7, 0.45), (-W / 2 - 0.05, 0.2), spoil, 4)
            if si == 1:
                # the tank down in the pit: its top just below the ground, the risers on it, bedding stone round it
                K.bx((tw + 0.16, td + 0.16, 0.012), (0, 0, 0.012), stone)
                if kind == "concrete":
                    K.bx((tw, td, 0.03), (0, 0, 0.015), conc)
                else:
                    for k in range(7):
                        K.bx((tw * 0.92, 0.1, 0.03), (0, -td / 2 + td * (k + 0.5) / 7, 0.015), poly)
                for y in (-ly, ly):
                    lid(K, 0, y, 0.12, green, dark)
                K.tube((0, -td / 2 - 0.1, 0.056), (0, -td / 2 + 0.05, 0.056), 0.055, 0.055, dark, 10, dark, dark)   # the inlet tee's stub
                K.tube((0, td / 2 - 0.05, 0.056), (0, td / 2 + 0.1, 0.056), 0.055, 0.055, dark, 10, dark, dark)     # the outlet's
            if si == 2:
                # backfilled: a low mound of fresh soil, the two risers and lids just above the ground
                K.lathe([(0.0, 0.07), (0.5, 0.065), (0.85, 0.04), (1.0, 0.0)], back, 16, T((0, 0, 0)) @ Matrix.Scale(W / 2, 4, (1, 0, 0)) @ Matrix.Scale(D / 2, 4, (0, 1, 0)))
                for y in (-ly, ly):
                    lid(K, 0, y, 0.12, green, dark)
            K.done("Tank")
            export("%s_%d" % (tid, si + 1))

    # ---------------------------------------------------------------- the leach fields
    for fid, (_n, lines, W, D, _cap, _p, _d) in FIELDS.items():
        for si in range(3):
            reset()
            spoil, hole, back = soil_mats()
            gravel = M("Gravel", (0.5, 0.49, 0.46), 0.95)
            white = M("PipeWhite", (0.9, 0.9, 0.87), 0.5)
            green = M("PipeGreen", (0.25, 0.45, 0.25), 0.5)
            cap = M("PortCap", (0.85, 0.85, 0.82), 0.5)
            K = props.Kit()
            L = D - 1.2
            xs = [-W / 2 + W * (k + 0.5) / lines for k in range(lines)]
            for k, x in enumerate(xs):
                if si == 0:
                    K.bx((0.6, L, 0.01), (x, 0.3, 0.005), hole)
                    berm(K, (0.35, L * 0.95, 0.3), (x + 0.5 if x < W / 2 - 0.8 else x - 0.5, 0.3), spoil, 10 + k)
                elif si == 1:
                    K.bx((0.6, L, 0.01), (x, 0.3, 0.005), hole)
                    K.bx((0.56, L - 0.04, 0.03), (x, 0.3, 0.015), gravel)
                    K.tube((x, 0.3 - L / 2, 0.08), (x, 0.3 + L / 2, 0.08), 0.05, 0.05, white, 10, white, white)
                else:
                    K.bx((0.7, L, 0.04), (x, 0.3, 0.02), back)
                    K.lathe([(0.05, 0.0), (0.05, 0.14), (0.065, 0.14), (0.065, 0.17), (0.0, 0.18)], cap, 10, T((x, 0.3 + L / 2 - 0.3, 0)))   # an inspection port
            # the header from the distribution box across the front of the lines
            if si == 1:
                K.tube((xs[0], 0.3 - L / 2, 0.08), (xs[-1], 0.3 - L / 2, 0.08), 0.052, 0.052, green, 10, green, green)
                K.tube((0, -D / 2 + 0.1, 0.08), (0, 0.3 - L / 2, 0.08), 0.052, 0.052, green, 10, green, green)
            K.done("Field")
            export("%s_%d" % (fid, si + 1))

    # ---------------------------------------------------------------- the pipe (lies along x, on the ground)
    reset()
    black = M("ABS", (0.04, 0.04, 0.045), 0.45)
    r = 0.045
    K = props.Kit()
    K.tube((-1.5, 0, r), (1.5, 0, r), r, r, black, 12, black, black)
    K.tube((1.38, 0, r), (1.5, 0, r), r * 1.18, r * 1.18, black, 12, black, black)   # the bell
    K.done(PIPE)
    export(PIPE)

    # ---------------------------------------------------------------- the waste outlet (through the wall: Plate, Pipe, Riser)
    reset()
    black = M("ABS", (0.04, 0.04, 0.045), 0.45)
    plate = M("Bracket", (0.12, 0.12, 0.13), 0.55)
    capm = M("CleanoutCap", (0.75, 0.74, 0.7), 0.5)
    r = 0.045
    cz = 0.4
    P = props.Kit()
    P.bx((0.2, 0.008, 0.2), (0, -0.004, cz), plate)
    P.tube((0, -0.008, cz), (0, -0.09, cz), r, r, black, 12)                            # out of the wall
    P.tube((0, -0.12, cz - 0.05), (0, -0.12, cz + 0.12), r * 1.15, r * 1.15, black, 12, black, None)   # the cleanout tee
    P.lathe([(r * 1.2, cz + 0.12), (r * 1.2, cz + 0.15), (0.0, cz + 0.155)], capm, 12, T((0, -0.12, 0)))
    P.bx((0.03, 0.03, 0.012), (0, -0.12, cz + 0.16), capm)
    P.done("Plate")
    S = props.Kit()
    S.tube((0, 0.0, cz), (0, 0.04, cz), r * 1.2, r * 1.2, black, 12, black, black)   # only the stub into the wall: the outlet shows on the outside alone
    S.done("Pipe")
    R = props.Kit()
    R.tube((0, -0.12, 0.0), (0, -0.12, cz - 0.05), r, r, black, 12, black)               # down into the ground
    R.bx((0.08, 0.1, 0.014), (0, -0.06, cz * 0.45), plate)                               # a strap to the wall
    R.done("Riser")
    export(OUTLET)

    # ---------------------------------------------------------------- the macerator pump (stands on the floor; inlet at the side, outlet up)
    reset()
    whiteP = M("PumpBody", (0.9, 0.9, 0.88), 0.45)
    grey = M("Motor", (0.45, 0.47, 0.5), 0.4)
    black = M("ABS", (0.04, 0.04, 0.045), 0.45)
    K = props.Kit()
    K.bx((0.46, 0.3, 0.26), (0, 0, 0.13), whiteP)
    K.bx((0.48, 0.32, 0.02), (0, 0, 0.27), whiteP)
    K.tube((0.08, 0, 0.28), (0.08, 0, 0.42), 0.075, 0.075, grey, 14, None, grey)        # the motor
    K.tube((-0.14, 0, 0.28), (-0.14, 0, 0.42), 0.02, 0.02, black, 8, None, black)       # the discharge
    K.tube((-0.23, 0, 0.12), (-0.3, 0, 0.12), 0.05, 0.05, black, 12, None, black)       # the inlet
    K.bx((0.08, 0.02, 0.06), (0.1, -0.16, 0.18), grey)                                  # its switch box
    K.done(MACERATOR)
    export(MACERATOR)

    # ---------------------------------------------------------------- the distribution box (its lid at the ground)
    reset()
    conc = M("Concrete", (0.6, 0.59, 0.56), 0.9)
    dark = M("Dark", (0.1, 0.1, 0.11), 0.6)
    K = props.Kit()
    K.bx((0.56, 0.46, 0.05), (0, 0, 0.025), conc)
    K.bx((0.5, 0.4, 0.015), (0, 0, 0.055), conc)
    K.bx((0.14, 0.03, 0.02), (0, 0, 0.07), dark)                                        # the lifting handle
    K.done(DBOX)
    export(DBOX)

    # ---------------------------------------------------------------- a riser and lid (loose, as bought)
    reset()
    green = M("LidGreen", (0.12, 0.38, 0.16), 0.55)
    dark = M("Dark", (0.08, 0.08, 0.09), 0.6)
    K = props.Kit()
    K.lathe([(0.31, 0.0), (0.31, 0.28), (0.3, 0.3), (0.0, 0.3)], green, 20)
    for k in range(6):
        K.bx((0.5, 0.025, 0.012), (0, 0, 0.304), green, Matrix.Rotation(math.pi * k / 6, 4, 'Z'))
    K.bx((0.06, 0.03, 0.015), (0.2, 0, 0.306), dark)
    K.done(RISER)
    export(RISER)

    # ---------------------------------------------------------------- the fixtures (placed on the floor, the front towards -y)
    def toilet():
        china = M("China", (0.95, 0.95, 0.93), 0.25)
        chrome = M("Chrome", (0.8, 0.81, 0.83), 0.15)
        K = props.Kit()
        K.lathe([(0.11, 0.0), (0.13, 0.12), (0.18, 0.3), (0.19, 0.4), (0.0, 0.4)], china, 18, T((0, -0.06, 0)) @ Matrix.Scale(1.25, 4, (0, 1, 0)))
        K.lathe([(0.2, 0.0), (0.2, 0.02), (0.0, 0.02)], china, 18, T((0, -0.06, 0.4)) @ Matrix.Scale(1.25, 4, (0, 1, 0)))   # the seat
        K.bx((0.4, 0.18, 0.36), (0, 0.17, 0.58), china)                                 # the tank
        K.bx((0.42, 0.2, 0.03), (0, 0.17, 0.775), china)
        K.bx((0.05, 0.02, 0.015), (-0.14, 0.07, 0.72), chrome)                          # the handle
        return K.done(TOILET)

    def sink(premium):
        china = M("China", (0.95, 0.95, 0.93), 0.25)
        chrome = M("Chrome", (0.8, 0.81, 0.83), 0.15)
        wood = M("Vanity", (0.42, 0.3, 0.2), 0.6)
        top = M("Counter", (0.85, 0.84, 0.8), 0.3)
        K = props.Kit()
        if premium:
            K.bx((0.6, 0.5, 0.8), (0, 0.02, 0.4), wood)
            K.bx((0.27, 0.01, 0.6), (-0.14, -0.235, 0.38), wood)
            K.bx((0.27, 0.01, 0.6), (0.14, -0.235, 0.38), wood)
            K.bx((0.64, 0.54, 0.04), (0, 0.02, 0.82), top)
            K.lathe([(0.18, 0.0), (0.15, -0.12), (0.0, -0.13)], china, 16, T((0, -0.02, 0.84)))
        else:
            K.lathe([(0.1, 0.0), (0.07, 0.15), (0.06, 0.6), (0.08, 0.68)], china, 14, T((0, 0.04, 0)))
            K.bx((0.56, 0.42, 0.16), (0, 0.04, 0.76), china)
        K.tube((0, 0.18, 0.84), (0, 0.18, 1.0), 0.015, 0.015, chrome, 8, None, chrome)
        K.path([(0, 0.18, 1.0), (0, 0.1, 1.02), (0, 0.04, 0.96)], 0.012, chrome, 8)
        K.bx((0.04, 0.03, 0.03), (0.1, 0.18, 0.88), chrome)
        return K.done("Sink")

    def shower():
        white = M("ShowerWall", (0.93, 0.93, 0.9), 0.3)
        chrome = M("Chrome", (0.8, 0.81, 0.83), 0.15)
        K = props.Kit()
        K.bx((0.9, 0.9, 0.08), (0, 0, 0.04), white)
        K.bx((0.9, 0.03, 1.95), (0, 0.435, 1.0), white)
        K.bx((0.03, 0.9, 1.95), (-0.435, 0, 1.0), white)
        K.bx((0.03, 0.9, 1.95), (0.435, 0, 1.0), white)
        K.bx((0.9, 0.02, 0.02), (0, -0.44, 1.96), chrome)                                # the curtain rail across the open front
        K.tube((0.0, 0.42, 1.75), (0.0, 0.32, 1.85), 0.012, 0.012, chrome, 8)
        K.lathe([(0.0, 0.0), (0.06, 0.0), (0.04, 0.03)], chrome, 12, T((0.0, 0.31, 1.83)) @ Matrix.Rotation(math.pi, 4, 'X'))
        K.bx((0.06, 0.03, 0.1), (0.0, 0.41, 1.1), chrome)
        return K.done("Shower")

    def washer(front):
        white = M("Enamel", (0.93, 0.93, 0.92), 0.3)
        dark = M("DoorGlass", (0.12, 0.14, 0.17), 0.1)
        grey = M("Panel", (0.6, 0.62, 0.65), 0.4)
        K = props.Kit()
        K.bx((0.68, 0.66, 0.9), (0, 0, 0.45), white)
        K.bx((0.68, 0.12, 0.14), (0, 0.27, 0.97), white)                                # the control panel
        K.bx((0.4, 0.01, 0.06), (0, 0.205, 0.99), grey)
        if front:
            K.lathe([(0.0, 0.0), (0.2, 0.0), (0.22, 0.02), (0.0, 0.03)], dark, 18, T((0, -0.33, 0.48)) @ Matrix.Rotation(math.pi / 2, 4, 'X'))
        else:
            K.bx((0.5, 0.5, 0.01), (0, -0.04, 0.905), grey)                                # the top lid
        return K.done("Washer")

    def dishwasher(steel):
        body = M("Steel" if steel else "Enamel", (0.72, 0.73, 0.75) if steel else (0.93, 0.93, 0.92), 0.25 if steel else 0.3)
        dark = M("Dark", (0.1, 0.1, 0.11), 0.5)
        K = props.Kit()
        K.bx((0.6, 0.58, 0.85), (0, 0.01, 0.425), body)
        K.bx((0.6, 0.02, 0.1), (0, -0.29, 0.79), dark)                                  # the control strip
        K.tube((-0.22, -0.32, 0.72), (0.22, -0.32, 0.72), 0.012, 0.012, body, 8, body, body)   # the handle
        return K.done("Dishwasher")

    for fx, fn in ((TOILET, toilet), ("appliance_sink_budget", lambda: sink(False)), ("appliance_sink_premium", lambda: sink(True)),
                   ("appliance_shower_stall", shower), ("appliance_washer_budget", lambda: washer(False)), ("appliance_washer_premium", lambda: washer(True)),
                   ("appliance_dishwasher_budget", lambda: dishwasher(False)), ("appliance_dishwasher_premium", lambda: dishwasher(True))):
        reset()
        fn()
        export(fx)

    with open(os.path.join(out_dir, "tris.txt"), "w") as f:
        for k, v in results.items():
            f.write("%s %d\n" % (k, v))


# ------------------------------------------------------------------ install

def find_blender():
    for p in [shutil.which("blender"), r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"]:
        if p and os.path.exists(p):
            return p
    raise SystemExit("blender not found")


def retry(fn, *a):
    for _ in range(8):
        try:
            return fn(*a)
        except OSError:
            time.sleep(0.5)
    return fn(*a)


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def write_json(p, d, crlf=True):
    text = json.dumps(d, indent=2, ensure_ascii=False) + "\n"
    if crlf:
        text = text.replace("\n", "\r\n")
    retry(lambda: open(p, "wb").write(text.encode("utf-8")))


def render_icon(glb, png):
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "render_icon_from_model.py"), glb, png], check=True, capture_output=True)


def readme(d, title, item_id, cat, desc):
    retry(lambda: open(os.path.join(d, "README.md"), "w", encoding="utf-8", newline="").write(
        "# %s\n\n**Item ID:** `%s`  \n**Category:** `%s`  \n**Icon:** ![%s](%s.png)\n\n%s\n\nProcedural model (tools/make_septic.py). See docs/SEPTIC.md.\n" % (title, item_id, cat, title, item_id, desc)))


def clean(d, keep):
    for f in os.listdir(d):
        if f.endswith((".obj", ".mtl")) or (f.endswith(".glb") and f != keep):
            os.remove(os.path.join(d, f))


def model_entry(item, dims, tris):
    return [{"file": item + ".glb", "format": "glb", "dimensions_m": {"x": dims[0], "y": dims[2], "z": dims[1]}, "triangles": int(tris)}]


def item(cat, item_id, template, name, desc, props, dims, tris, out, cf=None, src_glb=None):
    """Writes (or updates) an item: its model, icon, manifest and README. A new item copies the template's manifest."""
    d = os.path.join(A, cat, item_id)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, item_id + ".json")
    m = load(p) if os.path.exists(p) else copy.deepcopy(load(template))
    m["id"] = item_id
    m["category"] = cat
    m["icon"] = item_id + ".png"
    if name:
        m["name"] = name
    if desc:
        m["description"] = desc
    m.setdefault("properties", {}).update(props)
    for k in ("liquid_container",):
        if k in props:
            m[k] = props.pop(k)
    if cf:
        m.setdefault("category_fields", {}).update(cf)
    if dims is not None:
        m["models"] = model_entry(item_id, dims, tris)
        m.setdefault("category_fields", {})["dimensions_m"] = {"width": dims[0], "depth": dims[1], "height": dims[2]}
        clean(d, item_id + ".glb")
        retry(shutil.copy, os.path.join(out, (src_glb or item_id) + ".glb"), os.path.join(d, item_id + ".glb"))
        render_icon(os.path.join(d, item_id + ".glb"), os.path.join(d, item_id + ".png"))
    write_json(p, m)
    readme(d, m["name"], item_id, cat, m["description"])
    print("item", item_id)
    return m


def structure(sid, name, desc, price, W, D, heights, plan, tris, out, props):
    well = load(os.path.join(STRUCT, "water_well_concrete", "water_well_concrete.json"))
    stage_tpl = load(os.path.join(STRUCT, "water_well_concrete", "stages", "struct_wellhead", "struct_wellhead_water_well_concrete.json"))
    gdir = os.path.join(STRUCT, sid)
    group = copy.deepcopy(well)
    group["id"] = sid
    group["name"] = name
    group["icon"] = sid + ".png"
    group["description"] = desc
    gp = group["properties"]
    for k in ("attach_item", "is_well"):
        gp.pop(k, None)
    gp["base_value"] = price
    gp["is_buyable"] = True
    gp["stores"] = ["depot"]
    gp.update(props)
    g = group["growth"]
    g["species"] = sid
    g["stages"] = []
    for i, stname in enumerate(STAGES):
        folder = "struct_" + stname
        item_id = "%s_%s" % (folder, sid)
        sdir = os.path.join(gdir, "stages", folder)
        os.makedirs(sdir, exist_ok=True)
        recipe, tools, clips = plan[i]
        sm = copy.deepcopy(stage_tpl)
        sm["id"] = item_id
        sm["name"] = "%s - %s" % (name, stname.capitalize())
        sm["description"] = "The %s phase of the %s." % (stname, name.lower())
        sm["icon"] = item_id + ".png"
        sm["properties"]["weight_kg"] = 50.0 * (i + 1)
        cf = sm["category_fields"]
        cf["dimensions_m"] = {"width": W, "depth": D, "height": heights[i]}
        cf["construction_recipe"] = copy.deepcopy(recipe)
        cf["required_tools"] = copy.deepcopy(tools)
        cf["build_clips"] = clips
        cf["build_motion"] = ""
        sm["models"] = [{"file": item_id + ".glb", "format": "glb", "dimensions_m": {"x": W, "y": heights[i], "z": D}, "triangles": int(tris["%s_%d" % (sid, i + 1)])}]
        clean(sdir, item_id + ".glb")
        retry(shutil.copy, os.path.join(out, "%s_%d.glb" % (sid, i + 1)), os.path.join(sdir, item_id + ".glb"))
        render_icon(os.path.join(sdir, item_id + ".glb"), os.path.join(sdir, item_id + ".png"))
        write_json(os.path.join(sdir, item_id + ".json"), sm)
        retry(lambda: open(os.path.join(sdir, "README.md"), "w", encoding="utf-8", newline="").write("# %s\n\nProcedural model (tools/make_septic.py).\n" % sm["name"]))
        g["stages"].append({"stage": i + 1, "name": stname, "age_min": AGES[i][0], "age_max": AGES[i][1], "resource": "stages/%s/" % folder, "model": "",
                            "icon": item_id + ".png", "construction_recipe": copy.deepcopy(recipe), "required_tools": copy.deepcopy(tools),
                            "build_clips": clips, "build_motion": ""})
    g["total_stages"] = 3
    g["icon_stage"] = 3
    g["max_age"] = 100
    write_json(os.path.join(gdir, sid + ".json"), group)
    retry(shutil.copy, os.path.join(gdir, "stages", "struct_backfill", "struct_backfill_%s.png" % sid), os.path.join(gdir, sid + ".png"))
    readme(gdir, name, sid, "structures", desc)
    kc_path = os.path.join(A, "kit_config.json")
    kc = load(kc_path)
    kc["subfolders"][sid] = {"name": name, "icon": "", "category": "structures"}
    kc["growth_groups"][sid] = {"name": name, "icon": "", "category": "structures", "growth_type": "percent", "max_age": 100, "time_unit": "percent",
                                "stages": [{"stage": i + 1, "name": n, "item_id": "struct_%s_%s" % (n, sid), "age_min": AGES[i][0], "age_max": AGES[i][1]} for i, n in enumerate(STAGES)]}
    write_json(kc_path, kc, crlf=False)
    print("structure", sid)


def install(out):
    tris = dict(l.split() for l in open(os.path.join(out, "tris.txt")).read().strip().splitlines())

    # ---------------------------------------------------------------- structures
    for sid, (name, kind, W, D, cap, price, desc) in TANKS.items():
        structure(sid, name, desc, price, W, D, [0.55, 0.35, 0.25], stage_plan(kind), tris, out, {"wire_role": "septic_tank", "sewage_capacity_l": cap})
    for fid, (name, lines, W, D, (lpd, store), price, desc) in FIELDS.items():
        structure(fid, name, desc, price, W, D, [0.35, 0.15, 0.2], stage_plan("field", lines), tris, out, {"wire_role": "leach_field", "leach_lpd": lpd, "leach_storage_l": store})

    # ---------------------------------------------------------------- items
    pipe_tpl = os.path.join(A, "building", "pipe_pvc_two_inch", "pipe_pvc_two_inch.json")
    m = item("building", PIPE, pipe_tpl, '3" Black Waste Pipe',
             "A 3 m length of black ABS waste pipe for a building's drain line. With a pipe wrench in hand, right click a building's waste outlet and then a macerator "
             "pump or a septic tank to lay it (and on from the tank to a distribution box and its leach fields). Outside it runs underground.",
             {"weight_kg": 2.2, "base_value": 14, "max_stack_size": 20, "placeable": True, "wire_kind": "sewer", "wire_length_m": 3, "is_buyable": True, "stores": ["depot"]},
             [3.0, 0.11, 0.11], tris[PIPE], out)
    m["properties"].pop("flow_lph", None)
    write_json(os.path.join(A, "building", PIPE, PIPE + ".json"), m)

    inlet_tpl = os.path.join(A, "water", "water_inlet_house", "water_inlet_house.json")
    item("waste", OUTLET, inlet_tpl, "Building Waste Outlet",
         "Takes a building's waste water out: a black drain pipe through the wall with a cleanout cap, going down into the ground. Mount it on the OUTSIDE of a "
         "building (left click a wall with it in hand); it shows on the outside only. Then pipe it to a septic tank with black waste pipe and a pipe wrench (a macerator "
         "pump inside the building on the way is optional). The sinks, toilets, showers and washers in the building drain through it.",
         {"weight_kg": 2.0, "base_value": 42, "max_stack_size": 5, "placeable": False, "wire_role": "sewer_outlet", "attach_surface": "wall", "attach_side": "exterior",
          "attach_through": False, "stores": ["depot"], "is_buyable": True},
         [0.2, 0.37, 0.56], tris[OUTLET], out)

    item("waste", MACERATOR, None, None,
         "A grinder pump that stands inside a building between its waste outlet and the septic tank: it grinds the solids fine, so the tank fills with sludge half as "
         "fast and needs pumping out less often. It runs on the building's power; without power nothing drains through it.",
         {"placeable": True, "wire_role": "sewer_pump", "is_buyable": True, "stores": ["depot"]},
         [0.6, 0.32, 0.42], tris[MACERATOR], out, cf={"power_draw_w": 500})

    item("waste", DBOX, None, None,
         "A concrete distribution box, buried with its lid at the ground: it splits the liquid from a septic tank evenly between the leach fields piped to it. Pipe "
         "the tank to it, then it to each leach field, with black waste pipe.",
         {"placeable": True, "wire_role": "septic_dbox", "is_buyable": True, "stores": ["depot"]},
         [0.56, 0.46, 0.08], tris[DBOX], out)

    item("waste", RISER, None, None,
         "A green riser ring and its locking lid: it brings a buried septic tank's access opening up to the ground for the cleanout. A septic tank takes two.",
         {"placeable": True, "is_buyable": True, "stores": ["depot"]},
         [0.62, 0.62, 0.31], tris[RISER], out)

    # ---------------------------------------------------------------- the fixtures: models, placeable, liters a use
    sink_tpl = os.path.join(A, "appliances", "appliance_sink_budget", "appliance_sink_budget.json")
    fdims = {TOILET: [0.42, 0.7, 0.8], "appliance_sink_budget": [0.56, 0.42, 1.02], "appliance_sink_premium": [0.64, 0.54, 1.02],
             "appliance_shower_stall": [0.9, 0.9, 1.97], "appliance_washer_budget": [0.68, 0.66, 1.04], "appliance_washer_premium": [0.68, 0.68, 1.04],
             "appliance_dishwasher_budget": [0.6, 0.62, 0.85], "appliance_dishwasher_premium": [0.6, 0.62, 0.85]}
    for fx in FIXTURES:
        new = fx == TOILET
        item("appliances", fx, sink_tpl, "Flush Toilet" if new else None,
             "A white flush toilet. Placed in a building that has water and a waste outlet piped to a septic tank, a right click flushes it." if new else None,
             {"placeable": True} if not new else {"placeable": True, "base_value": 180, "weight_kg": 30.0, "is_buyable": True, "stores": ["furniture"]},
             fdims[fx], tris[fx], out, cf=dict({"water_per_use_l": PER_USE[fx]}, **({"water_usage_lpm": 0, "power_draw_w": 0} if new else {})))

    # ---------------------------------------------------------------- the pump-out service (Tank You)
    svc_tpl = os.path.join(A, "fuel", "fuel_service_tank_pickup", "fuel_service_tank_pickup.json")
    sd = os.path.join(A, "waste", SERVICE)
    os.makedirs(sd, exist_ok=True)
    m = copy.deepcopy(load(svc_tpl))
    m.update({"id": SERVICE, "category": "waste", "icon": SERVICE + ".png", "name": "Septic Pump-Out",
              "description": "The honey pot truck comes the next morning and pumps out one of your septic tanks: the sludge and the liquid, the fullest tank first. Order "
                             "one pump-out for each tank."})
    m["properties"].update({"base_value": 325, "stores": ["water"], "is_buyable": True, "max_stack_size": 9})
    write_json(os.path.join(sd, SERVICE + ".json"), m)
    truck_png = os.path.join(A, "vehicles", "vehicle_septic_pump_truck", "vehicle_septic_pump_truck.png")
    if os.path.exists(truck_png):
        retry(shutil.copy, truck_png, os.path.join(sd, SERVICE + ".png"))
    readme(sd, m["name"], SERVICE, "waste", m["description"])

    # ---------------------------------------------------------------- the pipe is an equivalency of its own
    ep = os.path.join(A, "_schemas", "equivalencies.json")
    eq = load(ep)
    eq["equivalencies"]["pipe_abs_waste_three_inch"] = {"unit": "pcs", "label": '3" Black Waste Pipe', "members": [{"item": PIPE, "value": 1}]}
    write_json(ep, eq, crlf=False)

    # ---------------------------------------------------------------- the old septic tank items (they are structures now)
    trash = os.path.join(A, "_trash")
    for old in OLD:
        d = os.path.join(A, "waste", old)
        if os.path.isdir(d):
            dst = os.path.join(trash, old)
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            shutil.move(d, dst)
            print("retired", old)


def main():
    if "--blender" in sys.argv:
        blender_main(sys.argv[sys.argv.index("--") + 1])
        return
    out = os.path.join(WORK, "glb")
    os.makedirs(out, exist_ok=True)
    tt = os.path.join(out, "tris.txt")
    if os.path.exists(tt):
        os.remove(tt)
    r = subprocess.run([find_blender(), "--background", "--python", os.path.abspath(__file__), "--", out, "--blender"], capture_output=True, text=True)
    if not os.path.exists(tt):
        print((r.stdout + r.stderr)[-3000:])
        return
    print(open(tt).read())
    if "--install" in sys.argv:
        install(out)
        print("installed")


if __name__ == "__main__":
    main()
