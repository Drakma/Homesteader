"""
Builds the foundation, framing and walls models of a log-cabin style structure (the finished model is a separate asset) as GLBs in
headless Blender: free, local, low-poly, no Meshy credits. Sizes come from the stage manifests under
assets/structures/<id>/stages/<stage>/ (dimensions_m: width = x, depth = y, height = the stage's overall height), pivot centred on
the footprint with the ground at z = 0, front (the door) on the -Y side.

  foundation  a concrete slab with a low lip and a front step
  framing     the slab, timber wall studs and plates, a door and a window opening, gable studs, ridge beam and rafters
  walls       the slab, stacked round logs with the same openings, log gables, ridge beam and rafters (no roof boards)
  complete    the walls, roof boards and ridge cap, a plank door with its frame, a glazed window, a stone chimney

    blender --background --python tools/make_structure_stages.py -- small_cabin

It writes <stage item id>.glb beside each stage manifest, sets the manifest's models, and (afterwards, with the normal tools)
the icons are rendered from the models: python tools/render_icon_from_model.py <glb> <png>.
"""
import json
import math
import os
import sys

import bmesh
import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRUCTURES = os.path.join(ROOT, 'assets', 'structures')

WALL_H = 2.7          # eave height of the log walls, metres (the doorway is 2.3 m, the player 1.8 m)
LOG_D = 0.2           # log diameter
DOOR_W, DOOR_H = 1.2, 2.3    # wide and tall enough for the player (0.7 m capsule plus skin, 1.8 m tall) to pass with room to spare
WIN_W, WIN_H, WIN_SILL = 0.8, 0.8, 0.95


def material(name, rgb, rough=0.9):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1.0)
    b.inputs['Roughness'].default_value = rough
    return m


def glass_material():
    # roughness 0.85, not a mirror: a smooth pane reflects the (daytime) sky probe, so every window glowed pale blue at night
    m = material('Glass', (0.6, 0.78, 0.9), 0.85)
    m.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = 0.3
    for attr, val in (('blend_method', 'BLEND'), ('surface_render_method', 'BLENDED')):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    return m


