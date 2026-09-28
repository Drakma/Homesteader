"""Inspect what _build_hud_ttf._build_glyph produces for hyphen."""
import sys
sys.path.insert(0, r'C:\Users\casey\Desktop\Homesteader\assets\hud_kit\font')
import glyph_specs as g
import _build_hud_ttf as bh

# Find hyphen glyph
hyph = next(s for s in g.GLYPHS if s.name == 'hyphen')
print('hyphen name:', hyph.name, 'char:', repr(hyph.char), 'strokes:', hyph.strokes)

# What does _normalize produce?
norm = bh._normalize(hyph.strokes)
print('normalized:', norm)

# Build the glyph from the breaking routine.
pen_glyph = bh._build_glyph(hyph.strokes, 0, 0)
print('built glyph:', pen_glyph)
print('  numberOfContours:', getattr(pen_glyph, 'numberOfContours', '?'))
print('  bounds:', getattr(pen_glyph, 'xMin', '?'), getattr(pen_glyph, 'yMin', '?'),
      getattr(pen_glyph, 'xMax', '?'), getattr(pen_glyph, 'yMax', '?'))
