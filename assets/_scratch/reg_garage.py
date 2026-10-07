import json
import os
os.chdir(r'C:\Users\casey\Desktop\Homesteader')


def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (p, a[:50])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8', newline='').write(s)


edit('assets/kit_config.json', [('''      "prefix": "laundry"
    }
''', '''      "prefix": "laundry"
    },
    "garage": {
      "name": "Garage & Workshop",
      "icon": "",
      "desc": "Workbenches, pegboards, steel tool chests and cabinets, shelving, parts cabinets, an air compressor and a bench grinder, each in a classic and a modern style and four colours: procedural low-poly models.",
      "prefix": "garage"
    }
''')])
edit('tools/generate_unity_asset_catalog.py', [('"laundry": "Laundry", ', '"laundry": "Laundry", "garage": "Garage", ')])
edit('tools/package_catalog_as_mods.py', [('    "laundry": (', '    "garage": ("Garage and Workshop Pack", "Workbenches, steel tool chests and cabinets, shelving, an air compressor and a bench grinder in classic and modern styles."),\n    "laundry": (')])
edit('Homesteader/Assets/Scripts/Modding/ModManifest.cs', [('        public const string Laundry = "laundry";', '        public const string Garage = "garage";           // garage and workshop furniture and tools\n        public const string Laundry = "laundry";'), ("Bedroom, Laundry, Material,", "Bedroom, Laundry, Garage, Material,")])
edit('docs/MODDING_GUIDE.md', [('`bedroom`, `laundry`, ', '`bedroom`, `laundry`, `garage`, ')])
d = json.load(open('assets/_schemas/laundry.schema.json'))
d['category'] = 'garage'
d['title'] = 'Garage & Workshop'
d['note'] = 'Garage and workshop pack (tools/make_garage_assets.py). The size (dimensions_m) comes from the universal _base_dimensions schema.'
f = d['fields']
f['garage_kind'] = f.pop('laundry_kind')
f['garage_kind']['note'] = 'Which piece: workbench, pegboard_wall, sawhorse, shop_stool, lumber_rack_wall, tool_chest_rolling, tool_chest_top, cabinet_tall, cabinet_base, wall_cabinet, steel_shelving, parts_cabinet, air_compressor or bench_grinder.'
f['color']['note'] = 'The colour of the painted steel (red, forest, navy, black, grey, orange, white) or of the wood (mahogany, walnut, cherry, oak, birch, white, black).'
f.pop('water_per_use_l', None)
f.pop('water_usage_lpm', None)
f['power_draw_w'] = {'type': 'number', 'required': False, 'min': 0, 'label': 'Power draw (W)', 'note': 'Watts drawn while it runs (the compressor, the grinder).'}
json.dump(d, open('assets/_schemas/garage.schema.json', 'w', encoding='utf-8', newline='\n'), indent=2)
open('assets/_schemas/garage.schema.json', 'a').write('\n')
open('docs/GARAGE.md', 'w', encoding='utf-8', newline='\n').write('''# Garage and workshop pack

A category of its own (`assets/garage/<id>/`, ids `garage_<piece>_<style>_<color>`). 14 pieces x 2 styles (classic, modern) x 4 colours = 112 items. Floor pieces are placeable, wall pieces mount on walls; all are bolted down (`wrench_remove`).

- Wood colour: workbench (vise), pegboard wall panel with tools (wall), sawhorse, shop stool.
- Painted-steel colour (classic red, forest green, navy, black; modern steel grey, matte black, safety orange, white): lumber rack (wall), rolling tool chest, top tool chest, tall cabinet, base cabinet with wood top, wall cabinet (wall), steel shelving with boxes, parts cabinet, air compressor (1500 W), bench grinder (400 W).

Code: `tools/garage_colors.py`, `tools/garage_lib.py`, `tools/garage_models.py`, `tools/make_garage_assets.py`; schema `assets/_schemas/garage.schema.json`.

```bash
blender --background --python tools/make_garage_assets.py
python tools/make_garage_assets.py --icons --force
python tools/generate_unity_asset_catalog.py && python tools/package_catalog_as_mods.py
```
''')
print('ok')
