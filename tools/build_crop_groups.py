#!/usr/bin/env python3
"""
Rebuilds the asset kit's crop growth groups around the PROCEDURAL crop models (Homesteader/Assets/Scripts/World/ProceduralCrops.cs).

    python tools/build_crop_groups.py [crop ...]            (default: all ten crops)

Needs the GLBs the Unity menu "Homesteader / Export Crop Models" writes to assets/_scratch/crop_models/<crop>__<look>.glb.
For each crop it
  * saves the old group folder to assets/_originals/crops_old/<crop>/ (first run only, never overwritten),
  * writes the six looks of a fruiting tree as crop stages: sprout, small, medium, mature, ripe (the harvest look) as stages 1-5, plus the
    withered and dead versions (growth.rules.failure), each with its GLB, icon (rendered from the model), stage manifest and README,
  * rewrites the group manifest (age windows are fractions of max_age; harvest at stage 5; the seed plants the group) and the kit_config entries.
Creates the groups for carrot, potato, tomato, strawberry, herb and cotton, which had seeds but no group.
Run tools/generate_unity_asset_catalog.py and tools/package_catalog_as_mods.py afterwards.
"""
import copy
import json
import os
import shutil
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FARM = os.path.join(ROOT, 'assets', 'farming')
SRC = os.path.join(ROOT, 'assets', '_scratch', 'crop_models')
OLD = os.path.join(ROOT, 'assets', '_originals', 'crops_old')
STAGES = ['sprout', 'small', 'medium', 'mature', 'ripe']
FRACTIONS = [0.0, 0.11, 0.33, 0.6, 0.83, 1.0]

# crop -> display name, yield item, amount range, seed, planting seasons, max age (None = keep the group's), water interval, harvest tool
CROPS = {
    'corn':       dict(name='Corn Plant', item='ingredient_corn', amt=(3, 3), seed='seed_corn', seasons=['spring', 'summer'], age=None, water=7),
    'sunflower':  dict(name='Sunflower Plant', item='ingredient_sunflower', amt=(1, 1), seed='seed_sunflower', seasons=['summer'], age=None, water=7),
    'wheat':      dict(name='Wheat Plant', item='ingredient_wheat', amt=(2, 2), seed='seed_wheat', seasons=['summer'], age=None, water=7, tool='#tool_sickle'),
    'pumpkin':    dict(name='Pumpkin Plant', item='food_pumpkin', amt=(1, 2), seed='seed_pumpkin', seasons=['spring', 'summer'], age=None, water=5),
    'carrot':     dict(name='Carrot Plant', item='food_carrot', amt=(2, 4), seed='seed_carrot', seasons=['spring'], age=70, water=4),
    'potato':     dict(name='Potato Plant', item='food_potato', amt=(3, 5), seed='seed_potato', seasons=['spring'], age=80, water=5),
    'tomato':     dict(name='Tomato Plant', item='food_tomato', amt=(3, 6), seed='seed_tomato', seasons=['spring', 'summer'], age=75, water=3),
    'strawberry': dict(name='Strawberry Plant', item='food_strawberry', amt=(3, 6), seed='seed_strawberry', seasons=['spring'], age=60, water=3),
    'herb':       dict(name='Herb Plant', item='ingredient_herbs', amt=(1, 3), seed='seed_herb', seasons=['spring', 'summer', 'fall'], age=30, water=4),
    'cotton':     dict(name='Cotton Plant', item='ingredient_cotton', amt=(1, 3), seed='seed_cotton', seasons=['summer'], age=150, water=6),
}


def _new(name, item, item_name, amt, seasons, age, water, season_text=None, weight=0.5, value=10, seed_name=None, tool=None):
    """A crop that has no seed or harvest item yet: build_crop_groups creates the seed manifest (no icon, no model: the packets are made by hand),
    and the harvest item (an icon rendered from the ripe plant, no model)."""
    c = dict(name=name + ' Plant', item=item, item_name=item_name, amt=amt, seed='seed_' + name.lower().replace(' ', '_'), seasons=seasons, age=age,
             water=water, new=True, season_text=season_text or seasons[-1], weight=weight, value=value, seed_name=seed_name or (name + ' Seeds'))
    if tool:
        c['tool'] = tool
    return c


