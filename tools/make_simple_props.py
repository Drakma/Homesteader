"""
Builds the simple props that had no model, as GLBs in headless Blender: free, local, low-poly (no Meshy).

    blender --background --python tools/make_simple_props.py                    (all of them)
    blender --background --python tools/make_simple_props.py -- mat_stone ...   (only these)
    python tools/render_icon_from_model.py assets/<category>/<id>/<id>.glb assets/<category>/<id>/<id>.png

  bales        mat_bale_hay_square / _round, mat_bale_straw_square / _round, mat_bale_silage_round
  logs         mat_log_<species>, mat_pile_logs_<species>_<size>, mat_wood_logs_stack      (firewood bundles: tools/make_fuel_props.py)
  lumber       lumber_bundle_2x4_small / _large, lumber_bundle_2x10_small / _large
  cans, tanks  fuel_propane_1_5l / _18l / _36l, fuel_tank_propane_1900l / _3800l, fuel_tank_bulk_small / _large      (fuel cans and pumps: tools/make_fuel_props.py),
               building_paint_interior_wall, tool_bucket_empty, water_bucket_water
  poles, pipe  electricity_power_pole_wood / _metal, electricity_wooden_utility_pole, water_pipe, net_cable, mat_rope
  docks        dock_small_new / _old, dock_large_new / _old
  small        mat_stone, electricity_mpptcontroller, water_filter, tool_tap, fishing_bait

Every item is already in the kit: only its model entry, its dimensions and its README are written, the name, price and the rest stay.
The bags (fertilizer, charcoal, seed bag, grain sacks) are not here: tools/make_sacks.py restyles the sand bag model for them.

Conventions: 1 unit = 1 m, pivot at the centre of the footprint, ground at z = 0. Long things lie along x (docks and log piles along y).
"""
import glob
import json
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_romex as shapes  # noqa: E402    (Mesh: box, radial_box, cylinder, finish; material)

ROOT = shapes.ROOT
RX = Matrix.Rotation(math.pi / 2, 4, 'Y')       # turns a lathe's axis (z) to x
RY = Matrix.Rotation(-math.pi / 2, 4, 'X')      # and to y
T = Matrix.Translation
mat = shapes.material


class Kit(shapes.Mesh):
    smooth = True

    def lathe(self, profile, m, seg=16, matrix=None, closed=False):
        """Turns a profile [(r, z), ...] round the z axis, then places it with `matrix`."""
        i = self.mi(m)
        mx = matrix or Matrix.Identity(4)
        rings = []
        for r, z in profile:
            if r <= 1e-6:
                rings.append([self.bm.verts.new(mx @ Vector((0.0, 0.0, z)))])
            else:
                rings.append([self.bm.verts.new(mx @ Vector((r * math.cos(2 * math.pi * k / seg), r * math.sin(2 * math.pi * k / seg), z))) for k in range(seg)])
        n = len(rings)
        for a in range(n if closed else n - 1):
            ra, rb = rings[a], rings[(a + 1) % n]
            for k in range(seg):
                j = (k + 1) % seg
                if len(ra) == 1 and len(rb) == 1:
                    continue
                if len(ra) == 1:
                    f = self.bm.faces.new((ra[0], rb[j], rb[k]))
                elif len(rb) == 1:
                    f = self.bm.faces.new((ra[k], ra[j], rb[0]))
                else:
                    f = self.bm.faces.new((ra[k], ra[j], rb[j], rb[k]))
                f.material_index = i

    def tube(self, p0, p1, r0, r1, m, sides=10, cap0=None, cap1=None):
        """A round bar from p0 to p1 (radius r0 to r1). cap0 / cap1: the material of each end, None leaves it open."""
        i = self.mi(m)
        p0, p1 = Vector(p0), Vector(p1)
        d = (p1 - p0).normalized()
        u = Vector((0.0, 0.0, 1.0)).cross(d)
        u = Vector((1.0, 0.0, 0.0)) if u.length < 1e-6 else u.normalized()
        v = d.cross(u)
        ring = lambda p, r: [self.bm.verts.new(p + (u * math.cos(2 * math.pi * k / sides) + v * math.sin(2 * math.pi * k / sides)) * r) for k in range(sides)]
        a, b = ring(p0, r0), ring(p1, r1)
        for k in range(sides):
            j = (k + 1) % sides
            self.bm.faces.new((a[k], a[j], b[j], b[k])).material_index = i
        if cap0 is not None:
            self.bm.faces.new(a[::-1]).material_index = self.mi(cap0)
        if cap1 is not None:
            self.bm.faces.new(b).material_index = self.mi(cap1)

    def path(self, pts, r, m, sides=6, caps=True):
        for k in range(len(pts) - 1):
            self.tube(pts[k], pts[k + 1], r, r, m, sides, m if caps and k == 0 else None, m if caps and k == len(pts) - 2 else None)

    def bx(self, size, loc, m, rot=None):
        self.box(size, T(loc) @ rot if rot is not None else T(loc), m)

    def prism(self, pts, depth, matrix, m, sides=None):
        """A flat outline [(x, y), ...] pulled out along local z by `depth`. sides: a material per edge (default: m)."""
        lo = [self.bm.verts.new(matrix @ Vector((x, y, 0.0))) for x, y in pts]
        hi = [self.bm.verts.new(matrix @ Vector((x, y, depth))) for x, y in pts]
        self.bm.faces.new(lo[::-1]).material_index = self.mi(m)
        self.bm.faces.new(hi).material_index = self.mi(m)
        for k in range(len(pts)):
            j = (k + 1) % len(pts)
            self.bm.faces.new((lo[k], lo[j], hi[j], hi[k])).material_index = self.mi(sides[k] if sides else m)

    def arc(self, radius, z0, z1, a0, a1, thick, m, steps=6):
        """A curved band (part of a ring) from angle a0 to a1."""
        for k in range(steps):
            a = a0 + (a1 - a0) * (k + 0.5) / steps
            chord = 2 * radius * math.sin((a1 - a0) / steps / 2) * 1.04
            self.box((thick, chord, z1 - z0), Matrix.Rotation(a, 4, 'Z') @ T((radius, 0.0, (z0 + z1) / 2)), m)

    def bail(self, radius, z, tilt, r, m, steps=10):
        """A wire handle hinged at (+-radius, 0, z). tilt: 90 = standing straight up, -70 = hanging down the side."""
        t = math.radians(tilt)
        pts = [(radius * math.cos(math.pi * k / steps), -radius * math.sin(math.pi * k / steps) * math.cos(t), z + radius * math.sin(math.pi * k / steps) * math.sin(t))
               for k in range(steps + 1)]
        self.path(pts, r, m, 5)
        return pts[steps // 2]

    def rock(self, size, m, rnd, jitter=0.22, sub=2, at=(0.0, 0.0)):
        i = self.mi(m)
        r = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=1.0)
        for v in r['verts']:
            k = 1 + rnd.uniform(-jitter, jitter)
            z = max(v.co.z * k, -0.55)
            v.co = Vector((at[0] + v.co.x * k * size[0] / 2, at[1] + v.co.y * k * size[1] / 2, (z + 0.55) / 1.55 * size[2]))
        for f in set(f for v in r['verts'] for f in v.link_faces):
            f.material_index = i

    def done(self, name):
        o = self.finish(name)
        if self.smooth:
            try:
                o.data.shade_smooth()
                o.data.set_sharp_from_angle(angle=math.radians(38))
            except AttributeError:
                pass
        return o


# ------------------------------------------------------------------------------------------------------------------------------------- bales

