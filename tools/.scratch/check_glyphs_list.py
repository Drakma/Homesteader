"""Check GLYPHS list directly."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\casey\Desktop\Homesteader\assets\hud_kit\font')
import glyph_specs as g

# Are hyphen and space in GLYPHS?
names = [s.name for s in g.GLYPHS]
print('hyphen in GLYPHS:', 'hyphen' in names)
print('space in GLYPHS:', 'space' in names)

# Index of hyphen in GLYPHS:
for i, s in enumerate(g.GLYPHS):
    if s.name == 'hyphen':
        print('hyphen at index', i, 'char=', repr(s.char), 'strokes triangles:', s.strokes)
        break

# Iterate through GLYPHS, find the first item
print('first 3 GLYPHS:', [(s.name, repr(s.char)) for s in g.GLYPHS[:3]])
