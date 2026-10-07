"""
The bathroom pack's models (tools/bathroom_lib.py has the palette, tools/make_bathroom_assets.py lists and exports them). Each function takes a BathPalette P and returns a Mesh.
Metres, centred on x and y, bottom at z = 0, FRONT = -Y (floor pieces stand with their back to +y). WALL pieces are slid back by the build script so their back is the plane y = 0.
CLASSIC: glazed pedestals and rolled rims, cross-handle taps, shaker doors, brass or chrome. MODERN: slab doors, square basins, single-lever taps, floating cabinets.
"""
import math

from bathroom_lib import faucet, vessel
from kitchen_lib import Mesh


def _door(M, x0, x1, y, z0, z1, m, classic, depth=0.02):
    """A cabinet door on the front plane y (its face towards -y): shaker frame with a recessed panel (classic) or a slab (modern)."""
    if classic:
        r = 0.045
        M.box(x0, x1, y - depth, y, z0, z1, m, r=0.002, seg=1)
        M.box(x0 + r, x1 - r, y - depth - 0.004, y - depth + 0.002, z0 + r, z1 - r, m)
        for a, b, c, d in ((x0, x1, z0, z0 + r), (x0, x1, z1 - r, z1), (x0, x0 + r, z0, z1), (x1 - r, x1, z0, z1)):
            M.box(a, b, y - depth - 0.008, y - depth, c, d, m, r=0.002, seg=1)
    else:
        M.box(x0, x1, y - depth, y, z0, z1, m, r=0.003, seg=1)


def _knob(M, P, x, y, z, vertical=False):
    if P.classic:
        M.cyl((x, y, z), (x, y - 0.02, z), 0.012, P.trim, seg=10, r1=0.008)
        M.cyl((x, y - 0.02, z), (x, y - 0.034, z), 0.019, P.trim, seg=12, r1=0.016)
    else:
        if vertical:
            M.box(x - 0.006, x + 0.006, y - 0.03, y, z - 0.07, z + 0.07, P.trim)
        else:
            M.box(x - 0.07, x + 0.07, y - 0.03, y, z - 0.006, z + 0.006, P.trim)


# ------------------------------------------------------------------ porcelain fixtures

def toilet(P):
    """A toilet with a tank and a lid: a two-piece (classic) or a one-piece (modern), 0.40 x 0.72 x 0.81 m."""
    M = Mesh('bathroom_toilet')
    g = P.main
    if P.classic:
        M.rbox(-0.12, 0.12, -0.22, 0.12, 0.0, 0.22, g, 0.08, rv=0.01)
        M.rbox(-0.19, 0.19, -0.36, 0.14, 0.18, 0.40, g, 0.17, rv=0.03)
        M.box(-0.19, 0.19, 0.12, 0.36, 0.38, 0.78, g, r=0.02, seg=2)
        M.box(-0.21, 0.21, 0.10, 0.375, 0.78, 0.81, g, r=0.012, seg=2)
        M.rbox(-0.185, 0.185, -0.35, 0.13, 0.40, 0.43, P.white, 0.16, rv=0.006)
        M.rbox(-0.18, 0.18, -0.345, 0.125, 0.43, 0.45, P.white, 0.155, rv=0.008)
        M.cyl((-0.19, 0.12, 0.72), (-0.23, 0.12, 0.72), 0.008, P.trim, seg=6)
        M.box(-0.26, -0.22, 0.115, 0.125, 0.70, 0.74, P.trim)
        for sx in (-1, 1):
            M.cyl((sx * 0.10, 0.20, 0.45), (sx * 0.10, 0.20, 0.47), 0.012, P.trim, seg=8)
    else:
        M.rbox(-0.14, 0.14, -0.20, 0.30, 0.0, 0.22, g, 0.09, rv=0.01)
        M.rbox(-0.185, 0.185, -0.37, 0.16, 0.20, 0.40, g, 0.18, rv=0.03)
        M.rbox(-0.185, 0.185, 0.10, 0.36, 0.20, 0.74, g, 0.06, rv=0.025)
        M.rbox(-0.19, 0.19, 0.09, 0.365, 0.74, 0.77, g, 0.06, rv=0.01)
        M.rbox(-0.18, 0.18, -0.36, 0.14, 0.40, 0.42, P.white, 0.17, rv=0.006)
        M.rbox(-0.175, 0.175, -0.355, 0.135, 0.42, 0.435, P.white, 0.165, rv=0.006)
        for sx in (-1, 1):
            M.cyl((sx * 0.045, 0.24, 0.77), (sx * 0.045, 0.24, 0.785), 0.026, P.trim, seg=14)
    return M


