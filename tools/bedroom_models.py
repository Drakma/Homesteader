"""
The bedroom pack's models (tools/living_lib.py has the palettes, tools/make_bedroom_assets.py lists and exports them). Each function takes a living_lib Palette P and returns a Mesh.
Metres, centred on x and y, bottom at z = 0, FRONT = -Y (a bed's head is at +y, a dresser's drawers face -y).
CLASSIC: turned posts and bun feet, tufted upholstery, raised-panel drawers, brass knobs. MODERN: platform frames, slab fronts, slim tapered legs, black metal.
"""
import math

from kitchen_lib import Mesh, material
from living_models import button, soft, tapered_leg, turned_leg


def _mirror():
    return material('MirrorGlass', (0.85, 0.88, 0.90), 0.02, 1.0)


def _knob(M, P, x, y, z):
    """A drawer knob (classic) or a slot handle (modern) on a front plane y."""
    if P.classic:
        M.cyl((x, y, z), (x, y - 0.018, z), 0.009, P.metal, seg=8)
        M.cyl((x, y - 0.018, z), (x, y - 0.03, z), 0.016, P.metal, seg=10, r1=0.014)
    else:
        M.box(x - 0.06, x + 0.06, y - 0.012, y, z - 0.004, z + 0.004, P.metal)


def _drawer(M, P, x0, x1, y, z0, z1, k=True):
    """A drawer front on the plane y (its face towards -y): a raised panel (classic) or a slab (modern), with its handle."""
    if P.classic:
        M.box(x0, x1, y - 0.02, y, z0, z1, P.main, r=0.002, seg=1)
        M.box(x0 + 0.03, x1 - 0.03, y - 0.026, y - 0.02, z0 + 0.03, z1 - 0.03, P.main, r=0.002, seg=1)
    else:
        M.box(x0, x1, y - 0.02, y, z0, z1, P.main, r=0.003, seg=1)
    if k:
        _knob(M, P, (x0 + x1) / 2, y - (0.026 if P.classic else 0.02), (z0 + z1) / 2 if P.classic else z1 - 0.035)


def _chest(M, P, w, d, z0, z1, cols, rows, gap=0.006):
    """A carcass with a grid of drawer fronts."""
    yf = -d / 2
    M.box(-w / 2, w / 2, yf, d / 2, z0, z1, P.main, r=0.003, seg=1)
    pad = 0.02
    dw = (w - 2 * pad - (cols - 1) * gap) / cols
    dh = (z1 - z0 - 2 * pad - (rows - 1) * gap) / rows
    for c in range(cols):
        for r in range(rows):
            xa = -w / 2 + pad + c * (dw + gap)
            za = z0 + pad + r * (dh + gap)
            _drawer(M, P, xa, xa + dw, yf, za, za + dh)


# ------------------------------------------------------------------ beds

def _bedding(M, P, w, d, yb, z, pillows, head_w=None):
    """A mattress with a duvet, a folded sheet, pillows and an accent pillow, on a frame whose deck is at z."""
    yf = -d / 2
    soft(M, -w / 2 + 0.05, w / 2 - 0.05, yf + 0.06, yb - 0.10, z, z + 0.26, P.cream, r=0.04)
    soft(M, -w / 2 + 0.01, w / 2 - 0.01, yf + 0.02, yb - 0.50, z + 0.22, z + 0.34, P.main, r=0.05)                         # the duvet
    for sx in (-1, 1):
        soft(M, sx * (w / 2 - 0.01) - 0.02, sx * (w / 2 - 0.01) + 0.02, yf + 0.04, yb - 0.50, z - 0.04, z + 0.30, P.main, r=0.02)    # hanging over the sides
    soft(M, -w / 2 + 0.02, w / 2 - 0.02, yf - 0.012, yf + 0.03, z, z + 0.32, P.main, r=0.02)                              # and the foot
    soft(M, -w / 2 + 0.01, w / 2 - 0.01, yb - 0.62, yb - 0.46, z + 0.26, z + 0.36, P.cream, r=0.03)                       # the sheet folded back
    pw = (w - 0.12) / pillows
    for i in range(pillows):
        cx = -w / 2 + 0.06 + pw * (i + 0.5)
        soft(M, cx - pw / 2 + 0.01, cx + pw / 2 - 0.01, yb - 0.50, yb - 0.12, z + 0.26, z + 0.44, P.cream, r=0.06)
    if pillows >= 2:
        soft(M, -0.20, 0.20, yb - 0.70, yb - 0.60, z + 0.34, z + 0.54, P.cushion, r=0.05)                                 # an accent cushion