class Builder:
    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.mats = []

    def mat_index(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def box(self, x0, x1, y0, y1, z0, z1, m, uv=False):
        """A box. With uv=True its faces get UVs that run 0..1 across the box (u along its wide horizontal side, v up), for a door leaf or a shutter: the game lays
        a grayscale panel or louvre picture on them (StructureLook.cs), tinted by the paint, so the panels are a picture and not geometry."""
        i = self.mat_index(m)
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        for v in r['verts']:
            v.co.x = x0 + (v.co.x + 0.5) * (x1 - x0)
            v.co.y = y0 + (v.co.y + 0.5) * (y1 - y0)
            v.co.z = z0 + (v.co.z + 0.5) * (z1 - z0)
        faces = [f for f in self.bm.faces if all(v in r['verts'] for v in f.verts)]
        for f in faces:
            f.material_index = i
        if uv:
            layer = self.bm.loops.layers.uv.verify()
            sx, sy, sz = (max(1e-6, x1 - x0), max(1e-6, y1 - y0), max(1e-6, z1 - z0))
            thin = 0 if sx < sy else 1                           # the slab's thickness axis: its two big faces (inside and outside) face along it
            for f in faces:
                n = f.normal
                ax = max(range(3), key=lambda k: abs(n[k]))
                for loop in f.loops:
                    co = loop.vert.co
                    if ax != thin:                               # an edge (the sides, the top, the bottom): a plain part of the picture, so the pattern is only on the big faces
                        loop[layer].uv = (0.03, 0.5)
                        continue
                    u = (co.y - y0) / sy if ax == 0 else (co.x - x0) / sx            # across the face (a face turned to +-x runs along y, one turned to +-y along x)
                    v = (co.z - z0) / sz
                    loop[layer].uv = (min(1.0, max(0.0, u)), min(1.0, max(0.0, v)))

    def log(self, a, b, radius, m, sides=8):
        """A round log between two points (cylinder, capped)."""
        i = self.mat_index(m)
        ax, ay, az = a
        bx, by, bz = b
        d = (bx - ax, by - ay, bz - az)
        length = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2)
        if length < 0.02:
            return
        dx, dy, dz = d[0] / length, d[1] / length, d[2] / length
        # a perpendicular pair
        up = (0.0, 0.0, 1.0) if abs(dz) < 0.95 else (1.0, 0.0, 0.0)
        ux = dy * up[2] - dz * up[1]
        uy = dz * up[0] - dx * up[2]
        uz = dx * up[1] - dy * up[0]
        ul = math.sqrt(ux * ux + uy * uy + uz * uz)
        ux, uy, uz = ux / ul, uy / ul, uz / ul
        vx = dy * uz - dz * uy
        vy = dz * ux - dx * uz
        vz = dx * uy - dy * ux
        ring_a, ring_b = [], []
        for s in range(sides):
            t = 2 * math.pi * s / sides
            cx, cy, cz = math.cos(t) * radius, math.sin(t) * radius, 0
            off = (ux * cx + vx * cy, uy * cx + vy * cy, uz * cx + vz * cy)
            ring_a.append(self.bm.verts.new((ax + off[0], ay + off[1], az + off[2])))
            ring_b.append(self.bm.verts.new((bx + off[0], by + off[1], bz + off[2])))
        faces = []
        for s in range(sides):
            n = (s + 1) % sides
            faces.append(self.bm.faces.new((ring_a[s], ring_a[n], ring_b[n], ring_b[s])))
        faces.append(self.bm.faces.new(ring_a[::-1]))
        faces.append(self.bm.faces.new(ring_b))
        for f in faces:
            f.material_index = i

    def prism_gable(self, x0, x1, y, thick, z_eave, z_ridge, m):
        """A triangular gable wall (profile in XZ) of the given thickness at depth y."""
        i = self.mat_index(m)
        xm = (x0 + x1) / 2
        pts = [(x0, z_eave), (x1, z_eave), (xm, z_ridge)]
        front = [self.bm.verts.new((x, y - thick / 2, z)) for x, z in pts]
        back = [self.bm.verts.new((x, y + thick / 2, z)) for x, z in pts]
        faces = [self.bm.faces.new(front[::-1]), self.bm.faces.new(back)]
        for k in range(3):
            n = (k + 1) % 3
            faces.append(self.bm.faces.new((front[k], front[n], back[n], back[k])))
        for f in faces:
            f.material_index = i

    def roof_slab(self, x_eave, z_eave, z_ridge, y0, y1, thick, m):
        """One roof plane: from the eave (x_eave, z_eave) up to the ridge (x = 0, z_ridge), along y0..y1, `thick` deep (straight down)."""
        i = self.mat_index(m)
        top = [(x_eave, y0, z_eave), (0.0, y0, z_ridge), (0.0, y1, z_ridge), (x_eave, y1, z_eave)]
        tv = [self.bm.verts.new(c) for c in top]
        bv = [self.bm.verts.new((c[0], c[1], c[2] - thick)) for c in top]
        faces = [self.bm.faces.new(tv), self.bm.faces.new(bv[::-1])]
        for k in range(4):
            n = (k + 1) % 4
            faces.append(self.bm.faces.new((tv[k], bv[k], bv[n], tv[n])))
        for f in faces:
            f.material_index = i

    def finish(self):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        # box-projected UVs in METRES (1 unit = 1 m) on the masonry materials (the chimney's "Masonry", a brick foundation's "FoundationFace"): the game
        # lays a brick or stone picture on them (StructureLook.cs); courses run level. Everything else keeps no UVs.
        textured = [i for i, m in enumerate(self.mats) if m.name.split('.')[0] in ('Masonry', 'FoundationFace', 'Floor')]   # (Blender numbers repeated names: FoundationFace.010)
        if textured:
            uvl = me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')   # (a door or shutter box may have put UVs in already)
            for poly in me.polygons:
                if poly.material_index not in textured:
                    continue
                n = poly.normal
                ax = max(range(3), key=lambda i: abs(n[i]))
                a2, b2 = ((1, 2), (0, 2), (0, 1))[ax]
                for li in poly.loop_indices:
                    v = me.vertices[me.loops[li].vertex_index].co
                    uvl.data[li].uv = (v[a2], v[b2])
        o = bpy.data.objects.new(self.name, me)
        bpy.context.collection.objects.link(o)
        return o


FOUNDATION_BUILDER = None   # when set (main), the slab goes into this separate object ("Foundation") so the game can swap it for another foundation style