CROPS.update({
    'onion':       _new('Onion', 'food_onion', 'Fresh Onion', (2, 4), ['spring'], 100, 4),
    'garlic':      _new('Garlic', 'food_garlic', 'Garlic Bulb', (2, 4), ['spring'], 120, 4, value=12),
    'lettuce':     _new('Lettuce', 'food_lettuce', 'Head of Lettuce', (1, 2), ['spring', 'fall'], 45, 2),
    'cabbage':     _new('Cabbage', 'food_cabbage', 'Head of Cabbage', (1, 2), ['spring', 'fall'], 80, 3, weight=1.2),
    'spinach':     _new('Spinach', 'food_spinach', 'Fresh Spinach', (2, 4), ['spring', 'fall'], 40, 2),
    'broccoli':    _new('Broccoli', 'food_broccoli', 'Broccoli Crown', (1, 2), ['spring', 'fall'], 70, 3),
    'beet':        _new('Beet', 'food_beet', 'Fresh Beet', (2, 4), ['spring', 'fall'], 60, 4),
    'radish':      _new('Radish', 'food_radish', 'Fresh Radish', (3, 6), ['spring', 'fall'], 30, 3, value=6),
    'rhubarb':     _new('Rhubarb', 'food_rhubarb', 'Rhubarb Stalks', (2, 4), ['spring'], 90, 4),
    'peas':        _new('Peas', 'food_peas', 'Fresh Peas', (3, 6), ['spring', 'fall'], 60, 3, seed_name='Pea Seeds'),
    'green_beans': _new('Green Bean', 'food_green_beans', 'Green Beans', (3, 6), ['spring', 'summer'], 60, 3, 'summer', seed_name='Green Bean Seeds'),
    'cucumber':    _new('Cucumber', 'food_cucumber', 'Fresh Cucumber', (2, 4), ['spring', 'summer'], 55, 3, 'summer'),
    'zucchini':    _new('Zucchini', 'food_zucchini', 'Zucchini', (2, 4), ['spring', 'summer'], 50, 3, 'summer', weight=0.8),
    'peppers':     _new('Pepper', 'food_pepper', 'Bell Pepper', (2, 4), ['spring', 'summer'], 75, 3, 'summer', seed_name='Pepper Seeds'),
    'peanuts':     _new('Peanut', 'food_peanuts', 'Raw Peanuts', (3, 6), ['summer'], 110, 4, seed_name='Peanut Seeds'),
    'watermelon':  _new('Watermelon', 'food_watermelon', 'Watermelon', (1, 1), ['summer'], 90, 5, weight=5.0, value=25),
    'cantaloupe':  _new('Cantaloupe', 'food_cantaloupe', 'Cantaloupe', (1, 2), ['summer'], 80, 5, weight=1.5, value=15),
    'oats':        _new('Oat', 'ingredient_oats', 'Oat Grain', (2, 2), ['spring'], 90, 5, 'spring', seed_name='Oat Seeds', tool='#tool_sickle'),
    'barley':      _new('Barley', 'ingredient_barley', 'Barley Grain', (2, 2), ['spring'], 90, 5, 'spring', tool='#tool_sickle'),
    'soybeans':    _new('Soybean', 'ingredient_soybeans', 'Soybeans', (3, 3), ['summer'], 100, 5, seed_name='Soybean Seeds'),
    'alfalfa':     _new('Alfalfa', 'ingredient_alfalfa', 'Alfalfa Hay', (2, 2), ['spring'], 80, 5, tool='#tool_sickle'),
    'hops':        _new('Hops', 'ingredient_hops', 'Hops Cones', (2, 2), ['summer'], 120, 4),
    'tobacco':     _new('Tobacco', 'ingredient_tobacco', 'Tobacco Leaf', (2, 2), ['summer'], 120, 4),
    'flax':        _new('Flax', 'ingredient_flax', 'Flax Stems', (2, 2), ['spring'], 100, 4, tool='#tool_sickle'),
})
for _k, _v in CROPS.items():
    if _v.get('new') and _k != _v['name'].replace(' Plant', '').lower().replace(' ', '_'):
        _v['seed'] = 'seed_' + _k


def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def dump(p, d):
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write('\n')
    os.replace(tmp, p)