def _bed(name, P, w, d=2.10, pillows=2):
    M = Mesh(name)
    cl = P.classic
    yf, yb = -d / 2, d / 2
    head = 1.35 if cl else 1.10
    if cl:
        for sx in (-1, 1):
            turned_leg(M, sx * (w / 2 - 0.04), yb - 0.04, head, P.frame, r=0.04)
            turned_leg(M, sx * (w / 2 - 0.04), yf + 0.04, 0.66, P.frame, r=0.04)
            M.box(sx * (w / 2 - 0.04) - 0.02, sx * (w / 2 - 0.04) + 0.02, yf + 0.04, yb - 0.04, 0.20, 0.36, P.frame)
        M.box(-w / 2 + 0.04, w / 2 - 0.04, yf + 0.02, yf + 0.06, 0.20, 0.36, P.frame)
        M.box(-w / 2 + 0.04, w / 2 - 0.04, yf, yf + 0.04, 0.34, 0.62, P.frame, r=0.004, seg=1)                               # the footboard
        M.box(-w / 2 + 0.04, w / 2 - 0.04, yf + 0.06, yb - 0.06, 0.30, 0.34, P.frame)
        z = 0.34
        # the tufted headboard between the posts, with a wood cap
        soft(M, -w / 2 + 0.08, w / 2 - 0.08, yb - 0.10, yb - 0.01, 0.40, head - 0.12, P.main, r=0.04)
        M.box(-w / 2 + 0.04, w / 2 - 0.04, yb - 0.08, yb, head - 0.12, head - 0.04, P.frame, r=0.004, seg=1)
        nb = max(3, int((w - 0.3) / 0.22))
        for i in range(nb):
            bx = -w / 2 + 0.15 + (w - 0.3) * (i + 0.5) / nb
            for bz in (0.62, 0.84, 1.06):
                if bz < head - 0.18:
                    button(M, bx, yb - 0.10, bz, P.frame)
    else:
        M.box(-w / 2, w / 2, yf, yb, 0.14, 0.34, P.frame, r=0.01, seg=1)
        for sx in (-1, 1):
            for sy in (-1, 1):
                tapered_leg(M, sx * (w / 2 - 0.08), sy * (d / 2 - 0.08), 0.14, P.metal, r=0.02)
        z = 0.34
        soft(M, -w / 2 - 0.08, w / 2 + 0.08, yb - 0.10, yb, 0.20, head, P.main, r=0.03)                                    # a tall padded panel, wider than the bed
        for i in range(1, 4):
            M.box(-w / 2 - 0.08 + (w + 0.16) * i / 4 - 0.004, -w / 2 - 0.08 + (w + 0.16) * i / 4 + 0.004, yb - 0.103, yb - 0.098, 0.30, head - 0.10, P.dark)
    _bedding(M, P, w, d, yb, z, pillows)
    return M


def bed_queen(P):
    """A queen bed with a headboard, a duvet and pillows, 1.60 x 2.10 x 1.35 m."""
    return _bed('bedroom_bed_queen', P, 1.50)


def bed_king(P):
    """A king bed, 1.95 x 2.10 x 1.35 m."""
    return _bed('bedroom_bed_king', P, 1.85, pillows=3)


def bed_twin(P):
    """A twin bed, 1.05 x 2.00 x 1.2 m."""
    return _bed('bedroom_bed_twin', P, 0.95, d=2.00, pillows=1)


