#!/usr/bin/env python3
"""
Audits every structure stage recipe against the mixing rules (CLAUDE.md, docs/CONSTRUCTION.md):

  * a recipe that calls for mortar, grout or concrete (bagged mix) or for cement needs WATER (a ~water line, normally inside an "if uses" section) and
    a mixing tool: a wheelbarrow or a cement mixer in one of its tool groups;
  * a recipe that offers cement (the "mix your own" choice) also needs sand and aggregate (~sand and ~gravel lines) with the water.
  * proportions used by the well (tools/set_well_recipes.py): concrete 1 cement : 2 sand : 3 aggregate by volume, water/cement 0.5 by weight;
    mortar 1 cement : 3 sand; bagged mixes 3.5 L of water per bag.

    python tools/check_recipes.py            (exit code 1 when something breaks the rules)
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import recipe_format  # noqa: E402

WET_PREFIXES = ('building_mortar_mix', 'building_concrete_mix', 'building_grout', '20lb_cement_bag')
WET_SPECS = ('~mortar', '~concrete_mix', '~cement', '~grout')
MIXERS = ('tool_wheelbarrow', 'tool_plastic_wheelbarrow', 'tool_steel_wheelbarrow', 'tool_cement_mixer', '#tool_wheelbarrow')


def is_wet(spec):
    s = spec.lower()
    return s in WET_SPECS or s.startswith(WET_PREFIXES)


def is_cement(spec):
    s = spec.lower()
    return s == '~cement' or s.startswith('20lb_cement_bag')


def is_water(spec):
    s = spec.lower()
    return s in ('~water', 'liquid_water') or s.startswith('water_jug') or s.startswith('water_bucket')


def problems(name, recipe, tools):
    specs = [n['item_id'] for n in recipe_format.lines(recipe)]
    out = []
    if any(is_wet(s) for s in specs):
        if not any(is_water(s) for s in specs):
            out.append('%s: uses mortar / grout / concrete / cement but has no water line (~water)' % name)
        if not any(t in MIXERS for grp in (tools or []) for t in (grp if isinstance(grp, list) else [grp])):
            out.append('%s: uses mortar / grout / concrete / cement but no tool group has a wheelbarrow or a cement mixer' % name)
    if any(is_cement(s) for s in specs):
        for need, label in (('~sand', 'sand'), ('~gravel', 'aggregate')):
            if need not in [s.lower() for s in specs]:
                out.append('%s: offers cement but has no %s line (%s)' % (name, label, need))
    return out


def main():
    bad = []
    for p in sorted(glob.glob(os.path.join(ROOT, 'assets', 'structures', '*', '*.json'))):
        g = json.load(open(p, encoding='utf-8'))
        for st in ((g.get('growth') or {}).get('stages') or []):
            bad += problems('%s / %s' % (g.get('id'), st.get('name')), st.get('construction_recipe') or [], st.get('required_tools') or [])
    print('%d recipe problem(s)' % len(bad))
    for b in bad:
        print('  ' + b)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
