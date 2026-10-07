"""
The garage / workshop pack's models (tools/garage_lib.py has the palette, tools/make_garage_assets.py lists and exports them). Each function takes a GaragePalette P.
Metres, centred on x and y, bottom at z = 0, FRONT = -Y. A WALL piece is built with its back at y = +d / 2 and slid back so its back is the plane y = 0.
CLASSIC: riveted painted steel, chunky brass handles, plank bench tops, wood posts. MODERN: slab steel fronts, recessed black handles, steel legs.
"""
import math

from kitchen_lib import Mesh, material


def _handle(M, P, x, y, z, vertical=False, length=0.12):
    """A bar handle (classic: brass, standing off the face) or a recessed slot (modern: a dark strip) on a face at plane y."""
    if P.classic:
        if vertical:
            M.cyl((x, y - 0.025, z - length / 2), (x, y - 0.025, z + length / 2), 0.007, P.handle, seg=6)
            for dz in (-length / 2, length / 2):
                M.cyl((x, y, z + dz), (x, y - 0.025, z + dz), 0.006, P.handle, seg=6)
        else:
            M.cyl((x - length / 2, y - 0.025, z), (x + length / 2, y - 0.025, z), 0.007, P.handle, seg=6)
            for dx in (-length / 2, length / 2):
                M.cyl((x + dx, y, z), (x + dx, y - 0.025, z), 0.006, P.handle, seg=6)
    else:
        if vertical:
            M.box(x - 0.006, x + 0.006, y - 0.012, y, z - length / 2, z + length / 2, P.handle)
        else:
            M.box(x - length / 2, x + length / 2, y - 0.012, y, z - 0.006, z + 0.006, P.handle)


def _front(M, P, x0, x1, y, z0, z1, handle=True, vent=False):
    """A steel drawer or door front on the plane y, face to -y, with a rim (classic: with rivets), a handle and optional vent slots."""
    if P.classic:
        M.box(x0, x1, y - 0.018, y, z0, z1, P.main, r=0.003, seg=1)
        M.box(x0 + 0.02, x1 - 0.02, y - 0.022, y - 0.018, z0 + 0.02, z1 - 0.02, P.main)
        for rx in (x0 + 0.012, x1 - 0.012):
            for rz in (z0 + 0.012, z1 - 0.012):
                M.cyl((rx, y - 0.018, rz), (rx, y - 0.023, rz), 0.004, P.steel, seg=6)
    else:
        M.box(x0, x1, y - 0.016, y, z0, z1, P.main, r=0.002, seg=1)
    if vent:
        for k in range(5):
            M.box(x0 + 0.08, x1 - 0.08, y - 0.019, y - 0.016, z1 - 0.12 - 0.025 * k, z1 - 0.12 - 0.025 * k + 0.012, P.dark)
    if handle:
        _handle(M, P, (x0 + x1) / 2, y - (0.018 if P.classic else 0.016), (z0 + z1) / 2, length=0.14)


def _casters(M, P, w, d, z):
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (w / 2 - 0.06), sy * (d / 2 - 0.06)
            M.cyl((x, y, 0.03), (x, y, z), 0.01, P.steel, seg=6)
            M.cyl((x - 0.012, y, 0.045), (x + 0.012, y, 0.045), 0.045, P.rubber, seg=12)


# ------------------------------------------------------------------ benches and wood

