"""
The living / family room pack's models (tools/living_lib.py has the palettes and textures, tools/make_living_assets.py lists and exports them). Each function takes a Palette
(P.classic or modern, P.main = the colour that varies, P.frame / P.metal / P.cushion = the style's fixed parts) and returns a Mesh.

Everything is metres, centred on x and y, bottom at z = 0, FRONT = -Y. A WALL piece (mirror, picture, clock) is built the same way and slid back so its back is the plane y = 0.
CLASSIC pieces have turned legs, rolled arms, buttoned backs, mouldings, brass; MODERN ones clean lines, slim tapered legs, flat planes, black metal.
"""
import math

import bmesh

from kitchen_lib import Mesh, material
from living_lib import Palette  # noqa: F401  (the models are called with one)

# ------------------------------------------------------------------ parts


def turned_leg(K, x, y, h, m, r=0.032):
    """A classic turned leg with a bun foot, from the floor to height h."""
    K.lathe([(0.0, 0.0), (r * 0.8, 0.0), (r, 0.012), (r * 0.65, 0.04), (r * 0.5, h * 0.35), (r * 0.8, h * 0.55), (r * 0.55, h * 0.75), (r * 0.9, h - 0.03), (r * 0.9, h), (0.0, h)],
            m, at=(x, y, 0.0), seg=12, hard=(1, 8))


def tapered_leg(K, x, y, h, m, r=0.022, splay=(0.0, 0.0), seg=8):
    """A slim tapered round leg, optionally splayed (dx, dy at the foot)."""
    K.cyl((x + splay[0], y + splay[1], 0.0), (x, y, h), r * 0.65, m, seg=seg, r1=r)


def soft(K, x0, x1, y0, y1, z0, z1, m, r=0.035):
    """An upholstered cushion: a box with rounded corners and well-rounded top edges."""
    K.rbox(x0, x1, y0, y1, z0, z1, m, r, rv=min(0.04, (z1 - z0) * 0.45), seg=3)


def button(K, x, y, z, m, r=0.012):
    K.cyl((x, y, z), (x, y - 0.012, z), r, m, seg=8, r1=r * 0.6)


def prism_x(K, pts_yz, x0, x1, m, uv=1.0):
    """A polygon given in side view (y, z), counter-clockwise seen from +x, extruded across x from x0 to x1."""
    bm = K.bm
    before = set(bm.faces)
    a = [bm.verts.new((x0, y, z)) for y, z in pts_yz]
    b = [bm.verts.new((x1, y, z)) for y, z in pts_yz]
    n = len(pts_yz)
    bm.faces.new(a[::-1])
    bm.faces.new(b)
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((a[k], a[j], b[j], b[k]))
    K._finish_faces(K._new_faces(before), m, False, uv)


# ------------------------------------------------------------------ upholstered seating

def _sofa(name, P, w, d=0.92, seats=3, h=0.88, chaise=0.0, recline=False):
    K = Mesh(name)
    x0, x1 = -w / 2, w / 2
    yf, yb = -d / 2, d / 2
    cl = P.classic
    armw = 0.17 if cl else 0.13
    legh = 0.17 if cl else 0.16
    zs = 0.30                                              # the top of the base
    # legs
    for lx in (x0 + 0.08, x1 - 0.08):
        for ly in (yf + 0.09, yb - 0.09):
            (turned_leg(K, lx, ly, legh, P.frame) if cl else tapered_leg(K, lx, ly, legh, P.frame, splay=(0.02 if lx > 0 else -0.02, 0.0)))
    # the base / frame
    if cl:
        K.box(x0 + 0.02, x1 - 0.02, yf + 0.04, yb - 0.02, legh - 0.02, zs, P.frame, r=0.006, seg=1)
    soft(K, x0, x1, yf + 0.02, yb, legh, zs + 0.02, P.main, r=0.03)
    # the back and the seat
    inner0, inner1 = x0 + armw, x1 - armw
    soft(K, x0 + 0.02, x1 - 0.02, yb - 0.17, yb, zs, h, P.main, r=0.05)
    sw = (inner1 - inner0) / seats
    for i in range(seats):
        a, b = inner0 + i * sw + 0.004, inner0 + (i + 1) * sw - 0.004
        soft(K, a, b, yf + 0.04, yb - 0.16, zs + 0.02, zs + 0.15, P.main, r=0.04)                                   # the seat cushion
        soft(K, a + 0.005, b - 0.005, yb - 0.30, yb - 0.16, zs + 0.15, h - 0.04, P.main, r=0.04)                    # the back cushion
        if cl:
            for bz in (zs + 0.30, zs + 0.40):
                button(K, (a + b) / 2, yb - 0.30, bz, P.frame)
    # arms
    for sx in (-1, 1):
        ax0, ax1 = (x0, x0 + armw) if sx < 0 else (x1 - armw, x1)
        if cl:
            soft(K, ax0, ax1, yf + 0.02, yb - 0.17, zs, zs + 0.28, P.main, r=0.02)
            K.cyl((sx * (w / 2 - armw / 2), yf + 0.03, zs + 0.27), (sx * (w / 2 - armw / 2), yb - 0.17, zs + 0.27), armw * 0.62, P.main, seg=14)    # the rolled top
            K.cyl((sx * (w / 2 - armw / 2), yf + 0.03, zs + 0.27), (sx * (w / 2 - armw / 2), yf + 0.015, zs + 0.27), armw * 0.55, P.frame, seg=14)   # a scroll face
        else:
            soft(K, ax0, ax1, yf + 0.02, yb - 0.17, zs, zs + 0.34, P.main, r=0.025)
    if chaise > 0.0:
        soft(K, x0 + armw + 0.004, x0 + armw + sw * 1.0 - 0.004, yf - chaise, yf + 0.04, legh, zs + 0.15, P.main, r=0.04)
        for ly in (yf - chaise + 0.09,):
            lx = x0 + 0.08
            (turned_leg(K, lx + 0.1, ly, legh, P.frame) if cl else tapered_leg(K, lx + 0.1, ly, legh, P.frame))
    if recline:
        soft(K, inner0 + 0.05, inner1 - 0.05, yf - 0.42, yf + 0.02, zs - 0.02, zs + 0.10, P.main, r=0.04)
        K.box(inner0 + 0.1, inner0 + 0.13, yf - 0.40, yf + 0.0, zs - 0.10, zs - 0.02, P.metal)
    # throw pillows
    if seats >= 2:
        pc = P.cushion
        for sx in (-1, 1):
            px = sx * (w / 2 - armw - 0.17)
            soft(K, px - 0.17, px + 0.17, yb - 0.30, yb - 0.20, zs + 0.17, zs + 0.52, pc, r=0.05)
    return K


