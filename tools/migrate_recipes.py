"""Converts every construction recipe (group manifests' growth.stages[].construction_recipe and stage manifests' category_fields.construction_recipe)
to the section format (tools/recipe_format.py): legacy any_of lines become "any" sections. Safe to re-run."""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recipe_format, asset_references as ar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
changed = 0
for p in glob.glob(os.path.join(ROOT, 'assets', '*', '**', '*.json'), recursive=True):
    if os.sep + '_' in p[len(ROOT):] and '_schemas' in p or '_scratch' in p or '_trash' in p or '_originals' in p:
        continue
    try:
        text = open(p, encoding='utf-8').read()
        if 'construction_recipe' not in text:
            continue
        m = json.loads(text)
    except Exception:
        continue
    if not isinstance(m, dict):
        continue
    dirty = False
    holders = []
    cf = m.get('category_fields')
    if isinstance(cf, dict) and 'construction_recipe' in cf:
        holders.append(cf)
    g = m.get('growth')
    for st in (g.get('stages') if isinstance(g, dict) else None) or []:
        if isinstance(st, dict) and 'construction_recipe' in st:
            holders.append(st)
    for h in holders:
        new, err = recipe_format.normalize(h['construction_recipe'])
        if err:
            print('ERROR', p, err)
            continue
        if new != h['construction_recipe']:
            h['construction_recipe'] = new
            dirty = True
    if dirty:
        ar._dump_like(p, text, m)
        changed += 1
print('migrated', changed)