def bale_square(rgb, seed):
    K, rnd = Kit(), random.Random(seed)
    L, W, H = 0.9, 0.45, 0.35
    body = mat('Bale', rgb, 0.95)
    light = mat('BaleLight', tuple(min(1.0, c * 1.18) for c in rgb), 0.95)
    dark = mat('BaleShade', tuple(c * 0.72 for c in rgb), 0.95)
    twine = mat('Twine', (0.85, 0.42, 0.12), 0.8)
    K.bx((L, W, H), (0, 0, H / 2), body)
    for k in range(1, 6):                                            # the flakes: a seam across the bale every 15 cm
        x = -L / 2 + L * k / 6
        K.bx((0.008, W + 0.004, H + 0.004), (x, 0, H / 2), dark)
    for n in range(110):                                             # loose stalks on every face
        face = rnd.choice('TTTFBLR')
        ln = rnd.uniform(0.08, 0.2)
        m = rnd.choice((light, light, dark))
        if face == 'T':
            K.bx((ln, 0.012, 0.006), (rnd.uniform(-L / 2 + 0.1, L / 2 - 0.1), rnd.uniform(-W / 2 + 0.03, W / 2 - 0.03), H + 0.002), m, Matrix.Rotation(rnd.uniform(-0.5, 0.5), 4, 'Z'))
        elif face in 'FB':
            y = (-W / 2 - 0.002) if face == 'F' else (W / 2 + 0.002)
            K.bx((ln, 0.006, 0.012), (rnd.uniform(-L / 2 + 0.1, L / 2 - 0.1), y, rnd.uniform(0.03, H - 0.03)), m, Matrix.Rotation(rnd.uniform(-0.4, 0.4), 4, 'Y'))
        else:                                                        # the cut ends: stalk ends as little squares
            x = (-L / 2 - 0.002) if face == 'L' else (L / 2 + 0.002)
            K.bx((0.006, 0.02, 0.02), (x, rnd.uniform(-W / 2 + 0.03, W / 2 - 0.03), rnd.uniform(0.03, H - 0.03)), m)
    for y in (-W * 0.24, W * 0.24):                                  # two strings round the length
        K.bx((L + 0.014, 0.01, 0.006), (0, y, H + 0.004), twine)
        K.bx((L + 0.014, 0.01, 0.006), (0, y, 0.003), twine)
        for x in (-L / 2 - 0.004, L / 2 + 0.004):
            K.bx((0.006, 0.01, H), (x, y, H / 2), twine)
    return K.done('bale')


def bale_round(rgb, seed, wrap=None):
    """A round bale lying on its side (the axis along y). wrap: the colour of a plastic wrap (silage), else net-wrapped with open ends."""
    K, rnd = Kit(), random.Random(seed)
    R, W = 0.6, 1.2
    mx = T((0, 0, R)) @ RY
    if wrap:
        skin = mat('SilageWrap', wrap, 0.35)
        seam = mat('SilageWrapSeam', tuple(c * 0.9 for c in wrap), 0.35)
        e = 0.1
        prof = [(0.0, -W / 2 + 0.02), (R * 0.3, -W / 2)] + [(R - e + e * math.sin(a), -W / 2 + e - e * math.cos(a)) for a in (0.0, 0.55, 1.1, math.pi / 2)]
        prof += [(R - e + e * math.sin(a), W / 2 - e + e * math.cos(a)) for a in (math.pi / 2, 1.1, 0.55, 0.0)] + [(R * 0.3, W / 2), (0.0, W / 2 - 0.02)]
        K.lathe(prof, skin, 24, mx)
        for k in range(1, 8):                                        # the overlaps of the wrap
            z = -W / 2 + W * k / 8
            K.lathe([(R + 0.004, z - 0.012), (R + 0.007, z), (R + 0.004, z + 0.012)], seam, 24, mx)
        for s in (-1, 1):                                            # the wrap gathers at the middle of each end
            K.lathe([(R * 0.3, s * (W / 2 + 0.003)), (R * 0.06, s * (W / 2 + 0.012)), (0.0, s * (W / 2 + 0.004))], seam, 12, mx)
        return K.done('bale')
    body = mat('Bale', rgb, 0.95)
    light = mat('BaleLight', tuple(min(1.0, c * 1.18) for c in rgb), 0.95)
    dark = mat('BaleShade', tuple(c * 0.72 for c in rgb), 0.95)
    net = mat('BaleNet', tuple(min(1.0, c * 1.3 + 0.08) for c in rgb), 0.8)
    K.lathe([(R - 0.02, -W / 2), (R, -W / 2 + 0.03), (R, W / 2 - 0.03), (R - 0.02, W / 2)], body, 24, mx)
    for s in (-1, 1):                                                # the ends: the roll shows as rings
        z = s * W / 2
        rings = [0.0, 0.07, 0.16, 0.25, 0.34, 0.43, 0.52, R - 0.02]
        for k in range(len(rings) - 1):
            K.lathe([(rings[k], z + s * (0.012 if k % 2 else 0.0)), (rings[k + 1], z + s * (0.0 if k % 2 else 0.012))], (dark, body, light)[k % 3], 24, mx)
    for k in range(9):                                               # the net wrap
        z = -W / 2 + 0.08 + (W - 0.16) * k / 8
        K.lathe([(R + 0.003, z - 0.006), (R + 0.003, z + 0.006)], net, 24, mx)
    for n in range(60):                                              # loose stalks round the roll
        a, y = rnd.uniform(0, 2 * math.pi), rnd.uniform(-W / 2 + 0.08, W / 2 - 0.08)
        K.box((0.006, rnd.uniform(0.1, 0.24), 0.012), T((0, y, R)) @ Matrix.Rotation(a, 4, 'Y') @ T((R + 0.004, 0, 0)) @ Matrix.Rotation(rnd.uniform(-0.3, 0.3), 4, 'X'),
              rnd.choice((light, dark)))
    return K.done('bale')


# -------------------------------------------------------------------------------------------------------------------------------------- logs

# species: bark, wood, heartwood, bark marks (None: plain)
SPECIES = {
    'birch': ((0.9, 0.89, 0.84), (0.9, 0.8, 0.6), (0.78, 0.62, 0.42), (0.16, 0.14, 0.12)),
    'maple': ((0.4, 0.32, 0.26), (0.9, 0.78, 0.58), (0.74, 0.56, 0.38), None),
    'oak': ((0.27, 0.22, 0.17), (0.8, 0.64, 0.42), (0.55, 0.38, 0.22), None),
    'pine': ((0.5, 0.34, 0.22), (0.93, 0.8, 0.52), (0.82, 0.6, 0.32), (0.36, 0.22, 0.13)),
    'willow': ((0.5, 0.41, 0.29), (0.88, 0.8, 0.62), (0.7, 0.58, 0.42), None),
}


def log_mats(species):
    bark, wood, heart, marks = SPECIES[species]
    return (mat('Bark_' + species, bark, 0.95), mat('Wood_' + species, wood, 0.8), mat('Heartwood_' + species, heart, 0.8),
            mat('BarkMarks_' + species, marks, 0.95) if marks else None)


def log(K, p0, p1, r, mats, rnd, sides=10, marks=3):
    """A cut log from p0 to p1: bark with a little wobble, sawn ends with the heartwood showing."""
    bark, wood, heart, mark = mats
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    rs = [r * (1 + rnd.uniform(-0.06, 0.06)) for _ in range(4)]
    for k in range(3):
        K.tube(p0 + d * (k / 3), p0 + d * ((k + 1) / 3), rs[k], rs[k + 1], bark, sides, wood if k == 0 else None, wood if k == 2 else None)
    n = d.normalized()
    K.tube(p0 - n * 0.002, p0, r * 0.45, r * 0.45, heart, 6, heart)
    K.tube(p1, p1 + n * 0.002, r * 0.45, r * 0.45, heart, 6, None, heart)
    if mark:
        for _ in range(marks):
            t = rnd.uniform(0.08, 0.92)
            w = rnd.uniform(0.008, 0.02)
            K.tube(p0 + d * t, p0 + d * t + n * w, r * 1.07, r * 1.07, mark, sides)