def glb_info(path):
    """(triangles, [x, y, z] size in metres) of a GLB, from its accessors."""
    b = open(path, 'rb').read()
    jl = struct.unpack_from('<I', b, 12)[0]
    j = json.loads(b[20:20 + jl])
    tris, lo, hi = 0, [1e9] * 3, [-1e9] * 3
    for mesh in j.get('meshes', []):
        for prim in mesh['primitives']:
            if 'indices' in prim:
                tris += j['accessors'][prim['indices']]['count'] // 3
            a = j['accessors'][prim['attributes']['POSITION']]
            for i in range(3):
                lo[i] = min(lo[i], a['min'][i])
                hi[i] = max(hi[i], a['max'][i])
    return tris, [round(hi[i] - lo[i], 3) for i in range(3)]


def render_icon(glb, png):
    subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'render_icon_from_model.py'), glb, png], check=True, capture_output=True)


def stage_manifest(template, crop, look, label, glb, size, tris, name):
    item_id = 'crop_%s_%s' % (look, crop)
    m = copy.deepcopy(template)
    m['id'] = item_id
    m['name'] = '%s (%s)' % (name.replace(' Plant', ''), label)
    m['description'] = 'The %s look of a %s plant.' % (label.lower(), name.replace(' Plant', '').lower())
    m['icon'] = item_id + '.png'
    m['models'] = [{'file': item_id + '.glb', 'format': 'glb', 'triangles': tris}]
    m.setdefault('category_fields', {})
    m['category_fields']['crop_species'] = crop
    m['category_fields']['dimensions_m'] = {'width': size[0], 'depth': size[2], 'height': size[1]}
    return item_id, m