def slab(b, w, d, h, concrete):
    b = FOUNDATION_BUILDER if FOUNDATION_BUILDER is not None else b
    b.box(-w / 2, w / 2, -d / 2, d / 2, 0.0, h, concrete)
    # a low lip around the edge and a front step
    lip = 0.05
    b.box(-w / 2, w / 2, -d / 2, -d / 2 + lip, h, h + 0.04, concrete)
    b.box(-w / 2, w / 2, d / 2 - lip, d / 2, h, h + 0.04, concrete)
    b.box(-w / 2, -w / 2 + lip, -d / 2, d / 2, h, h + 0.04, concrete)
    b.box(w / 2 - lip, w / 2, -d / 2, d / 2, h, h + 0.04, concrete)
    b.box(-0.7, 0.7, -d / 2 - 0.45, -d / 2, 0.0, h * 0.55, concrete)


def opening_x_ranges(wall, w, d):
    """x (or y) intervals that stay open on a wall: the door on the front (-Y), a window on the +X side. (lo, hi, z_lo, z_hi)"""
    if wall == 'front':
        return [(-DOOR_W / 2, DOOR_W / 2, 0.0, DOOR_H)]
    if wall == 'right':
        return [(-WIN_W / 2 + d * 0.12, WIN_W / 2 + d * 0.12, WIN_SILL, WIN_SILL + WIN_H)]
    return []


def roof_frame(b, w, d, base_z, ridge_z, timber):
    """Ridge beam along the depth (y) and rafters every ~0.9 m, from the eave plate up to the ridge."""
    ov = 0.25
    b.box(-0.06, 0.06, -d / 2 - ov, d / 2 + ov, ridge_z - 0.12, ridge_z, timber)
    n = max(3, int(d / 0.9) + 1)
    for k in range(n):
        y = -d / 2 + d * k / (n - 1)
        for side in (-1, 1):
            b.log((side * (w / 2 + ov), y, base_z - 0.1), (side * 0.04, y, ridge_z - 0.05), 0.055, timber, sides=6)
    # plates under the rafters
    for side in (-1, 1):
        b.box(side * (w / 2 - 0.12) - 0.06, side * (w / 2 - 0.12) + 0.06, -d / 2, d / 2, base_z - 0.12, base_z, timber)


def framing(b, w, d, h_total, found_h, mats):
    concrete, timber, _logm = mats
    slab(b, w, d, found_h, concrete)
    z0 = found_h + 0.04
    stud_w, stud_d = 0.09, 0.14
    top = z0 + WALL_H
    spacing = 0.6

    def studs_along(axis, fixed, length, openings):
        n = max(2, int(length / spacing) + 1)
        for k in range(n):
            s = -length / 2 + length * k / (n - 1)
            blocked = False
            for lo, hi, zlo, zhi in openings:
                if lo - 0.05 < s < hi + 0.05:
                    blocked = True
            z_a = z0
            if blocked:
                continue
            if axis == 'x':
                b.box(s - stud_w / 2, s + stud_w / 2, fixed - stud_d / 2, fixed + stud_d / 2, z_a, top, timber)
            else:
                b.box(fixed - stud_d / 2, fixed + stud_d / 2, s - stud_w / 2, s + stud_w / 2, z_a, top, timber)

    studs_along('x', -d / 2 + stud_d / 2, w - 0.2, opening_x_ranges('front', w, d))   # front, with the door gap
    studs_along('x', d / 2 - stud_d / 2, w - 0.2, [])
    studs_along('y', -w / 2 + stud_d / 2, d - 0.2, [])
    studs_along('y', w / 2 - stud_d / 2, d - 0.2, opening_x_ranges('right', w, d))
    # door and window frames: header, king studs and a sill
    b.box(-DOOR_W / 2 - 0.05, DOOR_W / 2 + 0.05, -d / 2, -d / 2 + stud_d, z0 + DOOR_H, z0 + DOOR_H + 0.12, timber)
    wlo, whi, _, _ = opening_x_ranges('right', w, d)[0][0], opening_x_ranges('right', w, d)[0][1], 0, 0
    b.box(w / 2 - stud_d, w / 2, wlo, whi, z0 + WIN_SILL - 0.1, z0 + WIN_SILL, timber)
    b.box(w / 2 - stud_d, w / 2, wlo, whi, z0 + WIN_SILL + WIN_H, z0 + WIN_SILL + WIN_H + 0.1, timber)
    # top plates
    b.box(-w / 2, w / 2, -d / 2, -d / 2 + stud_d, top, top + 0.09, timber)
    b.box(-w / 2, w / 2, d / 2 - stud_d, d / 2, top, top + 0.09, timber)
    b.box(-w / 2, -w / 2 + stud_d, -d / 2, d / 2, top, top + 0.09, timber)
    b.box(w / 2 - stud_d, w / 2, -d / 2, d / 2, top, top + 0.09, timber)
    # gable studs and the roof frame
    for y in (-d / 2 + stud_d / 2, d / 2 - stud_d / 2):
        for x in (-w * 0.3, -w * 0.15, 0.0, w * 0.15, w * 0.3):
            ridge_here = (top + 0.09) + (h_total - (top + 0.09)) * (1 - abs(x) / (w / 2 + 0.25))
            b.box(x - stud_w / 2, x + stud_w / 2, y - stud_w / 2, y + stud_w / 2, top + 0.09, ridge_here, timber)
    roof_frame(b, w, d, top + 0.09, h_total, timber)


