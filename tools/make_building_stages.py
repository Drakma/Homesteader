"""
Builds the stage models of every building structure that is not the cabin or the starter house, in headless Blender (free, local, low-poly):
chicken coop, barn, stable, farmhouse, large log cabin, large metal garage, 3-bay truck garage and greenhouse. Same conventions as the cabin
and the house (docs/STRUCTURE_STAGES_GUIDE.md: metres, pivot at the footprint centre, front = -Y, FrontMarker, named parts and materials),
and they reuse the starter house's wall / trim / roof helpers (tools/make_house_stages.py). What is new here:

  * a per-building config (CONFIGS) instead of constants: footprint, wall height, porch, cladding (siding, log, metal), the openings of
    each wall, big doors (barn doors, roll-up doors), the chimney, the colours;
  * INTERIOR PARTITIONS with doorways: stud walls in the framing stage, drywall in the walls stage, painted and cased with real interior
    doors in the exterior / finishing stages. Interior doors are objects "DoorHinge_<n>" > "DoorLeaf_<n>": the game swings them like the front
    door (ConstructionSite.cs). Half-height partitions make stall walls;
  * the stage manifests are created from the cabin's when missing, and the group manifest becomes five stages (finishings) for the houses.

    blender --background --python tools/make_building_stages.py -- barn stable
    (no names: every building in CONFIGS)
"""
import copy
import json
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_structure_stages as base  # noqa: E402
import make_house_stages as hs  # noqa: E402

Builder = base.Builder
ROOT = base.ROOT
STRUCTURES = base.STRUCTURES
colour = hs.colour

T_SIDING, T_SHEATH, T_STUD = hs.T_SIDING, hs.T_SHEATH, hs.T_STUD
DOOR_W, DOOR_H = hs.DOOR_W, hs.DOOR_H
IN = T_SIDING + T_SHEATH + T_STUD + 0.02          # a wall's thickness including its interior layer
PT = 0.12                                          # partition thickness
IDOOR_W, IDOOR_H = 0.9, 2.05


def win(u, w=0.95, h=1.25, sill=0.9):
    return (u - w / 2, u + w / 2, sill, sill + h)


# ------------------------------------------------------------------ the buildings

CONFIGS = {
    'chicken_coop': dict(
        name='Chicken Coop', w=3.0, d=4.0, wall_h=2.5, h_total=3.6, found_h=0.2, ov=0.3, stages=4, style='siding',
        palette=dict(siding=(0.62, 0.72, 0.58), trim=(0.95, 0.95, 0.92), shingle=(0.36, 0.24, 0.2), shingle_dark=(0.26, 0.17, 0.14)),
        door_x=0.55,
        openings=dict(front=[win(-0.75, 0.6, 0.5, 1.5)], back=[], left=[win(-0.6, 0.6, 0.5, 1.5)], right=[win(-0.6, 0.6, 0.5, 1.5)]),
        partitions=[dict(axis='y', pos=0.5, lo=None, hi=None, h=None, doors=[(-0.55, 0.55)])]),
    'barn': dict(
        name='Barn', w=10.0, d=14.0, wall_h=3.4, h_total=7.6, found_h=0.26, ov=0.45, stages=4, style='siding', rib_course=0.3,
        palette=dict(siding=(0.62, 0.17, 0.13), trim=(0.94, 0.93, 0.9), shingle=(0.3, 0.3, 0.32), shingle_dark=(0.22, 0.22, 0.24), door=(0.55, 0.15, 0.12)),
        door_x=-3.6, slide_doors=True, big=[dict(u=(-1.6, 1.6), h=3.1, kind='barn')],
        openings=dict(front=[], back=[win(-2.2, 0.9, 0.9, 1.7), win(2.2, 0.9, 0.9, 1.7)],
                      left=[win(-3.5, 0.9, 0.9, 1.7), win(0, 0.9, 0.9, 1.7), win(3.5, 0.9, 0.9, 1.7)],
                      right=[win(-3.5, 0.9, 0.9, 1.7), win(0, 0.9, 0.9, 1.7), win(3.5, 0.9, 0.9, 1.7)]),
        partitions=[dict(axis='x', pos=2.2, lo=2.8, hi=None, h=None, doors=[]),
                    dict(axis='y', pos=2.8, lo=2.2, hi=None, h=None, doors=[(3.1, 4.2)]),
                    dict(axis='x', pos=-2.2, lo=-3.5, hi=3.0, h=1.5, doors=[(-2.7, -1.5), (0.1, 1.3)], door_h=1.3, door_w=1.2),
                    dict(axis='y', pos=-3.5, lo=None, hi=-2.2, h=1.7, doors=[]),
                    dict(axis='y', pos=-0.9, lo=None, hi=-2.2, h=1.7, doors=[]),
                    dict(axis='y', pos=3.0, lo=None, hi=-2.2, h=1.7, doors=[])]),
    'stable': dict(
        name='Stable', w=8.0, d=14.0, wall_h=3.0, h_total=5.6, found_h=0.26, ov=0.4, stages=4, style='siding', rib_course=0.3,
        palette=dict(siding=(0.55, 0.38, 0.24), trim=(0.94, 0.92, 0.86), shingle=(0.22, 0.28, 0.24), shingle_dark=(0.15, 0.2, 0.17), door=(0.35, 0.22, 0.14)),
        door_x=-2.6, slide_doors=True, big=[dict(u=(-1.3, 1.3), h=2.9, kind='barn')],
        openings=dict(front=[], back=[win(0, 0.9, 0.9, 1.6)],
                      left=[win(y, 0.9, 0.9, 1.6) for y in (-1.85, 1.45, 4.75)], right=[win(y, 0.9, 0.9, 1.6) for y in (-1.85, 1.45, 4.75)]),
        partitions=([dict(axis='x', pos=s * 1.5, lo=-3.5, hi=6.4, h=1.4, doors=[(c - 0.6, c + 0.6) for c in (-1.85, 1.45, 4.75)], door_h=1.25, door_w=1.2)
                     for s in (-1, 1)] +
                    [dict(axis='y', pos=y, lo=lo, hi=hi, h=1.9, doors=[]) for y in (-3.5, -0.2, 3.1, 6.4) for lo, hi in ((None, -1.5), (1.5, None))])),
    'farmhouse': dict(
        name='Farmhouse', rib_course=0.5, w=10.0, d=12.0, wall_h=2.6, h_total=6.6, found_h=0.3, ov=0.4, porch=2.0, stages=5, style='siding', chimney=('left', -1.8),
        palette=dict(siding=(0.93, 0.92, 0.88), trim=(0.97, 0.97, 0.95), shutter=(0.16, 0.3, 0.26), shingle=(0.3, 0.27, 0.28), shingle_dark=(0.2, 0.18, 0.19),
                     door=(0.2, 0.34, 0.3), door_panel=(0.16, 0.28, 0.25)),
        door_x=0.0, shutters=True,
        openings=dict(front=[win(-3.0), win(3.0)], back=[win(-3.2), win(3.2)],
                      left=[win(-3.0), win(-0.6), win(2.5)], right=[win(-2.5), win(2.5)]),
        partitions=[dict(axis='y', pos=0.0, lo=None, hi=None, h=None, doors=[(-4.0, -2.9), (-0.55, 0.55), (2.9, 4.0)]),
                    dict(axis='x', pos=-1.9, lo=0.0, hi=None, h=None, doors=[]),
                    dict(axis='x', pos=1.9, lo=0.0, hi=None, h=None, doors=[]),
                    dict(axis='x', pos=1.0, lo=None, hi=0.0, h=None, doors=[], open_doors=[(-3.0, -1.0)])]),
    'large_log_cabin': dict(
        name='Large Log Cabin', log_course=0.26, w=9.0, d=11.0, wall_h=2.9, h_total=6.2, found_h=0.3, ov=0.45, porch=1.6, stages=5, style='log', chimney=('left', -1.95),
        palette=dict(log=(0.42, 0.27, 0.14), trim=(0.55, 0.38, 0.22), shingle=(0.3, 0.2, 0.16), shingle_dark=(0.2, 0.13, 0.1), door=(0.3, 0.19, 0.1), door_panel=(0.25, 0.15, 0.08)),
        door_x=0.0,
        openings=dict(front=[win(-2.8), win(2.8)], back=[win(-2.5), win(2.5)],
                      left=[win(-3.0), win(-0.9), win(3.0)], right=[win(-2.5), win(3.0)]),
        partitions=[dict(axis='y', pos=0.8, lo=None, hi=None, h=None, doors=[(-3.3, -2.2), (2.2, 3.3)]),
                    dict(axis='x', pos=0.0, lo=0.8, hi=None, h=None, doors=[])]),
    'house_garage': dict(
        # a medium house (living room and kitchen in front, two rooms behind) with a one-car-wide garage attached on its right under the same roof
        name='House With Garage', rib_course=0.3, w=14.0, d=9.0, wall_h=2.6, h_total=6.0, found_h=0.26, ov=0.4, stages=5, style='siding', ridge_x=True,
        palette=dict(siding=(0.78, 0.82, 0.84), trim=(0.96, 0.96, 0.94), shingle=(0.3, 0.3, 0.34), shingle_dark=(0.21, 0.21, 0.24),
                     door=(0.55, 0.2, 0.17), door_panel=(0.47, 0.16, 0.14)),
        door_x=-3.0, big=[dict(u=(2.1, 6.4), h=2.4, kind='roll')],
        openings=dict(front=[win(-5.5), win(-0.4)], back=[win(-5.5), win(-2.5), win(0.0), win(4.2, 0.9, 1.1, 1.2)],
                      left=[win(-2.2), win(2.0)], right=[win(0.0, 0.9, 1.1, 1.2)]),
        partitions=[dict(axis='x', pos=1.4, lo=None, hi=None, h=None, doors=[(1.0, 2.0)]),
                    dict(axis='y', pos=0.5, lo=None, hi=1.4, h=None, doors=[(-5.8, -4.8), (-1.9, -0.9)]),
                    dict(axis='x', pos=-3.0, lo=0.5, hi=None, h=None, doors=[])]),
    'large_metal_garage': dict(
        name='Large Metal Garage', w=9.0, d=12.0, wall_h=3.6, h_total=5.6, found_h=0.22, ov=0.3, stages=4, style='metal',
        palette=dict(siding=(0.72, 0.74, 0.76), trim=(0.88, 0.88, 0.86), shingle=(0.34, 0.37, 0.42), shingle_dark=(0.26, 0.28, 0.32), door=(0.6, 0.62, 0.64)),
        door_x=-3.2, big=[dict(u=(-0.4, 3.6), h=3.0, kind='roll')],
        openings=dict(front=[], back=[win(0, 1.2, 0.7, 2.3)], left=[win(-2.5, 1.2, 0.7, 2.3), win(2.5, 1.2, 0.7, 2.3)], right=[win(-2.5, 1.2, 0.7, 2.3), win(2.5, 1.2, 0.7, 2.3)]),
        partitions=[dict(axis='x', pos=-1.2, lo=2.0, hi=None, h=None, doors=[]),
                    dict(axis='y', pos=2.0, lo=None, hi=-1.2, h=None, doors=[(-3.0, -1.9)])]),
    '3_bay_truck_garage': dict(
        name='3-Bay Truck Garage', w=16.0, d=10.0, wall_h=4.2, h_total=6.8, found_h=0.22, ov=0.3, stages=4, style='metal',
        palette=dict(siding=(0.8, 0.8, 0.78), trim=(0.5, 0.52, 0.55), shingle=(0.3, 0.33, 0.38), shingle_dark=(0.22, 0.25, 0.3), door=(0.7, 0.72, 0.74)),
        door_x=-7.3, big=[dict(u=(-5.4, -1.8), h=3.6, kind='roll'), dict(u=(-1.0, 2.6), h=3.6, kind='roll'), dict(u=(3.4, 7.0), h=3.6, kind='roll')],
        openings=dict(front=[], back=[win(-4, 1.2, 0.7, 2.8), win(0, 1.2, 0.7, 2.8), win(4, 1.2, 0.7, 2.8)],
                      left=[win(-1.5, 1.2, 0.7, 2.8), win(2.0, 1.2, 0.7, 2.8)], right=[win(-1.5, 1.2, 0.7, 2.8), win(2.0, 1.2, 0.7, 2.8)]),
        partitions=[dict(axis='x', pos=4.4, lo=2.0, hi=None, h=None, doors=[]),
                    dict(axis='y', pos=2.0, lo=4.4, hi=None, h=None, doors=[(5.3, 6.4)])]),
    'struct_shed': dict(
        name='Tool Shed', w=4.0, d=5.0, wall_h=2.5, h_total=3.7, found_h=0.2, ov=0.3, stages=4, style='siding', rib_course=0.24,
        palette=dict(siding=(0.52, 0.6, 0.66), trim=(0.95, 0.95, 0.93), shingle=(0.3, 0.22, 0.2), shingle_dark=(0.22, 0.16, 0.14), door=(0.35, 0.22, 0.14), door_panel=(0.3, 0.18, 0.1)),
        door_x=0.9,
        openings=dict(front=[win(-0.9, 0.7, 0.8, 1.4)], back=[win(0, 0.7, 0.8, 1.4)], left=[win(0.2, 0.7, 0.8, 1.4)], right=[win(0.2, 0.7, 0.8, 1.4)]),
        partitions=[dict(axis='y', pos=1.0, lo=None, hi=None, h=None, doors=[(-0.55, 0.55)])]),
    'struct_woodshed': dict(
        name='Woodshed', w=5.0, d=3.0, wall_h=2.5, h_total=3.7, found_h=0.16, ov=0.35, stages=4, style='siding', rib_course=0.24, open_front=True,
        palette=dict(siding=(0.5, 0.36, 0.24), trim=(0.62, 0.45, 0.3), shingle=(0.24, 0.26, 0.28), shingle_dark=(0.16, 0.17, 0.19)),
        openings=dict(front=[], back=[], left=[], right=[]),
        partitions=[dict(axis='x', pos=0.0, lo=None, hi=None, h=None, doors=[], open_doors=[(-0.2, 0.9)])]),
    'greenhouse': dict(
        name='Greenhouse', w=4.0, d=8.0, wall_h=2.4, h_total=3.6, found_h=0.18, ov=0.2, stages=4, style='glass',
        palette=dict(siding=(0.85, 0.85, 0.82), trim=(0.82, 0.84, 0.86), door=(0.82, 0.84, 0.86)),
        door_x=0.0,
        openings=dict(front=[], back=[], left=[], right=[]),
        partitions=[dict(axis='y', pos=2.5, lo=None, hi=None, h=None, doors=[(-0.55, 0.55)])]),
}


