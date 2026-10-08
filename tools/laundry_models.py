"""
The laundry / mudroom pack's models (tools/living_lib.py has the palettes, tools/make_laundry_assets.py lists and exports them). Each function takes a living_lib Palette P.
Metres, centred on x and y, bottom at z = 0, FRONT = -Y. A WALL piece is built with its back at y = +d / 2 and slid back so its back is the plane y = 0.
CLASSIC: turned legs, plank backs, shaker doors, brass hooks. MODERN: slab fronts, slim steel legs, black metal hooks.
"""
import math

from bathroom_lib import faucet, vessel
from bathroom_models import _door
from bedroom_models import _knob
from kitchen_lib import Mesh, material
from living_models import soft, tapered_leg, turned_leg


def _steel():
    return material('LaundrySteel', (0.70, 0.72, 0.74), 0.30, 1.0)


class _Tap:
    """What bathroom_lib.faucet wants of a palette: the trim material and the style."""

    def __init__(self, P):
        self.classic = P.classic
        self.trim = P.chrome


def _hook(M, P, x, y, z):
    """A coat hook on a board whose face is the plane y."""
    M.cyl((x, y, z), (x, y - 0.045, z), 0.008, P.metal, seg=8)
    if P.classic:
        M.cyl((x, y - 0.045, z), (x, y - 0.065, z + 0.045), 0.008, P.metal, seg=8)
        M.lathe([(0.0, -0.012), (0.014, -0.008), (0.016, 0.0), (0.012, 0.012), (0.0, 0.016)], P.metal, at=(x, y - 0.066, z + 0.05), seg=8)
    else:
        M.cyl((x, y - 0.045, z), (x, y - 0.052, z), 0.015, P.metal, seg=10)


# ------------------------------------------------------------------ mudroom

def boot_bench(P):
    """A mudroom bench with a shoe shelf under the seat, 1.20 x 0.40 x 0.50 m."""
    M = Mesh('laundry_boot_bench')
    w, d = 1.20, 0.40
    if P.classic:
        for sx in (-1, 1):
            for sy in (-1, 1):
                turned_leg(M, sx * (w / 2 - 0.04), sy * (d / 2 - 0.04), 0.46, P.main, r=0.032)
        for k in range(6):
            yy = -d / 2 + 0.03 + k * (d - 0.06) / 5
            M.box(-w / 2, w / 2, yy - 0.025, yy + 0.025, 0.46, 0.50, P.main, r=0.004, seg=1)
        for k in range(5):
            yy = -d / 2 + 0.05 + k * (d - 0.1) / 4
            M.box(-w / 2 + 0.05, w / 2 - 0.05, yy - 0.02, yy + 0.02, 0.14, 0.17, P.main)
    else:
        M.box(-w / 2, w / 2, -d / 2, d / 2, 0.40, 0.46, P.main, r=0.005, seg=2)
        for sx in (-1, 1):
            M.box(sx * (w / 2 - 0.06) - 0.012, sx * (w / 2 - 0.06) + 0.012, -d / 2 + 0.03, d / 2 - 0.03, 0.0, 0.40, P.metal)
        M.box(-w / 2 + 0.06, w / 2 - 0.06, -d / 2 + 0.04, d / 2 - 0.04, 0.13, 0.16, P.main)
        M.box(-0.012, 0.012, -d / 2 + 0.04, d / 2 - 0.04, 0.16, 0.40, P.metal)
    return M


def coat_rack_wall(P):
    """A wall board with five coat hooks and a hat shelf, 1.00 x 0.20 x 0.30 m. A wall item."""
    M = Mesh('laundry_coat_rack_wall')
    w, d = 1.00, 0.20
    yb = d / 2
    M.box(-w / 2, w / 2, yb - 0.025, yb, 0.0, 0.22, P.main, r=0.004, seg=1)
    if P.classic:
        M.box(-w / 2 - 0.02, w / 2 + 0.02, -d / 2, yb, 0.22, 0.25, P.main, r=0.004, seg=1)
        for x in (-w / 2 + 0.02, w / 2 - 0.02):
            M.box(x - 0.012, x + 0.012, -d / 2 + 0.02, yb - 0.025, 0.14, 0.22, P.main)
    else:
        M.box(-w / 2, w / 2, -d / 2, yb, 0.22, 0.245, P.main, r=0.003, seg=1)
    for k in range(5):
        _hook(M, P, -0.40 + 0.2 * k, yb - 0.025, 0.10)
    M.shift(0, -d / 2, 0)
    return M


