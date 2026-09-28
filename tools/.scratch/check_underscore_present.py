"""Check what the kit font GLYPHS list has."""
import sys
sys.path.insert(0, r'C:\Users\casey\Desktop\Homesteader\assets\hud_kit\font')
import glyph_specs as g

chars_in_specs = sorted(set(ord(s.char) for s in g.GLYPHS if s.char))
print('spec chars count:', len(chars_in_specs))
for cp in chars_in_specs:
    print('  U+' + format(cp, '04X'), chr(cp) if 0x20 <= cp < 0x7F else '?')
