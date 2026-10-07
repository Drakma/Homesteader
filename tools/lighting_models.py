"""
The lighting pack's models (tools/make_lighting_assets.py lists and exports them). Each function takes a Lamp (style + metal finish) and returns a Mesh.

Metres. CEILING pieces: z = 0 is the lowest point, the top (touching the ceiling) is the height. WALL pieces: the back is the plane y = 0, they stick out to -y, z = 0 is the bottom.
GROUND pieces (posts, bollards): centred on x and y, bottom at z = 0. FRONT = -Y.
Light positions live in the manifest (tools/make_lighting_assets.py LIGHT_AT), in the same frames.
"""
import math

from kitchen_lib import Mesh, material

# style -> [(key, label, rgb, rough, metal)]
FINISHES = {
    'classic': [('brass', 'Antique Brass', (0.70, 0.52, 0.22), 0.34, 1.0), ('bronze', 'Oiled Bronze', (0.20, 0.13, 0.08), 0.42, 0.8),
                ('black', 'Black Iron', (0.04, 0.04, 0.045), 0.45, 0.6), ('white', 'White', (0.93, 0.93, 0.90), 0.40, 0.0)],
    'modern': [('chrome', 'Chrome', (0.82, 0.83, 0.85), 0.14, 1.0), ('black', 'Matte Black', (0.05, 0.05, 0.055), 0.62, 0.3),
               ('nickel', 'Brushed Nickel', (0.62, 0.63, 0.64), 0.36, 1.0), ('white', 'White', (0.94, 0.94, 0.94), 0.50, 0.0)],
}


class Lamp:
    def __init__(self, style, key):
        self.style, self.key = style, key
        self.classic = style == 'classic'
        row = [r for r in FINISHES[style] if r[0] == key][0]
        self.metal = material('Fix_%s_%s' % (style, key), row[2], row[3], row[4])
        self.dark = material('LampDark', (0.05, 0.05, 0.055), 0.5)
        self.glass = material('FrostedGlass', (0.96, 0.93, 0.82), 0.30)
        self.clear = material('AmberGlass', (0.92, 0.84, 0.58), 0.12)
        self.bulb = material('BulbWarm', (1.0, 0.93, 0.70), 0.2)
        self.blade = material('FanBlade', (0.36, 0.23, 0.13) if self.classic else row[2], 0.55, 0.0)


def line(K, pts, r, m, seg=8):
    for a, b in zip(pts, pts[1:]):
        K.cyl(a, b, r, m, seg=seg)