def single_log(species):
    K, rnd = Kit(), random.Random(hash(species) % 1000)
    mats = log_mats(species)
    r, L = 0.15, 1.2
    log(K, (-L / 2, 0, r), (L / 2, 0, r), r, mats, rnd, 12, 5)
    K.tube((0.2, 0.0, r + r * 0.9), (0.22, 0.02, r + r * 1.25), 0.03, 0.022, mats[0], 6, None, mats[1])       # the stub of a branch
    return K.done('log')


def log_pile(species, base, rows, r, length, seed):
    """Cut logs stacked in a pyramid, lying along y."""
    K, rnd = Kit(), random.Random(seed)
    mats = log_mats(species)
    for j in range(rows):
        n = base - j
        for i in range(n):
            x = (i - (n - 1) / 2) * 2 * r
            z = r + j * r * math.sqrt(3)
            ln = length * rnd.uniform(0.94, 1.0)
            off = rnd.uniform(-0.02, 0.02)
            log(K, (x, -ln / 2 + off, z), (x, ln / 2 + off, z), r * rnd.uniform(0.9, 0.99), mats, rnd, 8, 1)
    return K.done('pile')


def logs_stack():
    """A squared stack of mixed logs held between four stakes."""
    K, rnd = Kit(), random.Random(11)
    r, length = 0.105, 0.78
    species = [log_mats(s) for s in ('oak', 'pine', 'maple')]
    for j in range(4):
        n = 6 if j % 2 == 0 else 5
        for i in range(n):
            x = (i - (n - 1) / 2) * 2 * r
            z = r + j * r * math.sqrt(3)
            ln = length * rnd.uniform(0.92, 1.0)
            log(K, (x, -ln / 2, z), (x, ln / 2, z), r * rnd.uniform(0.88, 0.99), rnd.choice(species), rnd, 8, 0)
    stake = mat('Stake', (0.5, 0.38, 0.24), 0.9)
    for sx in (-1, 1):
        for sy in (-1, 1):
            K.tube((sx * (6 * r + 0.045), sy * 0.25, 0.0), (sx * (6 * r + 0.045), sy * 0.25, 1.0), 0.04, 0.035, stake, 6, None, stake)
    return K.done('stack')


def firewood():
    """An armful of split firewood: three quarter-round pieces."""
    K = Kit()
    bark, wood, heart, _ = log_mats('pine')
    r, L = 0.11, 0.4
    arc = [(r * math.cos(a), r * math.sin(a)) for a in (0.0, math.pi / 8, math.pi / 4, 3 * math.pi / 8, math.pi / 2)]
    pts = [(0.0, 0.0)] + arc
    sides = [wood] + [bark] * 4 + [wood]
    along_x = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))       # the outline in y-z, pulled out along x
    lay = lambda y, z, roll, yaw, ln: T((0, y, z)) @ Matrix.Rotation(yaw, 4, 'Z') @ T((-ln / 2, 0, 0)) @ Matrix.Rotation(roll, 4, 'X') @ along_x
    K.prism(pts, L, lay(-r * 0.78, 0.0, math.radians(135), 0.0, L), wood, sides)             # two on the ground, bark down, the split faces up
    K.prism(pts, L * 0.94, lay(r * 0.78, 0.0, math.radians(135), 0.05, L * 0.94), wood, sides)
    K.prism(pts, L * 0.9, lay(0.0, r * 0.62, math.radians(-45), -0.14, L * 0.9), wood, sides)      # one on top, its corner down between them
    o = K.done('firewood')
    lo = min(v.co.z for v in o.data.vertices)
    o.data.transform(T((0, 0, -lo)))
    return o


def lumber_bundle(width, thick, length, cols, rows):
    """Boards strapped into a bundle on three bearers."""
    K, rnd = Kit(), random.Random(cols * 100 + rows)
    woods = [mat('Lumber', (0.87, 0.73, 0.5), 0.85), mat('LumberLight', (0.92, 0.8, 0.58), 0.85), mat('LumberDark', (0.8, 0.64, 0.42), 0.85)]
    end = mat('LumberEnd', (0.95, 0.85, 0.62), 0.85)
    strap = mat('Strap', (0.12, 0.12, 0.13), 0.5)
    bearer_h = 0.07
    W, H = cols * width, rows * thick
    for j in range(rows):
        for i in range(cols):
            x_off = rnd.uniform(-0.012, 0.012)
            K.bx((length, width - 0.003, thick - 0.002), (x_off, (i - (cols - 1) / 2) * width, bearer_h + thick * (j + 0.5)), rnd.choice(woods))
            K.bx((0.004, width - 0.012, thick - 0.01), (x_off + length / 2 + 0.002, (i - (cols - 1) / 2) * width, bearer_h + thick * (j + 0.5)), end)
            K.bx((0.004, width - 0.012, thick - 0.01), (x_off - length / 2 - 0.002, (i - (cols - 1) / 2) * width, bearer_h + thick * (j + 0.5)), end)
    for x in (-length * 0.36, 0.0, length * 0.36):
        K.bx((0.09, W + 0.06, bearer_h), (x, 0, bearer_h / 2), woods[2])
    for x in (-length * 0.28, length * 0.28):
        K.bx((0.03, W + 0.008, 0.003), (x, 0, bearer_h + H + 0.0015), strap)
        K.bx((0.03, W + 0.008, 0.003), (x, 0, bearer_h - 0.0015), strap)
        for s in (-1, 1):
            K.bx((0.03, 0.003, H + 0.004), (x, s * (W / 2 + 0.003), bearer_h + H / 2), strap)
    return K.done('bundle')


# ------------------------------------------------------------------------------------------------------------------------------ cans and tanks

def propane(r, h, rgb, collar=True):
    """A propane cylinder: foot ring, body with a domed shoulder, valve, and (the refillable sizes) a collar guard with hand holes."""
    K = Kit()
    body = mat('PropaneBody', rgb, 0.4)
    dark = mat('PropaneFoot', tuple(c * 0.75 for c in rgb), 0.5)
    brass = mat('Brass', (0.8, 0.62, 0.25), 0.35)
    black = mat('ValveHandle', (0.08, 0.08, 0.09), 0.6)
    label = mat('PropaneLabel', (0.85, 0.15, 0.1), 0.7)
    foot = 0.035 if collar else 0.0
    dome = r * 0.6
    top = h - dome
    prof = [(0.0, foot), (r * 0.6, foot)] + [(r * (0.6 + 0.4 * math.sin(a)), foot + r * 0.35 * (1 - math.cos(a))) for a in (0.5, 1.0, math.pi / 2)]
    prof += [(r * math.cos(a), top + dome * math.sin(a)) for a in (0.0, 0.4, 0.8, 1.15, 1.4)] + [(r * 0.14, h)]
    K.lathe(prof, body, 16)
    if collar:
        K.lathe([(r * 0.82, 0.0), (r * 0.86, foot + 0.02)], dark, 16)
        K.lathe([(r * 0.82, 0.0), (r * 0.76, 0.0), (r * 0.8, foot + 0.02)], dark, 16)
        for a0 in (math.radians(35), math.radians(215)):                 # the collar: two guards with a gap each side for the hose
            K.arc(r * 0.72, h - dome * 0.35, h + 0.11, a0, a0 + math.radians(110), 0.006, body, 6)
            K.arc(r * 0.72, h + 0.1, h + 0.125, a0 - 0.5, a0 + math.radians(110) + 0.5, 0.012, body, 8)
    K.lathe([(r * 0.14, h - 0.01), (r * 0.14, h + 0.035), (r * 0.09, h + 0.04), (r * 0.09, h + 0.06)], brass, 8)
    K.tube((0, 0, h + 0.03), (r * 0.42, 0, h + 0.03), r * 0.07, r * 0.07, brass, 6, None, brass)             # the outlet
    K.lathe([(0.0, h + 0.058), (r * 0.26, h + 0.058), (r * 0.26, h + 0.075), (0.0, h + 0.075)], black, 6)      # the handwheel
    K.lathe([(r * 1.004, top * 0.42), (r * 1.004, top * 0.72)], label, 16)
    return K.done('propane')