def sofa(P):
    """A three-seat sofa, 2.10 x 0.92 x 0.88 m."""
    return _sofa('living_sofa', P, 2.10, seats=3)


def loveseat(P):
    """A two-seat loveseat, 1.55 x 0.90 x 0.88 m."""
    return _sofa('living_loveseat', P, 1.55, d=0.90, seats=2)


def armchair(P):
    """An upholstered armchair, 0.95 x 0.90 x 0.88 m."""
    return _sofa('living_armchair', P, 0.95, d=0.90, seats=1)


def recliner(P):
    """A recliner with its footrest out, 0.95 x 1.35 x 1.00 m."""
    K = _sofa('living_recliner', P, 0.95, d=0.92, seats=1, h=1.0, recline=True)
    return K


def sectional(P):
    """An L-shaped sectional: a three-seat sofa with a chaise, 2.60 x 1.85 x 0.88 m."""
    return _sofa('living_sectional', P, 2.60, d=0.92, seats=3, chaise=0.92)


def ottoman(P):
    """A cushioned ottoman on short legs, 0.70 x 0.70 x 0.42 m."""
    K = Mesh('living_ottoman')
    for lx in (-0.28, 0.28):
        for ly in (-0.28, 0.28):
            (turned_leg(K, lx, ly, 0.12, P.frame, r=0.026) if P.classic else tapered_leg(K, lx, ly, 0.12, P.frame, r=0.02, splay=(0.015 * (1 if lx > 0 else -1), 0.015 * (1 if ly > 0 else -1))))
    soft(K, -0.35, 0.35, -0.35, 0.35, 0.12, 0.42, P.main, r=0.07)
    if P.classic:
        for bx in (-0.15, 0.15):
            for by in (-0.15, 0.15):
                button(K, bx, by, 0.42, P.frame)
        K.box(-0.34, 0.34, -0.345, 0.345, 0.115, 0.14, P.frame)
    return K


def pouf(P):
    """A round floor pouf, 0.60 m across, 0.40 m high."""
    K = Mesh('living_pouf')
    K.lathe([(0.0, 0.0), (0.24, 0.0), (0.29, 0.06), (0.31, 0.2), (0.28, 0.34), (0.2, 0.40), (0.0, 0.41)], P.main, at=(0, 0, 0), seg=24, hard=(1,))
    K.cyl((0, 0, 0.41), (0, 0, 0.42), 0.012, P.frame if P.classic else P.metal, seg=8)
    K.cyl((0, 0, 0.12), (0, 0, 0.125), 0.30, P.metal if P.classic else P.cream, seg=24, r1=0.30)
    return K


def accent_chair(P):
    """An accent chair: a wing chair (classic) or a shell chair on splayed legs (modern), 0.72 x 0.76 x 0.98 m."""
    K = Mesh('living_accent_chair')
    cl = P.classic
    if cl:
        for lx in (-0.28, 0.28):
            turned_leg(K, lx, -0.30, 0.18, P.frame)
            turned_leg(K, lx, 0.30, 0.18, P.frame)
        soft(K, -0.34, 0.34, -0.36, 0.36, 0.18, 0.30, P.main, r=0.03)
        soft(K, -0.30, 0.30, -0.34, 0.20, 0.30, 0.44, P.main, r=0.04)                       # the seat cushion
        soft(K, -0.36, 0.36, 0.24, 0.38, 0.30, 0.98, P.main, r=0.05)                         # the tall back
        for sx in (-1, 1):
            soft(K, sx * 0.31 - 0.06 if sx < 0 else 0.25, sx * 0.31 + 0.06 if sx > 0 else -0.25, -0.36, 0.30, 0.30, 0.62, P.main, r=0.03)   # the arms
            soft(K, sx * 0.34 - 0.04 if sx < 0 else 0.30, sx * 0.34 + 0.04 if sx > 0 else -0.30, 0.10, 0.34, 0.62, 0.92, P.main, r=0.03)       # the wings
        for bz in (0.62, 0.75, 0.88):
            button(K, 0.0, 0.24, bz, P.frame)
    else:
        for sx in (-1, 1):
            tapered_leg(K, sx * 0.26, -0.26, 0.40, P.frame, r=0.02, splay=(sx * 0.05, -0.04))
            tapered_leg(K, sx * 0.26, 0.26, 0.40, P.frame, r=0.02, splay=(sx * 0.05, 0.04))
        soft(K, -0.34, 0.34, -0.34, 0.30, 0.40, 0.50, P.main, r=0.05)                       # the seat
        prism_x(K, [(0.18, 0.46), (0.34, 0.46), (0.44, 0.98), (0.30, 0.98)], -0.34, 0.34, P.main)   # the shell back, leaning back
        for sx in (-1, 1):
            K.cyl((sx * 0.34, 0.28, 0.46), (sx * 0.34, -0.30, 0.46), 0.012, P.metal, seg=8)
    return K


def rocker(P):
    """A rocking chair with spindles (classic) or a slatted glider (modern), 0.62 x 0.95 x 1.02 m."""
    K = Mesh('living_rocker')
    cl = P.classic
    w = 0.60
    # the runners: curved skids
    for sx in (-1, 1):
        pts = []
        for k in range(9):
            a = -0.9 + 1.8 * k / 8
            pts.append((0.46 * math.sin(a), 0.03 + 0.46 * (1 - math.cos(a)) * 0.35))
        for k in range(8):
            (ya, za), (yb, zb) = pts[k], pts[k + 1]
            K.cyl((sx * w / 2, ya, za), (sx * w / 2, yb, zb), 0.018, P.main, seg=8)
        for ly in (-0.26, 0.26):
            K.cyl((sx * w / 2, ly, 0.06), (sx * (w / 2 - 0.03), ly, 0.44), 0.02, P.main, seg=8)
    K.box(-w / 2 + 0.03, w / 2 - 0.03, -0.30, 0.20, 0.44, 0.48, P.main, r=0.008, seg=1)       # the seat
    if cl:
        K.box(-w / 2 + 0.03, w / 2 - 0.03, -0.22, 0.20, 0.48, 0.52, P.cushion, r=0.02, seg=2)
        for sx in (-1, 1):
            K.cyl((sx * w / 2, -0.26, 0.44), (sx * w / 2, -0.26, 0.70), 0.016, P.main, seg=8)
            K.box(sx * w / 2 - 0.025, sx * w / 2 + 0.025, -0.30, 0.18, 0.70, 0.73, P.main)
        for k in range(7):
            sxk = -0.22 + k * 0.073
            K.cyl((sxk, 0.24, 0.50), (sxk, 0.30, 1.0), 0.012, P.main, seg=6)
        K.box(-w / 2 + 0.02, w / 2 - 0.02, 0.28, 0.32, 0.98, 1.04, P.main, r=0.01, seg=1)
    else:
        for k in range(4):
            K.box(-w / 2 + 0.03, w / 2 - 0.03, 0.22 + k * 0.01, 0.26 + k * 0.01, 0.52 + k * 0.12, 0.60 + k * 0.12, P.main, r=0.006, seg=1)
        K.box(-w / 2 + 0.03, w / 2 - 0.03, -0.20, 0.18, 0.48, 0.53, P.cushion, r=0.02, seg=2)
    return K