# ------------------------------------------------------------------ context

class BCtx:
    """The numbers every builder shares (the same names as the starter house's Ctx, so its helpers work on this)."""

    def __init__(self, cfg, h_total, found_h):
        self.cfg = cfg
        self.w, self.d, self.h_total = cfg['w'], cfg['d'], h_total
        self.z0 = found_h + 0.04
        self.top = self.z0 + cfg['wall_h']
        self.yh0 = -self.d / 2 + cfg.get('porch', 0.0)
        self.ov = cfg.get('ov', 0.35)
        self.zr = h_total - 0.2
        self.zw = self.top + (0.04 if cfg.get('style') == 'glass' else 0.40)
        self.slope = (self.zr - self.zw) / (self.w / 2 - 0.04)
        self.eave_z = self.zw - self.slope * self.ov
        self.half = self.w / 2
        self.dx = cfg.get('door_x', 0.0)
        front = [] if cfg.get('open_front') else [(self.dx - DOOR_W / 2, self.dx + DOOR_W / 2, 0.0, DOOR_H)]
        for g in cfg.get('big', []):
            front.append((g['u'][0], g['u'][1], 0.0, g['h']))
        front += cfg['openings'].get('front', [])
        self.openings = {'front': front, 'back': list(cfg['openings'].get('back', [])),
                         'left': list(cfg['openings'].get('left', [])), 'right': list(cfg['openings'].get('right', []))}
        self.style = cfg.get('style', 'siding')
        self.open_front = bool(cfg.get('open_front'))
        self.walls = ('back', 'left', 'right') if self.open_front else ('front', 'back', 'left', 'right')
        self.rib = cfg.get('rib_course', 0.24)
        self.log_course = cfg.get('log_course', 0.2)
        self.parts = [self.resolve(p) for p in cfg.get('partitions', [])]

    def inner(self, axis):
        """The clear span inside the walls along an axis ('x' across, 'y' front to back)."""
        if axis == 'x':
            return -self.w / 2 + IN, self.w / 2 - IN
        return self.yh0 + IN, self.d / 2 - IN

    def resolve(self, p):
        q = dict(p)
        # a partition along y (axis 'y') runs across x; its ends are x values, the doors too
        lo, hi = self.inner('x' if p['axis'] == 'y' else 'y')
        q['lo'] = lo if p.get('lo') is None else p['lo']
        q['hi'] = hi if p.get('hi') is None else p['hi']
        q['h'] = (self.top - self.z0) if p.get('h') is None else p['h']
        q['door_h'] = min(p.get('door_h', IDOOR_H), q['h'] - 0.05) if q['h'] > 2.0 else q['h']   # a half wall's door is the wall's full height
        q['door_w'] = p.get('door_w', IDOOR_W)
        return q


# ------------------------------------------------------------------ a roof whose ridge runs left to right (cfg ridge_x)
#
# The roof code is written for a ridge that runs front to back (gables on the front and back walls). For a building whose ridge runs the other way
# the roof pieces are built in a context with the footprint turned (ridge front to back there), then turned back a quarter turn into place:
# the gables of that context land on the left and right walls and its slopes face the front and back.

def roof_ctx(c):
    """The context the roof pieces are built in: the building's own, or the turned one when the ridge runs left to right."""
    if not c.cfg.get('ridge_x'):
        return c
    cfg2 = dict(c.cfg)
    cfg2.update(w=c.d, d=c.w, porch=0.0, big=[], partitions=[], door_x=0.0, open_front=False, openings=dict(front=[], back=[], left=[], right=[]))
    return BCtx(cfg2, c.h_total, c.z0 - 0.04)


def merge_turned(src, dst):
    """Copies the geometry of builder `src` into `dst`, turned a quarter turn about the vertical axis ((x, y) -> (y, -x): the context's front gable lands on the left)."""
    for f in src.bm.faces:
        vs = [dst.bm.verts.new((v.co.y, -v.co.x, v.co.z)) for v in f.verts]
        try:
            nf = dst.bm.faces.new(vs)
        except ValueError:
            continue
        nf.material_index = dst.mat_index(src.mats[f.material_index])
    src.bm.free()


# ------------------------------------------------------------------ shared pieces

PB = None   # the separate "Porch" object (posts, beam, railing) while a stage is built
FB = None
glass_builder = None


def foundation(b, c, M):
    b = FB if FB is not None else b
    w, d = c.w, c.d
    h = c.z0 - 0.04
    conc, dark = M['concrete'], M['concrete_dark']
    b.box(-w / 2, w / 2, -d / 2, d / 2, 0.0, h, conc)
    b.box(-w / 2 - 0.06, w / 2 + 0.06, -d / 2 - 0.06, d / 2 + 0.06, 0.0, h * 0.45, dark)
    for x0, x1, y0, y1 in ((-w / 2, w / 2, -d / 2, -d / 2 + 0.06), (-w / 2, w / 2, d / 2 - 0.06, d / 2),
                           (-w / 2, -w / 2 + 0.06, -d / 2, d / 2), (w / 2 - 0.06, w / 2, -d / 2, d / 2)):
        b.box(x0, x1, y0, y1, h, h + 0.04, conc)
    # steps at the personal door (the porch's, or straight onto the ground)
    sw = 0.8 if c.cfg.get('porch') else 0.75
    sx = c.dx if not c.cfg.get('porch') else 0.0
    for k in range(0 if c.open_front else (3 if c.cfg.get('porch') else 2)):
        b.box(sx - sw, sx + sw, -d / 2 - 0.3 * (k + 1), -d / 2, 0.0, h * (1 - (k + 1) * 0.28), conc)
    # anchor bolts along the front and back, and rebar stubs along the sides
    n = max(3, int(w / 2.4))
    for k in range(n):
        u = -w / 2 + 0.6 + (w - 1.2) * k / max(1, n - 1)
        b.box(u - 0.012, u + 0.012, c.yh0 + 0.08, c.yh0 + 0.10, h, h + 0.12, M['steel'])
        b.box(u - 0.012, u + 0.012, d / 2 - 0.10, d / 2 - 0.08, h, h + 0.12, M['steel'])
    n = max(3, int((d - c.yh0 - d / 2) / 2.4)) if False else max(3, int(d / 3.0))
    for k in range(n):
        v = c.yh0 + 0.8 + (d / 2 - c.yh0 - 1.6) * k / max(1, n - 1)
        b.box(-w / 2 + 0.08, -w / 2 + 0.10, v - 0.012, v + 0.012, h, h + 0.12, M['steel'])
        b.box(w / 2 - 0.10, w / 2 - 0.08, v - 0.012, v + 0.012, h, h + 0.12, M['steel'])
    return h


