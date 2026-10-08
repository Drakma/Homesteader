"""
The dining room pack's models (tools/living_lib.py has the palettes, tools/make_dining_assets.py lists and exports them). Each function takes a living_lib Palette P.
Metres, centred on x and y, bottom at z = 0, FRONT = -Y.
CLASSIC: turned legs, mouldings, tufted upholstery, brass. MODERN: slab tops, slim tapered or metal legs, shell backs, black metal.
"""
import math

from bathroom_models import _door
from bedroom_models import _knob
from kitchen_lib import Mesh, material
from living_models import button, prism_x, soft, tapered_leg, turned_leg


# ------------------------------------------------------------------ tables

def dining_table(P):
    """A dining table that seats six, 1.80 x 0.90 x 0.76 m."""
    M = Mesh('dining_dining_table')
    w, d, h = 1.80, 0.90, 0.76
    if P.classic:
        for sx in (-1, 1):
            for sy in (-1, 1):
                turned_leg(M, sx * (w / 2 - 0.08), sy * (d / 2 - 0.08), h - 0.06, P.main, r=0.05)
        M.box(-w / 2 + 0.08, w / 2 - 0.08, -d / 2 + 0.06, -d / 2 + 0.10, h - 0.16, h - 0.06, P.main)
        M.box(-w / 2 + 0.08, w / 2 - 0.08, d / 2 - 0.10, d / 2 - 0.06, h - 0.16, h - 0.06, P.main)
        for sx in (-1, 1):
            M.box(sx * (w / 2 - 0.10) - 0.02, sx * (w / 2 - 0.10) + 0.02, -d / 2 + 0.08, d / 2 - 0.08, h - 0.16, h - 0.06, P.main)
        M.box(-w / 2, w / 2, -d / 2, d / 2, h - 0.06, h, P.main, r=0.012, seg=3)
    else:
        for sx in (-1, 1):
            tapered_leg(M, sx * (w / 2 - 0.10), -d / 2 + 0.10, h - 0.04, P.metal, r=0.03, splay=(sx * 0.03, 0.0))
            tapered_leg(M, sx * (w / 2 - 0.10), d / 2 - 0.10, h - 0.04, P.metal, r=0.03, splay=(sx * 0.03, 0.0))
        M.box(-w / 2, w / 2, -d / 2, d / 2, h - 0.04, h, P.main, r=0.006, seg=2)
    return M


def round_table(P):
    """A round pedestal dining table that seats four, 1.20 m across, 0.76 m high."""
    M = Mesh('dining_round_table')
    h = 0.76
    if P.classic:
        M.lathe([(0.0, 0.0), (0.22, 0.0), (0.25, 0.04), (0.12, 0.10), (0.09, 0.30), (0.12, 0.45), (0.08, 0.60), (0.18, 0.70), (0.0, 0.72)], P.main, at=(0, 0, 0.0), seg=20, hard=(1,))
        for k in range(3):
            a = math.radians(120 * k + 90)
            M.cyl((0.0, 0.0, 0.07), (0.34 * math.cos(a), 0.34 * math.sin(a), 0.0), 0.04, P.main, seg=8, r1=0.05)
        M.cyl((0, 0, h - 0.05), (0, 0, h), 0.60, P.main, seg=36)
    else:
        M.cyl((0, 0, 0.0), (0, 0, 0.03), 0.34, P.metal, seg=30)
        M.cyl((0, 0, 0.03), (0, 0, h - 0.04), 0.07, P.metal, seg=14)
        M.cyl((0, 0, h - 0.035), (0, 0, h), 0.60, P.main, seg=36)
    return M


