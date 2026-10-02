"""
Builds the four stage models of the STARTER HOUSE (a framed, sided house with a front porch) in headless Blender: free, local,
low-poly. A more detailed sibling of the log cabin (tools/make_structure_stages.py, which this reuses): see
docs/STRUCTURE_STAGES_GUIDE.md for the conventions (metres, pivot at the footprint centre, ground at z = 0, front = -Y, FrontMarker,
DoorHinge > DoorLeaf, WindowGlass).

  foundation  slab with a footing step down, anchor bolts, rebar stubs, three front steps
  framing     porch deck, sill plates, studs every 0.4 m with doubled headers and rough openings, double top plates, ceiling joists,
              rafters with collar ties and a ridge board, porch posts and beam
  walls       the framing wrapped in sheathing (openings cut), a sheathed roof deck, porch deck boards, rough window boxes
  complete    clapboard siding, corner and window trim with muntins, shutters, panel door, porch with railing and steps, shingled roof
              with ridge cap, fascia, a brick chimney, glazed windows (WindowGlass, shadow-free)

    blender --background --python tools/make_house_stages.py -- starter_house
"""
import json
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_structure_stages as base  # noqa: E402  (a library here: its main() only runs when it is the script)

Builder = base.Builder
ROOT = base.ROOT
STRUCTURES = base.STRUCTURES

PORCH_D = 1.6            # depth of the front porch inside the footprint
WALL_H = 2.5             # wall height above the floor
T_SIDING, T_SHEATH, T_STUD = 0.03, 0.02, 0.14
DOOR_W, DOOR_H = 1.2, 2.3
WIN_W, WIN_H, WIN_SILL = 0.95, 1.25, 0.9


def colour(name, rgb, rough=0.85):
    return base.material(name, rgb, rough)


class Ctx:
    """Everything the stage builders share."""

    def __init__(self, w, d, h_total, found_h):
        self.w, self.d, self.h_total = w, d, h_total
        self.z0 = found_h + 0.04               # the floor
        self.top = self.z0 + WALL_H             # top of the walls
        self.yh0 = -d / 2 + PORCH_D             # the front wall's outer plane (behind the porch)
        self.ov = 0.35                          # roof overhang
        self.zr = h_total - 0.2                 # rafter centre line at the ridge
        self.half = w / 2
        # openings per wall: u0, u1 along the wall (x for front/back, y for left/right), z0, z1 above the floor
        win = lambda c: (c - WIN_W / 2, c + WIN_W / 2, WIN_SILL, WIN_SILL + WIN_H)
        ya, yb = self.yh0 + 1.5, self.yh0 + 4.2
        self.openings = {
            'front': [(-DOOR_W / 2, DOOR_W / 2, 0.0, DOOR_H), win(-1.85), win(1.85)],
            'back': [win(-1.2), win(1.2)],
            'left': [win(ya), win(yb)],
            'right': [win(ya), win(yb)],
        }


def blocked(openings, lo, hi, za, zb, pad=0.0):
    """Intervals along a wall that stay open in the band za..zb."""
    return sorted((u0 - pad, u1 + pad) for u0, u1, z0, z1 in openings if za < z1 + 0.0001 and zb > z0 - 0.0001)


def pieces(lo, hi, gaps, min_len=0.04):
    """lo..hi cut by the gaps."""
    cuts = [lo]
    for g0, g1 in gaps:
        cuts += [max(lo, g0), min(hi, g1)]
    cuts.append(hi)
    out = []
    for k in range(0, len(cuts), 2):
        if cuts[k + 1] - cuts[k] > min_len:
            out.append((cuts[k], cuts[k + 1]))
    return out


