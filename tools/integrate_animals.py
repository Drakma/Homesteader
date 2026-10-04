#!/usr/bin/env python3
"""
Puts finished animal models (assets/_scratch/animal_work/final/<sheet>__<stage>.glb, made by tools/finish_animal_model.py) into the asset kit's
animal growth groups: stage models, icons, stage manifests, the group's stage list and its female/male choice (stage `sexes`).

    python tools/integrate_animals.py [group_id ...]      (default: every group whose four models exist)

Per group: stage 1 (baby), a YEARLING stage (created when the group has none), and the final stage "adult" = the FEMALE with `sexes`
(female 80 / male 20), both models in the adult stage's folder. The old model files of a stage are moved to assets/_trash/animals_replaced/.
Icons are rendered from the models (tools/render_icon_from_model.py). Run tools/generate_unity_asset_catalog.py and
tools/package_catalog_as_mods.py afterwards.
"""
import copy
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, 'assets', '_scratch', 'animal_work')
RANCH = os.path.join(ROOT, 'assets', 'ranching')
TRASH = os.path.join(ROOT, 'assets', '_trash', 'animals_replaced')

# sheet (the folder name of its crops) -> the growth group it replaces
GROUPS = {
    'holstein_cow': 'cow_jersey', 'highland_cow': 'cow_holstein', 'jersey_cow': 'cow_gemini_unnamed',
    'duroc_pig': 'pig_duroc', 'hampshire_pig': 'pig_hampshire', 'pink_pig': 'pig_pink',
    'suffolk_sheep': 'sheep_white', 'tan_sheep': 'sheep_brown',
    'black_white_goat': 'goat_gemini_unnamed', 'brown_goat': 'goat_brown', 'white_goat': 'goat_white',
    'red_chicken': 'chicken_red', 'white_chicken': 'chicken_white', 'welsummer_rooter': 'chicken_welsummer',
    'quarter_horse': 'horse_american_quarter',
}
# groups that do not exist yet: id -> (an existing group to copy the shape of, name, sheet)
NEW_GROUPS = {'black_goat': ('brown_goat', 'Black Goat', 'goat_black')}
AGES = [(0, 90), (90, 365), (365, 730)]


def load(p):
    return json.load(open(p, encoding='utf-8'))


def dump(p, d):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)


def trash_old_models(folder, group):
    """Moves a stage folder's old model files (and their textures) out of the way."""
    dest = os.path.join(TRASH, group, os.path.basename(folder.rstrip('/\\')))
    for fn in os.listdir(folder):
        if fn.lower().endswith(('.fbx', '.obj', '.mtl', '.glb', '_base_color.png')) and not fn.startswith('animal_'):
            os.makedirs(dest, exist_ok=True)
            shutil.move(os.path.join(folder, fn), os.path.join(dest, fn))


def render_icon(glb, png):
    subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'render_icon_from_model.py'), glb, png], check=True, capture_output=True)


def stage_manifest(template, item_id, name, models, desc):
    m = copy.deepcopy(template)
    m['id'] = item_id
    m['name'] = name
    m['icon'] = item_id + '.png'
    m['description'] = desc
    m['models'] = models
    m.pop('dimensions', None)
    return m