def pbox(b, p, u0, u1, t0, t1, za, zb, m):
    """A box on a partition: u along it, t across it (from its centre line), z absolute."""
    if p['axis'] == 'y':
        b.box(u0, u1, p['pos'] + t0, p['pos'] + t1, za, zb, m)
    else:
        b.box(p['pos'] + t0, p['pos'] + t1, u0, u1, za, zb, m)


def door_gaps(p, pad=0.0):
    gaps = []
    for u0, u1 in p.get('doors', []) + p.get('open_doors', []):
        gaps.append((u0 - pad, u1 + pad))
    return sorted(gaps)


def open_front_frame(b, c, M):
    """The open front of a woodshed: corner and middle posts and a beam across the top."""
    w, d = c.w, c.d
    xs = [-w / 2 + 0.12, w / 2 - 0.12] + [-w / 2 + (w / (int(w / 1.6) + 1)) * k for k in range(1, int(w / 1.6) + 1)]
    for x in xs:
        b.box(x - 0.08, x + 0.08, -d / 2 + 0.02, -d / 2 + 0.2, c.z0, c.top + 0.1, M['lumber'])
    b.box(-w / 2, w / 2, -d / 2, -d / 2 + 0.22, c.top, c.top + 0.26, M['lumber'])


def woodpile(b, c, M, x0, x1, rows=5):
    """Split logs stacked in rows along y between x0 and x1, against the back wall."""
    y0, y1 = -c.d / 2 + 0.5, c.d / 2 - IN - 0.05
    r = 0.09
    per = max(1, int((x1 - x0) / (2 * r)))
    for row in range(rows):
        n = per - (row % 2)
        for k in range(n):
            x = x0 + r * (1 + (row % 2)) + k * 2 * r
            z = c.z0 + 0.04 + r + row * 1.7 * r
            b.log((x, y0, z), (x, y1, z), r * 0.95, M['logend'], sides=6)


def partition_framing(b, c, M, p):
    z0 = c.z0
    top = z0 + p['h']
    gaps = door_gaps(p)
    for u0, u1 in hs.pieces(p['lo'], p['hi'], gaps, 0.03):
        pbox(b, p, u0, u1, -0.045, 0.045, z0, z0 + 0.04, M['lumber'])                 # bottom plate
    headless = p['door_h'] >= p['h'] - 0.12                                            # a door the full height of the wall has no header: the plate stops at it
    for u0, u1 in (hs.pieces(p['lo'], p['hi'], gaps, 0.0) if headless else [(p['lo'], p['hi'])]):
        pbox(b, p, u0, u1, -0.045, 0.045, top - 0.09, top, M['lumber'])                # top plate
    n = int((p['hi'] - p['lo']) / (0.4 if p['h'] > 2.0 else 0.6)) + 1
    for k in range(n):
        u = p['lo'] + 0.02 + (p['hi'] - p['lo'] - 0.04) * k / max(1, n - 1)
        if any(g0 - 0.03 < u < g1 + 0.03 for g0, g1 in gaps):
            continue
        pbox(b, p, u - 0.02, u + 0.02, -0.045, 0.045, z0 + 0.04, top - 0.09, M['lumber'])
    for g0, g1 in gaps:                                                                # king studs and a header at each doorway
        pbox(b, p, g0 - 0.05, g0, -0.045, 0.045, z0 + 0.04, top - 0.09, M['lumber'])
        pbox(b, p, g1, g1 + 0.05, -0.045, 0.045, z0 + 0.04, top - 0.09, M['lumber'])
        dh = p['door_h']
        if z0 + dh + 0.1 < top - 0.09:
            pbox(b, p, g0 - 0.05, g1 + 0.05, -0.045, 0.045, z0 + dh, z0 + dh + 0.1, M['lumber'])


def partition_wall(b, c, M, p, finished=False, finishings=False):
    """The drywalled partition: one slab either side the doorways (a lintel above them)."""
    z0 = c.z0
    top = z0 + p['h']
    mat = M['interior']
    gaps = door_gaps(p)
    for u0, u1 in hs.pieces(p['lo'], p['hi'], gaps, 0.02):
        pbox(b, p, u0, u1, -PT / 2, PT / 2, z0, top, mat)
    dh = p['door_h']
    for g0, g1 in gaps:
        if top - (z0 + dh) > 0.03 and p['h'] > 2.0:     # a lintel only on a full height wall: over a stall door it would be a bar at head height
            pbox(b, p, g0, g1, -PT / 2, PT / 2, z0 + dh, top, mat)
    if finishings:                                                                     # baseboards each side
        for u0, u1 in hs.pieces(p['lo'], p['hi'], gaps, 0.02):
            pbox(b, p, u0, u1, -PT / 2 - 0.012, PT / 2 + 0.012, z0, z0 + 0.12, M['trim'])


INTERIOR_DOORS = []   # (hinge, leaf) pairs of the stage being built


def partition_run(p, gaps, g0, g1, direction):
    """The free wall length beyond a doorway on one side along its partition (casings, the next doorway and the wall end are in the way)."""
    if direction > 0:
        lim = p['hi'] - 0.05
        for a, b in gaps:
            if a >= g1 - 1e-6:
                lim = min(lim, a - 0.07)
        return max(0.0, lim - (g1 + 0.07))
    lim = p['lo'] + 0.05
    for a, b in gaps:
        if b <= g0 + 1e-6:
            lim = max(lim, b + 0.07)
    return max(0.0, (g0 - 0.07) - lim)


def slide_node(name, origin, offset, build):
    """A sliding leaf: an empty `name` at `origin` (the leaf's closed place) with the leaf mesh as its child, built in coordinates relative to the
    origin, and an empty 'SlideTo...' child whose position is how far the game slides the leaf when it opens (ConstructionSite.cs)."""
    leaf = Builder(name + '_Leaf')
    build(leaf)
    obj = leaf.finish()
    node = bpy.data.objects.new(name, None)
    node.location = origin
    bpy.context.collection.objects.link(node)
    obj.parent = node
    to = bpy.data.objects.new('SlideTo_' + name[len('DoorSlide_'):], None)
    to.location = offset
    bpy.context.collection.objects.link(to)
    to.parent = node
    base.EXTRA_OBJECTS.extend([node, obj, to])


def partition_doors(b, c, M, p, idx0):
    """Casings round every doorway, and a leaf in each one that is not an open cased opening: hinged ("DoorHinge_<n>" > "DoorLeaf_<n>") or, in a
    building with slide_doors (barn, stable), a sliding leaf ("DoorSlide_<n>") that runs along the partition on the side facing the building's middle."""
    z0 = c.z0
    dh = p['door_h']
    n = idx0
    gaps = door_gaps(p)
    for g0, g1 in p.get('doors', []) + p.get('open_doors', []):
        t = 0.06
        pieces = [(g0 - t, g0, z0, z0 + dh + t), (g1, g1 + t, z0, z0 + dh + t)]
        if p['h'] > 2.0:                                                                  # no head casing over a stall door: it would be a bar at head height
            pieces.append((g0 - t, g1 + t, z0 + dh, z0 + dh + t))
        for (a0, a1, za, zb) in pieces:
            pbox(b, p, a0, a1, -PT / 2 - 0.014, PT / 2 + 0.014, za, zb, M['trim'])
    slide = bool(c.cfg.get('slide_doors'))
    for g0, g1 in p.get('doors', []):
        n += 1
        dw = (g1 - g0) - 0.04
        if slide:
            side = -1.0 if p['pos'] > 0.0 else 1.0                                        # towards the middle of the building
            plane = p['pos'] + side * (PT / 2 + 0.035 + 0.05 * (n % 2))
            plus, minus = partition_run(p, gaps, g0, g1, 1), partition_run(p, gaps, g0, g1, -1)
            direction = 1.0 if plus >= minus else -1.0
            run = plus if direction > 0 else minus
            dist = max(0.3, min(dw, run))
            uc = (g0 + g1) / 2
            hh = dh - 0.03

            def build(leaf, dw=dw, hh=hh, axis=p['axis']):
                def bx(u0, u1, t0, t1, za, zb, m):
                    if axis == 'y':
                        leaf.box(u0, u1, t0, t1, za, zb, m)
                    else:
                        leaf.box(t0, t1, u0, u1, za, zb, m)
                bx(-dw / 2, dw / 2, -0.02, 0.02, 0.0, hh, M['door'])
                for (x0, x1, za, zb) in ((-dw / 2 + 0.08, -0.03, 0.1, hh - 0.1), (0.03, dw / 2 - 0.08, 0.1, hh - 0.1)):
                    bx(x0, x1, -0.03, 0.03, za, zb, M['door_panel'] if 'door_panel' in M else M['door'])
                bx(dw / 2 - 0.2, dw / 2 - 0.14, -0.05, 0.05, hh * 0.45, hh * 0.45 + 0.05, M['brass'])
                bx(-dw / 2 + 0.14, -dw / 2 + 0.2, -0.05, 0.05, hh * 0.45, hh * 0.45 + 0.05, M['brass'])
            if p['axis'] == 'y':
                origin, offset = (uc, plane, z0), (direction * dist, 0.0, 0.0)
            else:
                origin, offset = (plane, uc, z0), (0.0, direction * dist, 0.0)
            slide_node('DoorSlide_%d' % n, origin, offset, build)
            if p['h'] > 2.0:                                                              # a track above a full height door
                u0, u1 = sorted((g0 - 0.05, g1 + 0.05 + direction * dist) if direction > 0 else (g0 - 0.05 - dist, g1 + 0.05))
                pbox(b, p, u0, u1, plane - p['pos'] - 0.03, plane - p['pos'] + 0.03, z0 + dh + 0.015, z0 + dh + 0.05, M['trim'])
            continue
        leaf = Builder('DoorLeaf_%d' % n)
        if p['axis'] == 'y':
            leaf.box(0.0, dw, -0.02, 0.02, 0.0, dh - 0.03, M['door'])
            leaf.box(dw - 0.14, dw - 0.08, -0.05, 0.05, dh * 0.45, dh * 0.45 + 0.05, M['brass'])
        else:
            leaf.box(-0.02, 0.02, 0.0, dw, 0.0, dh - 0.03, M['door'])
            leaf.box(-0.05, 0.05, dw - 0.14, dw - 0.08, dh * 0.45, dh * 0.45 + 0.05, M['brass'])
        leaf_obj = leaf.finish()
        hinge = bpy.data.objects.new('DoorHinge_%d' % n, None)
        hinge.location = (g0 + 0.02, p['pos'], z0) if p['axis'] == 'y' else (p['pos'], g0 + 0.02, z0)
        bpy.context.collection.objects.link(hinge)
        leaf_obj.parent = hinge
        base.EXTRA_OBJECTS.extend([hinge, leaf_obj])
    return n