def capsule_profile(r, length, dish, steps=5):
    """The (r, z) profile of a tank with dished ends, z from -length/2 to length/2."""
    prof = [(r * math.sin(a), -length / 2 + dish * (1 - math.cos(a))) for a in [math.pi / 2 * k / steps for k in range(steps + 1)]]
    return prof + [(rr, -z) for rr, z in reversed(prof)]


def propane_tank_big(r, L):
    """A big residential propane tank: a long white capsule on two cradle feet, a domed valve cover on top, a PROPANE sticker on each side.
    Both sizes are the same tank, one longer and a little fatter."""
    K = Kit()
    zc = r + 0.16
    white = mat('TankWhite', (0.93, 0.93, 0.9), 0.4)
    grey = mat('TankFeet', (0.55, 0.56, 0.57), 0.6)
    K.lathe(capsule_profile(r, L, r * 0.7), white, 20, T((0, 0, zc)) @ RX)
    for x in (-L * 0.28, L * 0.28):
        K.bx((0.12, r * 1.3, zc - r * 0.8), (x, 0, (zc - r * 0.8) / 2), grey)
        K.bx((0.22, r * 1.5, 0.03), (x, 0, 0.015), grey)
        K.lathe([(r + 0.004, -0.04), (r + 0.004, 0.04)], grey, 20, T((x, 0, zc)) @ RX)                         # the weld band over each foot
    K.lathe([(0.17, zc + r - 0.03), (0.17, zc + r + 0.12), (0.12, zc + r + 0.17), (0.0, zc + r + 0.18)], white, 12)     # the dome over the valves
    for x in (-L * 0.36, L * 0.36):
        K.bx((0.05, 0.012, 0.06), (x, 0, zc + r + 0.02), grey)                                                 # lifting lugs
    import case_labels
    return case_labels.add_tank_sticker(K.done('tank'), 'tank_propane', r, zc, r * 0.9)


def bulk_tank(r, L, rgb, band):
    """A skid-mounted bulk fuel tank: a drum on saddles and runners, fill cap, vent, an outlet with a hose and nozzle."""
    K = Kit()
    zc = r + 0.3
    body = mat('BulkTank', rgb, 0.45)
    stripe = mat('BulkTankBand', band, 0.5)
    steel = mat('SkidSteel', (0.2, 0.2, 0.22), 0.6)
    hose = mat('Hose', (0.06, 0.06, 0.06), 0.8)
    metal = mat('Nozzle', (0.7, 0.71, 0.72), 0.35)
    K.lathe(capsule_profile(r, L, r * 0.22, 3), body, 20, T((0, 0, zc)) @ RX)
    K.lathe([(r + 0.004, -L * 0.06), (r + 0.004, L * 0.06)], stripe, 20, T((0, 0, zc)) @ RX)
    for y in (-r * 0.6, r * 0.6):
        K.bx((L * 0.95, 0.1, 0.1), (0, y, 0.05), steel)
    for x in (-L * 0.3, L * 0.3):
        K.bx((0.1, r * 1.5, zc - r * 0.82 - 0.1), (x, 0, 0.1 + (zc - r * 0.82 - 0.1) / 2), steel)
        K.lathe([(r + 0.006, -0.03), (r + 0.006, 0.03)], steel, 20, T((x, 0, zc)) @ RX)
    K.lathe([(0.06, zc + r - 0.02), (0.06, zc + r + 0.05), (0.075, zc + r + 0.05), (0.075, zc + r + 0.08), (0.0, zc + r + 0.08)], steel, 10, T((-L * 0.2, 0, 0)))    # the fill cap
    K.path([(L * 0.25, 0, zc + r - 0.02), (L * 0.25, 0, zc + r + 0.22), (L * 0.25 + 0.1, 0, zc + r + 0.22), (L * 0.25 + 0.1, 0, zc + r + 0.14)], 0.02, steel, 6)       # the vent
    x = L / 2 + 0.02                                                     # the outlet at the bottom of one end, a hose looped up to a hook, the nozzle
    K.tube((x - 0.12, 0, zc - r * 0.8), (x + 0.06, 0, zc - r * 0.8), 0.03, 0.03, metal, 8, None, metal)
    K.path([(x + 0.05, 0, zc - r * 0.8), (x + 0.12, 0.05, zc - r * 0.95), (x + 0.14, 0.2, zc - r * 0.7), (x + 0.12, 0.3, zc + r * 0.1), (x + 0.1, 0.22, zc + r * 0.5),
            (x + 0.08, 0.1, zc + r * 0.45)], 0.018, hose, 6)
    K.bx((0.05, 0.16, 0.05), (x + 0.08, 0.03, zc + r * 0.42), metal)
    K.bx((0.04, 0.04, 0.12), (x + 0.08, -0.04, zc + r * 0.34), metal)
    import case_labels
    return case_labels.add_tank_sticker(K.done('tank'), 'tank_fuel', r, zc, r * 0.7)


def jerry_can(w, d, h):
    """A red plastic fuel can: pressed side panels, a handle moulded over the top, a yellow spout with a cap."""
    K = Kit()
    red = mat('FuelCan', (0.78, 0.08, 0.06), 0.45)
    dark = mat('FuelCanPanel', (0.62, 0.06, 0.05), 0.5)
    yellow = mat('Spout', (0.95, 0.78, 0.1), 0.5)
    black = mat('SpoutCap', (0.07, 0.07, 0.08), 0.6)
    c = min(w, h) * 0.08
    hb = h * 0.8
    side = [(-w / 2 + c, 0.0), (w / 2 - c, 0.0), (w / 2, c), (w / 2, hb - c * 2), (w / 2 - c * 2.5, hb), (-w / 2 + c, hb), (-w / 2, hb - c), (-w / 2, c)]
    K.prism(side, d, T((0, d / 2, 0)) @ Matrix.Rotation(math.pi / 2, 4, 'X'), red)
    for s in (-1, 1):                                                    # the pressed panels
        K.bx((w * 0.62, 0.006, hb * 0.5), (0, s * (d / 2 + 0.002), hb * 0.48), dark)
        K.bx((w * 0.5, 0.008, hb * 0.07), (0, s * (d / 2 + 0.004), hb * 0.48), red, Matrix.Rotation(0.6, 4, 'Y'))
        K.bx((w * 0.5, 0.008, hb * 0.07), (0, s * (d / 2 + 0.004), hb * 0.48), red, Matrix.Rotation(-0.6, 4, 'Y'))
    g = h * 0.045                                                        # the handle
    K.bx((g, d * 0.5, h - hb), (-w * 0.32, 0, hb + (h - hb) / 2 - g / 2), red)
    K.bx((g, d * 0.5, (h - hb) * 0.7), (w * 0.1, 0, hb + (h - hb) * 0.35), red)
    K.bx((w * 0.42 + g, d * 0.5, g), (-w * 0.11, 0, h - g), red)
    p0 = Vector((w / 2 - c * 1.6, 0, hb - c * 0.8))                      # the spout
    n = Vector((0.75, 0, 0.66)).normalized()
    K.tube(p0 - n * 0.02, p0 + n * (h * 0.14), d * 0.16, d * 0.14, black, 10, None, black)
    K.tube(p0 + n * (h * 0.14), p0 + n * (h * 0.3), d * 0.09, d * 0.07, yellow, 10, None, black)
    return K.done('can')


