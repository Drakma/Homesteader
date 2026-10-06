"""
Builds every internet item's model (assets/internet/net_*) as a GLB in headless Blender: free, local, low-poly (no Meshy). The shapes are plain;
the DETAIL is painted (tools/net_pictures.py): port panels, status lights, vents, labels, cable windings, put on as pictures.

    python tools/net_pictures.py
    blender --background --python tools/make_internet.py                 (-- <id> <id> = only those)
    python tools/render_icon_from_model.py assets/internet/<id>/<id>.glb assets/internet/<id>/<id>.png      (each)

An item keeps its manifest (name, price, bandwidth and the rest); its model entry, footprint and dimensions are rewritten, the old OBJ / MTL /
odd-named GLB files are removed, and the three old stubs (NEW below) get a real name, description and price.

Conventions: 1 unit = 1 m, the ground at z = 0, centred on x and y, the FRONT facing -y.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import case_labels  # noqa: E402
import make_simple_props as props  # noqa: E402    (Kit, mat, save)

NET = os.path.join(props.ROOT, 'assets', 'internet')
T = Matrix.Translation
mat = props.mat
E = 0.0007      # a picture stands this far off the face it is on


def RX(a):
    return Matrix.Rotation(a, 4, 'X')


def RZ(a):
    return Matrix.Rotation(a, 4, 'Z')


# ------------------------------------------------------------------ pictures on faces (each quad: bottom left, bottom right, top right, top left as its reader sees it)

def fq(x0, x1, z0, z1, y):
    return [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)]


def bq(x0, x1, z0, z1, y):
    return [(x1, y, z0), (x0, y, z0), (x0, y, z1), (x1, y, z1)]


def tq(x0, x1, y0, y1, z):
    return [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]


def lq(y0, y1, z0, z1, x):
    return [(x, y1, z0), (x, y0, z0), (x, y0, z1), (x, y1, z1)]


def rq(y0, y1, z0, z1, x):
    return [(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)]


def cq(r, z0, z1, n, at=(0.0, 0.0), a0=0.0, a1=2 * math.pi):
    """A band round a cylinder, as n quads (each shows the whole picture: for windings and cloth, which repeat)."""
    out = []
    for k in range(n):
        p, q = a0 + (a1 - a0) * k / n, a0 + (a1 - a0) * (k + 1) / n
        c = lambda a, z: (at[0] + r * math.cos(a), at[1] + r * math.sin(a), z)
        out.append([c(p, z0), c(q, z0), c(q, z1), c(p, z1)])
    return out


def moved(quads, m):
    return [[tuple(m @ Vector(c)) for c in q] for q in quads]


def pictures(obj, *pairs):
    for name, quads in pairs:
        obj = case_labels.add_flat(obj, name, quads)
    return obj


def feet(K, W, D, m, h=0.004, r=0.008):
    for sx in (-1, 1):
        for sy in (-1, 1):
            K.lathe([(r, 0.0), (r, h), (0.0, h)], m, 8, T((sx * (W / 2 - 0.02), sy * (D / 2 - 0.02), 0.0)))


def tripod(K, m, h, spread=0.3, r=0.012):
    """Three legs meeting at the mast at height h, a foot pad under each."""
    for k in range(3):
        a = math.radians(90 + 120 * k)
        foot = (spread * math.cos(a), spread * math.sin(a), 0.01)
        K.tube(foot, (0, 0, h), r, r, m, 6, m, m)
        K.lathe([(0.03, 0.0), (0.03, 0.012), (0.0, 0.012)], m, 8, T((foot[0], foot[1], 0.0)))
        K.tube((foot[0] * 0.55, foot[1] * 0.55, h * 0.45), (0, 0, h * 0.25), r * 0.7, r * 0.7, m, 5)   # a brace back to the mast


def coax(K, pts, m, r=0.004):
    K.path(pts, r, m, 6)


# ------------------------------------------------------------------ the items

def omni():
    K = props.Kit()
    steel = mat('MastSteel', (0.62, 0.65, 0.67), 0.4)
    white = mat('Radome', (0.93, 0.93, 0.9), 0.5)
    black = mat('CoaxBlack', (0.03, 0.03, 0.035), 0.6)
    brass = mat('NConnector', (0.78, 0.6, 0.24), 0.35)
    K.lathe([(0.11, 0.0), (0.11, 0.012), (0.03, 0.02), (0.0, 0.02)], steel, 14)               # a weighted base
    K.tube((0, 0, 0.015), (0, 0, 0.3), 0.014, 0.014, steel, 10, None, steel)
    K.bx((0.05, 0.045, 0.06), (0, -0.012, 0.25), steel)                                      # the clamp
    for z in (0.235, 0.265):
        K.tube((-0.03, -0.036, z), (0.03, -0.036, z), 0.004, 0.004, brass, 6, brass, brass)   # its bolts
    y = -0.045
    K.tube((0, y, 0.2), (0, y, 0.23), 0.009, 0.009, brass, 8, brass)                          # the connector under the antenna
    K.lathe([(0.016, 0.0), (0.016, 0.03), (0.013, 0.04), (0.013, 0.6), (0.009, 0.62), (0.0, 0.62)], white, 10, T((0, y, 0.23)))
    coax(K, [(0, y, 0.2), (0.01, y - 0.02, 0.15), (0.03, y - 0.01, 0.06), (0.09, y + 0.02, 0.022), (0.2, y + 0.03, 0.006)], black)
    obj = K.done('omni')
    return pictures(obj, ('net_label_omni', [fq(-0.011, 0.011, 0.4, 0.411 + 0.0, y - 0.0137 - E)]))


def yagi():
    K = props.Kit()
    steel = mat('MastSteel', (0.62, 0.65, 0.67), 0.4)
    alu = mat('YagiAluminium', (0.8, 0.82, 0.84), 0.3)
    black = mat('CoaxBlack', (0.03, 0.03, 0.035), 0.6)
    grey = mat('DipoleBox', (0.3, 0.31, 0.33), 0.6)
    H = 1.15
    tripod(K, steel, 0.5, 0.32)
    K.tube((0, 0, 0.02), (0, 0, H), 0.016, 0.016, steel, 10, steel, steel)
    zb = 1.02
    K.bx((0.026, 0.74, 0.026), (0, -0.12, zb), alu)                                         # the boom, pointing forward
    K.bx((0.06, 0.05, 0.07), (0, 0.0, zb - 0.01), steel)                                      # the mast clamp
    ys = [0.22] + [0.12 - 0.075 * k for k in range(8)]
    for k, y in enumerate(ys):
        half = 0.2 if k == 0 else 0.17 - 0.009 * k
        K.tube((-half, y, zb + 0.014), (half, y, zb + 0.014), 0.007, 0.007, alu, 6, alu, alu)
    K.bx((0.05, 0.04, 0.035), (0, 0.17, zb - 0.02), grey)                                     # the driven element's housing
    coax(K, [(0, 0.17, zb - 0.04), (0.01, 0.1, zb - 0.1), (0.02, 0.03, zb - 0.2), (0.02, 0.02, 0.5), (0.05, 0.05, 0.1), (0.2, 0.12, 0.006)], black)
    obj = K.done('yagi')
    w = 0.07
    return pictures(obj, ('net_label_yagi', [lq(-0.3, -0.3 + w, zb - 0.013, zb + 0.013, -0.013 - E)]))


def access_point():
    K = props.Kit()
    steel = mat('MastSteel', (0.62, 0.65, 0.67), 0.4)
    white = mat('ApWhite', (0.93, 0.93, 0.9), 0.5)
    black = mat('CoaxBlack', (0.03, 0.03, 0.035), 0.6)
    K.lathe([(0.12, 0.0), (0.12, 0.012), (0.03, 0.02), (0.0, 0.02)], steel, 14)
    K.tube((0, 0, 0.015), (0, 0, 0.62), 0.016, 0.016, steel, 10, None, steel)
    W, D, Hh, z0 = 0.17, 0.06, 0.25, 0.32
    y = -0.02 - D / 2
    K.bx((W, D, Hh), (0, y, z0 + Hh / 2), white)
    K.bx((W - 0.02, D, Hh + 0.012), (0, y, z0 + Hh / 2), white)                               # rounded off top and bottom
    for z in (z0 + 0.06, z0 + Hh - 0.06):
        K.lathe([(0.02, -0.007), (0.02, 0.007)], steel, 10, T((0, 0, z)))                     # the band clamps round the pole
        K.bx((0.05, 0.03, 0.014), (0, -0.012, z), steel)
    for sx in (-1, 1):                                                                        # two stub antennas
        K.tube((sx * 0.055, y, z0 + Hh), (sx * 0.055, y, z0 + Hh + 0.13), 0.007, 0.006, white, 8, None, white)
        K.lathe([(0.01, 0.0), (0.01, 0.014)], black, 8, T((sx * 0.055, y, z0 + Hh)))
    K.lathe([(0.012, 0.0), (0.012, -0.02), (0.008, -0.025)], black, 8, T((0, y, z0 - 0.006)))   # the cable gland
    coax(K, [(0, y, z0 - 0.03), (0.0, y + 0.01, 0.2), (0.02, y + 0.02, 0.05), (0.1, y + 0.05, 0.022), (0.2, y + 0.06, 0.006)], black, 0.0035)
    obj = K.done('ap')
    return pictures(obj, ('net_ap_face', [fq(-W / 2 + 0.006, W / 2 - 0.006, z0 + 0.004, z0 + Hh - 0.004, y - D / 2 - E)]))


def arrestor():
    K = props.Kit()
    alu = mat('ArrestorAluminium', (0.69, 0.71, 0.73), 0.35)
    dark = mat('FlangeDark', (0.45, 0.47, 0.49), 0.4)
    brass = mat('GroundStud', (0.78, 0.6, 0.24), 0.35)
    green = mat('GroundWire', (0.1, 0.5, 0.16), 0.6)
    W, D, H = 0.11, 0.055, 0.03
    K.bx((W, D, H), (0, 0, H / 2 + 0.003), alu)
    K.bx((W * 0.7, D + 0.03, 0.003), (0, 0, 0.0015), dark)                                    # the mounting flange, a screw hole each side
    for sy in (-1, 1):
        K.lathe([(0.004, 0.0), (0.004, 0.0035)], brass, 6, T((0, sy * (D / 2 + 0.008), 0.0)))
    K.lathe([(0.004, 0.0), (0.004, 0.012), (0.007, 0.012), (0.007, 0.016), (0.0, 0.016)], brass, 6, T((0, D / 2 - 0.012, H + 0.003)))   # the ground stud
    K.path([(0, D / 2 - 0.012, H + 0.012), (0.0, D / 2 + 0.01, H + 0.012), (0.01, D / 2 + 0.03, 0.01), (0.04, D / 2 + 0.07, 0.004)], 0.003, green, 6)
    obj = K.done('arrestor')
    z0, z1 = 0.003 + 0.002, H + 0.003 - 0.002
    return pictures(obj,
                    ('net_arrestor_top', [tq(-W / 2 + 0.004, W / 2 - 0.004, -D / 2 + 0.002, D / 2 - 0.016, H + 0.003 + E)]),
                    ('net_port_alu', [lq(-D / 2 + 0.002, D / 2 - 0.002, z0, z1, -W / 2 - E), rq(-D / 2 + 0.002, D / 2 - 0.002, z0, z1, W / 2 + E)]))


def patch_cable(loops, R):
    def build():
        K = props.Kit()
        blue = mat('Cat6Blue', (0.1, 0.3, 0.72), 0.55)
        clear = mat('PlugClear', (0.82, 0.86, 0.88), 0.25)
        gold = mat('PlugGold', (0.83, 0.68, 0.26), 0.3)
        tie = mat('TieBlack', (0.05, 0.05, 0.055), 0.7)
        r = 0.0035
        ring = [(r * math.cos(a), r * math.sin(a)) for a in [2 * math.pi * k / 6 for k in range(6)]]
        n = 0
        top = 0.0
        for layer in range(2 if loops > 5 else 1):
            for k in range(loops // (2 if loops > 5 else 1)):
                rr = R - layer * 0.009 + (0.002 if k % 2 else 0.0)
                z = r + k * r * 1.85
                K.lathe([(rr + x, z + y) for x, y in ring], blue, 22, None, closed=True)
                top = max(top, z + r)
                n += 1
        for a in (math.radians(40), math.radians(220)):                                        # two hook-and-loop ties round the coil
            K.box((0.03, 0.016, top + 0.004), RZ(a) @ T((R - 0.004, 0, (top + 0.004) / 2 - 0.001)), tie)
        for k, a in enumerate((math.radians(-60), math.radians(-120))):                         # the two ends: a boot and a plug each
            p = Vector((R * math.cos(a), R * math.sin(a), top - r))
            d = Vector((math.cos(a) * 0.5, -1.0, 0.0)).normalized()
            K.tube(p, p + d * 0.03, r, r * 1.6, blue, 6)
            m = T(p + d * 0.045) @ RZ(math.atan2(d.y, d.x))
            K.box((0.03, 0.012, 0.009), m, blue)                                              # the boot
            K.box((0.022, 0.0115, 0.008), m @ T((0.026, 0, 0)), clear)                        # the plug
            K.box((0.008, 0.0095, 0.002), m @ T((0.032, 0, 0.004)), gold)                     # its contacts
            K.box((0.014, 0.005, 0.002), m @ T((0.02, 0, 0.0055)), clear)                     # the latch
        obj = K.done('patch')
        a = math.radians(220)
        m = RZ(a) @ T((R - 0.004, 0, top + 0.003 + E))
        return pictures(obj, ('net_label_patch', moved([tq(-0.0145, 0.0145, -0.0075, 0.0075, 0.0)], m @ RZ(math.pi / 2))))
    return build


def panel_dish(W, L, t, tilt, pole):
    """A flat satellite antenna: a white panel tilted to the sky, on a kickstand (pole 0) or on a pipe mount."""
    def build():
        K = props.Kit()
        white = mat('PanelWhite', (0.92, 0.92, 0.9), 0.45)
        grey = mat('PanelBack', (0.23, 0.24, 0.26), 0.6)
        steel = mat('MountSteel', (0.62, 0.65, 0.67), 0.4)
        black = mat('CableBlack', (0.03, 0.03, 0.035), 0.6)
        a = math.radians(tilt)
        if pole > 0:
            K.lathe([(0.16, 0.0), (0.16, 0.014), (0.04, 0.024), (0.0, 0.024)], steel, 14)
            K.tube((0, 0, 0.02), (0, 0, pole), 0.02, 0.02, steel, 10, None, steel)
            K.bx((0.07, 0.07, 0.09), (0, 0, pole - 0.02), grey)                               # the head that tilts and turns
            hinge = Vector((0, -0.02, pole + 0.03))
        else:
            hinge = Vector((0, 0.02, L * 0.5 * math.sin(a) + 0.02))
        M = T(hinge) @ RX(a)                                                                # the panel's own frame: x across, y up its length, z out of its face
        K.box((W, L, t), M, white)
        K.box((W - 0.03, L - 0.03, t * 0.6), M @ T((0, 0, -t * 0.7)), grey)                   # the thicker back
        K.box((0.09, 0.09, 0.05), M @ T((0, 0, -t * 1.2 - 0.02)), grey)                       # the motor housing
        if pole <= 0:
            foot = Vector((0, hinge.y + 0.26, 0.0))
            top = M @ Vector((0, 0.02, -t * 1.2 - 0.03))
            K.tube(top, foot + Vector((0, 0, 0.012)), 0.014, 0.014, steel, 8, steel, steel)   # the kickstand
            K.bx((0.26, 0.03, 0.016), (0, foot.y, 0.008), steel)
            low = M @ Vector((0, -L / 2, 0))
            K.bx((W * 0.7, 0.03, 0.016), (0, low.y + 0.005, 0.008), steel)                    # the bar the low edge rests on
        port = M @ Vector((0.03, -L * 0.2, -t * 1.2))
        end = (0.25, 0.3, 0.006) if pole <= 0 else (0.22, 0.2, 0.006)
        coax(K, [tuple(port), (port.x + 0.02, port.y + 0.05, max(0.03, port.z - 0.12)), (end[0] * 0.6, end[1] * 0.8, 0.02), end], black)
        obj = K.done('dish')
        return pictures(obj,
                        ('net_panel_face', moved([tq(-W / 2 + 0.003, W / 2 - 0.003, -L / 2 + 0.003, L / 2 - 0.003, t / 2 + E)], M)),
                        ('net_panel_back', moved([[(W / 2 - 0.02, -L / 2 + 0.02, -t - E), (-W / 2 + 0.02, -L / 2 + 0.02, -t - E), (-W / 2 + 0.02, L / 2 - 0.02, -t - E), (W / 2 - 0.02, L / 2 - 0.02, -t - E)]], M)))
    return build


def injector():
    K = props.Kit()
    black = mat('InjectorBlack', (0.06, 0.06, 0.065), 0.55)
    cord = mat('CordBlack', (0.03, 0.03, 0.035), 0.6)
    rubber = mat('Rubber', (0.1, 0.1, 0.1), 0.9)
    W, D, H = 0.13, 0.062, 0.034
    z0 = 0.003
    K.bx((W, D, H), (0, 0, z0 + H / 2), black)
    K.bx((W - 0.008, D - 0.008, 0.002), (0, 0, z0 + H + 0.001), black)
    feet(K, W, D, rubber, 0.003, 0.006)
    K.lathe([(0.007, 0.0), (0.007, 0.012), (0.005, 0.02)], cord, 8, T((0.03, D / 2, z0 + H / 2)) @ RX(-math.pi / 2))   # the strain relief
    coax(K, [(0.03, D / 2 + 0.018, z0 + H / 2), (0.035, D / 2 + 0.05, 0.012), (0.07, D / 2 + 0.09, 0.005), (0.14, D / 2 + 0.1, 0.005)], cord, 0.0035)
    obj = K.done('injector')
    return pictures(obj,
                    ('net_injector_top', [tq(-W / 2 + 0.006, W / 2 - 0.006, -D / 2 + 0.005, D / 2 - 0.005, z0 + H + 0.002 + E)]),
                    ('net_port_in', [lq(-D / 2 + 0.004, D / 2 - 0.004, z0 + 0.003, z0 + H - 0.003, -W / 2 - E)]),
                    ('net_port_out', [rq(-D / 2 + 0.004, D / 2 - 0.004, z0 + 0.003, z0 + H - 0.003, W / 2 + E)]))


def j_mast():
    K = props.Kit()
    galv = mat('MastGalvanized', (0.66, 0.68, 0.7), 0.35)
    dark = mat('MastBracket', (0.45, 0.47, 0.49), 0.45)
    bolt = mat('BoltHead', (0.3, 0.31, 0.33), 0.4)
    cap = mat('MastCap', (0.05, 0.05, 0.055), 0.7)
    K.bx((0.16, 0.12, 0.006), (0, 0, 0.003), dark)                                             # the foot plate and its four lag bolts
    for sx in (-1, 1):
        for sy in (-1, 1):
            K.lathe([(0.008, 0.0), (0.008, 0.005), (0.0, 0.005)], bolt, 6, T((sx * 0.06, sy * 0.042, 0.006)))
    for sx in (-1, 1):                                                                         # the two cheeks the mast pivots between
        K.bx((0.005, 0.07, 0.05), (sx * 0.024, 0, 0.031), dark)
    K.tube((-0.034, 0, 0.036), (0.034, 0, 0.036), 0.005, 0.005, bolt, 6, bolt, bolt)           # the pivot bolt
    r = 0.019
    pts = [(0, 0, 0.036), (0, -0.09, 0.07), (0, -0.17, 0.12), (0, -0.225, 0.2), (0, -0.24, 0.3), (0, -0.24, 0.78)]
    K.path(pts, r, galv, 10)
    K.lathe([(r + 0.002, 0.0), (r + 0.002, 0.02), (0.0, 0.022)], cap, 10, T((0, -0.24, 0.775)))
    return K.done('jmast')


def switch(W, D, H, front, ears=False, uplink_rear='net_rear_switch'):
    def build():
        K = props.Kit()
        body = mat('SwitchBody', (0.13, 0.14, 0.155), 0.5)
        rubber = mat('Rubber', (0.1, 0.1, 0.1), 0.9)
        steel = mat('RackEar', (0.2, 0.21, 0.23), 0.45)
        z0 = 0.004
        K.bx((W, D, H), (0, 0, z0 + H / 2), body)
        feet(K, W, D, rubber)
        if ears:
            for sx in (-1, 1):
                K.bx((0.022, 0.003, H), (sx * (W / 2 + 0.011), -D / 2 + 0.0015, z0 + H / 2), steel)
                K.bx((0.003, 0.05, H), (sx * (W / 2 + 0.0015), -D / 2 + 0.025, z0 + H / 2), steel)
        obj = K.done('switch')
        m = 0.003
        return pictures(obj,
                        (front, [fq(-W / 2 + m, W / 2 - m, z0 + m, z0 + H - m, -D / 2 - E)]),
                        (uplink_rear, [bq(-W / 2 + m, W / 2 - m, z0 + m, z0 + H - m, D / 2 + E)]),
                        ('net_vents_dark', [tq(-W / 2 + 0.02, W / 2 - 0.02, -D / 2 + 0.02, D / 2 - 0.02, z0 + H + E)]),
                        ('net_vents_side', [lq(-D / 2 + 0.02, D / 2 - 0.02, z0 + m, z0 + H - m, -W / 2 - E), rq(-D / 2 + 0.02, D / 2 - 0.02, z0 + m, z0 + H - m, W / 2 + E)]))
    return build


def router():
    K = props.Kit()
    body = mat('RouterBody', (0.07, 0.07, 0.075), 0.5)
    rubber = mat('Rubber', (0.1, 0.1, 0.1), 0.9)
    W, D, H = 0.26, 0.17, 0.036
    z0 = 0.004
    K.bx((W, D, H), (0, 0, z0 + H / 2), body)
    feet(K, W, D, rubber)
    for k in range(4):                                                                         # four aerials hinged at the back, leaning out
        x = (k - 1.5) * W / 4.4
        lean = math.radians((k - 1.5) * 9)
        base = Vector((x, D / 2 - 0.006, z0 + H))
        K.lathe([(0.008, 0.0), (0.008, 0.016)], body, 8, T(base))
        tip = base + Vector((math.sin(lean) * 0.17, 0.02, math.cos(lean) * 0.17))
        K.tube(base + Vector((0, 0, 0.014)), tip, 0.0065, 0.005, body, 8, None, body)
    obj = K.done('router')
    m = 0.004
    return pictures(obj,
                    ('net_router_top', [tq(-W / 2 + 0.01, W / 2 - 0.01, -D / 2 + 0.01, D / 2 - 0.022, z0 + H + E)]),
                    ('net_router_front', [fq(-W / 2 + m, W / 2 - m, z0 + H * 0.5, z0 + H - 0.002, -D / 2 - E)]),
                    ('net_router_back', [bq(-W / 2 + m, W / 2 - m, z0 + m, z0 + H - m, D / 2 + E)]))


def mesh_router():
    K = props.Kit()
    white = mat('MeshWhite', (0.93, 0.93, 0.91), 0.45)
    dark = mat('MeshBase', (0.2, 0.21, 0.23), 0.6)
    r, H = 0.055, 0.19
    K.lathe([(r * 0.92, 0.0), (r * 0.92, 0.012)], dark, 16)
    K.lathe([(0.0, 0.012), (r, 0.012), (r, H - 0.01), (r * 0.93, H), (0.0, H)], white, 16)
    obj = K.done('mesh')
    s = r * 0.62
    return pictures(obj, ('net_fabric', cq(r + E, 0.03, H - 0.03, 16)), ('net_mesh_top', [tq(-s, s, -s, s, H + E)]))


def spool():
    K = props.Kit()
    ply = mat('ReelPlywood', (0.72, 0.58, 0.38), 0.85)
    edge = mat('ReelEdge', (0.55, 0.42, 0.26), 0.9)
    blue = mat('Cat6Blue', (0.1, 0.3, 0.72), 0.55)
    dark = mat('ReelBore', (0.12, 0.1, 0.08), 0.9)
    R, w, fl = 0.2, 0.2, 0.012
    top = fl + w + fl
    K.lathe([(0.04, 0.0), (R, 0.0), (R, fl), (0.04, fl)], edge, 24, None, closed=True)
    K.lathe([(0.04, top - fl), (R, top - fl), (R, top), (0.04, top)], edge, 24, None, closed=True)
    K.lathe([(R * 0.5, fl), (R * 0.5, top - fl)], ply, 14)                                     # the drum
    K.lathe([(R * 0.9, fl), (R * 0.9, top - fl)], blue, 24)                                    # the cable (its windings are painted on)
    K.lathe([(0.04, 0.0), (0.04, top)], dark, 12)                                              # the bore
    K.path([(R * 0.9, 0.0, top - fl - 0.01), (R * 0.93, 0.03, top - fl - 0.012), (R * 0.9, 0.07, top - fl - 0.012)], 0.0035, blue, 6)   # the loose end tucked in
    obj = K.done('spool')
    return pictures(obj,
                    ('net_wind_blue', cq(R * 0.9 + E, fl + 0.001, top - fl - 0.001, 24)),
                    ('net_label_cat6', [tq(-0.14, -0.14 + 0.18, -0.045 - 0.1, 0.045 - 0.1, top + E)]))


def camera():
    """A wall item: its BACK on the plane y = 0, sticking out towards -y, its bottom at z = 0."""
    K = props.Kit()
    white = mat('CameraWhite', (0.93, 0.93, 0.91), 0.45)
    dark = mat('CameraDark', (0.07, 0.07, 0.08), 0.5)
    steel = mat('CameraBracket', (0.75, 0.76, 0.78), 0.4)
    zc = 0.07
    K.lathe([(0.045, 0.0), (0.045, 0.008), (0.03, 0.012), (0.0, 0.012)], white, 14, T((0, 0, zc)) @ RX(math.pi / 2))        # the wall plate
    K.tube((0, -0.01, zc), (0, -0.06, zc - 0.005), 0.011, 0.011, steel, 8)                                                # the arm
    K.lathe([(0.016, -0.012), (0.019, 0.0), (0.016, 0.012)], steel, 10, T((0, -0.062, zc - 0.006)))                       # the ball joint
    tilt = math.radians(12)                                                                                             # the body looks slightly down
    M = T((0, -0.062, zc - 0.006)) @ RX(-tilt)
    r, L = 0.034, 0.15
    body = M @ T((0, -0.02 - L / 2, -0.028)) @ RX(math.pi / 2)
    K.lathe([(r, -L / 2), (r, L / 2)], white, 14, body)
    K.lathe([(0.0, -L / 2), (r, -L / 2)], white, 14, body)
    K.lathe([(r + 0.004, L / 2 - 0.05), (r + 0.004, L / 2 + 0.02)], white, 14, body)                                       # the sun shield round the front
    K.lathe([(r * 0.9, L / 2 - 0.004), (0.0, L / 2 - 0.004)], dark, 14, body)
    obj = K.done('camera')
    fy = -0.02 - L + 0.004 - E
    s = r * 0.62
    return pictures(obj, ('net_camera_face', moved([fq(-s, s, -0.028 - s, -0.028 + s, fy)], M)))


def wall_jack():
    """A through-the-wall item (AttachedObject.ApplyThrough): "Plate", the wall plate with its RJ45 jack (its back on y = 0, its face towards -y; the game copies it onto
    the far side of the wall), and "Pipe", the sleeve the cable goes through (0.25 m towards +y, stretched to the wall). The same on both sides: it uses no bandwidth."""
    P = props.Kit()
    white = mat('JackPlate', (0.93, 0.93, 0.91), 0.45)
    grey = mat('JackSleeve', (0.5, 0.52, 0.55), 0.6)
    W, H, t = 0.07, 0.114, 0.006
    P.bx((W, t, H), (0, -t / 2, H / 2), white)
    P.bx((0.03, 0.01, 0.03), (0, -t - 0.005, H / 2), white)          # the keystone standing proud of the plate
    plate = P.done('Plate')
    plate = pictures(plate, ('net_jack_face', [fq(-W / 2 + 0.001, W / 2 - 0.001, 0.001, H - 0.001, -t - E)]),
                     ('net_port_alu', [fq(-0.0145, 0.0145, H / 2 - 0.0145, H / 2 + 0.0145, -t - 0.01 - E)]))
    plate.name = 'Plate'
    S = props.Kit()
    S.tube((0, 0.0, H / 2), (0, 0.25, H / 2), 0.011, 0.011, grey, 8, grey, grey)
    pipe = S.done('Pipe')
    return [plate, pipe]


def ceiling_ap():
    """A ceiling item: it hangs from its TOP (z = 0 is its lowest point, its height is where it touches the ceiling). A white disc with a ring light underneath."""
    K = props.Kit()
    white = mat('ApWhite', (0.93, 0.93, 0.9), 0.5)
    grey = mat('ApMount', (0.6, 0.62, 0.64), 0.5)
    r, h = 0.1, 0.034
    K.lathe([(0.0, 0.0), (r * 0.86, 0.0), (r, 0.008), (r, h - 0.008), (r * 0.9, h - 0.006)], white, 20)
    K.lathe([(r * 0.9, h - 0.006), (r * 0.9, h), (0.0, h)], grey, 20)                    # the mounting plate against the ceiling
    obj = K.done('ap')
    s = r * 0.6
    return pictures(obj, ('net_ap_ceiling', [[(-s, s, -E), (s, s, -E), (s, -s, -E), (-s, -s, -E)]]))   # facing down


RACK_W, RACK_D, RACK_U, RACK_Z0 = 0.53, 0.42, 0.04445, 0.03      # the wall rack: outside width and depth, one unit, the bottom of unit 1 (the game seats the gear with these)


def wall_rack():
    """An 8U open wall rack (a wall item): two side panels, a top and a bottom, the front rails. The gear slides in from the front (NetRack.cs)."""
    K = props.Kit()
    black = mat('RackBlack', (0.06, 0.06, 0.065), 0.5)
    rail = mat('RackRail', (0.1, 0.1, 0.11), 0.45)
    W, D = RACK_W, RACK_D
    H = RACK_Z0 * 2 + 8 * RACK_U
    t = 0.004
    for sx in (-1, 1):
        K.bx((t, D, H), (sx * (W / 2 - t / 2), -D / 2, H / 2), black)
        K.bx((0.022, 0.004, H - 0.02), (sx * (W / 2 - t - 0.011), -D + 0.002, H / 2), rail)        # the front rails
    K.bx((W, D, t), (0, -D / 2, t / 2), black)
    K.bx((W, D, t), (0, -D / 2, H - t / 2), black)
    K.bx((W, t, H), (0, -t / 2, H / 2), black)                                                    # the back plate on the wall
    obj = K.done('rack')
    z0, z1 = RACK_Z0, RACK_Z0 + 8 * RACK_U
    y = -D - E
    pics = [('net_rack_rail', [fq(sx * (W / 2 - t - 0.011) - 0.011, sx * (W / 2 - t - 0.011) + 0.011, z0, z1, y) for sx in (-1, 1)]),
            ('net_vents_dark', [lq(-D + 0.04, -0.04, 0.04, H - 0.04, -W / 2 - E), rq(-D + 0.04, -0.04, 0.04, H - 0.04, W / 2 + E)]),
            ('net_label_rack', [tq(-0.09, 0.09, -D + 0.03, -D + 0.03 + 0.0675, H + E)])]
    return pictures(obj, *pics)


# id: (builder, note, new manifest values for an old stub)
ITEMS = {
    'net_antenna_omni_cellular': (omni, 'a fibreglass stick antenna clamped to a short mast on a weighted base, its coax run down to the ground', None),
    'net_antenna_yagi_directional': (yagi, 'a nine element yagi on a tripod mast, aimed forward', None),
    'net_ap_outdoor_weatherproof': (access_point, 'a white weatherproof access point banded to a pole, two stub aerials', None),
    'net_arrestor_lightning_ethernet': (arrestor, 'an aluminium in-line surge protector, a jack at each end, a ground stud and its green wire', None),
    'net_cable_ethernet_cat6_15m': (patch_cable(5, 0.085), 'a blue patch cable coiled and tied, an RJ45 plug on each end', None),
    'net_cable_ethernet_cat6_30m': (patch_cable(10, 0.105), 'a longer blue patch cable in a two layer coil, tied, a plug on each end', None),
    'net_dish_satellite': (panel_dish(0.5, 0.3, 0.022, 28, 0.0), 'a flat white satellite antenna on its kickstand',
                           dict(name='Satellite Dish', price=450, kg=4.2, stack=1,
                                text='A flat satellite internet antenna on a kickstand. Stand it in the open with a clear view of the sky: it brings the internet to the homestead.')),
    'net_dish_satellite_high_perf': (panel_dish(0.57, 0.5, 0.03, 35, 0.62), 'a larger flat satellite antenna on a pipe mount', None),
    'net_injector_poe_adapter': (injector, 'a black power-over-ethernet injector, a jack at each end, its power cord', None),
    'net_mount_j_mast_bracket': (j_mast, 'a galvanized J mast on a pivoting foot plate', None),
    'net_networkswitch_poe': (switch(0.16, 0.1, 0.028, 'net_switch_front_5', uplink_rear='net_rear_small'), 'a compact five port PoE switch',
                              dict(name='Compact PoE Switch', price=45, kg=0.5, stack=10,
                                   text='A small desktop network switch with five gigabit ports that also power what is plugged into them (PoE): a camera, an access point.')),
    'net_router': (router, 'a black router with four aerials',
                   dict(name='Internet Router', price=70, kg=0.6, stack=10,
                        text='A home router: it shares the internet connection over four wired ports and Wi-Fi.')),
    'net_router_mesh_wifi6': (mesh_router, 'a white cloth-wrapped mesh router', None),
    'net_spool_cable_cat6_150m': (spool, 'a plywood reel of blue Cat6 cable, lying flat', None),
    'net_switch_poe_8port': (switch(0.28, 0.18, 0.044, 'net_switch_front_8'), 'an eight port PoE switch with two uplink cages', None),
    'net_switch_rackmount_16port': (switch(0.44, 0.22, 0.044, 'net_switch_front_16', ears=True), 'a sixteen port switch with rack ears', None),
    'net_switch_rackmount_32port': (switch(0.44, 0.26, 0.044, 'net_switch_front_32', ears=True), 'a thirty-two port switch with rack ears, its jacks in two rows',
                                    dict(name='32-Port Rackmount Switch', price=240, kg=3.4, stack=5, only_new=True,
                                         text='A managed gigabit switch with thirty-two ports, for a rack. It shares the connection of a router among many wired devices.')),
    'net_switch_poe_16port': (switch(0.44, 0.26, 0.044, 'net_switch_front_16_poe', ears=True), 'a sixteen port PoE switch with rack ears',
                              dict(name='16-Port PoE Switch', price=260, kg=3.8, stack=5, only_new=True,
                                   text='A rackmount switch with sixteen gigabit ports that each give 15 W of power over the cable (PoE): cameras, access points and antennas run from it with no other supply.')),
    'net_router_rackmount': (switch(0.44, 0.22, 0.044, 'net_rack_router_front', ears=True), 'a rack router: an internet port, four LAN ports',
                             dict(name='Rackmount Router', price=180, kg=2.6, stack=5, only_new=True,
                                  text='A wired gateway router for a rack: the dish or a yagi link comes into it and its four ports go on to switches and devices. It has no Wi-Fi of its own.')),
    'net_camera_poe': (camera, 'a white bullet camera on a wall bracket',
                       dict(name='PoE Camera', price=85, kg=0.5, stack=10, only_new=True, wall=True,
                            text='A weatherproof network camera. Mount it on a wall and run a Cat6 cable to a PoE switch: the cable powers it and carries its picture.')),
    'net_jack_wall': (wall_jack, 'an Ethernet wall plate with a sleeve through the wall',
                      dict(name='Ethernet Wall Jack', price=18, kg=0.2, stack=20, only_new=True, wall=True, through=True,
                           text='A wall plate with an RJ45 jack on each side of the wall. Mount it on a wall: a cable from outside (the dish, another building) plugs into the outside, and the gear inside is cabled to the inside. It uses no bandwidth.')),
    'net_ap_indoor_ceiling': (ceiling_ap, 'a white disc access point for a ceiling, a ring light underneath',
                              dict(name='Indoor Access Point', price=95, kg=0.4, stack=10, only_new=True, ceiling=True,
                                   text='A Wi-Fi access point for indoors. Mount it on a ceiling and cable it to a PoE port: the cable powers it. It covers the rooms round it.')),
    'net_ups_rackmount': (switch(0.44, 0.32, 0.086, 'net_ups_front', ears=True), 'a two unit rack UPS: a vented front with a display',
                          dict(name='Rackmount UPS', price=320, kg=24.0, stack=1, only_new=True,
                               text='A battery backup for a wall rack (two units). When the building loses power it keeps the rack, and what the rack feeds over its cables, running: two hours with the rack fully loaded, longer with less in it. It charges again when the power is back.')),
    'net_rack_wall_8u': (wall_rack, 'an eight unit open wall rack',
                         dict(name='Wall Rack', price=140, kg=9.0, stack=1, only_new=True, wall=True,
                              text='An eight unit rack that bolts to a wall. Rackmount routers and switches slide into it (left click with one in hand) and are cabled as one.')),
}


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for item, (build, note, new) in ITEMS.items():
        if args and item not in args:
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        built = build()
        objs = built if isinstance(built, list) else [built]
        obj = objs[0]
        if len(objs) == 1:
            obj.name = item
        folder = os.path.join(NET, item)
        os.makedirs(folder, exist_ok=True)
        pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
        lo = [min(p[i] for p in pts) for i in range(3)]
        dims = [round(max(p[i] for p in pts) - lo[i], 3) for i in range(3)]
        tris = sum(len(p.vertices) - 2 for o in objs for p in o.data.polygons)
        assert lo[2] > -0.003, (item, lo)
        if item == 'net_rack_wall_8u':
            dims[2] = round(RACK_Z0 * 2 + 8 * RACK_U, 3)
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = obj
        for f in os.listdir(folder):                                                      # the old models, whatever they were called
            if f.lower().endswith(('.obj', '.mtl', '.glb', '.fbx')):
                try:
                    os.remove(os.path.join(folder, f))
                except OSError:
                    pass
        bpy.ops.export_scene.gltf(filepath=os.path.join(folder, item + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
        path = os.path.join(folder, item + '.json')
        fresh = not os.path.exists(path)
        m = json.load(open(path if not fresh else os.path.join(NET, 'net_switch_rackmount_16port', 'net_switch_rackmount_16port.json'), encoding='utf-8'))
        if fresh:
            m['id'], m['icon'] = item, item + '.png'
            m['category_fields'] = {'power_draw_w': 0, 'bandwidth_mbps': 0, 'range_m': 0, 'is_connected': False}
            for k in ('wire_role', 'net_ports', 'poe', 'rack_units', 'rack_capacity_u'):
                m['properties'].pop(k, None)
        p = m['properties']
        if new and (fresh or not new.get('only_new')):
            m['name'], m['description'] = new['name'], new['text']
            p.update({'base_value': new['price'], 'weight_kg': new['kg'], 'max_stack_size': new['stack']})
        p['placeable'] = not (new and new.get('wall'))
        if new and new.get('wall'):
            p.update({'attach_surface': 'wall', 'attach_side': 'either'})
        if new and new.get('ceiling'):
            p.update({'attach_surface': 'ceiling', 'placeable': False})
            p.pop('attach_side', None)
        if new and new.get('through'):
            p['attach_through'] = True
        p['footprint'] = '%.2fm W x %.2fm D x %.2fm H' % (dims[0], dims[1], dims[2])
        m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
        m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
        props.save(path, json.dumps(m, indent=2))
        props.save(os.path.join(folder, 'README.md'), '# %s\n\n%s\n\nProcedural model (tools/make_internet.py): %s. Its detail is painted (tools/net_pictures.py). '
                   '%d triangles, %.2f x %.2f x %.2f m.\n' % (m['name'], m['description'], note, tris, *dims))
        print('net', item, '|', tris, 'tris |', dims)


if __name__ == '__main__':
    main()