# ------------------------------------------------------------------ shared pieces

FB = None
glass_builder = None


def log_courses(b, c, wall, z_top, m):
    """The wall of a log building as ROUND logs laid one on another, split round the openings. The logs of the front and back walls run the full
    width on the even courses and stop short of the corners on the odd ones, and the side walls the other way round, so the corners interlock
    and no two logs ever cross."""
    z0 = c.z0
    course = c.log_course
    ops = [(a, bb, z0 + zl, z0 + zh) for a, bb, zl, zh in c.openings[wall]]
    w, d, yh0 = c.w, c.d, c.yh0
    k = 0
    zc = z0
    while zc < z_top - 0.02:
        zb = min(zc + course, z_top)
        r = (zb - zc) * 0.5 * 0.98
        zm = (zc + zb) * 0.5
        full = (k % 2 == 0) == (wall in ('front', 'back'))
        short = 0.0 if full else course
        if wall in ('front', 'back'):
            lo, hi = -w / 2 + short, w / 2 - short
        else:
            lo, hi = yh0 + short, d / 2 - short
        for u0, u1 in hs.pieces(lo, hi, hs.blocked(ops, lo, hi, zc, zb, 0.0), 0.05):
            if wall == 'front':
                b.log((u0, yh0 + r, zm), (u1, yh0 + r, zm), r, m, sides=8)
            elif wall == 'back':
                b.log((u0, d / 2 - r, zm), (u1, d / 2 - r, zm), r, m, sides=8)
            elif wall == 'left':
                b.log((-w / 2 + r, u0, zm), (-w / 2 + r, u1, zm), r, m, sides=8)
            else:
                b.log((w / 2 - r, u0, zm), (w / 2 - r, u1, zm), r, m, sides=8)
        zc = zb
        k += 1
    # a course that an opening only partly covers is left out whole across the opening, which left a gap above and below every window (and
    # above a door): a log as thick as the gap fills it, so the logs run right up to the window and the door
    def fill(u0, u1, za, zb):
        if zb - za < 0.05 or u1 - u0 < 0.05:
            return
        rr = (zb - za) * 0.5 * 0.98
        zm = (za + zb) * 0.5
        if wall == 'front':
            b.log((u0, yh0 + rr, zm), (u1, yh0 + rr, zm), rr, m, sides=8)
        elif wall == 'back':
            b.log((u0, d / 2 - rr, zm), (u1, d / 2 - rr, zm), rr, m, sides=8)
        elif wall == 'left':
            b.log((-w / 2 + rr, u0, zm), (-w / 2 + rr, u1, zm), rr, m, sides=8)
        else:
            b.log((w / 2 - rr, u0, zm), (w / 2 - rr, u1, zm), rr, m, sides=8)

    for u0, u1, oz0, oz1 in ops:
        below = z0 + math.floor((oz0 - z0) / course + 1e-6) * course
        above = min(z_top, z0 + math.ceil((oz1 - z0) / course - 1e-6) * course)
        if oz0 > z0 + 0.05:
            fill(u0, u1, below, oz0)
        fill(u0, u1, oz1, above)


def clad_wall(parts, c, M, wall, z_top):
    """The exterior cladding of one wall: clapboard, log courses or ribbed metal, split round the openings."""
    z0 = c.z0
    pw = parts[wall]
    if c.style != 'log':
        hs.wall_box(pw, c, wall, T_SIDING, T_SIDING + T_SHEATH + T_STUD, z0, z_top, M['osb'], inset=T_SIDING, trim=T_SIDING)
    if c.style == 'log':
        log_courses(pw, c, wall, z_top, M['log'])
        # the chinking: a thin panel behind the logs (the side walls stop short of the front and back ones), so no light shows between the logs
        hs.wall_box(pw, c, wall, 0.13, 0.21, z0, z_top, M['log'], inset=0.0, trim=0.21)
        return
    course = c.rib
    zc = z0
    k = 0
    while zc < z_top - 0.02:
        zb = min(zc + course, z_top)
        # lap siding: every other board stands 18 mm proud, so the boards always read (a flat run of boxes only showed them in some light)
        proud = -0.018 if (c.style == 'siding' and k % 2) else 0.0
        hs.wall_box(pw, c, wall, proud, T_SIDING, zc, zb, M['siding'], gap_pad=0.07 if c.style != 'metal' else 0.0, inset=T_SIDING)
        zc = zb
        k += 1
    if c.style == 'metal':                                                               # vertical panel seams, a metre apart
        lo, hi = (-c.w / 2 + 0.5, c.w / 2 - 0.5) if wall in ('front', 'back') else (c.yh0 + 0.5, c.d / 2 - 0.5)
        n = int((hi - lo) / 1.6) + 1
        ops = [(a, bb, zl, zh) for a, bb, zl, zh in c.openings[wall]]
        for k in range(n):
            u = lo + k * (hi - lo) / max(1, n - 1)
            if any(o[0] - 0.08 < u < o[1] + 0.08 for o in ops):
                continue
            hs.trim_box(pw, c, wall, u - 0.015, u + 0.015, z0, z_top, -0.012, 0.0, M['siding_dark'])


def front_run(c, g, edge, direction):
    """How far (m) a leaf whose outer edge is at `edge` can slide along the front wall before it meets another opening or the corner."""
    lim = (c.w / 2 - 0.15) if direction > 0 else (-c.w / 2 + 0.15)
    for a, b, zl, zh in c.openings['front']:
        if (a, b) == tuple(g['u']):
            continue
        if direction > 0 and a >= edge - 1e-6:
            lim = min(lim, a - 0.16)
        if direction < 0 and b <= edge + 1e-6:
            lim = max(lim, b + 0.16)
    return max(0.0, abs(lim - edge))


def gable_courses(builder, c, y, thick, m, course, seams=None):
    """A gable end clad like the wall below it: a stack of boards (alternate ones proud), each as wide as the gable is at its height.
    With `seams` (metal) it is the plain gable with vertical seams instead."""
    w = c.w
    zb0, zs, za = c.top + 0.18, c.zw - 0.07, c.zr - 0.05
    sgn = -1.0 if y < 0 else 1.0

    def half(z):
        return w / 2 if z <= zs else max(0.0, w / 2 * (za - z) / (za - zs))

    if c.style == 'log':                                                         # a log gable: round logs, each as long as the gable is wide at its height
        z = zb0
        while z < za - 0.05:
            z1 = min(z + course, za)
            zm = (z + z1) * 0.5
            hw = half(zm) - 0.03
            if hw > 0.1:
                rr = (z1 - z) * 0.5 * 0.98
                yc = (y - thick / 2 + rr) if y < 0 else (y + thick / 2 - rr)      # the log's outer side flush with the gable's outer plane, like the wall logs
                builder.log((-hw, yc, zm), (hw, yc, zm), rr, m, sides=8)
            z = z1
        # the chinking: a thin log-coloured panel behind the logs, so no light shows through the gaps between them
        ys = (y - thick / 2 + 0.17) if y < 0 else (y + thick / 2 - 0.17)
        hs.gable_poly(builder, c, ys, 0.08, m)
        return
    i = builder.mat_index(m)
    if seams is not None:
        hs.gable_poly(builder, c, y, thick, m)
        lo, hi = -w / 2 + 0.5, w / 2 - 0.5
        n = int((hi - lo) / 2.4) + 1
        for q in range(n):
            u = lo + q * (hi - lo) / max(1, n - 1)
            top = zs + (za - zs) * (1 - abs(u) / (w / 2)) if abs(u) > 0 else za
            top = min(top, za) - 0.05
            if top > zb0 + 0.1:
                y0 = (y - thick / 2 - 0.012) if y < 0 else (y + thick / 2)
                builder.box(u - 0.015, u + 0.015, y0, y0 + 0.012, zb0, top, seams)
        return
    k = 0
    z = zb0
    while z < za - 0.02:
        z1 = min(z + course, za)
        yy = y + sgn * (0.018 if k % 2 else 0.0)
        pts = [(-half(z), z), (half(z), z), (half(z1), z1), (-half(z1), z1)]
        if half(z1) < 1e-4:
            pts = [(-half(z), z), (half(z), z), (0.0, z1)]
        front = [builder.bm.verts.new((x, yy - thick / 2, zz)) for x, zz in pts]
        back = [builder.bm.verts.new((x, yy + thick / 2, zz)) for x, zz in pts]
        faces = [builder.bm.faces.new(front[::-1]), builder.bm.faces.new(back)]
        for q in range(len(pts)):
            nq = (q + 1) % len(pts)
            faces.append(builder.bm.faces.new((front[q], front[nq], back[nq], back[q])))
        for f in faces:
            f.material_index = i
        z = z1
        k += 1


