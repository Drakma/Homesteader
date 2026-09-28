import sys
sys.path.insert(0, r'C:\Users\casey\Desktop\Homesteader\assets\hud_kit\font')
from glyph_specs import GLYPHS
for g in GLYPHS:
    if g.name == 'space':
        print('space strokes:', g.strokes)
    if g.name == 'period':
        print('period strokes:', g.strokes)
