"""Map codepoints 0x20..0x7E and dump the lowest/highest registered."""
from fontTools.ttLib import TTFont
import io
import sys
f = TTFont(r'C:\Users\casey\Desktop\Homesteader\assets\hud_kit\font\homesteader_hud.ttf')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
cm = f.getBestCmap()
for cp in range(0x20, 0x7F):
    label = chr(cp) if 0x20 <= cp < 0x7F else '?'
    print(f"U+{cp:04X} '{label}' -> " + ('yes' if cp in cm else 'MISSING'))
print()
print('total codepoints:', len(cm))
print('lowest 5:', sorted(cm.keys())[:5])
print('highest 5:', sorted(cm.keys())[-5:])