def wall_box(b, c, wall, depth0, depth1, za, zb, m, openings=None, gap_pad=0.0, inset=0.0):
    """A band of one wall between two depths measured inward from the outer plane, split round the openings."""
    z0 = c.z0
    ops = [(a, bb, z0 + zl, z0 + zh) for a, bb, zl, zh in (c.openings[wall] if openings is None else openings)]
    w, d, yh0 = c.w, c.d, c.yh0
    if wall in ('front', 'back'):
        lo, hi = -w / 2 + inset, w / 2 - inset
    else:
        lo, hi = yh0 + 0.0, d / 2
    for u0, u1 in pieces(lo, hi, blocked(ops, lo, hi, za, zb, gap_pad)):
        if wall == 'front':
            b.box(u0, u1, yh0 + depth0, yh0 + depth1, za, zb, m)
        elif wall == 'back':
            b.box(u0, u1, d / 2 - depth1, d / 2 - depth0, za, zb, m)
        elif wall == 'left':
            b.box(-w / 2 + depth0, -w / 2 + depth1, u0, u1, za, zb, m)
        else:
            b.box(w / 2 - depth1, w / 2 - depth0, u0, u1, za, zb, m)


# ------------------------------------------------------------------ pieces shared by several stages

FB = None   # the separate "Foundation" object while a stage is built (the game can swap it for another foundation style)


def foundation(b, c, M):
    b = FB if FB is not None else b
    w, d = c.w, c.d
    h = c.z0 - 0.04                              # slab height
    conc, dark = M['concrete'], M['concrete_dark']
    b.box(-w / 2, w / 2, -d / 2, d / 2, 0.0, h, conc)
    b.box(-w / 2 - 0.06, w / 2 + 0.06, -d / 2 - 0.06, d / 2 + 0.06, 0.0, h * 0.45, dark)          # the wider footing
    for x0, x1, y0, y1 in ((-w / 2, w / 2, -d / 2, -d / 2 + 0.06), (-w / 2, w / 2, d / 2 - 0.06, d / 2),
                           (-w / 2, -w / 2 + 0.06, -d / 2, d / 2), (w / 2 - 0.06, w / 2, -d / 2, d / 2)):
        b.box(x0, x1, y0, y1, h, h + 0.04, conc)                                                   # a low lip round the edge
    for k in range(3):                                                                           # three front steps
        b.box(-0.8, 0.8, -d / 2 - 0.3 * (k + 1), -d / 2, 0.0, h * (1 - (k + 1) * 0.28), conc)
    # anchor bolts along the walls and rebar stubs poking out of the slab
    for u in (-2.2, -0.7, 0.7, 2.2):
        b.box(u - 0.012, u + 0.012, c.yh0 + 0.08, c.yh0 + 0.10, h, h + 0.12, M['steel'])
        b.box(u - 0.012, u + 0.012, d / 2 - 0.10, d / 2 - 0.08, h, h + 0.12, M['steel'])
    for v in (c.yh0 + 1.2, c.yh0 + 2.8, c.yh0 + 4.4):
        b.box(-w / 2 + 0.08, -w / 2 + 0.10, v - 0.012, v + 0.012, h, h + 0.12, M['steel'])
        b.box(w / 2 - 0.10, w / 2 - 0.08, v - 0.012, v + 0.012, h, h + 0.12, M['steel'])
    return h


def porch_posts(b, c, M, top_z):
    w, d = c.w, c.d
    for x in (-w / 2 + 0.12, 0.0, w / 2 - 0.12):
        b.box(x - 0.07, x + 0.07, -d / 2 + 0.08, -d / 2 + 0.22, c.z0, top_z, M['lumber'])


def rafters(b, c, M, spacing=0.6, collar=True):
    w, d, ov = c.w, c.d, c.ov
    top, zr = c.top, c.zr
    y0, y1 = -d / 2 - ov, d / 2 + ov
    b.box(-0.04, 0.04, y0, y1, zr - 0.09, zr + 0.09, M['lumber'])                                   # the ridge board
    n = max(3, int((y1 - y0) / spacing) + 1)
    for k in range(n):
        y = y0 + (y1 - y0) * k / (n - 1)
        for side in (-1, 1):
            b.log((side * (w / 2 + ov), y, top - 0.12), (side * 0.04, y, zr), 0.05, M['lumber'], sides=6)
        if collar and k % 2 == 0:
            zc = top + (zr - top) * 0.55
            xc = (w / 2 + ov) * (1 - (zc - (top - 0.12)) / (zr - (top - 0.12)))
            b.box(-xc, xc, y - 0.03, y + 0.03, zc, zc + 0.05, M['lumber'])                           # collar ties