def workbench(P):
    """A workshop bench with a plank top, a lower shelf and a vise, 1.80 x 0.70 x 0.92 m."""
    M = Mesh('garage_workbench')
    w, d, h = 1.80, 0.70, 0.92
    if P.classic:
        for sx in (-1, 1):
            for sy in (-1, 1):
                M.box(sx * (w / 2 - 0.08) - 0.045, sx * (w / 2 - 0.08) + 0.045, sy * (d / 2 - 0.08) - 0.045, sy * (d / 2 - 0.08) + 0.045, 0.0, h - 0.06, P.main, r=0.003, seg=1)
        for z in (0.14, h - 0.14):
            M.box(-w / 2 + 0.06, w / 2 - 0.06, -d / 2 + 0.05, -d / 2 + 0.09, z, z + 0.07, P.main)
            M.box(-w / 2 + 0.06, w / 2 - 0.06, d / 2 - 0.09, d / 2 - 0.05, z, z + 0.07, P.main)
        for k in range(7):
            yy = -d / 2 + 0.05 + k * (d - 0.1) / 6
            M.box(-w / 2 + 0.07, w / 2 - 0.07, yy - 0.04, yy + 0.04, 0.17, 0.20, P.main)
        M.box(-w / 2, w / 2, -d / 2, d / 2, h - 0.06, h, P.top, r=0.004, seg=2)
    else:
        for sx in (-1, 1):
            M.box(sx * (w / 2 - 0.08) - 0.02, sx * (w / 2 - 0.08) + 0.02, -d / 2 + 0.06, d / 2 - 0.06, 0.0, h - 0.05, P.blackmetal)
            M.box(sx * (w / 2 - 0.08) - 0.05, sx * (w / 2 - 0.08) + 0.05, -d / 2 + 0.04, -d / 2 + 0.07, 0.0, 0.02, P.blackmetal)
            M.box(sx * (w / 2 - 0.08) - 0.05, sx * (w / 2 - 0.08) + 0.05, d / 2 - 0.07, d / 2 - 0.04, 0.0, 0.02, P.blackmetal)
        M.box(-w / 2 + 0.08, w / 2 - 0.08, -d / 2 + 0.06, d / 2 - 0.06, 0.20, 0.23, P.main)
        M.box(-w / 2, w / 2, -d / 2, d / 2, h - 0.05, h, P.main, r=0.004, seg=2)
        M.box(-w / 2 + 0.05, w / 2 - 0.05, d / 2 - 0.03, d / 2 - 0.005, h, h + 0.12, P.blackmetal)       # an upstand
    vx = -w / 2 + 0.18                                                                                    # the vise on the front left corner
    M.box(vx - 0.08, vx + 0.08, -d / 2 - 0.02, -d / 2 + 0.12, h, h + 0.09, P.steel, r=0.004, seg=1)
    M.box(vx - 0.07, vx + 0.07, -d / 2 - 0.10, -d / 2 - 0.02, h + 0.01, h + 0.085, P.steel)
    M.cyl((vx, -d / 2 - 0.10, h + 0.045), (vx, -d / 2 - 0.22, h + 0.045), 0.01, P.steel, seg=6)
    M.cyl((vx - 0.06, -d / 2 - 0.22, h + 0.045), (vx + 0.06, -d / 2 - 0.22, h + 0.045), 0.008, P.steel, seg=6)
    return M


def pegboard_wall(P):
    """A pegboard wall panel with hanging tools, 1.20 x 0.06 x 0.90 m. A wall item."""
    M = Mesh('garage_pegboard_wall')
    w, h, d = 1.20, 0.90, 0.06
    yb = d / 2
    board = material('PegboardTan', (0.66, 0.52, 0.34), 0.9)
    M.box(-w / 2, w / 2, yb - 0.012, yb, 0.0, h, board)
    for bar in (-w / 2, w / 2 - 0.035):
        M.box(bar, bar + 0.035, yb - d, yb, 0.0, h, P.main)
    M.box(-w / 2, w / 2, yb - d, yb, 0.0, 0.035, P.main)
    M.box(-w / 2, w / 2, yb - d, yb, h - 0.035, h, P.main)
    fy = yb - 0.012                                                                       # the face of the board: a hammer, a saw, two wrenches
    M.box(-0.48, -0.40, fy - 0.03, fy, 0.30, 0.68, P.top)
    M.box(-0.54, -0.34, fy - 0.034, fy, 0.66, 0.74, P.steel)
    M.box(-0.30, 0.08, fy - 0.012, fy, 0.50, 0.70, P.steel)
    M.box(-0.34, -0.26, fy - 0.03, fy, 0.44, 0.52, P.top)
    for z in (0.66, 0.50):
        M.box(0.18, 0.22, fy - 0.02, fy, z - 0.22, z + 0.12, P.steel)
        M.box(0.15, 0.25, fy - 0.02, fy, z + 0.12, z + 0.2, P.steel)
        M.box(0.32, 0.35, fy - 0.02, fy, z - 0.18, z + 0.12, P.steel)
        M.box(0.30, 0.37, fy - 0.025, fy, z - 0.30, z - 0.18, P.main)
    M.shift(0, -d / 2, 0)
    return M