def locker_unit(P):
    """A mudroom locker unit: three open cubbies with a hat shelf, hooks and a bench ledge, 0.90 x 0.42 x 1.85 m."""
    M = Mesh('laundry_locker_unit')
    w, d, h = 0.90, 0.42, 1.85
    yf = -d / 2
    t = 0.022
    base = 0.06 if P.classic else 0.10
    if not P.classic:
        for sx in (-1, 1):
            M.box(sx * (w / 2 - 0.05) - 0.012, sx * (w / 2 - 0.05) + 0.012, yf + 0.05, d / 2 - 0.05, 0.0, base, P.metal)
    for sx in (-1, 1):
        M.box(sx * (w / 2 - t / 2) - t / 2, sx * (w / 2 - t / 2) + t / 2, yf, d / 2, base, h, P.main, r=0.002, seg=1)
    for x in (-w / 6, w / 6):
        M.box(x - t / 2, x + t / 2, yf, d / 2, base, h, P.main)
    M.box(-w / 2, w / 2, d / 2 - 0.012, d / 2, base, h, P.main)
    for z in (base, base + 0.40, 1.55, h - t):
        M.box(-w / 2, w / 2, yf, d / 2, z, z + t, P.main)
    if P.classic:
        M.box(-w / 2 - 0.02, w / 2 + 0.02, yf - 0.02, d / 2 + 0.01, h, h + 0.04, P.main, r=0.005, seg=2)
    cw = w / 3
    for k in range(3):
        cx = -w / 3 + k * cw
        M.cyl((cx - 0.15, d / 2 - 0.02, 1.35), (cx + 0.15, d / 2 - 0.02, 1.35), 0.008, P.metal, seg=6)
        for hx in (cx - 0.10, cx, cx + 0.10):
            _hook(M, P, hx, d / 2 - 0.012, 1.30)
    return M


def shoe_rack(P):
    """A three-tier shoe rack, 0.80 x 0.30 x 0.50 m."""
    M = Mesh('laundry_shoe_rack')
    w, d = 0.80, 0.30
    sh = [0.08, 0.26, 0.44]
    if P.classic:
        for sx in (-1, 1):
            M.box(sx * (w / 2 - 0.012) - 0.012, sx * (w / 2 - 0.012) + 0.012, -d / 2, d / 2, 0.0, 0.50, P.main, r=0.002, seg=1)
        for z in sh:
            for k in range(5):
                yy = -d / 2 + 0.04 + k * (d - 0.08) / 4
                M.box(-w / 2, w / 2, yy - 0.018, yy + 0.018, z, z + 0.02, P.main)
    else:
        for sx in (-1, 1):
            for sy in (-1, 1):
                M.box(sx * (w / 2 - 0.02) - 0.01, sx * (w / 2 - 0.02) + 0.01, sy * (d / 2 - 0.02) - 0.01, sy * (d / 2 - 0.02) + 0.01, 0.0, 0.50, P.metal)
        for z in sh:
            M.box(-w / 2 + 0.01, w / 2 - 0.01, -d / 2 + 0.01, d / 2 - 0.01, z, z + 0.022, P.main, r=0.002, seg=1)
    return M


# ------------------------------------------------------------------ laundry

def laundry_wall_cabinet(P):
    """A two-door wall cabinet for detergent and supplies, 0.80 x 0.35 x 0.70 m. A wall item."""
    M = Mesh('laundry_laundry_wall_cabinet')
    w, d, h = 0.80, 0.35, 0.70
    yf = -d / 2
    M.box(-w / 2, w / 2, yf, d / 2, 0.0, h, P.main, r=0.003, seg=1)
    if P.classic:
        M.box(-w / 2 - 0.015, w / 2 + 0.015, yf - 0.015, d / 2, h, h + 0.03, P.main, r=0.004, seg=1)
    for sx in (-1, 1):
        a, b = (-w / 2 + 0.012, -0.002) if sx < 0 else (0.002, w / 2 - 0.012)
        _door(M, a, b, yf, 0.012, h - 0.012, P.main, P.classic)
        _knob(M, P, (b - 0.05) if sx < 0 else (a + 0.05), yf - (0.026 if P.classic else 0.02), 0.20 if P.classic else 0.30)
    M.shift(0, -d / 2, 0)
    return M