def deck_boards(b, c, M, z, y0, y1):
    """Porch / floor boards laid across x."""
    w = c.w
    n = int((y1 - y0) / 0.14)
    for k in range(n):
        ya = y0 + k * (y1 - y0) / n
        b.box(-w / 2, w / 2, ya + 0.004, ya + (y1 - y0) / n - 0.004, z, z + 0.035, M['deck'])


def window_dressing(b, c, M, glass, wall, u0, u1, zl, zh, shutters=False):
    """Trim, muntins, sill and the glass pane for one window on a wall (outer face at depth 0)."""
    z0 = c.z0
    za, zb = z0 + zl, z0 + zh
    t = 0.07
    for (a0, a1, b0, b1) in ((u0 - t, u0, za - t, zb + t), (u1, u1 + t, za - t, zb + t), (u0 - t, u1 + t, za - t, za), (u0 - t, u1 + t, zb, zb + t)):
        trim_box(b, c, wall, a0, a1, b0, b1, -0.05, 0.03, M['trim'])
    um = (u0 + u1) / 2
    trim_box(b, c, wall, um - 0.015, um + 0.015, za, zb, -0.03, 0.012, M['trim'])                     # muntins
    trim_box(b, c, wall, u0, u1, (za + zb) / 2 - 0.015, (za + zb) / 2 + 0.015, -0.03, 0.012, M['trim'])
    trim_box(b, c, wall, u0 - t - 0.04, u1 + t + 0.04, za - t - 0.04, za - t, -0.09, 0.03, M['trim'])  # sill
    trim_box(b, c, wall, u0, u1, za, zb, 0.02, 0.05, glass, to=glass_builder)
    if shutters:
        for s0, s1 in ((u0 - t - 0.42, u0 - t - 0.04), (u1 + t + 0.04, u1 + t + 0.42)):
            trim_box(b, c, wall, s0, s1, za - t, zb + t, -0.04, 0.0, M['shutter'])


glass_builder = None


def trim_box(b, c, wall, u0, u1, za, zb, d0, d1, m, to=None):
    """A box on the outer face of a wall: u0..u1 along it, z (absolute) za..zb, d0..d1 outward (negative) / inward (positive) of the outer plane."""
    target = to if to is not None else b
    if wall == 'front':
        target.box(u0, u1, c.yh0 + d0, c.yh0 + d1, za, zb, m)
    elif wall == 'back':
        target.box(u0, u1, c.d / 2 - d1, c.d / 2 - d0, za, zb, m)
    elif wall == 'left':
        target.box(-c.w / 2 + d0, -c.w / 2 + d1, u0, u1, za, zb, m)
    else:
        target.box(c.w / 2 - d1, c.w / 2 - d0, u0, u1, za, zb, m)


# ------------------------------------------------------------------ stages