def pail(rgb_label):
    """A 19 L plastic paint pail: tapered, ribbed under the rim, a lid, a wire handle hanging down, a colour label."""
    K = Kit()
    white = mat('Pail', (0.93, 0.93, 0.92), 0.5)
    lid = mat('PailLid', (0.88, 0.88, 0.87), 0.5)
    label = mat('PaintLabel', rgb_label, 0.7)
    ink = mat('PaintLabelBand', (0.2, 0.3, 0.5), 0.7)
    wire = mat('Wire', (0.6, 0.61, 0.62), 0.35)
    r0, r1, h = 0.128, 0.145, 0.35
    rr = lambda z: r0 + (r1 - r0) * z / h
    prof = [(0.0, 0.0), (r0, 0.0), (rr(h * 0.78), h * 0.78)]
    for z in (0.8, 0.86, 0.92):
        prof += [(rr(h * z) + 0.008, h * z), (rr(h * z) + 0.008, h * (z + 0.02)), (rr(h * (z + 0.03)), h * (z + 0.03))]
    prof += [(r1, h)]
    K.lathe(prof, white, 18)
    K.lathe([(r1 + 0.008, h - 0.012), (r1 + 0.008, h + 0.008), (r1 - 0.02, h + 0.008), (r1 - 0.03, h - 0.004), (0.0, h - 0.004)], lid, 18)
    K.lathe([(rr(h * 0.2) + 0.002, h * 0.2), (rr(h * 0.7) + 0.002, h * 0.7)], label, 18)
    K.lathe([(rr(h * 0.2) + 0.003, h * 0.2), (rr(h * 0.3) + 0.003, h * 0.3)], ink, 18)
    for s in (-1, 1):
        K.bx((0.012, 0.03, 0.03), (s * (r1 + 0.008), 0, h * 0.86), white)
    K.bail(r1 + 0.016, h * 0.86, -72, 0.004, wire)
    return K.done('pail')


def bucket(water):
    """A galvanized steel bucket with a wire handle and a wooden grip; `water`: filled nearly to the rim."""
    K = Kit()
    steel = mat('Galvanized', (0.68, 0.7, 0.72), 0.35)
    inner = mat('GalvanizedInside', (0.5, 0.52, 0.54), 0.4)
    wire = mat('Wire', (0.45, 0.46, 0.47), 0.35)
    grip = mat('Grip', (0.6, 0.42, 0.24), 0.8)
    r0, r1, h = 0.105, 0.15, 0.3
    rr = lambda z: r0 + (r1 - r0) * z / h
    prof = [(0.0, 0.012), (r0 - 0.012, 0.012), (r0 - 0.008, 0.0), (r0, 0.0)]
    for z in (0.3, 0.62):                                                # two pressed ribs
        prof += [(rr(h * z), h * z), (rr(h * z) + 0.005, h * (z + 0.015)), (rr(h * (z + 0.03)), h * (z + 0.03))]
    prof += [(r1, h - 0.012), (r1 + 0.007, h - 0.008), (r1 + 0.007, h), (r1 - 0.004, h)]
    K.lathe(prof, steel, 18)
    K.lathe([(r1 - 0.004, h), (r0 - 0.004, 0.02), (0.0, 0.02)], inner, 18)
    for s in (-1, 1):
        K.bx((0.006, 0.035, 0.04), (s * (r1 + 0.006), 0, h - 0.03), steel)
    top = K.bail(r1 + 0.012, h - 0.03, 78, 0.0035, wire)
    K.tube((-0.05, top[1], top[2]), (0.05, top[1], top[2]), 0.012, 0.012, grip, 8, grip, grip)
    if water:
        K.lathe([(0.0, h * 0.84), (rr(h * 0.84) - 0.005, h * 0.84)], mat('Water', (0.2, 0.45, 0.75), 0.08), 18)
    return K.done('bucket')


# -------------------------------------------------------------------------------------------------------------------------------- poles, pipe

def insulator(K, at, m, pin):
    K.lathe([(0.012, 0.0), (0.012, 0.06)], pin, 6, T(at))
    K.lathe([(0.03, 0.06), (0.05, 0.075), (0.03, 0.09), (0.05, 0.105), (0.03, 0.12), (0.04, 0.135), (0.02, 0.15), (0.0, 0.15)], m, 8, T(at))


def pole_wood(crossarm):
    """A 9 m wooden pole. crossarm: with an arm, braces and three insulators; else a bare utility pole with a cap and a tag."""
    K = Kit()
    wood = mat('PoleWood', (0.42, 0.3, 0.2), 0.9)
    base = mat('PoleTreated', (0.22, 0.16, 0.11), 0.9)
    steel = mat('PoleSteel', (0.6, 0.61, 0.62), 0.4)
    porcelain = mat('Insulator', (0.5, 0.3, 0.22), 0.3)
    H = 9.0
    rr = lambda z: 0.15 - 0.05 * z / H
    K.tube((0, 0, 0), (0, 0, 1.2), rr(0), rr(1.2), base, 10)
    for z0, z1 in ((1.2, 3.8), (3.8, 6.4), (6.4, H)):
        K.tube((0, 0, z0), (0, 0, z1), rr(z0), rr(z1), wood, 10, None, wood if z1 == H else None)
    K.bx((0.004, 0.09, 0.06), (0, -rr(1.7) - 0.001, 1.7), steel)        # the number tag
    if crossarm:
        z = 8.3
        K.bx((2.4, 0.09, 0.115), (0, -rr(z) - 0.045, z), wood)
        for s in (-1, 1):
            K.tube((s * 0.75, -rr(z) - 0.05, z - 0.05), (0, -rr(7.5) - 0.01, 7.5), 0.014, 0.014, steel, 5)
            insulator(K, (s * 1.08, -rr(z) - 0.045, z + 0.057), porcelain, steel)
            insulator(K, (s * 0.45, -rr(z) - 0.045, z + 0.057), porcelain, steel)
        insulator(K, (0, 0, H), porcelain, steel)
        K.lathe([(rr(z) + 0.004, z - 0.02), (rr(z) + 0.004, z + 0.02)], steel, 10)
    else:
        K.lathe([(rr(H) + 0.006, H - 0.05), (rr(H) + 0.006, H + 0.006), (0.0, H + 0.02)], steel, 10)           # a cap over the top
        for z in (2.6, 3.0, 3.4, 3.8):                                      # pole steps
            K.tube((0, 0, z), (0.24 if int(z * 10) % 8 else -0.24, 0, z), 0.01, 0.01, steel, 5, None, steel)
    return K.done('pole')


def pole_metal():
    """A 9 m galvanized steel pole: eight-sided and tapered, a bolted base plate, a steel arm with three insulators."""
    K = Kit()
    steel = mat('PoleSteel', (0.66, 0.68, 0.7), 0.35)
    dark = mat('PoleSteelDark', (0.4, 0.41, 0.43), 0.45)
    glass = mat('Insulator', (0.75, 0.78, 0.8), 0.2)
    H = 9.0
    rr = lambda z: 0.12 - 0.05 * z / H
    K.bx((0.42, 0.42, 0.03), (0, 0, 0.015), dark)
    for sx in (-1, 1):
        for sy in (-1, 1):
            K.tube((sx * 0.16, sy * 0.16, 0.03), (sx * 0.16, sy * 0.16, 0.075), 0.018, 0.018, dark, 6, None, dark)
    for z0, z1 in ((0.03, 4.5), (4.5, H)):
        K.tube((0, 0, z0), (0, 0, z1), rr(z0), rr(z1), steel, 8, None, dark if z1 == H else None)
    K.lathe([(rr(4.5) + 0.006, 4.44), (rr(4.5) + 0.006, 4.56)], dark, 8)                                       # the joint of the two sections
    K.bx((0.006, 0.12, 0.3), (0, -rr(0.9) + 0.002, 0.9), dark)                                              # the hand hole cover
    z = 8.5
    K.bx((2.0, 0.07, 0.09), (0, -rr(z) - 0.035, z), steel)
    for s in (-1, 1):
        K.tube((s * 0.6, -rr(z) - 0.035, z - 0.04), (0, -rr(7.9), 7.9), 0.012, 0.012, dark, 5)
        insulator(K, (s * 0.9, -rr(z) - 0.035, z + 0.045), glass, dark)
    insulator(K, (0, 0, H), glass, dark)
    return K.done('pole')