# ------------------------------------------------------------------ tables

def _legs_for_table(K, P, w, d, h, inset=0.06, thick=0.05):
    for sx in (-1, 1):
        for sy in (-1, 1):
            lx, ly = sx * (w / 2 - inset), sy * (d / 2 - inset)
            if P.classic:
                turned_leg(K, lx, ly, h, P.main, r=thick * 0.65)
            else:
                tapered_leg(K, lx, ly, h, P.metal if P.key in ('white', 'black') else P.metal, r=0.018, splay=(sx * 0.02, sy * 0.02))


def coffee_table(P):
    """A coffee table with a lower shelf, 1.20 x 0.60 x 0.45 m."""
    K = Mesh('living_coffee_table')
    w, d, h = 1.20, 0.60, 0.45
    if P.classic:
        _legs_for_table(K, P, w, d, h - 0.04, inset=0.07, thick=0.06)
        K.box(-w / 2, w / 2, -d / 2, d / 2, h - 0.04, h, P.main, r=0.01, seg=2)
        K.box(-w / 2 + 0.07, w / 2 - 0.07, -d / 2 + 0.07, d / 2 - 0.07, 0.12, 0.15, P.main, r=0.005, seg=1)
        K.box(-w / 2 + 0.05, w / 2 - 0.05, -d / 2 + 0.03, -d / 2 + 0.07, h - 0.10, h - 0.04, P.main)
        K.box(-w / 2 + 0.05, w / 2 - 0.05, d / 2 - 0.07, d / 2 - 0.03, h - 0.10, h - 0.04, P.main)
    else:
        K.box(-w / 2, w / 2, -d / 2, d / 2, h - 0.035, h, P.main, r=0.006, seg=2)
        for sx in (-1, 1):
            K.box(sx * (w / 2 - 0.05) - 0.01, sx * (w / 2 - 0.05) + 0.01, -d / 2 + 0.05, d / 2 - 0.05, 0.0, h - 0.035, P.metal)
            K.box(sx * (w / 2 - 0.05) - 0.07, sx * (w / 2 - 0.05) + 0.07, -d / 2 + 0.05, -d / 2 + 0.07, 0.0, 0.02, P.metal)
            K.box(sx * (w / 2 - 0.05) - 0.07, sx * (w / 2 - 0.05) + 0.07, d / 2 - 0.07, d / 2 - 0.05, 0.0, 0.02, P.metal)
        K.box(-w / 2 + 0.08, w / 2 - 0.08, -d / 2 + 0.06, d / 2 - 0.06, 0.16, 0.185, P.main, r=0.004, seg=1)
    return K


def end_table(P):
    """A side table with a drawer (classic) or a round drum table (modern), 0.55 x 0.55 x 0.60 m."""
    K = Mesh('living_end_table')
    h = 0.60
    if P.classic:
        w = 0.55
        _legs_for_table(K, P, w, w, h - 0.03, inset=0.05, thick=0.05)
        K.box(-w / 2, w / 2, -w / 2, w / 2, h - 0.03, h, P.main, r=0.008, seg=2)
        K.box(-w / 2 + 0.04, w / 2 - 0.04, -w / 2 + 0.04, w / 2 - 0.04, h - 0.17, h - 0.03, P.main)
        K.box(-w / 2 + 0.06, w / 2 - 0.06, -w / 2 + 0.02, -w / 2 + 0.04, h - 0.16, h - 0.05, P.main, r=0.002, seg=1)
        K.cyl((0, -w / 2 + 0.02, h - 0.105), (0, -w / 2 - 0.01, h - 0.105), 0.014, P.metal, seg=10, r1=0.012)
        K.box(-w / 2 + 0.05, w / 2 - 0.05, -w / 2 + 0.05, w / 2 - 0.05, 0.12, 0.145, P.main)
    else:
        K.cyl((0, 0, h - 0.03), (0, 0, h), 0.27, P.main, seg=28, smooth=False)
        K.cyl((0, 0, 0.02), (0, 0, h - 0.03), 0.25, P.main, seg=28, smooth=False)
        K.cyl((0, 0, 0.0), (0, 0, 0.02), 0.26, P.metal, seg=28)
    return K


def console_table(P):
    """A narrow console table, 1.20 x 0.35 x 0.80 m."""
    K = Mesh('living_console_table')
    w, d, h = 1.20, 0.35, 0.80
    if P.classic:
        _legs_for_table(K, P, w, d, h - 0.07, inset=0.05, thick=0.055)
        K.box(-w / 2, w / 2, -d / 2, d / 2, h - 0.03, h, P.main, r=0.008, seg=2)
        K.box(-w / 2 + 0.04, w / 2 - 0.04, -d / 2 + 0.03, d / 2 - 0.03, h - 0.15, h - 0.03, P.main)
        for dx in (-0.28, 0.28):
            K.box(dx - 0.25, dx + 0.25, -d / 2 + 0.005, -d / 2 + 0.03, h - 0.14, h - 0.05, P.main, r=0.002, seg=1)
            K.cyl((dx, -d / 2 + 0.005, h - 0.095), (dx, -d / 2 - 0.02, h - 0.095), 0.013, P.metal, seg=10, r1=0.011)
    else:
        K.box(-w / 2, w / 2, -d / 2, d / 2, h - 0.03, h, P.main, r=0.005, seg=2)
        for sx in (-1, 1):
            K.box(sx * (w / 2 - 0.06) - 0.012, sx * (w / 2 - 0.06) + 0.012, -d / 2 + 0.04, -d / 2 + 0.065, 0.0, h - 0.03, P.metal)
            K.box(sx * (w / 2 - 0.06) - 0.012, sx * (w / 2 - 0.06) + 0.012, d / 2 - 0.065, d / 2 - 0.04, 0.0, h - 0.03, P.metal)
            K.box(sx * (w / 2 - 0.06) - 0.012, sx * (w / 2 - 0.06) + 0.012, -d / 2 + 0.04, d / 2 - 0.04, 0.32, 0.345, P.metal)
    return K