def bed_bunk(P):
    """A bunk bed: two twin beds with a ladder and a guard rail, 1.05 x 2.05 x 1.75 m."""
    M = Mesh('bedroom_bed_bunk')
    w, d = 0.95, 2.00
    yf, yb = -d / 2, d / 2
    cl = P.classic
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = sx * (w / 2 + 0.02), sy * (d / 2 - 0.04)
            if cl:
                turned_leg(M, px, py, 1.75, P.frame, r=0.035)
            else:
                M.box(px - 0.035, px + 0.035, py - 0.035, py + 0.035, 0.0, 1.75, P.frame, r=0.006, seg=1)
    for z in (0.28, 1.00):
        for sx in (-1, 1):
            M.box(sx * (w / 2 + 0.02) - 0.02, sx * (w / 2 + 0.02) + 0.02, yf + 0.04, yb - 0.04, z, z + 0.16, P.frame)
        M.box(-w / 2, w / 2, yf + 0.04, yb - 0.04, z + 0.12, z + 0.16, P.frame)
        soft(M, -w / 2 + 0.02, w / 2 - 0.02, yf + 0.06, yb - 0.06, z + 0.16, z + 0.34, P.cream, r=0.03)
        soft(M, -w / 2 + 0.0, w / 2 - 0.0, yf + 0.06, yb - 0.50, z + 0.30, z + 0.40, P.main, r=0.04)
        soft(M, -w / 2 + 0.06, w / 2 - 0.06, yb - 0.48, yb - 0.12, z + 0.34, z + 0.48, P.cream, r=0.05)
    # the guard rail on the top bunk and the ladder at the foot
    for sx in (-1, 1):
        M.box(sx * (w / 2 + 0.02) - 0.012, sx * (w / 2 + 0.02) + 0.012, yf + 0.04, yb - 0.04, 1.32, 1.44, P.frame)
    for z in (0.35, 0.65, 0.95, 1.25):
        M.cyl((-w / 2 + 0.10, yf + 0.02, z), (w / 2 - 0.10 - 0.2, yf + 0.02, z), 0.016, P.frame, seg=8)
    return M


def end_bench(P):
    """A cushioned bench for the foot of a bed, 1.30 x 0.45 x 0.48 m."""
    M = Mesh('bedroom_end_bench')
    w, d = 1.30, 0.45
    for sx in (-1, 1):
        for sy in (-1, 1):
            lx, ly = sx * (w / 2 - 0.05), sy * (d / 2 - 0.05)
            (turned_leg(M, lx, ly, 0.20, P.frame, r=0.03) if P.classic else tapered_leg(M, lx, ly, 0.20, P.frame, r=0.02))
    M.box(-w / 2 + 0.02, w / 2 - 0.02, -d / 2 + 0.02, d / 2 - 0.02, 0.18, 0.24, P.frame)
    soft(M, -w / 2, w / 2, -d / 2, d / 2, 0.24, 0.48, P.main, r=0.06)
    if P.classic:
        for bx in (-0.40, -0.14, 0.14, 0.40):
            button(M, bx, 0.0, 0.48, P.frame)
    return M


def vanity_stool(P):
    """A padded vanity stool, 0.42 m across, 0.46 m high."""
    M = Mesh('bedroom_vanity_stool')
    for k in range(4):
        a = math.radians(90 * k + 45)
        lx, ly = 0.15 * math.cos(a), 0.15 * math.sin(a)
        (turned_leg(M, lx, ly, 0.24, P.frame, r=0.022) if P.classic else tapered_leg(M, lx, ly, 0.24, P.frame, r=0.016, splay=(lx * 0.2, ly * 0.2)))
    M.cyl((0, 0, 0.22), (0, 0, 0.26), 0.21, P.frame, seg=20)
    M.lathe([(0.0, 0.0), (0.20, 0.0), (0.22, 0.04), (0.21, 0.16), (0.14, 0.20), (0.0, 0.205)], P.main, at=(0, 0, 0.26), seg=22, hard=(1,))
    return M


