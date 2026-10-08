#!/usr/bin/env python3
"""
When an asset is renamed (or moved to another category, which renames it), EVERYTHING that refers to its id has to follow: material tags (members and the
tag_values equivalencies), construction recipes and required tools, growth rules (yield, planting, fruit drops), container "accepts" lists, conversion chains,
path materials, kit_config stages, shop lists - anywhere an id is used.

    python tools/asset_references.py <old_id> <new_id> [--dry]      what the asset kit's rename does automatically
    python tools/asset_references.py --check                        lists references to ids that no longer exist (broken after an old rename)

Rewrites every JSON file under assets/ (except the scratch, original, trash and request folders): any string that IS the old id, in any key or list, and any
dict key that is the old id (tag_values entries). Only descriptive text is left alone (name, description, note, label ...). Files are rewritten only when something
changed, keeping their indentation and non-ASCII escaping. The code that may mention an id (tools/*.py, Unity scripts, the kit page) is reported, not edited.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'assets')
SKIP_DIRS = {'_scratch', '_originals', '_trash', '_pipeline_stats', '_asset_requests', 'node_modules'}
TEXT_KEYS = {'name', 'description', 'note', 'label', 'title', 'summary', 'text', '_readme', '_readme_values', 'message'}   # words, not references
CODE_DIRS = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'Homesteader', 'Assets', 'Scripts'), os.path.join(ROOT, 'assets', 'index.html')]


def _walk(o, old, new, key=None):
    """Replaces in place; returns the number of changes."""
    n = 0
    if isinstance(o, dict):
        for k in list(o.keys()):
            v = o[k]
            if k == old:                                           # a dict KEY that is the id (tag_values[tag].values, per-item maps)
                o[new] = o.pop(k)
                n += 1
                k = new
                v = o[k]
            if isinstance(v, str):
                if v == old and k not in TEXT_KEYS and k != 'id':
                    o[k] = new
                    n += 1
            else:
                n += _walk(v, old, new, k)
    elif isinstance(o, list):
        for i, x in enumerate(o):
            if isinstance(x, str):
                if x == old and key not in TEXT_KEYS:
                    o[i] = new
                    n += 1
            else:
                n += _walk(x, old, new, key)
    return n


def _dump_like(path, text, data):
    m = re.search(r'\n( +)"', text)
    indent = len(m.group(1)) if m else 2
    ascii_only = '\\u' in text
    out = json.dumps(data, indent=indent, ensure_ascii=ascii_only)
    if text.endswith('\n'):
        out += '\n'
    crlf = '\r\n' in text
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\r\n' if crlf else '\n') as f:
        f.write(out)
    os.replace(tmp, path)


def _json_files(assets_dir):
    for root, dirs, files in os.walk(assets_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if fn.endswith('.json'):
                yield os.path.join(root, fn)


def code_mentions(old_id, limit=20):
    """Source files that mention the id as a whole word (they are not edited: a person decides)."""
    pat = re.compile(r'(?<![A-Za-z0-9_])' + re.escape(old_id) + r'(?![A-Za-z0-9_])')
    hits = []
    for base in CODE_DIRS:
        paths = [base] if os.path.isfile(base) else [os.path.join(r, f) for r, d, fs in os.walk(base) for f in fs if f.endswith(('.py', '.cs', '.html', '.js'))]
        for p in paths:
            try:
                with open(p, encoding='utf-8', errors='ignore') as f:
                    if pat.search(f.read()):
                        hits.append(os.path.relpath(p, ROOT).replace('\\', '/'))
            except Exception:
                pass
            if len(hits) >= limit:
                return hits
    return hits


def rewrite_asset_references(old_id, new_id, dry=False, assets_dir=ASSETS):
    """Returns {'files': [relative paths changed], 'replacements': n, 'code': [source files that mention the old id]}."""
    changed, total = [], 0
    if not old_id or not new_id or old_id == new_id:
        return {'files': changed, 'replacements': 0, 'code': []}
    for path in _json_files(assets_dir):
        try:
            with open(path, encoding='utf-8') as f:
                text = f.read()
            if old_id not in text:                      # cheap test before parsing
                continue
            data = json.loads(text)
        except Exception:
            continue
        n = _walk(data, old_id, new_id)
        if n:
            total += n
            changed.append(os.path.relpath(path, assets_dir).replace('\\', '/'))
            if not dry:
                _dump_like(path, text, data)
    return {'files': changed, 'replacements': total, 'code': code_mentions(old_id)}


# ------------------------------------------------------------------ integrity check

def known_ids(assets_dir=ASSETS):
    ids = set()
    for cat in os.listdir(assets_dir):
        cdir = os.path.join(assets_dir, cat)
        if cat.startswith('_') or not os.path.isdir(cdir):
            continue
        for item in os.listdir(cdir):
            if os.path.isfile(os.path.join(cdir, item, item + '.json')):
                ids.add(item)
    stage_ids = set()
    for root, dirs, files in os.walk(assets_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        if os.path.basename(os.path.dirname(root)) == 'stages' or os.path.basename(root) in ('stages',):
            for f in files:
                if f.endswith('.json'):
                    stage_ids.add(f[:-5])
    return ids, stage_ids


ID_KEYS = {'item_id', 'next_item_id', 'path_material_item', 'yields_item_id', 'fence_post_item', 'fence_panel_item', 'seed_item', 'harvest_item', 'tool', 'post_item', 'uses', 'not_uses'}
LIST_KEYS = {'accepts', 'drops', 'tools', 'required_tools', 'any_of', 'members', 'items', 'tool_groups'}


def dangling_references(assets_dir=ASSETS):
    """[(file, key, id)] for references (recipes, tags, accepts, drops ...) to ids that are not an asset and not a tag."""
    ids, stage_ids = known_ids(assets_dir)
    try:
        tagdata = json.load(open(os.path.join(assets_dir, '_schemas', 'material_tags.json'), encoding='utf-8'))
    except Exception:
        tagdata = {'tags': {}, 'tag_values': {}}
    tags = set(tagdata.get('tags', {}))
    try:
        eqdata = json.load(open(os.path.join(assets_dir, '_schemas', 'equivalencies.json'), encoding='utf-8')).get('equivalencies', {})
    except Exception:
        eqdata = {}
    bad = []
    categories = {c for c in os.listdir(assets_dir) if not c.startswith('_') and os.path.isdir(os.path.join(assets_dir, c))}

    def ok(v):
        return (not v) or v in ids or v in stage_ids or (v.startswith('#') and v[1:] in tags) or (v.startswith('~') and v[1:] in eqdata)

    # the members of every equivalency: items that exist, tags that exist
    for ename, e in eqdata.items():
        for m in e.get('members', []):
            if m.get('item') and m['item'] not in ids:
                bad.append(('_schemas/equivalencies.json', 'equivalency ~' + ename, m['item']))
            if m.get('tag') and m['tag'] not in tags:
                bad.append(('_schemas/equivalencies.json', 'equivalency ~' + ename, '#' + m['tag']))

    def walk(o, key, f, inlist=False):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, str):
                    if k in ID_KEYS and not ok(v):
                        bad.append((f, k, v))
                else:
                    walk(v, k, f, k in LIST_KEYS)
        elif isinstance(o, list):
            for x in o:
                if isinstance(x, str):
                    if inlist and not ok(x) and not (key == 'accepts' and x in categories):   # a category name is a valid accepts entry
                        bad.append((f, key, x))
                else:
                    walk(x, key, f, inlist)

    for path in _json_files(assets_dir):
        rel = os.path.relpath(path, assets_dir).replace('\\', '/')
        if rel.startswith(('kit_config', '_schemas/')) and not rel.endswith('material_tags.json'):
            continue
        if rel.endswith('ledger.json') or rel.endswith('AssetCatalog.json'):
            continue
        try:
            data = json.load(open(path, encoding='utf-8'))
        except Exception:
            continue
        if rel.endswith('material_tags.json'):
            for tname, members in data.get('tags', {}).items():
                for m in members:
                    if m not in ids:
                        bad.append((rel, 'tag ' + tname, m))
            for tname, tv in data.get('tag_values', {}).items():
                for m in (tv.get('values') or {}):
                    if m not in ids:
                        bad.append((rel, 'tag_values ' + tname, m))
            continue
        walk(data, '', rel)
    return bad


if __name__ == '__main__':
    if '--check' in sys.argv:
        bad = dangling_references()
        print('%d dangling reference(s)' % len(bad))
        for f, k, v in bad:
            print('  %s  %s -> %s' % (f, k, v))
        sys.exit(1 if bad else 0)
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) != 2:
        sys.exit(__doc__)
    r = rewrite_asset_references(args[0], args[1], dry='--dry' in sys.argv)
    print('%s %d replacements in %d files' % ('would make' if '--dry' in sys.argv else 'made', r['replacements'], len(r['files'])))
    for f in r['files']:
        print('  ', f)
    if r['code']:
        print('also mentioned in code (not edited):', ', '.join(r['code']))