def tv_stand(P):
    """A media console / TV stand, 1.50 x 0.45 x 0.55 m."""
    K = Mesh('living_tv_stand')
    w, d, h = 1.50, 0.45, 0.55
    yf = -d / 2
    if P.classic:
        K.box(-w / 2 + 0.02, w / 2 - 0.02, yf + 0.04, d / 2 - 0.02, 0.0, 0.07, P.main)
        K.box(-w / 2, w / 2, yf, d / 2, 0.07, h - 0.03, P.main, r=0.005, seg=1)
        K.box(-w / 2 - 0.015, w / 2 + 0.015, yf - 0.015, d / 2 + 0.01, h - 0.03, h, P.main, r=0.008, seg=2)
        third = (w - 0.06) / 3
        for i in range(3):
            a = -w / 2 + 0.03 + i * third
            b = a + third - 0.008
            K.box(a, b, yf - 0.012, yf + 0.008, 0.10, h - 0.06, P.main, r=0.003, seg=1)
            K.box(a + 0.04, b - 0.04, yf - 0.014, yf - 0.011, 0.14, h - 0.10, P.main)
            K.cyl(((a + b) / 2, yf - 0.012, h / 2), ((a + b) / 2, yf - 0.04, h / 2), 0.014, P.metal, seg=10, r1=0.011)
    else:
        for sx in (-1, 1):
            tapered_leg(K, sx * (w / 2 - 0.07), yf + 0.06, 0.14, P.metal, r=0.02, splay=(sx * 0.03, -0.02))
            tapered_leg(K, sx * (w / 2 - 0.07), d / 2 - 0.06, 0.14, P.metal, r=0.02, splay=(sx * 0.03, 0.02))
        K.box(-w / 2, w / 2, yf, d / 2, 0.14, h, P.main, r=0.005, seg=2)
        for i, (a, b) in enumerate(((-w / 2 + 0.03, -0.30), (-0.29, 0.29), (0.30, w / 2 - 0.03))):
            if i == 1:
                K.box(a, b, yf - 0.002, yf + 0.005, 0.19, h - 0.05, P.dark)                      # an open media bay
                K.box(a + 0.02, b - 0.02, yf + 0.01, yf + 0.012, 0.25, 0.27, P.screen)
            else:
                K.box(a, b, yf - 0.012, yf + 0.008, 0.17, h - 0.03, P.main, r=0.003, seg=1)
                K.box(a + 0.03, a + 0.036, yf - 0.014, yf - 0.012, h - 0.20, h - 0.06, P.metal)
    return K


def sideboard(P):
    """A sideboard / buffet with doors and drawers, 1.60 x 0.45 x 0.85 m."""
    K = Mesh('living_sideboard')
    w, d, h = 1.60, 0.45, 0.85
    yf = -d / 2
    if P.classic:
        for sx in (-1, 1):
            K.box(sx * (w / 2 - 0.07) - 0.06, sx * (w / 2 - 0.07) + 0.06, yf + 0.02, yf + 0.10, 0.0, 0.10, P.main, r=0.005, seg=1)
            K.box(sx * (w / 2 - 0.07) - 0.06, sx * (w / 2 - 0.07) + 0.06, d / 2 - 0.10, d / 2 - 0.02, 0.0, 0.10, P.main, r=0.005, seg=1)
        K.box(-w / 2, w / 2, yf, d / 2, 0.10, h - 0.04, P.main, r=0.004, seg=1)
        K.box(-w / 2 - 0.02, w / 2 + 0.02, yf - 0.02, d / 2 + 0.01, h - 0.04, h, P.main, r=0.01, seg=2)
        q = (w - 0.06) / 4
        for i in range(4):
            a = -w / 2 + 0.03 + i * q
            b = a + q - 0.008
            if i in (1, 2):
                for dz in (0.0, 0.13):
                    K.box(a, b, yf - 0.014, yf + 0.008, h - 0.28 + dz, h - 0.16 + dz, P.main, r=0.003, seg=1)
                    K.cyl(((a + b) / 2, yf - 0.014, h - 0.22 + dz), ((a + b) / 2, yf - 0.04, h - 0.22 + dz), 0.012, P.metal, seg=8)
                K.box(a, b, yf - 0.014, yf + 0.008, 0.13, h - 0.30, P.main, r=0.003, seg=1)
                K.cyl(((a + b) / 2, yf - 0.014, 0.40), ((a + b) / 2, yf - 0.04, 0.40), 0.012, P.metal, seg=8)
            else:
                K.box(a, b, yf - 0.014, yf + 0.008, 0.13, h - 0.06, P.main, r=0.003, seg=1)
                K.box(a + 0.04, b - 0.04, yf - 0.016, yf - 0.013, 0.20, h - 0.12, P.main)
                K.cyl(((a + b) / 2 + (0.05 if i == 0 else -0.05), yf - 0.014, h / 2), ((a + b) / 2 + (0.05 if i == 0 else -0.05), yf - 0.04, h / 2), 0.014, P.metal, seg=8)
    else:
        for sx in (-1, 1):
            tapered_leg(K, sx * (w / 2 - 0.08), yf + 0.07, 0.18, P.main, r=0.025, splay=(sx * 0.04, -0.02))
            tapered_leg(K, sx * (w / 2 - 0.08), d / 2 - 0.07, 0.18, P.main, r=0.025, splay=(sx * 0.04, 0.02))
        K.box(-w / 2, w / 2, yf, d / 2, 0.18, h, P.main, r=0.005, seg=2)
        q = (w - 0.04) / 4
        for i in range(4):
            a = -w / 2 + 0.02 + i * q
            b = a + q - 0.006
            K.box(a, b, yf - 0.012, yf + 0.006, 0.20, h - 0.02, P.main, r=0.002, seg=1)
            K.box(a + 0.015, a + 0.02, yf - 0.014, yf - 0.012, h - 0.20, h - 0.10, P.dark)
    return K


# ------------------------------------------------------------------ storage

def _books(K, P, x0, x1, y0, ztop, z0=None):
    """A row of books standing on a shelf (top at z0): random-looking widths and heights in the colours of a small set, the same every run."""
    cols = [material('Book%d' % i, c, 0.8) for i, c in enumerate(((0.55, 0.10, 0.12), (0.12, 0.25, 0.45), (0.14, 0.40, 0.25), (0.82, 0.70, 0.35), (0.35, 0.20, 0.12), (0.9, 0.9, 0.85), (0.2, 0.2, 0.22)))]
    x = x0 + 0.02
    k = 0
    while x < x1 - 0.06:
        bw = 0.025 + 0.012 * ((k * 7) % 4)
        bh = 0.17 + 0.03 * ((k * 5) % 5)
        if x + bw > x1 - 0.02:
            break
        K.box(x, x + bw, y0 + 0.02, y0 + 0.02 + 0.17 + 0.02 * ((k * 3) % 3), ztop, ztop + bh, cols[(k * 3) % len(cols)])
        x += bw + 0.003
        k += 1
        if k % 9 == 0:
            x += 0.10