def arc(cx, cz, rad, a0, a1, n, y=0.0):
    return [(cx + rad * math.cos(math.radians(a0 + (a1 - a0) * k / n)), y, cz + rad * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


def bulb(K, L, p, r=0.03):
    K.lathe([(0.0, -r), (r * 0.9, -r * 0.4), (r, 0.0), (r * 0.8, r * 0.8), (r * 0.4, r * 1.3), (0.0, r * 1.5)], L.bulb, at=p, seg=10)


def canopy(K, L, z_top, r=0.08, h=0.025):
    K.cyl((0, 0, z_top - h), (0, 0, z_top), r, L.metal, seg=20)


# ------------------------------------------------------------------ ceiling

def ceiling_flush(L):
    """A flush-mount ceiling light: a glass bowl (classic) or a slim drum (modern), 0.40 x 0.40 m."""
    K = Mesh('lighting_ceiling_flush')
    if L.classic:
        h = 0.17
        K.lathe([(0.0, 0.0), (0.09, 0.008), (0.16, 0.04), (0.19, 0.09), (0.195, 0.15)], L.glass, at=(0, 0, 0), seg=28, hard=(4,))
        K.cyl((0, 0, h - 0.02), (0, 0, h), 0.205, L.metal, seg=28)
        K.cyl((0, 0, 0.0), (0, 0, 0.012), 0.025, L.metal, seg=10, r1=0.012)
        for k in range(3):
            a = math.radians(120 * k + 30)
            K.cyl((0.19 * math.cos(a), 0.19 * math.sin(a), 0.12), (0.19 * math.cos(a), 0.19 * math.sin(a), 0.16), 0.012, L.metal, seg=6)
    else:
        h = 0.07
        K.cyl((0, 0, 0.0), (0, 0, h - 0.015), 0.20, L.glass, seg=36)
        K.cyl((0, 0, h - 0.015), (0, 0, h), 0.205, L.metal, seg=36)
    return K


def ceiling_pendant(L):
    """A pendant light on a cord: a metal bell shade (classic) or a glass globe (modern), 0.38 x 0.38 x 0.95 m."""
    K = Mesh('lighting_ceiling_pendant')
    if L.classic:
        h = 0.95
        K.lathe([(0.03, 0.0), (0.12, 0.0), (0.185, 0.045), (0.19, 0.06), (0.17, 0.12), (0.10, 0.19), (0.04, 0.23), (0.02, 0.26)], L.metal, at=(0, 0, 0.02), seg=26, hard=(2,), smooth=True)
        K.lathe([(0.0, 0.0), (0.12, 0.0), (0.17, 0.045)], L.glass, at=(0, 0, 0.012), seg=26)
        bulb(K, L, (0, 0, 0.05), 0.04)
        K.cyl((0, 0, 0.26), (0, 0, h - 0.02), 0.008, L.dark, seg=6)
    else:
        h = 0.95
        K.lathe([(0.0, 0.0), (0.07, 0.008), (0.13, 0.04), (0.17, 0.10), (0.18, 0.18), (0.16, 0.27), (0.10, 0.33), (0.04, 0.36), (0.0, 0.365)], L.glass, at=(0, 0, 0.0), seg=28)
        K.cyl((0, 0, 0.36), (0, 0, 0.40), 0.03, L.metal, seg=10)
        K.cyl((0, 0, 0.40), (0, 0, h - 0.02), 0.006, L.dark, seg=6)
    canopy(K, L, h)
    return K


def chandelier(L):
    """A chandelier: candle arms round a column (classic) or a sputnik of rods and bulbs (modern)."""
    K = Mesh('lighting_chandelier')
    if L.classic:
        h = 0.95
        K.lathe([(0.0, 0.0), (0.03, 0.01), (0.07, 0.06), (0.05, 0.11), (0.035, 0.16), (0.06, 0.22), (0.03, 0.30), (0.02, 0.34)], L.metal, at=(0, 0, 0.0), seg=14, hard=(2,))
        K.cyl((0, 0, 0.34), (0, 0, h - 0.02), 0.012, L.metal, seg=8)
        for k in range(6):
            a = math.radians(60 * k)
            c, s = math.cos(a), math.sin(a)
            # a scrolled arm: out from the column, curling up to a cup
            pts = [(0.04 * c, 0.04 * s, 0.20)] + [((0.04 + 0.30 * t) * c, (0.04 + 0.30 * t) * s, 0.20 - 0.07 * math.sin(math.pi * t) + 0.09 * t * t) for t in (0.25, 0.5, 0.75, 1.0)]
            line(K, [(x, y, z) for x, y, z in pts], 0.010, L.metal)
            ex, ey, ez = pts[-1]
            K.cyl((ex, ey, ez), (ex, ey, ez + 0.03), 0.026, L.metal, seg=10, r1=0.018)
            K.cyl((ex, ey, ez + 0.03), (ex, ey, ez + 0.14), 0.013, L.glass, seg=8)
            bulb(K, L, (ex, ey, ez + 0.14), 0.014)
        K.cyl((0, 0, 0.60), (0, 0, 0.62), 0.04, L.metal, seg=10)
    else:
        h = 0.70
        K.lathe([(0.0, 0.0), (0.06, 0.02), (0.08, 0.06), (0.06, 0.10), (0.0, 0.12)], L.metal, at=(0, 0, 0.14), seg=14)
        K.cyl((0, 0, 0.26), (0, 0, h - 0.02), 0.008, L.metal, seg=6)
        for k in range(10):
            a = math.radians(36 * k)
            c, s = math.cos(a), math.sin(a)
            tilt = 0.45 + 0.35 * (k % 2)
            ex, ey, ez = 0.36 * c, 0.36 * s, 0.20 + 0.23 * tilt
            K.cyl((0.0, 0.0, 0.20), (ex, ey, ez), 0.006, L.metal, seg=5)
            K.lathe([(0.0, -0.035), (0.03, -0.02), (0.04, 0.0), (0.03, 0.03), (0.0, 0.05)], L.glass, at=(ex, ey, ez), seg=10)
    canopy(K, L, h)
    return K


def ceiling_fan(L):
    """A ceiling fan with five blades and a light kit, 1.20 m across, 0.42 m high."""
    K = Mesh('lighting_ceiling_fan')
    h = 0.42
    # the light kit (a glass bowl) hangs lowest
    if L.classic:
        K.lathe([(0.0, 0.0), (0.05, 0.004), (0.095, 0.03), (0.105, 0.07), (0.07, 0.10)], L.glass, at=(0, 0, 0.0), seg=20)
        K.cyl((0, 0, 0.10), (0, 0, 0.12), 0.075, L.metal, seg=16)
    else:
        K.cyl((0, 0, 0.0), (0, 0, 0.06), 0.09, L.glass, seg=20)
        K.cyl((0, 0, 0.06), (0, 0, 0.075), 0.095, L.metal, seg=20)
    K.lathe([(0.0, 0.0), (0.09, 0.0), (0.14, 0.03), (0.14, 0.07), (0.10, 0.10), (0.0, 0.10)], L.metal, at=(0, 0, 0.13), seg=22, hard=(1, 3))        # the motor housing
    K.cyl((0, 0, 0.23), (0, 0, h - 0.04), 0.014, L.metal, seg=8)
    canopy(K, L, h, r=0.07, h=0.04)
    for k in range(5):
        a = math.radians(72 * k)
        c, s = math.cos(a), math.sin(a)
        bx0, bx1 = 0.15, 0.60
        z = 0.15
        # the blade: a slim slab, a little narrower at the hub, tilted
        pts = [(bx0 * c - 0.035 * s, bx0 * s + 0.035 * c), (bx1 * c - 0.065 * s, bx1 * s + 0.065 * c), (bx1 * c + 0.065 * s, bx1 * s - 0.065 * c), (bx0 * c + 0.035 * s, bx0 * s - 0.035 * c)]
        K.prism(pts, z, z + 0.012, L.blade)
        K.cyl((0.10 * c, 0.10 * s, z + 0.03), (0.17 * c, 0.17 * s, z + 0.006), 0.010, L.metal, seg=6)
    return K


def track_light(L):
    """A track with three adjustable spot heads, 1.00 m long."""
    K = Mesh('lighting_track_light')
    h = 0.24
    K.box(-0.50, 0.50, -0.02, 0.02, h - 0.03, h, L.metal)
    for x in (-0.34, 0.0, 0.34):
        K.cyl((x, 0, h - 0.03), (x, 0, h - 0.07), 0.012, L.metal, seg=8)
        K.cyl((x, 0, h - 0.07), (x, -0.025, h - 0.11), 0.01, L.metal, seg=8)
        # the can tilted forward
        K.cyl((x, -0.01, h - 0.11), (x, -0.07, h - 0.215), 0.04, L.metal, seg=14, r1=0.052)
        K.cyl((x, -0.071, h - 0.216), (x, -0.075, h - 0.224), 0.044, L.glass, seg=14)
    return K


# ------------------------------------------------------------------ wall (interior)

def wall_sconce(L):
    """A wall sconce: a glass tulip on a scrolled arm (classic) or an up-and-down cylinder (modern)."""
    K = Mesh('lighting_wall_sconce')
    if L.classic:
        K.box(-0.045, 0.045, -0.014, 0.0, 0.02, 0.24, L.metal, r=0.004, seg=1)
        line(K, [(0, -0.014, 0.10), (0, -0.07, 0.11), (0, -0.12, 0.14), (0, -0.13, 0.17)], 0.011, L.metal)
        K.cyl((0, -0.13, 0.15), (0, -0.13, 0.18), 0.04, L.metal, seg=12, r1=0.026)
        K.lathe([(0.0, 0.0), (0.03, 0.0), (0.05, 0.05), (0.07, 0.13), (0.075, 0.17)], L.glass, at=(0, -0.13, 0.18), seg=16, hard=(0,))
        bulb(K, L, (0, -0.13, 0.19), 0.02)
    else:
        K.box(-0.05, 0.05, -0.012, 0.0, 0.06, 0.34, L.metal, r=0.003, seg=1)
        K.cyl((0, -0.012, 0.20), (0, -0.07, 0.20), 0.012, L.metal, seg=8)
        K.cyl((0, -0.13, 0.04), (0, -0.13, 0.36), 0.055, L.metal, seg=24)
        K.cyl((0, -0.13, 0.12), (0, -0.13, 0.28), 0.057, L.glass, seg=24)
    return K


def vanity_bar(L):
    """A three-light vanity bar over a mirror, 0.62 m wide."""
    K = Mesh('lighting_vanity_bar')
    K.box(-0.31, 0.31, -0.012, 0.0, 0.03, 0.07, L.metal, r=0.003, seg=1)
    for x in (-0.20, 0.0, 0.20):
        if L.classic:
            K.cyl((x, -0.012, 0.05), (x, -0.07, 0.05), 0.008, L.metal, seg=6)
            K.lathe([(0.0, -0.06), (0.05, -0.04), (0.07, 0.0), (0.05, 0.05), (0.03, 0.075), (0.0, 0.08)], L.glass, at=(x, -0.12, 0.07), seg=14)
            bulb(K, L, (x, -0.12, 0.06), 0.02)
        else:
            K.cyl((x, -0.012, 0.05), (x, -0.045, 0.05), 0.012, L.metal, seg=8, r1=0.02)
            K.cyl((x, -0.045, 0.05), (x, -0.10, 0.05), 0.032, L.glass, seg=18)
    return K


def picture_light(L):
    """A picture light: a slim hood on two arms over a frame, 0.50 m wide."""
    K = Mesh('lighting_picture_light')
    K.box(-0.02, 0.02, -0.01, 0.0, 0.03, 0.10, L.metal)
    for x in (-0.15, 0.15):
        line(K, [(x, -0.005, 0.07), (x, -0.08, 0.07), (x, -0.17, 0.065)], 0.007, L.metal, seg=6)
    K.cyl((-0.25, -0.17, 0.065), (0.25, -0.17, 0.065), 0.025, L.metal, seg=14)
    if L.classic:
        K.cyl((-0.22, -0.17, 0.045), (0.22, -0.17, 0.045), 0.012, L.glass, seg=8)
    return K


def swing_arm(L):
    """A swing-arm reading lamp on a wall plate, 0.55 m reach."""
    K = Mesh('lighting_swing_arm')
    K.box(-0.05, 0.05, -0.012, 0.0, 0.08, 0.22, L.metal, r=0.004, seg=1)
    K.cyl((0, -0.012, 0.15), (0, -0.04, 0.15), 0.022, L.metal, seg=10)
    line(K, [(0, -0.04, 0.15), (0, -0.30, 0.15)], 0.009, L.metal)
    K.cyl((0, -0.30, 0.15), (0, -0.30, 0.15), 0.01, L.metal)
    line(K, [(0, -0.30, 0.15), (0, -0.52, 0.19)], 0.009, L.metal)
    # the shade: a cone looking down, on its hinge
    if L.classic:
        K.lathe([(0.0, 0.10), (0.04, 0.10), (0.10, 0.0)], material('SwingShade', (0.93, 0.89, 0.78), 0.9), at=(0, -0.52, 0.12), seg=18)
        bulb(K, L, (0, -0.52, 0.17), 0.02)
    else:
        K.cyl((0, -0.52, 0.20), (0, -0.52, 0.09), 0.03, L.metal, seg=16, r1=0.075)
        K.cyl((0, -0.52, 0.09), (0, -0.52, 0.085), 0.07, L.glass, seg=16)
    return K


# ------------------------------------------------------------------ wall (exterior)

def wall_lantern(L):
    """An exterior wall lantern: a coach lantern (classic) or a cylinder up/down light (modern)."""
    K = Mesh('lighting_wall_lantern')
    if L.classic:
        K.box(-0.06, 0.06, -0.012, 0.0, 0.06, 0.36, L.metal, r=0.003, seg=1)
        K.box(-0.02, 0.02, -0.07, -0.012, 0.18, 0.22, L.metal)
        # the lantern body: a tapering glass box in a frame, with a roof and a finial
        K.box(-0.07, 0.07, -0.20, -0.075, 0.08, 0.10, L.metal, r=0.004, seg=1)
        K.cyl((0, -0.1375, 0.10), (0, -0.1375, 0.40), 0.088, L.glass, seg=4, r1=0.062)
        for a in (0, 90, 180, 270):
            c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        for a in (0, 90, 180, 270):
            c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
            K.cyl((0.062 * c, -0.1375 + 0.062 * s, 0.10), (0.088 * c, -0.1375 + 0.088 * s, 0.40), 0.007, L.metal, seg=5)
        K.cyl((0, -0.1375, 0.40), (0, -0.1375, 0.46), 0.115, L.metal, seg=4, r1=0.04)
        K.cyl((0, -0.1375, 0.46), (0, -0.1375, 0.50), 0.012, L.metal, seg=8)
        bulb(K, L, (0, -0.1375, 0.17), 0.025)
    else:
        K.box(-0.05, 0.05, -0.014, 0.0, 0.05, 0.31, L.metal, r=0.003, seg=1)
        K.cyl((0, -0.014, 0.18), (0, -0.07, 0.18), 0.02, L.metal, seg=8)
        K.cyl((0, -0.10, 0.04), (0, -0.10, 0.34), 0.06, L.metal, seg=24)
        K.cyl((0, -0.10, 0.10), (0, -0.10, 0.26), 0.062, L.glass, seg=24)
    return K


def barn_light(L):
    """A gooseneck barn light with a wide dome shade, 0.40 m across, 0.55 m reach."""
    K = Mesh('lighting_barn_light')
    K.box(-0.04, 0.04, -0.012, 0.0, 0.10, 0.30, L.metal, r=0.003, seg=1)
    line(K, [(0.0, -0.012, 0.26), (0.0, -0.10, 0.34), (0.0, -0.22, 0.36), (0.0, -0.31, 0.30), (0.0, -0.33, 0.24)], 0.011, L.metal)
    K.lathe([(0.0, 0.10), (0.04, 0.10), (0.12, 0.085), (0.19, 0.03), (0.20, 0.0), (0.185, 0.0), (0.12, 0.05), (0.0, 0.07)],
            L.metal, at=(0, -0.38, 0.0), seg=28, hard=(3,))
    bulb(K, L, (0, -0.38, 0.01), 0.035)
    return K


def flood_light(L):
    """A security flood light: a lamp housing with a hood on a wall bracket, 0.30 m wide."""
    K = Mesh('lighting_flood_light')
    K.box(-0.04, 0.04, -0.012, 0.0, 0.02, 0.12, L.metal, r=0.003, seg=1)
    K.cyl((0, -0.012, 0.07), (0, -0.07, 0.07), 0.016, L.metal, seg=8)
    K.box(-0.14, 0.14, -0.19, -0.07, 0.01, 0.20, L.metal, r=0.012, seg=2)
    K.box(-0.125, 0.125, -0.206, -0.19, 0.04, 0.17, L.glass)
    K.box(-0.15, 0.15, -0.26, -0.19, 0.19, 0.205, L.metal)                                    # the hood
    return K


# ------------------------------------------------------------------ outdoor posts

def post_lamp(L):
    """A garden post lamp 2.45 m tall: a fluted cast post with a lantern (classic) or a slim square post with a box head (modern)."""
    K = Mesh('lighting_post_lamp')
    if L.classic:
        K.lathe([(0.0, 0.0), (0.12, 0.0), (0.13, 0.04), (0.10, 0.10), (0.07, 0.20), (0.05, 0.32), (0.045, 0.40)], L.metal, at=(0, 0, 0.0), seg=12, hard=(1,))
        K.lathe([(0.0, 0.0), (0.04, 0.0), (0.035, 0.30), (0.04, 0.60), (0.034, 1.00), (0.04, 1.40), (0.05, 1.70), (0.065, 1.80), (0.04, 1.84)], L.metal, at=(0, 0, 0.40), seg=12, hard=())
        z = 2.20
        K.box(-0.10, 0.10, -0.10, 0.10, z - 0.40, z - 0.37, L.metal)
        K.cyl((0, 0, z - 0.37), (0, 0, z - 0.02), 0.145, L.glass, seg=4, r1=0.105)
        for a in (0, 90, 180, 270):
            c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
            K.cyl((0.105 * c, 0.105 * s, z - 0.37), (0.145 * c, 0.145 * s, z - 0.02), 0.009, L.metal, seg=5)
        K.cyl((0, 0, z - 0.02), (0, 0, z + 0.10), 0.19, L.metal, seg=4, r1=0.04)
        K.cyl((0, 0, z + 0.10), (0, 0, z + 0.25), 0.012, L.metal, seg=8)
        bulb(K, L, (0, 0, z - 0.33), 0.04)
    else:
        K.box(-0.07, 0.07, -0.07, 0.07, 0.0, 0.04, L.metal)
        K.box(-0.035, 0.035, -0.035, 0.035, 0.04, 2.20, L.metal, r=0.004, seg=1)
        z = 2.20
        K.box(-0.12, 0.12, -0.12, 0.12, z, z + 0.04, L.metal)
        K.box(-0.10, 0.10, -0.10, 0.10, z - 0.20 + 0.04, z, L.glass)
        K.box(-0.13, 0.13, -0.13, 0.13, z + 0.04, z + 0.07, L.metal)
        K.box(-0.12, 0.12, -0.12, 0.12, z - 0.20, z - 0.16, L.metal)
    return K


def pole_light(L):
    """A yard pole light 3.80 m tall with an arm: a gooseneck dome (classic) or a flat cobra head (modern). The arm points along +x."""
    K = Mesh('lighting_pole_light')
    K.cyl((0, 0, 0.0), (0, 0, 0.12), 0.11, L.metal, seg=14, r1=0.09)
    K.cyl((0, 0, 0.12), (0, 0, 3.70), 0.045, L.metal, seg=14, r1=0.075)
    if L.classic:
        line(K, [(0, 0, 3.55), (0.18, 0, 3.78), (0.42, 0, 3.80), (0.60, 0, 3.70)], 0.022, L.metal)
        K.lathe([(0.0, 0.10), (0.04, 0.10), (0.15, 0.08), (0.24, 0.02), (0.25, 0.0), (0.23, -0.01), (0.14, 0.04), (0.0, 0.06)], L.metal, at=(0.60, 0, 3.52), seg=24, hard=(3,))
        bulb(K, L, (0.60, 0, 3.52), 0.04)
    else:
        line(K, [(0, 0, 3.60), (0.12, 0, 3.74), (0.30, 0, 3.76)], 0.028, L.metal)
        K.box(0.20, 0.84, -0.12, 0.12, 3.64, 3.70, L.metal, r=0.025, seg=2)
        K.box(0.30, 0.78, -0.09, 0.09, 3.625, 3.64, L.glass)
    return K


def bollard(L):
    """A garden bollard light 0.95 m tall: a lantern on a short post (classic) or a slotted cylinder (modern)."""
    K = Mesh('lighting_bollard')
    if L.classic:
        K.lathe([(0.0, 0.0), (0.08, 0.0), (0.09, 0.03), (0.06, 0.10), (0.045, 0.20), (0.04, 0.5)], L.metal, at=(0, 0, 0.0), seg=12, hard=(1,))
        K.box(-0.07, 0.07, -0.07, 0.07, 0.50, 0.53, L.metal)
        K.cyl((0, 0, 0.53), (0, 0, 0.78), 0.095, L.glass, seg=4, r1=0.075)
        for a in (0, 90, 180, 270):
            c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
            K.cyl((0.075 * c, 0.075 * s, 0.53), (0.095 * c, 0.095 * s, 0.78), 0.007, L.metal, seg=5)
        K.cyl((0, 0, 0.78), (0, 0, 0.88), 0.125, L.metal, seg=4, r1=0.03)
        K.cyl((0, 0, 0.88), (0, 0, 0.95), 0.01, L.metal, seg=6)
        bulb(K, L, (0, 0, 0.58), 0.03)
    else:
        K.cyl((0, 0, 0.0), (0, 0, 0.92), 0.075, L.metal, seg=24)
        K.cyl((0, 0, 0.92), (0, 0, 0.95), 0.08, L.metal, seg=24)
        K.cyl((0, 0, 0.66), (0, 0, 0.84), 0.0765, L.glass, seg=24)
        K.cyl((0, 0, 0.0), (0, 0, 0.04), 0.095, L.metal, seg=24)
    return K


def path_light(L):
    """A path light on a ground stake, 0.58 m tall: a tiered pagoda cap (classic) or a mushroom hood (modern)."""
    K = Mesh('lighting_path_light')
    K.cyl((0, 0, 0.0), (0, 0, 0.38), 0.015, L.metal, seg=10)
    K.cyl((0, 0, 0.0), (0, 0, 0.03), 0.03, L.metal, seg=10)
    if L.classic:
        K.cyl((0, 0, 0.30), (0, 0, 0.45), 0.06, L.glass, seg=4, r1=0.05)
        K.cyl((0, 0, 0.45), (0, 0, 0.50), 0.14, L.metal, seg=4, r1=0.085)
        K.cyl((0, 0, 0.50), (0, 0, 0.56), 0.085, L.metal, seg=4, r1=0.04)
        K.cyl((0, 0, 0.56), (0, 0, 0.58), 0.01, L.metal, seg=6)
        bulb(K, L, (0, 0, 0.34), 0.02)
    else:
        K.cyl((0, 0, 0.36), (0, 0, 0.44), 0.035, L.glass, seg=14)
        K.lathe([(0.0, 0.0), (0.10, 0.0), (0.12, 0.01), (0.11, 0.025), (0.08, 0.05), (0.0, 0.06)], L.metal, at=(0, 0, 0.44), seg=26, hard=(1,))
    return K