def framing(b, c, M):
    w, d = c.w, c.d
    h = foundation(b, c, M)
    z0, top = c.z0, c.top
    # a subfloor over the whole footprint, then the sill plates and studs
    b.box(-w / 2 + 0.02, w / 2 - 0.02, -d / 2 + 0.02, d / 2 - 0.02, h, z0, M['osb'])
    for wall in ('front', 'back', 'left', 'right'):
        wall_box(b, c, wall, 0.05, 0.05 + T_STUD, z0, z0 + 0.04, M['lumber'], openings=[])                # sill plate
        # studs every 0.4 m, kept out of the openings (king studs and headers instead)
        ops = [(a, bb, z0 + zl, z0 + zh) for a, bb, zl, zh in c.openings[wall]]
        lo, hi = (-w / 2 + 0.2, w / 2 - 0.2) if wall in ('front', 'back') else (c.yh0 + 0.2, d / 2 - 0.2)
        n = int((hi - lo) / 0.4) + 1
        for k in range(n):
            u = lo + k * (hi - lo) / max(1, n - 1)
            za = z0 + 0.04
            zb = top
            gap = [o for o in ops if o[0] - 0.05 < u < o[1] + 0.05]
            for o in gap:
                zb2 = o[2] - 0.0
                # jack studs: below the sill and above the header only
                spans = [(za, o[2] - 0.1), (o[3] + 0.12, zb)]
                for sa, sb in spans:
                    if sb - sa > 0.05:
                        stud(b, c, wall, u, sa, sb, M)
            if not gap:
                stud(b, c, wall, u, za, zb, M)
        # doubled headers and sills of the openings, and king studs either side
        for u0, u1, zl, zh in c.openings[wall]:
            for k, (a, bb) in enumerate(((zh, zh + 0.14), (zh + 0.14, zh + 0.28))):
                if z0 + bb < top:
                    trim_box(b, c, wall, u0 - 0.1, u1 + 0.1, z0 + a, z0 + bb, T_SIDING + T_SHEATH, T_SIDING + T_SHEATH + T_STUD, M['lumber'])
            if zl > 0.05:
                trim_box(b, c, wall, u0, u1, z0 + zl - 0.09, z0 + zl, T_SIDING + T_SHEATH, T_SIDING + T_SHEATH + T_STUD, M['lumber'])
            for u in (u0 - 0.1, u1 + 0.04):
                trim_box(b, c, wall, u, u + 0.06, z0 + 0.04, top, T_SIDING + T_SHEATH, T_SIDING + T_SHEATH + T_STUD, M['lumber'])
        # double top plate
        wall_box(b, c, wall, T_SIDING + T_SHEATH, T_SIDING + T_SHEATH + T_STUD, top, top + 0.09, M['lumber'], openings=[])
        wall_box(b, c, wall, T_SIDING + T_SHEATH, T_SIDING + T_SHEATH + T_STUD, top + 0.09, top + 0.18, M['lumber'], openings=[])
    # ceiling joists across the house at 0.6 m, porch posts and beam, then the roof framing
    n = int((d / 2 - c.yh0) / 0.6) + 1
    for k in range(n):
        y = c.yh0 + 0.1 + (d / 2 - c.yh0 - 0.2) * k / max(1, n - 1)
        b.box(-w / 2, w / 2, y - 0.03, y + 0.03, top + 0.18, top + 0.38, M['lumber'])
    porch_posts(b, c, M, top)
    b.box(-w / 2, w / 2, -d / 2 + 0.08, -d / 2 + 0.22, top, top + 0.22, M['lumber'])                  # porch beam
    for x in (-w / 2 + 0.12, w / 2 - 0.12):
        b.box(x - 0.04, x + 0.04, -d / 2 + 0.1, c.yh0, top - 0.1, top, M['lumber'])                  # porch ceiling beams to the house
    rafters(b, c, M)
    gable_studs(b, c, M)


def stud(b, c, wall, u, za, zb, M):
    trim_box(b, c, wall, u - 0.02, u + 0.02, za, zb, T_SIDING + T_SHEATH, T_SIDING + T_SHEATH + T_STUD, M['lumber'])


def gable_studs(b, c, M):
    w = c.w
    for y in (-c.d / 2 + 0.12, c.d / 2 - 0.1):
        for x in (-w * 0.4, -w * 0.25, -w * 0.1, w * 0.1, w * 0.25, w * 0.4):
            zt = c.top + 0.18 + (c.zr - 0.1 - (c.top + 0.18)) * (1 - abs(x) / (w / 2 + 0.05))
            b.box(x - 0.025, x + 0.025, y - 0.035, y + 0.035, c.top + 0.18, zt, M['lumber'])


