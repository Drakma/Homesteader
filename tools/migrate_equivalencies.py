#!/usr/bin/env python3
"""
One-time migration: equivalencies become their OWN thing, separate from tags.

    python tools/migrate_equivalencies.py [--dry]

Before: a tag ("#framing_lumber") held its members and, optionally, `tag_values` (what each member is worth, plus a unit word).
After:  tags are plain groups of interchangeable items; an EQUIVALENCY (assets/_schemas/equivalencies.json, referenced in a recipe as "~name") is a unit system:

    "framing_lumber": {"unit": "studs", "label": "2x4 Framing Lumber",
                        "members": [{"item": "lumber_stud_2x4", "value": 1}, {"item": "lumber_bundle_2x4_small", "value": 20}, {"tag": "some_tag", "value": 1}]}

A member is an item OR a tag (every item of the tag counts at that value: choices of colour or material), worth `value` units. A recipe line "~framing_lumber x 20" is
paid by any mix of members worth 20 units.

This script turns every tag that has tag_values into an equivalency of the same name, rewrites the recipes that named "#tag" for those tags to "~tag", removes
tag_values from material_tags.json and removes the tags that only existed to carry values (nothing else uses them).
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asset_references as ar  # noqa: E402  (writes a file back the way it was)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'assets')
TAGS = os.path.join(ASSETS, '_schemas', 'material_tags.json')
EQUIV = os.path.join(ASSETS, '_schemas', 'equivalencies.json')
README = ("An equivalency is a unit system a recipe can ask for as '~name x N' (a recipe line is paid by ANY mix of members worth N units). Each member is an item "
          "(item) or a tag (tag: every item of the tag counts, so the player chooses a colour or a material) and says how many units it is worth (value). The smallest "
          "member is 1. `unit` is the word shown after a count (studs, bags ...). Tags themselves are plain groups of interchangeable items (material_tags.json).")


def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def dump(p, d):
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write('\n')
    os.replace(tmp, p)


def replace_specs(o, old, new):
    """'#old' -> '~new' for every string in the JSON value; returns the number of changes."""
    n = 0
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, str):
                if v == old:
                    o[k] = new
                    n += 1
            else:
                n += replace_specs(v, old, new)
    elif isinstance(o, list):
        for i, x in enumerate(o):
            if isinstance(x, str):
                if x == old:
                    o[i] = new
                    n += 1
            else:
                n += replace_specs(x, old, new)
    return n


def label_of(name):
    return name.replace('_', ' ').title()


def main():
    dry = '--dry' in sys.argv
    data = load(TAGS)
    tag_values = data.get('tag_values') or {}
    eq = load(EQUIV) if os.path.exists(EQUIV) else {'_readme': README, 'equivalencies': {}}
    eq['_readme'] = README
    eqs = eq.setdefault('equivalencies', {})
    converted = []
    for name, tv in tag_values.items():
        members = data['tags'].get(name, [])
        vals = (tv or {}).get('values') or {}
        rows = [{'item': m, 'value': vals.get(m, 1)} for m in members]
        rows.sort(key=lambda r: (r['value'], r['item']))
        eqs[name] = {'unit': (tv or {}).get('unit', ''), 'label': label_of(name), 'members': rows}
        converted.append(name)
    # recipes that named '#tag' for a converted tag now name '~tag'
    changed = {}
    for path in glob.glob(os.path.join(ASSETS, '**', '*.json'), recursive=True):
        rel = os.path.relpath(path, ASSETS).replace('\\', '/')
        if rel.split('/')[0] in ('_scratch', '_originals', '_trash', '_asset_requests') or rel in ('_schemas/material_tags.json', '_schemas/equivalencies.json'):
            continue
        try:
            text = open(path, encoding='utf-8').read()
        except Exception:
            continue
        if not any('"#%s"' % n in text for n in converted):
            continue
        d = json.loads(text)
        n = sum(replace_specs(d, '#' + name, '~' + name) for name in converted)
        if n:
            changed[rel] = n
            if not dry:
                dump(path, d) if not text.endswith('\n') is False else dump(path, d)
    # tags that only carried values: remove when nothing names them any more
    still_used = set()
    for path in glob.glob(os.path.join(ASSETS, '**', '*.json'), recursive=True):
        rel = os.path.relpath(path, ASSETS).replace('\\', '/')
        if rel.split('/')[0] in ('_scratch', '_originals', '_trash', '_asset_requests') or rel.startswith('_schemas/'):
            continue
        try:
            text = open(path, encoding='utf-8').read()
        except Exception:
            continue
        for n in converted:
            if '"#%s"' % n in text:
                still_used.add(n)
    removed = []
    for name in converted:
        if name not in still_used:
            data['tags'].pop(name, None)
            removed.append(name)
    data.pop('tag_values', None)
    data.pop('_readme_values', None)
    print('equivalencies made:', len(converted), converted)
    print('recipes rewritten (#tag -> ~tag):', changed)
    print('tags removed (only existed for the values):', removed)
    print('tags kept (still named elsewhere):', sorted(still_used))
    if not dry:
        dump(EQUIV, eq)
        dump(TAGS, data)


if __name__ == '__main__':
    main()