def big_door(part, glass_b, c, M, g, k, wall='front'):
    """A barn door (two leaves that slide apart along the wall, "DoorSlide_<n>") or a roll-up door (one panel that rolls up into its header,
    "DoorRoll_<n>"), in its opening. The game opens them with a right click (ConstructionSite.cs)."""
    u0, u1, h = g['u'][0], g['u'][1], g['h']
    z0 = c.z0
    za, zb = z0, z0 + h
    t = 0.09
    y0 = c.yh0
    hs.trim_box(part, c, wall, u0 - t, u0, za, zb + t, -0.05, 0.03, M['trim'])
    hs.trim_box(part, c, wall, u1, u1 + t, za, zb + t, -0.05, 0.03, M['trim'])
    hs.trim_box(part, c, wall, u0 - t, u1 + t, zb, zb + t, -0.05, 0.03, M['trim'])
    xc = (u0 + u1) / 2
    if g['kind'] == 'roll':
        node = bpy.data.objects.new('DoorRoll_%d' % k, None)      # origin at the top centre: the game squashes it upwards
        node.location = (xc, y0, zb)
        bpy.context.collection.objects.link(node)
        leaf = Builder('RollLeaf_%d' % k)
        n = max(4, int(h / 0.8))
        hw = (u1 - u0) / 2
        for i in range(n):                                                                # horizontal roll-up panels
            a = -(i + 1) * h / n
            leaf.box(-hw, hw, 0.0, 0.045, a + 0.008, a + h / n - 0.008, M['door'])
        if g.get('window', True):
            leaf.box(-hw + 0.3, hw - 0.3, 0.02, 0.05, -0.75, -0.45, M['glass'])
        leaf.box(-0.12, 0.12, -0.012, 0.0, -h + 0.5, -h + 0.58, M['trim'])                # a pull handle
        obj = leaf.finish()
        obj.parent = node
        base.EXTRA_OBJECTS.extend([node, obj])
        hs.trim_box(part, c, wall, u0, u1, zb + 0.0, zb + 0.16, -0.06, 0.0, M['trim'])      # the roll-up hood
        return
    # a barn door: a slab with a Z brace per leaf, the two braces mirroring each other; the leaves hang in front of the wall on a track
    um = xc
    lw = (u1 - u0) / 2
    for side, (a, bb) in ((-1, (u0, um - 0.01)), (1, (um + 0.01, u1))):
        w = bb - a
        edge = a if side < 0 else bb
        dist = max(0.3, min(w - 0.15, front_run(c, g, edge, side)))
        hw = w / 2

        def build(leaf, w=w, hw=hw, side=side):
            leaf.box(-hw, hw, -0.125, -0.07, 0.0, h, M['door'])
            leaf.box(-hw + 0.06, hw - 0.06, -0.145, -0.125, 0.15, 0.3, M['trim'])           # top and bottom rails
            leaf.box(-hw + 0.06, hw - 0.06, -0.145, -0.125, h - 0.3, h - 0.15, M['trim'])
            leaf.box(-hw, -hw + 0.06, -0.145, -0.125, 0.15, h - 0.15, M['trim'])             # stiles
            leaf.box(hw - 0.06, hw, -0.145, -0.125, 0.15, h - 0.15, M['trim'])
            # the diagonal runs from the bottom outer corner up to the top of the middle edge: mirrored on the two leaves
            xo, xi = (-hw + 0.1, hw - 0.1) if side < 0 else (hw - 0.1, -hw + 0.1)
            leaf.log((xo, -0.135, 0.22), (xi, -0.135, h - 0.22), 0.035, M['trim'], sides=4)
            xh = (hw - 0.22) if side < 0 else (-hw + 0.22)
            leaf.box(xh - 0.03, xh + 0.03, -0.17, -0.125, h * 0.45, h * 0.45 + 0.28, M['brass'])   # a handle
            for xr in (-hw + 0.3, hw - 0.3):                                                      # hangers: from the leaf up to the track
                leaf.box(xr - 0.04, xr + 0.04, -0.19, -0.15, h - 0.05, h + 0.1, M['brass'])
                leaf.box(xr - 0.04, xr + 0.04, -0.19, -0.07, h - 0.05, h + 0.0, M['brass'])
        origin = ((a + bb) / 2, y0, za)
        slide_node('DoorSlide_b%d%s' % (k, 'L' if side < 0 else 'R'), origin, (side * dist, 0.0, 0.0), build)
    # the track the leaves hang from, held off the wall by brackets (a bar floating in the air looked wrong)
    hs.trim_box(part, c, wall, u0 - lw, u1 + lw, zb + 0.1, zb + 0.18, -0.2, -0.14, M['trim'])
    nb = int((u1 - u0 + 2 * lw) / 1.0) + 1
    for i in range(nb):
        ub = (u0 - lw + 0.1) + (u1 - u0 + 2 * lw - 0.2) * i / max(1, nb - 1)
        hs.trim_box(part, c, wall, ub - 0.035, ub + 0.035, zb + 0.1, zb + 0.18, -0.2, 0.02, M['trim'])
        hs.trim_box(part, c, wall, ub - 0.025, ub + 0.025, zb + 0.0, zb + 0.1, -0.06, 0.02, M['trim'])   # and a post down to the header


def personal_door(b, c, M, parts):
    """The front door, 1.2 m by 2.3 m, on its hinge, at x = door_x."""
    dx = c.dx
    dw, dh = DOOR_W - 0.06, DOOR_H - 0.04
    z0 = c.z0
    leaf = Builder('DoorLeaf')
    leaf.box(0.0, dw, -0.04, 0.04, 0.0, dh, M['door'])
    if c.style != 'metal':
        for (x0, x1, za, zb) in ((0.12, dw / 2 - 0.05, 0.15, 1.0), (dw / 2 + 0.05, dw - 0.12, 0.15, 1.0),
                                 (0.12, dw / 2 - 0.05, 1.12, 1.95), (dw / 2 + 0.05, dw - 0.12, 1.12, 1.95)):
            leaf.box(x0, x1, -0.055, -0.035, za, zb, M['door_panel'])
    leaf.box(dw - 0.16, dw - 0.1, -0.09, 0.09, 1.0, 1.06, M['brass'])
    leaf_obj = leaf.finish()
    hinge = bpy.data.objects.new('DoorHinge', None)
    hinge.location = (dx - dw / 2, c.yh0 + 0.09, z0)
    bpy.context.collection.objects.link(hinge)
    leaf_obj.parent = hinge
    base.EXTRA_OBJECTS.extend([hinge, leaf_obj])
    t = 0.07
    pf = parts['front']
    hs.trim_box(pf, c, 'front', dx - DOOR_W / 2 - t, dx - DOOR_W / 2, z0, z0 + DOOR_H + t, -0.05, 0.03, M['trim'])
    hs.trim_box(pf, c, 'front', dx + DOOR_W / 2, dx + DOOR_W / 2 + t, z0, z0 + DOOR_H + t, -0.05, 0.03, M['trim'])
    hs.trim_box(pf, c, 'front', dx - DOOR_W / 2 - t, dx + DOOR_W / 2 + t, z0 + DOOR_H, z0 + DOOR_H + t, -0.05, 0.03, M['trim'])
    hs.trim_box(pf, c, 'front', dx - DOOR_W / 2, dx + DOOR_W / 2, z0, z0 + 0.03, -0.02, 0.19, M['concrete'])


def railing(b, c, M):
    """The porch railing (balusters every 0.32 m: the house's every 0.2 m costs too many triangles on a big porch)."""
    w, d = c.w, c.d
    rail_y0, rail_y1 = -d / 2 + 0.1, c.yh0
    zb, zt = c.z0, c.z0 + 0.9
    for x0, x1 in ((-w / 2 + 0.12, -0.8), (0.8, w / 2 - 0.12)):
        b.box(x0, x1, -d / 2 + 0.12, -d / 2 + 0.18, zt - 0.06, zt, M['trim'])
        b.box(x0, x1, -d / 2 + 0.12, -d / 2 + 0.18, zb + 0.08, zb + 0.14, M['trim'])
        n = int((x1 - x0) / 0.32)
        for k in range(1, n):
            x = x0 + k * (x1 - x0) / n
            b.box(x - 0.018, x + 0.018, -d / 2 + 0.135, -d / 2 + 0.165, zb + 0.14, zt - 0.06, M['trim'])
    for x in (-w / 2 + 0.12, w / 2 - 0.12):
        b.box(x - 0.03, x + 0.03, rail_y0, rail_y1, zt - 0.06, zt, M['trim'])
        b.box(x - 0.03, x + 0.03, rail_y0, rail_y1, zb + 0.08, zb + 0.14, M['trim'])
        n = int((rail_y1 - rail_y0) / 0.32)
        for k in range(1, n):
            y = rail_y0 + k * (rail_y1 - rail_y0) / n
            b.box(x - 0.015, x + 0.015, y - 0.018, y + 0.018, zb + 0.14, zt - 0.06, M['trim'])


def porch_posts(b, c, M, top_z):
    w, d = c.w, c.d
    for x in (-w / 2 + 0.12, -0.8, 0.8, w / 2 - 0.12):
        b.box(x - 0.07, x + 0.07, -d / 2 + 0.08, -d / 2 + 0.22, c.z0, top_z, M['lumber'])


# ------------------------------------------------------------------ stages

def framing(b, c, M, with_partitions=True):
    w, d = c.w, c.d
    h = foundation(b, c, M)
    z0, top = c.z0, c.top
    b.box(-w / 2 + 0.02, w / 2 - 0.02, (c.yh0 if c.cfg.get('porch') else -d / 2 + 0.02), d / 2 - 0.02, h, z0, M['osb'])
    for wall in c.walls:
        hs.wall_box(b, c, wall, 0.05, 0.05 + T_STUD, z0, z0 + 0.04, M['lumber'], openings=[])
        ops = [(a, bb, z0 + zl, z0 + zh) for a, bb, zl, zh in c.openings[wall]]
        lo, hi = (-w / 2 + 0.2, w / 2 - 0.2) if wall in ('front', 'back') else (c.yh0 + 0.2, d / 2 - 0.2)
        step = 0.6 if c.style in ('metal',) or w * d > 80 else 0.4
        n = int((hi - lo) / step) + 1
        for k in range(n):
            u = lo + k * (hi - lo) / max(1, n - 1)
            za = z0 + 0.04
            gap = [o for o in ops if o[0] - 0.05 < u < o[1] + 0.05]
            for o in gap:
                for sa, sb in ((za, o[2] - 0.1), (o[3] + 0.12, top)):
                    if sb - sa > 0.05:
                        hs.stud(b, c, wall, u, sa, sb, M)
            if not gap:
                hs.stud(b, c, wall, u, za, top, M)
        for u0, u1, zl, zh in c.openings[wall]:
            for a, bb in ((zh, zh + 0.14), (zh + 0.14, zh + 0.28)):
                if z0 + bb < top:
                    hs.trim_box(b, c, wall, u0 - 0.1, u1 + 0.1, z0 + a, z0 + bb, T_SIDING + T_SHEATH, T_SIDING + T_SHEATH + T_STUD, M['lumber'])
            if zl > 0.05:
                hs.trim_box(b, c, wall, u0, u1, z0 + zl - 0.09, z0 + zl, T_SIDING + T_SHEATH, T_SIDING + T_SHEATH + T_STUD, M['lumber'])
            for u in (u0 - 0.1, u1 + 0.04):
                hs.trim_box(b, c, wall, u, u + 0.06, z0 + 0.04, top, T_SIDING + T_SHEATH, T_SIDING + T_SHEATH + T_STUD, M['lumber'])
        hs.wall_box(b, c, wall, T_SIDING + T_SHEATH, T_SIDING + T_SHEATH + T_STUD, top, top + 0.09, M['lumber'], openings=[])
        hs.wall_box(b, c, wall, T_SIDING + T_SHEATH, T_SIDING + T_SHEATH + T_STUD, top + 0.09, top + 0.18, M['lumber'], openings=[])
        if hs.wall_top(c, wall) > top + 0.3:                              # the walls the roof rests on: blocking up to the rafters
            hs.wall_box(b, c, wall, T_SIDING + T_SHEATH, T_SIDING + T_SHEATH + T_STUD, top + 0.18, c.zw + 0.05, M['lumber'], openings=[])
    def roof_frame(rb, rc):
        rw_, rd_ = rc.w, rc.d
        n = int((rd_ / 2 - rc.yh0) / (0.6 if rw_ < 7 else 0.9)) + 1
        for k in range(n):                                              # ceiling joists across
            y = rc.yh0 + 0.1 + (rd_ / 2 - rc.yh0 - 0.2) * k / max(1, n - 1)
            rb.box(-rw_ / 2, rw_ / 2, y - 0.03, y + 0.03, rc.top + 0.18, rc.top + 0.34, M['lumber'])
        hs.rafters(rb, rc, M, spacing=0.6 if rw_ < 7 else 0.9, collar=rw_ < 9)
        hs.gable_studs(rb, rc, M)
    if c.cfg.get('porch'):
        pb = PB if PB is not None else b
        porch_posts(pb, c, M, top)
        pb.box(-w / 2, w / 2, -d / 2 + 0.08, -d / 2 + 0.22, top, top + 0.22, M['lumber'])
        for x in (-w / 2 + 0.12, w / 2 - 0.12):
            pb.box(x - 0.04, x + 0.04, -d / 2 + 0.1, c.yh0, top - 0.1, top, M['lumber'])
    rc = roof_ctx(c)
    if rc is c:
        roof_frame(b, c)
    else:
        tb = Builder('tmp')
        roof_frame(tb, rc)
        merge_turned(tb, b)
    if c.open_front:
        open_front_frame(b, c, M)
    if with_partitions:
        for p in c.parts:
            partition_framing(b, c, M, p)