def pedestal_sink(P):
    """A pedestal sink (classic) or a slim column basin (modern), 0.56 x 0.46 x 0.92 m."""
    M = Mesh('bathroom_pedestal_sink')
    g = P.main
    if P.classic:
        M.lathe([(0.0, 0.0), (0.11, 0.0), (0.12, 0.03), (0.075, 0.10), (0.05, 0.28), (0.06, 0.50), (0.09, 0.68), (0.0, 0.70)], g, at=(0, 0.12, 0.0), seg=16, hard=(1,))
        vessel(M, -0.28, 0.28, -0.23, 0.23, 0.12, 0.03, 0.85, 0.75, 0.66, g)
        M.box(-0.28, 0.28, 0.19, 0.23, 0.85, 0.92, g, r=0.012, seg=2)
        faucet(M, P, 0.0, 0.15, 0.85, reach=0.13, height=0.08, spread=0.11)
    else:
        M.box(-0.07, 0.07, 0.04, 0.20, 0.0, 0.72, g, r=0.008, seg=2)
        M.box(-0.15, 0.15, 0.02, 0.22, 0.0, 0.015, g)
        vessel(M, -0.28, 0.28, -0.23, 0.23, 0.05, 0.03, 0.86, 0.76, 0.70, g)
        faucet(M, P, 0.0, 0.17, 0.86, reach=0.14, height=0.11)
    M.cyl((0.0, -0.02, 0.76), (0.0, -0.02, 0.765), 0.025, P.trim, seg=14)
    return M


def _tub_faucet(M, P, y, z):
    faucet(M, P, 0.0, y, z, reach=0.20, height=0.13, spread=0.13)


def bathtub_alcove(P):
    """A rectangular alcove bathtub with a deck faucet, 1.52 x 0.76 x 0.60 m."""
    M = Mesh('bathroom_bathtub_alcove')
    g = P.main
    vessel(M, -0.76, 0.76, -0.38, 0.38, 0.09 if P.classic else 0.04, 0.06, 0.58, 0.14, 0.0, g)
    M.box(-0.40, 0.40, 0.24, 0.38, 0.54, 0.60, g, r=0.01, seg=2)
    _tub_faucet(M, P, 0.30, 0.60)
    M.cyl((0.55, 0.0, 0.14), (0.55, 0.0, 0.145), 0.032, P.trim, seg=14)
    M.cyl((-0.70, 0.0, 0.46), (-0.715, 0.0, 0.46), 0.03, P.trim, seg=12)
    return M


def bathtub_freestanding(P):
    """A freestanding tub: a clawfoot (classic) or a smooth oval (modern), 1.70 x 0.80 x 0.70 m."""
    M = Mesh('bathroom_bathtub_freestanding')
    g = P.main
    if P.classic:
        vessel(M, -0.85, 0.85, -0.40, 0.40, 0.40, 0.05, 0.64, 0.24, 0.18, g, seg=6)
        for sx in (-1, 1):
            for sy in (-1, 1):
                lx, ly = sx * 0.60, sy * 0.24
                M.lathe([(0.0, 0.0), (0.045, 0.0), (0.05, 0.03), (0.035, 0.08), (0.03, 0.14), (0.05, 0.19), (0.0, 0.20)], P.trim, at=(lx, ly, 0.0), seg=10, hard=(1,))
        M.box(-0.20, 0.20, 0.33, 0.40, 0.60, 0.66, g, r=0.01, seg=2)
        faucet(M, P, 0.0, 0.36, 0.66, reach=0.22, height=0.13, spread=0.13)
    else:
        vessel(M, -0.80, 0.80, -0.39, 0.39, 0.39, 0.045, 0.58, 0.14, 0.02, g, seg=6)
        M.rbox(-0.64, 0.64, -0.28, 0.28, 0.0, 0.02, P.dark, 0.28, seg=4)
        M.box(-0.12, 0.12, 0.33, 0.39, 0.56, 0.60, g, r=0.01, seg=2)
        faucet(M, P, 0.0, 0.36, 0.60, reach=0.22, height=0.15)
    M.cyl((0.45, 0.0, 0.24 if P.classic else 0.14), (0.45, 0.0, 0.245 if P.classic else 0.145), 0.03, P.trim, seg=14)
    return M