def desk_chair(P):
    """An upholstered desk chair on wood legs (classic) or a swivel base (modern), 0.52 x 0.55 x 0.90 m."""
    M = Mesh('bedroom_desk_chair')
    if P.classic:
        for sx in (-1, 1):
            turned_leg(M, sx * 0.20, -0.20, 0.44, P.frame, r=0.028)
            turned_leg(M, sx * 0.20, 0.20, 0.90, P.frame, r=0.028)
        M.box(-0.22, 0.22, -0.22, 0.22, 0.40, 0.45, P.frame)
        soft(M, -0.23, 0.23, -0.23, 0.22, 0.45, 0.53, P.main, r=0.04)
        soft(M, -0.21, 0.21, 0.19, 0.24, 0.55, 0.88, P.main, r=0.04)
    else:
        M.cyl((0, 0, 0.0), (0, 0, 0.05), 0.26, P.metal, seg=5)
        M.cyl((0, 0, 0.05), (0, 0, 0.42), 0.02, P.metal, seg=8)
        soft(M, -0.24, 0.24, -0.24, 0.22, 0.42, 0.52, P.main, r=0.05)
        soft(M, -0.22, 0.22, 0.18, 0.25, 0.52, 0.88, P.main, r=0.05)
    return M


# ------------------------------------------------------------------ case goods

def nightstand(P):
    """A bedside table with a drawer and a shelf, 0.50 x 0.40 x 0.60 m."""
    M = Mesh('bedroom_nightstand')
    w, d, h = 0.50, 0.40, 0.60
    yf = -d / 2
    if P.classic:
        for sx in (-1, 1):
            for sy in (-1, 1):
                turned_leg(M, sx * (w / 2 - 0.035), sy * (d / 2 - 0.035), 0.50, P.main, r=0.03)
        M.box(-w / 2, w / 2, yf, d / 2, 0.50, h, P.main, r=0.006, seg=2)
        M.box(-w / 2 + 0.03, w / 2 - 0.03, yf + 0.03, d / 2 - 0.03, 0.14, 0.17, P.main)
        _drawer(M, P, -w / 2 + 0.03, w / 2 - 0.03, yf, 0.34, 0.50)
    else:
        for sx in (-1, 1):
            for sy in (-1, 1):
                tapered_leg(M, sx * (w / 2 - 0.05), sy * (d / 2 - 0.05), 0.20, P.metal, r=0.016)
        M.box(-w / 2, w / 2, yf, d / 2, 0.20, h, P.main, r=0.004, seg=2)
        _drawer(M, P, -w / 2 + 0.015, w / 2 - 0.015, yf, 0.36, h - 0.02)
        M.box(-w / 2 + 0.015, w / 2 - 0.015, yf - 0.004, yf + 0.004, 0.22, 0.34, P.dark)
    return M


def dresser(P):
    """A six-drawer dresser, 1.40 x 0.50 x 0.88 m."""
    M = Mesh('bedroom_dresser')
    w, d = 1.40, 0.50
    if P.classic:
        for sx in (-1, 1):
            for sy in (-1, 1):
                M.lathe([(0.0, 0.0), (0.04, 0.0), (0.05, 0.03), (0.035, 0.08), (0.0, 0.10)], P.main, at=(sx * (w / 2 - 0.06), sy * (d / 2 - 0.06), 0.0), seg=10)
        _chest(M, P, w, d, 0.10, 0.82, 2, 3)
        M.box(-w / 2 - 0.02, w / 2 + 0.02, -d / 2 - 0.02, d / 2 + 0.01, 0.82, 0.86, P.main, r=0.008, seg=2)
    else:
        for sx in (-1, 1):
            for sy in (-1, 1):
                tapered_leg(M, sx * (w / 2 - 0.07), sy * (d / 2 - 0.07), 0.18, P.metal, r=0.018, splay=(sx * 0.02, sy * 0.01))
        _chest(M, P, w, d, 0.18, 0.84, 2, 3)
    return M


def chest_of_drawers(P):
    """A tall chest of five drawers, 0.80 x 0.48 x 1.25 m."""
    M = Mesh('bedroom_chest_of_drawers')
    w, d = 0.80, 0.48
    if P.classic:
        M.box(-w / 2 + 0.02, w / 2 - 0.02, -d / 2 + 0.03, d / 2 - 0.02, 0.0, 0.10, P.main)
        _chest(M, P, w, d, 0.10, 1.19, 1, 5)
        M.box(-w / 2 - 0.02, w / 2 + 0.02, -d / 2 - 0.02, d / 2 + 0.01, 1.19, 1.23, P.main, r=0.008, seg=2)
    else:
        for sx in (-1, 1):
            for sy in (-1, 1):
                tapered_leg(M, sx * (w / 2 - 0.06), sy * (d / 2 - 0.06), 0.16, P.metal, r=0.016)
        _chest(M, P, w, d, 0.16, 1.22, 1, 5)
    return M


