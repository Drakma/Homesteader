"""Confirm new glyph designers register without errors and GLYPHS list looks right."""
import sys
sys.path.insert(0, r'C:\Users\casey\Desktop\Homesteader\assets\hud_kit\font')
import glyph_specs as g
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print('GLYPHS total:', len(g.GLYPHS))
needed = ['"', '#', '$', '@', '`', '|', '{', '}', '°', '±', '²', '³', '×', '÷', '-']
for c in needed:
    spec = g.glyph_by_char(c)
    print('  ', repr(c), '->', 'OK' if spec else 'MISSING',
          '(' + (spec.name if spec else '?') + ')')
