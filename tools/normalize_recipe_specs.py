#!/usr/bin/env python3
"""
A recipe line that names a plain item ("post_wood_round_6inch") only counts that single item; its stacks, bundles and cases are not recognized at the build site.
When the item is the UNIT (value 1) of an equivalency that also has bigger packs, the line is changed to the equivalency ("~post_wood_round_6inch") so the packs count
too. The quantity stays the same (it is already in singles). Run after adding equivalencies; safe to re-run.

    python tools/normalize_recipe_specs.py [--dry-run]
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import asset_references as ar  # noqa: E402


def main():
    dry = '--dry-run' in sys.argv
    eqs = json.load(open(os.path.join(ROOT, 'assets', '_schemas', 'equivalencies.json'), encoding='utf-8'))['equivalencies']
    unit_of = {}   # plain item id -> equivalency name (the item is the unit and the equivalency has bigger members)
    for name, e in eqs.items():
        members = e.get('members', [])
        if not any(m.get('item') and m['value'] > 1 for m in members):
            continue
        for m in members:
            if m.get('item') and abs(m['value'] - 1) < 1e-9:
                if m['item'] not in unit_of or name == m['item']:
                    unit_of[m['item']] = name

    changed_files = 0
    changes = {}

    def fix(nodes):
        n_changed = 0
        for n in nodes or []:
            if not isinstance(n, dict):
                continue
            if isinstance(n.get('items'), list):
                n_changed += fix(n['items'])
            elif isinstance(n.get('any_of'), list):
                n_changed += fix(n['any_of'])
            else:
                spec = n.get('item_id', '')
                if spec and spec[0] not in '#~' and spec in unit_of:
                    n['item_id'] = '~' + unit_of[spec]
                    changes[spec] = unit_of[spec]
                    n_changed += 1
        return n_changed

    for p in glob.glob(os.path.join(ROOT, 'assets', 'structures', '**', '*.json'), recursive=True):
        text = open(p, encoding='utf-8').read()
        if 'construction_recipe' not in text:
            continue
        try:
            m = json.loads(text)
        except Exception:
            continue
        count = 0
        cf = m.get('category_fields')
        if isinstance(cf, dict):
            count += fix(cf.get('construction_recipe'))
        g = m.get('growth')
        for st in (g.get('stages') if isinstance(g, dict) else None) or []:
            if isinstance(st, dict):
                count += fix(st.get('construction_recipe'))
        if count:
            changed_files += 1
            if not dry:
                ar._dump_like(p, text, m)
    print('changed %d file(s)%s' % (changed_files, ' (dry run)' if dry else ''))
    for spec, eq in sorted(changes.items()):
        print('  %s -> ~%s' % (spec, eq))


if __name__ == '__main__':
    main()