def shower_stall(P):
    """A corner shower: a tray, tiled back and side, a glass door, a rain head and a valve, 0.90 x 0.90 x 2.05 m."""
    M = Mesh('bathroom_shower_stall')
    vessel(M, -0.45, 0.45, -0.45, 0.45, 0.03, 0.03, 0.12, 0.09, 0.0, P.main)
    M.box(-0.45, 0.45, 0.42, 0.45, 0.12, 2.0, P.tile)
    M.box(-0.45, -0.42, -0.42, 0.42, 0.12, 2.0, P.tile)
    M.box(0.425, 0.445, -0.42, 0.42, 0.12, 2.0, P.glass)
    M.box(-0.42, 0.445, -0.445, -0.425, 0.12, 2.0, P.glass)
    if P.classic:
        for x0, x1, y0, y1 in ((-0.45, 0.45, -0.45, -0.42), (0.42, 0.45, -0.45, 0.45)):
            M.box(x0, x1, y0, y1, 2.0, 2.05, P.trim)
            M.box(x0, x1, y0, y1, 0.12, 0.15, P.trim)
        for x in (-0.44, 0.0, 0.44):
            M.box(x - 0.012, x + 0.012, -0.45, -0.42, 0.12, 2.05, P.trim)
    else:
        for z in (0.35, 1.0, 1.65):
            M.box(0.20, 0.23, -0.452, -0.42, z - 0.02, z + 0.02, P.trim)
    M.cyl((0.30, -0.465, 0.8), (0.30, -0.465, 1.4), 0.011, P.trim, seg=8)
    M.cyl((0.30, -0.445, 0.8), (0.30, -0.465, 0.8), 0.008, P.trim, seg=6)
    M.cyl((0.30, -0.445, 1.4), (0.30, -0.465, 1.4), 0.008, P.trim, seg=6)
    M.cyl((0.0, 0.42, 1.80), (0.0, 0.22, 1.96), 0.012, P.trim, seg=8)
    M.cyl((0.0, 0.22, 1.96), (0.0, 0.22, 1.945), 0.11 if not P.classic else 0.09, P.trim, seg=20)
    M.cyl((0.0, 0.42, 1.10), (0.0, 0.385, 1.10), 0.028, P.trim, seg=12)
    M.box(-0.012, 0.012, 0.36, 0.385, 1.10, 1.17, P.trim) if P.classic else M.box(-0.07, 0.07, 0.37, 0.385, 1.095, 1.105, P.trim)
    M.cyl((0.0, 0.0, 0.09), (0.0, 0.0, 0.095), 0.045, P.trim, seg=14)
    return M


# ------------------------------------------------------------------ vanities and cabinets

