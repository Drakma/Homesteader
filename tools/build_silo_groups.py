#!/usr/bin/env python3
"""
Creates the three grain silo structure groups (small, medium, large): group manifest with the four construction stages (recipe and tools), the stage
manifests, the models (tools/make_silo_stages.py in headless Blender), the icons (rendered from the models) and the kit_config entries.

    python tools/build_silo_groups.py

Run tools/generate_unity_asset_catalog.py and tools/package_catalog_as_mods.py afterwards.
"""
import copy
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRUCT = os.path.join(ROOT, 'assets', 'structures')
sys.path.insert(0, os.path.join(ROOT, 'tools'))

# id -> name, tower radius, body height, price, recipe multiplier
SILOS = {
    'grain_silo_small': dict(name='Grain Silo (Small)', R=1.1, H=6.0, price=6000, k=1.0, cap=3000),
    'grain_silo_medium': dict(name='Grain Silo (Medium)', R=2.0, H=10.0, price=16000, k=2.2, cap=12000),
    'grain_silo_large': dict(name='Grain Silo (Large)', R=3.0, H=15.0, price=36000, k=4.0, cap=36000),
}
SLAB_H = 0.3
STAGE_NAMES = ['foundation', 'framing', 'walls', 'complete']
AGES = [(0, 25), (25, 50), (50, 75), (75, 100)]

SHOVELS = ['tool_shovel', 'tool_shovel_round_point', 'tool_shovel_trenching', 'tool_pickaxe']
WRENCH = ['tool_wrench_adjustable', 'tool_wrench_pipe']
DRILLS = ['tool_drill_corded', 'tool_drill_cordless_basic', 'tool_drill_cordless_pro', 'tool_impact_driver_cordless']


def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def dump(p, d):
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write('\n')
    os.replace(tmp, p)


def recipes(k):
    q = lambda n: max(1, round(n * k))
    return {
        'foundation': ([{'item_id': '80lb_cement_bag', 'quantity': q(6)}, {'item_id': '#rebar', 'quantity': q(4)}], [SHOVELS, ['tool_trowel_hand']]),
        'framing': ([{'item_id': '#steel_framing', 'quantity': q(8)}], [WRENCH, DRILLS]),
        'walls': ([{'item_id': '#metal_siding', 'quantity': q(20)}], [WRENCH, DRILLS]),
        'complete': ([{'item_id': '#roofing', 'quantity': q(6)}, {'item_id': '#metal_siding', 'quantity': q(4)}], [WRENCH, DRILLS]),
    }


def heights(cfg):
    body = cfg['H'] + SLAB_H + 0.1
    rise = cfg['R'] * 0.55
    return {'foundation': SLAB_H + 0.1, 'framing': body, 'walls': body, 'complete': body + rise + 0.45}


def build(sid, cfg, cabin_group, cabin_stage):
    footprint = int(-(-2 * (cfg['R'] + 0.4) // 1))
    gdir = os.path.join(STRUCT, sid)
    hs = heights(cfg)
    rec = recipes(cfg['k'])
    group = copy.deepcopy(cabin_group)
    group['id'] = sid
    group['name'] = cfg['name']
    group['icon'] = sid + '.png'
    group['description'] = ('A %s: a round concrete slab, a steel frame, a corrugated steel tower and a conical roof with a ladder and a discharge chute, '
                            'built in 4 stages (foundation -> framing -> walls -> complete).' % cfg['name'].lower())
    group['properties']['base_value'] = cfg['price']
    # the storage built into the finished structure (container component schema; the game reads it from the blueprint item, see ConstructionSite.IsStorage)
    group['container'] = {'capacity_kg': cfg['cap'], 'stacking_limit': 1, 'accepts': ['#grain'], 'show_fill': False, 'single_type': False, 'disposable': False}
    g = group['growth']
    g['species'] = sid
    g['stages'] = []
    for i, name in enumerate(STAGE_NAMES):
        folder = 'struct_' + name
        item_id = '%s_%s' % (folder, sid)
        sdir = os.path.join(gdir, 'stages', folder)
        os.makedirs(sdir, exist_ok=True)
        m = copy.deepcopy(cabin_stage)
        m['id'] = item_id
        m['name'] = '%s - %s' % (cfg['name'], name.capitalize())
        m['description'] = 'The %s construction phase of the %s.' % (name, cfg['name'].lower())
        m['icon'] = item_id + '.png'
        m['models'] = []
        m['properties']['weight_kg'] = round(1500 * cfg['k'] * (i + 1), 1)
        m['properties']['base_value'] = round(cfg['price'] * 0.2 * (i + 1), 1)
        cf = m['category_fields']
        cf['dimensions_m'] = {'width': footprint, 'depth': footprint, 'height': round(hs[name], 2)}
        cf['interior_area_m2'] = 0
        cf['room_count'] = 0
        cf['construction_recipe'], cf['required_tools'] = rec[name]
        dump(os.path.join(sdir, item_id + '.json'), m)
        open(os.path.join(sdir, 'README.md'), 'w', encoding='utf-8', newline='\n').write('# %s\n\nProcedural model (tools/make_silo_stages.py).\n' % m['name'])
        g['stages'].append({'stage': i + 1, 'name': name, 'age_min': AGES[i][0], 'age_max': AGES[i][1], 'resource': 'stages/%s/' % folder, 'model': '',
                            'icon': item_id + '.png', 'construction_recipe': rec[name][0], 'required_tools': rec[name][1]})
    g['total_stages'] = 4
    g['icon_stage'] = 4
    g['max_age'] = 100
    dump(os.path.join(gdir, sid + '.json'), group)


def main():
    cabin_group = load(os.path.join(STRUCT, 'small_cabin', 'small_cabin.json'))
    cabin_stage = load(os.path.join(STRUCT, 'small_cabin', 'stages', 'struct_walls', 'struct_walls_small_cabin.json'))
    for sid, cfg in SILOS.items():
        build(sid, cfg, cabin_group, cabin_stage)
    subprocess.run(['blender', '-b', '-P', os.path.join(ROOT, 'tools', 'make_silo_stages.py'), '--'] + list(SILOS), check=True, capture_output=True)
    for sid in SILOS:
        for name in STAGE_NAMES:
            d = os.path.join(STRUCT, sid, 'stages', 'struct_' + name)
            item_id = 'struct_%s_%s' % (name, sid)
            subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'render_icon_from_model.py'), os.path.join(d, item_id + '.glb'), os.path.join(d, item_id + '.png')],
                           check=True, capture_output=True)
        icon = os.path.join(STRUCT, sid, 'stages', 'struct_complete', 'struct_complete_%s.png' % sid)
        with open(icon, 'rb') as a, open(os.path.join(STRUCT, sid, sid + '.png'), 'wb') as b:
            b.write(a.read())
        print('built', sid)
    # kit_config: the subfolder and the growth group of each silo
    p = os.path.join(ROOT, 'assets', 'kit_config.json')
    cfgk = load(p)
    for sid, cfg in SILOS.items():
        cfgk['subfolders'][sid] = {'name': cfg['name'], 'icon': '', 'category': 'structures'}
        cfgk['growth_groups'][sid] = {
            'name': cfg['name'], 'icon': '', 'category': 'structures', 'growth_type': 'percent', 'max_age': 100, 'time_unit': 'percent',
            'stages': [{'stage': i + 1, 'name': n, 'item_id': 'struct_%s_%s' % (n, sid), 'age_min': AGES[i][0], 'age_max': AGES[i][1]} for i, n in enumerate(STAGE_NAMES)],
        }
    dump(p, cfgk)


if __name__ == '__main__':
    main()