def walls(b, w, d, h_total, found_h, mats, parts=None):
    """parts (the finished stage only): separate Builders named front/back/left/right/roof, so the game can cut the near walls and the roof away."""
    concrete, timber, logm = mats
    P = (lambda k: parts[k]) if parts else (lambda k: b)
    slab(b, w, d, found_h, concrete)
    z0 = found_h + 0.04
    r = LOG_D / 2
    courses = int(WALL_H / (LOG_D * 0.92))
    pitch = (WALL_H - r) / max(1, courses - 1)

    def run(wall, length, make):
        """One course of one wall, split around the openings."""
        for c in range(courses):
            zc = z0 + r + c * pitch
            gaps = [(lo, hi) for lo, hi, zl, zh in opening_x_ranges(wall, w, d) if zc + r > z0 + zl and zc - r < z0 + zh]
            lo_s = -length / 2 - (r if c % 2 == 0 else 0)
            hi_s = length / 2 + (r if c % 2 == 0 else 0)
            cuts = [lo_s]
            for g in sorted(gaps):
                cuts += [g[0], g[1]]
            cuts.append(hi_s)
            for k in range(0, len(cuts), 2):
                if cuts[k + 1] - cuts[k] > 0.05:
                    make(cuts[k], cuts[k + 1], zc, c)

    run('front', w, lambda a, bb, zc, c: P('front').log((a, -d / 2 + r, zc), (bb, -d / 2 + r, zc), r, logm))
    run('back', w, lambda a, bb, zc, c: P('back').log((a, d / 2 - r, zc), (bb, d / 2 - r, zc), r, logm))
    run('left', d, lambda a, bb, zc, c: P('left').log((-w / 2 + r, a, zc), (-w / 2 + r, bb, zc), r, logm))
    run('right', d, lambda a, bb, zc, c: P('right').log((w / 2 - r, a, zc), (w / 2 - r, bb, zc), r, logm))
    top = z0 + WALL_H
    # log gables and the open roof frame
    for y in (-d / 2 + r, d / 2 - r):
        P('front' if y < 0 else 'back').prism_gable(-w / 2, w / 2, y, LOG_D * 0.9, top, h_total - 0.1, logm)
    roof_frame(P('roof'), w, d, top, h_total, timber)
    # window frame, door frame
    P('front').box(-DOOR_W / 2 - 0.06, -DOOR_W / 2, -d / 2, -d / 2 + LOG_D, z0, z0 + DOOR_H + 0.1, timber)
    P('front').box(DOOR_W / 2, DOOR_W / 2 + 0.06, -d / 2, -d / 2 + LOG_D, z0, z0 + DOOR_H + 0.1, timber)
    P('front').box(-DOOR_W / 2 - 0.06, DOOR_W / 2 + 0.06, -d / 2, -d / 2 + LOG_D, z0 + DOOR_H, z0 + DOOR_H + 0.1, timber)


EXTRA_OBJECTS = []   # the hinge and the door leaf of the finished stage (exported with the building)