def _vanity(name, P, w, basins, h=0.84):
    M = Mesh(name)
    c = P.classic
    d = 0.52
    yf, yb = -d / 2, d / 2
    x0, x1 = -w / 2, w / 2
    base = 0.08
    # the plinth (classic) or the slim legs (modern)
    if c:
        M.box(x0 + 0.02, x1 - 0.02, yf + 0.03, yb - 0.02, 0.0, base, P.main)
    else:
        for sx in (-1, 1):
            for sy in (-1, 1):
                M.cyl((sx * (w / 2 - 0.07), sy * (d / 2 - 0.07), 0.0), (sx * (w / 2 - 0.07), sy * (d / 2 - 0.07), base), 0.016, P.trim, seg=8)
    M.box(x0, x1, yf, yb, base, 0.60, P.main, r=0.003, seg=1)                      # the carcass under the basins
    bw = 0.20                                                                      # basin half width
    centers = [0.0] if basins == 1 else [-w / 4, w / 4]
    # the aprons round the basins and the stone top with holes
    edges = [x0]
    for cx in centers:
        edges += [cx - bw, cx + bw]
    edges.append(x1)
    for i in range(0, len(edges), 2):
        a, b = edges[i], edges[i + 1]
        M.box(a, b, yf, yb, 0.60, 0.80, P.main, r=0.003, seg=1)
    for cx in centers:
        M.box(cx - bw, cx + bw, 0.15, yb, 0.60, 0.80, P.main)
        M.box(cx - bw, cx + bw, yf, -0.18, 0.60, 0.80, P.main)
    h0, h1 = 0.80, 0.835
    for i in range(0, len(edges), 2):
        M.box(edges[i] - 0.012, edges[i + 1] + 0.012, yf - 0.012, yb + 0.012, h0, h1, P.stone, r=0.004, seg=1)
    for cx in centers:
        M.box(cx - bw + 0.012, cx + bw - 0.012, 0.145, yb + 0.012, h0, h1, P.stone)
        M.box(cx - bw + 0.012, cx + bw - 0.012, yf - 0.012, -0.175, h0, h1, P.stone)
        vessel(M, cx - bw, cx + bw, -0.175, 0.145, 0.06, 0.02, 0.84, 0.69, 0.62, P.basin)
        faucet(M, P, cx, 0.20, h1, reach=0.15, height=0.11, spread=0.10)
        M.cyl((cx, -0.015, 0.69), (cx, -0.015, 0.695), 0.022, P.trim, seg=12)
    # the doors on the front
    n = 2 if basins == 1 else 4
    gap = 0.004
    dw = (w - 0.03) / n
    for i in range(n):
        a = x0 + 0.015 + i * dw + gap
        b = x0 + 0.015 + (i + 1) * dw - gap
        _door(M, a, b, yf - 0.002, 0.10, 0.78, P.main, c)
        side = -1 if i % 2 == 0 else 1
        _knob(M, P, (b - 0.045) if side < 0 else (a + 0.045), yf - 0.024 if c else yf - 0.022, 0.70, vertical=not c)
    return M


def vanity_single(P):
    """A single-basin bathroom vanity with a stone top, a faucet and two doors, 0.80 x 0.52 x 0.97 m."""
    return _vanity('bathroom_vanity_single', P, 0.80, 1)


def vanity_double(P):
    """A double-basin bathroom vanity with a stone top, two faucets and four doors, 1.50 x 0.52 x 0.97 m."""
    return _vanity('bathroom_vanity_double', P, 1.50, 2)


def medicine_cabinet(P):
    """A wall medicine cabinet with a mirror door, 0.50 x 0.14 x 0.70 m. A wall item."""
    M = Mesh('bathroom_medicine_cabinet')
    w, d, h = 0.50, 0.14, 0.70
    M.box(-w / 2, w / 2, -d / 2, d / 2, 0.0, h, P.main, r=0.004, seg=1)
    if P.classic:
        M.box(-w / 2 - 0.015, w / 2 + 0.015, -d / 2 - 0.012, -d / 2, h - 0.0, h + 0.025, P.main, r=0.004, seg=1)
        M.box(-w / 2 + 0.03, w / 2 - 0.03, -d / 2 - 0.006, -d / 2, 0.03, h - 0.03, P.main)
        M.box(-w / 2 + 0.06, w / 2 - 0.06, -d / 2 - 0.0075, -d / 2 - 0.006, 0.06, h - 0.06, P.mirror)
    else:
        M.box(-w / 2 + 0.01, w / 2 - 0.01, -d / 2 - 0.008, -d / 2, 0.01, h - 0.01, P.mirror)
        M.box(w / 2 - 0.03, w / 2 - 0.02, -d / 2 - 0.016, -d / 2 - 0.008, 0.25, 0.45, P.trim)
    M.shift(0, d / 2, 0)
    return M


