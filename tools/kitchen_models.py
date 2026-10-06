"""
The kitchen pack's models (tools/kitchen_lib.py builds them, tools/make_kitchen_assets.py lists and exports them). Each function takes a finish and returns a Mesh.

Everything is metres, centred on x and y, bottom at z = 0, FRONT = -Y (the side you open the door on). A WALL item (wall cabinet, hood, shelf, rack) is built the same way and then slid
back so its back is the plane y = 0 (the kit's wall-item convention). Low poly (a few hundred to a few thousand triangles) but with real detail: rounded edges, proud doors with a
dark seam, handles on posts, knobs, burners and grates, shaker panels.

Finishes: the appliance functions take one of the three appliance finishes (kitchen_lib.finishes(): stainless, white, black); cabinets, tables and chairs take a wood / paint finish (CAB below).
"""
import math

from kitchen_lib import Mesh, material

# ------------------------------------------------------------------ shared parts


def handle_bar(K, x, y, z0, z1, m, out=0.035, r=0.008):
    """A vertical bar handle on two posts, standing out from the face at depth y (the face is at y, standing out towards -y)."""
    K.cyl((x, y, z0 + 0.03), (x, y - out, z0 + 0.03), r * 0.9, m, seg=8)
    K.cyl((x, y, z1 - 0.03), (x, y - out, z1 - 0.03), r * 0.9, m, seg=8)
    K.cyl((x, y - out, z0), (x, y - out, z1), r, m, seg=10)


def handle_bar_h(K, x0, x1, y, z, m, out=0.035, r=0.008):
    """A horizontal bar handle on two posts."""
    K.cyl((x0 + 0.03, y, z), (x0 + 0.03, y - out, z), r * 0.9, m, seg=8)
    K.cyl((x1 - 0.03, y, z), (x1 - 0.03, y - out, z), r * 0.9, m, seg=8)
    K.cyl((x0, y - out, z), (x1, y - out, z), r, m, seg=10)


def knob(K, x, y, z, F, r=0.016, out=0.03):
    """A control knob on a front face at depth y: a dark skirt, a chrome cap and a pointer."""
    K.cyl((x, y, z), (x, y - out * 0.55, z), r, F.rubber, seg=14, r1=r * 0.95)
    K.cyl((x, y - out * 0.55, z), (x, y - out, z), r * 0.8, F.chrome, seg=14, r1=r * 0.7)
    K.box(x - 0.0015, x + 0.0015, y - out - 0.0005, y - out * 0.6, z + r * 0.15, z + r * 0.75, F.rubber)


def dial(K, x, y, z, F, r=0.02):
    """A flat round dial."""
    K.cyl((x, y, z), (x, y - 0.018, z), r, F.black, seg=16)
    K.cyl((x, y - 0.018, z), (x, y - 0.022, z), r * 0.8, F.chrome, seg=16)


def feet(K, xs, ys, m, h=0.025, r=0.018):
    for x in xs:
        for y in ys:
            K.cyl((x, y, 0.0), (x, y, h), r, m, seg=10)


# ------------------------------------------------------------------ refrigeration

def fridge_top(F):
    """A top-freezer refrigerator, 0.70 x 0.70 x 1.75 m."""
    K = Mesh('kitchen_fridge_top')
    w, d, h = 0.70, 0.70, 1.75
    x0, x1 = -w / 2, w / 2
    yf = -d / 2
    K.rbox(x0, x1, yf + 0.01, d / 2, 0.06, h - 0.005, F.body, 0.03, rv=0.012, seg=3)
    K.box(x0 + 0.03, x1 - 0.03, yf + 0.02, d / 2 - 0.05, 0.0, 0.07, F.rubber)
    feet(K, (x0 + 0.05, x1 - 0.05), (yf + 0.08,), F.rubber, 0.06, 0.022)
    zs = 1.19
    K.box(x0 + 0.005, x1 - 0.005, yf, yf + 0.025, zs - 0.006, zs + 0.006, F.rubber)
    K.rbox(x0 + 0.002, x1 - 0.002, yf - 0.026, yf + 0.012, 0.075, zs - 0.007, F.body, 0.02, rv=0.01, seg=3)
    K.rbox(x0 + 0.002, x1 - 0.002, yf - 0.026, yf + 0.012, zs + 0.007, h - 0.012, F.body, 0.02, rv=0.01, seg=3)
    hx = x1 - 0.055
    handle_bar(K, hx, yf - 0.026, zs + 0.06, h - 0.20, F.trim)
    handle_bar(K, hx, yf - 0.026, 0.95, zs - 0.07, F.trim)
    K.box(-0.04, 0.04, yf - 0.029, yf - 0.026, 0.14, 0.152, F.chrome)
    return K


def fridge_side(F):
    """A side-by-side refrigerator with a water and ice dispenser, 0.91 x 0.74 x 1.78 m."""
    K = Mesh('kitchen_fridge_side')
    w, d, h = 0.91, 0.74, 1.78
    x0, x1 = -w / 2, w / 2
    yf = -d / 2
    K.rbox(x0, x1, yf + 0.01, d / 2, 0.06, h - 0.005, F.body, 0.03, rv=0.012, seg=3)
    K.box(x0 + 0.03, x1 - 0.03, yf + 0.02, d / 2 - 0.05, 0.0, 0.07, F.rubber)
    feet(K, (x0 + 0.06, x1 - 0.06), (yf + 0.08,), F.rubber, 0.06, 0.024)
    K.box(-0.006, 0.006, yf, yf + 0.025, 0.075, h - 0.012, F.rubber)
    K.rbox(x0 + 0.002, -0.0045, yf - 0.026, yf + 0.012, 0.075, h - 0.012, F.body, 0.02, rv=0.01, seg=3)     # the freezer door (left, narrower)
    K.rbox(0.0045, x1 - 0.002, yf - 0.026, yf + 0.012, 0.075, h - 0.012, F.body, 0.02, rv=0.01, seg=3)       # the fridge door
    handle_bar(K, -0.045, yf - 0.026, 0.50, 1.25, F.trim)
    handle_bar(K, 0.045, yf - 0.026, 0.50, 1.25, F.trim)
    # the dispenser: a dark recessed panel with a tray and two buttons on the freezer door
    K.box(x0 + 0.07, -0.13, yf - 0.029, yf - 0.026, 1.05, 1.45, F.glass)
    K.box(x0 + 0.10, -0.16, yf - 0.032, yf - 0.029, 1.08, 1.14, F.lcd)
    K.box(x0 + 0.11, -0.17, yf - 0.045, yf - 0.026, 1.16, 1.20, F.rubber)
    K.box(x0 + 0.115, -0.175, yf - 0.047, yf - 0.043, 1.15, 1.17, F.chrome)
    return K


def fridge_french(F):
    """A French-door refrigerator with a bottom freezer drawer, 0.90 x 0.74 x 1.78 m."""
    K = Mesh('kitchen_fridge_french')
    w, d, h = 0.90, 0.74, 1.78
    x0, x1 = -w / 2, w / 2
    yf = -d / 2
    K.rbox(x0, x1, yf + 0.01, d / 2, 0.06, h - 0.005, F.body, 0.03, rv=0.012, seg=3)
    K.box(x0 + 0.03, x1 - 0.03, yf + 0.02, d / 2 - 0.05, 0.0, 0.07, F.rubber)
    feet(K, (x0 + 0.06, x1 - 0.06), (yf + 0.08,), F.rubber, 0.06, 0.024)
    zs = 0.60
    K.box(x0 + 0.005, x1 - 0.005, yf, yf + 0.025, zs - 0.006, zs + 0.006, F.rubber)
    K.box(-0.006, 0.006, yf, yf + 0.025, zs + 0.006, h - 0.012, F.rubber)
    K.rbox(x0 + 0.002, -0.0045, yf - 0.026, yf + 0.012, zs + 0.007, h - 0.012, F.body, 0.02, rv=0.01, seg=3)
    K.rbox(0.0045, x1 - 0.002, yf - 0.026, yf + 0.012, zs + 0.007, h - 0.012, F.body, 0.02, rv=0.01, seg=3)
    K.rbox(x0 + 0.002, x1 - 0.002, yf - 0.026, yf + 0.012, 0.075, zs - 0.007, F.body, 0.02, rv=0.01, seg=3)  # the freezer drawer
    handle_bar(K, -0.05, yf - 0.026, 0.95, 1.70, F.trim)
    handle_bar(K, 0.05, yf - 0.026, 0.95, 1.70, F.trim)
    handle_bar_h(K, -0.28, 0.28, yf - 0.026, zs - 0.07, F.trim)
    K.box(-0.04, 0.04, yf - 0.029, yf - 0.026, 0.16, 0.172, F.chrome)
    return K