def chimney_with_fireplace(b, masonry, soot, stone, x_out, x_wall, bx, cy, half, z_floor, z_ceil, z_top):
    """
    A chimney against an EXTERIOR wall with a working fireplace (docs/STRUCTURE_STAGES_GUIDE.md, rules). The stack stands outside the wall
    (x_out to x_wall, from the ground up to z_top) with a flue hole in its cap; the breast continues inside the room (to bx) around a firebox
    opening 0.8 m high with a hearth in front. Build it into its own Builder named "Chimney": the game finds that object to know where a
    right click hit the chimney, and the empties FireboxPoint (where logs lie and the fire burns) and SmokePoint (the flue) it exports.
    """
    ow = half * 0.58                       # half the width of the firebox opening
    breast_top = z_floor + 0.4 * (z_ceil - z_floor)          # the breast inside is a MANTEL-height fireplace, about 40% of the wall, not a column to the ceiling
    fz0, fz1 = z_floor + 0.05, z_floor + 0.72
    depth = 0.3
    # the stack and its cap with the flue hole
    # the stack stops 0.12 m below the top of the cap: the flue hole is that deep, with the soot floor 5 cm thick, so no two surfaces sit within
    # millimetres of each other (depth fighting)
    b.box(x_out, x_wall, cy - half, cy + half, 0.0, z_top - 0.12, masonry)
    cap_out, ch = x_out - 0.06, half + 0.06
    xm = (x_out + x_wall) / 2
    hole = min(0.14, (x_wall - x_out) / 2 - 0.1)
    zc0, zc1 = z_top - 0.2, z_top + 0.08
    b.box(cap_out, xm - hole, cy - ch, cy + ch, zc0, zc1, stone)
    b.box(xm + hole, x_wall, cy - ch, cy + ch, zc0, zc1, stone)
    b.box(xm - hole, xm + hole, cy - ch, cy - hole, zc0, zc1, stone)
    b.box(xm - hole, xm + hole, cy + hole, cy + ch, zc0, zc1, stone)
    b.box(xm - hole, xm + hole, cy - hole, cy + hole, z_top - 0.12, z_top - 0.07, soot)    # the dark flue floor
    # the breast inside: back, two pillars, a lintel, the firebox floor
    x0 = x_wall - 0.02
    b.box(x0, bx - depth, cy - half, cy + half, z_floor, breast_top, masonry)
    b.box(x0, bx, cy - half, cy - ow, z_floor, breast_top, masonry)
    b.box(x0, bx, cy + ow, cy + half, z_floor, breast_top, masonry)
    b.box(x0, bx, cy - half, cy + half, fz1, breast_top, masonry)
    b.box(x0, bx + 0.08, cy - half - 0.08, cy + half + 0.08, breast_top, breast_top + 0.05, stone)          # the mantel shelf
    b.box(x0, bx, cy - ow, cy + ow, z_floor, fz0, masonry)
    # sooty lining on the back, sides and top of the firebox (4 mm proud: no coplanar faces)
    e = 0.004
    b.box(bx - depth, bx - depth + e, cy - ow, cy + ow, fz0, fz1, soot)
    b.box(bx - depth, bx, cy - ow, cy - ow + e, fz0, fz1, soot)
    b.box(bx - depth, bx, cy + ow - e, cy + ow, fz0, fz1, soot)
    b.box(bx - depth, bx, cy - ow, cy + ow, fz1 - e, fz1, soot)
    b.box(bx - depth, bx, cy - ow, cy + ow, fz0, fz0 + e, soot)
    # a hearth slab in front
    b.box(bx, bx + 0.4, cy - half - 0.1, cy + half + 0.1, z_floor, z_floor + 0.05, stone)
    pts = {}
    for name, loc in (('FireboxPoint', (bx - depth / 2, cy, fz0)), ('SmokePoint', (xm, cy, z_top + 0.08))):
        e_obj = bpy.data.objects.new(name, None)
        e_obj.location = loc
        bpy.context.collection.objects.link(e_obj)
        EXTRA_OBJECTS.append(e_obj)
        pts[name] = loc
    return pts