def bookshelf(P):
    """A tall open bookshelf with five EMPTY shelves (things are placed on them in the game), 0.90 x 0.32 x 1.90 m."""
    K = Mesh('living_bookshelf')
    w, d, h = 0.90, 0.32, 1.90
    cl = P.classic
    yf = -d / 2
    t = 0.025
    K.box(-w / 2, -w / 2 + 0.03, yf, d / 2, 0.0, h, P.main, r=0.003, seg=1)
    K.box(w / 2 - 0.03, w / 2, yf, d / 2, 0.0, h, P.main, r=0.003, seg=1)
    K.box(-w / 2 + 0.03, w / 2 - 0.03, d / 2 - 0.012, d / 2, 0.0, h, P.main)
    base = 0.10 if cl else 0.04
    zs = [base, 0.50, 0.90, 1.30, 1.68]
    for z in zs:
        K.box(-w / 2 + 0.03, w / 2 - 0.03, yf + 0.005, d / 2 - 0.012, z, z + t, P.main)
    K.box(-w / 2 - (0.02 if cl else 0.0), w / 2 + (0.02 if cl else 0.0), yf - (0.02 if cl else 0.0), d / 2 + (0.01 if cl else 0.0), h - 0.03, h + (0.0 if not cl else 0.03), P.main, r=0.006, seg=1)
    if cl:
        K.box(-w / 2 + 0.03, w / 2 - 0.03, yf, yf + 0.02, 0.0, 0.10, P.main)
    return K


def display_cabinet(P):
    """A glass-door display cabinet with shelves, 0.95 x 0.42 x 1.85 m."""
    K = Mesh('living_display_cabinet')
    w, d, h = 0.95, 0.42, 1.85
    yf = -d / 2
    cl = P.classic
    if cl:
        for sx in (-1, 1):
            K.box(sx * (w / 2 - 0.06) - 0.05, sx * (w / 2 - 0.06) + 0.05, yf + 0.03, yf + 0.11, 0.0, 0.10, P.main, r=0.005, seg=1)
            K.box(sx * (w / 2 - 0.06) - 0.05, sx * (w / 2 - 0.06) + 0.05, d / 2 - 0.11, d / 2 - 0.03, 0.0, 0.10, P.main, r=0.005, seg=1)
    else:
        for sx in (-1, 1):
            tapered_leg(K, sx * (w / 2 - 0.06), yf + 0.06, 0.12, P.metal, r=0.016)
            tapered_leg(K, sx * (w / 2 - 0.06), d / 2 - 0.06, 0.12, P.metal, r=0.016)
    z0 = 0.10 if cl else 0.12
    K.box(-w / 2, w / 2, yf, d / 2, z0, 0.80, P.main, r=0.003, seg=1)                          # the closed lower cabinet
    for sx in (-1, 1):
        K.box(sx * (w / 2 - 0.015) - 0.015, sx * (w / 2 - 0.015) + 0.015, yf, d / 2, 0.80, h - 0.05, P.main)
    K.box(-w / 2, w / 2, d / 2 - 0.012, d / 2, 0.80, h - 0.05, P.main)
    K.box(-w / 2 - (0.02 if cl else 0.0), w / 2 + (0.02 if cl else 0.0), yf - (0.02 if cl else 0.0), d / 2 + (0.01 if cl else 0.0), h - 0.05, h, P.main, r=0.006, seg=1)
    for z in (0.80, 1.12, 1.44):
        K.box(-w / 2 + 0.03, w / 2 - 0.03, yf + 0.02, d / 2 - 0.012, z, z + 0.012, P.glass)
    half = (w - 0.03) / 2
    for sx in (-1, 1):
        a, b = (-w / 2 + 0.015, -0.002) if sx < 0 else (0.002, w / 2 - 0.015)
        K.box(a, b, yf - 0.012, yf + 0.008, z0 + 0.02, 0.78, P.main, r=0.003, seg=1)                          # the lower doors
        K.cyl(((a + b) / 2 + sx * -0.3 * 0 + (0.08 if sx < 0 else -0.08), yf - 0.012, 0.50), ((a + b) / 2 + (0.08 if sx < 0 else -0.08), yf - 0.04, 0.50), 0.013, P.metal, seg=8)
        K.box(a, b, yf - 0.006, yf + 0.0, 0.82, h - 0.07, P.main)                                              # the glass door frame
        K.box(a + 0.035, b - 0.035, yf - 0.007, yf + 0.001, 0.855, h - 0.105, P.glass)
    return K


def toy_chest(P):
    """A toy chest with a lid, 0.80 x 0.45 x 0.50 m."""
    K = Mesh('living_toy_chest')
    w, d, h = 0.80, 0.45, 0.50
    cl = P.classic
    K.box(-w / 2, w / 2, -d / 2, d / 2, 0.0 if cl else 0.06, h - 0.07, P.main, r=0.004, seg=1)
    if not cl:
        for sx in (-1, 1):
            for sy in (-1, 1):
                tapered_leg(K, sx * (w / 2 - 0.06), sy * (d / 2 - 0.06), 0.07, P.metal, r=0.016)
    K.box(-w / 2 - 0.01, w / 2 + 0.01, -d / 2 - 0.01, d / 2 + 0.01, h - 0.07, h, P.main, r=0.008, seg=2)
    if cl:
        for sx in (-1, 1):
            K.box(sx * (w / 2 - 0.07) - 0.025, sx * (w / 2 - 0.07) + 0.025, -d / 2 - 0.012, -d / 2 + 0.004, 0.02, h - 0.02, P.metal)
        K.box(-0.05, 0.05, -d / 2 - 0.014, -d / 2 + 0.004, h - 0.16, h - 0.08, P.metal)
        K.cyl((0, -d / 2 - 0.014, h - 0.12), (0, -d / 2 - 0.02, h - 0.12), 0.012, P.dark, seg=8)
    else:
        K.box(-0.10, 0.10, -d / 2 - 0.011, -d / 2 - 0.009, h - 0.12, h - 0.10, P.dark)
    for sx in (-1, 1):
        K.box(sx * (w / 2 - 0.12) - 0.04, sx * (w / 2 - 0.12) + 0.04, d / 2 + 0.01, d / 2 + 0.02, h - 0.10, h - 0.03, P.metal)
    return K


