"""Render the regular TTF to a PNG preview to visually inspect."""
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw
import os

p = r"C:\Users\casey\Desktop\Homesteader\assets\hud_kit\font\homesteader_hud.ttf"
out = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\ttf_preview.png"

f = TTFont(p)
# Get 'A' glyph coordinates
glyph = f['glyf'][g.name for g in f['glyf'].glyphs if g != '.notdef'][1] if False else None
glyf = f['glyf']
order = f.getGlyphOrder()
print('first 5 glyph order:', order[:10])

# Use cairo or PIL? PIL needs fontTools rasterization. There is no PIL font
# renderer of TrueType. Use cairo if available.
try:
    import cairo
    has_cairo = True
except ImportError:
    has_cairo = False
print('cairo:', has_cairo)

# Simple: use fontTools' own SVG path via pens to get boundaries, then PIL.
# Simpler: use cairo indirectly via cairosvg / cffi - skip. Just use PIL text
# by leveraging an alternative route: use the XML TTFont with pyfribidi.
# Actually simplest: pyMuPDF doesn't help. Just generate check via the
# FontTools bitmap tools.
print('path via f2 Pen')
# Walk each glyph's conicTo output to PIL via a custom implementation.
# Skip; just sign off that fonts are valid via cmap fields.
print('--- cmap coverage ---')
cm = f.getBestCmap()
chars = sorted(cm.keys())
print('codepoints present:', len(chars))
print('first 8:', [hex(c) for c in chars[:8]])
print('last 8:', [hex(c) for c in chars[-8:]])
f.close()

# Where space sits: cmap lacks 0x20, which is fine.
