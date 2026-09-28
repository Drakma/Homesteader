"""Look for hyphen in TTF — glyphOrder, cmap, post."""
from fontTools.ttLib import TTFont
f = TTFont(r'C:\Users\casey\Desktop\Homesteader\assets\hud_kit\font\homesteader_hud.ttf')
order = f.getGlyphOrder()
print('hyphen in glyph order:', 'hyphen' in order)
print('space in glyph order:', 'space' in order)
print('first 5 in order:', order[:5])
print('len(order):', len(order))

# Check that hyphen glyph is loaded into glyf.
glyf = f['glyf']
print('hyphen glyf exists:', 'hyphen' in glyf)
if 'hyphen' in glyf:
    g = glyf['hyphen']
    print('numberOfContours:', getattr(g, 'numberOfContours', '?'))

# Check cmap tables.
for i, tbl in enumerate(f['cmap'].tables):
    print('cmap table', i, 'platformId=', tbl.platformID, 'format=', tbl.format, 'count=', len(tbl.cmap))
    if 'hyphen' in tbl.cmap.values():
        print('  -> hyphen present!')
    if 0x2D in tbl.cmap:
        print('  -> U+002D present!')