def vanity_mirror(P):
    """A framed bathroom mirror: an oval in a wood frame (classic) or a slim rectangle (modern), 0.70 x 0.04 x 0.90 m. A wall item."""
    M = Mesh('bathroom_vanity_mirror')
    d = 0.04
    if P.classic:
        M.rbox(-0.35, 0.35, -d, 0.0, 0.0, 0.90, P.main, 0.34, rv=0.006, seg=6)
        M.rbox(-0.30, 0.30, -d - 0.002, -d + 0.01, 0.05, 0.85, P.mirror, 0.29, seg=6)
    else:
        M.box(-0.35, 0.35, -d, 0.0, 0.0, 0.90, P.main, r=0.004, seg=1)
        M.box(-0.33, 0.33, -d - 0.004, -d + 0.01, 0.02, 0.88, P.mirror)
    return M


def linen_cabinet(P):
    """A tall linen cabinet with a glazed upper door and a closed lower door, 0.45 x 0.35 x 1.80 m."""
    M = Mesh('bathroom_linen_cabinet')
    w, d, h = 0.45, 0.35, 1.80
    yf = -d / 2
    c = P.classic
    if c:
        M.box(-w / 2 + 0.01, w / 2 - 0.01, yf + 0.03, d / 2 - 0.02, 0.0, 0.08, P.main)
    else:
        for sx in (-1, 1):
            for sy in (-1, 1):
                M.cyl((sx * 0.18, sy * 0.12, 0.0), (sx * 0.18, sy * 0.12, 0.10), 0.014, P.trim, seg=8)
    z0 = 0.08 if c else 0.10
    M.box(-w / 2, w / 2, yf, d / 2, z0, h - 0.03, P.main, r=0.003, seg=1)
    if c:
        M.box(-w / 2 - 0.015, w / 2 + 0.015, yf - 0.015, d / 2 + 0.01, h - 0.03, h, P.main, r=0.005, seg=2)
    else:
        M.box(-w / 2, w / 2, yf, d / 2, h - 0.03, h, P.main, r=0.003, seg=1)
    zs = 0.95
    _door(M, -w / 2 + 0.012, w / 2 - 0.012, yf - 0.002, z0 + 0.012, zs - 0.004, P.main, c)
    if c:
        _door(M, -w / 2 + 0.012, w / 2 - 0.012, yf - 0.002, zs + 0.004, h - 0.045, P.main, True)
        M.box(-w / 2 + 0.06, w / 2 - 0.06, yf - 0.026, yf - 0.02, zs + 0.05, h - 0.09, P.glass)
    else:
        _door(M, -w / 2 + 0.012, w / 2 - 0.012, yf - 0.002, zs + 0.004, h - 0.045, P.main, False)
        M.box(-w / 2 + 0.05, w / 2 - 0.05, yf - 0.024, yf - 0.020, zs + 0.06, h - 0.10, P.glass)
    _knob(M, P, w / 2 - 0.05, yf - 0.024, zs - 0.15, vertical=not c)
    _knob(M, P, w / 2 - 0.05, yf - 0.024, zs + 0.15, vertical=not c)
    return M


def towel_shelf(P):
    """A wall shelf with a towel bar under it and a hanging towel, 0.80 x 0.22 x 0.46 m. A wall item that holds things on its top."""
    M = Mesh('bathroom_towel_shelf')
    w, d = 0.80, 0.22
    M.box(-w / 2, w / 2, -d, 0.0, 0.42, 0.46, P.main, r=0.004, seg=1)
    for sx in (-1, 1):
        M.box(sx * (w / 2 - 0.08) - 0.012, sx * (w / 2 - 0.08) + 0.012, -0.17, -0.0, 0.18, 0.42, P.main)
        M.box(sx * (w / 2 - 0.08) - 0.012, sx * (w / 2 - 0.08) + 0.012, -0.012, 0.0, 0.18, 0.42, P.main)
    M.cyl((-w / 2 + 0.07, -0.15, 0.30), (w / 2 - 0.07, -0.15, 0.30), 0.011, P.trim, seg=8)
    for sx in (-1, 1):
        M.cyl((sx * (w / 2 - 0.07), -0.15, 0.30), (sx * (w / 2 - 0.07), -0.17, 0.30), 0.018, P.trim, seg=8)
    M.box(-0.17, 0.17, -0.172, -0.13, 0.08, 0.32, P.towel, r=0.008, seg=1)
    M.box(-0.17, 0.17, -0.172, -0.13, 0.30, 0.32, P.towel)
    return M