def freezer_upright(F):
    """An upright freezer, 0.70 x 0.70 x 1.75 m."""
    K = Mesh('kitchen_freezer_upright')
    w, d, h = 0.70, 0.70, 1.75
    x0, x1 = -w / 2, w / 2
    yf = -d / 2
    K.rbox(x0, x1, yf + 0.01, d / 2, 0.06, h - 0.005, F.body, 0.03, rv=0.012, seg=3)
    K.box(x0 + 0.03, x1 - 0.03, yf + 0.02, d / 2 - 0.05, 0.0, 0.07, F.rubber)
    feet(K, (x0 + 0.05, x1 - 0.05), (yf + 0.08,), F.rubber, 0.06, 0.022)
    K.rbox(x0 + 0.002, x1 - 0.002, yf - 0.026, yf + 0.012, 0.075, h - 0.012, F.body, 0.02, rv=0.01, seg=3)
    handle_bar(K, x1 - 0.055, yf - 0.026, 0.80, 1.55, F.trim)
    K.box(x0 + 0.06, x0 + 0.20, yf - 0.029, yf - 0.026, 1.55, 1.62, F.glass)
    K.box(x0 + 0.075, x0 + 0.115, yf - 0.031, yf - 0.029, 1.57, 1.60, F.red)
    return K


def freezer_chest(F):
    """A chest freezer with a hinged lid, 1.00 x 0.60 x 0.86 m."""
    K = Mesh('kitchen_freezer_chest')
    w, d, h = 1.00, 0.62, 0.86
    x0, x1 = -w / 2, w / 2
    yf = -d / 2
    K.rbox(x0, x1, yf, d / 2, 0.05, h - 0.06, F.body, 0.02, rv=0.01, seg=3)
    K.box(x0 + 0.02, x1 - 0.02, yf + 0.02, d / 2 - 0.02, 0.0, 0.06, F.rubber)
    K.rbox(x0 - 0.004, x1 + 0.004, yf - 0.012, d / 2 + 0.01, h - 0.07, h, F.body, 0.02, rv=0.012, seg=3)         # the lid
    K.box(x0 + 0.01, x1 - 0.01, yf + 0.006, yf + 0.03, h - 0.075, h - 0.065, F.rubber)                          # its gasket line
    handle_bar_h(K, -0.15, 0.15, yf - 0.012, h - 0.03, F.trim, out=0.035)
    for hx in (x0 + 0.12, x1 - 0.12):
        K.box(hx - 0.04, hx + 0.04, d / 2 - 0.005, d / 2 + 0.03, h - 0.06, h - 0.02, F.rubber)                    # the hinges
    K.box(x1 - 0.20, x1 - 0.06, yf - 0.002, yf + 0.006, 0.55, 0.62, F.glass)
    K.box(x1 - 0.175, x1 - 0.135, yf - 0.004, yf - 0.002, 0.57, 0.60, F.lcd)
    return K


# ------------------------------------------------------------------ cooking

def range_oven(F):
    """A freestanding 4-burner range with an oven, 0.76 x 0.66 x 0.92 m (backguard to 1.18 m)."""
    K = Mesh('kitchen_range')
    w, d, h = 0.76, 0.66, 0.915
    x0, x1 = -w / 2, w / 2
    yf = -d / 2
    K.box(x0 + 0.02, x1 - 0.02, yf + 0.03, d / 2 - 0.02, 0.0, 0.10, F.rubber)
    K.rbox(x0, x1, yf, d / 2, 0.10, h, F.body, 0.012, rv=0.008, seg=2)
    cooktop(K, F, x0, x1, yf, d / 2, h)
    K.rbox(x0 + 0.005, x1 - 0.005, d / 2 - 0.11, d / 2 - 0.01, h, 1.18, F.body, 0.01, rv=0.008, seg=2)
    K.box(x0 + 0.03, x1 - 0.03, d / 2 - 0.115, d / 2 - 0.11, 1.07, 1.15, F.glass)
    K.box(-0.07, 0.07, d / 2 - 0.118, d / 2 - 0.115, 1.10, 1.12, F.lcd)
    K.box(x0 + 0.02, x1 - 0.02, yf - 0.004, yf + 0.004, 0.80, h - 0.012, F.black)
    for k in range(5):
        knob(K, x0 + 0.10 + k * 0.14, yf - 0.004, 0.857, F)
    K.rbox(x0 + 0.03, x1 - 0.03, yf - 0.035, yf + 0.01, 0.13, 0.785, F.body, 0.014, rv=0.012, seg=2)
    K.box(x0 + 0.11, x1 - 0.11, yf - 0.037, yf - 0.030, 0.26, 0.62, F.glass)
    handle_bar_h(K, x0 + 0.06, x1 - 0.06, yf - 0.035, 0.725, F.trim, out=0.045, r=0.011)
    K.box(x0 + 0.02, x1 - 0.02, yf - 0.002, yf + 0.004, 0.105, 0.128, F.rubber)
    return K


def cooktop(K, F, x0, x1, yf, yb, h, depth_free=0.1):
    """A dark glass cooktop with four burners and cast-iron grates, lying on a body whose top is at z = h."""
    K.box(x0 + 0.012, x1 - 0.012, yf + 0.012, yb - depth_free, h, h + 0.008, F.glass)
    cy0, cy1 = (yf + 0.012 + yb - depth_free) / 2 - 0.125, (yf + 0.012 + yb - depth_free) / 2 + 0.125
    cxl, cxr = (x0 + x1) / 2 - 0.18, (x0 + x1) / 2 + 0.18
    for bx, by, br in ((cxl, cy0, 0.085), (cxr, cy0, 0.065), (cxl, cy1, 0.065), (cxr, cy1, 0.085)):
        K.cyl((bx, by, h + 0.008), (bx, by, h + 0.02), br, F.iron, seg=18)
        K.cyl((bx, by, h + 0.02), (bx, by, h + 0.028), br * 0.55, F.chrome, seg=14)
    gz = h + 0.034
    mid = (x0 + x1) / 2
    for gx0, gx1 in ((x0 + 0.03, mid - 0.012), (mid + 0.012, x1 - 0.03)):
        K.box(gx0, gx1, cy0 - 0.115, cy0 - 0.105, h + 0.008, gz, F.iron)
        K.box(gx0, gx1, cy1 + 0.105, cy1 + 0.115, h + 0.008, gz, F.iron)
        K.box(gx0, gx0 + 0.01, cy0 - 0.115, cy1 + 0.115, h + 0.008, gz, F.iron)
        K.box(gx1 - 0.01, gx1, cy0 - 0.115, cy1 + 0.115, h + 0.008, gz, F.iron)
        for fy in (cy0, cy1):
            K.box(gx0, gx1, fy - 0.004, fy + 0.004, gz - 0.006, gz, F.iron)


def cooktop_unit(F):
    """A built-in 4-burner cooktop to set into a countertop, 0.76 x 0.52 x 0.07 m."""
    K = Mesh('kitchen_cooktop')
    x0, x1, yf, yb = -0.38, 0.38, -0.26, 0.26
    K.rbox(x0, x1, yf, yb, 0.0, 0.04, F.body, 0.01, rv=0.006, seg=2)
    K.rbox(x0, x1, yf, yb, 0.04, 0.052, F.black if F.name != 'white' else F.white, 0.006, rv=0.004, seg=2)
    cooktop(K, F, x0, x1, yf, yb, 0.052, depth_free=0.012)
    for k in range(4):
        knob(K, x0 + 0.17 + k * 0.14, yf + 0.0, 0.026, F, r=0.014, out=0.026)
    return K


def oven_tower(F):
    """A tall oven cabinet with a double wall oven and a warming drawer, 0.76 x 0.62 x 2.10 m."""
    K = Mesh('kitchen_oven_tower')
    w, d, h = 0.76, 0.62, 2.10
    x0, x1 = -w / 2, w / 2
    yf = -d / 2
    K.box(x0 + 0.02, x1 - 0.02, yf + 0.05, d / 2 - 0.01, 0.0, 0.10, F.rubber)
    K.rbox(x0, x1, yf + 0.01, d / 2, 0.10, h, F.body, 0.01, rv=0.006, seg=2)
    for z0, z1 in ((0.20, 0.82), (0.90, 1.52)):
        K.rbox(x0 + 0.03, x1 - 0.03, yf - 0.03, yf + 0.012, z0, z1, F.body, 0.014, rv=0.01, seg=2)
        K.box(x0 + 0.10, x1 - 0.10, yf - 0.032, yf - 0.026, z0 + 0.10, z1 - 0.13, F.glass)
        handle_bar_h(K, x0 + 0.07, x1 - 0.07, yf - 0.03, z1 - 0.045, F.trim, out=0.04, r=0.010)
    K.box(x0 + 0.03, x1 - 0.03, yf - 0.002, yf + 0.004, 1.55, 1.75, F.black)                                      # the control panel
    for k in range(6):
        knob(K, x0 + 0.10 + k * 0.11, yf - 0.002, 1.65, F, r=0.014, out=0.026)
    K.box(-0.06, 0.06, yf - 0.004, yf - 0.002, 1.70, 1.725, F.lcd)
    K.rbox(x0 + 0.03, x1 - 0.03, yf - 0.03, yf + 0.012, 1.78, 2.05, F.body, 0.012, rv=0.008, seg=2)              # the warming drawer
    handle_bar_h(K, x0 + 0.10, x1 - 0.10, yf - 0.03, 1.98, F.trim, out=0.035, r=0.009)
    return K