def sawhorse(P):
    """A sawhorse, 0.90 x 0.45 x 0.80 m."""
    M = Mesh('garage_sawhorse')
    w, d = 0.90, 0.45
    if P.classic:
        M.box(-w / 2, w / 2, -0.04, 0.04, 0.72, 0.80, P.main, r=0.003, seg=1)
        for sx in (-1, 1):
            for sy in (-1, 1):
                M.cyl((sx * (w / 2 - 0.10), sy * 0.02, 0.72), (sx * (w / 2 - 0.04), sy * d / 2 * 0.95, 0.0), 0.022, P.main, seg=6)
        M.box(-w / 2 + 0.10, w / 2 - 0.10, -0.015, 0.015, 0.34, 0.37, P.main)
    else:
        M.box(-w / 2, w / 2, -0.04, 0.04, 0.74, 0.80, P.blackmetal, r=0.003, seg=1)
        for sx in (-1, 1):
            for sy in (-1, 1):
                M.cyl((sx * (w / 2 - 0.08), sy * 0.02, 0.74), (sx * (w / 2 - 0.02), sy * d / 2 * 0.95, 0.0), 0.014, P.blackmetal, seg=8)
        M.box(-w / 2 + 0.02, w / 2 - 0.02, -0.03, 0.03, 0.74, 0.76, P.main)
    return M


def shop_stool(P):
    """A shop stool with a round seat, 0.38 m across, 0.66 m high."""
    M = Mesh('garage_shop_stool')
    leg = P.main if P.classic else P.blackmetal
    for k in range(4):
        a = math.radians(90 * k + 45)
        M.cyl((0.12 * math.cos(a), 0.12 * math.sin(a), 0.62), (0.19 * math.cos(a), 0.19 * math.sin(a), 0.0), 0.016, leg, seg=6)
    M.cyl((0, 0, 0.26), (0, 0, 0.28), 0.17, leg, seg=20)
    M.cyl((0, 0, 0.62), (0, 0, 0.67), 0.19, P.top if P.classic else P.main, seg=24)
    return M


def lumber_rack_wall(P):
    """Three steel arms on a wall rail holding a stack of boards, 1.20 x 0.40 x 0.40 m. A wall item."""
    M = Mesh('garage_lumber_rack_wall')
    w, d = 1.20, 0.40
    yb = d / 2
    M.box(-w / 2, w / 2, yb - 0.04, yb, 0.0, 0.08, P.main)
    for x in (-0.50, 0.0, 0.50):
        M.box(x - 0.02, x + 0.02, -d / 2 + 0.02, yb - 0.04, 0.0, 0.04, P.main)
        M.box(x - 0.02, x + 0.02, -d / 2 + 0.02, -d / 2 + 0.05, 0.0, 0.09, P.main)
        M.box(x - 0.02, x + 0.02, yb - 0.08, yb - 0.04, 0.0, 0.12, P.main)
    for k in range(3):
        M.box(-w / 2 + 0.02 + 0.03 * k, w / 2 - 0.02 - 0.05 * (k % 2), -d / 2 + 0.07, -d / 2 + 0.07 + 0.28, 0.04 + 0.04 * k, 0.04 + 0.04 * (k + 1), P.top)
    M.shift(0, -d / 2, 0)
    return M


# ------------------------------------------------------------------ steel cabinets and chests

def tool_chest_rolling(P):
    """A rolling tool chest with five drawers, 0.72 x 0.46 x 1.00 m."""
    M = Mesh('garage_tool_chest_rolling')
    w, d = 0.72, 0.46
    yf = -d / 2
    _casters(M, P, w, d, 0.10)
    M.box(-w / 2, w / 2, yf, d / 2, 0.10, 0.92, P.main, r=0.004, seg=1)
    M.box(-w / 2 - 0.01, w / 2 + 0.01, yf - 0.01, d / 2 + 0.01, 0.92, 0.96, P.steel, r=0.004, seg=1)
    for z in (0.12, 0.28, 0.44, 0.60, 0.76):
        _front(M, P, -w / 2 + 0.02, w / 2 - 0.02, yf, z, z + 0.14)
    return M


def tool_chest_top(P):
    """A top tool chest with a lid and drawers, 0.62 x 0.32 x 0.38 m."""
    M = Mesh('garage_tool_chest_top')
    w, d = 0.62, 0.32
    yf = -d / 2
    M.box(-w / 2, w / 2, yf, d / 2, 0.0, 0.28, P.main, r=0.004, seg=1)
    M.box(-w / 2 - 0.005, w / 2 + 0.005, yf - 0.005, d / 2 + 0.005, 0.28, 0.34, P.main, r=0.01, seg=2)
    M.box(-0.08, 0.08, yf - 0.012, yf, 0.285, 0.31, P.steel)
    for z in (0.02, 0.10, 0.18):
        _front(M, P, -w / 2 + 0.02, w / 2 - 0.02, yf, z, z + 0.07)
    M.box(-0.10, 0.10, -0.02, 0.02, 0.34, 0.37, P.handle)
    return M


