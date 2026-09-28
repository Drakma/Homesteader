"""Bisect where 'hyphen' leaves the build chain."""
import io
import sys

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

sys.path.insert(0, r'C:\Users\casey\Desktop\Homesteader\assets\hud_kit\font')
import glyph_specs as g

UPEM = 1024
PX = UPEM // g.GLYPH_WIDTH

glyph_order = ['hyphen', '.notdef']
glyph_dict = {}

def add_rect(pen, pts):
    # pts: list of (px, py) on the design grid. y is flipped via
    # (ASCENDER - py). Starts new contour.
    for i, pt in enumerate(pts):
        x_fu = pt[0] * PX
        y_fu = (g.ASCENDER - pt[1]) * PX
        if i == 0:
            pen.moveTo((x_fu, y_fu))
        else:
            pen.lineTo((x_fu, y_fu))
    pen.closePath()

pen = TTGlyphPen(None)
add_rect(pen, [(4, 13), (12, 13), (12, 15), (4, 15), (4, 13)])
glyph_dict['hyphen'] = pen.glyph()

pen_nd = TTGlyphPen(None)
add_rect(pen_nd, [(0, 0), (16, 0), (16, 24), (0, 24), (0, 0)])
glyph_dict['.notdef'] = pen_nd.glyph()

fb = FontBuilder(UPEM, isTTF=True)
fb.setupGlyphOrder(glyph_order)
print('after setupGlyphOrder: hyphen in glyph order?',
      'hyphen' in fb.font.getGlyphOrder())
fb.setupCharacterMap({0x2D: 'hyphen'})
print('after setupCharacterMap: glyph table count:', len(fb.font['cmap'].tables))
for t in fb.font['cmap'].tables:
    print('  table', t.platformID, 'has 0x2D:', 0x2D in t.cmap)
fb.setupHorizontalMetrics({'hyphen': (16 * PX, 0), '.notdef': (16 * PX, 0)})
fb.setupHorizontalHeader(ascent=g.ASCENDER * PX, descent=0)
fb.setupNameTable({'familyName': 'Test', 'styleName': 'R'})
fb.setupOS2(sTypoAscender=g.ASCENDER * PX, sTypoDescender=0,
            usWinAscent=g.ASCENDER * PX, usWinDescent=0,
            usWeightClass=400)
fb.setupHead(unitsPerEm=UPEM)
print('right before setupGlyf: hyphen in order?',
      'hyphen' in fb.font.getGlyphOrder())
fb.setupGlyf(glyph_dict)
print('after setupGlyf: hyphen in order?',
      'hyphen' in fb.font.getGlyphOrder())
print('                  hyphen in glyf:',
      'hyphen' in fb.font.get('glyf', {}))
buf = io.BytesIO()
fb.font.save(buf)
buf.seek(0)
from fontTools.ttLib import TTFont
f = TTFont(buf)
print('after save+load: hyphen in glyph order?',
      'hyphen' in f.getGlyphOrder())