def microwave_counter(F):
    """A countertop microwave oven, 0.50 x 0.40 x 0.30 m."""
    K = Mesh('kitchen_microwave')
    w, d, h = 0.50, 0.40, 0.30
    x0, x1 = -w / 2, w / 2
    yf = -d / 2
    K.rbox(x0, x1, yf, d / 2, 0.015, h, F.body, 0.015, rv=0.01, seg=3)
    K.box(x0 + 0.02, x1 - 0.02, yf + 0.04, d / 2 - 0.04, 0.0, 0.016, F.rubber)
    K.box(x0 + 0.02, x0 + 0.34, yf - 0.006, yf + 0.004, 0.03, h - 0.03, F.black)                                     # the door frame
    K.box(x0 + 0.04, x0 + 0.32, yf - 0.009, yf - 0.004, 0.06, h - 0.06, F.glass)                                      # window
    K.box(x0 + 0.36, x1 - 0.02, yf - 0.004, yf + 0.004, 0.03, h - 0.03, F.black)                                    # the control panel
    K.box(x0 + 0.375, x1 - 0.035, yf - 0.007, yf - 0.004, h - 0.09, h - 0.05, F.lcd)
    for k in range(6):
        K.box(x0 + 0.375 + (k % 2) * 0.045, x0 + 0.405 + (k % 2) * 0.045, yf - 0.009, yf - 0.004, 0.17 - (k // 2) * 0.045, 0.19 - (k // 2) * 0.045, F.trim)
    dial(K, x0 + 0.43, yf - 0.004, 0.06, F, r=0.022)
    K.box(x0 + 0.34, x0 + 0.36, yf - 0.014, yf - 0.006, 0.07, h - 0.07, F.trim)                                      # the door handle
    return K


def microwave_otr(F):
    """An over-the-range microwave with a vent underneath, 0.76 x 0.40 x 0.40 m. A wall item."""
    K = Mesh('kitchen_microwave_otr')
    w, d, h = 0.76, 0.40, 0.38
    x0, x1 = -w / 2, w / 2
    yf = -d / 2
    K.rbox(x0, x1, yf, d / 2, 0.0, h, F.body, 0.012, rv=0.01, seg=3)
    K.box(x0 + 0.03, x0 + 0.52, yf - 0.006, yf + 0.004, 0.03, h - 0.03, F.black)
    K.box(x0 + 0.05, x0 + 0.50, yf - 0.009, yf - 0.004, 0.06, h - 0.06, F.glass)
    K.box(x0 + 0.54, x1 - 0.03, yf - 0.004, yf + 0.004, 0.03, h - 0.03, F.black)
    K.box(x0 + 0.555, x1 - 0.045, yf - 0.007, yf - 0.004, h - 0.09, h - 0.05, F.lcd)
    for k in range(8):
        K.box(x0 + 0.56 + (k % 2) * 0.06, x0 + 0.60 + (k % 2) * 0.06, yf - 0.009, yf - 0.004, 0.22 - (k // 2) * 0.05, 0.25 - (k // 2) * 0.05, F.trim)
    handle_bar(K, x0 + 0.525, yf - 0.006, 0.06, h - 0.06, F.trim, out=0.03)
    K.box(x0 + 0.05, x1 - 0.05, yf + 0.04, d / 2 - 0.04, -0.001, 0.002, F.rubber)
    K.shift(0, d / 2, 0)
    return K


def range_hood(F):
    """A chimney range hood, 0.76 x 0.50 x 0.90 m (a wall item: mount it above the cooker)."""
    K = Mesh('kitchen_range_hood')
    w, d = 0.76, 0.50
    x0, x1 = -w / 2, w / 2
    yf = -d / 2
    # the canopy: a low slanted hood
    K.prism([(x0, d / 2), (x1, d / 2), (x1 - 0.03, yf), (x0 + 0.03, yf)], 0.0, 0.10, F.body)
    K.box(x0 + 0.04, x1 - 0.04, yf + 0.03, d / 2 - 0.03, -0.002, 0.004, F.rubber)
    K.box(x0 + 0.06, x1 - 0.06, yf + 0.04, yf + 0.06, 0.0, 0.003, F.chrome)
    for k in range(3):
        K.box(x0 + 0.10 + k * 0.05, x0 + 0.12 + k * 0.05, yf - 0.002, yf + 0.0, 0.03, 0.07, F.black)
    # the chimney
    K.rbox(-0.17, 0.17, 0.0, d / 2, 0.10, 0.90, F.body, 0.01, rv=0.006, seg=2)
    K.rbox(-0.15, 0.15, 0.04, d / 2 - 0.05, 0.50, 0.90, F.body, 0.005, seg=1)
    K.shift(0, d / 2, 0)
    return K


def dishwasher(F):
    """A built-in dishwasher, 0.60 x 0.60 x 0.85 m."""
    K = Mesh('kitchen_dishwasher')
    w, d, h = 0.60, 0.60, 0.84
    x0, x1 = -w / 2, w / 2
    yf = -d / 2
    K.box(x0 + 0.02, x1 - 0.02, yf + 0.04, d / 2 - 0.02, 0.0, 0.08, F.rubber)
    K.rbox(x0, x1, yf + 0.01, d / 2, 0.08, h, F.body, 0.01, rv=0.006, seg=2)
    K.rbox(x0 + 0.004, x1 - 0.004, yf - 0.026, yf + 0.014, 0.09, h - 0.01, F.body, 0.012, rv=0.01, seg=2)
    K.box(x0 + 0.03, x1 - 0.03, yf - 0.03, yf - 0.026, h - 0.11, h - 0.04, F.black)                                    # the control strip
    K.box(x0 + 0.08, x0 + 0.20, yf - 0.032, yf - 0.030, h - 0.085, h - 0.065, F.lcd)
    for k in range(5):
        K.box(x0 + 0.26 + k * 0.05, x0 + 0.29 + k * 0.05, yf - 0.032, yf - 0.030, h - 0.09, h - 0.06, F.trim)
    handle_bar_h(K, x0 + 0.06, x1 - 0.06, yf - 0.03, h - 0.14, F.trim, out=0.04, r=0.010)
    return K


def sink_unit(F):
    """A double-bowl kitchen sink set in a cabinet with a countertop, a tall faucet and a soap dispenser, 0.90 x 0.62 x 1.18 m."""
    K = Mesh('kitchen_sink')
    cab = CAB['black'] if F.name == 'black' else CAB['white']
    w, d = 0.90, 0.60
    cabinet_carcass(K, w, d, 0.88, cab, doors=2, handles=True)
    zt = 0.88
    x0, x1 = -w / 2, w / 2
    yf = -d / 2
    ctr = cab['counter']
    K.box(x0, x1, yf - 0.025, d / 2, zt, zt + 0.04, ctr, r=0.004, seg=1, uv=2.0)
    basin = F.steel if F.name == 'stainless' else (F.white if F.name == 'white' else F.black)
    for bx in (-0.19, 0.19):
        K.box(bx - 0.165, bx + 0.165, -0.20, 0.10, zt + 0.039, zt + 0.045, F.trim if F.name == 'stainless' else basin)     # the rim
        K.box(bx - 0.15, bx + 0.15, -0.185, 0.085, zt - 0.17, zt + 0.047, F.rubber if F.name != 'stainless' else material('SinkDark', (0.10, 0.10, 0.11), 0.4))
        K.box(bx - 0.14, bx + 0.14, -0.175, 0.075, zt - 0.16, zt + 0.0475, basin)
        K.cyl((bx, -0.05, zt - 0.16), (bx, -0.05, zt - 0.158), 0.025, F.chrome, seg=10)                              # the drain
    K.box(-0.02, 0.02, -0.20, 0.10, zt + 0.039, zt + 0.047, basin)
    # the faucet: base, a tall arched spout, a lever
    fy = 0.15
    K.cyl((0.0, fy, zt + 0.04), (0.0, fy, zt + 0.06), 0.028, F.chrome, seg=14)
    K.cyl((0.0, fy, zt + 0.06), (0.0, fy, zt + 0.30), 0.014, F.chrome, seg=12)
    K.cyl((0.0, fy, zt + 0.30), (0.0, fy - 0.06, zt + 0.34), 0.013, F.chrome, seg=10)
    K.cyl((0.0, fy - 0.06, zt + 0.34), (0.0, fy - 0.17, zt + 0.34), 0.013, F.chrome, seg=10)
    K.cyl((0.0, fy - 0.17, zt + 0.34), (0.0, fy - 0.17, zt + 0.30), 0.012, F.chrome, seg=10)
    K.cyl((0.0, fy, zt + 0.12), (0.06, fy, zt + 0.16), 0.007, F.chrome, seg=8)
    K.cyl((0.30, fy, zt + 0.04), (0.30, fy, zt + 0.10), 0.014, F.chrome, seg=10)
    return K


# ------------------------------------------------------------------ small appliances

def toaster(F):
    """A two-slice toaster, 0.30 x 0.18 x 0.20 m."""
    K = Mesh('kitchen_toaster')
    K.rbox(-0.15, 0.15, -0.09, 0.09, 0.0, 0.18, F.body, 0.05, rv=0.02, seg=3)
    K.box(-0.12, -0.04, -0.07, 0.07, 0.178, 0.186, F.black)
    K.box(0.04, 0.12, -0.07, 0.07, 0.178, 0.186, F.black)
    K.box(0.152, 0.158, -0.02, 0.02, 0.07, 0.15, F.black)
    K.box(0.152, 0.164, -0.02, 0.02, 0.10, 0.12, F.trim)
    K.cyl((-0.152, -0.04, 0.10), (-0.168, -0.04, 0.10), 0.012, F.rubber, seg=10)
    K.cyl((-0.152, 0.02, 0.10), (-0.168, 0.02, 0.10), 0.012, F.rubber, seg=10)
    K.box(-0.14, 0.14, -0.092, -0.088, 0.012, 0.03, F.rubber)
    return K


def kettle(F):
    """An electric kettle on its power base, 0.24 x 0.20 x 0.26 m."""
    K = Mesh('kitchen_kettle')
    K.cyl((0, 0, 0), (0, 0, 0.02), 0.095, F.rubber, seg=24)
    K.lathe([(0.0, 0.02), (0.085, 0.02), (0.088, 0.045), (0.082, 0.14), (0.065, 0.20), (0.05, 0.225), (0.0, 0.235)], F.body, at=(0, 0, 0.0), seg=24, hard=(1,))
    K.cyl((0, 0, 0.225), (0, 0, 0.245), 0.04, F.rubber, seg=16, r1=0.03)
    K.cyl((0, 0, 0.245), (0, 0, 0.262), 0.012, F.rubber, seg=10)
    K.cyl((0.075, 0, 0.12), (0.115, 0, 0.17), 0.018, F.body, seg=10, r1=0.012)                                   # the spout
    K.cyl((-0.085, 0, 0.05), (-0.13, 0, 0.09), 0.012, F.rubber, seg=8)
    K.cyl((-0.13, 0, 0.09), (-0.13, 0, 0.19), 0.013, F.rubber, seg=8)
    K.cyl((-0.13, 0, 0.19), (-0.07, 0, 0.225), 0.012, F.rubber, seg=8)
    K.box(-0.095, -0.075, -0.004, 0.004, 0.10, 0.12, F.lcd)
    return K


def coffee_maker(F):
    """A drip coffee maker with a glass carafe, 0.26 x 0.32 x 0.36 m."""
    K = Mesh('kitchen_coffee_maker')
    K.rbox(-0.13, 0.13, 0.02, 0.16, 0.0, 0.05, F.body, 0.01, seg=2)
    K.rbox(-0.13, 0.13, 0.10, 0.16, 0.05, 0.36, F.body, 0.02, rv=0.01, seg=3)
    K.rbox(-0.13, 0.13, -0.10, 0.16, 0.30, 0.36, F.body, 0.02, rv=0.01, seg=3)
    K.box(-0.12, 0.12, 0.0, 0.10, 0.045, 0.30, F.rubber)
    K.box(-0.10, 0.10, 0.11, 0.17, 0.0, 0.01, F.rubber)
    K.cyl((0, -0.03, 0.30), (0, -0.03, 0.31), 0.028, F.rubber, seg=12)
    K.lathe([(0.0, 0.05), (0.075, 0.05), (0.078, 0.07), (0.07, 0.15), (0.06, 0.2), (0.058, 0.215), (0.0, 0.215)], F.glass, at=(0, -0.03, 0.0), seg=20, hard=(1,))
    K.cyl((0.0, -0.03, 0.215), (0.0, -0.03, 0.225), 0.06, F.rubber, seg=16)
    K.cyl((0.07, -0.03, 0.12), (0.115, -0.03, 0.12), 0.01, F.rubber, seg=8)
    K.box(-0.10, 0.10, -0.101, -0.099, 0.325, 0.345, F.lcd)
    K.box(0.06, 0.11, -0.101, -0.098, 0.04, 0.05, F.red)
    return K


def stand_mixer(F):
    """A tilt-head stand mixer with a steel bowl, 0.36 x 0.24 x 0.36 m."""
    K = Mesh('kitchen_stand_mixer')
    K.rbox(-0.12, 0.12, -0.12, 0.12, 0.0, 0.03, F.body, 0.02, seg=3)
    K.rbox(-0.06, 0.07, 0.04, 0.12, 0.03, 0.28, F.body, 0.03, rv=0.015, seg=3)                            # the column
    K.rbox(-0.075, 0.075, -0.12, 0.12, 0.26, 0.34, F.body, 0.04, rv=0.02, seg=3)                           # the motor head
    K.cyl((-0.0, -0.12, 0.30), (0.0, -0.135, 0.30), 0.028, F.chrome, seg=14)
    K.box(0.075, 0.105, -0.02, 0.0, 0.29, 0.30, F.trim)
    K.lathe([(0.0, 0.03), (0.07, 0.03), (0.08, 0.05), (0.115, 0.09), (0.125, 0.15), (0.12, 0.18), (0.126, 0.185), (0.0, 0.185)], F.steel, at=(0, -0.04, 0.0), seg=24, hard=(1, 5))
    K.cyl((0.0, -0.04, 0.12), (0.0, -0.04, 0.28), 0.007, F.chrome, seg=8)
    K.cyl((0.0, -0.04, 0.14), (0.02, -0.04, 0.22), 0.005, F.chrome, seg=6)
    return K


def blender_jug(F):
    """A countertop blender with a glass jug, 0.20 x 0.20 x 0.42 m."""
    K = Mesh('kitchen_blender')
    K.lathe([(0.0, 0.0), (0.095, 0.0), (0.098, 0.02), (0.085, 0.12), (0.07, 0.17), (0.0, 0.17)], F.body, at=(0, 0, 0), seg=20, hard=(1,))
    K.cyl((0.0, -0.085, 0.10), (0.0, -0.1, 0.10), 0.016, F.chrome, seg=10)
    K.cyl((0.04, -0.075, 0.13), (0.04, -0.09, 0.13), 0.01, F.rubber, seg=8)
    K.cyl((-0.04, -0.075, 0.13), (-0.04, -0.09, 0.13), 0.01, F.rubber, seg=8)
    K.cyl((0, 0, 0.17), (0, 0, 0.19), 0.075, F.rubber, seg=18, r1=0.065)
    K.lathe([(0.0, 0.19), (0.062, 0.19), (0.08, 0.3), (0.095, 0.4), (0.0, 0.4)], F.glass, at=(0, 0, 0), seg=20, hard=(1,))
    K.cyl((0, 0, 0.4), (0, 0, 0.415), 0.1, F.rubber, seg=20, r1=0.085)
    K.cyl((0, 0, 0.415), (0, 0, 0.428), 0.02, F.rubber, seg=10)
    K.cyl((0.09, 0.0, 0.22), (0.125, 0.0, 0.25), 0.009, F.rubber, seg=8)
    K.cyl((0.125, 0.0, 0.25), (0.125, 0.0, 0.36), 0.009, F.rubber, seg=8)
    K.cyl((0.125, 0.0, 0.36), (0.092, 0.0, 0.38), 0.009, F.rubber, seg=8)
    return K


def toaster_oven(F):
    """A countertop toaster oven, 0.44 x 0.34 x 0.26 m."""
    K = Mesh('kitchen_toaster_oven')
    x0, x1, yf = -0.22, 0.22, -0.17
    K.rbox(x0, x1, yf, 0.17, 0.012, 0.26, F.body, 0.02, rv=0.012, seg=3)
    K.box(x0 + 0.03, x1 - 0.03, yf + 0.04, 0.13, 0.0, 0.013, F.rubber)
    K.box(x0 + 0.02, x0 + 0.32, yf - 0.006, yf + 0.004, 0.03, 0.23, F.black)
    K.box(x0 + 0.04, x0 + 0.30, yf - 0.009, yf - 0.004, 0.055, 0.205, F.glass)
    handle_bar_h(K, x0 + 0.05, x0 + 0.29, yf - 0.006, 0.225, F.trim, out=0.03, r=0.007)
    for k in range(3):
        dial(K, x0 + 0.375, yf + 0.0, 0.065 + k * 0.07, F, r=0.016)
    return K


# ------------------------------------------------------------------ cabinetry

def _mat(name, rgb, rough, tex=None, metal=0.0):
    return material(name, rgb, rough, metal, tex=tex)


def _build_cab():
    return {
        'white': dict(name='White', body=_mat('CabWhite', (0.92, 0.92, 0.90), 0.40), door=_mat('CabWhite', (0.92, 0.92, 0.90), 0.40), style='shaker',
                      counter=_mat('CounterMarble', (0.93, 0.93, 0.92), 0.22, tex='marble'), pull=_mat('PullChrome', (0.82, 0.83, 0.85), 0.16, metal=1.0),
                      kick=_mat('KickDark', (0.10, 0.10, 0.11), 0.7), glass=_mat('CabGlass', (0.55, 0.65, 0.70), 0.05)),
        'oak': dict(name='Oak', body=_mat('CabOak', (0.75, 0.58, 0.38), 0.55, tex='oak'), door=_mat('CabOak', (0.75, 0.58, 0.38), 0.55, tex='oak'), style='slab',
                    counter=_mat('CounterButcher', (0.7, 0.55, 0.36), 0.5, tex='butcher'), pull=_mat('PullBlack', (0.06, 0.06, 0.065), 0.35, metal=0.6),
                    kick=_mat('KickDark', (0.10, 0.10, 0.11), 0.7), glass=_mat('CabGlass', (0.55, 0.65, 0.70), 0.05)),
        'black': dict(name='Black', body=_mat('CabBlack', (0.07, 0.07, 0.075), 0.45), door=_mat('CabBlack', (0.07, 0.07, 0.075), 0.45), style='slab',
                      counter=_mat('CounterGranite', (0.08, 0.08, 0.09), 0.24, tex='granite'), pull=_mat('PullChrome', (0.82, 0.83, 0.85), 0.16, metal=1.0),
                      kick=_mat('KickDark', (0.10, 0.10, 0.11), 0.7), glass=_mat('CabGlass', (0.55, 0.65, 0.70), 0.05)),
    }


class _LazyCab:
    """CAB['white'] etc.: the cabinet material sets, made when first asked for (after the scene exists) and made again if the scene was reset since."""
    _cache = None

    def __getitem__(self, key):
        c = _LazyCab._cache
        try:
            if c is not None:
                c['white']['body'].name
        except ReferenceError:
            c = None
        if c is None:
            c = _LazyCab._cache = _build_cab()
        return c[key]


CAB = _LazyCab()


def door_panel(K, x0, x1, z0, z1, yf, cab, glass=False):
    """A cabinet door whose outer face is the plane y = yf and which is 0.02 m thick (towards +y): a shaker frame with a recessed panel, or a plain slab."""
    t = 0.02
    m = cab['door']
    if cab['style'] == 'shaker':
        fr = 0.06
        K.box(x0, x1, yf, yf + t, z0, z0 + fr, m, r=0.002, seg=1)                          # bottom rail
        K.box(x0, x1, yf, yf + t, z1 - fr, z1, m, r=0.002, seg=1)                          # top rail
        K.box(x0, x0 + fr, yf, yf + t, z0 + fr, z1 - fr, m, r=0.002, seg=1)                # stiles
        K.box(x1 - fr, x1, yf, yf + t, z0 + fr, z1 - fr, m, r=0.002, seg=1)
        K.box(x0 + fr - 0.002, x1 - fr + 0.002, yf + 0.009, yf + 0.014, z0 + fr - 0.002, z1 - fr + 0.002, cab['glass'] if glass else m)   # the recessed panel
    else:
        K.box(x0, x1, yf, yf + t, z0, z1, m, r=0.003, seg=1, uv=1.0)
        if glass:
            K.box(x0 + 0.05, x1 - 0.05, yf - 0.001, yf + 0.004, z0 + 0.05, z1 - 0.05, cab['glass'])


def pull(K, cab, x, yf, z, vertical=True, length=0.12):
    if vertical:
        handle_bar(K, x, yf, z - length / 2, z + length / 2, cab['pull'], out=0.028, r=0.006)
    else:
        handle_bar_h(K, x - length / 2, x + length / 2, yf, z, cab['pull'], out=0.028, r=0.006)


def cabinet_carcass(K, w, d, h, cab, doors=2, drawers=0, handles=True, toe=0.10, glass=False, shelves=0, top=True, double_stack=False):
    """A base-style cabinet from the floor: toe kick, carcass, doors (and/or drawers), handles. The front face is y = -d/2."""
    x0, x1 = -w / 2, w / 2
    yf = -d / 2
    K.box(x0 + 0.01, x1 - 0.01, yf + 0.07, d / 2 - 0.01, 0.0, toe, cab['kick'])
    K.box(x0, x1, yf + 0.02, d / 2, toe, h, cab['body'], r=0.003, seg=1)
    gap = 0.004
    zb = toe + 0.005
    zt = h - 0.005
    dz0 = zb
    if drawers:
        zone = (zt - zb)
        each = zone / drawers
        for i in range(drawers):
            a = zb + i * each
            b = a + each - gap
            door_panel(K, x0 + 0.004, x1 - 0.004, a, b, yf, cab)
            if handles:
                pull(K, cab, 0.0, yf, b - 0.05 if cab['style'] == 'shaker' else b - 0.04, vertical=False, length=min(0.16, w * 0.4))
    elif doors:
        if doors == 1:
            door_panel(K, x0 + 0.004, x1 - 0.004, zb, zt, yf, cab, glass=glass)
            if handles:
                pull(K, cab, x1 - 0.045, yf, zb + (zt - zb) * (0.72 if h > 0.9 else 0.82), vertical=True, length=0.14 if h < 1.2 else 0.20)
        else:
            mid = 0.0
            door_panel(K, x0 + 0.004, mid - gap / 2, zb, zt, yf, cab, glass=glass)
            door_panel(K, mid + gap / 2, x1 - 0.004, zb, zt, yf, cab, glass=glass)
            if handles:
                hz = zb + (zt - zb) * (0.78 if h > 0.6 else 0.5)
                pull(K, cab, -0.04, yf, hz, vertical=True, length=0.14)
                pull(K, cab, 0.04, yf, hz, vertical=True, length=0.14)


def countertop(K, w, d, z, cab, front_over=0.025, back=0.0, thickness=0.04):
    x0, x1 = -w / 2, w / 2
    K.box(x0, x1, -d / 2 - front_over, d / 2 + back, z, z + thickness, cab['counter'], r=0.004, seg=1, uv=2.0)


def base_cab_60(C):
    """A 0.60 m base cabinet with two doors under a countertop, 0.60 x 0.62 x 0.92 m."""
    cab = CAB[C]
    K = Mesh('kitchen_base_cab_60')
    cabinet_carcass(K, 0.60, 0.60, 0.88, cab, doors=1)
    countertop(K, 0.60, 0.60, 0.88, cab)
    return K


def base_cab_90(C):
    """A 0.90 m double-door base cabinet under a countertop, 0.90 x 0.62 x 0.92 m."""
    cab = CAB[C]
    K = Mesh('kitchen_base_cab_90')
    cabinet_carcass(K, 0.90, 0.60, 0.88, cab, doors=2)
    countertop(K, 0.90, 0.60, 0.88, cab)
    return K


def base_cab_drawers(C):
    """A 0.60 m drawer base (three drawers) under a countertop, 0.60 x 0.62 x 0.92 m."""
    cab = CAB[C]
    K = Mesh('kitchen_base_cab_drawers')
    cabinet_carcass(K, 0.60, 0.60, 0.88, cab, drawers=3)
    countertop(K, 0.60, 0.60, 0.88, cab)
    return K


def corner_base(C):
    """An L-shaped corner base cabinet under a countertop, 0.90 x 0.90 x 0.92 m. The doors face out of the corner."""
    cab = CAB[C]
    K = Mesh('kitchen_corner_base')
    w = 0.90
    x0, x1, y0, y1 = -w / 2, w / 2, -w / 2, w / 2
    toe = 0.10
    K.prism([(x0, y0), (x1, y0), (x1, y0 + 0.60), (x0 + 0.60, y0 + 0.60), (x0 + 0.60, y1), (x0, y1)], toe, 0.88, cab['body'])
    K.box(x0 + 0.01, x1 - 0.01, y0 + 0.07, y0 + 0.58, 0.0, toe, cab['kick'])
    K.box(x0 + 0.01, x0 + 0.58, y0 + 0.58, y1 - 0.01, 0.0, toe, cab['kick'])
    door_panel(K, x0 + 0.004, x0 + 0.58, 0.105, 0.875, y0 - 0.001, cab)                                          # the front door
    pull(K, cab, x0 + 0.535, y0 - 0.001, 0.70, vertical=True, length=0.14)
    K.box(x1 - 0.64, x1 - 0.60, y0 + 0.0, y0 + 0.002, 0.2, 0.2 + 0.001, cab['kick'])
    # the countertop: the same L, a little proud at the two open sides
    K.prism([(x0, y0 - 0.025), (x1, y0 - 0.025), (x1, y0 + 0.60), (x0 + 0.60, y0 + 0.60), (x0 + 0.60, y1), (x0 - 0.0, y1)], 0.88, 0.92, cab['counter'], uv=2.0)
    return K


def wall_cab(w, name):
    def build(C):
        cab = CAB[C]
        K = Mesh(name)
        d, h = 0.34, 0.72
        cabinet_carcass(K, w, d, h, cab, doors=1 if w < 0.7 else 2, toe=0.0, handles=True)
        K.shift(0, d / 2, 0)
        return K
    build.__doc__ = 'A %.2f m wall cabinet, %.2f x 0.34 x 0.72 m (a wall item).' % (w, w)
    return build


wall_cab_60 = wall_cab(0.60, 'kitchen_wall_cab_60')
wall_cab_90 = wall_cab(0.90, 'kitchen_wall_cab_90')


def wall_cab_glass(C):
    """A 0.60 m wall cabinet with a glass door, 0.60 x 0.34 x 0.72 m (a wall item)."""
    cab = CAB[C]
    K = Mesh('kitchen_wall_cab_glass')
    d, h = 0.34, 0.72
    cabinet_carcass(K, 0.60, d, h, cab, doors=1, toe=0.0, glass=True)
    K.shift(0, d / 2, 0)
    return K


def pantry(C):
    """A tall pantry cabinet with two doors, 0.60 x 0.60 x 2.10 m."""
    cab = CAB[C]
    K = Mesh('kitchen_pantry')
    cabinet_carcass(K, 0.60, 0.60, 2.10, cab, doors=2)
    return K


def island(C):
    """A kitchen island with drawers, doors and a seating overhang, 1.60 x 0.90 x 0.92 m."""
    cab = CAB[C]
    K = Mesh('kitchen_island')
    w, d = 1.60, 0.70
    x0, x1 = -w / 2, w / 2
    yf = -d / 2 - 0.0
    # two cabinet bays on the front and an open back with the seating overhang
    K.box(x0 + 0.01, x1 - 0.01, yf + 0.07, yf + d - 0.2, 0.0, 0.10, cab['kick'])
    K.box(x0, x1, yf + 0.02, yf + d - 0.15, 0.10, 0.88, cab['body'], r=0.003, seg=1)
    third = (w - 0.02) / 3
    for i in range(3):
        a = x0 + 0.004 + i * third
        b = a + third - 0.008
        if i == 1:
            for k in range(3):
                za = 0.105 + k * 0.255
                door_panel(K, a, b, za, za + 0.25, yf, cab)
                pull(K, cab, (a + b) / 2, yf, za + 0.2, vertical=False, length=0.16)
        else:
            door_panel(K, a, b, 0.105, 0.875, yf, cab)
            pull(K, cab, b - 0.045 if i == 0 else a + 0.045, yf, 0.72, vertical=True, length=0.16)
    # the back: panelled end, the seating side open under a deep overhang on two legs
    K.box(x0 + 0.02, x0 + 0.04, yf + d - 0.15, yf + d - 0.12, 0.10, 0.88, cab['body'])
    for lx in (x0 + 0.04, x1 - 0.06):
        K.box(lx, lx + 0.06, yf + d - 0.10, yf + d - 0.04, 0.0, 0.88, cab['body'], r=0.004, seg=1)
    K.box(x0, x1, yf - 0.03, yf + d + 0.20, 0.88, 0.92, cab['counter'], r=0.004, seg=1, uv=2.0)
    K.shift(0, -0.10, 0)
    return K


def countertop_slab(C):
    """A freestanding countertop slab on four slim legs (a work table), 1.20 x 0.62 x 0.92 m."""
    cab = CAB[C]
    K = Mesh('kitchen_countertop')
    w, d = 1.20, 0.62
    K.box(-w / 2, w / 2, -d / 2, d / 2, 0.88, 0.92, cab['counter'], r=0.004, seg=1, uv=2.0)
    for lx in (-w / 2 + 0.04, w / 2 - 0.04):
        for ly in (-d / 2 + 0.04, d / 2 - 0.04):
            K.cyl((lx, ly, 0.0), (lx, ly, 0.88), 0.022, cab['pull'], seg=10, r1=0.016)
    K.box(-w / 2 + 0.04, w / 2 - 0.04, -d / 2 + 0.02, -d / 2 + 0.05, 0.84, 0.88, cab['body'])
    K.box(-w / 2 + 0.04, w / 2 - 0.04, d / 2 - 0.05, d / 2 - 0.02, 0.84, 0.88, cab['body'])
    return K


def open_shelf(C):
    """A wall shelf board on two black brackets with a rail for hooks, 1.00 x 0.24 x 0.30 m (a wall item)."""
    cab = CAB[C]
    K = Mesh('kitchen_open_shelf')
    w, d = 1.00, 0.24
    K.box(-w / 2, w / 2, -d / 2, d / 2, 0.26, 0.30, cab['body'], r=0.004, seg=1, uv=1.5)
    for bx in (-w / 2 + 0.10, w / 2 - 0.10):
        K.box(bx - 0.01, bx + 0.01, d / 2 - 0.012, d / 2, 0.0, 0.26, cab['pull'])
        K.box(bx - 0.01, bx + 0.01, -d / 2 + 0.02, d / 2, 0.24, 0.26, cab['pull'])
        K.cyl((bx, d / 2 - 0.006, 0.02), (bx, -d / 2 + 0.03, 0.245), 0.006, cab['pull'], seg=6)
    K.shift(0, d / 2, 0)
    return K


def kitchen_cart(C):
    """A rolling kitchen cart with a drawer, a lower shelf and a towel bar, 0.60 x 0.45 x 0.90 m."""
    cab = CAB[C]
    K = Mesh('kitchen_cart')
    w, d = 0.60, 0.45
    x0, x1, yf = -w / 2, w / 2, -d / 2
    for lx in (x0 + 0.03, x1 - 0.03):
        for ly in (yf + 0.03, -yf - 0.03):
            K.box(lx - 0.02, lx + 0.02, ly - 0.02, ly + 0.02, 0.06, 0.84, cab['body'], r=0.003, seg=1)
            K.cyl((lx, ly, 0.0), (lx, ly, 0.06), 0.02, cab['pull'], seg=10)
    K.box(x0, x1, yf, -yf, 0.84, 0.88, cab['counter'], r=0.004, seg=1, uv=2.0)
    K.box(x0 + 0.03, x1 - 0.03, yf + 0.03, -yf - 0.03, 0.20, 0.23, cab['body'], r=0.003, seg=1)             # the lower shelf
    K.box(x0 + 0.04, x1 - 0.04, yf + 0.02, -yf - 0.02, 0.62, 0.84, cab['body'])                               # the drawer box
    door_panel(K, x0 + 0.045, x1 - 0.045, 0.64, 0.82, yf + 0.01, cab)
    pull(K, cab, 0.0, yf + 0.01, 0.74, vertical=False, length=0.14)
    K.cyl((x0 - 0.03, yf + 0.02, 0.80), (x0 - 0.03, -yf - 0.02, 0.80), 0.008, cab['pull'], seg=8)             # the towel bar
    K.cyl((x0 + 0.03, yf + 0.02, 0.80), (x0 - 0.03, yf + 0.02, 0.80), 0.007, cab['pull'], seg=8)
    K.cyl((x0 + 0.03, -yf - 0.02, 0.80), (x0 - 0.03, -yf - 0.02, 0.80), 0.007, cab['pull'], seg=8)
    return K


# ------------------------------------------------------------------ tables and chairs

def _top_m(C):
    return CAB[C]['body']


def table_rect(C):
    """A rectangular dining table seating six, 1.60 x 0.90 x 0.76 m."""
    cab = CAB[C]
    K = Mesh('kitchen_table')
    w, d = 1.60, 0.90
    K.box(-w / 2, w / 2, -d / 2, d / 2, 0.72, 0.76, cab['body'], r=0.006, seg=2, uv=1.0)
    for lx in (-w / 2 + 0.07, w / 2 - 0.07):
        for ly in (-d / 2 + 0.07, d / 2 - 0.07):
            K.box(lx - 0.035, lx + 0.035, ly - 0.035, ly + 0.035, 0.0, 0.72, cab['body'], r=0.004, seg=1)
    K.box(-w / 2 + 0.10, w / 2 - 0.10, -d / 2 + 0.05, -d / 2 + 0.08, 0.64, 0.72, cab['body'])
    K.box(-w / 2 + 0.10, w / 2 - 0.10, d / 2 - 0.08, d / 2 - 0.05, 0.64, 0.72, cab['body'])
    K.box(-w / 2 + 0.05, -w / 2 + 0.08, -d / 2 + 0.10, d / 2 - 0.10, 0.64, 0.72, cab['body'])
    K.box(w / 2 - 0.08, w / 2 - 0.05, -d / 2 + 0.10, d / 2 - 0.10, 0.64, 0.72, cab['body'])
    return K


def table_round(C):
    """A round pedestal table seating four, 1.00 m across, 0.75 m high."""
    cab = CAB[C]
    K = Mesh('kitchen_table_round')
    K.cyl((0, 0, 0.71), (0, 0, 0.75), 0.50, cab['body'], seg=32, smooth=False)
    K.lathe([(0.0, 0.0), (0.24, 0.0), (0.24, 0.02), (0.10, 0.06), (0.06, 0.14), (0.055, 0.60), (0.12, 0.69), (0.12, 0.71), (0.0, 0.71)], cab['body'], at=(0, 0, 0), seg=20, hard=(1, 2))
    return K


def table_bistro(C):
    """A small round bistro table for two, 0.60 m across, 0.74 m high."""
    cab = CAB[C]
    K = Mesh('kitchen_table_bistro')
    K.cyl((0, 0, 0.71), (0, 0, 0.74), 0.30, cab['body'], seg=28, smooth=False)
    K.cyl((0, 0, 0.0), (0, 0, 0.71), 0.025, cab['pull'], seg=12)
    K.cyl((0, 0, 0.0), (0, 0, 0.02), 0.20, cab['pull'], seg=24, r1=0.19)
    return K


def chair_dining(C):
    """A dining chair with a slatted back, 0.44 x 0.46 x 0.90 m."""
    cab = CAB[C]
    K = Mesh('kitchen_chair')
    w, d = 0.44, 0.44
    K.box(-w / 2, w / 2, -d / 2, d / 2, 0.44, 0.48, cab['body'], r=0.006, seg=2)
    for lx in (-w / 2 + 0.03, w / 2 - 0.03):
        K.box(lx - 0.02, lx + 0.02, -d / 2 + 0.01, -d / 2 + 0.05, 0.0, 0.44, cab['body'], r=0.003, seg=1)
        K.box(lx - 0.02, lx + 0.02, d / 2 - 0.05, d / 2 - 0.01, 0.0, 0.44, cab['body'], r=0.003, seg=1)
        K.box(lx - 0.02, lx + 0.02, d / 2 - 0.05, d / 2 - 0.01, 0.48, 0.90, cab['body'], r=0.003, seg=1)
    K.box(-w / 2 + 0.01, w / 2 - 0.01, d / 2 - 0.045, d / 2 - 0.015, 0.84, 0.90, cab['body'], r=0.004, seg=1)
    for k in range(3):
        K.box(-w / 2 + 0.05, w / 2 - 0.05, d / 2 - 0.04, d / 2 - 0.02, 0.52 + k * 0.10, 0.58 + k * 0.10, cab['body'], r=0.002, seg=1)
    return K


def stool_bar(C):
    """A counter-height bar stool with a round seat and a foot rail, 0.38 x 0.38 x 0.66 m."""
    cab = CAB[C]
    K = Mesh('kitchen_stool')
    K.cyl((0, 0, 0.62), (0, 0, 0.66), 0.19, cab['body'], seg=24, smooth=False)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        K.cyl((0.14 * math.cos(a), 0.14 * math.sin(a), 0.0), (0.12 * math.cos(a), 0.12 * math.sin(a), 0.62), 0.016, cab['pull'], seg=8)
    for z in (0.22,):
        K.cyl((0.0, 0.0, z), (0.0, 0.0, z + 0.015), 0.16, cab['pull'], seg=24, smooth=False)
    return K


def bench(C):
    """A kitchen bench seating two or three, 1.20 x 0.36 x 0.46 m."""
    cab = CAB[C]
    K = Mesh('kitchen_bench')
    w, d = 1.20, 0.36
    K.box(-w / 2, w / 2, -d / 2, d / 2, 0.42, 0.46, cab['body'], r=0.006, seg=2)
    for lx in (-w / 2 + 0.05, w / 2 - 0.05):
        K.box(lx - 0.025, lx + 0.025, -d / 2 + 0.03, d / 2 - 0.03, 0.0, 0.42, cab['body'], r=0.003, seg=1)
    K.box(-w / 2 + 0.05, w / 2 - 0.05, -0.01, 0.01, 0.12, 0.17, cab['body'])
    return K


# ------------------------------------------------------------------ accessories

def trash_can(F):
    """A step-on kitchen trash can with a pedal, 0.30 x 0.30 x 0.62 m."""
    K = Mesh('kitchen_trash_can')
    body = F.steel if F.name == 'stainless' else (F.white if F.name == 'white' else F.black)
    K.lathe([(0.0, 0.0), (0.135, 0.0), (0.15, 0.02), (0.15, 0.55), (0.0, 0.55)], body, at=(0, 0, 0.0), seg=28, hard=(1, 3))
    K.cyl((0, 0, 0.55), (0, 0, 0.60), 0.155, body, seg=28, r1=0.152)
    K.cyl((0, 0, 0.60), (0, 0, 0.62), 0.07, F.black, seg=16, r1=0.05)
    K.box(-0.04, 0.04, -0.20, -0.14, 0.005, 0.03, F.rubber)
    K.box(-0.012, 0.012, -0.153, -0.147, 0.03, 0.40, F.rubber)
    return K


def pot_stock(F):
    """A stainless stock pot with a lid, 0.32 x 0.24 x 0.26 m."""
    K = Mesh('kitchen_pot_stock')
    K.lathe([(0.0, 0.0), (0.105, 0.0), (0.12, 0.015), (0.12, 0.215), (0.125, 0.22), (0.0, 0.22)], F.steel, at=(0, 0, 0.0), seg=28, hard=(1, 3))
    K.lathe([(0.0, 0.22), (0.13, 0.22), (0.13, 0.226), (0.12, 0.24), (0.04, 0.255), (0.0, 0.258)], F.steel, at=(0, 0, 0.0), seg=28, hard=(1,))
    K.cyl((0, 0, 0.256), (0, 0, 0.275), 0.012, F.rubber, seg=10)
    K.cyl((0, 0, 0.275), (0, 0, 0.29), 0.022, F.rubber, seg=12, r1=0.016)
    K.cyl((-0.12, 0, 0.17), (-0.20, 0, 0.17), 0.007, F.rubber, seg=8)
    K.cyl((0.12, 0, 0.17), (0.20, 0, 0.17), 0.007, F.rubber, seg=8)
    return K


def saucepan(F):
    """A saucepan with a long handle, 0.38 x 0.17 x 0.10 m."""
    K = Mesh('kitchen_saucepan')
    K.lathe([(0.0, 0.0), (0.075, 0.0), (0.085, 0.012), (0.085, 0.10), (0.088, 0.104), (0.0, 0.104)], F.steel, at=(0, 0, 0.0), seg=24, hard=(1, 3))
    K.cyl((0.08, 0, 0.085), (0.21, 0, 0.095), 0.009, F.rubber, seg=8)
    K.box(0.085, 0.100, -0.012, 0.012, 0.075, 0.095, F.steel)
    K.cyl((0, 0, 0.104), (0, 0, 0.11), 0.088, F.steel, seg=24, r1=0.088)
    return K


def skillet(F):
    """A cast-iron skillet, 0.42 x 0.28 x 0.06 m."""
    K = Mesh('kitchen_skillet')
    K.lathe([(0.0, 0.0), (0.095, 0.0), (0.125, 0.045), (0.13, 0.05), (0.12, 0.05), (0.0, 0.02)], F.iron, at=(0, 0, 0.0), seg=28, hard=(2, 3))
    K.lathe([(0.12, 0.05), (0.095, 0.01), (0.0, 0.012)], F.rubber, at=(0, 0, 0.0), seg=28)
    K.box(0.12, 0.28, -0.017, 0.017, 0.036, 0.05, F.iron, r=0.006, seg=1)
    K.cyl((0.28, 0, 0.036), (0.28, 0, 0.05), 0.017, F.iron, seg=12)
    return K


def cutting_board(C):
    """A thick wooden cutting board with a handle hole, 0.40 x 0.28 x 0.04 m."""
    K = Mesh('kitchen_cutting_board')
    mt = {'oak': _mat('BoardOak', (0.75, 0.58, 0.38), 0.5, tex='butcher'), 'white': _mat('BoardMaple', (0.9, 0.78, 0.58), 0.5, tex='butcher'), 'black': _mat('BoardWalnut', (0.4, 0.27, 0.17), 0.5, tex='walnut')}[C]
    K.rbox(-0.20, 0.20, -0.14, 0.14, 0.0, 0.04, mt, 0.02, rv=0.006, seg=3, uv=2.0)
    return K


def dish_rack(F):
    """A dish drying rack with a drip tray, 0.46 x 0.34 x 0.20 m."""
    K = Mesh('kitchen_dish_rack')
    K.box(-0.23, 0.23, -0.17, 0.17, 0.0, 0.025, F.rubber, r=0.004, seg=1)
    for k in range(9):
        K.cyl((-0.21 + k * 0.0525, -0.15, 0.025), (-0.21 + k * 0.0525, -0.15, 0.18), 0.004, F.chrome, seg=6)
        K.cyl((-0.21 + k * 0.0525, 0.15, 0.025), (-0.21 + k * 0.0525, 0.15, 0.18), 0.004, F.chrome, seg=6)
    K.cyl((-0.215, -0.15, 0.18), (0.215, -0.15, 0.18), 0.004, F.chrome, seg=6)
    K.cyl((-0.215, 0.15, 0.18), (0.215, 0.15, 0.18), 0.004, F.chrome, seg=6)
    for y in (-0.15, -0.05, 0.05, 0.15):
        K.cyl((-0.215, y, 0.07), (0.215, y, 0.07), 0.003, F.chrome, seg=6)
    return K


def utensil_crock(F):
    """A ceramic crock of utensils, 0.14 x 0.14 x 0.30 m."""
    K = Mesh('kitchen_utensil_crock')
    body = F.steel if F.name == 'stainless' else (F.white if F.name == 'white' else F.black)
    K.lathe([(0.0, 0.0), (0.06, 0.0), (0.068, 0.015), (0.07, 0.14), (0.072, 0.15), (0.064, 0.15), (0.0, 0.01)], body, at=(0, 0, 0.0), seg=22, hard=(1, 4))
    for ux, uy, tilt, ln, mk in ((-0.02, 0.0, -0.25, 0.30, F.rubber), (0.025, 0.01, 0.2, 0.28, F.chrome), (0.0, -0.025, 0.05, 0.27, F.rubber), (0.03, -0.015, 0.35, 0.26, F.rubber)):
        K.cyl((ux, uy, 0.04), (ux + tilt * 0.1, uy + 0.0, 0.04 + ln * 0.9), 0.007, mk, seg=6)
    K.box(-0.022, 0.0, -0.02, 0.0, 0.22, 0.29, F.rubber)
    return K


def fruit_bowl(C):
    """A wooden fruit bowl with an apple, a lemon and a banana, 0.30 x 0.30 x 0.14 m."""
    K = Mesh('kitchen_fruit_bowl')
    wood = CAB['oak']['body'] if C == 'oak' else (CAB['white']['body'] if C == 'white' else CAB['black']['body'])
    K.lathe([(0.0, 0.0), (0.06, 0.0), (0.08, 0.01), (0.14, 0.05), (0.15, 0.065), (0.145, 0.067), (0.135, 0.05), (0.07, 0.02), (0.0, 0.016)], wood, at=(0, 0, 0.0), seg=24, hard=(1, 4, 5))
    red = material('FruitRed', (0.75, 0.10, 0.08), 0.45)
    yellow = material('FruitYellow', (0.95, 0.80, 0.18), 0.5)
    K.lathe([(0.0, 0.0), (0.03, 0.005), (0.04, 0.03), (0.032, 0.06), (0.0, 0.058)], red, at=(-0.03, 0.02, 0.02), seg=14)
    K.lathe([(0.0, 0.0), (0.03, 0.01), (0.036, 0.04), (0.02, 0.07), (0.0, 0.075)], yellow, at=(0.045, -0.02, 0.02), seg=14)
    K.lathe([(0.0, 0.0), (0.028, 0.01), (0.034, 0.035), (0.0, 0.062)], red, at=(0.0, -0.06, 0.03), seg=12)
    K.cyl((-0.06, 0.05, 0.05), (0.07, 0.07, 0.06), 0.014, yellow, seg=8, r1=0.012)
    return K


def canisters(F):
    """A set of three lidded canisters, 0.45 x 0.16 x 0.28 m."""
    K = Mesh('kitchen_canisters')
    body = F.steel if F.name == 'stainless' else (F.white if F.name == 'white' else F.black)
    for i, (h, r) in enumerate(((0.28, 0.075), (0.23, 0.07), (0.18, 0.065))):
        cx = -0.15 + i * 0.15
        K.lathe([(0.0, 0.0), (r - 0.01, 0.0), (r, 0.01), (r, h - 0.03), (r + 0.004, h - 0.025), (r + 0.004, h - 0.01), (0.0, h - 0.008)], body, at=(cx, 0, 0.0), seg=22, hard=(1, 3, 4))
        K.cyl((cx, 0, h - 0.01), (cx, 0, h + 0.012), r * 0.55, F.rubber, seg=12, r1=r * 0.5)
        K.cyl((cx, 0, h + 0.012), (cx, 0, h + 0.03), 0.012, F.chrome, seg=10)
    return K


def paper_towel_holder(F):
    """A paper towel holder on a weighted base, 0.20 x 0.20 x 0.34 m."""
    K = Mesh('kitchen_paper_towels')
    K.cyl((0, 0, 0), (0, 0, 0.02), 0.095, F.trim if F.name != 'black' else F.rubber, seg=24)
    K.cyl((0, 0, 0.02), (0, 0, 0.34), 0.008, F.trim if F.name != 'black' else F.rubber, seg=8)
    K.lathe([(0.055, 0.04), (0.10, 0.04), (0.10, 0.30), (0.055, 0.30)], material('PaperWhite', (0.96, 0.96, 0.94), 0.9), at=(0, 0, 0.0), seg=22, hard=(0, 1, 2, 3))
    K.cyl((0, 0, 0.30), (0, 0, 0.31), 0.103, material('PaperWhite', (0.96, 0.96, 0.94), 0.9), seg=22)
    K.cyl((0, 0, 0.345), (0, 0, 0.36), 0.02, F.trim if F.name != 'black' else F.rubber, seg=10)
    return K


def bread_box(F):
    """A bread box with a roll-top lid, 0.38 x 0.25 x 0.24 m."""
    K = Mesh('kitchen_bread_box')
    body = F.steel if F.name == 'stainless' else (F.white if F.name == 'white' else F.black)
    K.rbox(-0.19, 0.19, -0.125, 0.125, 0.0, 0.17, body, 0.012, rv=0.008, seg=2)
    K.cyl((-0.19, 0.0, 0.17), (0.19, 0.0, 0.17), 0.125, body, seg=16, smooth=True)
    K.rbox(-0.18, 0.18, -0.10, -0.12, 0.05, 0.14, F.rubber, 0.004, seg=1)
    K.box(-0.03, 0.03, -0.128, -0.12, 0.08, 0.11, F.chrome)
    return K


def spice_rack(C):
    """A wall spice rack with two shelves and a row of jars, 0.50 x 0.12 x 0.40 m (a wall item)."""
    cab = CAB[C]
    K = Mesh('kitchen_spice_rack')
    w, d = 0.50, 0.12
    K.box(-w / 2, -w / 2 + 0.015, -d / 2, d / 2, 0.0, 0.40, cab['body'])
    K.box(w / 2 - 0.015, w / 2, -d / 2, d / 2, 0.0, 0.40, cab['body'])
    for z in (0.0, 0.19, 0.38):
        K.box(-w / 2, w / 2, -d / 2, d / 2, z, z + 0.02, cab['body'])
    K.box(-w / 2, w / 2, d / 2 - 0.01, d / 2, 0.0, 0.40, cab['body'])
    lids = [material('SpiceLid%d' % i, c, 0.5) for i, c in enumerate(((0.85, 0.2, 0.1), (0.9, 0.7, 0.15), (0.3, 0.55, 0.2), (0.6, 0.35, 0.15), (0.85, 0.85, 0.82)))]
    for shelf, z in enumerate((0.02, 0.21)):
        for k in range(5):
            jx = -0.2 + k * 0.1
            K.cyl((jx, 0.0, z), (jx, 0.0, z + 0.11), 0.03, cab['glass'], seg=12)
            K.cyl((jx, 0.0, z + 0.11), (jx, 0.0, z + 0.14), 0.031, lids[(k + shelf) % 5], seg=12)
    K.shift(0, d / 2, 0)
    return K


def pot_rack(F):
    """A hanging pot rack with a bar, hooks and three pans, 0.80 x 0.30 x 0.55 m (a wall item)."""
    K = Mesh('kitchen_pot_rack')
    w = 0.80
    K.box(-w / 2, w / 2, 0.0, 0.012, 0.50, 0.55, F.iron)
    K.cyl((-w / 2 + 0.02, 0.0, 0.52), (-w / 2 + 0.02, -0.18, 0.52), 0.01, F.iron, seg=8)
    K.cyl((w / 2 - 0.02, 0.0, 0.52), (w / 2 - 0.02, -0.18, 0.52), 0.01, F.iron, seg=8)
    K.cyl((-w / 2 + 0.02, -0.18, 0.52), (w / 2 - 0.02, -0.18, 0.52), 0.011, F.iron, seg=10)
    for k, rr in enumerate((0.075, 0.09, 0.07)):
        hx = -0.25 + k * 0.25
        K.cyl((hx, -0.18, 0.52), (hx, -0.18, 0.48), 0.004, F.chrome, seg=6)
        K.cyl((hx, -0.18, 0.48), (hx, -0.18, 0.43), 0.006, F.chrome, seg=6)
        K.cyl((hx, -0.18, 0.43), (hx, -0.18, 0.40), 0.008, F.rubber, seg=8)
        # a pan hanging by its handle: the pan is a flat disc in front, the handle goes up to the hook
        K.cyl((hx, -0.18, 0.40), (hx, -0.18, 0.32), 0.009, F.rubber, seg=8)
        K.cyl((hx, -0.20 - rr, 0.16), (hx, -0.18 - 0.012, 0.16), 0.008, F.rubber, seg=6)
        K.lathe([(0.0, 0.0), (rr, 0.0), (rr, 0.035), (0.0, 0.035)], F.steel, at=(hx, -0.20 - rr, 0.12), seg=18, hard=(1,))
    K.shift(0, 0.012, 0)
    return K


def knife_block(C):
    """A wooden knife block with five knife handles, 0.17 x 0.12 x 0.26 m."""
    K = Mesh('kitchen_knife_block')
    wood = CAB['oak']['body'] if C == 'oak' else (CAB['white']['body'] if C == 'white' else CAB['black']['body'])
    K.box(-0.085, 0.085, -0.06, 0.06, 0.0, 0.17, wood, r=0.004, seg=1)
    K.box(-0.085, 0.085, -0.045, 0.06, 0.17, 0.19, wood, r=0.004, seg=1)
    black = material('KnifeHandle', (0.04, 0.04, 0.045), 0.5)
    steel = material('KnifeSteel', (0.8, 0.82, 0.84), 0.3, 1.0)
    for k in range(5):
        kx = -0.065 + k * 0.0325
        K.box(kx - 0.009, kx + 0.009, -0.03, -0.012, 0.19, 0.25 + (0.01 if k in (1, 3) else 0.0), black, r=0.003, seg=1)
        K.box(kx - 0.003, kx + 0.003, -0.025, -0.017, 0.185, 0.19, steel)
    return K


# Models that take a CAB key ('white', 'oak', 'black') instead of an appliance finish
CAB_KEYS = {}
CAB_MODELS = {'base_cab_60', 'base_cab_90', 'base_cab_drawers', 'corner_base', 'wall_cab_60', 'wall_cab_90', 'wall_cab_glass', 'pantry', 'island', 'countertop_slab',
              'open_shelf', 'kitchen_cart', 'table_rect', 'table_round', 'table_bistro', 'chair_dining', 'stool_bar', 'bench', 'cutting_board', 'fruit_bowl', 'spice_rack', 'knife_block'}
