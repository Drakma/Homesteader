"""
Bitumen for asphalt: a 20 litre pail of bitumen binder (assets/building/building_bitumen_bucket), then its pallets of 9 and 18 on a pallet and the `bitumen` equivalency
(a pallet pays 9 or 18 buckets, like the other packs). An asphalt lot (docs/LOTS.md) is gravel aggregate mixed with bitumen.

    blender --background --python tools/make_bitumen.py
    blender --background --python tools/make_material_stacks.py -- building_bitumen_bucket
    python tools/render_icon_from_model.py assets/building/<id>/<id>.glb assets/building/<id>/<id>.png        (the bucket and each stack)
    python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_building_items as mod  # noqa: E402
import make_building_items2 as more  # noqa: E402


def main():
    items = [('building_bitumen_bucket', 'Bitumen (Bucket)', 'A 20 litre pail of bitumen binder: mixed with gravel aggregate it makes asphalt.',
              lambda: more.bucket('building_bitumen_bucket', 0.15, 0.38, (0.09, 0.09, 0.1), (0.16, 0.16, 0.18), (0.95, 0.72, 0.08)), 22.0, 10, 38, ['bitumen'])]
    mod.ITEMS = items
    mod.main()
    path = os.path.join(mod.ROOT, 'assets', '_schemas', 'equivalencies.json')
    d = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {'equivalencies': {}}
    eqs = d.setdefault('equivalencies', {})
    eqs['bitumen'] = {'unit': 'buckets', 'label': 'Bitumen',
                      'members': [{'item': 'building_bitumen_bucket', 'value': 1}, {'item': 'building_bitumen_bucket_stack_9', 'value': 9}, {'item': 'building_bitumen_bucket_stack_18', 'value': 18}]}
    with open(path, 'w', encoding='utf-8', newline=chr(10)) as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write(chr(10))
    print('bitumen equivalency written')


if __name__ == '__main__':
    main()
