#!/usr/bin/env python3
"""
Rebuilds the farmhouse's construction recipes (group manifest + every stage manifest) on the recipe tree system (tools/recipe_format.py) so that they
use the building materials and tools of the catalog: concrete or block or brick/stone foundations (concrete mixed from bags or from cement, sand, aggregate
and water), wood or steel framing, trusses or rafters, sheathing, house wrap, windows and doors, rough electrical (Romex) and plumbing (PVC), insulation of
every kind, roofing with felt, flashing and nails, siding, fascia, soffit, gutters, drywall with tape and compound, paint, flooring (tile adds thinset and
grout with water), trim and finishing nails.

The mixing rule (CLAUDE.md): mortar, grout, concrete and cement need water and a wheelbarrow or cement mixer; cement also needs sand and aggregate.
Quantities are game scale (the farmhouse is 10 x 12 m, two storeys); tune them in the kit.

    python tools/set_farmhouse_recipe.py
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import asset_references as ar  # noqa: E402
import recipe_format  # noqa: E402

STRUCT = os.path.join(ROOT, 'assets', 'structures', 'farmhouse')

SHOVELS = ['tool_shovel', 'tool_shovel_round_point', 'tool_shovel_trenching', 'tool_pickaxe']
TROWEL = ['tool_trowel_hand']
MIXER = ['tool_wheelbarrow', 'tool_plastic_wheelbarrow', 'tool_steel_wheelbarrow', 'tool_cement_mixer']
GRINDER = ['tool_angle_grinder_corded', 'tool_angle_grinder_cordless']
SAWS = ['tool_circular_saw_corded', 'tool_circular_saw_cordless', 'tool_saw_hand', 'tool_miter_saw', 'tool_table_saw']
FIX = ['tool_hammer_claw', 'tool_drill_corded', 'tool_drill_cordless_basic', 'tool_drill_cordless_pro', 'tool_impact_driver_cordless']
HAMMERS = ['tool_hammer', 'tool_hammer_claw', 'tool_hammer_club']
WRENCH = ['tool_wrench_adjustable', 'tool_wrench_pipe']


def L(spec, q):
    return {'item_id': spec, 'quantity': q}


def S(title, mode, items, cond=None):
    d = {'section': title, 'mode': mode, 'items': items}
    if cond:
        d['if'] = cond
    return d


def concrete(bags, cement, sand, gravel, water_bag, water_own):
    """Concrete: bagged mix, or your own from cement, sand and aggregate (1 : 2 : 3 by volume), each with its water."""
    return [
        S('Concrete', 'any', [
            S('Bagged concrete mix', 'all', [L('~concrete_mix', bags), L('~water', water_bag)]),
            S('Mix your own: 1 cement, 2 sand, 3 aggregate', 'all', [L('~cement', cement), L('~sand', sand), L('~gravel', gravel), L('~water', water_own)]),
        ]),
    ]


def doors(exterior):
    if exterior:
        return [L('building_door_frame_exterior', 2), L('#door_exterior', 2), L('building_door_hardware_set', 2)]
    return [L('building_door_frame_interior', 6), L('#door_interior', 6), L('building_door_hardware_set', 6)]


RECIPES = {
    'foundation': ([
        L('~gravel', 0.5),
        L('~rebar', 12),
        L('~anchor_bolts', 24),
        L('~drain_french_sock', 4),
        S('Foundation', 'any', [
            S('Poured slab', 'all', concrete(100, 18, 0.22, 0.32, 90, 80)),
            S('Block foundation', 'all', [L('~masonry_units', 120), L('~mortar', 8), L('~water', 28)]),
            S('Brick or fieldstone foundation', 'all', [S('Masonry', 'any', [L('~bricks', 400), L('~masonry_fieldstone', 40)]), L('~mortar', 8), L('~water', 28)]),
            S('On stilts', 'all', [L('~post_wood_round_6inch', 12)] + concrete(12, 2, 0.03, 0.04, 11, 10)),
        ]),
    ], [SHOVELS, TROWEL, MIXER, GRINDER]),

    'framing': ([
        S('Frame', 'any', [
            S('Wood frame', 'all', [L('~framing_lumber', 200), L('~lumber_2x6', 60), L('~joists', 40), L('~lumber_joist_2x8', 24), L('~lumber_post_4x4', 12), L('~beam_glulam', 4)]),
            S('Steel frame', 'all', [L('~steel_stud_framing', 120), L('~steel_frame_beam', 8), L('~joists', 40)]),
        ]),
        S('Roof structure', 'any', [L('~truss_large', 6), L('~truss_medium', 8), L('~truss_small', 10), L('~rafters', 48)]),
        L('~framing_nails', 400),
        L('~joist_hangers', 40),
        L('~hurricane_ties', 60),
        L('~lag_bolts', 16),
        L('~deck_screws', 100),
    ], [SAWS, FIX, WRENCH]),

    'walls': ([
        S('Sheathing', 'any', [L('~osb', 40), L('~sheet_plywood_cdx', 40)]),
        L('building_house_wrap_roll', 4),
        L('~romex_14_2', 150),
        L('~romex_12_2', 150),
        L('~romex_10_3', 30),
        L('~pipe_pvc_half_inch', 30),
        L('~pipe_pvc_one_inch', 16),
        L('~pipe_pvc_two_inch', 10),
        L('~pipe_sewer_solid_4inch', 8),
        L('pipe_pvc_elbow', 30),
        L('pipe_pvc_tee', 20),
        L('building_valve_ball_pvc', 6),
        L('valve_ball_brass', 2),
        L('valve_gate_brass', 1),
        L('gland_cable_entry_wall', 4),
        L('~pvc_primer_can', 4),
        L('~pvc_cement_can', 4),
        S('Insulation', 'any', [L('~insulation_fiberglass_batt', 60), L('~foam_board', 20), L('~insulation_blown', 20)]),
        L('~insulation_spray_foam', 6),   # sealing gaps and penetrations: always
    ], [SAWS, FIX, WRENCH]),

    'exterior': ([
        L('~roofing', 60),
        L('building_roofing_felt_roll', 8),
        L('building_flashing_roll', 4),
        L('~metal', 4),
        L('~roofing_nails', 12),
        L('~siding', 80),
        L('~fascia', 24),
        L('~soffit', 24),
        L('~gutters', 12),
        L('~downspout', 6),
        L('#window', 10),
        L('building_weatherstripping_roll', 4),
    ] + doors(True) + [
        S('Chimney masonry', 'all', [L('~chimney_masonry', 9), L('~mortar', 3), L('~water', 11)]),
    ], [SAWS, FIX, TROWEL, MIXER]),

    'finishings': ([
        L('~drywall', 90),
        L('~joint_compound_bucket', 8),
        L('building_drywall_tape_roll', 10),
        L('#paint', 8),
        L('~flooring', 108),
        S('Tile setting', 'all', [L('~thinset_bucket', 6), L('building_grout_bag', 4), L('~water', 8)], {'uses': '#floor_tile'}),
        L('building_trim_baseboard', 80),
        L('building_trim_casing', 40),
        L('~finishing_nails', 300),
    ] + doors(False), [SAWS, FIX, TROWEL, MIXER]),
}


def wr(path, d, text):
    ar._dump_like(path, text, d)


def main():
    for k, (r, t) in list(RECIPES.items()):
        n, err = recipe_format.normalize(r)
        assert not err, (k, err)
        RECIPES[k] = (n, t)

    # tags and equivalencies the recipe needs
    tp = os.path.join(ROOT, 'assets', '_schemas', 'material_tags.json')
    td = json.load(open(tp, encoding='utf-8'))
    tags = td['tags']
    def items_of(prefix_list):
        out = []
        for cat in ('building',):
            for d in sorted(os.listdir(os.path.join(ROOT, 'assets', cat))):
                if d.startswith(prefix_list) and os.path.isfile(os.path.join(ROOT, 'assets', cat, d, d + '.json')):
                    out.append(d)
        return out
    # only add what is missing: never overwrite what the kit or a later change edited
    tags.setdefault('door_exterior', items_of(('building_door_exterior',)))
    tags.setdefault('door_interior', items_of(('building_door_interior',)))
    tags.setdefault('floor_tile', items_of(('building_floor_tile_')))
    tags.setdefault('window', items_of(('building_window_',)))
    open(tp + '.tmp', 'w', encoding='utf-8', newline='').write(json.dumps(td, indent=2, ensure_ascii=False) + '\n')
    os.replace(tp + '.tmp', tp)

    ep = os.path.join(ROOT, 'assets', '_schemas', 'equivalencies.json')
    ed = json.load(open(ep, encoding='utf-8'))
    E = ed['equivalencies']
    E.setdefault('insulation_blown', {'unit': 'bags', 'label': 'Blown Insulation', 'members': [
        {'item': 'building_insulation_blown_bag', 'value': 1}, {'item': 'building_insulation_blown_bag_pallet_10', 'value': 10},
        {'item': 'building_insulation_blown_bag_pallet_20', 'value': 20}]})
    open(ep + '.tmp', 'w', encoding='utf-8', newline='').write(json.dumps(ed, indent=2, ensure_ascii=False) + '\n')
    os.replace(ep + '.tmp', ep)

    gp = os.path.join(STRUCT, 'farmhouse.json')
    gt = open(gp, encoding='utf-8').read()
    g = json.loads(gt)
    for st in g['growth']['stages']:
        r, t = RECIPES[st['name']]
        st['construction_recipe'] = copy.deepcopy(r)
        st['required_tools'] = copy.deepcopy(t)
    wr(gp, g, gt)
    for st in g['growth']['stages']:
        folder = os.path.join(STRUCT, st['resource'].strip('/').replace('/', os.sep))
        for fn in sorted(os.listdir(folder)):
            if not fn.endswith('.json') or fn.startswith('_'):
                continue
            sp = os.path.join(folder, fn)
            t = open(sp, encoding='utf-8').read()
            m = json.loads(t)
            cf = m.setdefault('category_fields', {})
            cf['construction_recipe'] = copy.deepcopy(st['construction_recipe'])
            cf['required_tools'] = copy.deepcopy(st['required_tools'])
            wr(sp, m, t)
    print('farmhouse recipes set:', ', '.join('%s %d nodes' % (k, len(v[0])) for k, v in RECIPES.items()))


if __name__ == '__main__':
    main()
