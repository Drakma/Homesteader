"""Inspect the GLYPHS list for hyphen."""
import sys
sys.path.insert(0, r'C:\Users\casey\Desktop\Homesteader\assets\hud_kit\font')
import glyph_specs as g
print('total GLYPHS:', len(g.GLYPHS))
hyphen_count = 0
for spec in g.GLYPHS:
    if spec.char and 'hyphen' in (spec.name or ''):
        hyphen_count += 1
        print('  found:', spec.name, '/', repr(spec.char))
# Find any - in char
for spec in g.GLYPHS:
    if spec.char == chr(0x2D):
        print('  found by char:', spec.name, 'kclass=', spec.kclass)
print('hyphen records:', hyphen_count)
