"""
The decor pack's house plants (tools/make_decor_assets.py lists and exports them). Each function takes a Pot (style + pot colour) and returns a Mesh.

Metres. FLOOR pieces: centred on x and y, bottom at z = 0. The hanging basket is a CEILING piece: z = 0 is its lowest point, its height is where it touches the ceiling. FRONT = -Y.
Leaves are thin extruded outlines (a pointed ellipse, a heart) turned to a yaw and a pitch; tools/decor_models.py has the curtains.
"""
import math
import random

import bmesh
from mathutils import Matrix, Vector

from kitchen_lib import Mesh, material

from decor_colors import POT_RGB  # noqa: E402


class Pot:
    def __init__(self, style, key):
        self.style, self.key = style, key
        self.classic = style == 'classic'
        rgb = POT_RGB[style][key]
        self.pot = material('Pot_%s_%s' % (style, key), rgb, 0.62 if self.classic else 0.5, 0.0)
        self.base = material('PotBase_%s' % style, tuple(c * 0.55 for c in rgb), 0.6, 0.0)
        self.soil = material('Soil', (0.17, 0.12, 0.08), 0.98)
        self.leaf = material('LeafGreen', (0.13, 0.36, 0.14), 0.55)
        self.leaf2 = material('LeafDeep', (0.08, 0.26, 0.11), 0.55)
        self.leaf3 = material('LeafLight', (0.30, 0.52, 0.20), 0.55)
        self.stem = material('PlantStem', (0.30, 0.22, 0.12), 0.8)
        self.chain = material('PlantChain', (0.18, 0.18, 0.19), 0.45, 1.0)


def leaf(K, m, base, length, width, yaw, pitch, roll=0.0, shape=None, thick=0.004, n=6):
    """A leaf: an outline in the x (length) and y (width) plane, extruded `thick`, then raised by `pitch` (degrees above the horizontal) and turned `yaw` about the vertical at `base`."""
    before = set(K.bm.verts)
    if shape is None:
        up = [(length * i / n, width * 0.5 * math.sin(math.pi * i / n) ** 0.75) for i in range(1, n)]
        pts = up + [(length, 0.0)] + [(x, -y) for x, y in reversed(up)] + [(0.0, 0.0)]
    else:
        pts = [(u * length, v * width * 0.5) for u, v in shape]
    K.prism(pts, 0.0, thick, m)
    mx = Matrix.Translation(base) @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Rotation(math.radians(-pitch), 4, 'Y') @ Matrix.Rotation(math.radians(roll), 4, 'X')
    new = [v for v in K.bm.verts if v not in before]
    bmesh.ops.transform(K.bm, matrix=mx, verts=new)


HEART = [(0.0, 0.0), (0.08, 0.35), (0.22, 0.62), (0.40, 0.50), (0.46, 0.64), (0.62, 0.48), (0.70, 0.52), (0.84, 0.30), (1.0, 0.0),
         (0.84, -0.30), (0.70, -0.52), (0.62, -0.48), (0.46, -0.64), (0.40, -0.50), (0.22, -0.62), (0.08, -0.35)]


def pot(K, P, R, h, saucer=True):
    """The pot: classic is a tapered, rimmed pot on a saucer, modern a plain drum on a low plinth. Returns the height of the soil."""
    z0 = 0.0
    if saucer:
        K.lathe([(0.0, 0.0), (R * 0.78, 0.0), (R * 1.04, 0.014), (R * 1.08, 0.026)], P.base, seg=24)
        z0 = 0.022
    if P.classic:
        K.lathe([(0.0, 0.0), (R * 0.62, 0.0), (R * 0.70, 0.03), (R * 0.93, h * 0.86), (R * 1.0, h * 0.88), (R * 1.0, h), (R * 0.93, h), (R * 0.9, h - 0.012)], P.pot, at=(0, 0, z0), seg=24, hard=(4,))
    else:
        K.lathe([(0.0, 0.0), (R * 0.9, 0.0), (R * 0.96, 0.012), (R * 0.97, h * 0.18), (R, h * 0.2), (R, h), (R * 0.94, h), (R * 0.9, h - 0.012)], P.pot, at=(0, 0, z0), seg=24, hard=(4,))
    K.cyl((0, 0, z0 + h - 0.034), (0, 0, z0 + h - 0.014), R * 0.88, P.soil, seg=20)
    return z0 + h - 0.014


def fig(P):
    """A fiddle-leaf fig: a bare trunk with a crown of big violin-shaped leaves, 0.4 x 0.4 x 1.6 m."""
    K = Mesh('decor_plant_fig')
    R = 0.17
    z = pot(K, P, R, 0.30)
    K.cyl((0, 0, z), (0.01, 0.01, 1.05), 0.016, P.stem, seg=8, r1=0.011)
    rnd = random.Random(4)
    for i in range(18):
        t = i / 17
        zz = 0.68 + t * 0.86
        size = 0.30 - 0.06 * t + rnd.uniform(-0.02, 0.02)
        yaw = i * 137.5
        r = 0.02 + 0.02 * (1 - t)
        leaf(K, P.leaf if i % 3 else P.leaf2, (r * math.cos(math.radians(yaw)), r * math.sin(math.radians(yaw)), zz), size, size * 0.62, yaw, 28 + 18 * t + rnd.uniform(-6, 6), roll=rnd.uniform(-10, 10), n=7)
    return K


