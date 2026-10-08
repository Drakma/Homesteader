"""
The modelling kit for the kitchen pack (tools/make_kitchen_assets.py), in headless Blender: free, local, low-poly with real detail.

  * Mesh       a bmesh builder: bevelled boxes, rounded-rectangle prisms, cylinders, lathes (pots, kettles, bowls), extruded outlines. Every face gets box-projected UVs
               in metres (times a scale), so the tiling textures below sit on it at a real size. Boxes are flat shaded, turned shapes smooth with hard edges where asked.
  * textures   brushed steel, oak, walnut, butcher block, black granite, white marble: small tileable PNGs made with numpy (seeded, so the same every run) in
               assets/_kitchen_textures/. They are embedded in each GLB on export.
  * material   a Principled BSDF material (colour or texture, roughness, metallic) that the glTF exporter writes out as a PBR material.
  * FINISHES   the three appliance finishes (black, white, stainless) as sets of materials, so one model gives the whole series.

Conventions (as the rest of the kit): 1 unit = 1 m, pivot at the middle of the footprint, bottom at z = 0, FRONT = -Y.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(ROOT, 'assets', '_kitchen_textures')
TEX_N = 256


# ------------------------------------------------------------------ textures

def _fft_noise(seed, scale, n=TEX_N):
    """Tileable smooth noise in 0..1 (random numbers low-pass filtered in the frequency domain: periodic, so it wraps without a seam). Bigger scale = broader blobs."""
    rng = np.random.RandomState(seed)
    f = np.fft.fft2(rng.rand(n, n))
    fy = np.fft.fftfreq(n)[:, None]
    fx = np.fft.fftfreq(n)[None, :]
    f *= np.exp(-(fx * fx + fy * fy) * (scale * scale) * 40.0)
    a = np.real(np.fft.ifft2(f))
    a -= a.min()
    return a / max(1e-9, a.max())


def _save_png(name, rgb):
    """rgb: n x n x 3 floats 0..1 -> assets/_kitchen_textures/<name>.png (made with Blender's own image writer)."""
    os.makedirs(TEX_DIR, exist_ok=True)
    path = os.path.join(TEX_DIR, name + '.png')
    n = rgb.shape[0]
    img = bpy.data.images.new(name, n, n, alpha=False)
    px = np.ones((n, n, 4), dtype=np.float32)
    px[:, :, :3] = np.clip(rgb, 0.0, 1.0)
    img.pixels.foreach_set(px.reshape(-1))
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)
    return path


def _lerp(c0, c1, t):
    c0, c1 = np.array(c0, dtype=np.float32), np.array(c1, dtype=np.float32)
    return c0[None, None, :] * (1 - t[:, :, None]) + c1[None, None, :] * t[:, :, None]


