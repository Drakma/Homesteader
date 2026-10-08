"""
The decor pack's models (tools/make_decor_assets.py lists and exports them). Each function takes a Deco (style + fabric colour) and returns a Mesh.

Metres. WALL pieces: the back is the plane y = 0, they stick out to -y, z = 0 is the bottom (a curtain's hem; a drape's floor), centred on x. FRONT = -Y.
Curtains hang from a rod on brackets, in two panels open at the sides with the window between them; drapes are floor-length, tied back, with a valance (classic) or a ceiling track (modern).
"""
import math

from kitchen_lib import Mesh, material

BRASS = (0.70, 0.52, 0.22)
BLACK = (0.05, 0.05, 0.055)


class Deco:
    def __init__(self, style, key, rgb):
        self.style, self.key, self.rgb = style, key, rgb
        self.classic = style == 'classic'
        self.cloth = material('Cloth_%s_%s' % (style, key), rgb, 0.96, 0.0)
        dark = tuple(c * 0.72 for c in rgb)
        self.trim = material('ClothTrim_%s_%s' % (style, key), dark, 0.96, 0.0)
        self.metal = material('Rod_%s' % style, BRASS if self.classic else BLACK, 0.34 if self.classic else 0.55, 1.0 if self.classic else 0.4)


def panel(K, D, xa, xb, z0, z1, amp, period, base=0.075, th=0.012, per=4, m=None, ph=0.0):
    """One hanging panel of cloth between x = xa and xb, z0..z1: a wavy sheet (the folds), `per` points to each fold."""
    m = m or D.cloth
    folds = max(1.0, (xb - xa) / period)
    n = max(per, int(round(folds * per)))
    front = []
    for i in range(n + 1):
        x = xa + (xb - xa) * i / n
        s = 0.5 - 0.5 * math.cos(2 * math.pi * i * folds / n + ph)           # 0 at the back of a fold, 1 at the front
        front.append((x, -(base - amp / 2 + amp * s)))
    pts = front + [(x, y + th) for x, y in reversed(front)]
    K.prism(pts, z0, z1, m)


def rod(K, D, half, z, y=-0.08, finial=True, rings=None):
    """A curtain rod from -half to +half at height z, on a bracket at each end (and one in the middle on a long rod), with finials (classic) or end caps (modern)."""
    r = 0.011 if D.classic else 0.008
    K.cyl((-half, y, z), (half, y, z), r, D.metal, seg=10)
    brackets = [-half + 0.03, half - 0.03] + ([0.0] if half > 0.7 else [])
    for x in brackets:
        K.cyl((x, 0.0, z), (x, y, z), 0.008, D.metal, seg=8)
        K.cyl((x, -0.002, z), (x, 0.004, z), 0.022, D.metal, seg=10)
    if finial:
        for s in (-1, 1):
            if D.classic:
                K.lathe([(0.0, -0.032), (0.018, -0.024), (0.028, -0.004), (0.026, 0.014), (0.012, 0.03), (0.0, 0.034)], D.metal, at=(s * (half + 0.028), y, z), seg=10)
            else:
                K.cyl((s * half, y, z), (s * (half + 0.03), y, z), 0.016, D.metal, seg=12)
    if rings:
        for x in rings:
            K.cyl((x - 0.005, y, z), (x + 0.005, y, z), 0.021, D.metal, seg=10)


def curtains(D):
    """Window curtains: a pair of sill-length panels on a rod, open at the sides. 1.8 m wide, 1.6 m high."""
    K = Mesh('decor_curtains')
    H, zr = 1.6, 1.57
    half = 0.86
    amp, period = (0.032, 0.10) if D.classic else (0.016, 0.15)
    for s in (-1, 1):
        xa, xb = (0.34, 0.84) if s > 0 else (-0.84, -0.34)
        panel(K, D, xa, xb, 0.0, zr - 0.006, amp, period, ph=0.0 if s > 0 else math.pi)
        # a band along the hem and a header at the top, in the darker cloth
        panel(K, D, xa, xb, 0.0, 0.07, amp, period, base=0.0755, th=0.013, m=D.trim, ph=0.0 if s > 0 else math.pi)
        panel(K, D, xa, xb, zr - 0.09, zr - 0.006, amp, period, base=0.0755, th=0.013, m=D.trim if D.classic else D.cloth, ph=0.0 if s > 0 else math.pi)
    rings = [x for x in (-0.80, -0.70, -0.60, -0.50, -0.40, 0.40, 0.50, 0.60, 0.70, 0.80)] if D.classic else None
    rod(K, D, half, zr, rings=rings)
    return K


def drapes(D):
    """Floor-length drapes: a pair of heavy lined panels, tied back at the sides, with a valance (classic) or a ceiling track (modern). 2.3 m wide, 2.5 m high."""
    K = Mesh('decor_drapes')
    H, zr = 2.5, 2.4
    half = 1.06
    amp, period = (0.04, 0.12) if D.classic else (0.02, 0.18)
    tie = 0.95
    for s in (-1, 1):
        xa, xb = (0.30, 1.04) if s > 0 else (-1.04, -0.30)
        ph = 0.0 if s > 0 else math.pi
        outer0, outer1 = (0.66, 1.04) if s > 0 else (-1.04, -0.66)        # where the tie-back gathers the cloth in, at the outer side
        panel(K, D, xa, xb, tie + 0.05, zr - 0.006, amp, period, ph=ph)                 # above the tie
        panel(K, D, outer0, outer1, tie - 0.03, tie + 0.05, amp * 0.5, period, base=0.075, ph=ph)   # gathered at the tie
        panel(K, D, xa - (0.03 if s > 0 else -0.03), xb, 0.0, tie - 0.03, amp * 1.25, period, base=0.082, ph=ph)   # below it, a little fuller
        # the puddle at the floor
        panel(K, D, xa - 0.04 if s > 0 else xa - 0.05, xb + 0.05 if s > 0 else xb + 0.04, 0.0, 0.1, amp * 1.6, period, base=0.09, th=0.014, m=D.trim, ph=ph)
        # the tie-back: a cord round the gathered cloth and a hook on the wall
        cx0, cx1 = outer0 - 0.02, outer1 + 0.02
        K.box(cx0, cx1, -0.118, -0.034, tie - 0.012, tie + 0.012, D.trim if D.classic else D.metal)
        K.cyl((s * 1.12, 0.0, tie), (s * 1.12, -0.05, tie), 0.012, D.metal, seg=8)
    if D.classic:
        rod(K, D, half, zr, rings=[-0.95, -0.80, -0.65, -0.50, -0.35, 0.35, 0.50, 0.65, 0.80, 0.95])
        # the valance across the top
        K.box(-1.0, 1.0, -0.12, -0.03, zr - 0.17, zr + 0.095, D.trim)
        for i in range(-4, 5):
            K.box(i * 0.222 - 0.1, i * 0.222 + 0.1, -0.128, -0.12, zr - 0.2, zr + 0.06, D.cloth)
    else:
        K.box(-half, half, -0.075, 0.0, zr + 0.04, zr + 0.095, D.metal)                  # a ceiling track
        for x in [i * 0.12 for i in range(-8, 9)]:
            K.cyl((x, -0.04, zr + 0.04), (x, -0.04, zr + 0.0), 0.004, D.metal, seg=6)
    return K