def build(crop, cfg, template, pumpkin_group):
    gdir = os.path.join(FARM, crop)
    gpath = os.path.join(gdir, crop + '.json')
    if os.path.isdir(gdir) and not os.path.isdir(os.path.join(OLD, crop)):
        shutil.copytree(gdir, os.path.join(OLD, crop))          # the old models, kept
    os.makedirs(gdir, exist_ok=True)
    old = load(gpath) if os.path.exists(gpath) else None
    rules_old = ((old or {}).get('growth') or {}).get('rules') or {}
    max_age = cfg['age'] or (old['growth']['max_age'] if old else 90)
    ages = [round(max_age * f) for f in FRACTIONS]
    ages[-1] = max_age

    looks = STAGES + ['withered', 'dead']
    missing = [l for l in looks if not os.path.exists(os.path.join(SRC, '%s__%s.glb' % (crop, l)))]
    if missing:
        print('SKIP', crop, 'missing models', missing)
        return None

    # the old stage folders that are not part of the new layout go away (they are saved in _originals)
    sdir = os.path.join(gdir, 'stages')
    if os.path.isdir(sdir):
        for f in os.listdir(sdir):
            shutil.rmtree(os.path.join(sdir, f))
    os.makedirs(sdir, exist_ok=True)

    stage_entries, ids = [], {}
    for i, look in enumerate(looks):
        glb_src = os.path.join(SRC, '%s__%s.glb' % (crop, look))
        tris, size = glb_info(glb_src)
        folder = 'crop_' + look
        d = os.path.join(sdir, folder)
        os.makedirs(d, exist_ok=True)
        item_id, m = stage_manifest(template, crop, look, look.capitalize(), glb_src, size, tris, cfg['name'])
        shutil.copyfile(glb_src, os.path.join(d, item_id + '.glb'))
        render_icon(os.path.join(d, item_id + '.glb'), os.path.join(d, item_id + '.png'))
        dump(os.path.join(d, item_id + '.json'), m)
        open(os.path.join(d, 'README.md'), 'w', encoding='utf-8', newline='\n').write('# %s\n\nModel: %s.glb (procedural, exported from the game)\n' % (m['name'], item_id))
        ids[look] = item_id
        if i < len(STAGES):
            stage_entries.append({'stage': i + 1, 'name': look, 'age_min': ages[i], 'age_max': ages[i + 1],
                                  'resource': 'stages/%s/' % folder, 'model': item_id + '.glb', 'icon': item_id + '.png'})

    yield_rule = {'item_id': cfg['item'], 'amount_min': cfg['amt'][0], 'amount_max': cfg['amt'][1], 'harvest_stage': 5}
    tool = cfg.get('tool') or (rules_old.get('yield') or {}).get('tool')
    if tool:
        yield_rule['tool'] = tool
    old_plant = rules_old.get('planting') or {}
    rules = {
        'yield': yield_rule,
        'planting': {'seasons': old_plant.get('seasons') or cfg['seasons'], 'biomes': ['biome_farmland'], 'item_id': cfg['seed'],
                     'min_temp_c': old_plant.get('min_temp_c', 8), 'max_temp_c': old_plant.get('max_temp_c', 40)},
        'needs': {'water_interval_days': (rules_old.get('needs') or {}).get('water_interval_days', cfg['water'])},
        'failure': {
            'out_of_season': 'wither', 'frost_kills': True, 'drought_days_before_wither': 7, 'wither_behavior': 'die',
            'withered': {'resource': 'stages/crop_withered/', 'model': ids['withered'] + '.glb', 'icon': ids['withered'] + '.png'},
            'dead': {'resource': 'stages/crop_dead/', 'model': ids['dead'] + '.glb', 'icon': ids['dead'] + '.png'},
        },
    }
    if old and (rules_old.get('failure') or {}).get('wither_behavior'):
        for k in ('out_of_season', 'frost_kills', 'drought_days_before_wither', 'wither_behavior'):
            if k in rules_old['failure']:
                rules['failure'][k] = rules_old['failure'][k]

    group = copy.deepcopy(pumpkin_group)
    group['id'] = crop
    group['name'] = cfg['name']
    group['icon'] = crop + '.png'
    group['description'] = ('A %s lifecycle growing through 5 stages (sprout -> small -> medium -> mature -> ripe) over %d days, with withered and dead '
                            'versions. The models are procedural (built in the game), the originals are kept in assets/_originals/crops_old.'
                            % (cfg['name'].replace(' Plant', '').lower(), max_age))
    g = group['growth']
    g.update({'growth_type': 'crop', 'species': crop, 'max_age': max_age, 'time_unit': 'days', 'total_stages': 5, 'icon_stage': 5,
              'stages': stage_entries, 'rules': rules})
    dump(gpath, group)
    shutil.copyfile(os.path.join(sdir, 'crop_ripe', ids['ripe'] + '.png'), os.path.join(gdir, crop + '.png'))
    if cfg.get('new'):
        create_items(crop, cfg, os.path.join(sdir, 'crop_ripe', ids['ripe'] + '.png'), os.path.join(sdir, 'crop_ripe', ids['ripe'] + '.glb'))
    print('built', crop, 'max_age', max_age, [(s['name'], s['age_min'], s['age_max']) for s in stage_entries])
    return {'name': cfg['name'], 'max_age': max_age, 'stages': [(s['stage'], s['name'], ids[s['name']], s['age_min'], s['age_max']) for s in stage_entries]}