def interior_layer(parts, w, d, z0, top, interiorm):
    """A thin painted layer on the inside of the log walls (material 'Interior'), cut round the door and the window."""
    t = 0.02
    for wall in ('front', 'back', 'left', 'right'):
        length = w if wall in ('front', 'back') else d
        ops = opening_x_ranges(wall, w, d)
        zs = sorted({z0, top} | {z0 + o[2] for o in ops} | {z0 + o[3] for o in ops})
        for za, zb in zip(zs[:-1], zs[1:]):
            blocked = sorted((o[0], o[1]) for o in ops if za < z0 + o[3] - 1e-4 and zb > z0 + o[2] + 1e-4)
            lo, hi = -length / 2 + LOG_D, length / 2 - LOG_D
            cuts = [lo]
            for g in blocked:
                cuts += [max(lo, g[0]), min(hi, g[1])]
            cuts.append(hi)
            for k in range(0, len(cuts), 2):
                u0, u1 = cuts[k], cuts[k + 1]
                if u1 - u0 < 0.05:
                    continue
                p = parts[wall]
                if wall == 'front':
                    p.box(u0, u1, -d / 2 + LOG_D, -d / 2 + LOG_D + t, za, zb, interiorm)
                elif wall == 'back':
                    p.box(u0, u1, d / 2 - LOG_D - t, d / 2 - LOG_D, za, zb, interiorm)
                elif wall == 'left':
                    p.box(-w / 2 + LOG_D, -w / 2 + LOG_D + t, u0, u1, za, zb, interiorm)
                else:
                    p.box(w / 2 - LOG_D - t, w / 2 - LOG_D, u0, u1, za, zb, interiorm)


