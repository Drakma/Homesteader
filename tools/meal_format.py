"""
The MEAL format, in one place (kit server, generators, checks). Meals are mod data (content type "meal"): assets/_meals/*.json, packaged to meals/*.json.
Reference: docs/COOKING.md. The Meals List (right click on any kitchen object) shows every meal the kitchen can make right now.

A file is {"meals": [ meal, ... ]}; a meal is

    id           unique, snake_case ("meal_bread")
    name         shown in the list (defaults to the result item's name)
    group        a heading in the list ("Baking", "Cooking")
    result       {"item_id": "<item id>", "quantity": N}   what one cooking makes. Or FILLS a container: {"container": "<empty liquid container item>", "liquid": "<liquid item>"}: it needs an empty one
                 in the kitchen (not used up: it comes back full, what is in it kept) and fills it to its capacity (or "liters": L)
    ingredients  the recipe tree (tools/recipe_format.py): lines {item_id (item | #tag | ~equivalency), quantity} and sections {section, mode, if, items}.
                 Ingredients are taken from the kitchen's containers and shelves. They are consumed.
    liquids      (a blend) [{"liquid": "<liquid item>", "share": 0.5}, ...]: what the result container is filled with, each liquid's share (they add up to 1) poured out of the filled containers
                 in the kitchen (they keep what is left). Needs a result container; the meal may have no ingredients.
    appliances   a list of groups {"tools": ["#appliance_oven", "<item id>", ...]}: the kitchen needs ANY ONE of each group (placed in the kitchen, in the same
                 room or within reach). Appliances are not consumed.

Ingredients are whole items (a bag of flour, a jar of yeast): a meal that uses a whole bag makes a batch.
"""
import json
import os
import re

import recipe_format

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'assets')
MEALS_DIR = os.path.join(ASSETS, '_meals')
ID_RE = re.compile(r'^[a-z][a-z0-9_]*$')


def item_ids():
    ids = set()
    for path in __import__('glob').glob(os.path.join(ASSETS, '*', '*', '*.json')):
        folder = os.path.basename(os.path.dirname(path))
        if os.path.basename(path) == folder + '.json':
            ids.add(folder)
    return ids


def tags():
    with open(os.path.join(ASSETS, '_schemas', 'material_tags.json'), encoding='utf-8') as f:
        return set(json.load(f).get('tags', {}))


def _lines(nodes, out):
    for n in nodes:
        if recipe_format.is_section(n):
            _lines(n['items'], out)
        else:
            out.append(n)


def _manifest(item_id):
    import glob
    for path in glob.glob(os.path.join(ASSETS, '*', item_id, item_id + '.json')):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return None


def _check_fill(mid, res, ids, tag_names):
    """A meal that fills a container: the container must be a liquid container and take the liquid."""
    errs = []
    c, liquid = res.get('container'), res.get('liquid')
    cm = _manifest(c) if c in ids else None
    if cm is None or 'liquid_container' not in cm:
        return ['%s: result container %r is not a liquid container' % (mid, c)]
    if liquid not in ids:
        return ['%s: result liquid %r does not exist' % (mid, liquid)]
    tags_all = json.load(open(os.path.join(ASSETS, '_schemas', 'material_tags.json'), encoding='utf-8')).get('tags', {})
    accepts = cm['liquid_container'].get('accepts') or []
    if accepts and not any((a == liquid) or (a.startswith('#') and liquid in tags_all.get(a[1:], [])) for a in accepts):
        errs.append('%s: %s does not take %s (accepts %s)' % (mid, c, liquid, accepts))
    return errs


