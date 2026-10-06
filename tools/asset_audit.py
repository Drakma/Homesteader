"""
Asset check: writes docs/ASSET_AUDIT.md, the list of items that need a model, a GLB, an icon or a pack (case / pallet / stack).

    python tools/asset_audit.py

A file-level check of the manifests under assets/<category>/<id>/: it does not judge how a model or an icon looks.
"""
import collections
import datetime
import hashlib
import json
import os
import re

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'assets')
OUT = os.path.join(ROOT, 'docs', 'ASSET_AUDIT.md')

# no model on purpose: built in code, staged, or data only
NO_MODEL_OK = {'hud', 'hud_kit', 'liquids', 'structures', 'peds'}
NO_MODEL_OK_PREFIX = ('fence_', 'gate_', 'path_', 'road_', 'mat_scoop_', 'clutter_', 'ground_', 'fuel_bulk_', 'fuel_service_')
PACK = re.compile(r'(_stack(_\d+|_large|_small)?|_pallet(_\d+|_large|_small)?|_case(_\d+)?|_box(_\d+)?|_bundle(_\d+|_large|_small)?|_pack(_\d+)?|_crate(_\d+)?|_coil|_spool(_small)?)$')
# categories where a pack makes sense, and what is left out of them
LAST = ['farming', 'food', 'appliances']          # user rule: these categories go at the bottom of every list
PACK_CATEGORIES =('building', 'farming', 'fuel', 'food', 'ingredients', 'materials')
PACK_SKIP = re.compile(r'^(building_paint_|box_|dock_|fence_|gate_|path_|road_|part_floor_|camp_|icon_|mat_pile_|mat_log_|mat_scoop_|fuel_pump_|fuel_tank_|lumber_bundle_|building_bundle_)|_container$|_drum_')


def load():
    items = {}
    for cat in sorted(os.listdir(ASSETS)):
        folder = os.path.join(ASSETS, cat)
        if cat.startswith('_') or not os.path.isdir(folder):
            continue
        for item in sorted(os.listdir(folder)):
            path = os.path.join(folder, item, item + '.json')
            if os.path.exists(path):
                try:
                    items[item] = (cat, json.load(open(path, encoding='utf-8')))
                except ValueError:
                    items[item] = (cat, None)
    return items


def model_files(m):
    return [(x.get('file') if isinstance(x, dict) else x) or '' for x in (m.get('models') or [])]


def audit(items):
    by = lambda: collections.defaultdict(list)
    r = {'bad_json': [], 'no_model': by(), 'grown': by(), 'broken': [], 'no_glb': by(), 'over': [], 'no_icon': [], 'bad_icon': [], 'thin_icon': [],
         'dup_icon': [], 'no_pack': by(), 'old_pack': []}
    hashes = collections.defaultdict(list)
    for item, (cat, m) in items.items():
        if m is None:
            r['bad_json'].append(item)
            continue
        folder = os.path.join(ASSETS, cat, item)
        files = model_files(m)
        if not files:
            if m.get('is_growable') and 'models' not in m:
                r['grown'][cat].append(item)
            elif cat not in NO_MODEL_OK and not item.startswith(NO_MODEL_OK_PREFIX):
                r['no_model'][cat].append(item)
        else:
            missing = [f for f in files if f and not os.path.exists(os.path.join(folder, f))]
            if missing and not any(f.lower().endswith('.glb') and f not in missing for f in files):
                r['broken'].append('%s (%s)' % (item, ', '.join(missing)))
            elif not any(f.lower().endswith('.glb') for f in files):
                r['no_glb'][cat].append(item)
        limit = 10000 if cat in ('structures', 'vehicles') else 5000
        for x in m.get('models') or []:
            if isinstance(x, dict) and (x.get('triangles') or 0) > limit:
                r['over'].append('%s (%d tris, limit %d)' % (item, x['triangles'], limit))
        icon = os.path.join(folder, item + '.png')
        if not os.path.exists(icon):
            r['no_icon'].append(item)
        else:
            im = Image.open(icon)
            if im.size != (128, 128) or im.mode != 'RGBA':
                r['bad_icon'].append('%s (%dx%d %s)' % (item, im.size[0], im.size[1], im.mode))
            else:
                alpha = im.getchannel('A')
                cover = alpha.histogram()
                cover = sum(cover[11:]) / 16384.0
                if cat not in NO_MODEL_OK and cover < 0.045:
                    r['thin_icon'].append('%s (%d%% of the icon)' % (item, round(cover * 100)))
                hashes[hashlib.md5(im.tobytes()).hexdigest()].append(item)
        p = m.get('properties') or {}
        if cat in PACK_CATEGORIES and (p.get('is_buyable') or p.get('stores')) and not PACK.search(item) and not PACK_SKIP.search(item):
            stem = re.sub(r's?$', '', item)
            if not any(j != item and PACK.search(j) and (j.startswith(item + '_') or j.startswith(stem + 's_')) for j in items):
                r['no_pack'][cat].append(item)
        if re.search(r'_(stack|bundle|pallet)_(large|small)$', item):
            r['old_pack'].append(item)
    r['dup_icon'] = [' = '.join(v) for v in hashes.values() if len(v) > 1 and not all(items[i][0] in NO_MODEL_OK for i in v)]
    return r