def walls_stage(b, c, M):
    w, d = c.w, c.d
    framing(b, c, M)
    z0, top = c.z0, c.top
    # sheathing over the studs on all four walls, openings left clear
    for wall in ('front', 'back', 'left', 'right'):
        wall_box(b, c, wall, T_SIDING, T_SIDING + T_SHEATH, z0, top + 0.18, M['osb'], gap_pad=0.0, inset=T_SIDING)
    # sheathed roof deck, in two sheets a side with a gap left at the ridge for the cap
    roof_deck(b, c, M['osb'], 0.04)
    porch_floor(b, c, M)
    # rough window boxes
    for wall in ('front', 'back', 'left', 'right'):
        for u0, u1, zl, zh in c.openings[wall]:
            if zl > 0.05:
                trim_box(b, c, wall, u0, u1, z0 + zl - 0.04, z0 + zl, -0.02, T_SIDING + T_SHEATH, M['lumber'])


def porch_floor(b, c, M):
    deck_boards(b, c, M, c.z0 - 0.035, -c.d / 2, c.yh0)


def roof_deck(b, c, m, thick):
    w, d, ov = c.w, c.d, c.ov
    for side in (-1, 1):
        b.roof_slab(side * (w / 2 + ov), c.top - 0.12 + 0.06 + thick, c.zr + 0.06 + thick, -d / 2 - ov, d / 2 + ov, thick, m)