def create_items(crop, cfg, ripe_png, ripe_glb):
    """The seed manifest (icon and 3D packet are made by hand: none are written) and the harvest item (icon from the ripe plant, no model) of a new crop."""
    # ---- seed
    seed_id = cfg['seed']
    sdir = os.path.join(FARM, seed_id)
    if not os.path.exists(os.path.join(sdir, seed_id + '.json')):
        m = load(os.path.join(FARM, 'seed_carrot', 'seed_carrot.json'))
        m['id'] = seed_id
        m['name'] = cfg['seed_name']
        m['description'] = 'Seeds for planting %s.' % cfg['name'].replace(' Plant', '').lower()
        m['icon'] = seed_id + '.png'
        m['models'] = []
        m['category_fields'].update({'crop_species': crop, 'days_to_mature': cfg['age'], 'season': cfg['season_text'], 'yield_amount': 0, 'yields_item_id': ''})
        os.makedirs(sdir, exist_ok=True)
        dump(os.path.join(sdir, seed_id + '.json'), m)
        seed_icon = os.path.join(ROOT, 'assets', '_scratch', 'crop_icons_final', seed_id + '.png')
        if os.path.exists(seed_icon):
            shutil.copyfile(seed_icon, os.path.join(sdir, seed_id + '.png'))
        open(os.path.join(sdir, 'README.md'), 'w', encoding='utf-8', newline='\n').write(
            '# %s\n\nSeed packet item. The icon comes from the seed sheet when one exists; the 3D packet model is made by hand and none exists yet.\n' % m['name'])
    # ---- harvest item
    item = cfg['item']
    is_food = item.startswith('food_')
    cat = 'food' if is_food else 'ingredients'
    idir = os.path.join(ROOT, 'assets', cat, item)
    if not os.path.exists(os.path.join(idir, item + '.json')):
        src = load(os.path.join(ROOT, 'assets', 'food', 'food_carrot', 'food_carrot.json')) if is_food else \
            load(os.path.join(ROOT, 'assets', 'ingredients', 'ingredient_wheat', 'ingredient_wheat.json'))
        m = src
        m['id'] = item
        m['name'] = cfg['item_name']
        m['category'] = cat
        m['description'] = 'The harvest of a %s plant.' % cfg['name'].replace(' Plant', '').lower()
        m['icon'] = item + '.png'
        m['models'] = []
        m.pop('dimensions', None)
        m['properties']['weight_kg'] = cfg['weight']
        m['properties']['base_value'] = cfg['value']
        if 'category_fields' in m:
            m['category_fields'].pop('dimensions_m', None)
        os.makedirs(idir, exist_ok=True)
        dump(os.path.join(idir, item + '.json'), m)
        own = os.path.join(ROOT, 'assets', '_scratch', 'crop_icons_final', 'harvest_%s.png' % crop)
        shutil.copyfile(own if os.path.exists(own) else ripe_png, os.path.join(idir, item + '.png'))
        open(os.path.join(idir, 'README.md'), 'w', encoding='utf-8', newline='\n').write(
            '# %s\n\nIcon rendered from the ripe %s plant. No 3D model yet.\n' % (m['name'], crop))


def update_kit_config(done):
    p = os.path.join(ROOT, 'assets', 'kit_config.json')
    cfg = load(p)
    for crop, info in done.items():
        cfg.setdefault('subfolders', {})
        cfg['subfolders'].setdefault(crop, {'name': info['name'], 'icon': '', 'category': 'farming'})
        cfg['subfolders'][crop]['name'] = info['name']
        cfg['growth_groups'][crop] = {
            'name': info['name'], 'icon': (cfg['subfolders'][crop].get('icon') or ''), 'category': 'farming', 'growth_type': 'crop',
            'max_age': info['max_age'], 'time_unit': 'days',
            'stages': [{'stage': n, 'name': nm, 'item_id': iid, 'age_min': a, 'age_max': b} for n, nm, iid, a, b in info['stages']],
        }
    dump(p, cfg)


def apply_icons():
    """Copies the staged seed / harvest icons (assets/_scratch/crop_icons_final, from tools/split_crop_sheets.py) into the items of the new crops."""
    src = os.path.join(ROOT, 'assets', '_scratch', 'crop_icons_final')
    n = 0
    for crop, cfg in CROPS.items():
        if not cfg.get('new'):
            continue
        for kind, item_id, cat in (('seed', cfg['seed'], 'farming'), ('harvest', cfg['item'], 'food' if cfg['item'].startswith('food_') else 'ingredients')):
            f = os.path.join(src, '%s_%s.png' % (kind, crop))
            d = os.path.join(ROOT, 'assets', cat, item_id)
            if os.path.exists(f) and os.path.isdir(d):
                shutil.copyfile(f, os.path.join(d, item_id + '.png'))
                n += 1
    print('applied', n, 'icons')


def main():
    if '--icons' in sys.argv:
        apply_icons()
        return
    only = sys.argv[1:] or list(CROPS)
    template = load(os.path.join(OLD, 'pumpkin', 'stages', 'crop_small', 'crop_small_pumpkin.json')) if os.path.isdir(os.path.join(OLD, 'pumpkin')) \
        else load(os.path.join(FARM, 'pumpkin', 'stages', 'crop_small', 'crop_small_pumpkin.json'))
    pumpkin_group = load(os.path.join(OLD, 'pumpkin', 'pumpkin.json')) if os.path.isdir(os.path.join(OLD, 'pumpkin')) else load(os.path.join(FARM, 'pumpkin', 'pumpkin.json'))
    done = {}
    for crop in only:
        info = build(crop, CROPS[crop], template, pumpkin_group)
        if info:
            done[crop] = info
    if done:
        update_kit_config(done)


if __name__ == '__main__':
    main()