def walls_stage(b, c, M):
    w, d = c.w, c.d
    framing(b, c, M, with_partitions=False)
    z0 = c.z0
    for wall in c.walls:
        if c.style == 'log':
            log_courses(b, c, wall, hs.wall_top(c, wall), M['log'])
        else:
            hs.wall_box(b, c, wall, T_SIDING, T_SIDING + T_SHEATH, z0, hs.wall_top(c, wall), M['osb'], inset=T_SIDING)
    rc = roof_ctx(c)
    if rc is c:
        hs.roof_deck(b, c, M['osb'], 0.04)
    else:
        tb = Builder('tmp')
        hs.roof_deck(tb, rc, M['osb'], 0.04)
        merge_turned(tb, b)
    if c.open_front:
        open_front_frame(b, c, M)
    if c.cfg.get('porch'):
        hs.deck_boards(b, c, M, c.z0 - 0.025, -d / 2, c.yh0)
    for wall in c.walls:
        for u0, u1, zl, zh in c.openings[wall]:
            if zl > 0.05:
                hs.trim_box(b, c, wall, u0, u1, z0 + zl - 0.04, z0 + zl, -0.02, T_SIDING + T_SHEATH, M['lumber'])
    for p in c.parts:                                                    # the partitions, drywalled
        partition_wall(b, c, M, p)


def roof_and_gables(tp, tg, c, M):
    """The gable ends (with their vent) and the roof, built for a ridge that runs front to back in the context `c` (tp: its front, back and roof builders)."""
    w, d, z0, top, ov = c.w, c.d, c.z0, c.top, c.ov
    # gables
    gm = M['log'] if c.style == 'log' else M['siding']
    # the gables stand flush with the cladding below them (a porch building's gable stands at the porch edge, over the porch)
    gy = -d / 2 + 0.1 if c.cfg.get('porch') else c.yh0 + 0.03
    for y in (gy, d / 2 - 0.03):
        if c.style == 'metal':
            gable_courses(tp['front' if y < 0 else 'back'], c, y, 0.06, gm, c.rib, seams=M['siding_dark'])
        else:
            gable_courses(tp['front' if y < 0 else 'back'], c, y, 0.06, gm, c.log_course if c.style == 'log' else c.rib)
    if c.style == 'siding' and not c.cfg.get('porch'):
        # the gable vent sits inside the gable: on a low gable (the chicken coop's is 1.1 m) it is scaled down, or it would stand out above the roof
        gh = c.zr - top
        v0 = top + min(0.85, 0.35 * gh)
        v1 = v0 + min(0.4, 0.3 * gh)
        tp['front'].box(-0.22, 0.22, c.yh0 - 0.03, c.yh0 + 0.0, v0, v1, M['trim'])
        tg.box(-0.18, 0.18, c.yh0 - 0.02, c.yh0 + 0.01, v0 + 0.04, v1 - 0.04, M['glass'])
    # the roof
    hs.roof_deck(tp['roof'], c, M['osb'], 0.035)
    for side in (-1, 1):
        zs = 0.035 + 0.035
        tp['roof'].roof_slab(side * (w / 2 + ov), c.eave_z + 0.06 + zs, c.zr + 0.06 + zs, -d / 2 - ov, d / 2 + ov, 0.035, M['shingle'])
        # seams run down the slope, from the ridge to the lower edge (shingled or metal alike), a little under a metre apart
        n = int((d + 2 * ov) / 0.9)
        for k in range(n + 1):
            y = -d / 2 - ov + (d + 2 * ov) * k / max(1, n)
            tp['roof'].log((side * (w / 2 + ov), y, c.eave_z + 0.06 + zs + 0.02), (side * 0.04, y, c.zr + 0.06 + zs + 0.02), 0.018, M['shingle_dark'], sides=3)
        tp['roof'].box(side * (w / 2 + ov) - 0.035, side * (w / 2 + ov) + 0.035, -d / 2 - ov, d / 2 + ov, c.eave_z - 0.1, c.eave_z + 0.12, M['trim'])
    tp['roof'].box(-0.1, 0.1, -d / 2 - ov, d / 2 + ov, c.zr + 0.12, c.zr + 0.2, M['shingle_dark'])


def complete(b, c, M, finishings=False):
    w, d = c.w, c.d
    z0, top, ov = c.z0, c.top, c.ov
    parts = {k: Builder(n) for k, n in (('front', 'Wall_Front'), ('back', 'Wall_Back'), ('left', 'Wall_Left'), ('right', 'Wall_Right'), ('roof', 'Roof'))}
    h = foundation(b, c, M)
    b.box(-w / 2 + 0.02, w / 2 - 0.02, (c.yh0 if c.cfg.get('porch') else -d / 2 + 0.02), d / 2 - 0.02, h, z0, M['floor'])
    for wall in c.walls:
        clad_wall(parts, c, M, wall, hs.wall_top(c, wall))
    ti = T_SIDING + T_SHEATH + T_STUD
    for wall in c.walls:
        if c.style == 'log':
            continue                                   # log walls show their logs inside too: no painted interior layer (nothing to paint there)
        hs.wall_box(parts[wall], c, wall, ti, ti + 0.02, z0 + 0.03, top, M['interior'], inset=ti + 0.02, trim=ti)
        if finishings:
            hs.wall_box(parts[wall], c, wall, ti + 0.02, ti + 0.04, z0 + 0.03, z0 + 0.14, M['trim'], inset=ti + 0.04, trim=ti + 0.02)
    # corner boards (clapboard and metal; logs interlock)
    if c.style != 'log':
        for (x, y) in ((-w / 2, c.yh0), (w / 2 - 0.08, c.yh0), (-w / 2, d / 2 - 0.08), (w / 2 - 0.08, d / 2 - 0.08)):
            x0, x1 = (x - 0.015, x + 0.08) if x < 0 else (x, x + 0.095)
            y0, y1 = (y - 0.015, y + 0.08) if y < 0 else (y, y + 0.095)
            if abs(y - c.yh0) < 1e-6:
                y0, y1 = y - 0.015, y + 0.08
            b.box(x0, x1, y0, y1, z0, c.zw + 0.05, M['trim'])
    # windows and the big doors
    for wall in c.walls:
        for u0, u1, zl, zh in c.openings[wall]:
            if zl > 0.05 and not (wall == 'front' and abs(zl) < 0.01):
                hs.window_dressing(parts[wall], c, M, M['glass'], wall, u0, u1, zl, zh, shutters=(wall == 'front' and c.cfg.get('shutters', False)))
    for k, g in enumerate(c.cfg.get('big', [])):
        big_door(parts['front'], glass_builder, c, M, g, k + 1)
    rc = roof_ctx(c)
    if rc is c:
        roof_and_gables(parts, glass_builder, c, M)
    else:
        tp = {k: Builder('tmp') for k in ('front', 'back', 'roof')}
        tg = Builder('tmp')
        roof_and_gables(tp, tg, rc, M)
        merge_turned(tp['front'], parts['left'])      # the context's front gable is the left wall's
        merge_turned(tp['back'], parts['right'])
        merge_turned(tp['roof'], parts['roof'])
        merge_turned(tg, glass_builder)
    # the porch
    if c.cfg.get('porch'):
        hs.deck_boards(b, c, M, z0 - 0.025, -d / 2, c.yh0)
        pb = PB if PB is not None else b
        porch_posts(pb, c, M, top)
        pb.box(-w / 2, w / 2, -d / 2 + 0.06, -d / 2 + 0.24, top, top + 0.2, M['trim'])
        railing(pb, c, M)
        for k in range(3):
            zz = (z0 - 0.04) * (1 - (k + 1) * 0.28)
            b.box(-0.82, 0.82, -d / 2 - 0.3 * (k + 1), -d / 2 - 0.3 * k, zz, zz + 0.03, M['deck'])
    if c.open_front:
        open_front_frame(b, c, M)
    else:
        personal_door(b, c, M, parts)
    for wp in c.cfg.get('woodpiles', []):
        woodpile(b, c, M, wp[0], wp[1])
    # the chimney: against an exterior wall, between two windows, never in a room (STRUCTURE_STAGES_GUIDE.md)
    if c.cfg.get('chimney'):
        wall, cy = c.cfg['chimney']
        cx0, cx1 = -w / 2 - 0.5, -w / 2 + 0.1
        ctop = c.zw + 1.0
        chim = Builder('Chimney')
        base.chimney_with_fireplace(chim, M['brick'], colour('Soot', (0.08, 0.07, 0.07), 1.0), M['concrete'], cx0, cx1, -w / 2 + 0.6, cy, 0.45, z0, top + 0.1, ctop)
        base.EXTRA_OBJECTS.append(chim.finish())
    # the interior partitions, painted and cased, with their doors
    n = 0
    for p in c.parts:
        partition_wall(b, c, M, p, finished=True, finishings=finishings)
        n = partition_doors(b, c, M, p, n)
    for part in parts.values():
        base.EXTRA_OBJECTS.append(part.finish())


# ------------------------------------------------------------------ the greenhouse (glazed)