def make_textures(force=False):
    """Writes the tileable textures (once) and returns {name: path}."""
    out = {}
    n = TEX_N
    jobs = {}

    def steel():
        rng = np.random.RandomState(11)
        rows = rng.rand(n)
        rows = np.convolve(np.r_[rows[-4:], rows, rows[:4]], np.ones(5) / 5, mode='same')[4:-4]      # the brush lines run along u: one value per row of v
        streak = rows[:, None] * np.ones((1, n))
        fine = _fft_noise(3, 1.5)
        broad = _fft_noise(5, 14.0)
        t = 0.55 + 0.30 * (streak - 0.5) + 0.18 * (fine - 0.5) + 0.10 * (broad - 0.5)
        base = np.clip(t, 0, 1)
        return _lerp((0.58, 0.60, 0.63), (0.86, 0.88, 0.90), base)

    def wood(seed, light, dark, freq=24.0, warp=0.9):
        y = (np.arange(n)[:, None] / n) * np.ones((1, n))
        x = (np.arange(n)[None, :] / n) * np.ones((n, 1))
        w = _fft_noise(seed, 18.0)
        w2 = _fft_noise(seed + 1, 2.5)
        fine = _fft_noise(seed + 2, 1.2)
        rings = np.sin((y * freq + w * warp + w2 * 0.25) * 2 * math.pi) * 0.5 + 0.5          # grain lines run along u
        streak = _fft_noise(seed + 3, 0.7)[:, :1] * np.ones((1, n))
        t = 0.38 * rings + 0.22 * w2 + 0.10 * w + 0.15 * fine + 0.15 * streak
        return _lerp(dark, light, np.clip(t, 0, 1))

    def butcher():
        base = wood(21, (0.78, 0.60, 0.38), (0.55, 0.38, 0.20), freq=16.0)
        blocks = 8
        cell = n // blocks
        out_img = base.copy()
        rng = np.random.RandomState(33)
        for i in range(blocks):                                           # strips side by side, each its own tone and a hairline seam between
            tone = 0.88 + 0.20 * rng.rand()
            out_img[:, i * cell:(i + 1) * cell, :] *= tone
            out_img[:, i * cell, :] *= 0.55
        return out_img

    def granite():
        a = _fft_noise(41, 0.8)
        b = _fft_noise(42, 2.0)
        fleck = (a > 0.90).astype(np.float32) * 0.30 + (b > 0.92).astype(np.float32) * 0.22
        t = 0.06 + 0.04 * b + fleck
        return np.repeat(np.clip(t, 0, 1)[:, :, None], 3, axis=2) * np.array([1.0, 1.0, 1.02], dtype=np.float32)

    def marble():
        x = (np.arange(n)[None, :] / n) * np.ones((n, 1))
        y = (np.arange(n)[:, None] / n) * np.ones((1, n))
        w = _fft_noise(51, 9.0)
        vein = np.abs(np.sin((x * 3 + y * 2 + w * 3.2) * math.pi))
        vein = np.clip(1 - vein * 7.0, 0, 1) ** 1.5
        cloud = _fft_noise(52, 6.0)
        t = 0.93 - 0.20 * vein * (0.5 + cloud) - 0.05 * cloud
        return np.repeat(np.clip(t, 0, 1)[:, :, None], 3, axis=2) * np.array([1.0, 1.0, 0.985], dtype=np.float32)

    jobs['steel'] = steel
    jobs['oak'] = lambda: wood(61, (0.80, 0.62, 0.40), (0.62, 0.44, 0.25))
    jobs['walnut'] = lambda: wood(71, (0.42, 0.28, 0.17), (0.24, 0.15, 0.09), freq=22.0)
    jobs['butcher'] = butcher
    jobs['granite'] = granite
    jobs['marble'] = marble
    for name, fn in jobs.items():
        path = os.path.join(TEX_DIR, name + '.png')
        if force or not os.path.exists(path):
            _save_png(name, fn())
        out[name] = path
    return out


def make_controls_texture(force=False):
    """The touch-control strip of the built-in cooktop: four groups (burner symbol, slide bar, 7-segment level), 1024 x 128, drawn with numpy. Not tiling: it is mapped once over the plate."""
    path = os.path.join(TEX_DIR, 'cooktop_controls.png')
    if os.path.exists(path) and not force:
        return path
    H, W = 128, 1024
    img = np.zeros((H, W, 3), dtype=np.float32)
    img[:] = (0.014, 0.016, 0.021)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

    def rect(x0, x1, y0, y1, col):
        img[int(y0):int(y1), int(x0):int(x1)] = col

    def ring(cx, cy, r, w, col):
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        m = np.clip(1.0 - np.abs(d - r) / w, 0, 1)[:, :, None]
        img[:] = img * (1 - m) + np.array(col, dtype=np.float32)[None, None, :] * m

    def disc(cx, cy, r, col):
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        m = np.clip(r - d + 0.5, 0, 1)[:, :, None]
        img[:] = img * (1 - m) + np.array(col, dtype=np.float32)[None, None, :] * m

    segs = {0: 'abcdef', 1: 'bc', 2: 'abdeg', 3: 'abcdg', 4: 'bcfg', 5: 'acdfg', 6: 'acdefg', 7: 'abc', 8: 'abcdefg', 9: 'abcdfg'}

    def digit(x, y, w, h, t, n, on, off):
        mid = y + h / 2
        sx0, sx1 = x + t, x + w - t
        boxes = {'a': (sx0, sx1, y, y + t), 'd': (sx0, sx1, y + h - t, y + h), 'g': (sx0, sx1, mid - t / 2, mid + t / 2),
                 'f': (x, x + t, y + t, mid), 'e': (x, x + t, mid, y + h - t), 'b': (x + w - t, x + w, y + t, mid), 'c': (x + w - t, x + w, mid, y + h - t)}
        for k, (a, b, c, d) in boxes.items():
            rect(a, b, c, d, on if k in segs[n] else off)

    cyan, dim, white, track = (0.10, 0.85, 0.95), (0.05, 0.075, 0.09), (0.78, 0.80, 0.82), (0.16, 0.18, 0.21)
    levels = (6, 0, 3, 0)
    sizes = (21, 15, 15, 21)
    for g in range(4):
        x0 = g * 256
        if g:
            rect(x0 - 1, x0 + 1, 22, 106, (0.07, 0.08, 0.10))                                  # a hairline between the groups
        ring(x0 + 36, 64, sizes[g], 1.8, white)                                                  # the burner symbol: its size
        ring(x0 + 36, 64, sizes[g] * 0.5, 1.6, white)
        sx0, sx1 = x0 + 74, x0 + 172
        rect(sx0, sx1, 61, 67, track)                                                            # the slide bar
        lit = sx0 + (sx1 - sx0) * levels[g] / 9.0
        if levels[g]:
            rect(sx0, lit, 61, 67, cyan)
            disc(lit, 64, 8, cyan)
        else:
            disc(sx0, 64, 8, (0.30, 0.32, 0.36))
        for k in range(10):
            tx = sx0 + (sx1 - sx0) * k / 9.0
            rect(tx - 1, tx + 1, 76, 84, (0.30, 0.32, 0.36))
        digit(x0 + 190, 28, 38, 72, 6, levels[g], cyan, dim)                                    # the level, 7 segments
        disc(x0 + 240, 100, 4, (0.95, 0.45, 0.10) if levels[g] else (0.12, 0.08, 0.05))        # the hot-surface light
    os.makedirs(TEX_DIR, exist_ok=True)
    out = bpy.data.images.new('cooktop_controls', W, H, alpha=False)
    px = np.ones((H, W, 4), dtype=np.float32)
    px[:, :, :3] = np.clip(img[::-1], 0, 1)          # row 0 of a Blender image is the bottom
    out.pixels.foreach_set(px.reshape(-1))
    out.filepath_raw = path
    out.file_format = 'PNG'
    out.save()
    bpy.data.images.remove(out)
    return path


