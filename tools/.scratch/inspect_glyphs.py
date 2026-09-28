import sys
sys.path.insert(0, r'C:\Users\casey\Desktop\Homesteader\assets\hud_kit\font')
import glyph_specs as g
print('total GLYPHS:', len(g.GLYPHS))
space = [s for s in g.GLYPHS if s.name == 'space' or s.char == chr(0x20)]
print('space matches:')
for s in space:
    print('  ', s.name, repr(s.char), len(s.strokes), s.kclass)
print('first 5 GLYPHS:')
for s in g.GLYPHS[:6]:
    print('  ', s.name, repr(s.char), len(s.strokes), s.kclass)