def vanity_table(P):
    """A dressing table with two drawers and a mirror, 1.00 x 0.45 x 1.55 m."""
    M = Mesh('bedroom_vanity_table')
    w, d, h = 1.00, 0.45, 0.76
    yf = -d / 2
    mir = _mirror()
    if P.classic:
        for sx in (-1, 1):
            for sy in (-1, 1):
                turned_leg(M, sx * (w / 2 - 0.04), sy * (d / 2 - 0.04), h - 0.04, P.main, r=0.032)
        M.box(-w / 2, w / 2, yf, d / 2, h - 0.04, h, P.main, r=0.006, seg=2)
        M.box(-0.20, 0.20, yf + 0.04, d / 2 - 0.03, 0.40, h - 0.04, P.dark)                                   # the knee hole
        for sx in (-1, 1):
            x0, x1 = (-w / 2 + 0.04, -0.22) if sx < 0 else (0.22, w / 2 - 0.04)
            M.box(x0, x1, yf + 0.02, d / 2 - 0.03, 0.36, h - 0.04, P.main)
            _drawer(M, P, x0, x1, yf, 0.44, h - 0.07)
        M.rbox(-0.36, 0.36, d / 2 - 0.04, d / 2, 0.88, 1.52, P.main, 0.33, rv=0.006, seg=6)                    # the oval mirror
        M.rbox(-0.31, 0.31, d / 2 - 0.047, d / 2 - 0.035, 0.93, 1.47, mir, 0.29, seg=6)
        M.box(-0.03, 0.03, d / 2 - 0.06, d / 2 - 0.02, h, 0.90, P.main)
    else:
        for sx in (-1, 1):
            for sy in (-1, 1):
                tapered_leg(M, sx * (w / 2 - 0.05), sy * (d / 2 - 0.05), h - 0.03, P.metal, r=0.018)
        M.box(-w / 2, w / 2, yf, d / 2, h - 0.03, h, P.main, r=0.004, seg=2)
        M.box(-w / 2 + 0.04, 0.0, yf + 0.03, d / 2 - 0.03, h - 0.16, h - 0.03, P.main)
        _drawer(M, P, -w / 2 + 0.04, -0.01, yf, h - 0.16, h - 0.04)
        M.box(-0.40, 0.40, d / 2 - 0.03, d / 2, 0.84, 1.52, P.main, r=0.004, seg=1)
        M.box(-0.37, 0.37, d / 2 - 0.037, d / 2 - 0.027, 0.87, 1.49, mir)
    return M


def wardrobe(P):
    """A two-door wardrobe, 1.10 x 0.58 x 2.00 m."""
    M = Mesh('bedroom_wardrobe')
    w, d, h = 1.10, 0.58, 2.00
    yf = -d / 2
    mir = _mirror()
    if P.classic:
        M.box(-w / 2 + 0.03, w / 2 - 0.03, yf + 0.04, d / 2 - 0.02, 0.0, 0.12, P.main)
        M.box(-w / 2, w / 2, yf, d / 2, 0.12, h - 0.10, P.main, r=0.004, seg=1)
        M.box(-w / 2 - 0.03, w / 2 + 0.03, yf - 0.03, d / 2 + 0.02, h - 0.10, h, P.main, r=0.01, seg=2)
        z0, z1 = 0.16, h - 0.14
    else:
        for sx in (-1, 1):
            tapered_leg(M, sx * (w / 2 - 0.06), yf + 0.07, 0.12, P.metal, r=0.018)
            tapered_leg(M, sx * (w / 2 - 0.06), d / 2 - 0.07, 0.12, P.metal, r=0.018)
        M.box(-w / 2, w / 2, yf, d / 2, 0.12, h, P.main, r=0.004, seg=1)
        z0, z1 = 0.14, h - 0.04
    for sx in (-1, 1):
        a, b = (-w / 2 + 0.02, -0.003) if sx < 0 else (0.003, w / 2 - 0.02)
        if P.classic:
            M.box(a, b, yf - 0.018, yf, z0, z1, P.main, r=0.002, seg=1)
            M.box(a + 0.07, b - 0.07, yf - 0.026, yf - 0.018, z0 + 0.08, z0 + 0.62, P.main, r=0.002, seg=1)
            M.box(a + 0.07, b - 0.07, yf - 0.026, yf - 0.018, z0 + 0.72, z1 - 0.08, P.main, r=0.002, seg=1)
        else:
            M.box(a, b, yf - 0.02, yf, z0, z1, P.main, r=0.003, seg=1)
        kx = (b - 0.05) if sx < 0 else (a + 0.05)
        if P.classic:
            _knob(M, P, kx, yf - 0.026, 1.05)
        else:
            M.box(kx - 0.006, kx + 0.006, yf - 0.032, yf - 0.02, 0.95, 1.30, P.metal)
    return M


