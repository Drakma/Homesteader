"""Sets the manual well's recipes (group and stage manifests) and the water and cement equivalencies. Run after tools/build_well_group.py."""
import json, os, sys, time, glob
sys.path.insert(0, r'C:\Users\casey\Desktop\Homesteader\tools')
import asset_references as ar
import recipe_format

ROOT = r'C:\Users\casey\Desktop\Homesteader'


def wr(p, d):
    txt = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    for _ in range(30):
        try:
            open(p + '.tmp', 'w', encoding='utf-8', newline='').write(txt)
            os.replace(p + '.tmp', p)
            return
        except OSError:
            time.sleep(1.5)
    raise SystemExit('write ' + p)


# ---- equivalencies: water (liters, the full jugs and the bucket) and cement (bags)
ep = os.path.join(ROOT, 'assets', '_schemas', 'equivalencies.json')
ed = json.load(open(ep, encoding='utf-8'))
E = ed['equivalencies']
if 'water' not in E:     # never overwrite: the kit and later changes edit these (the jug pallets, for one)
    E['water'] = {'unit': 'L', 'label': 'Water', 'members': [
        {'item': 'water_jug_1l', 'value': 1}, {'item': 'water_jug_5l', 'value': 5}, {'item': 'water_bucket_water', 'value': 10},
        {'item': 'water_jug_1l_pallet_5', 'value': 5}, {'item': 'water_jug_1l_pallet_10', 'value': 10},
        {'item': 'water_jug_5l_pallet_5', 'value': 25}, {'item': 'water_jug_5l_pallet_10', 'value': 50}]}
if 'cement' not in E:
    E['cement'] = {'unit': 'bags', 'label': 'Cement', 'members': [
        {'item': '20lb_cement_bag', 'value': 1}, {'item': '20lb_cement_bag_pallet_10', 'value': 10}, {'item': '20lb_cement_bag_pallet_20', 'value': 20}]}
wr(ep, ed)

# ---- the recipes
SHOVELS = ['tool_shovel', 'tool_shovel_round_point', 'tool_shovel_trenching', 'tool_pickaxe']
TROWEL = ['tool_trowel_hand']
HAMMERS = ['tool_hammer', 'tool_hammer_claw', 'tool_hammer_club']
SAWS = ['tool_saw_hand', 'tool_circular_saw_corded', 'tool_circular_saw_cordless', 'tool_miter_saw']
MIXER = ['tool_wheelbarrow', 'tool_plastic_wheelbarrow', 'tool_steel_wheelbarrow', 'tool_cement_mixer']   # wet mixes are mixed in a wheelbarrow or a cement mixer


def L(spec, q):
    return {'item_id': spec, 'quantity': q}


RECIPES = {
    # Footing ring about 0.28 m3 of concrete. Bagged mix: 20 lb bag yields 0.15 cu ft (0.0042 m3) -> 67 bags, about 0.9 L of water each (1 quart).
    # Own mix 1 cement : 2 sand : 3 aggregate by volume (dry volume = 1.54 x wet): 0.072 m3 cement (about 104 kg = 12 bags of 20 lb), 0.14 m3 sand,
    # 0.22 m3 aggregate; water/cement 0.5 by weight -> about 52 L.
    'foundation': ([
        L('~gravel', 0.15),
        {'section': 'Concrete', 'mode': 'any', 'items': [
            {'section': 'Bagged concrete mix', 'mode': 'all', 'items': [L('~concrete_mix', 67), L('~water', 60)]},
            {'section': 'Mix your own: 1 cement, 2 sand, 3 aggregate', 'mode': 'all', 'items': [L('~cement', 12), L('~sand', 0.14), L('~gravel', 0.22), L('~water', 52)]},
        ]},
    ], [SHOVELS, TROWEL, MIXER]),
    # Mortar joints about 0.05 m3. A 60 lb mortar bag yields about 0.45 cu ft (0.013 m3) -> 4 bags, about 3.5 L of water each (Quikrete: 3 3/4 quarts).
    'framing': ([
        {'section': 'Stone lining', 'mode': 'any', 'items': [L('~masonry_fieldstone', 12), L('~masonry_units', 30)]},
        {'section': 'Mortar', 'mode': 'all', 'items': [L('~mortar', 4), L('~water', 14)]},
    ], [SHOVELS, TROWEL, MIXER]),
    # the curb: about 0.025 m3 of mortar (2 bags)
    'walls': ([
        L('~masonry_units', 12),
        {'section': 'Mortar', 'mode': 'all', 'items': [L('~mortar', 2), L('~water', 7)]},
        L('~framing_lumber', 10),
    ], [TROWEL, SAWS, HAMMERS, MIXER]),
    'complete': ([L('~framing_lumber', 8), L('#roofing', 4), L('mat_rope', 1), L('tool_bucket_empty', 1)], [SAWS, HAMMERS]),
}
for k, (r, t) in RECIPES.items():
    n, err = recipe_format.normalize(r)
    assert not err, (k, err)
    RECIPES[k] = (n, t)

gp = os.path.join(ROOT, 'assets', 'structures', 'water_well_manual', 'water_well_manual.json')
gt = open(gp, encoding='utf-8').read()
g = json.loads(gt)
for st in g['growth']['stages']:
    r, t = RECIPES[st['name']]
    st['construction_recipe'] = json.loads(json.dumps(r))
    st['required_tools'] = json.loads(json.dumps(t))
ar._dump_like(gp, gt, g)
for st in g['growth']['stages']:
    sid = 'struct_%s_water_well_manual' % st['name']
    sp = os.path.join(ROOT, 'assets', 'structures', 'water_well_manual', 'stages', 'struct_' + st['name'], sid + '.json')
    t = open(sp, encoding='utf-8').read()
    m = json.loads(t)
    m['category_fields']['construction_recipe'] = json.loads(json.dumps(st['construction_recipe']))
    m['category_fields']['required_tools'] = json.loads(json.dumps(st['required_tools']))
    ar._dump_like(sp, t, m)
print('ok')