def water_pipe():
    """A 3 m length of blue water pipe with a white print line."""
    K = Kit()
    blue = mat('WaterPipe', (0.12, 0.38, 0.8), 0.45)
    bore = mat('PipeBore', (0.03, 0.06, 0.12), 0.8)
    L, r = 3.0, 0.016
    K.tube((-L / 2, 0, r), (L / 2, 0, r), r, r, blue, 10, blue, blue)
    K.tube((-L / 2 - 0.001, 0, r), (-L / 2, 0, r), r * 0.72, r * 0.72, bore, 8, bore)
    K.tube((L / 2, 0, r), (L / 2 + 0.001, 0, r), r * 0.72, r * 0.72, bore, 8, None, bore)
    K.bx((L * 0.96, 0.004, 0.002), (0, 0, 2 * r), mat('PipePrint', (0.92, 0.94, 0.96), 0.6))
    return K.done('pipe')


def coil(K, radii, layers, r, mats, seg=20):
    """Wraps of rope or cable lying in a flat coil: one ring per wrap."""
    n = 0
    for j in range(layers):
        for i, R in enumerate(radii):
            Rj = R + (r if j % 2 else 0.0)
            z = r + j * r * 1.75
            K.lathe([(Rj + r * math.cos(a), z + r * math.sin(a)) for a in [2 * math.pi * k / 6 for k in range(6)]], mats[n % len(mats)], seg, closed=True)
            n += 1


def net_cable():
    """A 5 m network cable in a tied coil, a plug on each end."""
    K = Kit()
    blue = mat('NetCable', (0.1, 0.35, 0.8), 0.5)
    blue2 = mat('NetCableShade', (0.08, 0.28, 0.68), 0.5)
    tie = mat('CableTie', (0.06, 0.06, 0.07), 0.6)
    plug = mat('Plug', (0.85, 0.87, 0.9), 0.3)
    r = 0.006
    coil(K, [0.085, 0.085 + 2 * r, 0.085 + 4 * r], 2, r, [blue, blue2])
    top = r + r * 1.75 + r
    for a in (0.6, 0.6 + math.pi):
        K.radial_box(a, 0.085 - r * 1.6, 0.085 + 6 * r, 0.014, -0.0005, top + 0.002, tie)
    for s, R in ((1, 0.085 + 5 * r), (-1, 0.085 - r)):                     # the two ends leave the coil and end in a plug
        pts = [(R * math.cos(a), R * math.sin(a) * s, top - r) for a in (2.0, 2.3)] + [(R * math.cos(2.6) - 0.02, (R * math.sin(2.6) + 0.02) * s, r), (-0.15, s * 0.05, r)]
        K.path(pts, r, blue, 6)
        K.bx((0.024, 0.012, 0.009), (-0.162, s * 0.05, 0.0055), plug)
    return K.done('cable')


def rope():
    """A coil of rope: four layers of wraps, tied in two places, the end lying loose."""
    K = Kit()
    a, b = mat('Rope', (0.78, 0.64, 0.42), 0.95), mat('RopeShade', (0.66, 0.52, 0.32), 0.95)
    r = 0.016
    coil(K, [0.11, 0.11 + 2 * r, 0.11 + 4 * r], 4, r, [a, b, a, a, b], 18)
    top = r + 3 * r * 1.75 + r
    for ang in (0.9, 0.9 + math.pi):
        K.radial_box(ang, 0.11 - r * 1.8, 0.11 + 6.2 * r, 0.03, -0.0005, top + 0.004, b)
    R = 0.11 + 5 * r
    K.path([(R * math.cos(t), R * math.sin(t), top - r) for t in (3.6, 3.9)] + [(-0.2, -0.13, r), (-0.26, -0.1, r), (-0.3, -0.03, r)], r, a, 6)
    return K.done('rope')


# -------------------------------------------------------------------------------------------------------------------------------------- docks

def dock(w, L, old, rail):
    """A dock section along y: piles, two stringers, planks across. old: grey, planks gone or lifting, the rail broken."""
    K, rnd = Kit(), random.Random(int(w * 10 + L))
    if old:
        woods = [mat('DockOld', (0.53, 0.47, 0.39), 0.95), mat('DockOldLight', (0.62, 0.56, 0.47), 0.95), mat('DockOldDark', (0.41, 0.36, 0.29), 0.95)]
        post_m = mat('DockPileOld', (0.36, 0.3, 0.23), 0.95)
    else:
        woods = [mat('DockNew', (0.72, 0.55, 0.34), 0.85), mat('DockNewLight', (0.79, 0.62, 0.4), 0.85), mat('DockNewDark', (0.64, 0.47, 0.28), 0.85)]
        post_m = mat('DockPile', (0.5, 0.36, 0.22), 0.9)
    steel = mat('DockSteel', (0.3, 0.3, 0.32), 0.5)
    top = 0.4
    n_bays = max(1, round(L / 3.0))
    for k in range(n_bays + 1):                                          # the piles
        y = -L / 2 + 0.12 + (L - 0.24) * k / n_bays
        for s in (-1, 1):
            lean = rnd.uniform(-0.04, 0.04) if old else 0.0
            hgt = top + (rnd.uniform(0.08, 0.3) if old else 0.22)
            K.tube((s * (w / 2 - 0.02), y, 0.0), (s * (w / 2 - 0.02) + lean, y + lean, hgt), 0.085, 0.075, post_m, 8, None, woods[2])
        K.bx((w - 0.1, 0.07, 0.14), (0, y, top - 0.025 - 0.14 - 0.07), woods[2])                             # a cross beam on each pair
    for s in (-1, 1):
        K.bx((0.07, L - 0.1, 0.14), (s * (w / 2 - 0.16), 0, top - 0.025 - 0.07), woods[2])
    pw, gap = 0.14, 0.008
    n = int((L - 0.02) / (pw + gap))
    y0 = -(n * (pw + gap) - gap) / 2 + pw / 2
    gone = set(rnd.sample(range(3, n - 3), 3 if L > 4 else 2)) if old else set()
    for k in range(n):
        if k in gone:
            continue
        y = y0 + k * (pw + gap)
        lift = Matrix.Rotation(rnd.uniform(-0.035, 0.035), 4, 'Y') if old and rnd.random() < 0.25 else None
        short = old and rnd.random() < 0.12
        ww = (w - 0.26) * (0.62 if short else 1.0)
        K.bx((ww, pw, 0.025), ((-(w - 0.26) * 0.19 if short else 0.0) + (rnd.uniform(-0.02, 0.02) if old else 0.0), y, top - 0.0125), rnd.choice(woods), lift)
    if rail:
        x = w / 2 - 0.17
        posts = [-L / 2 + 0.3 + (L - 0.6) * k / 4 for k in range(5)]
        for k, y in enumerate(posts):
            tilt = Matrix.Rotation(0.16, 4, 'Y') if old and k == 3 else None
            K.bx((0.07, 0.07, 0.95), (x + (0.07 if tilt else 0.0), y, top + 0.475), woods[0], tilt)
        for k in range(4):
            ya, yb = posts[k], posts[k + 1]
            if not (old and k == 2):
                K.bx((0.04, yb - ya + 0.07, 0.09), (x + 0.045, (ya + yb) / 2, top + 0.92), woods[1])
            else:                                                           # the broken rail: one end dropped to the deck
                K.bx((0.04, yb - ya, 0.09), (x + 0.045, (ya + yb) / 2, top + 0.47), woods[1], Matrix.Rotation(-0.72, 4, 'X'))
            if not (old and k in (1, 2)):
                K.bx((0.03, yb - ya + 0.07, 0.07), (x + 0.045, (ya + yb) / 2, top + 0.5), woods[1])
    if not old:                                                             # mooring cleats
        for y in ((-L * 0.3, L * 0.3) if L > 4 else (0.0,)):
            K.bx((0.03, 0.05, 0.03), (-w / 2 + 0.2, y, top + 0.015), steel)
            K.bx((0.03, 0.18, 0.02), (-w / 2 + 0.2, y, top + 0.04), steel)
    return K.done('dock')


# -------------------------------------------------------------------------------------------------------------------------------------- small