def blanket_chest(P):
    """A blanket chest with a lid, 1.00 x 0.45 x 0.50 m."""
    M = Mesh('bedroom_blanket_chest')
    w, d, h = 1.00, 0.45, 0.50
    if P.classic:
        for sx in (-1, 1):
            for sy in (-1, 1):
                M.lathe([(0.0, 0.0), (0.035, 0.0), (0.045, 0.025), (0.03, 0.07), (0.0, 0.09)], P.main, at=(sx * (w / 2 - 0.05), sy * (d / 2 - 0.05), 0.0), seg=10)
        M.box(-w / 2, w / 2, -d / 2, d / 2, 0.08, h - 0.06, P.main, r=0.004, seg=1)
        M.box(-w / 2 - 0.012, w / 2 + 0.012, -d / 2 - 0.012, d / 2 + 0.012, h - 0.06, h, P.main, r=0.008, seg=2)
        for sx in (-1, 1):
            M.box(sx * 0.35 - 0.025, sx * 0.35 + 0.025, -d / 2 - 0.014, -d / 2 + 0.002, 0.10, h - 0.04, P.metal)
        M.box(-0.04, 0.04, -d / 2 - 0.016, -d / 2 + 0.002, h - 0.15, h - 0.08, P.metal)
    else:
        for sx in (-1, 1):
            for sy in (-1, 1):
                tapered_leg(M, sx * (w / 2 - 0.06), sy * (d / 2 - 0.05), 0.12, P.metal, r=0.016)
        M.box(-w / 2, w / 2, -d / 2, d / 2, 0.12, h, P.main, r=0.005, seg=2)
        M.box(-w / 2 + 0.01, w / 2 - 0.01, -d / 2 - 0.003, -d / 2 + 0.003, h - 0.06, h - 0.05, P.dark)
    return M


def crib(P):
    """A baby crib with a mattress and a drop side, 1.40 x 0.75 x 1.00 m."""
    M = Mesh('bedroom_crib')
    w, d = 1.40, 0.75
    cl = P.classic
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = sx * (w / 2 - 0.03), sy * (d / 2 - 0.03)
            if cl:
                turned_leg(M, px, py, 1.00, P.main, r=0.03)
            else:
                M.box(px - 0.03, px + 0.03, py - 0.03, py + 0.03, 0.0, 1.00, P.main, r=0.004, seg=1)
    M.box(-w / 2 + 0.04, w / 2 - 0.04, -d / 2 + 0.04, d / 2 - 0.04, 0.30, 0.33, P.main)
    soft(M, -w / 2 + 0.06, w / 2 - 0.06, -d / 2 + 0.06, d / 2 - 0.06, 0.33, 0.45, P.cream, r=0.02)
    soft(M, -w / 2 + 0.07, 0.0, -d / 2 + 0.07, d / 2 - 0.07, 0.43, 0.47, P.main, r=0.02)
    for sy in (-1, 1):
        M.box(-w / 2 + 0.03, w / 2 - 0.03, sy * (d / 2 - 0.03) - 0.015, sy * (d / 2 - 0.03) + 0.015, 0.92, 0.98, P.main)
        M.box(-w / 2 + 0.03, w / 2 - 0.03, sy * (d / 2 - 0.03) - 0.015, sy * (d / 2 - 0.03) + 0.015, 0.40, 0.44, P.main)
        n = 17
        for k in range(n):
            x = -w / 2 + 0.09 + (w - 0.18) * k / (n - 1)
            M.box(x - 0.008, x + 0.008, sy * (d / 2 - 0.03) - 0.008, sy * (d / 2 - 0.03) + 0.008, 0.44, 0.92, P.main)
    for sx in (-1, 1):
        M.box(sx * (w / 2 - 0.03) - 0.015, sx * (w / 2 - 0.03) + 0.015, -d / 2 + 0.03, d / 2 - 0.03, 0.40, 0.98, P.main)
    return M


