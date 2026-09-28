"""Check glyph order and outline of space in saved TTF."""
from fontTools.ttLib import TTFont
f = TTFont(r'C:\Users\casey\Desktop\Homesteader\assets\hud_kit\font\homesteader_hud.ttf')
order = f.getGlyphOrder()
print('first 5 in glyph order:', order[:5])
print('space in order?', 'space' in order)
# Check glyf table for an actual space glyph
glyf = f['glyf']
print('space glyf:', glyf['space'].numberOfContours if 'space' in glyf else 'absent')