def stone():
    K = Kit()
    K.smooth = False
    rnd = random.Random(5)
    K.rock((0.26, 0.22, 0.19), mat('Stone', (0.52, 0.52, 0.5), 0.95), rnd, jitter=0.09)
    o = K.done('stone')
    shade = mat('StoneShade', (0.42, 0.42, 0.41), 0.95)
    lightm = mat('StoneLight', (0.62, 0.61, 0.58), 0.95)
    o.data.materials.append(shade)
    o.data.materials.append(lightm)
    for p in o.data.polygons:
        p.material_index = rnd.choice((0, 0, 0, 1, 2))
    return o


def mppt():
    """A wall-mount solar charge controller: finned heat sink, a faceplate with a display and buttons, a terminal cover with cable glands."""
    K = Kit()
    body = mat('ControllerBody', (0.1, 0.22, 0.42), 0.45)
    face = mat('ControllerFace', (0.13, 0.14, 0.16), 0.5)
    alu = mat('HeatSink', (0.62, 0.64, 0.66), 0.35)
    screen = mat('Display', (0.42, 0.82, 0.55), 0.2)
    button = mat('Button', (0.75, 0.76, 0.78), 0.5)
    w, d, h = 0.2, 0.07, 0.24
    K.bx((w, d * 0.55, h), (0, 0, h / 2), body)
    for k in range(11):                                                  # the fins at the back
        K.bx((0.004, d * 0.4, h * 0.86), (-w / 2 + 0.014 + (w - 0.028) * k / 10, d * 0.45, h * 0.52), alu)
    K.bx((w * 0.86, 0.006, h * 0.5), (0, -d * 0.275 - 0.003, h * 0.66), face)
    K.bx((w * 0.5, 0.004, h * 0.2), (-w * 0.12, -d * 0.275 - 0.007, h * 0.74), screen)
    for k in range(4):
        K.bx((0.02, 0.006, 0.014), (-w * 0.3 + k * 0.034, -d * 0.275 - 0.008, h * 0.5), button)
    K.bx((0.012, 0.005, 0.012), (w * 0.33, -d * 0.275 - 0.007, h * 0.78), mat('Led', (0.2, 0.9, 0.3), 0.3))
    K.bx((w * 0.92, d * 0.62, h * 0.26), (0, -0.002, h * 0.15), face)                                       # the terminal cover
    for k in range(4):
        x = -w * 0.33 + k * w * 0.22
        K.tube((x, -0.002, 0.0), (x, -0.002, 0.03), 0.014, 0.014, face, 8, face)
    for sx in (-1, 1):                                                   # mounting ears
        for z in (0.012, h - 0.012):
            K.bx((0.03, 0.004, 0.03), (sx * (w / 2 + 0.008), d * 0.2, z + (0.008 if z > h / 2 else -0.0)), alu)
    o = K.done('mppt')
    o.data.transform(T((0, 0, -min(v.co.z for v in o.data.vertices))))
    return o


def water_filter():
    """An inline cartridge filter: a head with two ports and a relief button, a ribbed blue sump below."""
    K = Kit()
    head = mat('FilterHead', (0.1, 0.1, 0.12), 0.5)
    sump = mat('FilterSump', (0.12, 0.36, 0.78), 0.3)
    brass = mat('Brass', (0.8, 0.62, 0.25), 0.35)
    r, hs = 0.05, 0.27
    prof = [(0.0, 0.0), (r * 0.5, 0.0), (r * 0.5, 0.02), (r * 0.9, 0.035)]
    for k in range(6):                                                   # grip ribs low on the sump
        z = 0.045 + k * 0.018
        prof += [(r, z), (r, z + 0.008), (r * 0.93, z + 0.012)]
    prof += [(r * 0.96, 0.17), (r * 0.96, hs)]
    K.lathe(prof, sump, 16)
    K.lathe([(r * 0.5, 0.0), (r * 0.5, 0.02)], head, 6)                  # the hex nut under it
    K.lathe([(r * 1.12, hs - 0.012), (r * 1.12, hs + 0.02), (r * 1.0, hs + 0.045), (r * 0.6, hs + 0.06), (0.0, hs + 0.06)], head, 16)
    for s in (-1, 1):
        K.tube((s * r * 0.8, 0, hs + 0.025), (s * (r + 0.035), 0, hs + 0.025), 0.02, 0.02, head, 8)
        K.tube((s * (r + 0.035), 0, hs + 0.025), (s * (r + 0.055), 0, hs + 0.025), 0.016, 0.016, brass, 8, None, brass)
    K.lathe([(0.009, hs + 0.06), (0.009, hs + 0.072), (0.0, hs + 0.072)], mat('ReliefButton', (0.85, 0.12, 0.1), 0.5), 8)
    return K.done('filter')


def tree_tap():
    """A spile for tapping maples: a tapered tube that goes into the tree, an open spout, a hook for the bucket."""
    K = Kit()
    alu = mat('Spile', (0.72, 0.73, 0.75), 0.3)
    dark = mat('SpileBore', (0.2, 0.2, 0.22), 0.6)
    z = 0.016
    K.tube((-0.05, 0, z), (0.0, 0, z), 0.0055, 0.009, alu, 8, dark)
    K.tube((0.0, 0, z), (0.012, 0, z), 0.012, 0.012, alu, 8, alu, alu)                                     # the shoulder that stops against the bark
    trough = [(-0.009, 0.004), (-0.007, -0.006), (0.0, -0.009), (0.007, -0.006), (0.009, 0.004), (0.006, 0.004), (0.0, -0.005), (-0.006, 0.004)]
    K.prism(trough, 0.045, T((0.012, 0, z)) @ Matrix.Rotation(0.12, 4, 'Y') @ RX @ Matrix.Rotation(math.pi / 2, 4, 'Z'), alu)
    K.path([(0.008, 0, z - 0.012), (0.012, 0, z - 0.024) if False else (0.012, 0.0, 0.004), (0.022, 0, 0.0025), (0.028, 0, 0.008)], 0.0022, alu, 5)
    return K.done('tap')


def bait_tin():
    """An open tin of earthworms: dark soil, a few worms on it, the lid leaning against the side."""
    K = Kit()
    tin = mat('Tin', (0.7, 0.71, 0.72), 0.3)
    labelm = mat('TinLabel', (0.2, 0.5, 0.3), 0.7)
    soil = mat('Soil', (0.2, 0.14, 0.09), 0.95)
    worm = mat('Worm', (0.78, 0.45, 0.42), 0.5)
    r, h = 0.04, 0.055
    K.lathe([(0.0, 0.0), (r, 0.0), (r, h), (r + 0.002, h), (r + 0.002, h + 0.003), (r - 0.002, h + 0.003), (r - 0.002, h * 0.75)], tin, 14)
    K.lathe([(r + 0.0006, h * 0.15), (r + 0.0006, h * 0.8)], labelm, 14)
    K.lathe([(r - 0.002, h * 0.75), (r * 0.5, h * 0.82), (0.0, h * 0.8)], soil, 14)
    for a0, R in ((0.3, 0.02), (2.6, 0.016), (4.4, 0.024)):
        K.path([((R + 0.004 * math.sin(k * 2.1)) * math.cos(a0 + k * 0.42), (R + 0.004 * math.sin(k * 2.1)) * math.sin(a0 + k * 0.42), h * 0.82 + 0.003 + 0.002 * (k % 2))
                for k in range(6)], 0.0032, worm, 5)
    K.lathe([(0.0, 0.0), (r + 0.003, 0.0), (r + 0.003, 0.006), (r, 0.006), (0.0, 0.003)], tin, 14, T((r + 0.028, 0, r * 0.93)) @ Matrix.Rotation(math.radians(68), 4, 'Y'))
    return K.done('bait')


# ------------------------------------------------------------------------------------------------------------------------------------- output

