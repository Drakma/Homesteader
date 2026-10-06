#!/usr/bin/env python3
"""
Turns the manual well into a buildable structure group (assets/structures/water_well_manual): group manifest with the four construction stages
(recipe and tools), the stage manifests, the models (tools/make_well_stages.py in headless Blender), the icons (rendered from the models) and the
kit_config entries. The old plain item assets/water/water_well_manual (no model) is kept in assets/_originals/.

    python tools/build_well_group.py

Run tools/refresh_game_content.py afterwards.
"""
import copy
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRUCT = os.path.join(ROOT, 'assets', 'structures')
sys.path.insert(0, os.path.join(ROOT, 'tools'))

SID = 'water_well_manual'
NAME = 'Manual Well'
STAGE_NAMES = ['foundation', 'framing', 'walls', 'complete']
AGES = [(0, 25), (25, 50), (50, 75), (75, 100)]
HEIGHTS = {'foundation': 0.2, 'framing': 0.8, 'walls': 2.1, 'complete': 2.6}
FOOTPRINT = 2

SHOVELS = ['tool_shovel', 'tool_shovel_round_point', 'tool_shovel_trenching', 'tool_pickaxe']
TROWEL = ['tool_trowel_hand']
HAMMERS = ['tool_hammer', 'tool_hammer_claw', 'tool_hammer_club']
SAWS = ['tool_saw_hand', 'tool_circular_saw_corded', 'tool_circular_saw_cordless', 'tool_miter_saw']

# placeholder recipes: tools/set_well_recipes.py (run at the end) replaces them with the real ones
RECIPES = {
    'foundation': ([{'item_id': '~gravel', 'quantity': 0.15}, {'item_id': '~concrete_mix', 'quantity': 4}], [SHOVELS, TROWEL]),
    'framing': ([{'section': 'Stone lining', 'mode': 'any', 'items': [{'item_id': 'masonry_fieldstone', 'quantity': 12}, {'item_id': '~masonry_units', 'quantity': 30}]},
                 {'item_id': '~mortar', 'quantity': 4}], [SHOVELS, TROWEL]),
    'walls': ([{'item_id': '~masonry_units', 'quantity': 12}, {'item_id': '~mortar', 'quantity': 2}, {'item_id': '~framing_lumber', 'quantity': 10}], [TROWEL, SAWS, HAMMERS]),
    'complete': ([{'item_id': '~framing_lumber', 'quantity': 8}, {'item_id': '#roofing', 'quantity': 4}, {'item_id': 'mat_rope', 'quantity': 1},
                  {'item_id': 'tool_bucket_empty', 'quantity': 1}], [SAWS, HAMMERS]),
}


def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def dump(p, d):
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write('\n')
    os.replace(tmp, p)


def main():
    old_dir = os.path.join(ROOT, 'assets', 'water', SID)
    keep = os.path.join(ROOT, 'assets', '_originals', 'water_well_manual_item')
    if os.path.isdir(old_dir) and not os.path.isdir(keep):
        shutil.copytree(old_dir, keep)
    old = load(os.path.join(old_dir, SID + '.json')) if os.path.isfile(os.path.join(old_dir, SID + '.json')) else {}
    cabin_group = load(os.path.join(STRUCT, 'small_cabin', 'small_cabin.json'))
    cabin_stage = load(os.path.join(STRUCT, 'small_cabin', 'stages', 'struct_walls', 'struct_walls_small_cabin.json'))
    gdir = os.path.join(STRUCT, SID)
    group = copy.deepcopy(cabin_group)
    group['id'] = SID
    group['name'] = NAME
    group['icon'] = SID + '.png'
    group['description'] = ('A traditional stone-walled well with a bucket on a rope, drawn up by hand with a windlass - no power or pump required. '
                            'Built in 4 stages (foundation -> framing -> walls -> complete).')
    group['properties']['base_value'] = old.get('properties', {}).get('base_value', 1200)
    g = group['growth']
    g['species'] = SID
    g['stages'] = []
    for i, name in enumerate(STAGE_NAMES):
        folder = 'struct_' + name
        item_id = '%s_%s' % (folder, SID)
        sdir = os.path.join(gdir, 'stages', folder)
        os.makedirs(sdir, exist_ok=True)
        m = copy.deepcopy(cabin_stage)
        m['id'] = item_id
        m['name'] = '%s - %s' % (NAME, name.capitalize())
        m['description'] = 'The %s construction phase of the %s.' % (name, NAME.lower())
        m['icon'] = item_id + '.png'
        m['models'] = []
        m['properties']['weight_kg'] = 400.0 * (i + 1)
        m['properties']['base_value'] = round(group['properties']['base_value'] * 0.2 * (i + 1), 1)
        cf = m['category_fields']
        cf['dimensions_m'] = {'width': FOOTPRINT, 'depth': FOOTPRINT, 'height': HEIGHTS[name]}
        cf['interior_area_m2'] = 0
        cf['room_count'] = 0
        cf['construction_recipe'], cf['required_tools'] = copy.deepcopy(RECIPES[name][0]), copy.deepcopy(RECIPES[name][1])
        dump(os.path.join(sdir, item_id + '.json'), m)
        open(os.path.join(sdir, 'README.md'), 'w', encoding='utf-8', newline='\n').write('# %s\n\nProcedural model (tools/make_well_stages.py).\n' % m['name'])
        g['stages'].append({'stage': i + 1, 'name': name, 'age_min': AGES[i][0], 'age_max': AGES[i][1], 'resource': 'stages/%s/' % folder, 'model': '',
                            'icon': item_id + '.png', 'construction_recipe': copy.deepcopy(RECIPES[name][0]), 'required_tools': copy.deepcopy(RECIPES[name][1])})
    g['total_stages'] = 4
    g['icon_stage'] = 4
    g['max_age'] = 100
    dump(os.path.join(gdir, SID + '.json'), group)

    subprocess.run(['blender', '-b', '-P', os.path.join(ROOT, 'tools', 'make_well_stages.py'), '--', SID], check=True, capture_output=True)
    for name in STAGE_NAMES:
        d = os.path.join(gdir, 'stages', 'struct_' + name)
        item_id = 'struct_%s_%s' % (name, SID)
        subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'render_icon_from_model.py'), os.path.join(d, item_id + '.glb'), os.path.join(d, item_id + '.png')],
                       check=True, capture_output=True)
    shutil.copyfile(os.path.join(gdir, 'stages', 'struct_complete', 'struct_complete_%s.png' % SID), os.path.join(gdir, SID + '.png'))

    p = os.path.join(ROOT, 'assets', 'kit_config.json')
    cfgk = load(p)
    cfgk['subfolders'][SID] = {'name': NAME, 'icon': '', 'category': 'structures'}
    cfgk['growth_groups'][SID] = {
        'name': NAME, 'icon': '', 'category': 'structures', 'growth_type': 'percent', 'max_age': 100, 'time_unit': 'percent',
        'stages': [{'stage': i + 1, 'name': n, 'item_id': 'struct_%s_%s' % (n, SID), 'age_min': AGES[i][0], 'age_max': AGES[i][1]} for i, n in enumerate(STAGE_NAMES)],
    }
    dump(p, cfgk)
    if os.path.isdir(old_dir):
        shutil.rmtree(old_dir)          # the plain item is replaced by the structure of the same id
    subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'set_well_recipes.py')], check=True)   # the real recipes (wet mixes need water and a mixing tool)
    print('built', SID)


if __name__ == '__main__':
    main()