def folding_counter(P):
    """A laundry folding counter with a shelf under it, 1.20 x 0.60 x 0.92 m."""
    M = Mesh('laundry_folding_counter')
    w, d, h = 1.20, 0.60, 0.92
    if P.classic:
        for sx in (-1, 1):
            for sy in (-1, 1):
                turned_leg(M, sx * (w / 2 - 0.04), sy * (d / 2 - 0.04), h - 0.04, P.main, r=0.034)
        M.box(-w / 2, w / 2, -d / 2, d / 2, h - 0.04, h, P.main, r=0.006, seg=2)
        M.box(-w / 2 + 0.05, w / 2 - 0.05, -d / 2 + 0.05, d / 2 - 0.05, 0.16, 0.19, P.main)
    else:
        for sx in (-1, 1):
            M.box(sx * (w / 2 - 0.05) - 0.012, sx * (w / 2 - 0.05) + 0.012, -d / 2 + 0.04, d / 2 - 0.04, 0.0, h - 0.04, P.metal)
            M.box(sx * (w / 2 - 0.05) - 0.012, sx * (w / 2 - 0.05) + 0.012, -d / 2 + 0.04, -d / 2 + 0.07, 0.0, 0.02, P.metal)
        M.box(-w / 2, w / 2, -d / 2, d / 2, h - 0.04, h, P.main, r=0.005, seg=2)
        M.box(-w / 2 + 0.06, w / 2 - 0.06, -d / 2 + 0.06, d / 2 - 0.06, 0.20, 0.225, P.main)
    return M


def laundry_sink(P):
    """A utility sink: a deep steel basin on a cabinet with a tall faucet, 0.70 x 0.55 x 0.95 m."""
    M = Mesh('laundry_laundry_sink')
    w, d = 0.70, 0.55
    yf = -d / 2
    steel = _steel()
    if P.classic:
        M.box(-w / 2 + 0.02, w / 2 - 0.02, yf + 0.03, d / 2 - 0.02, 0.0, 0.08, P.main)
        M.box(-w / 2, w / 2, yf, d / 2, 0.08, 0.60, P.main, r=0.004, seg=1)
    else:
        for sx in (-1, 1):
            for sy in (-1, 1):
                tapered_leg(M, sx * (w / 2 - 0.05), sy * (d / 2 - 0.05), 0.12, P.metal, r=0.016)
        M.box(-w / 2, w / 2, yf, d / 2, 0.12, 0.60, P.main, r=0.004, seg=1)
    for sx in (-1, 1):
        a, b = (-w / 2 + 0.014, -0.003) if sx < 0 else (0.003, w / 2 - 0.014)
        _door(M, a, b, yf, 0.10 if P.classic else 0.14, 0.58, P.main, P.classic)
        _knob(M, P, (b - 0.05) if sx < 0 else (a + 0.05), yf - (0.026 if P.classic else 0.02), 0.34)
    M.box(-w / 2, w / 2, yf, d / 2, 0.60, 0.70, P.main)
    vessel(M, -w / 2 + 0.02, w / 2 - 0.02, yf + 0.03, d / 2 - 0.10, 0.04, 0.025, 0.86, 0.62, 0.60, steel)
    M.box(-w / 2, w / 2, d / 2 - 0.10, d / 2, 0.70, 0.95, P.main)                                  # the backsplash
    faucet(M, _Tap(P), 0.0, d / 2 - 0.05, 0.86, reach=0.22, height=0.24, spread=0.15)
    return M


def drying_rack(P):
    """A folding wooden clothes drying rack, 0.75 x 0.55 x 1.00 m."""
    M = Mesh('laundry_drying_rack')
    w, d = 0.75, 0.55
    for sx in (-1, 1):
        x = sx * (w / 2 - 0.02)
        for sy in (-1, 1):
            M.cyl((x, sy * d / 2 * 0.92, 0.0), (x, sy * 0.05, 1.0), 0.014, P.main, seg=6)
        M.box(x - 0.012, x + 0.012, -0.05, 0.05, 0.96, 1.0, P.main)
        M.box(x - 0.012, x + 0.012, -d / 2 * 0.9, d / 2 * 0.9, 0.28, 0.31, P.main)
    for z, ys in ((1.0, (-0.05, 0.05)), (0.62, (-0.16, 0.16)), (0.30, (-0.25, 0.25))):
        for y in ys:
            M.cyl((-w / 2 + 0.02, y, z), (w / 2 - 0.02, y, z), 0.011, P.main, seg=6)
    M.cyl((-w / 2 + 0.02, 0.0, 0.80), (w / 2 - 0.02, 0.0, 0.80), 0.011, P.main, seg=6)
    return M


