"""
The living / family room pack's palettes and textures (tools/living_models.py builds the furniture, tools/make_living_assets.py lists and exports it). It builds on the kitchen
pack's modelling kit (tools/kitchen_lib.py: the Mesh builder, materials, GLB export) and adds:

  * fabrics   a fine woven upholstery texture in each fabric colour, leather grain for the camel, and a rug pattern (border, field, medallion) in each colour
  * woods     tileable grain in each wood colour (mahogany, walnut, cherry, oak, birch) - white and black are plain painted
  * palettes  the colours of each STYLE: classic (burgundy, forest green, navy, camel; mahogany, walnut, cherry, oak) and modern (charcoal, stone, teal, mustard; birch, walnut,
              white, black). They are deliberately not the building-paint colours.

Textures are small tileable PNGs made with numpy (seeded) in assets/_living_textures/ and embedded in each GLB.
"""
import math
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitchen_lib as K  # noqa: E402

ROOT = K.ROOT
TEX_DIR = os.path.join(ROOT, 'assets', '_living_textures')
N = 256

from living_colors import FABRICS, WOOD_RGB, WOODS, colors  # noqa: E402,F401


def _noise(seed, scale):
    return K._fft_noise(seed, scale, N)


def _save(name, rgb):
    os.makedirs(TEX_DIR, exist_ok=True)
    path = os.path.join(TEX_DIR, name + '.png')
    img = bpy.data.images.new(name, N, N, alpha=False)
    px = np.ones((N, N, 4), dtype=np.float32)
    px[:, :, :3] = np.clip(rgb, 0.0, 1.0)
    img.pixels.foreach_set(px.reshape(-1))
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)
    return path


def _seed(key):
    """A seed from a name that is the same on every run (Python's hash() of a string is not)."""
    return 17 + sum((i + 1) * ord(c) for i, c in enumerate(key)) % 9973


