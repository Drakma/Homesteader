"""Check which specific characters are missing from current kit font."""
from fontTools.ttLib import TTFont
f = TTFont(r"C:\Users\casey\Desktop\Homesteader\assets\hud_kit\font\homesteader_hud.ttf")
cm = f.getBestCmap()
for c in [' ', '"', '#', '$', '-', '@', '`', '{', '|', '}']:
    print(repr(c), '->', 'YES' if ord(c) in cm else 'NO')
print('total codepoints:', len(cm))