def gh_frame(P, c, M, glazed):
    """The greenhouse's frame. P holds one builder per part the game can hide in the cutaway view: Wall_Left / Right / Front / Back and Roof."""
    w, d, z0, top = c.w, c.d, c.z0, c.top
    post = 0.07
    alu = M['alu']
    n = int(d / 1.0) + 1
    ys = [-d / 2 + 0.06 + (d - 0.12) * k / (n - 1) for k in range(n)]
    for y in ys:
        for x, side in ((-w / 2 + 0.06, 'left'), (w / 2 - 0.06, 'right')):
            P[side].box(x - post / 2, x + post / 2, y - post / 2, y + post / 2, z0, top, alu)
    for x, side in ((-w / 2 + 0.06, 'left'), (w / 2 - 0.06, 'right')):   # rails along the sides
        for zr in (z0 + 0.9, top - 0.06):
            P[side].box(x - 0.03, x + 0.03, -d / 2 + 0.06 - post / 2, d / 2 - 0.06 + post / 2, zr, zr + 0.06, alu)
    # front and back walls: posts every metre, a rail, with the door gap at the front
    nx = int(w / 1.0) + 1
    for k in range(1, nx - 1):                                            # the corners already have their posts (the side walls')
        x = -w / 2 + 0.06 + (w - 0.12) * k / (nx - 1)
        for y in (-d / 2 + 0.06, d / 2 - 0.06):
            if y < 0 and abs(x - c.dx) < DOOR_W / 2 + 0.03:
                continue
            P['front' if y < 0 else 'back'].box(x - 0.03, x + 0.03, y - 0.03, y + 0.03, z0, top, alu)
    xa, xb = -w / 2 + 0.06 + post / 2, w / 2 - 0.06 - post / 2               # between the corner posts: no rail crosses another
    door0, door1 = c.dx - DOOR_W / 2, c.dx + DOOR_W / 2
    for y in (-d / 2 + 0.06, d / 2 - 0.06):
        W = P['front' if y < 0 else 'back']
        W.box(xa, xb, y - 0.03, y + 0.03, top - 0.06, top, alu)
        if y < 0:
            W.box(door0, door1, y - 0.04, y + 0.04, z0 + DOOR_H, z0 + DOOR_H + 0.07, alu)
            W.box(xa, door0, y - 0.03, y + 0.03, z0 + 0.9, z0 + 0.96, alu)   # the mid rail stops at the doorway
            W.box(door1, xb, y - 0.03, y + 0.03, z0 + 0.9, z0 + 0.96, alu)
        else:
            W.box(xa, xb, y - 0.03, y + 0.03, z0 + 0.9, z0 + 0.96, alu)
    # roof: ridge, rafters at every post, purlins
    R = P['roof']
    R.box(-0.04, 0.04, -d / 2 - c.ov, d / 2 + c.ov, c.zr - 0.06, c.zr + 0.06, alu)
    for y in ys:
        for side in (-1, 1):
            R.log((side * (w / 2 + c.ov), y, c.eave_z), (side * 0.04, y, c.zr), 0.03, alu, sides=4)
    for t in (0.35, 0.7):
        for side in (-1, 1):
            xe = side * (w / 2 + c.ov) * (1 - t)
            ze = c.eave_z + (c.zr - c.eave_z) * t
            R.box(xe - 0.02, xe + 0.02, -d / 2 - c.ov, d / 2 + c.ov, ze, ze + 0.04, alu)
    # gable posts
    for x in (-w * 0.25, 0.0, w * 0.25):
        zt = c.zr - c.slope * abs(x)
        for y in (-d / 2 + 0.06, d / 2 - 0.06):
            if y < 0 and abs(x - c.dx) < DOOR_W / 2 + 0.03:
                continue
            R.box(x - 0.025, x + 0.025, y - 0.025, y + 0.025, top, zt - 0.04, alu)


def gh_knee_wall(P, c, M):
    w, d, z0 = c.w, c.d, c.z0
    kh = 0.9
    for wall in c.walls:
        b = P[wall]
        gaps = [(c.dx - DOOR_W / 2, c.dx + DOOR_W / 2)] if wall == 'front' else []
        lo, hi = (-w / 2, w / 2) if wall in ('front', 'back') else (-d / 2, d / 2)
        for u0, u1 in hs.pieces(lo, hi, gaps, 0.04):
            if wall == 'front':
                b.box(u0, u1, -d / 2, -d / 2 + 0.07, z0, z0 + kh, M['siding'])
            elif wall == 'back':
                b.box(u0, u1, d / 2 - 0.07, d / 2, z0, z0 + kh, M['siding'])
            elif wall == 'left':
                b.box(-w / 2, -w / 2 + 0.07, u0, u1, z0, z0 + kh, M['siding'])
            else:
                b.box(w / 2 - 0.07, w / 2, u0, u1, z0, z0 + kh, M['siding'])


def gh_glass(P, c, M):
    """The glazing goes into the same part as the frame it fills (a wall's panes hide with that wall, the roof's and the gable ends' with the roof)."""
    w, d, z0, top = c.w, c.d, c.z0, c.top
    kh = 0.96
    g = M['glass']
    # panes between the posts, side walls and the front / back walls
    n = int(d / 1.0) + 1
    ys = [-d / 2 + 0.06 + (d - 0.12) * k / (n - 1) for k in range(n)]
    for y0, y1 in zip(ys[:-1], ys[1:]):
        for x, side in ((-w / 2 + 0.03, 'left'), (w / 2 - 0.03, 'right')):
            P[side].box(x - 0.008, x + 0.008, y0 + 0.04, y1 - 0.04, z0 + kh, top - 0.08, g)
    nx = int(w / 1.0) + 1
    xs = [-w / 2 + 0.06 + (w - 0.12) * k / (nx - 1) for k in range(nx)]
    for y in (-d / 2 + 0.03, d / 2 - 0.03):
        for x0, x1 in zip(xs[:-1], xs[1:]):
            if y < 0 and x0 < c.dx + DOOR_W / 2 and x1 > c.dx - DOOR_W / 2:
                continue
            P['front' if y < 0 else 'back'].box(x0 + 0.04, x1 - 0.04, y - 0.008, y + 0.008, z0 + kh, top - 0.08, g)
    # gable ends: glass from the top rail up to the roof
    gb = P['roof']
    zt, zw, zr = top, c.zw, c.zr
    pts = [(-w / 2 + 0.07, zt), (w / 2 - 0.07, zt), (w / 2 - 0.07, zw), (0.0, zr - 0.05), (-w / 2 + 0.07, zw)]
    gi = gb.mat_index(g)
    for y in (-d / 2 + 0.03, d / 2 - 0.03):
        f = [gb.bm.verts.new((x, y - 0.008, z)) for x, z in pts]
        bk = [gb.bm.verts.new((x, y + 0.008, z)) for x, z in pts]
        faces = [gb.bm.faces.new(f[::-1]), gb.bm.faces.new(bk)]
        for k in range(len(pts)):
            nn = (k + 1) % len(pts)
            faces.append(gb.bm.faces.new((f[k], f[nn], bk[nn], bk[k])))
        for fc in faces:
            fc.material_index = gi
    # one unbroken pane per slope, over the whole frame (the overhang at both ends too), lying on the rafters (their tops are 0.03 above the roof line)
    for side in (-1, 1):
        gb.roof_slab(side * (w / 2 + c.ov), c.eave_z + 0.035, c.zr + 0.035, -d / 2 - c.ov + 0.01, d / 2 + c.ov - 0.01, 0.012, g)


def gh_door(b, c, M, parts_b):
    dx = c.dx
    dw, dh = DOOR_W - 0.06, DOOR_H - 0.04
    leaf = Builder('DoorLeaf')
    leaf.box(0.0, dw, -0.03, 0.03, 0.0, 0.1, M['alu'])
    leaf.box(0.0, dw, -0.03, 0.03, dh - 0.1, dh, M['alu'])
    leaf.box(0.0, 0.1, -0.03, 0.03, 0.0, dh, M['alu'])
    leaf.box(dw - 0.1, dw, -0.03, 0.03, 0.0, dh, M['alu'])
    leaf.box(0.1, dw - 0.1, -0.01, 0.01, 0.1, dh - 0.1, M['glass'])
    leaf.box(dw - 0.2, dw - 0.14, -0.06, 0.06, 1.0, 1.06, M['brass'])
    leaf_obj = leaf.finish()
    hinge = bpy.data.objects.new('DoorHinge', None)
    hinge.location = (dx - dw / 2, c.yh0 + 0.06, c.z0)
    bpy.context.collection.objects.link(hinge)
    leaf_obj.parent = hinge
    base.EXTRA_OBJECTS.extend([hinge, leaf_obj])


def gh_benches(b, c, M):
    w, d, z0 = c.w, c.d, c.z0
    y0, y1 = -d / 2 + 1.0, c.cfg['partitions'][0]['pos'] - 0.3 if c.cfg['partitions'] else d / 2 - 0.3
    for x in (-w / 2 + 0.55, w / 2 - 0.55):
        b.box(x - 0.4, x + 0.4, y0, y1, z0 + 0.7, z0 + 0.75, M['lumber'])
        for yy in (y0 + 0.1, (y0 + y1) / 2, y1 - 0.1):
            b.box(x - 0.36, x - 0.3, yy - 0.03, yy + 0.03, z0, z0 + 0.7, M['lumber'])
            b.box(x + 0.3, x + 0.36, yy - 0.03, yy + 0.03, z0, z0 + 0.7, M['lumber'])


def greenhouse_stage(b, c, M, stage):
    """stage: 'foundation' | 'framing' | 'walls' | 'complete'."""
    w, d = c.w, c.d
    h = foundation(b, c, M)
    if stage == 'foundation':
        return
    b.box(-w / 2 + 0.02, w / 2 - 0.02, -d / 2 + 0.02, d / 2 - 0.02, h, c.z0, M['floor'])
    P = {k: Builder(n) for k, n in (('left', 'Wall_Left'), ('right', 'Wall_Right'), ('front', 'Wall_Front'), ('back', 'Wall_Back'), ('roof', 'Roof'))}
    gh_frame(P, c, M, glazed=(stage == 'complete'))
    if stage in ('walls', 'complete'):
        gh_knee_wall(P, c, M)
    for p in c.parts:
        if stage == 'framing':
            partition_framing(b, c, M, p)
        else:
            partition_wall(b, c, M, p, finished=(stage == 'complete'))
    if stage == 'complete':
        gh_glass(P, c, M)
        gh_door(b, c, M, None)
        gh_benches(b, c, M)
        n = 0
        for p in c.parts:
            n = partition_doors(b, c, M, p, n)
        # a pair of roof vents and a water barrel by the door
        b.log((w / 2 + 0.25, -d / 2 + 0.5, c.z0), (w / 2 + 0.25, -d / 2 + 0.5, c.z0 + 0.9), 0.3, M['barrel'], sides=10)
    for part in P.values():
        base.EXTRA_OBJECTS.append(part.finish())   # Wall_* and Roof: the game hides them in the cutaway view