def piano(P):
    """An upright piano (classic) or a slim digital piano on a stand (modern), 1.50 x 0.65 x 1.25 m."""
    K = Mesh('living_piano')
    w = 1.50
    if P.classic:
        d, h = 0.62, 1.25
        yf = -d / 2
        K.box(-w / 2 + 0.03, w / 2 - 0.03, yf + 0.04, d / 2 - 0.02, 0.0, 0.10, P.main)
        K.box(-w / 2, w / 2, yf + 0.06, d / 2, 0.10, h - 0.05, P.main, r=0.006, seg=1)
        K.box(-w / 2 - 0.015, w / 2 + 0.015, yf + 0.04, d / 2 + 0.01, h - 0.05, h, P.main, r=0.008, seg=2)
        K.box(-w / 2 + 0.02, w / 2 - 0.02, yf - 0.02, yf + 0.20, 0.70, 0.74, P.main)                                  # the key slip and fallboard
        K.box(-w / 2 + 0.05, w / 2 - 0.05, yf - 0.20, yf + 0.20, 0.66, 0.70, P.main, r=0.004, seg=1)                   # the keyboard shelf
        K.box(-w / 2 + 0.07, w / 2 - 0.07, yf - 0.185, yf + 0.06, 0.70, 0.725, P.white)                                # the white keys
        for k in range(36):
            kx = -w / 2 + 0.07 + (w - 0.14) * (k + 0.5) / 36 * 0.0 + (w - 0.14) * (k + 0.75) / 36
            if k % 7 in (2, 6):
                continue
            K.box(kx - 0.007, kx + 0.007, yf - 0.185, yf - 0.06, 0.725, 0.745, P.black)
        K.box(-w / 2 + 0.05, w / 2 - 0.05, yf + 0.18, yf + 0.20, 0.74, 1.0, P.main)                                   # the music desk
        K.box(-0.35, 0.35, yf + 0.14, yf + 0.18, 0.80, 0.95, P.cream)
        K.box(-w / 2 + 0.06, w / 2 - 0.06, yf + 0.04, yf + 0.12, 0.16, 0.62, P.main, r=0.004, seg=1)                   # the lower panel
        for px in (-0.08, 0.0, 0.08):
            K.cyl((px, yf + 0.06, 0.04), (px, yf + 0.06, 0.12), 0.012, P.metal, seg=8)                                # the pedals
        for sx in (-1, 1):
            K.cyl((sx * 0.36, yf + 0.045, 0.40), (sx * 0.36, yf + 0.03, 0.40), 0.03, P.metal, seg=10)                  # candle holder discs
    else:
        d, h = 0.34, 0.95
        yf = -d / 2
        for sx in (-1, 1):
            K.box(sx * (w / 2 - 0.12) - 0.02, sx * (w / 2 - 0.12) + 0.02, yf + 0.04, d / 2 - 0.04, 0.0, 0.76, P.metal)
            K.box(sx * (w / 2 - 0.12) - 0.05, sx * (w / 2 - 0.12) + 0.05, yf, d / 2, 0.0, 0.03, P.metal)
        K.box(-w / 2 + 0.12, w / 2 - 0.12, yf + 0.06, yf + 0.08, 0.30, 0.34, P.metal)
        K.box(-w / 2 + 0.05, w / 2 - 0.05, yf, d / 2, 0.76, 0.84, P.main, r=0.008, seg=2)                              # the body
        K.box(-w / 2 + 0.10, w / 2 - 0.10, yf - 0.04, yf + 0.03, 0.80, 0.86, P.white)                                 # keys
        for k in range(30):
            kx = -w / 2 + 0.10 + (w - 0.20) * (k + 0.75) / 30
            if k % 7 in (2, 6):
                continue
            K.box(kx - 0.007, kx + 0.007, yf - 0.04, yf + 0.0, 0.86, 0.875, P.black)
        K.box(-0.35, 0.35, d / 2 - 0.04, d / 2 - 0.02, 0.84, 0.95, P.dark)                                             # a music stand
        K.box(-0.20, 0.20, yf + 0.04, yf + 0.06, 0.845, 0.848, P.lcd if hasattr(P, 'lcd') else P.screen)
    return K


# ------------------------------------------------------------------ lighting and decor

def _lamp(name, P, floor):
    K = Mesh(name)
    cl = P.classic
    metal = P.brass if cl else P.chrome
    if floor:
        H = 1.62
        K.lathe([(0.0, 0.0), (0.16, 0.0), (0.17, 0.015), (0.14, 0.03), (0.0, 0.035)], metal if cl else P.dark, at=(0, 0, 0), seg=24, hard=(1,))
        K.cyl((0, 0, 0.03), (0, 0, H - 0.20), 0.012, metal, seg=10)
        if cl:
            for z, r in ((0.45, 0.025), (0.95, 0.02)):
                K.lathe([(0.0, -r), (r, -r * 0.5), (r * 1.2, 0.0), (r, r * 0.5), (0.0, r)], metal, at=(0, 0, z), seg=10)
        else:
            K.cyl((0, 0, H - 0.22), (0.18, 0, H - 0.12), 0.012, metal, seg=8)
        sx = 0.0 if cl else 0.18
        K.lathe([(0.0, H - 0.30), (0.20, H - 0.30), (0.15, H - 0.02), (0.0, H - 0.02)] if cl else [(0.0, H - 0.34), (0.16, H - 0.34), (0.16, H - 0.12), (0.0, H - 0.12)],
                P.main, at=(sx, 0, 0), seg=20, hard=(1, 2))
        K.cyl((sx, 0, H - 0.31), (sx, 0, H - 0.27), 0.03, P.white, seg=10)
    else:
        H = 0.56
        if cl:
            K.lathe([(0.0, 0.0), (0.08, 0.0), (0.095, 0.03), (0.10, 0.12), (0.06, 0.22), (0.035, 0.27), (0.0, 0.28)], metal, at=(0, 0, 0), seg=18, hard=(1,))
            K.lathe([(0.0, H - 0.27), (0.17, H - 0.27), (0.12, H - 0.02), (0.0, H - 0.02)], P.main, at=(0, 0, 0.0), seg=20, hard=(1, 2))
        else:
            K.cyl((0, 0, 0.0), (0, 0, 0.22), 0.08, P.dark, seg=20)
            K.cyl((0, 0, 0.22), (0, 0, 0.30), 0.012, P.chrome, seg=8)
            K.lathe([(0.0, 0.26), (0.13, 0.26), (0.13, 0.50), (0.0, 0.50)], P.main, at=(0, 0, 0.0), seg=20, hard=(1, 2))
    return K


def floor_lamp(P):
    """A floor lamp with a fabric shade, 0.40 x 0.40 x 1.62 m. It lights a room when it has power."""
    return _lamp('living_floor_lamp', P, True)


def table_lamp(P):
    """A table lamp with a fabric shade, 0.34 x 0.34 x 0.56 m. It lights a room when it has power."""
    return _lamp('living_table_lamp', P, False)