def complete(b, w, d, h_total, found_h, mats, finishings=False):
    """The enclosed building. finishings=True adds the baseboards of the finishing stage (paint, flooring and the chimney masonry are materials)."""
    concrete, timber, logm, roofm, doorm, glassm, stonem, masonrym, interiorm, floorm = mats
    # the log walls and the rafters are built a little lower than the finished height: the roof boards go ON TOP of the rafters
    h_frame = h_total - 0.14
    parts = {k: Builder(n) for k, n in (('front', 'Wall_Front'), ('back', 'Wall_Back'), ('left', 'Wall_Left'), ('right', 'Wall_Right'), ('roof', 'Roof'))}
    walls(b, w, d, h_frame, found_h, (concrete, timber, logm), parts)
    z0 = found_h + 0.04
    top = z0 + WALL_H
    ov = 0.3
    thick = 0.08
    margin = 0.07                       # the boards' underside rides this far above the rafters' centre line (rafter radius 0.055 + a little)
    z_eave = top - 0.1 + margin + thick
    ridge = h_frame - 0.05 + margin + thick
    # the inside: a painted layer on the walls and a floor (materials Interior and Floor are recoloured by the paint and flooring used)
    interior_layer(parts, w, d, z0, top, interiorm)
    b.box(-w / 2 + LOG_D, w / 2 - LOG_D, -d / 2 + LOG_D, d / 2 - LOG_D, z0, z0 + 0.03, floorm)
    if finishings:
        for wall in ('front', 'back', 'left', 'right'):                       # baseboards round the room
            length = w if wall in ('front', 'back') else d
            lo, hi = -length / 2 + LOG_D, length / 2 - LOG_D
            pieces = [(lo, hi)] if wall != 'front' else [(lo, -DOOR_W / 2), (DOOR_W / 2, hi)]
            for u0, u1 in pieces:
                zb0, zb1 = z0 + 0.03, z0 + 0.13
                if wall == 'front':
                    parts[wall].box(u0, u1, -d / 2 + LOG_D + 0.02, -d / 2 + LOG_D + 0.035, zb0, zb1, timber)
                elif wall == 'back':
                    parts[wall].box(u0, u1, d / 2 - LOG_D - 0.035, d / 2 - LOG_D - 0.02, zb0, zb1, timber)
                elif wall == 'left':
                    parts[wall].box(-w / 2 + LOG_D + 0.02, -w / 2 + LOG_D + 0.035, u0, u1, zb0, zb1, timber)
                else:
                    parts[wall].box(w / 2 - LOG_D - 0.035, w / 2 - LOG_D - 0.02, u0, u1, zb0, zb1, timber)
    # fill the gable ends up to the underside of the boards
    for y in (-d / 2 + LOG_D / 2, d / 2 - LOG_D / 2):
        parts['front' if y < 0 else 'back'].prism_gable(-w / 2, w / 2, y, LOG_D * 0.9, top + 0.12, h_frame + 0.02, logm)
    # roof boards on both sides with a ridge cap, and fascia boards along the eaves
    for side in (-1, 1):
        parts['roof'].roof_slab(side * (w / 2 + ov), z_eave, ridge, -d / 2 - ov, d / 2 + ov, thick, roofm)
        parts['roof'].box(side * (w / 2 + ov) - 0.04, side * (w / 2 + ov) + 0.04, -d / 2 - ov, d / 2 + ov, z_eave - thick - 0.04, z_eave + 0.03, timber)
    parts['roof'].box(-0.09, 0.09, -d / 2 - ov, d / 2 + ov, ridge - 0.03, ridge + 0.06, timber)
    # the front door is its own object on a hinge (DoorHinge > DoorLeaf) so the game can swing it open; the opening in the wall stays
    dw, dh = DOOR_W - 0.06, DOOR_H - 0.04
    leaf = Builder('DoorLeaf')
    leaf.box(0.0, dw, -0.04, 0.04, 0.0, dh, doorm)
    for x in (dw / 4, dw / 2, dw * 0.75):
        leaf.box(x - 0.012, x + 0.012, -0.05, -0.035, 0.05, dh - 0.05, timber)   # plank seams
    leaf.box(dw - 0.16, dw - 0.1, -0.1, 0.1, 1.0, 1.06, stonem)                   # a handle through the leaf
    leaf_obj = leaf.finish()
    hinge = bpy.data.objects.new('DoorHinge', None)
    hinge.location = (-dw / 2, -d / 2 + 0.07, z0)
    bpy.context.collection.objects.link(hinge)
    leaf_obj.parent = hinge
    EXTRA_OBJECTS.extend([hinge, leaf_obj])
    # the window on the +X side: a frame, a pane and a sill
    wlo, whi = opening_x_ranges('right', w, d)[0][0], opening_x_ranges('right', w, d)[0][1]
    zl, zh = z0 + WIN_SILL, z0 + WIN_SILL + WIN_H
    xw0, xw1 = w / 2 - LOG_D + 0.02, w / 2 - 0.02
    # the pane is its OWN object (WindowGlass): the game turns its shadow casting off so light passes through it, while the walls block it
    glass = Builder('WindowGlass')
    glass.box(xw0 + 0.06, xw0 + 0.1, wlo, whi, zl, zh, glassm)
    EXTRA_OBJECTS.append(glass.finish())
    for (ya, yb, za, zb) in ((wlo - 0.06, wlo, zl - 0.06, zh + 0.06), (whi, whi + 0.06, zl - 0.06, zh + 0.06),
                             (wlo - 0.06, whi + 0.06, zl - 0.06, zl), (wlo - 0.06, whi + 0.06, zh, zh + 0.06)):
        parts['right'].box(xw0, xw1 + 0.03, ya, yb, za, zb, timber)
    parts['right'].box(xw0 + 0.05, xw0 + 0.11, (wlo + whi) / 2 - 0.02, (wlo + whi) / 2 + 0.02, zl, zh, timber)   # a mullion
    parts['right'].box(xw0, xw1 + 0.1, wlo - 0.1, whi + 0.1, zl - 0.1, zl - 0.06, timber)                          # sill
    # the inside of the window: a lining through the wall (no outdoors showing between the round log ends) and a flat casing round the opening on the inner face
    xi = w / 2 - LOG_D - 0.02                      # the inner face, painted layer included
    kk, cw = 0.025, 0.1
    for (ya, yb, za, zb) in ((wlo - kk, wlo, zl - kk, zh + kk), (whi, whi + kk, zl - kk, zh + kk), (wlo, whi, zl - kk, zl), (wlo, whi, zh, zh + kk)):
        parts['right'].box(xi, w / 2 - 0.02, ya, yb, za, zb, timber)
    for (ya, yb, za, zb) in ((wlo - cw, wlo, zl - cw, zh + cw), (whi, whi + cw, zl - cw, zh + cw), (wlo, whi, zl - cw, zl), (wlo, whi, zh, zh + cw)):
        parts['right'].box(xi - 0.03, xi + 0.012, ya, yb, za, zb, timber)
    for part in parts.values():
        EXTRA_OBJECTS.append(part.finish())   # Wall_Front / Wall_Back / Wall_Left / Wall_Right / Roof: the game can hide them (cutaway view)
    # a stone chimney against the -X wall with a fireplace inside (its own object: "Chimney")
    chim = Builder('Chimney')
    chimney_with_fireplace(chim, masonrym, material('Soot', (0.08, 0.07, 0.07), 1.0), material('Hearth', (0.5, 0.49, 0.47), 0.95),
                           -w / 2 - 0.42, -w / 2 + 0.12, -w / 2 + 0.72, 0.55, 0.35, z0, top + 0.1, h_total)
    EXTRA_OBJECTS.append(chim.finish())