def validate_meal(m, ids, tag_names):
    """A list of problems with one meal (empty = fine)."""
    errs = []
    mid = m.get('id', '')
    if not ID_RE.match(str(mid)):
        errs.append('id %r must be snake_case' % mid)
    res = m.get('result') or {}
    if res.get('container'):
        errs += _check_fill(mid, res, ids, tag_names)
    elif res.get('item_id') not in ids:
        errs.append('%s: result item %r does not exist' % (mid, res.get('item_id')))
    if not res.get('container') and (not isinstance(res.get('quantity'), int) or res.get('quantity', 0) < 1):
        errs.append('%s: result quantity must be a whole number of at least 1' % mid)
    nodes, err = recipe_format.normalize(m.get('ingredients'))
    if err:
        errs.append('%s: %s' % (mid, err))
        nodes = []
    liquids = m.get('liquids') or []
    if not nodes and not liquids:
        errs.append('%s: a meal needs at least one ingredient' % mid)
    if liquids:
        if not res.get('container'):
            errs.append('%s: liquids are poured into a result container' % mid)
        total = 0.0
        for l in liquids:
            if (l or {}).get('liquid') not in ids:
                errs.append('%s: blend liquid %r does not exist' % (mid, (l or {}).get('liquid')))
            total += float((l or {}).get('share', 0) or 0)
        if abs(total - 1.0) > 0.011:
            errs.append('%s: the blend shares add up to %.2f, not 1' % (mid, total))
    lines = []
    _lines(nodes, lines)
    for ln in lines:
        spec = str(ln.get('item_id', ''))
        if spec.startswith('#'):
            if spec[1:] not in tag_names:
                errs.append('%s: ingredient tag %s does not exist' % (mid, spec))
        elif spec.startswith('~'):
            pass                                     # equivalencies are checked by tools/check_recipes.py
        elif spec not in ids:
            errs.append('%s: ingredient %r does not exist' % (mid, spec))
    groups = m.get('appliances') or []
    if not isinstance(groups, list):
        errs.append('%s: appliances must be a list of groups' % mid)
        groups = []
    for g in groups:
        tools = (g or {}).get('tools')
        if not isinstance(tools, list) or not tools:
            errs.append('%s: every appliance group needs a tools list' % mid)
            continue
        for t in tools:
            if str(t).startswith('#'):
                if str(t)[1:] not in tag_names:
                    errs.append('%s: appliance tag %s does not exist' % (mid, t))
            elif t not in ids:
                errs.append('%s: appliance %r does not exist' % (mid, t))
    return errs


def load_all():
    """Every meal file in assets/_meals: [(path, meal), ...]."""
    out = []
    if os.path.isdir(MEALS_DIR):
        for name in sorted(os.listdir(MEALS_DIR)):
            if name.endswith('.json'):
                path = os.path.join(MEALS_DIR, name)
                with open(path, encoding='utf-8') as f:
                    for m in json.load(f).get('meals', []):
                        out.append((path, m))
    return out


def check_all():
    ids, tag_names = item_ids(), tags()
    seen, problems = set(), []
    for path, m in load_all():
        if m.get('id') in seen:
            problems.append('duplicate meal id %s' % m.get('id'))
        seen.add(m.get('id'))
        problems += validate_meal(m, ids, tag_names)
    return len(seen), problems


# ------------------------------------------------------------------ the kit server (tools/server.py): list, read, validate and save the meal files

FILE_RE = re.compile(r'^[a-z][a-z0-9_]*\.json$')


def validate_data(data, others=None):
    """Problems of a whole meal file's data ({"meals": [...]}). `others`: meal ids that already exist in OTHER files (a duplicate id is a problem)."""
    if not isinstance(data, dict) or not isinstance(data.get('meals'), list):
        return ['the file must be {"meals": [ ... ]}']
    ids, tag_names = item_ids(), tags()
    seen, problems = set(others or ()), []
    for m in data['meals']:
        if not isinstance(m, dict):
            problems.append('a meal must be an object')
            continue
        if m.get('id') in seen:
            problems.append('duplicate meal id %s' % m.get('id'))
        seen.add(m.get('id'))
        problems += validate_meal(m, ids, tag_names)
    return problems


def _ids_elsewhere(name):
    out = set()
    for path, m in load_all():
        if os.path.basename(path) != name:
            out.add(m.get('id'))
    return out


def list_files():
    """[{file, meals, problems}] for every file in assets/_meals."""
    out = []
    if os.path.isdir(MEALS_DIR):
        for name in sorted(os.listdir(MEALS_DIR)):
            if name.endswith('.json'):
                with open(os.path.join(MEALS_DIR, name), encoding='utf-8') as f:
                    data = json.load(f)
                out.append({'file': name, 'meals': len(data.get('meals', [])), 'problems': len(validate_data(data, _ids_elsewhere(name)))})
    return out


def get_file(name):
    """(data, problems) of one meal file, or (None, []) when there is none."""
    if not FILE_RE.match(name or ''):
        return None, []
    path = os.path.join(MEALS_DIR, name)
    if not os.path.isfile(path):
        return None, []
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return data, validate_data(data, _ids_elsewhere(name))


def save_file(name, data):
    """Validates and writes assets/_meals/<name>. Returns (ok, problems): any problem rejects the save."""
    if not FILE_RE.match(name or ''):
        return False, ['the file name must be snake_case and end in .json']
    problems = validate_data(data, _ids_elsewhere(name))
    if problems:
        return False, problems
    os.makedirs(MEALS_DIR, exist_ok=True)
    with open(os.path.join(MEALS_DIR, name), 'w', encoding='utf-8', newline=chr(10)) as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write(chr(10))
    return True, []


if __name__ == '__main__':
    n, problems = check_all()
    for p in problems:
        print('PROBLEM', p)
    print('%d meal(s), %d problem(s)' % (n, len(problems)))