def area_rug(P):
    """An area rug with a border and a medallion, 2.40 x 1.70 x 0.015 m."""
    K = Mesh('living_area_rug')
    w, d, t = 2.40, 1.70, 0.015
    bm = K.bm
    i = K.mi(P.main)
    layer = K.uv
    v = [bm.verts.new(c) for c in ((-w / 2, -d / 2, 0), (w / 2, -d / 2, 0), (w / 2, d / 2, 0), (-w / 2, d / 2, 0),
                                     (-w / 2, -d / 2, t), (w / 2, -d / 2, t), (w / 2, d / 2, t), (-w / 2, d / 2, t))]
    top = bm.faces.new((v[4], v[5], v[6], v[7]))
    sides = [bm.faces.new((v[0], v[1], v[5], v[4])), bm.faces.new((v[1], v[2], v[6], v[5])), bm.faces.new((v[2], v[3], v[7], v[6])), bm.faces.new((v[3], v[0], v[4], v[7])), bm.faces.new((v[3], v[2], v[1], v[0]))]
    for f in [top] + sides:
        f.material_index = i
        f.smooth = False
    for loop in top.loops:
        c = loop.vert.co
        loop[layer].uv = ((c.x + w / 2) / w, (c.y + d / 2) / d)
    for f in sides:
        for loop in f.loops:
            loop[layer].uv = (0.02, 0.02)
    return K


def plant_pot(P):
    """A potted plant with a ceramic pot in the piece's colour, 0.45 x 0.45 x 1.15 m."""
    K = Mesh('living_plant')
    K.lathe([(0.0, 0.0), (0.12, 0.0), (0.17, 0.30), (0.19, 0.31), (0.19, 0.34), (0.16, 0.34), (0.0, 0.33)], material('Pot_' + P.key, P.rgb(), 0.4), at=(0, 0, 0), seg=20, hard=(1, 3, 4))
    K.cyl((0, 0, 0.32), (0, 0, 0.34), 0.165, P.dark, seg=18)
    for k in range(9):
        a = 2 * math.pi * k / 9
        lean = 0.13 + 0.05 * (k % 3)
        top = 0.78 + 0.07 * ((k * 5) % 4)
        K.cyl((0.02 * math.cos(a), 0.02 * math.sin(a), 0.33), (lean * math.cos(a), lean * math.sin(a), top), 0.008, P.green, seg=5)
        K.lathe([(0.0, 0.0), (0.04, 0.05), (0.03, 0.14), (0.0, 0.22)], P.green, at=(lean * math.cos(a), lean * math.sin(a), top - 0.02), seg=6)
    K.cyl((0.0, 0.0, 0.33), (0.0, 0.0, 1.0), 0.012, P.green, seg=5)
    K.lathe([(0.0, 0.0), (0.06, 0.06), (0.05, 0.20), (0.0, 0.34)], P.green, at=(0.0, 0.0, 0.92), seg=8)
    return K


def tv(P):
    """A flat-screen TV on a stand (modern) or a wood-cabinet CRT television (classic), 1.25 x 0.25 x 0.80 m (classic 0.72 x 0.58 x 0.62 m)."""
    K = Mesh('living_tv')
    if P.classic:
        w, d, h = 0.72, 0.58, 0.62
        yf = -d / 2
        K.box(-w / 2, w / 2, yf, d / 2 - 0.08, 0.04, h, P.main, r=0.008, seg=2)
        K.box(-w / 2 + 0.05, w / 2 - 0.05, d / 2 - 0.30, d / 2, 0.20, h - 0.12, P.dark)
        K.box(-w / 2 + 0.03, w / 2 - 0.03, yf + 0.02, d / 2 - 0.10, 0.0, 0.04, P.main)
        K.box(-w / 2 + 0.04, w / 2 - 0.20, yf - 0.012, yf + 0.01, 0.10, h - 0.06, P.dark)                      # the screen bezel
        K.box(-w / 2 + 0.07, w / 2 - 0.23, yf - 0.016, yf - 0.011, 0.14, h - 0.10, P.screen)
        for k in range(2):
            K.cyl((w / 2 - 0.10, yf, 0.45 - k * 0.12), (w / 2 - 0.10, yf - 0.03, 0.45 - k * 0.12), 0.025, P.dark, seg=14)
            K.cyl((w / 2 - 0.10, yf - 0.03, 0.45 - k * 0.12), (w / 2 - 0.10, yf - 0.04, 0.45 - k * 0.12), 0.018, P.metal, seg=12)
        K.box(w / 2 - 0.18, w / 2 - 0.04, yf - 0.012, yf - 0.008, 0.20, 0.32, P.dark)                         # speaker slots
        for k in range(5):
            K.box(w / 2 - 0.17, w / 2 - 0.05, yf - 0.014, yf - 0.011, 0.215 + k * 0.022, 0.225 + k * 0.022, P.metal)
        K.cyl((0.0, 0.0, h), (-0.12, 0.05, h + 0.25), 0.005, P.metal, seg=5)
        K.cyl((0.0, 0.0, h), (0.14, 0.04, h + 0.28), 0.005, P.metal, seg=5)
    else:
        w, h = 1.25, 0.80
        K.box(-0.22, 0.22, -0.11, 0.11, 0.0, 0.02, P.main if P.key in ('black', 'charcoal') else P.dark)
        K.box(-0.02, 0.02, -0.02, 0.05, 0.02, 0.18, P.metal)
        K.rbox(-w / 2, w / 2, -0.02, 0.03, 0.12, h, P.dark, 0.006, rv=0.004, seg=2)
        K.box(-w / 2 + 0.012, w / 2 - 0.012, -0.0225, -0.02, 0.132, h - 0.012, P.screen)
        K.box(-0.12, 0.12, -0.03, 0.0, 0.14, 0.15, P.dark)
        K.box(-0.01, 0.01, 0.03, 0.05, 0.45, 0.75, P.dark)
    return K


def _wall_back(K, d):
    K.shift(0, -d / 2, 0)


def wall_mirror(P):
    """A wall mirror in a frame (rectangular classic, round modern), 0.80 x 0.05 x 1.10 m. A wall item."""
    K = Mesh('living_wall_mirror')
    mirror = material('MirrorGlass', (0.85, 0.88, 0.90), 0.02, 1.0)
    d = 0.05
    if P.classic:
        w, h = 0.80, 1.10
        K.box(-w / 2, w / 2, -d / 2, d / 2, 0.0, h, P.main, r=0.006, seg=2)
        K.box(-w / 2 + 0.05, w / 2 - 0.05, -d / 2 - 0.003, -d / 2 + 0.012, 0.05, h - 0.05, P.metal)
        K.box(-w / 2 + 0.07, w / 2 - 0.07, -d / 2 - 0.008, -d / 2 - 0.003, 0.07, h - 0.07, mirror)
        K.box(-0.07, 0.07, -d / 2 - 0.006, -d / 2 + 0.004, h - 0.012, h + 0.04, P.main)
    else:
        r = 0.45
        K.cyl((0, -d / 2 + 0.02, r), (0, d / 2, r), r, P.metal, seg=40)
        K.cyl((0, -d / 2 + 0.01, r), (0, -d / 2 + 0.02, r), r - 0.025, mirror, seg=40)
        K.box(-0.03, 0.03, d / 2 - 0.005, d / 2, r * 2 - 0.05, r * 2 - 0.02, P.metal)
    _wall_back(K, d)
    return K


