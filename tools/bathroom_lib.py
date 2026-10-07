"""
The bathroom pack's palette and shared parts (tools/bathroom_models.py builds the pieces, tools/make_bathroom_assets.py lists and exports them). Builds on the living pack's
palette (fabric, rug and wood textures) and the kitchen modelling kit.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitchen_lib as K  # noqa: E402
import living_lib as LL  # noqa: E402
from bathroom_colors import METALS, PORCELAIN, colors  # noqa: E402,F401


class BathPalette(LL.Palette):
    """`main` is the colour that varies: glaze (porcelain), a metal finish, fabric or wood. The trim, the stone top, the basin and the tile are fixed by style."""

    def _main(self, kind, key):
        if kind == 'porcelain':
            rgb = [c for k, _, c in PORCELAIN[self.style] if k == key][0]
            return K.material('Glaze_%s_%s' % (self.style, key), rgb, 0.16)
        if kind == 'metal':
            row = [r for r in METALS[self.style] if r[0] == key][0]
            return K.material('BathMetal_%s_%s' % (self.style, key), row[2], row[3], row[4])
        return LL.Palette._main(self, kind, key)

    def __init__(self, style, kind, key):
        LL.Palette.__init__(self, style, kind, key)
        mat = K.material
        self.trim = mat('BathChrome', (0.82, 0.83, 0.85), 0.14, 1.0) if self.classic else mat('BathNickel', (0.62, 0.63, 0.64), 0.34, 1.0)
        self.basin = mat('BasinWhite', (0.95, 0.95, 0.93), 0.14)
        self.stone = mat('VanityMarble', (0.88, 0.88, 0.86), 0.22) if self.classic else mat('VanityQuartz', (0.74, 0.74, 0.75), 0.25)
        self.tile = mat('BathTile', (0.90, 0.92, 0.93), 0.18)
        self.water = mat('DrainDark', (0.10, 0.11, 0.12), 0.5)
        self.towel = mat('TowelWhite', (0.93, 0.92, 0.88), 0.95)
        self.wicker = mat('Wicker', (0.66, 0.50, 0.30), 0.85)
        self.mirror = mat('MirrorGlass', (0.85, 0.88, 0.90), 0.02, 1.0)


def outline(x0, x1, y0, y1, r, seg=4):
    """A rounded rectangle in plan, counter-clockwise (the same points K.Mesh.rbox uses)."""
    pts = []
    r = min(r, 0.499 * min(x1 - x0, y1 - y0))
    for cx, cy, a0 in ((x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180), (x1 - r, y0 + r, 270)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90.0 * k / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def vessel(M, x0, x1, y0, y1, r, t, ztop, zfloor, zbot, m, seg=4):
    """An open tub, basin or tray: walls of thickness t from zbot to ztop round a hollow with its floor at zfloor (a rounded rectangle in plan, outer radius r)."""
    bm = M.bm
    before = set(bm.faces)
    O = outline(x0, x1, y0, y1, r, seg)
    I = outline(x0 + t, x1 - t, y0 + t, y1 - t, max(r - t, 0.01), seg)
    n = len(O)
    ot = [bm.verts.new((x, y, ztop)) for x, y in O]
    ob = [bm.verts.new((x, y, zbot)) for x, y in O]
    it = [bm.verts.new((x, y, ztop)) for x, y in I]
    fl = [bm.verts.new((x, y, zfloor)) for x, y in I]
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((ot[k], ot[j], it[j], it[k]))
        bm.faces.new((ob[k], ob[j], ot[j], ot[k]))
        bm.faces.new((it[k], it[j], fl[j], fl[k]))
    bm.faces.new(fl)
    bm.faces.new(ob[::-1])
    M._finish_faces(M._new_faces(before), m, False, 1.0)


def faucet(M, P, x, y, z, reach=0.14, height=0.12, classic=None, handles=True, spread=0.10, facing=-1):
    """A basin faucet standing on a deck at (x, y, z): a spout reaching `facing` (-1 = towards -y, the front) and two cross handles (classic) or one lever (modern)."""
    classic = P.classic if classic is None else classic
    m = P.trim
    M.cyl((x, y, z), (x, y, z + 0.02), 0.026, m, seg=12)
    pts = [(x, y, z + 0.02), (x, y, z + height), (x, y + facing * reach * 0.5, z + height + 0.02), (x, y + facing * reach, z + height - 0.01), (x, y + facing * reach, z + height - 0.045)]
    for a, b in zip(pts, pts[1:]):
        M.cyl(a, b, 0.0095, m, seg=8)
    if classic and handles:
        for sx in (-1, 1):
            hx = x + sx * spread
            M.cyl((hx, y, z), (hx, y, z + 0.06), 0.014, m, seg=8, r1=0.022)
            M.box(hx - 0.032, hx + 0.032, y - 0.007, y + 0.007, z + 0.055, z + 0.067, m)
            M.box(hx - 0.007, hx + 0.007, y - 0.032, y + 0.032, z + 0.055, z + 0.067, m)
    else:
        M.cyl((x + 0.02, y, z + 0.06), (x + 0.075, y, z + 0.075), 0.007, m, seg=6)