def finishings(b, w, d, h_total, found_h, mats):
    complete(b, w, d, h_total, found_h, mats, finishings=True)


def stage_manifest(structure, stage_folder):
    folder = os.path.join(STRUCTURES, structure, 'stages', stage_folder)
    for fn in sorted(os.listdir(folder)):
        if fn.endswith('.json'):
            return folder, os.path.join(folder, fn)
    raise FileNotFoundError(folder)


def main():
    argv = sys.argv
    structure = argv[argv.index('--') + 1] if '--' in argv else 'small_cabin'
    concrete = material('Concrete', (0.6, 0.6, 0.58), 0.95)
    timber = material('Timber', (0.74, 0.58, 0.36), 0.85)
    logm = material('Log', (0.42, 0.27, 0.14), 0.9)
    mats = (concrete, timber, logm)
    full_mats = (concrete, timber, logm, material('Roof', (0.30, 0.17, 0.12), 0.8), material('Door', (0.32, 0.2, 0.1), 0.85),
                 glass_material(), material('Stone', (0.52, 0.5, 0.48), 0.95), material('Masonry', (0.52, 0.5, 0.48), 0.95),
                 material('Interior', (0.9, 0.86, 0.78), 0.9), material('Floor', (0.55, 0.4, 0.26), 0.85))

    stage_list = [('struct_foundation', None), ('struct_framing', framing), ('struct_walls', walls), ('struct_complete', complete)]
    if os.path.isdir(os.path.join(STRUCTURES, structure, 'stages', 'struct_finishings')):
        stage_list.append(('struct_finishings', finishings))
    global FOUNDATION_BUILDER
    for stage_folder, fn in stage_list:
        folder, manifest_path = stage_manifest(structure, stage_folder)
        d = json.load(open(manifest_path, encoding='utf-8'))
        dims = d['category_fields']['dimensions_m']
        w, depth, h = dims['width'], dims['depth'], dims['height']
        found = json.load(open(stage_manifest(structure, 'struct_foundation')[1], encoding='utf-8'))['category_fields']['dimensions_m']['height']
        for o in list(bpy.data.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        b = Builder(d['id'])
        del EXTRA_OBJECTS[:]
        FOUNDATION_BUILDER = Builder('Foundation')    # the slab, lip and steps: its own object in every stage
        if fn is None:
            slab(b, w, depth, h, concrete)
        else:
            fn(b, w, depth, h, found, full_mats if fn in (complete, finishings) else mats)
        EXTRA_OBJECTS.append(FOUNDATION_BUILDER.finish())
        FOUNDATION_BUILDER = None
        obj = b.finish()
        # an empty named FrontMarker just in front of the door (the -Y side): the game reads it to know which way the front faces
        marker = bpy.data.objects.new('FrontMarker', None)
        marker.location = (0.0, -depth / 2 - 0.8, 0.05)
        bpy.context.collection.objects.link(marker)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        marker.select_set(True)
        for extra in EXTRA_OBJECTS:
            extra.select_set(True)
        bpy.context.view_layer.objects.active = obj
        out = os.path.join(folder, d['id'] + '.glb')
        bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_yup=True)
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        for extra in EXTRA_OBJECTS:
            if getattr(extra, 'data', None) is not None and hasattr(extra.data, 'polygons'):
                tris += sum(len(p.vertices) - 2 for p in extra.data.polygons)
        d['models'] = [{'file': d['id'] + '.glb', 'format': 'glb',
                        'dimensions_m': {'x': w, 'y': h, 'z': depth}, 'triangles': tris}]
        if fn in (complete, finishings):
            # the old Unreal-era model files of this stage are replaced: remove the legacy formats beside it
            for ext in ('.fbx', '.obj', '.mtl'):
                legacy = os.path.join(folder, d['id'] + ext)
                if os.path.exists(legacy):
                    os.remove(legacy)
        json.dump(d, open(manifest_path, 'w', encoding='utf-8'), indent=2)
        print('stage', d['id'], tris, 'tris ->', out)



if __name__ == '__main__':
    main()
