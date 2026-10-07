import json
import os
os.chdir(r'C:\Users\casey\Desktop\Homesteader')


def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (p, a[:50])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8', newline='').write(s)


PACKS = [
    dict(key='dining', name='Dining Room', mod='Dining Room Pack', cs='Dining', code='Dining',
         desc='Dining tables, upholstered chairs and benches, china cabinets, bar carts and wine racks, each in a classic and a modern style and four colours: procedural low-poly models.',
         mdesc='Dining tables, upholstered chairs, china cabinets, bar carts and wine racks in classic and modern styles.',
         kinds='dining_table, round_table, china_cabinet, bar_cart, wine_rack, dining_chair, host_chair or dining_bench', n=8, count=64,
         lines='- Wood colour: dining table (seats six), round pedestal table, china cabinet with plates, bar cart with bottles, wine rack.\n- Fabric colour: dining chair, host chair with arms, dining bench.'),
    dict(key='office', name='Home Office', mod='Home Office Pack', cs='Office', code='Office',
         desc='Desks, credenzas, filing cabinets, whiteboards, cork boards and chairs, each in a classic and a modern style and four colours: procedural low-poly models.',
         mdesc='Desks, credenzas, filing cabinets, boards and office chairs in classic and modern styles.',
         kinds='office_desk, executive_desk, credenza, filing_cabinet, lateral_file, whiteboard_wall, corkboard_wall, office_chair or guest_chair', n=9, count=72,
         lines='- Wood colour: writing desk, executive desk, credenza, filing cabinet, lateral file, whiteboard (wall), cork board (wall).\n- Fabric colour: swivel office chair, guest chair.'),
]
base = json.load(open('assets/_schemas/bedroom.schema.json'))
for p in PACKS:
    k = p['key']
    last = '"laundry"' if False else None
    edit('assets/kit_config.json', [('''      "prefix": "garage"
    }
''', '''      "prefix": "garage"
    },
    "%s": {
      "name": "%s",
      "icon": "",
      "desc": "%s",
      "prefix": "%s"
    }
''' % (k, p['name'], p['desc'], k))] if k == 'dining' else [('''      "prefix": "dining"
    }
''', '''      "prefix": "dining"
    },
    "%s": {
      "name": "%s",
      "icon": "",
      "desc": "%s",
      "prefix": "%s"
    }
''' % (k, p['name'], p['desc'], k))])
    edit('tools/generate_unity_asset_catalog.py', [('"garage": "Garage", ' if k == 'dining' else '"dining": "Dining", ', ('"garage": "Garage", "dining": "Dining", ' if k == 'dining' else '"dining": "Dining", "office": "Office", '))])
    edit('tools/package_catalog_as_mods.py', [('    "garage": (' if k == 'dining' else '    "dining": (', '    "%s": ("%s", "%s"),\n%s' % (k, p['mod'], p['mdesc'], '    "garage": (' if k == 'dining' else '    "dining": ('))])
    edit('Homesteader/Assets/Scripts/Modding/ModManifest.cs', [('        public const string Garage = "garage";' if k == 'dining' else '        public const string Dining = "dining";',
                                                              '        public const string %s = "%s";%s// %s\n%s' % (p['code'], k, ' ' * 12, p['name'].lower() + ' furniture', '        public const string Garage = "garage";' if k == 'dining' else '        public const string Dining = "dining";')),
                                                             ("Laundry, Garage, Material," if k == 'dining' else "Garage, Dining, Material,", ("Laundry, Garage, Dining, Material," if k == 'dining' else "Garage, Dining, Office, Material,"))])
    edit('docs/MODDING_GUIDE.md', [('`laundry`, `garage`, ' if k == 'dining' else '`garage`, `dining`, ', ('`laundry`, `garage`, `dining`, ' if k == 'dining' else '`garage`, `dining`, `office`, '))])
    d = json.loads(json.dumps(base))
    d['category'] = k
    d['title'] = p['name']
    d['note'] = '%s pack (tools/make_%s_assets.py). The size (dimensions_m) comes from the universal _base_dimensions schema.' % (p['name'], k)
    f = d['fields']
    f['%s_kind' % k] = f.pop('bedroom_kind')
    f['%s_kind' % k]['note'] = 'Which piece: %s.' % p['kinds']
    json.dump(d, open('assets/_schemas/%s.schema.json' % k, 'w', encoding='utf-8', newline='\n'), indent=2)
    open('assets/_schemas/%s.schema.json' % k, 'a').write('\n')
    open('docs/%s.md' % k.upper(), 'w', encoding='utf-8', newline='\n').write('''# %s pack

A category of its own (`assets/%s/<id>/`, ids `%s_<piece>_<style>_<color>`). %d pieces x 2 styles (classic, modern) x 4 colours = %d items. Floor pieces are placeable, wall pieces mount on walls; all are bolted down (`wrench_remove`).

%s

Code: `tools/%s_models.py`, `tools/make_%s_assets.py` (palettes from `tools/living_lib.py`); schema `assets/_schemas/%s.schema.json`.

```bash
blender --background --python tools/make_%s_assets.py
python tools/make_%s_assets.py --icons --force
python tools/generate_unity_asset_catalog.py && python tools/package_catalog_as_mods.py
```
''' % (p['name'], k, k, p['n'], p['count'], p['lines'], k, k, k, k, k))
print('ok')