def china_cabinet(P):
    """A china cabinet: closed doors below, glass doors above with empty glass shelves, 1.10 x 0.45 x 2.00 m."""
    M = Mesh('dining_china_cabinet')
    w, d, h = 1.10, 0.45, 2.00
    yf = -d / 2
    cl = P.classic
    if cl:
        for sx in (-1, 1):
            for sy in (-1, 1):
                M.box(sx * (w / 2 - 0.07) - 0.05, sx * (w / 2 - 0.07) + 0.05, sy * (d / 2 - 0.07) - 0.05, sy * (d / 2 - 0.07) + 0.05, 0.0, 0.10, P.main, r=0.004, seg=1)
        z0 = 0.10
    else:
        for sx in (-1, 1):
            for sy in (-1, 1):
                tapered_leg(M, sx * (w / 2 - 0.06), sy * (d / 2 - 0.06), 0.14, P.metal, r=0.016)
        z0 = 0.14
    M.box(-w / 2, w / 2, yf, d / 2, z0, 0.90, P.main, r=0.003, seg=1)
    M.box(-w / 2 + 0.01, w / 2 - 0.01, yf + 0.01, d / 2 - 0.01, 0.90, 0.93, P.main)
    for sx in (-1, 1):
        M.box(sx * (w / 2 - 0.015) - 0.015, sx * (w / 2 - 0.015) + 0.015, yf, d / 2, 0.93, h - 0.05, P.main)
    M.box(-w / 2, w / 2, d / 2 - 0.012, d / 2, 0.93, h - 0.05, P.main)
    M.box(-w / 2 - (0.03 if cl else 0.0), w / 2 + (0.03 if cl else 0.0), yf - (0.03 if cl else 0.0), d / 2 + 0.01, h - 0.05, h, P.main, r=0.006, seg=2)
    for z in (1.22, 1.52, 1.82):
        M.box(-w / 2 + 0.03, w / 2 - 0.03, yf + 0.02, d / 2 - 0.012, z, z + 0.012, P.glass)
    for sx in (-1, 1):
        a, b = (-w / 2 + 0.014, -0.002) if sx < 0 else (0.002, w / 2 - 0.014)
        _door(M, a, b, yf, z0 + 0.012, 0.88, P.main, cl)
        _knob(M, P, (b - 0.05) if sx < 0 else (a + 0.05), yf - (0.026 if cl else 0.02), 0.50)
        M.box(a, b, yf - 0.012, yf + 0.004, 0.95, h - 0.07, P.main)
        M.box(a + 0.035, b - 0.035, yf - 0.013, yf + 0.005, 0.99, h - 0.11, P.glass)
    return M


def bar_cart(P):
    """A rolling bar cart with two shelves and a top, all empty, 0.80 x 0.45 x 0.88 m."""
    M = Mesh('dining_bar_cart')
    w, d = 0.80, 0.45
    leg = P.metal
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (w / 2 - 0.03), sy * (d / 2 - 0.03)
            M.cyl((x, y, 0.05), (x, y, 0.82), 0.014, leg, seg=8)
            M.cyl((x - 0.01, y, 0.035), (x + 0.01, y, 0.035), 0.035, P.black, seg=10)
    for z in (0.18, 0.54):
        M.box(-w / 2, w / 2, -d / 2, d / 2, z, z + 0.03, P.main, r=0.004, seg=1)
    M.box(-w / 2, w / 2, -d / 2, d / 2, 0.82, 0.85, P.main, r=0.004, seg=1)
    M.cyl((w / 2 - 0.03, -d / 2 + 0.02, 0.82), (w / 2 + 0.07, -d / 2 + 0.02, 0.82), 0.012, leg, seg=8)
    return M


def wine_rack(P):
    """A wine rack with a grid of empty cubbies, 0.80 x 0.30 x 1.20 m."""
    M = Mesh('dining_wine_rack')
    w, d, h = 0.80, 0.30, 1.20
    t = 0.02
    for sx in (-1, 1):
        M.box(sx * (w / 2 - t / 2) - t / 2, sx * (w / 2 - t / 2) + t / 2, -d / 2, d / 2, 0.0, h, P.main)
    for z in (0.0, h - t):
        M.box(-w / 2, w / 2, -d / 2, d / 2, z, z + t, P.main)
    cols, rows = 4, 4
    cw = (w - 2 * t) / cols
    rh = (h - 2 * t) / rows
    for r in range(1, rows):
        M.box(-w / 2, w / 2, -d / 2, d / 2, t + r * rh - t / 2, t + r * rh + t / 2, P.main)
    for c in range(1, cols):
        M.box(-w / 2 + t + c * cw - t / 2, -w / 2 + t + c * cw + t / 2, -d / 2, d / 2, t, h - t, P.main)
    return M


