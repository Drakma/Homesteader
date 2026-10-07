import os
os.chdir(r'C:\Users\casey\Desktop\Homesteader')


def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (p, a[:60])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8', newline='').write(s)


edit('Homesteader/Assets/Scripts/UI/HintsPanel.cs', [(
    '                H("Place it, or lay the path", "Enter"),',
    '                H("Place it, or lay the path or lot", "Enter"),\n                H("Lot blueprint in hand: click a corner, then the opposite corner (a rectangle of any size) or more corners (any shape); right click undoes the last corner", "Left Click"),\n                H("Break up a lot (pickaxe or shovel in hand)", "Shift", "Right Click"),')])
s = open('docs/CONTROLS.md', encoding='utf-8').read()
i = s.index('| Left click (path or road kit in hand)')
j = s.index('\n', i) + 1
s = s[:j] + ('| Left click (a lot blueprint in hand: dirt, gravel, asphalt or concrete) | Lays a corner of the lot on land you own. A second corner makes a RECTANGLE of any size (the preview follows the cursor); a third and more make any other shape. Enter lays it (the ped walks over and works kneeling), Backspace or right click takes the last corner back, Esc throws the plan away. A lot of A square metres uses ceil(A / lot_m2_per_item) of its material from the toolbar and the 4 m work site round the first corner | `LotBuilder` |\n'
             '| Shift + right click on a lot (a pickaxe or a shovel in the active slot) | Breaks the lot up (the surface goes, no material comes back) | `LotBuilder.TryBreakUp` |\n') + s[j:]
open('docs/CONTROLS.md', 'w', encoding='utf-8', newline='').write(s)
open('docs/LOTS.md', 'w', encoding='utf-8', newline='\n').write('''# Lots

A LOT is a flat area of any size and shape paved with dirt, gravel, asphalt or concrete: a yard, a drive, a parking area, a pad, a pen floor. Like paths and roads it is a blueprint bought once at the depot
(`lot_dirt`, `lot_gravel`, `lot_asphalt`, `lot_concrete`; `tools/make_lot_blueprints.py` writes the manifests and icons).

## Laying one
- Hold the blueprint and left click the CORNERS on land you own. One corner then the opposite one makes a RECTANGLE of any size (the preview follows the cursor); three or more corners make any other shape (at most 24).
- Enter lays it. Backspace or a right click takes the last corner back; Esc (or another slot) throws the plan away.
- A lot is 4 m^2 to 2,500 m^2, on land you own, out of water, with no crossing edges. Trees, planted crops and placed objects (a pile of material does not count) inside it refuse it: fell, harvest or move them first. Plants and rocks that are left are cleared when it is laid.
- The material is the blueprint's `lot_material_item`, one per `lot_m2_per_item` square metres (a lot of A m^2 uses ceil(A / that)), from the toolbar and the 4 m work site round the FIRST corner (as for paths and fences).
  Dirt: small dirt pile, 3.5 m^2 each. Gravel: medium gravel pile, 8 m^2. Asphalt: medium gravel pile, 6 m^2 (as the asphalt road). Concrete: a bag of concrete mix, 1.5 m^2.
- The ped walks to the nearest corner and works kneeling (2 to 14 seconds, by size); a movement key or Esc stops it and nothing is laid or used.
- **Shift + right click** on a lot with a pickaxe or a shovel breaks it up (nothing comes back). A newer lot lies a hair above an older one where they overlap.

## How it is drawn
`Growth/LotRun.cs`: the polygon is cut into triangles (ear clipping), then cut small (no edge over 1.5 m) so it follows the ground, and drawn 5 cm above it with a tiling surface of its own (dirt 4 m, gravel 2.5 m, asphalt 6 m, concrete 3 m slabs with an expansion joint along two edges). It has no collider: it is ground you walk, drive and build on.
`Growth/LotBuilder.cs` is the input, the preview and the laying. Saved in `GameSave.lots` (style, blueprint id, corner points).

## Manifest fields (base schema `_base_fences_paths`)
`lot_style` (dirt, gravel, asphalt, concrete), `lot_material_item`, `lot_m2_per_item`; the catalog generator passes them on (`AssetCatalogItem.lot_*`).

Not done yet: concrete asks only for the bag of mix (no water or mixer, unlike the structure recipes), and asphalt uses gravel as its stand-in material until there is an asphalt item.
''')
print('ok')