def shelf_unit(P):
    """An open storage shelf, empty (things are placed on it in the game), 0.90 x 0.35 x 1.80 m."""
    M = Mesh('laundry_shelf_unit')
    w, d, h = 0.90, 0.35, 1.80
    yf = -d / 2
    t = 0.025
    if P.classic:
        for sx in (-1, 1):
            M.box(sx * (w / 2 - 0.02) - 0.02, sx * (w / 2 - 0.02) + 0.02, yf, d / 2, 0.0, h, P.main, r=0.003, seg=1)
    else:
        for sx in (-1, 1):
            for sy in (-1, 1):
                M.box(sx * (w / 2 - 0.02) - 0.015, sx * (w / 2 - 0.02) + 0.015, sy * (d / 2 - 0.02) - 0.015, sy * (d / 2 - 0.02) + 0.015, 0.0, h, P.metal)
    zs = [0.20, 0.62, 1.04, 1.46, h - t]
    for z in zs:
        M.box(-w / 2 + (0.04 if P.classic else 0.0), w / 2 - (0.04 if P.classic else 0.0), yf, d / 2, z, z + t, P.main)
    return M


# ------------------------------------------------------------------ fabric pieces

def ironing_board(P):
    """An ironing board with a padded cover on folding legs, 1.25 x 0.38 x 0.90 m."""
    M = Mesh('laundry_ironing_board')
    M.prism([(-0.62, -0.07), (-0.45, -0.19), (0.35, -0.19), (0.62, -0.05), (0.62, 0.05), (0.35, 0.19), (-0.45, 0.19), (-0.62, 0.07)], 0.855, 0.895, P.main)
    M.prism([(-0.60, -0.06), (-0.44, -0.17), (0.34, -0.17), (0.60, -0.04), (0.60, 0.04), (0.34, 0.17), (-0.44, 0.17), (-0.60, 0.06)], 0.84, 0.856, P.metal)
    for x in (-0.25, 0.25):
        for sy in (-1, 1):
            M.cyl((x, sy * 0.05, 0.84), (x + (0.14 if x < 0 else -0.14), sy * 0.24, 0.02), 0.012, P.metal, seg=6)
        M.cyl((x + (0.14 if x < 0 else -0.14), -0.24, 0.02), (x + (0.14 if x < 0 else -0.14), 0.24, 0.02), 0.012, P.metal, seg=6)
    return M


def laundry_basket(P):
    """A laundry basket with clothes in it, 0.55 x 0.40 x 0.42 m."""
    M = Mesh('laundry_laundry_basket')
    w, d = 0.55, 0.40
    M.rbox(-w / 2, w / 2, -d / 2, d / 2, 0.0, 0.34, P.main, 0.06, rv=0.015)
    M.rbox(-w / 2 - 0.01, w / 2 + 0.01, -d / 2 - 0.01, d / 2 + 0.01, 0.31, 0.35, P.frame, 0.06, rv=0.01)
    for sx in (-1, 1):
        M.box(sx * (w / 2 - 0.05) - 0.07, sx * (w / 2 - 0.05) + 0.07, -d / 2 - 0.012, -d / 2 - 0.004, 0.20, 0.27, P.dark)
    soft(M, -0.20, 0.10, -0.12, 0.14, 0.33, 0.42, P.cream, r=0.04)
    soft(M, -0.05, 0.22, -0.10, 0.12, 0.33, 0.39, P.cushion, r=0.04)
    return M


def sorter_hamper(P):
    """A three-bag laundry sorter on a frame, 0.90 x 0.35 x 0.80 m."""
    M = Mesh('laundry_sorter_hamper')
    w, d = 0.90, 0.35
    for sx in (-1, 1):
        for sy in (-1, 1):
            lx, ly = sx * (w / 2 - 0.02), sy * (d / 2 - 0.02)
            (turned_leg(M, lx, ly, 0.80, P.frame, r=0.022) if P.classic else M.box(lx - 0.015, lx + 0.015, ly - 0.015, ly + 0.015, 0.0, 0.80, P.metal))
    for z in (0.10, 0.80 - 0.03):
        M.box(-w / 2, w / 2, -d / 2, d / 2, z, z + 0.03, P.frame if P.classic else P.metal)
    cw = (w - 0.08) / 3
    for k in range(3):
        cx = -w / 2 + 0.04 + cw * (k + 0.5)
        M.rbox(cx - cw / 2 + 0.01, cx + cw / 2 - 0.01, -d / 2 + 0.02, d / 2 - 0.02, 0.12, 0.74, P.main, 0.05, rv=0.02)
        soft(M, cx - 0.09, cx + 0.09, -0.07, 0.07, 0.70, 0.80, P.cream, r=0.03)
    return M