def complete(b, c, M, glass, finishings=False):
    w, d, h_total = c.w, c.d, c.h_total
    z0, top, ov = c.z0, c.top, c.ov
    # the frame the cladding hangs on (no studs show once it is clad, so a closed shell of sheathing is enough)
    parts = {k: Builder(n) for k, n in (('front', 'Wall_Front'), ('back', 'Wall_Back'), ('left', 'Wall_Left'), ('right', 'Wall_Right'), ('roof', 'Roof'))}
    h = foundation(b, c, M)
    b.box(-w / 2 + 0.02, w / 2 - 0.02, -d / 2 + 0.02, d / 2 - 0.02, h, z0, M['floor'])                       # interior floor / subfloor
    for wall in ('front', 'back', 'left', 'right'):
        wall_box(parts[wall], c, wall, T_SIDING, T_SIDING + T_SHEATH + T_STUD, z0, top + 0.18, M['osb'], inset=T_SIDING)
        # clapboard siding: 0.24 m courses, each lapping the one below
        zc = z0
        k = 0
        while zc < top + 0.18 - 0.02:
            zb = min(zc + 0.24, top + 0.18)
            wall_box(parts[wall], c, wall, 0.0, T_SIDING, zc, zb, M['siding'], gap_pad=0.07, inset=0.0)
            zc = zb
            k += 1
    # the inside: a painted layer on the walls (material Interior), baseboards in the finishing stage; the floor above is material Floor
    ti = T_SIDING + T_SHEATH + T_STUD
    for wall in ('front', 'back', 'left', 'right'):
        wall_box(parts[wall], c, wall, ti, ti + 0.02, z0 + 0.03, top, M['interior'], inset=ti + 0.02)
        if finishings:
            wall_box(parts[wall], c, wall, ti + 0.02, ti + 0.04, z0 + 0.03, z0 + 0.14, M['trim'], inset=ti + 0.04)
    # corner boards
    for (x, y) in ((-w / 2, c.yh0), (w / 2 - 0.08, c.yh0), (-w / 2, d / 2 - 0.08), (w / 2 - 0.08, d / 2 - 0.08)):
        b.box(x, x + 0.08, y, y + 0.08, z0, top + 0.18, M['trim'])
    # window trim, glass, shutters on the front windows
    for wall in ('front', 'back', 'left', 'right'):
        for i, (u0, u1, zl, zh) in enumerate(c.openings[wall]):
            if zl > 0.05:
                window_dressing(parts[wall], c, M, M['glass'], wall, u0, u1, zl, zh, shutters=(wall == 'front'))
    # gable ends, clad: triangles with a vent window on the front
    for y in (-d / 2 + 0.1, d / 2 - 0.04):
        parts['front' if y < 0 else 'back'].prism_gable(-w / 2, w / 2, y, 0.06, top + 0.18, c.zr + 0.02, M['siding'])
    # a small round-ish vent in the front gable
    parts['front'].box(-0.22, 0.22, -d / 2 + 0.05, -d / 2 + 0.08, top + 0.85, top + 1.25, M['trim'])
    glass_builder.box(-0.18, 0.18, -d / 2 + 0.04, -d / 2 + 0.065, top + 0.89, top + 1.21, M['glass'])
    # the roof: deck, shingles in courses, ridge cap, fascia
    roof_deck(parts['roof'], c, M['osb'], 0.035)
    for side in (-1, 1):
        zs = 0.035 + 0.035
        parts['roof'].roof_slab(side * (w / 2 + ov), c.top - 0.12 + 0.06 + zs, c.zr + 0.06 + zs, -d / 2 - ov, d / 2 + ov, 0.035, M['shingle'])
        # shingle course lines: thin darker strips along the slope at intervals
        for k in range(1, 6):
            t = k / 6
            xe = side * (w / 2 + ov) * (1 - t)
            ze = (c.top - 0.12 + 0.06 + zs) + (c.zr + 0.06 + zs - (c.top - 0.12 + 0.06 + zs)) * t
            parts['roof'].box(min(xe, xe + side * 0.02), max(xe, xe + side * 0.02), -d / 2 - ov, d / 2 + ov, ze, ze + 0.045, M['shingle_dark'])
        parts['roof'].box(side * (w / 2 + ov) - 0.035, side * (w / 2 + ov) + 0.035, -d / 2 - ov, d / 2 + ov, c.top - 0.2, c.top - 0.12 + 0.12, M['trim'])      # fascia
    parts['roof'].box(-0.1, 0.1, -d / 2 - ov, d / 2 + ov, c.zr + 0.12, c.zr + 0.2, M['shingle_dark'])                          # ridge cap
    # the porch: deck boards, three posts, railing with balusters (a gap at the steps), a beam, step treads
    deck_boards(b, c, M, z0 - 0.035, -d / 2, c.yh0)
    porch_posts(b, c, M, top)
    b.box(-w / 2, w / 2, -d / 2 + 0.06, -d / 2 + 0.24, top, top + 0.2, M['trim'])
    railing(b, c, M)
    for k in range(3):                                                                                       # tread boards on the concrete steps
        b.box(-0.82, 0.82, -d / 2 - 0.3 * (k + 1), -d / 2 - 0.3 * k, (z0 - 0.04) * (1 - (k + 1) * 0.28), (z0 - 0.04) * (1 - (k + 1) * 0.28) + 0.03, M['deck'])
    # the front door: its own object on a hinge, with panels and a small light
    door(parts['front'], c, M)
    # brick chimney through the roof
    cx, cy = 1.0, d / 2 - 1.6
    b.box(cx - 0.4, cx + 0.4, cy - 0.3, cy + 0.3, z0, c.zr + 0.65, M['brick'])
    b.box(cx - 0.46, cx + 0.46, cy - 0.36, cy + 0.36, c.zr + 0.6, c.zr + 0.72, M['concrete'])
    for k in range(1, 8):                                                                                    # brick course lines
        zz = z0 + 0.1 + k * 0.62
        if zz < c.zr + 0.6:
            b.box(cx - 0.41, cx + 0.41, cy - 0.31, cy + 0.31, zz, zz + 0.025, M['concrete_dark'])
    # a downspout at the front corner
    b.box(w / 2 + 0.0, w / 2 + 0.07, c.yh0 - 0.1, c.yh0 - 0.03, z0, top - 0.1, M['trim'])
    for part in parts.values():
        base.EXTRA_OBJECTS.append(part.finish())   # Wall_* and Roof: the game can hide them (cutaway view)