def _weave(seed):
    """A fine woven cloth in 0..1 (threads over and under, a little uneven)."""
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    warp = 0.5 + 0.5 * np.sin(x * 2 * math.pi / 4.0)
    weft = 0.5 + 0.5 * np.sin(y * 2 * math.pi / 4.0)
    over = ((x // 4 + y // 4) % 2) == 0
    cloth = np.where(over, warp, weft)
    return 0.55 * cloth + 0.30 * _noise(seed, 1.0) + 0.15 * _noise(seed + 1, 6.0)


def fabric_texture(key, rgb):
    path = os.path.join(TEX_DIR, 'fabric_%s.png' % key)
    if not os.path.exists(path):
        w = _weave(_seed(key))
        _save('fabric_%s' % key, np.array(rgb, dtype=np.float32)[None, None, :] * (0.78 + 0.34 * w[:, :, None]))
    return path


def leather_texture(key, rgb):
    path = os.path.join(TEX_DIR, 'leather_%s.png' % key)
    if not os.path.exists(path):
        grain = 0.5 * _noise(81, 0.6) + 0.5 * _noise(82, 1.8)
        wear = _noise(83, 12.0)
        _save('leather_%s' % key, np.array(rgb, dtype=np.float32)[None, None, :] * (0.80 + 0.22 * grain[:, :, None] + 0.10 * (wear[:, :, None] - 0.5)))
    return path


def wood_texture(key):
    path = os.path.join(TEX_DIR, 'wood_%s.png' % key)
    if not os.path.exists(path):
        _, light, dark = WOOD_RGB[key]
        seed = 100 + sum(ord(c) for c in key)
        yy = (np.arange(N)[:, None] / N) * np.ones((1, N))
        w, w2 = _noise(seed, 18.0), _noise(seed + 1, 2.5)
        fine, streak = _noise(seed + 2, 1.2), _noise(seed + 3, 0.7)[:, :1] * np.ones((1, N))
        rings = np.sin((yy * 24.0 + w * 0.9 + w2 * 0.25) * 2 * math.pi) * 0.5 + 0.5
        t = np.clip(0.38 * rings + 0.22 * w2 + 0.10 * w + 0.15 * fine + 0.15 * streak, 0, 1)
        l, d = np.array(light, dtype=np.float32), np.array(dark, dtype=np.float32)
        _save('wood_%s' % key, d[None, None, :] * (1 - t[:, :, None]) + l[None, None, :] * t[:, :, None])
    return path


def rug_texture(key, rgb):
    """A rug seen from above (u, v = 0..1 across it): a fringe-less field with a border, an inner line and a diamond medallion, in tones of the colour."""
    path = os.path.join(TEX_DIR, 'rug_%s.png' % key)
    if not os.path.exists(path):
        y, x = np.mgrid[0:N, 0:N].astype(np.float32) / N
        base = np.array(rgb, dtype=np.float32)
        light = np.clip(base * 1.45 + 0.08, 0, 1)
        dark = base * 0.55
        edge = np.minimum(np.minimum(x, 1 - x), np.minimum(y, 1 - y))
        img = np.ones((N, N, 3), dtype=np.float32) * base
        img[(edge < 0.05)] = dark
        img[(edge > 0.05) & (edge < 0.065)] = light
        img[(edge > 0.10) & (edge < 0.115)] = light
        diamond = np.abs(x - 0.5) + np.abs(y - 0.5)
        img[diamond < 0.20] = light * 0.92
        img[(diamond > 0.20) & (diamond < 0.235)] = dark
        img[diamond < 0.12] = dark * 1.2
        img = img * (0.88 + 0.24 * _weave(_seed(key) + 7)[:, :, None])
        _save('rug_%s' % key, img)
    return path


def tex_material(name, path, rough, metal=0.0):
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    node = nt.nodes.new('ShaderNodeTexImage')
    node.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(node.outputs['Color'], bsdf.inputs['Base Color'])
    return m


class Palette:
    """The materials of one colour of one style of a piece: `main` is the colour that is varied (fabric or wood or rug ...), the rest are the style's fixed trim."""

    def __init__(self, style, kind, key):
        self.style, self.kind, self.key = style, kind, key
        self.classic = style == 'classic'
        mat = K.material
        # fixed trim
        self.brass = mat('Brass', (0.75, 0.58, 0.25), 0.30, 1.0)
        self.chrome = mat('Chrome', (0.82, 0.83, 0.85), 0.14, 1.0)
        self.blackmetal = mat('BlackMetal', (0.05, 0.05, 0.055), 0.40, 0.7)
        self.metal = self.brass if self.classic else self.blackmetal
        self.glass = mat('GlassClear', (0.70, 0.82, 0.88), 0.05)
        self.black = mat('BlackPlastic', (0.03, 0.03, 0.035), 0.35)
        self.screen = mat('ScreenDark', (0.01, 0.012, 0.016), 0.06)
        self.cream = mat('LivingCream', (0.92, 0.89, 0.80), 0.9)
        self.white = mat('LivingWhite', (0.93, 0.93, 0.91), 0.45)
        self.dark = mat('LivingDark', (0.07, 0.07, 0.075), 0.5)
        self.green = mat('LeafGreen', (0.14, 0.38, 0.16), 0.7)
        self.paper = mat('PaperWhite', (0.96, 0.95, 0.90), 0.9)
        self.main = self._main(kind, key)
        # frames and legs of an upholstered piece, and the cushions of a wooden one
        self.frame = self._wood('walnut' if self.classic else 'birch')
        self.cushion = self._fabric(FABRICS[style][0][0], FABRICS[style][0][2])

    def _fabric(self, key, rgb):
        if key == 'camel':
            return tex_material('Leather_' + key, leather_texture(key, rgb), 0.5)
        return tex_material('Fabric_' + key, fabric_texture(key, rgb), 0.92)

    def _wood(self, key):
        if key == 'white':
            return K.material('PaintWhite', (0.93, 0.93, 0.91), 0.45)
        if key == 'black':
            return K.material('PaintBlack', (0.05, 0.05, 0.055), 0.45)
        return tex_material('Wood_' + key, wood_texture(key), 0.5)

    def _main(self, kind, key):
        if kind == 'fabric':
            rgb = [c for k, _, c in FABRICS[self.style] if k == key][0]
            return self._fabric(key, rgb)
        if kind == 'rug':
            rgb = [c for k, _, c in FABRICS[self.style] if k == key][0]
            return tex_material('Rug_' + key, rug_texture(key, rgb), 0.95)
        if kind == 'wood':
            return self._wood(key)
        raise ValueError(kind)

    def rgb(self):
        for k, _, c in FABRICS[self.style]:
            if k == self.key:
                return c
        return (0.5, 0.5, 0.5)