def cabinet_tall(P):
    """A tall two-door steel cabinet with vents, 0.90 x 0.50 x 1.90 m."""
    M = Mesh('garage_cabinet_tall')
    w, d, h = 0.90, 0.50, 1.90
    yf = -d / 2
    base = 0.08
    M.box(-w / 2 + 0.02, w / 2 - 0.02, yf + 0.03, d / 2 - 0.02, 0.0, base, P.dark)
    M.box(-w / 2, w / 2, yf, d / 2, base, h, P.main, r=0.003, seg=1)
    for sx in (-1, 1):
        a, b = (-w / 2 + 0.014, -0.003) if sx < 0 else (0.003, w / 2 - 0.014)
        _front(M, P, a, b, yf, base + 0.014, h - 0.014, handle=False, vent=True)
        _handle(M, P, (b - 0.045) if sx < 0 else (a + 0.045), yf - (0.018 if P.classic else 0.016), 1.0, vertical=True, length=0.22)
    return M


def cabinet_base(P):
    """A base cabinet with three drawers, two doors and a wood top, 1.20 x 0.58 x 0.92 m."""
    M = Mesh('garage_cabinet_base')
    w, d = 1.20, 0.58
    yf = -d / 2
    M.box(-w / 2 + 0.02, w / 2 - 0.02, yf + 0.03, d / 2 - 0.02, 0.0, 0.08, P.dark)
    M.box(-w / 2, w / 2, yf, d / 2, 0.08, 0.86, P.main, r=0.003, seg=1)
    M.box(-w / 2 - 0.015, w / 2 + 0.015, yf - 0.02, d / 2 + 0.01, 0.86, 0.92, P.top, r=0.004, seg=2)
    third = (w - 0.04) / 3
    for k in range(3):
        a = -w / 2 + 0.02 + k * third
        _front(M, P, a + 0.004, a + third - 0.004, yf, 0.70, 0.84)
    for sx in (-1, 1):
        a, b = (-w / 2 + 0.02, -0.004) if sx < 0 else (0.004, w / 2 - 0.02)
        _front(M, P, a, b, yf, 0.10, 0.68, handle=False)
        _handle(M, P, (b - 0.05) if sx < 0 else (a + 0.05), yf - (0.018 if P.classic else 0.016), 0.45, vertical=True, length=0.16)
    return M


def wall_cabinet(P):
    """A two-door steel wall cabinet, 1.00 x 0.35 x 0.70 m. A wall item."""
    M = Mesh('garage_wall_cabinet')
    w, d, h = 1.00, 0.35, 0.70
    yf = -d / 2
    M.box(-w / 2, w / 2, yf, d / 2, 0.0, h, P.main, r=0.003, seg=1)
    for sx in (-1, 1):
        a, b = (-w / 2 + 0.014, -0.003) if sx < 0 else (0.003, w / 2 - 0.014)
        _front(M, P, a, b, yf, 0.014, h - 0.014, handle=False)
        _handle(M, P, (b - 0.045) if sx < 0 else (a + 0.045), yf - (0.018 if P.classic else 0.016), 0.30, vertical=True, length=0.14)
    M.shift(0, -d / 2, 0)
    return M


def steel_shelving(P):
    """A steel shelving unit with boxes and bins, 1.20 x 0.50 x 1.90 m."""
    M = Mesh('garage_steel_shelving')
    w, d, h = 1.20, 0.50, 1.90
    for sx in (-1, 1):
        for sy in (-1, 1):
            M.box(sx * (w / 2 - 0.02) - 0.02, sx * (w / 2 - 0.02) + 0.02, sy * (d / 2 - 0.02) - 0.02, sy * (d / 2 - 0.02) + 0.02, 0.0, h, P.main, r=0.002, seg=1)
    for z in (0.12, 0.60, 1.08, 1.56, h - 0.03):
        M.box(-w / 2, w / 2, -d / 2, d / 2, z, z + 0.03, P.steel)
        M.box(-w / 2, w / 2, -d / 2, -d / 2 + 0.012, z - 0.03, z, P.steel)
    cardboard = material('Cardboard', (0.62, 0.47, 0.28), 0.95)
    bin_ = material('BinBlue', (0.12, 0.30, 0.55), 0.6)
    for z, items in ((0.15, ((-0.40, 0.34, 0.28, cardboard), (0.0, 0.30, 0.22, bin_), (0.38, 0.32, 0.34, cardboard))),
                     (0.63, ((-0.38, 0.40, 0.30, bin_), (0.12, 0.34, 0.20, cardboard), (0.44, 0.22, 0.30, bin_))),
                     (1.11, ((-0.30, 0.50, 0.26, cardboard), (0.30, 0.40, 0.34, cardboard))),
                     (1.59, ((-0.20, 0.30, 0.20, bin_), (0.25, 0.36, 0.24, cardboard)))):
        for x, bw, bh, m in items:
            M.box(x - bw / 2, x + bw / 2, -d / 2 + 0.05, d / 2 - 0.05, z, z + bh, m, r=0.008, seg=1)
    return M