def section(out, title, note, groups):
    total = sum(len(v) for v in groups.values()) if isinstance(groups, dict) else len(groups)
    out.append('\n## %s (%d)\n' % (title, total))
    if note:
        out.append(note + '\n')
    if not total:
        out.append('None.\n')
    elif isinstance(groups, dict):
        for cat in sorted(groups, key=lambda c: (c in LAST, LAST.index(c) if c in LAST else 0, -len(groups[c]))):   # biggest first; LAST at the bottom
            out.append('\n### %s (%d)\n' % (cat, len(groups[cat])))
            out.extend('- [ ] `%s`' % i for i in groups[cat])
    else:
        out.extend('- [ ] `%s`' % i if ' ' not in i else '- [ ] %s' % i for i in groups)


def main():
    items = load()
    r = audit(items)
    out = ['# Asset Audit', '', 'Generated %s by `python tools/asset_audit.py` from %d manifests. Run it again to refresh; do not edit by hand.' %
           (datetime.date.today().isoformat(), len(items)), '',
           'A file-level check: it does not judge how a model or an icon looks.']
    section(out, 'Needs a model', 'No model at all, only an icon.', r['no_model'])
    section(out, 'Broken model link', 'The manifest names a model file that is not in the folder (old imperial names): a rename, not a new model.', r['broken'])
    section(out, 'Old OBJ / FBX only', 'No GLB. Convert with `tools/convert_models_to_glb.py` (rigged FBX stays FBX), or remake.', r['no_glb'])
    section(out, 'Over the triangle budget', '', r['over'])
    section(out, 'Icon missing', '', r['no_icon'])
    section(out, 'Icon not 128x128 RGBA', '', r['bad_icon'])
    section(out, 'Icon too thin to read', 'Long thin items that cover under 5% of the icon.', r['thin_icon'])
    section(out, 'Same icon on two items', 'Usually a duplicate item.', r['dup_icon'])
    section(out, 'No case, pallet or stack', 'Buyable singles with no pack item (paint, piles, logs, tanks and placed parts left out).', r['no_pack'])
    section(out, 'Old pack naming', 'Packs named `_large` / `_small` beside the newer counted packs (`_10` / `_20`).', sorted(r['old_pack']))
    section(out, 'Bad manifest JSON', '', r['bad_json'])
    grown = sum(len(v) for v in r['grown'].values())
    out.append('\n## Not checked\n\n%d grown things (crops, trees, animals) have no model of their own by design, and structures, HUD, liquids, fences, '
               'paths, roads, scoops and ground clutter are built in code or staged.\n' % grown)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out))
    print('wrote', OUT)
    for k, v in r.items():
        print(' ', k, sum(len(x) for x in v.values()) if isinstance(v, dict) else len(v))


if __name__ == '__main__':
    main()