def palm(P):
    """A parlor palm: arching fronds with paired leaflets round the base, 0.5 x 0.5 x 1.4 m."""
    K = Mesh('decor_plant_palm')
    R = 0.19
    z = pot(K, P, R, 0.30)
    rnd = random.Random(7)
    for f in range(8):
        yaw = f * 45 + rnd.uniform(-8, 8)
        ln = 0.95 + 0.25 * (f % 3) / 2
        ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        pts = []
        for k in range(6):                                     # the frond's arch: up, then out and over
            t = k / 5
            r = 0.04 + t * ln * 0.26
            pts.append((ca * r, sa * r, z + 0.02 + ln * 0.78 * math.sin(t * 1.9) * (1 - 0.25 * t)))
        for a, b in zip(pts, pts[1:]):
            K.cyl(a, b, 0.006, P.stem, seg=6)
        for k in range(1, 6):
            px, py, pz = pts[k]
            for s in (-1, 1):
                leaf(K, P.leaf if f % 2 else P.leaf2, (px, py, pz), 0.20 - 0.015 * k, 0.045, yaw + s * 62, 28 + 5 * k, n=3, thick=0.003)
        leaf(K, P.leaf3, pts[-1], 0.16, 0.04, yaw, -6, n=3, thick=0.003)
    return K


def snake(P):
    """A snake plant: stiff upright blades, 0.30 x 0.30 x 0.85 m."""
    K = Mesh('decor_plant_snake')
    R = 0.12
    z = pot(K, P, R, 0.22)
    rnd = random.Random(11)
    for i in range(11):
        yaw = i * 137.5
        d = 0.015 + 0.04 * (i % 4) / 3
        ln = 0.42 + 0.34 * ((i * 5) % 7) / 6
        leaf(K, P.leaf2 if i % 2 else P.leaf, (d * math.cos(math.radians(yaw)), d * math.sin(math.radians(yaw)), z), ln, 0.065, yaw, 80 + rnd.uniform(-6, 6), thick=0.012, n=6)
    return K


def monstera(P):
    """A monstera: a few stems with big split heart leaves, 0.5 x 0.5 x 1.1 m."""
    K = Mesh('decor_plant_monstera')
    R = 0.17
    z = pot(K, P, R, 0.28)
    rnd = random.Random(5)
    for i in range(7):
        yaw = i * 137.5
        ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        top = 0.45 + 0.5 * (i / 6)
        reach = 0.04 + 0.08 * ((i * 3) % 7) / 6
        K.cyl((0.01 * ca, 0.01 * sa, z), (reach * ca, reach * sa, z + top), 0.008, P.stem, seg=6)
        leaf(K, P.leaf if i % 2 else P.leaf2, (reach * ca, reach * sa, z + top), 0.30 - 0.02 * (i % 3), 0.28, yaw + rnd.uniform(-20, 20), 22 + rnd.uniform(-8, 12), roll=rnd.uniform(-15, 15), shape=HEART, thick=0.005)
    return K


def succulent(P):
    """A small succulent in a pot for a shelf or a table: a rosette of thick leaves, 0.14 x 0.14 x 0.2 m."""
    K = Mesh('decor_plant_succulent')
    R = 0.055
    z = pot(K, P, R, 0.085)
    for ring, (cnt, pit, ln, off) in enumerate(((10, 28, 0.075, 0.0), (7, 52, 0.06, 20.0), (5, 74, 0.045, 10.0))):
        for i in range(cnt):
            yaw = i * 360.0 / cnt + off
            leaf(K, P.leaf3 if ring == 1 else P.leaf, (0.0, 0.0, z + 0.004 + 0.012 * ring), ln, 0.034, yaw, pit, thick=0.012, n=4)
    return K


def hanging_fern(P):
    """A hanging basket of fern: a bowl on three chains from a ceiling hook, fronds drooping all round. 0.5 x 0.5 x 1.0 m, hung from the top (z = 0 is the lowest frond)."""
    K = Mesh('decor_plant_fern')
    top = 1.0
    bowl_z = 0.36
    R = 0.14
    K.lathe([(0.0, 0.0), (R * 0.5, 0.0), (R * 0.85, 0.05), (R, 0.13), (R, 0.16), (R * 0.93, 0.16), (R * 0.9, 0.145)], P.pot, at=(0, 0, bowl_z), seg=20, hard=(4,))
    K.cyl((0, 0, bowl_z + 0.12), (0, 0, bowl_z + 0.145), R * 0.88, P.soil, seg=18)
    for k in range(3):
        a = math.radians(k * 120 + 30)
        K.cyl((R * 0.98 * math.cos(a), R * 0.98 * math.sin(a), bowl_z + 0.15), (0, 0, top - 0.05), 0.0035, P.chain, seg=5)
    K.cyl((0, 0, top - 0.06), (0, 0, top), 0.012, P.chain, seg=8)
    K.lathe([(0.0, 0.0), (0.04, 0.0), (0.045, 0.012), (0.0, 0.02)], P.chain, at=(0, 0, top - 0.02), seg=10)
    rnd = random.Random(2)
    for i in range(22):
        yaw = i * 360 / 22 + rnd.uniform(-6, 6)
        ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        ln = 0.30 + rnd.uniform(0.0, 0.12)
        p0 = (0.07 * ca, 0.07 * sa, bowl_z + 0.15)
        pts = [p0]
        for k in range(1, 4):                                   # up and out, then over and down
            t = k / 3
            pts.append(((0.07 + 0.24 * t) * ca, (0.07 + 0.24 * t) * sa, bowl_z + 0.15 + 0.10 * math.sin(t * 2.4) - 0.33 * t * t * ln / 0.3))
        for a, b in zip(pts, pts[1:]):
            K.cyl(a, b, 0.004, P.stem, seg=5)
        for k in range(1, 4):
            px, py, pz = pts[k]
            for s in (-1, 1):
                leaf(K, P.leaf if i % 2 else P.leaf3, (px, py, pz), 0.11, 0.032, yaw + s * 78, -22 - 8 * k, n=3, thick=0.003)
    return K