def cheval_mirror(P):
    """A standing full-length mirror in a tilting frame, 0.60 x 0.45 x 1.65 m."""
    M = Mesh('bedroom_cheval_mirror')
    mir = _mirror()
    for sy in (-0.20, 0.20):
        M.box(-0.30, 0.30, sy - 0.025, sy + 0.025, 0.0, 0.05, P.main, r=0.005, seg=1)
    for sx in (-1, 1):
        if P.classic:
            turned_leg(M, sx * 0.28, 0.0, 1.65, P.main, r=0.025)
        else:
            M.box(sx * 0.28 - 0.02, sx * 0.28 + 0.02, -0.02, 0.02, 0.0, 1.65, P.main, r=0.004, seg=1)
        M.box(sx * 0.28 - 0.02, sx * 0.28 + 0.02, -0.20, 0.20, 0.0, 0.05, P.main)
    M.box(-0.28, 0.28, -0.012, 0.012, 0.28, 0.32, P.main)
    M.rbox(-0.25, 0.25, -0.03, 0.03, 0.30, 1.55, P.main, 0.02, seg=2)
    M.rbox(-0.215, 0.215, -0.036, -0.026, 0.345, 1.505, mir, 0.015, seg=2)
    return M


def desk(P):
    """A writing desk with two drawers, 1.20 x 0.60 x 0.76 m."""
    M = Mesh('bedroom_desk')
    w, d, h = 1.20, 0.60, 0.76
    yf = -d / 2
    if P.classic:
        for sx in (-1, 1):
            for sy in (-1, 1):
                turned_leg(M, sx * (w / 2 - 0.04), sy * (d / 2 - 0.04), h - 0.04, P.main, r=0.032)
        M.box(-w / 2, w / 2, yf, d / 2, h - 0.04, h, P.main, r=0.006, seg=2)
        M.box(0.10, w / 2 - 0.04, yf + 0.03, d / 2 - 0.03, 0.30, h - 0.04, P.main)
        _drawer(M, P, 0.10, w / 2 - 0.04, yf, 0.50, h - 0.07)
        _drawer(M, P, 0.10, w / 2 - 0.04, yf, 0.34, 0.48)
        M.box(-w / 2 + 0.03, 0.08, yf + 0.03, yf + 0.06, h - 0.12, h - 0.04, P.main)
    else:
        for sx in (-1, 1):
            tapered_leg(M, sx * (w / 2 - 0.05), yf + 0.06, h - 0.03, P.metal, r=0.018)
            tapered_leg(M, sx * (w / 2 - 0.05), d / 2 - 0.06, h - 0.03, P.metal, r=0.018)
        M.box(-w / 2, w / 2, yf, d / 2, h - 0.03, h, P.main, r=0.004, seg=2)
        M.box(0.20, w / 2 - 0.06, yf + 0.03, d / 2 - 0.03, h - 0.20, h - 0.03, P.main)
        _drawer(M, P, 0.20, w / 2 - 0.06, yf, h - 0.20, h - 0.04)
        M.box(-w / 2 + 0.05, w / 2 - 0.05, d / 2 - 0.06, d / 2 - 0.04, 0.30, 0.32, P.main)
    return M