# ------------------------------------------------------------------ chairs

def dining_chair(P):
    """An upholstered dining chair, 0.48 x 0.54 x 0.98 m."""
    M = Mesh('dining_dining_chair')
    if P.classic:
        for sx in (-1, 1):
            turned_leg(M, sx * 0.20, -0.20, 0.46, P.frame, r=0.028)
            turned_leg(M, sx * 0.20, 0.22, 0.98, P.frame, r=0.028)
        M.box(-0.22, 0.22, -0.22, 0.24, 0.40, 0.46, P.frame)
        soft(M, -0.22, 0.22, -0.23, 0.22, 0.46, 0.54, P.main, r=0.04)
        soft(M, -0.19, 0.19, 0.20, 0.25, 0.58, 0.94, P.main, r=0.04)
        for bz in (0.70, 0.82):
            button(M, 0.0, 0.20, bz, P.frame)
    else:
        for sx in (-1, 1):
            tapered_leg(M, sx * 0.19, -0.19, 0.46, P.metal, r=0.015, splay=(sx * 0.02, -0.02))
            tapered_leg(M, sx * 0.19, 0.19, 0.46, P.metal, r=0.015, splay=(sx * 0.02, 0.02))
        soft(M, -0.23, 0.23, -0.23, 0.22, 0.46, 0.53, P.main, r=0.04)
        prism_x(M, [(0.16, 0.50), (0.26, 0.50), (0.30, 0.96), (0.20, 0.96)], -0.23, 0.23, P.main)
    return M


def host_chair(P):
    """A carver (host) chair with arms, 0.60 x 0.58 x 1.02 m."""
    M = Mesh('dining_host_chair')
    cl = P.classic
    for sx in (-1, 1):
        if cl:
            turned_leg(M, sx * 0.25, -0.22, 0.48, P.frame, r=0.03)
            turned_leg(M, sx * 0.25, 0.24, 1.02, P.frame, r=0.03)
        else:
            tapered_leg(M, sx * 0.24, -0.22, 0.48, P.metal, r=0.017, splay=(sx * 0.02, -0.02))
            tapered_leg(M, sx * 0.24, 0.22, 0.48, P.metal, r=0.017, splay=(sx * 0.02, 0.02))
        M.box(sx * 0.25 - 0.025, sx * 0.25 + 0.025, -0.22, 0.20, 0.62, 0.66, P.frame if cl else P.metal)
        M.cyl((sx * 0.25, -0.18, 0.48), (sx * 0.25, -0.18, 0.63), 0.016, P.frame if cl else P.metal, seg=6)
    M.box(-0.24, 0.24, -0.24, 0.26, 0.42, 0.48, P.frame if cl else P.metal)
    soft(M, -0.25, 0.25, -0.25, 0.24, 0.48, 0.57, P.main, r=0.04)
    soft(M, -0.22, 0.22, 0.21, 0.27, 0.60, 0.98, P.main, r=0.04)
    if cl:
        for bz in (0.72, 0.84):
            button(M, 0.0, 0.21, bz, P.frame)
    return M


def dining_bench(P):
    """An upholstered dining bench, 1.40 x 0.40 x 0.48 m."""
    M = Mesh('dining_dining_bench')
    w, d = 1.40, 0.40
    for sx in (-1, 1):
        for sy in (-1, 1):
            lx, ly = sx * (w / 2 - 0.05), sy * (d / 2 - 0.05)
            (turned_leg(M, lx, ly, 0.22, P.frame, r=0.03) if P.classic else tapered_leg(M, lx, ly, 0.22, P.metal, r=0.018))
    M.box(-w / 2 + 0.02, w / 2 - 0.02, -d / 2 + 0.02, d / 2 - 0.02, 0.20, 0.26, P.frame if P.classic else P.metal)
    soft(M, -w / 2, w / 2, -d / 2, d / 2, 0.26, 0.48, P.main, r=0.05)
    if P.classic:
        for bx in (-0.45, -0.15, 0.15, 0.45):
            button(M, bx, 0.0, 0.48, P.frame)
    return M