HAY, STRAW = (0.58, 0.6, 0.3), (0.86, 0.72, 0.36)
ITEMS = {
    'mat_bale_hay_square': (lambda: bale_square(HAY, 1), 'A twine-tied square bale: flake seams, loose stalks, two strings.'),
    'mat_bale_straw_square': (lambda: bale_square(STRAW, 2), 'A twine-tied square bale: flake seams, loose stalks, two strings.'),
    'mat_bale_hay_round': (lambda: bale_round(HAY, 3), 'A net-wrapped round bale lying on its side, the roll showing on the ends.'),
    'mat_bale_straw_round': (lambda: bale_round(STRAW, 4), 'A net-wrapped round bale lying on its side, the roll showing on the ends.'),
    'mat_bale_silage_round': (lambda: bale_round(HAY, 5, wrap=(0.93, 0.94, 0.93)), 'A round bale sealed in white plastic wrap.'),
    'mat_wood_logs_stack': (logs_stack, 'A squared stack of mixed logs between four stakes.'),
    'lumber_bundle_2x4_small': (lambda: lumber_bundle(0.089, 0.038, 2.4, 5, 3), '15 boards of 2.4 m, strapped, on three bearers.'),
    'lumber_bundle_2x4_large': (lambda: lumber_bundle(0.089, 0.038, 3.6, 5, 5), '25 boards of 3.6 m, strapped, on three bearers.'),
    'lumber_bundle_2x10_small': (lambda: lumber_bundle(0.235, 0.038, 2.4, 2, 5), '10 boards of 2.4 m, strapped, on three bearers.'),
    'lumber_bundle_2x10_large': (lambda: lumber_bundle(0.235, 0.038, 3.6, 2, 8), '16 boards of 3.6 m, strapped, on three bearers.'),
    'fuel_propane_1_5l': (lambda: propane(0.055, 0.2, (0.15, 0.45, 0.4), collar=False), 'A small camping cylinder.'),
    'fuel_propane_18l': (lambda: propane(0.152, 0.36, (0.92, 0.92, 0.9)), 'A grill-size cylinder with a collar guard and foot ring.'),
    'fuel_propane_36l': (lambda: propane(0.152, 0.64, (0.92, 0.92, 0.9)), 'A tall cylinder with a collar guard and foot ring.'),
    # the two big propane tanks are one look (white capsule on cradles, a PROPANE sticker); the two bulk fuel tanks are another (red drum with a
    # white band on a black skid, hose and nozzle, a DIESEL FUEL sticker). The stickers are painted by tools/case_labels.py.
    'fuel_tank_propane_1900l': (lambda: propane_tank_big(0.48, 3.0), 'A long white capsule on two cradle feet, a PROPANE sticker on each side.'),
    'fuel_tank_propane_3800l': (lambda: propane_tank_big(0.52, 4.9), 'The same white capsule, longer: twice the capacity. A PROPANE sticker on each side.'),
    'fuel_tank_bulk_small': (lambda: bulk_tank(0.42, 1.9, (0.8, 0.1, 0.07), (0.93, 0.93, 0.9)), 'A red drum with a white band on a skid, hose and nozzle, a DIESEL FUEL sticker on each side.'),
    'fuel_tank_bulk_large': (lambda: bulk_tank(0.6, 3.2, (0.8, 0.1, 0.07), (0.93, 0.93, 0.9)), 'A red drum with a white band on a skid, hose and nozzle, a DIESEL FUEL sticker on each side.'),
    'building_paint_interior_wall': (lambda: pail((0.9, 0.88, 0.8)), 'A 19 L plastic pail with a lid and a wire handle.'),
    'tool_bucket_empty': (lambda: bucket(False), 'A galvanized bucket, empty.'),
    'water_bucket_water': (lambda: bucket(True), 'A galvanized bucket, full of water.'),
    'electricity_power_pole_wood': (lambda: pole_wood(True), 'A 9 m wooden pole with a crossarm, braces and insulators.'),
    'electricity_wooden_utility_pole': (lambda: pole_wood(False), 'A bare 9 m wooden pole: cap, steps and a tag, no crossarm.'),
    'electricity_power_pole_metal': (pole_metal, 'A 9 m eight-sided steel pole on a bolted base plate, with a steel arm and insulators.'),
    'water_pipe': (water_pipe, 'A 3 m length of blue water pipe.'),
    'net_cable': (net_cable, 'A 5 m network cable in a tied coil.'),
    'mat_rope': (rope, 'A tied coil of rope.'),
    'dock_small_new': (lambda: dock(1.8, 3.0, False, False), 'A 1.8 m by 3 m dock section on four piles.'),
    'dock_small_old': (lambda: dock(1.8, 3.0, True, False), 'A weathered 1.8 m by 3 m dock section: grey planks, some gone or lifting.'),
    'dock_large_new': (lambda: dock(2.4, 6.0, False, True), 'A 2.4 m by 6 m dock section on six piles, a railing down one side.'),
    'dock_large_old': (lambda: dock(2.4, 6.0, True, True), 'A weathered 2.4 m by 6 m dock section: planks gone, the railing broken.'),
    'mat_stone': (stone, 'A rough field stone.'),
    'electricity_mpptcontroller': (mppt, 'A wall-mount controller: heat sink fins, display, buttons, cable glands.'),
    'water_filter': (water_filter, 'An inline cartridge filter: a head with two ports over a ribbed sump.'),
    'tool_tap': (tree_tap, 'A spile: a tapered tube, an open spout and a bucket hook.'),
    'fishing_bait': (bait_tin, 'An open tin of soil and earthworms, the lid beside it.'),
}
for _s in SPECIES:
    ITEMS['mat_log_' + _s] = ((lambda s=_s: single_log(s)), 'A 1.2 m cut log lying on its side.')
for _s in ('birch', 'maple', 'oak', 'pine'):
    for _n, (_size, _base, _rows, _r, _len) in enumerate((('small', 4, 3, 0.11, 0.6), ('medium', 6, 4, 0.115, 0.8), ('large', 9, 4, 0.12, 1.0))):
        ITEMS['mat_pile_logs_%s_%s' % (_s, _size)] = ((lambda s=_s, b=_base, r=_rows, rr=_r, ln=_len, n=_n: log_pile(s, b, r, rr, ln, n + 1)),
                                                      '%d cut logs stacked in a pyramid.' % sum(_base - j for j in range(_rows)))


def save(path, text):
    """Writes a file, trying again when Windows refuses for a moment (something else has the file open: the kit, a scanner)."""
    import time
    for attempt in range(40):
        try:
            with open(path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(text)
            return
        except OSError:
            if attempt == 39:
                raise
            time.sleep(0.25)


def write(item, obj, note):
    found = glob.glob(os.path.join(ROOT, 'assets', '*', item, item + '.json'))
    if not found:
        print('SKIP (not in the kit)', item)
        return
    path = found[0]
    folder = os.path.dirname(path)
    pts = [v.co for v in obj.data.vertices]
    dims = [round(max(p[i] for p in pts) - min(p[i] for p in pts), 3) for i in range(3)]
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=os.path.join(folder, item + '.glb'), export_format='GLB', use_selection=True, export_yup=True)
    m = json.load(open(path, encoding='utf-8'))
    m['models'] = [{'file': item + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims[0], 'y': dims[2], 'z': dims[1]}, 'triangles': tris}]
    m['category_fields'] = dict(m.get('category_fields') or {}, dimensions_m={'width': round(dims[0], 2), 'depth': round(dims[1], 2), 'height': round(dims[2], 2)})
    save(path, json.dumps(m, indent=2))
    save(os.path.join(folder, 'README.md'),
         '# %s\n\n%s\n\nProcedural model (tools/make_simple_props.py), %d triangles, %.2f x %.2f x %.2f m. %s\n' % (m['name'], m.get('description', ''), tris, *dims, note))
    print('prop', item, '|', tris, 'tris |', dims)


def main():
    only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for item, (build, note) in ITEMS.items():
        if only and item not in only:
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        try:
            write(item, build(), note)
        except Exception as e:                                          # one bad builder does not stop the rest
            import traceback
            traceback.print_exc()
            print('FAILED', item, e)


if __name__ == '__main__':
    main()