def railing(b, c, M):
    w, d = c.w, c.d
    rail_y0, rail_y1 = -d / 2 + 0.1, c.yh0
    zb, zt = c.z0, c.z0 + 0.9
    # front: two runs either side of the steps
    for x0, x1 in ((-w / 2 + 0.12, -0.8), (0.8, w / 2 - 0.12)):
        b.box(x0, x1, -d / 2 + 0.05, -d / 2 + 0.11, zt - 0.06, zt, M['trim'])
        b.box(x0, x1, -d / 2 + 0.05, -d / 2 + 0.11, zb + 0.08, zb + 0.14, M['trim'])
        n = int((x1 - x0) / 0.2)
        for k in range(1, n):
            x = x0 + k * (x1 - x0) / n
            b.box(x - 0.018, x + 0.018, -d / 2 + 0.065, -d / 2 + 0.095, zb + 0.14, zt - 0.06, M['trim'])
    for x in (-w / 2 + 0.12, w / 2 - 0.12):                                                                  # the two sides
        b.box(x - 0.03, x + 0.03, rail_y0, rail_y1, zt - 0.06, zt, M['trim'])
        b.box(x - 0.03, x + 0.03, rail_y0, rail_y1, zb + 0.08, zb + 0.14, M['trim'])
        n = int((rail_y1 - rail_y0) / 0.2)
        for k in range(1, n):
            y = rail_y0 + k * (rail_y1 - rail_y0) / n
            b.box(x - 0.015, x + 0.015, y - 0.018, y + 0.018, zb + 0.14, zt - 0.06, M['trim'])


def door(b, c, M):
    dw, dh = DOOR_W - 0.06, DOOR_H - 0.04
    z0 = c.z0
    leaf = Builder('DoorLeaf')
    leaf.box(0.0, dw, -0.04, 0.04, 0.0, dh, M['door'])
    for (x0, x1, z_a, z_b) in ((0.12, dw / 2 - 0.05, 0.15, 1.0), (dw / 2 + 0.05, dw - 0.12, 0.15, 1.0),
                               (0.12, dw / 2 - 0.05, 1.12, 1.95), (dw / 2 + 0.05, dw - 0.12, 1.12, 1.95)):
        leaf.box(x0, x1, -0.055, -0.035, z_a, z_b, M['door_panel'])                                       # raised panels
    leaf.box(dw - 0.16, dw - 0.1, -0.09, 0.09, 1.0, 1.06, M['brass'])                                      # handle through the leaf
    leaf_obj = leaf.finish()
    hinge = bpy.data.objects.new('DoorHinge', None)
    hinge.location = (-dw / 2, c.yh0 + 0.09, z0)
    bpy.context.collection.objects.link(hinge)
    leaf_obj.parent = hinge
    base.EXTRA_OBJECTS.extend([hinge, leaf_obj])
    # frame, transom board and a threshold
    t = 0.07
    trim_box(b, c, 'front', -DOOR_W / 2 - t, -DOOR_W / 2, z0, z0 + DOOR_H + t, -0.05, 0.03, M['trim'])
    trim_box(b, c, 'front', DOOR_W / 2, DOOR_W / 2 + t, z0, z0 + DOOR_H + t, -0.05, 0.03, M['trim'])
    trim_box(b, c, 'front', -DOOR_W / 2 - t, DOOR_W / 2 + t, z0 + DOOR_H, z0 + DOOR_H + t, -0.05, 0.03, M['trim'])
    trim_box(b, c, 'front', -DOOR_W / 2, DOOR_W / 2, z0, z0 + 0.03, -0.02, 0.19, M['concrete'])


# ------------------------------------------------------------------ main

def manifest_for(structure, stage_folder):
    return base.stage_manifest(structure, stage_folder)