def wall_art(P):
    """A framed picture, 0.90 x 0.04 x 0.70 m. A wall item."""
    K = Mesh('living_wall_art')
    d = 0.04
    w, h = 0.90, 0.70
    fr = 0.06 if P.classic else 0.025
    K.box(-w / 2, w / 2, -d / 2, d / 2, 0.0, h, P.main, r=0.004, seg=2)
    if P.classic:
        K.box(-w / 2 + fr, w / 2 - fr, -d / 2 - 0.004, -d / 2 + 0.01, fr, h - fr, P.metal)
        sky, hill1, hill2, sun = (material('ArtSky', (0.62, 0.78, 0.88), 0.9), material('ArtHillA', (0.22, 0.45, 0.24), 0.9), material('ArtHillB', (0.40, 0.55, 0.28), 0.9), material('ArtSun', (0.95, 0.82, 0.35), 0.8))
        x0, x1, z0, z1 = -w / 2 + fr + 0.02, w / 2 - fr - 0.02, fr + 0.02, h - fr - 0.02
        K.box(x0, x1, -d / 2 - 0.006, -d / 2 - 0.004, z0, z1, sky)
        K.box(x0, x1, -d / 2 - 0.008, -d / 2 - 0.006, z0, z0 + (z1 - z0) * 0.40, hill1)
        K.box(x0 + 0.20, x0 + 0.52, -d / 2 - 0.008, -d / 2 - 0.006, z0 + (z1 - z0) * 0.35, z0 + (z1 - z0) * 0.55, hill2)
        K.cyl((x1 - 0.16, -d / 2 - 0.008, z1 - 0.12), (x1 - 0.16, -d / 2 - 0.010, z1 - 0.12), 0.07, sun, seg=16)
    else:
        cols = [material('ArtA', (0.80, 0.30, 0.18), 0.8), material('ArtB', (0.10, 0.35, 0.45), 0.8), material('ArtC', (0.92, 0.80, 0.30), 0.8), material('ArtD', (0.93, 0.92, 0.88), 0.9)]
        x0, x1, z0, z1 = -w / 2 + fr, w / 2 - fr, fr, h - fr
        K.box(x0, x1, -d / 2 - 0.004, -d / 2 - 0.002, z0, z1, cols[3])
        K.box(x0 + 0.05, x0 + 0.40, -d / 2 - 0.006, -d / 2 - 0.004, z0 + 0.06, z1 - 0.20, cols[0])
        K.box(x0 + 0.30, x1 - 0.10, -d / 2 - 0.008, -d / 2 - 0.006, z0 + 0.20, z1 - 0.10, cols[1])
        K.cyl((x1 - 0.20, -d / 2 - 0.010, z0 + 0.18), (x1 - 0.20, -d / 2 - 0.012, z0 + 0.18), 0.10, cols[2], seg=20)
    _wall_back(K, d)
    return K


def wall_clock(P):
    """A round wall clock, 0.50 m across, 0.06 m deep. A wall item."""
    K = Mesh('living_wall_clock')
    d, r = 0.06, 0.25
    rr = r
    z = r
    face = material('ClockFace', (0.95, 0.94, 0.90), 0.7)
    if P.classic:
        K.cyl((0, -d / 2 + 0.02, z), (0, d / 2, z), rr, P.main, seg=32)
        K.cyl((0, -d / 2 + 0.012, z), (0, -d / 2 + 0.02, z), rr - 0.035, face, seg=32)
    else:
        K.cyl((0, -d / 2 + 0.02, z), (0, d / 2, z), rr, P.metal if P.key not in ('white', 'black') else P.main, seg=32)
        K.cyl((0, -d / 2 + 0.012, z), (0, -d / 2 + 0.02, z), rr - 0.012, face, seg=32)
    for k in range(12):
        a = math.radians(30 * k)
        L = 0.03 if k % 3 == 0 else 0.015
        K.box(math.sin(a) * (rr - 0.045) - 0.004, math.sin(a) * (rr - 0.045) + 0.004, -d / 2 + 0.008, -d / 2 + 0.012, z + math.cos(a) * (rr - 0.045) - L / 2, z + math.cos(a) * (rr - 0.045) + L / 2, P.dark)
    K.box(-0.005, 0.005, -d / 2 + 0.003, -d / 2 + 0.012, z, z + 0.11, P.dark)
    K.box(-0.004, 0.0, -d / 2 + 0.003, -d / 2 + 0.012, z - 0.02, z + 0.015, P.dark)
    K.box(0.0, 0.14, -d / 2 + 0.003, -d / 2 + 0.008, z - 0.004, z + 0.004, P.dark)
    _wall_back(K, d)
    return K


def _wall_tv(name, P, w, h):
    M = Mesh(name)
    d, back = 0.04, 0.03
    yf, yb = -(back + d), -back                      # the panel's front and back planes; the bracket fills the rest to the wall
    bez = 0.045 if P.classic else 0.008
    # the bracket on the wall: a plate and two arms
    M.box(-0.20, 0.20, -back, 0.0, h * 0.5 - 0.12, h * 0.5 + 0.12, P.dark)
    # the set: a body, a bezel and the dark glass
    M.box(-w / 2, w / 2, yf, yb, 0.0, h, P.black, r=0.006, seg=1)
    if P.classic:
        M.box(-w / 2, w / 2, yf - 0.012, yb, 0.0, h, P.main, r=0.008, seg=2)                         # a wood frame round the set
        M.box(-w / 2 + bez, w / 2 - bez, yf - 0.016, yf - 0.011, bez, h - bez, P.dark)
        M.box(-w / 2 + bez + 0.01, w / 2 - bez - 0.01, yf - 0.018, yf - 0.016, bez + 0.01, h - bez - 0.01, P.screen)
    else:
        M.box(-w / 2 + bez, w / 2 - bez, yf - 0.002, yf, bez, h - bez, P.screen)
        M.box(w / 2 - 0.08, w / 2 - 0.06, yf - 0.003, yf - 0.002, 0.004, 0.006, P.main)       # the power light
    return M


def wall_tv(P):
    """A flat-screen TV on a wall bracket (55 inch), 1.23 x 0.07 x 0.69 m. Classic has a wood frame, modern a thin bezel. A wall item."""
    return _wall_tv('living_wall_tv', P, 1.23, 0.69)


def wall_tv_large(P):
    """A large flat-screen TV on a wall bracket (75 inch), 1.66 x 0.07 x 0.94 m. A wall item."""
    return _wall_tv('living_wall_tv_large', P, 1.66, 0.94)