# ------------------------------------------------------------------ manifests

STAGE_FOLDERS = ['struct_foundation', 'struct_framing', 'struct_walls', 'struct_complete', 'struct_finishings']
TEMPLATE = 'small_cabin'


def stage_names(n):
    return STAGE_FOLDERS[:n]


def ensure_manifests(sid, cfg):
    """Group manifest (five stages for houses, created for a structure that has none) and the stage manifests with their dimensions."""
    gpath = os.path.join(STRUCTURES, sid, sid + '.json')
    tmpl_group = json.load(open(os.path.join(STRUCTURES, TEMPLATE, TEMPLATE + '.json'), encoding='utf-8'))
    old = json.load(open(gpath, encoding='utf-8')) if os.path.exists(gpath) else {}
    if old.get('growth', {}).get('stages'):
        g = old
    else:
        g = json.load(open(os.path.join(STRUCTURES, 'large_metal_garage', 'large_metal_garage.json'), encoding='utf-8'))   # a four stage group to start from
        g['id'] = sid
        g['name'] = cfg['name']
        g['icon'] = sid + '.png'
        g['growth']['species'] = sid
        for k in ('stores', 'sale_unit'):
            pass
        # the old single model files of this item are replaced by the stage models
        os.makedirs(os.path.join(STRUCTURES, sid), exist_ok=True)
        for fn in os.listdir(os.path.join(STRUCTURES, sid)):
            if fn.lower().endswith(('.fbx', '.obj', '.mtl', '.glb')):
                os.remove(os.path.join(STRUCTURES, sid, fn))
    stages = g['growth']['stages']
    want = cfg['stages']
    if want == 5 and len(stages) == 4:
        # exterior + finishings, like the cabin: the roofing / glass / masonry go to the exterior, the drywall / paint / flooring to the finishings
        t4, t5 = copy.deepcopy(tmpl_group['growth']['stages'][3]), copy.deepcopy(tmpl_group['growth']['stages'][4])
        scale = max(1.0, cfg['w'] * cfg['d'] / 28.0)
        for t in (t4, t5):
            for line in t['construction_recipe']:
                line['quantity'] = int(math.ceil(line['quantity'] * scale))
        old = stages[3]
        t4['icon'] = 'struct_complete_%s.png' % sid
        t5['icon'] = 'struct_finishings_%s.png' % sid
        stages[3:] = [t4, t5]
        ages = [(0, 12), (12, 30), (30, 60), (60, 80), (80, 100)]
        for s, (a0, a1) in zip(stages, ages):
            s['age_min'], s['age_max'] = a0, a1
        g['growth']['total_stages'] = 5
        g['growth']['icon_stage'] = 5
        del old
    for s in stages:
        s['model'] = ''
    json.dump(g, open(gpath, 'w', encoding='utf-8'), indent=2)

    tmpl_stage = {f: json.load(open(os.path.join(STRUCTURES, TEMPLATE, 'stages', f, f + '_' + TEMPLATE + '.json'), encoding='utf-8'))
                  for f in STAGE_FOLDERS if os.path.isdir(os.path.join(STRUCTURES, TEMPLATE, 'stages', f))}
    for st, folder in zip(stages, stage_names(want)):
        d = os.path.join(STRUCTURES, sid, 'stages', folder)
        os.makedirs(d, exist_ok=True)
        mp = os.path.join(d, '%s_%s.json' % (folder, sid))
        m = copy.deepcopy(tmpl_stage[folder])
        m['id'] = '%s_%s' % (folder, sid)
        m['name'] = '%s - %s' % (cfg['name'], st['name'].capitalize())
        m['description'] = 'The %s construction phase of the %s.' % (st['name'], cfg['name'].lower())
        m['icon'] = m['id'] + '.png'
        cf = m['category_fields']
        cf['dimensions_m'] = {'width': cfg['w'], 'depth': cfg['d'], 'height': cfg['found_h'] if folder == 'struct_foundation' else cfg['h_total']}
        cf['construction_recipe'] = copy.deepcopy(st['construction_recipe'])
        cf['required_tools'] = copy.deepcopy(st['required_tools'])
        cf['room_count'] = len(cfg.get('partitions', []))
        m['properties']['weight_kg'] = round(cfg['w'] * cfg['d'] * 90.0, 1)
        m['properties']['base_value'] = round(cfg['w'] * cfg['d'] * 150.0, 1)
        m['models'] = []
        json.dump(m, open(mp, 'w', encoding='utf-8'), indent=2)
        readme = os.path.join(d, 'README.md')
        open(readme, 'w', encoding='utf-8').write('# %s\n\n![icon](%s.png)\n\nStage %d of the %s (generated by tools/make_building_stages.py).\n' % (m['name'], m['id'], st['stage'], cfg['name']))


# ------------------------------------------------------------------ main

def palette(cfg):
    p = cfg.get('palette', {})
    g = lambda k, d: p.get(k, d)  # noqa: E731
    siding = g('siding', (0.84, 0.8, 0.66))
    M = {
        'concrete': colour('Concrete', (0.62, 0.62, 0.6), 0.95), 'concrete_dark': colour('ConcreteDark', (0.45, 0.45, 0.44), 0.95),
        'steel': colour('Steel', (0.35, 0.36, 0.38), 0.5), 'lumber': colour('Lumber', (0.78, 0.62, 0.38)),
        'osb': colour('Sheathing', (0.72, 0.56, 0.34), 0.95), 'deck': colour('Deck', (0.62, 0.47, 0.3)),
        'floor': colour('Floor', (0.55, 0.4, 0.26)),
        'siding': colour('Siding', siding, 0.8 if cfg.get('style') != 'metal' else 0.45),
        'siding_dark': colour('SidingDark', tuple(v * 0.8 for v in siding), 0.6),
        'log': colour('Log', g('log', (0.42, 0.27, 0.14)), 0.9),
        'trim': colour('Trim', g('trim', (0.93, 0.93, 0.9)), 0.7), 'shutter': colour('Shutter', g('shutter', (0.2, 0.3, 0.38)), 0.8),
        'shingle': colour('Shingle', g('shingle', (0.24, 0.26, 0.3)), 0.9 if cfg.get('style') != 'metal' else 0.4),
        'shingle_dark': colour('ShingleDark', g('shingle_dark', (0.16, 0.17, 0.2)), 0.9),
        'interior': colour('Interior', (0.93, 0.91, 0.86), 0.9),
        'door': colour('Door', g('door', (0.45, 0.13, 0.11)), 0.7), 'door_panel': colour('DoorPanel', g('door_panel', (0.38, 0.1, 0.09)), 0.7),
        'brass': colour('Brass', (0.75, 0.6, 0.25), 0.4), 'brick': colour('Masonry', (0.55, 0.26, 0.2), 0.95),
        'alu': colour('Aluminium', (0.78, 0.8, 0.82), 0.4), 'pot': colour('Pot', (0.7, 0.36, 0.24), 0.9), 'plant': colour('Plant', (0.25, 0.5, 0.2), 0.9),
        'logend': colour('Firewood', (0.55, 0.38, 0.22), 0.9),
        'barrel': colour('Barrel', (0.2, 0.34, 0.5), 0.7),
        'glass': base.glass_material(),
    }
    return M


def build(sid):
    global glass_builder, FB, PB
    cfg = CONFIGS[sid]
    ensure_manifests(sid, cfg)
    M = palette(cfg)
    folders = stage_names(cfg['stages'])
    found_h = cfg['found_h']
    for folder in folders:
        sfolder = os.path.join(STRUCTURES, sid, 'stages', folder)
        mpath = os.path.join(sfolder, '%s_%s.json' % (folder, sid))
        d = json.load(open(mpath, encoding='utf-8'))
        dims = d['category_fields']['dimensions_m']
        for o in list(bpy.data.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        del base.EXTRA_OBJECTS[:]
        c = BCtx(cfg, cfg['h_total'], found_h)
        hs.glass_builder = None
        b = Builder(d['id'])
        glass_builder = Builder('WindowGlass')
        FB = Builder('Foundation')
        PB = Builder('Porch')
        if cfg['style'] == 'glass':
            greenhouse_stage(b, c, M, {'struct_foundation': 'foundation', 'struct_framing': 'framing', 'struct_walls': 'walls', 'struct_complete': 'complete'}[folder])
            glass_builder.bm.free()   # its glass is part of the walls and the roof
        elif folder == 'struct_foundation':
            foundation(b, c, M)
        elif folder == 'struct_framing':
            framing(b, c, M)
        elif folder == 'struct_walls':
            walls_stage(b, c, M)
        else:
            hs.glass_builder = glass_builder
            complete(b, c, M, finishings=(folder == 'struct_finishings'))
            base.EXTRA_OBJECTS.append(glass_builder.finish())
        base.EXTRA_OBJECTS.append(FB.finish())
        FB = None
        if PB.bm.verts:
            base.EXTRA_OBJECTS.append(PB.finish())   # the porch posts, beam and railing: the game hides them with the roof
        else:
            PB.bm.free()
        PB = None
        obj = b.finish()
        marker = bpy.data.objects.new('FrontMarker', None)
        marker.location = (0.0, -cfg['d'] / 2 - 0.8, 0.05)
        bpy.context.collection.objects.link(marker)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        marker.select_set(True)
        for extra in base.EXTRA_OBJECTS:
            extra.select_set(True)
        bpy.context.view_layer.objects.active = obj
        out = os.path.join(sfolder, d['id'] + '.glb')
        bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_yup=True)
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        for extra in base.EXTRA_OBJECTS:
            if getattr(extra, 'data', None) is not None and hasattr(extra.data, 'polygons'):
                tris += sum(len(p.vertices) - 2 for p in extra.data.polygons)
        d['models'] = [{'file': d['id'] + '.glb', 'format': 'glb', 'dimensions_m': {'x': dims['width'], 'y': dims['height'], 'z': dims['depth']}, 'triangles': tris}]
        json.dump(d, open(mpath, 'w', encoding='utf-8'), indent=2)
        print('stage', d['id'], tris, 'tris ->', out)


def main():
    argv = sys.argv
    names = argv[argv.index('--') + 1:] if '--' in argv else list(CONFIGS)
    for sid in names:
        build(sid)


if __name__ == '__main__':
    main()