def controls_material():
    """The cooktop's touch strip: the controls texture on a glossy dark glass, lit a little by itself so the digits glow."""
    m = bpy.data.materials.get('CooktopControls')
    if m is not None:
        return m
    m = bpy.data.materials.new('CooktopControls')
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 0.12
    img = bpy.data.images.load(make_controls_texture(), check_existing=True)
    node = nt.nodes.new('ShaderNodeTexImage')
    node.image = img
    node.interpolation = 'Linear'
    nt.links.new(node.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(node.outputs['Color'], bsdf.inputs['Emission Color'])
    bsdf.inputs['Emission Strength'].default_value = 0.8
    return m


# ------------------------------------------------------------------ materials

_TEX = None


def texture_path(name):
    global _TEX
    if _TEX is None:
        _TEX = make_textures()
    return _TEX[name]


def material(name, rgb=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, tex=None, emit=None):
    """A Principled BSDF material the glTF exporter writes as a PBR material; `tex` names one of the tileable textures (it replaces the plain colour)."""
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    if emit is not None:
        bsdf.inputs['Emission Color'].default_value = (emit[0], emit[1], emit[2], 1.0)
        bsdf.inputs['Emission Strength'].default_value = 1.0
    if tex is not None:
        img = bpy.data.images.load(texture_path(tex), check_existing=True)
        node = nt.nodes.new('ShaderNodeTexImage')
        node.image = img
        node.interpolation = 'Linear'
        nt.links.new(node.outputs['Color'], bsdf.inputs['Base Color'])
    return m


class Finish:
    """A set of materials for one finish of an appliance (or of a cabinet or table): the body, the handles and trim, and the parts every finish shares."""

    def __init__(self, name, body, trim, label):
        self.name = name
        self.body, self.trim, self.label = body, trim, label
        self.glass = material('GlassSmoked', (0.015, 0.016, 0.02), 0.05)
        self.chrome = material('Chrome', (0.82, 0.83, 0.85), 0.14, 1.0)
        self.rubber = material('Rubber', (0.025, 0.025, 0.027), 0.8)
        self.iron = material('CastIron', (0.05, 0.05, 0.055), 0.55, 0.6)
        self.steel = material('Stainless', (0.78, 0.80, 0.82), 0.40, 0.85, tex='steel')
        self.white = material('Enamel', (0.93, 0.93, 0.91), 0.28)
        self.black = material('BlackEnamel', (0.035, 0.035, 0.04), 0.30)
        self.lcd = material('Display', (0.05, 0.9, 0.55), 0.3, emit=(0.05, 0.9, 0.55))
        self.red = material('IndicatorRed', (0.9, 0.1, 0.05), 0.4, emit=(0.9, 0.1, 0.05))
        self.plastic = material('PlasticGrey', (0.55, 0.56, 0.57), 0.5)


def finishes():
    """The three appliance finishes."""
    steel = material('Stainless', (0.78, 0.80, 0.82), 0.40, 0.85, tex='steel')
    return {
        'stainless': Finish('stainless', steel, steel, 'Stainless Steel'),
        'white': Finish('white', material('Enamel', (0.93, 0.93, 0.91), 0.28), material('Chrome', (0.82, 0.83, 0.85), 0.14, 1.0), 'White'),
        'black': Finish('black', material('BlackEnamel', (0.035, 0.035, 0.04), 0.30), material('BlackTrim', (0.06, 0.06, 0.065), 0.35, 0.6), 'Black'),
    }


# ------------------------------------------------------------------ meshes

class Mesh:
    """A bmesh builder that gathers a model's parts and turns them into one object (one mesh, several materials)."""

    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.mats = []
        self.uv = self.bm.loops.layers.uv.new('UVMap')

    def mi(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def _finish_faces(self, faces, m, smooth=False, uvscale=1.0, swap=False):
        i = self.mi(m)
        for f in faces:
            if not f.is_valid:
                continue
            f.material_index = i
            f.smooth = smooth
            self._project(f, uvscale, swap)

    def _project(self, f, scale, swap=False):
        n = f.normal
        ax = max(range(3), key=lambda k: abs(n[k]))
        for loop in f.loops:
            c = loop.vert.co
            if ax == 0:
                u, v = c.y, c.z          # a face turned to the sides: along depth, up
            elif ax == 1:
                u, v = c.x, c.z          # front and back faces: along width, up (the brush lines run along the width)
            else:
                u, v = c.x, c.y          # top and bottom
            loop[self.uv].uv = ((v * scale, u * scale) if swap else (u * scale, v * scale))

    def _new_faces(self, before):
        return [f for f in self.bm.faces if f not in before]

    # -- primitives

    def box(self, x0, x1, y0, y1, z0, z1, m, r=0.0, seg=2, uv=1.0):
        """A box; r > 0 rounds every edge (seg steps). Flat shaded."""
        before = set(self.bm.faces)
        res = bmesh.ops.create_cube(self.bm, size=1.0)
        for v in res['verts']:
            v.co.x = x0 + (v.co.x + 0.5) * (x1 - x0)
            v.co.y = y0 + (v.co.y + 0.5) * (y1 - y0)
            v.co.z = z0 + (v.co.z + 0.5) * (z1 - z0)
        if r > 1e-5:
            rr = min(r, 0.49 * min(x1 - x0, y1 - y0, z1 - z0))
            edges = list({e for v in res['verts'] for e in v.link_edges})
            bmesh.ops.bevel(self.bm, geom=edges, offset=rr, offset_type='OFFSET', segments=seg, profile=0.5, affect='EDGES')
        self._finish_faces(self._new_faces(before), m, False, uv, swap=(z1 - z0) > 1.5 * max(x1 - x0, y1 - y0))   # a tall part: the grain runs up and down

    def rbox(self, x0, x1, y0, y1, z0, z1, m, r, rv=None, seg=3, uv=1.0, caps=True):
        """A rounded-rectangle prism: the outline in plan (x, y) has corner radius r; the top and bottom edges are bevelled by rv (None = sharp). Smooth round corners, flat faces."""
        before = set(self.bm.faces)
        pts = []
        r = min(r, 0.499 * min(x1 - x0, y1 - y0))
        corners = ((x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180), (x1 - r, y0 + r, 270))
        for cx, cy, a0 in corners:
            for k in range(seg + 1):
                a = math.radians(a0 + 90.0 * k / seg)
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        self._extrude(pts, z0, z1, m, uv, bevel=rv)

    def prism(self, pts, z0, z1, m, uv=1.0):
        """An outline in plan (x, y) points, counter-clockwise, extruded from z0 to z1 (flat shaded)."""
        self._extrude(pts, z0, z1, m, uv)

    def _extrude(self, pts, z0, z1, m, uv, bevel=None):
        before = set(self.bm.faces)
        lo = [self.bm.verts.new((x, y, z0)) for x, y in pts]
        hi = [self.bm.verts.new((x, y, z1)) for x, y in pts]
        n = len(pts)
        faces = [self.bm.faces.new(lo[::-1]), self.bm.faces.new(hi)]
        for k in range(n):
            j = (k + 1) % n
            faces.append(self.bm.faces.new((lo[k], lo[j], hi[j], hi[k])))
        if bevel and bevel > 1e-5:
            edges = []
            for f in faces[:2]:
                edges += list(f.edges)
            bmesh.ops.bevel(self.bm, geom=list({e for e in edges}), offset=min(bevel, 0.45 * (z1 - z0)), offset_type='OFFSET', segments=2, profile=0.5, affect='EDGES')
        self.bm.normal_update()   # faces made by hand have no normal yet, and the box projection of the textures reads it (a prism's top was projected like a side: streaks, a different colour)
        self._finish_faces(self._new_faces(before), m, False, uv)

    def quad_top(self, x0, x1, y0, y1, z, m):
        """One upward face with the UVs spread 0..1 over it (u along x, v along y: for a texture drawn once, not tiled)."""
        vs = [self.bm.verts.new(c) for c in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]
        f = self.bm.faces.new(vs)
        self.bm.normal_update()
        f.material_index = self.mi(m)
        f.smooth = False
        for loop, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            loop[self.uv].uv = uv

    def cyl(self, p0, p1, r, m, seg=16, r1=None, caps=True, smooth=True, uv=1.0):
        """A cylinder (a cone when r1 is given: r at p0, r1 at p1) between two points."""
        before = set(self.bm.faces)
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        length = d.length
        if length < 1e-6:
            return
        res = bmesh.ops.create_cone(self.bm, cap_ends=caps, cap_tris=False, segments=seg, radius1=r, radius2=(r if r1 is None else r1), depth=length)
        rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
        mx = Matrix.Translation((p0 + p1) / 2) @ rot
        bmesh.ops.transform(self.bm, matrix=mx, verts=res['verts'])
        new = self._new_faces(before)
        self._finish_faces(new, m, smooth, uv)
        if smooth:
            for f in new:                                              # the end caps stay flat so their rim stays crisp
                if len(f.verts) == seg:
                    f.smooth = False

    def lathe(self, profile, m, at=(0.0, 0.0, 0.0), seg=24, hard=(), smooth=True, uv=1.0, closed_axis=True):
        """Turns a profile [(r, z), ...] round the vertical axis through `at`. `hard` lists the profile points where the surface has a crease (a rim, a base)."""
        before = set(self.bm.faces)
        ax, ay, az = at
        rings = []
        for r, z in profile:
            if r <= 1e-6:
                rings.append([self.bm.verts.new((ax, ay, az + z))])
            else:
                rings.append([self.bm.verts.new((ax + r * math.cos(2 * math.pi * k / seg), ay + r * math.sin(2 * math.pi * k / seg), az + z)) for k in range(seg)])
        for a in range(len(rings) - 1):
            ra, rb = rings[a], rings[a + 1]
            for k in range(seg):
                j = (k + 1) % seg
                if len(ra) == 1 and len(rb) == 1:
                    continue
                if len(ra) == 1:
                    self.bm.faces.new((ra[0], rb[j], rb[k]))
                elif len(rb) == 1:
                    self.bm.faces.new((ra[k], ra[j], rb[0]))
                else:
                    self.bm.faces.new((ra[k], ra[j], rb[j], rb[k]))
        new = self._new_faces(before)
        self._finish_faces(new, m, smooth, uv)
        bmesh.ops.recalc_face_normals(self.bm, faces=[f for f in new if f.is_valid])
        for idx in hard:
            for v in rings[idx]:
                for e in v.link_edges:
                    if e.verts[0] in rings[idx] and e.verts[1] in rings[idx]:
                        e.smooth = False

    def shift(self, dx=0.0, dy=0.0, dz=0.0):
        """Moves everything built so far (a wall item is built centred, then slid so its back is the plane y = 0)."""
        bmesh.ops.translate(self.bm, vec=(dx, dy, dz), verts=self.bm.verts[:])

    # -- finishing

    def tris(self):
        return sum(len(f.verts) - 2 for f in self.bm.faces)

    def build(self):
        """The finished object (linked into the scene)."""
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        for m in self.mats:
            me.materials.append(m)
        tris = self.tris()
        self.bm.free()
        o = bpy.data.objects.new(self.name, me)
        bpy.context.collection.objects.link(o)
        o['triangles'] = tris
        return o


def reset_scene():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)


def export_glb(obj, path):
    """Writes the object as a GLB (textures embedded, Y up: Blender -Y front lands on glTF +Z)."""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True, export_image_format='AUTO', export_apply=False)


def bounds(obj):
    """(min, max) corners of the object in metres."""
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))), Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
