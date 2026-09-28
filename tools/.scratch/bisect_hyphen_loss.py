"""Bisect where 'hyphen' leaves the build chain."""
import os
import sys
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

sys.path.insert(0, r'C:\Users\casey\Desktop\Homesteader\assets\hud_kit\font')
import glyph_specs
import glyph_specs as g

UPEM = 1024
PX = UPEM // glyph_specs.GLYPH_WIDTH

# Build a minimal font with just the hyphen glyph and verify where it dies.
glyph_order = ['hyphen', '.notdef']
glyph_dict = {}
pen = TTGlyphPen(None)
for pt in [(4, 13), (12, 13), (12, 15), (4, 15), (4, 13)]:
    if pt == (4, 13):
        pen.moveTo((pt[0] * PX, (glyph_specs.ASCENDER - pt[1]) * PX))
    else:
        pen.lineTo((pt[0] * PX, (glyph_specs.ASCENDER - pt[1]) * PX))
pen.closePath()
glyph_dict['hyphen'] = pen.glyph()

# .notdef default
pen_nd = TTGlyphPen(None)
pen_nd.moveTo((0, 0)); pen_nd.lineTo((UPEM, 0))
pen_nd.lineTo((UPEM, 24 * PX)); pen_nd.lineTo((0, 24 * PX))
pen_nd.closePath()
glyph_dict['.notdef'] = pen_nd.glyph()

fb = FontBuilder(UPEM, isTTF=True)
fb.setupGlyphOrder(glyph_order)
print('after setupGlyphOrder: hyphen in order?',
      'hyphen' in fb.font.getGlyphOrder())
fb.setupCharacterMap({0x2D: 'hyphen'})
print('after setupCharacterMap: glyph table count:', len(fb.font['cmap'].tables))
for t in fb.font['cmap'].tables:
    print('  table', t.platformID, 'has 0x2D:', 0x2D in t.cmap)
fb.setupHorizontalMetrics({'hyphen': (16 * PX, 0), '.notdef': (16 * PX, 0)})
fb.setupHorizontalHeader(ascent=glyph_specs.ASCENDER * PX, descent=0)
fb.setupNameTable({'familyName': 'Test', 'styleName': 'R'})
fb.setupOS2(sTypoAscender=glyph_specs.ASCENDER * PX, sTypoDescender=0,
            usWinAscent=glyph_specs.ASCENDER * PX, usWinDescent=0,
            usWeightClass=400)
fb.setupHead(unitsPerEm=UPEM)
fb.setupGlyf(glyph_dict)
print('after setupGlyf: hyphen in order?',
      'hyphen' in fb.font.getGlyphOrder())
print('                  hyphens in glyf:',
      'hyphen' in fb.font.get('glyf', {}))
import io
buf = io.BytesIO()
fb.font.save(buf)
buf.seek(0)
from fontTools.ttLib import TTFont
f = TTFont(buf)
print('after save+load: hyphen in glyph order?',
      'hyphen' in f.getGlyphOrder())