def hamper(P):
    """A laundry hamper with a fabric bag in a frame and a lid, 0.40 x 0.32 x 0.62 m."""
    M = Mesh('bathroom_hamper')
    w, d, h = 0.40, 0.32, 0.62
    if P.classic:
        M.rbox(-w / 2, w / 2, -d / 2, d / 2, 0.06, h - 0.06, P.wicker, 0.05, rv=0.012)
        for sx in (-1, 1):
            for sy in (-1, 1):
                M.cyl((sx * 0.17, sy * 0.13, 0.0), (sx * 0.17, sy * 0.13, 0.08), 0.02, P.frame, seg=8)
        M.rbox(-w / 2 - 0.01, w / 2 + 0.01, -d / 2 - 0.01, d / 2 + 0.01, h - 0.06, h, P.frame, 0.05, rv=0.01)
        M.cyl((0, -d / 2 - 0.01, h - 0.03), (0, -d / 2 - 0.035, h - 0.03), 0.014, P.trim, seg=8)
        M.rbox(-w / 2 + 0.02, w / 2 - 0.02, -d / 2 + 0.02, d / 2 - 0.02, 0.08, h - 0.08, P.main, 0.04, rv=0.01)
    else:
        for sx in (-1, 1):
            tl = 0.14
            M.cyl((sx * 0.17, 0.0, 0.0), (sx * 0.17, 0.0, 0.14), 0.012, P.trim, seg=6)
        M.rbox(-w / 2, w / 2, -d / 2, d / 2, 0.14, h - 0.05, P.main, 0.09, rv=0.02)
        M.rbox(-w / 2 - 0.005, w / 2 + 0.005, -d / 2 - 0.005, d / 2 + 0.005, h - 0.05, h, P.frame, 0.09, rv=0.01)
    return M


def towel_stack(P):
    """A stack of folded towels with a rolled washcloth, 0.36 x 0.26 x 0.24 m."""
    M = Mesh('bathroom_towel_stack')
    for i, (w, d, dx) in enumerate(((0.36, 0.26, 0.0), (0.34, 0.25, 0.004), (0.33, 0.24, -0.004))):
        M.rbox(-w / 2 + dx, w / 2 + dx, -d / 2, d / 2, 0.0 + i * 0.075, 0.075 + i * 0.075, P.main if i != 1 else P.cushion, 0.02, rv=0.02)
    M.cyl((-0.10, 0.0, 0.265), (0.10, 0.0, 0.265), 0.04, P.main, seg=14)
    return M


def bath_mat(P):
    """A soft bath mat, 0.80 x 0.50 x 0.02 m."""
    M = Mesh('bathroom_bath_mat')
    M.rbox(-0.40, 0.40, -0.25, 0.25, 0.0, 0.02, P.main, 0.04, rv=0.006)
    return M


# ------------------------------------------------------------------ metal accessories

def towel_bar(P):
    """A wall towel bar with a hand towel, 0.62 x 0.08 x 0.34 m. A wall item."""
    M = Mesh('bathroom_towel_bar')
    m = P.main
    for sx in (-1, 1):
        x = sx * 0.28
        M.box(x - 0.018, x + 0.018, -0.008, 0.0, 0.0, 0.07, m, r=0.002, seg=1)
        M.cyl((x, -0.008, 0.035), (x, -0.07, 0.035), 0.009, m, seg=8)
        M.cyl((x, -0.07, 0.035), (x, -0.078, 0.035), 0.016, m, seg=10)
    M.cyl((-0.28, -0.07, 0.035), (0.28, -0.07, 0.035), 0.0095, m, seg=10)
    M.box(-0.13, 0.13, -0.095, -0.065, 0.0, 0.34, P.towel, r=0.006, seg=1)
    M.shift(0, 0.0, 0.0)
    return M