def integrate(group, sizes):
    sheet = GROUPS[group]
    gdir = os.path.join(RANCH, group)
    gpath = os.path.join(gdir, group + '.json')
    g = load(gpath)
    gname = g['name']
    growth = g['growth']
    old = {s['stage']: s for s in growth['stages']}
    first = growth['stages'][0]
    last = growth['stages'][-1]
    yearling = next((s for s in growth['stages'] if s['name'] == 'yearling'), None)
    # template for a new stage manifest: the old adult one
    tmpl_path = os.path.join(gdir, last['resource'].rstrip('/').replace('/', os.sep), 'animal_%s_%s.json' % (last['resource'].rstrip('/').split('/')[-1].replace('animal_', ''), group))
    template = load(tmpl_path) if os.path.exists(tmpl_path) else load(os.path.join(RANCH, 'holstein_cow', 'stages', 'animal_adult', 'animal_adult_holstein_cow.json'))

    # ---- the three stages: (stage name, folder, models [(file, source glb, icon file or None, label)])
    s1_name = first['name']
    s1_folder = first['resource'].rstrip('/').split('/')[-1]
    y_folder = (yearling['resource'].rstrip('/').split('/')[-1]) if yearling else 'animal_yearling'
    a_folder = last['resource'].rstrip('/').split('/')[-1]
    plan = [
        (s1_name, s1_folder, [('%s_%s.glb' % (group, s1_name), 'baby', None)]),
        ('yearling', y_folder, [('%s_yearling.glb' % group, 'juvenile', None)]),
        ('adult', a_folder, [('%s_adult_female.glb' % group, 'adult_female', None), ('%s_adult_male.glb' % group, 'adult_male', 'male')]),
    ]
    new_stages = []
    for idx, (sname, folder, models) in enumerate(plan):
        sdir = os.path.join(gdir, 'stages', folder)
        os.makedirs(sdir, exist_ok=True)
        trash_old_models(sdir, group)
        item_id = 'animal_%s_%s' % (folder.replace('animal_', ''), group)
        mlist = []
        icons = {}
        for fname, key, tag in models:
            src = os.path.join(W, 'final', '%s__%s.glb' % (sheet, key))
            dst = os.path.join(sdir, fname)
            shutil.copyfile(src, dst)
            info = sizes.get('%s__%s' % (sheet, key), {})
            sz = info.get('size', [0, 0, 0])
            mlist.append({'file': fname, 'format': 'glb', 'dimensions_m': {'x': sz[0], 'y': sz[2], 'z': sz[1]}, 'triangles': info.get('tris', 0)})
            icon_name = item_id + ('_male' if tag == 'male' else '') + '.png'
            render_icon(dst, os.path.join(sdir, icon_name))
            icons[tag or 'main'] = icon_name
        m = stage_manifest(template, item_id, '%s - %s' % (gname, sname.capitalize()), mlist,
                           'The %s stage of the %s.' % (sname, gname.lower()))
        dump(os.path.join(sdir, item_id + '.json'), m)
        open(os.path.join(sdir, 'README.md'), 'w', encoding='utf-8').write('# %s\n\nModels: %s\n' % (m['name'], ', '.join(x['file'] for x in mlist)))
        stage = {'stage': idx + 1, 'name': sname, 'age_min': AGES[idx][0], 'age_max': AGES[idx][1],
                 'resource': 'stages/%s/' % folder, 'model': models[0][0], 'icon': icons['main']}
        if sname == 'adult':
            stage['sexes'] = [
                {'sex': 'female', 'chance_pct': 80, 'model': models[0][0], 'icon': icons['main']},
                {'sex': 'male', 'chance_pct': 20, 'model': models[1][0], 'icon': icons['male']},
            ]
        new_stages.append(stage)
    growth['stages'] = new_stages
    growth['total_stages'] = 3
    growth['icon_stage'] = 3
    growth['max_age'] = 730
    g['growth'] = growth
    # the group's own icon: the adult female
    a_dir = os.path.join(gdir, 'stages', a_folder)
    shutil.copyfile(os.path.join(a_dir, new_stages[2]['icon']), os.path.join(gdir, g.get('icon') or group + '.png'))
    dump(gpath, g)
    print('integrated', group, [s['name'] for s in new_stages])


def clone_group(new_id, template_id, name):
    """A new growth group shaped like an existing one (same stage list and folders; models, icons and manifests are made by integrate())."""
    gdir = os.path.join(RANCH, new_id)
    if os.path.isdir(gdir):
        return
    t = load(os.path.join(RANCH, template_id, template_id + '.json'))
    os.makedirs(gdir)
    g = copy.deepcopy(t)
    g['id'] = new_id
    g['name'] = name
    g['icon'] = new_id + '.png'
    g['description'] = 'The %s.' % name.lower()
    g['growth']['species'] = new_id
    dump(os.path.join(gdir, new_id + '.json'), g)
    print('created group', new_id)


def main():
    sizes = load(os.path.join(W, 'final', 'sizes.json'))
    only = sys.argv[1:]
    for gid, (tmpl, name, sheet) in NEW_GROUPS.items():
        if only and gid not in only:
            continue
        if os.path.exists(os.path.join(W, 'final', sheet + '__baby.glb')):
            clone_group(gid, tmpl, name)
            GROUPS[gid] = sheet
    for group, sheet in GROUPS.items():
        if only and group not in only:
            continue
        need = ['%s__%s' % (sheet, k) for k in ('baby', 'juvenile', 'adult_female', 'adult_male')]
        missing = [n for n in need if not os.path.exists(os.path.join(W, 'final', n + '.glb'))]
        if missing:
            print('skipped', group, 'missing', missing)
            continue
        integrate(group, sizes)


if __name__ == '__main__':
    main()