def parts_cabinet(P):
    """A small-parts cabinet with 24 little drawers, 0.60 x 0.30 x 0.90 m."""
    M = Mesh('garage_parts_cabinet')
    w, d, h = 0.60, 0.30, 0.90
    yf = -d / 2
    M.box(-w / 2, w / 2, yf, d / 2, 0.0, h, P.main, r=0.003, seg=1)
    cw = (w - 0.04) / 3
    for c in range(3):
        for r in range(8):
            a = -w / 2 + 0.02 + c * cw
            z = 0.02 + r * 0.108
            M.box(a + 0.004, a + cw - 0.004, yf - 0.012, yf, z, z + 0.098, P.steel, r=0.002, seg=1)
            M.box(a + cw / 2 - 0.035, a + cw / 2 + 0.035, yf - 0.02, yf - 0.012, z + 0.06, z + 0.068, P.handle)
            M.box(a + cw / 2 - 0.025, a + cw / 2 + 0.025, yf - 0.013, yf - 0.011, z + 0.02, z + 0.045, P.paper)
    return M


# ------------------------------------------------------------------ machines

def air_compressor(P):
    """A tank air compressor on wheels, 0.90 x 0.42 x 0.82 m."""
    M = Mesh('garage_air_compressor')
    for sx in (-1, 1):
        M.box(sx * 0.30 - 0.02, sx * 0.30 + 0.02, -0.17, 0.17, 0.12, 0.17, P.steel)
        M.cyl((sx * 0.30, -0.19, 0.075), (sx * 0.30, -0.23, 0.075), 0.075, P.rubber, seg=14)
        M.cyl((sx * 0.30, 0.19, 0.075), (sx * 0.30, 0.23, 0.075), 0.075, P.rubber, seg=14)
    M.cyl((-0.42, 0.0, 0.30), (0.42, 0.0, 0.30), 0.17, P.main, seg=20)
    for sx in (-1, 1):
        M.cyl((sx * 0.42, 0.0, 0.30), (sx * 0.44, 0.0, 0.30), 0.12, P.main, seg=16)
    M.box(-0.22, 0.22, -0.12, 0.12, 0.46, 0.78, P.dark, r=0.01, seg=2)                               # the pump and motor shroud
    M.cyl((-0.12, 0.0, 0.78), (0.12, 0.0, 0.78), 0.045, P.steel, seg=10)
    M.cyl((0.0, 0.0, 0.78), (0.0, 0.0, 0.82), 0.05, P.handle, seg=10)
    M.cyl((0.20, -0.12, 0.50), (0.20, -0.17, 0.50), 0.035, P.steel, seg=12)                           # a gauge
    M.cyl((0.20, -0.17, 0.50), (0.20, -0.172, 0.50), 0.03, P.paper, seg=12)
    M.cyl((-0.30, -0.14, 0.34), (-0.30, -0.22, 0.34), 0.012, P.handle, seg=6)                       # a handle
    return M


def bench_grinder(P):
    """A bench grinder with two wheels, 0.50 x 0.24 x 0.34 m."""
    M = Mesh('garage_bench_grinder')
    M.box(-0.14, 0.14, -0.10, 0.10, 0.0, 0.04, P.main, r=0.004, seg=1)
    M.cyl((-0.17, 0.0, 0.17), (0.17, 0.0, 0.17), 0.065, P.main, seg=16)
    M.box(-0.04, 0.04, -0.06, 0.06, 0.04, 0.12, P.main)
    for sx in (-1, 1):
        M.cyl((sx * 0.17, 0.0, 0.17), (sx * 0.24, 0.0, 0.17), 0.10, P.steel, seg=20)
        M.cyl((sx * 0.20, 0.0, 0.17), (sx * 0.235, 0.0, 0.17), 0.085, P.dark, seg=20)
        M.box(sx * 0.21 - 0.03, sx * 0.21 + 0.03, -0.11, -0.06, 0.12, 0.14, P.steel)
    return M