def tp_holder(P):
    """A wall toilet-paper holder with a roll, 0.16 x 0.12 x 0.14 m. A wall item."""
    M = Mesh('bathroom_tp_holder')
    m = P.main
    M.box(-0.02, 0.02, -0.01, 0.0, 0.0, 0.12, m, r=0.002, seg=1)
    if P.classic:
        M.cyl((0.0, -0.01, 0.07), (0.0, -0.11, 0.07), 0.008, m, seg=8)
        M.cyl((-0.07, -0.11, 0.07), (0.075, -0.11, 0.07), 0.007, m, seg=8)
        M.cyl((-0.07, -0.01, 0.07), (-0.07, -0.11, 0.07), 0.007, m, seg=8)
        M.cyl((-0.065, -0.06, 0.07), (0.065, -0.06, 0.07), 0.052, P.towel, seg=16)
    else:
        M.cyl((0.0, -0.01, 0.06), (0.0, -0.09, 0.06), 0.008, m, seg=8)
        M.cyl((-0.01, -0.06, 0.06), (0.10, -0.06, 0.06), 0.05, P.towel, seg=16)
    return M


def hook_rail(P):
    """A wall rail with four robe and towel hooks, 0.50 x 0.07 x 0.12 m. A wall item."""
    M = Mesh('bathroom_hook_rail')
    m = P.main
    M.box(-0.25, 0.25, -0.016, 0.0, 0.0, 0.07, m, r=0.004, seg=1)
    for x in (-0.18, -0.06, 0.06, 0.18):
        if P.classic:
            M.cyl((x, -0.016, 0.035), (x, -0.06, 0.035), 0.007, m, seg=8)
            M.cyl((x, -0.06, 0.035), (x, -0.062, 0.095), 0.007, m, seg=8)
            M.lathe([(0.0, -0.012), (0.013, -0.01), (0.015, 0.0), (0.012, 0.012), (0.0, 0.015)], m, at=(x, -0.062, 0.105), seg=10)
        else:
            M.cyl((x, -0.016, 0.035), (x, -0.065, 0.035), 0.008, m, seg=8)
            M.cyl((x, -0.065, 0.035), (x, -0.07, 0.035), 0.014, m, seg=12)
    return M


def soap_set(P):
    """A soap pump, a dish and a toothbrush cup on a small tray, 0.24 x 0.12 x 0.20 m."""
    M = Mesh('bathroom_soap_set')
    m = P.main
    M.rbox(-0.12, 0.12, -0.06, 0.06, 0.0, 0.012, m, 0.02, rv=0.004)
    M.lathe([(0.0, 0.0), (0.03, 0.0), (0.034, 0.10), (0.03, 0.12), (0.0, 0.12)], P.glass, at=(-0.07, 0.0, 0.012), seg=14, hard=(1,))
    M.cyl((-0.07, 0.0, 0.132), (-0.07, 0.0, 0.17), 0.006, m, seg=6)
    M.cyl((-0.07, 0.0, 0.17), (-0.045, 0.0, 0.18), 0.006, m, seg=6)
    M.lathe([(0.0, 0.0), (0.04, 0.0), (0.045, 0.012), (0.0, 0.01)], m, at=(0.0, 0.0, 0.012), seg=14)
    M.box(-0.03, 0.03, -0.022, 0.022, 0.022, 0.034, P.towel, r=0.008, seg=2)
    M.lathe([(0.0, 0.0), (0.03, 0.0), (0.034, 0.10), (0.029, 0.10), (0.029, 0.01), (0.0, 0.01)], m, at=(0.075, 0.0, 0.012), seg=14, hard=(2,))
    for k, (dx, lean) in enumerate(((-0.01, -0.008), (0.0, 0.0), (0.01, 0.008))):
        M.cyl((0.075 + dx, 0.0, 0.03), (0.075 + dx + lean, 0.0, 0.20), 0.004, P.basin, seg=5)
    return M
