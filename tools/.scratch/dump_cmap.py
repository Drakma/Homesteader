"""Dump cmap table directly."""
from fontTools.ttLib import TTFont
f = TTFont(r'C:\Users\casey\Desktop\Homesteader\assets\hud_kit\font\homesteader_hud.ttf')
for table in f['cmap'].tables:
    print('platform ' + str(table.platformID) + ' encoding ' + str(table.platEncID) + ' format ' + str(table.format))
    cmap = table.cmap
    print('  codepoints (sorted):', sorted(cmap.keys())[:5], '...total:', len(cmap))
    if 32 in cmap:
        print('  space present! ->', cmap[32])
    else:
        print('  space (32) NOT present')
