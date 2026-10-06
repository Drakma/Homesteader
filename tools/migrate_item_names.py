#!/usr/bin/env python3
"""
Item names are plain; what the game SHOWS is generated from stored data (HudBindings.GetDisplayName):
  * properties.pack_quantity (a stack, pallet, case or bundle of N)  ->  "Name (N)"
  * properties.display_weight (materials and packaged goods)         ->  "Name (9 kg)" / "Name (20 lb)", through UnitFormat so the Metric / Imperial setting converts it.
A pack shows its quantity only; a single shows its weight only.

This moves the numbers out of the stored names: "Cement Bag (Pallet of 10)" -> name "Cement Bag Pallet", pack_quantity 10; "Large 2x6 Bundle (25)" -> "Large 2x6 Bundle", 25.
It also sets display_weight on materials and packaged goods. Safe to re-run.

    python tools/migrate_item_names.py [--dry-run]
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import asset_references as ar  # noqa: E402

PACK_OF = re.compile(r'^(.*?)\s*\((Pallet|Stack) of (\d+)\)$')
PACK_PLAIN = re.compile(r'^(.*?)\s*\((\d+)(?: boxes)?\)$')
WEIGHT_CATEGORIES = ('materials', 'building')
PACKAGED = re.compile(r'(bag|pallet|stack|bundle|case|pack|bucket|jug|spool|coil|roll|sack|box|barrel)', re.I)


def new_name(name):
    """(plain name, pack quantity or None)"""
    m = PACK_OF.match(name)
    if m:
        return '%s %s' % (m.group(1), m.group(2)), int(m.group(3))
    m = PACK_PLAIN.match(name)
    if m:
        return m.group(1), int(m.group(2))
    return name, None


def main():
    dry = '--dry-run' in sys.argv
    changed = 0
    names = {}
    for p in sorted(glob.glob(os.path.join(ROOT, 'assets', '*', '*', '*.json'))):
        rel = p.replace(os.sep, '/').split('/')
        item = rel[-1][:-5]
        if rel[-2] != item or rel[-3].startswith('_') or rel[-3] == 'structures':
            continue
        try:
            text = open(p, encoding='utf-8').read()
            m = json.loads(text)
        except Exception:
            continue
        if not isinstance(m, dict) or not isinstance(m.get('properties'), dict):
            continue
        props = m['properties']
        old = m.get('name', '')
        dirty = False
        plain, qty = new_name(old) if isinstance(old, str) else (old, None)
        if qty is not None and (plain != old or props.get('pack_quantity') != qty):
            m['name'] = plain
            props['pack_quantity'] = qty
            dirty = True
            rd = os.path.join(os.path.dirname(p), 'README.md')
            if os.path.exists(rd):
                r = open(rd, encoding='utf-8').read()
                if old in r:
                    open(rd, 'w', encoding='utf-8', newline='').write(r.replace(old, plain))
        elif 'pack_quantity' in props and qty is None and not isinstance(props.get('pack_quantity'), int):
            pass
        cat = rel[-3]
        wants = (cat in WEIGHT_CATEGORIES or bool(PACKAGED.search(item))) and float(props.get('weight_kg') or 0) > 0 and not props.get('is_blueprint') and cat not in ('structures', 'hud')
        if wants and props.get('display_weight') is not True:
            props['display_weight'] = True
            dirty = True
        names.setdefault(m.get('name', ''), []).append(item)
        if dirty:
            changed += 1
            if not dry:
                ar._dump_like(p, text, m)
    print('changed', changed, 'manifest(s)' + (' (dry run)' if dry else ''))


if __name__ == '__main__':
    main()