def main():
    argv = sys.argv
    structure = argv[argv.index('--') + 1] if '--' in argv else 'starter_house'
    M = {
        'concrete': colour('Concrete', (0.62, 0.62, 0.6), 0.95), 'concrete_dark': colour('ConcreteDark', (0.45, 0.45, 0.44), 0.95),
        'steel': colour('Steel', (0.35, 0.36, 0.38), 0.5), 'lumber': colour('Lumber', (0.78, 0.62, 0.38)),
        'osb': colour('Sheathing', (0.72, 0.56, 0.34), 0.95), 'deck': colour('Deck', (0.62, 0.47, 0.3)),
        'floor': colour('Floor', (0.55, 0.4, 0.26)), 'siding': colour('Siding', (0.84, 0.8, 0.66), 0.8),
        'trim': colour('Trim', (0.93, 0.93, 0.9), 0.7), 'shutter': colour('Shutter', (0.2, 0.3, 0.38), 0.8),
        'shingle': colour('Shingle', (0.24, 0.26, 0.3), 0.9), 'shingle_dark': colour('ShingleDark', (0.16, 0.17, 0.2), 0.9),
        'interior': colour('Interior', (0.93, 0.91, 0.86), 0.9),
        'door': colour('Door', (0.45, 0.13, 0.11), 0.7), 'door_panel': colour('DoorPanel', (0.38, 0.1, 0.09), 0.7),
        'brass': colour('Brass', (0.75, 0.6, 0.25), 0.4), 'brick': colour('Masonry', (0.55, 0.26, 0.2), 0.95),
        'glass': base.glass_material(),
    }
    sizes = {}
    stage_folders = ['struct_foundation', 'struct_framing', 'struct_walls', 'struct_complete']
    if os.path.isdir(os.path.join(STRUCTURES, structure, 'stages', 'struct_finishings')):
        stage_folders.append('struct_finishings')
    for stage_folder in stage_folders:
        folder, manifest_path = manifest_for(structure, stage_folder)
        d = json.load(open(manifest_path, encoding='utf-8'))
        dims = d['category_fields']['dimensions_m']
        w, depth, h = dims['width'], dims['depth'], dims['height']
        found = json.load(open(manifest_for(structure, 'struct_foundation')[1], encoding='utf-8'))['category_fields']['dimensions_m']['height']
        for o in list(bpy.data.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        del base.EXTRA_OBJECTS[:]
        c = Ctx(w, depth, h, found)
        b = Builder(d['id'])
        global glass_builder
        glass_builder = Builder('WindowGlass')
        global FB
        FB = Builder('Foundation')
        if stage_folder == 'struct_foundation':
            foundation(b, c, M)
        elif stage_folder == 'struct_framing':
            framing(b, c, M)
        elif stage_folder == 'struct_walls':
            walls_stage(b, c, M)
        else:
            complete(b, c, M, M['glass'], finishings=(stage_folder == 'struct_finishings'))
            base.EXTRA_OBJECTS.append(glass_builder.finish())
        base.EXTRA_OBJECTS.append(FB.finish())
        FB = None
        obj = b.finish()
        marker = bpy.data.objects.new('FrontMarker', None)
        marker.location = (0.0, -depth / 2 - 0.8, 0.05)
        bpy.context.collection.objects.link(marker)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        marker.select_set(True)
        for extra in base.EXTRA_OBJECTS:
            extra.select_set(True)
        bpy.context.view_layer.objects.active = obj
        out = os.path.join(folder, d['id'] + '.glb')
        bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_yup=True)
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        for extra in base.EXTRA_OBJECTS:
            if getattr(extra, 'data', None) is not None and hasattr(extra.data, 'polygons'):
                tris += sum(len(p.vertices) - 2 for p in extra.data.polygons)
        d['models'] = [{'file': d['id'] + '.glb', 'format': 'glb', 'dimensions_m': {'x': w, 'y': h, 'z': depth}, 'triangles': tris}]
        if stage_folder in ('struct_complete', 'struct_finishings'):
            for ext in ('.fbx', '.obj', '.mtl'):
                legacy = os.path.join(folder, d['id'] + ext)
                if os.path.exists(legacy):
                    os.remove(legacy)
        json.dump(d, open(manifest_path, 'w', encoding='utf-8'), indent=2)
        print('stage', d['id'], tris, 'tris ->', out)


if __name__ == '__main__':
    main()
