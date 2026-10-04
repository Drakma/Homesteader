#!/usr/bin/env python3
"""
Rigs every quadruped growth group's models with tools/auto_rig_quadruped.py and puts them into the asset kit.

    python tools/rig_animals_batch.py [group_id ...]

For each group: runs the rigger on the four finished models (baby, juvenile, adult female, adult male) from
assets/_originals/animals_2k/final_scaled, copies the rigged GLBs over the stage models, marks them rigged in the stage manifests and writes the
adult female's measured walk / run ground speed into the species AI profile (assets/_ai/<species>.json, movement.*_native_mps).
Then run tools/generate_unity_asset_catalog.py and tools/package_catalog_as_mods.py.
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from integrate_animals import GROUPS, NEW_GROUPS  # group -> the prefix of its model files

SRC = os.path.join(ROOT, 'assets', '_originals', 'animals_2k', 'final_scaled')
RANCH = os.path.join(ROOT, 'assets', 'ranching')
AI = os.path.join(ROOT, 'assets', '_ai')
# species -> (leg_top, run gait, AI profile)
SPECIES = {'cow': (0.55, 'trot', 'cow'), 'pig': (0.42, 'trot', 'pig'), 'sheep': (0.5, 'trot', 'sheep'), 'goat': (0.5, 'gallop', 'goat'),
           'horse': (0.58, 'gallop', 'horse'), 'goat_black': (0.5, 'gallop', 'goat')}
KEYS = ('baby', 'juvenile', 'adult_female', 'adult_male')
SKIP_AI = {'horse'}          # tuned by hand


def load(p):
    return json.load(open(p, encoding='utf-8'))


def dump(p, d):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)


def stage_files(group):
    """{key: (stage folder, model file)} from the group's growth stages."""
    g = load(os.path.join(RANCH, group, group + '.json'))
    out = {}
    stages = g['growth']['stages']
    out['baby'] = (stages[0]['resource'], stages[0]['model'])
    out['juvenile'] = (stages[1]['resource'], stages[1]['model'])
    ad = stages[-1]
    sexes = {s['sex']: s['model'] for s in ad.get('sexes', [])}
    out['adult_female'] = (ad['resource'], sexes.get('female', ad['model']))
    out['adult_male'] = (ad['resource'], sexes.get('male'))
    return out


def main():
    only = sys.argv[1:]
    log = open(os.path.join(ROOT, 'assets', '_scratch', 'animal_work', 'rig_batch.log'), 'a')
    species_native = {}
    todo = dict(GROUPS)
    for gid, (_t, _n, sh) in NEW_GROUPS.items():
        todo[gid] = sh
    for group, sheet in todo.items():
        if only and group not in only:
            continue
        sp = sheet.split('_')[0]
        if sp == 'chicken':
            continue                       # two legs: needs a bird rig
        leg_top, run_id, ai = SPECIES.get(sp, (0.55, 'trot', None))
        files = stage_files(group)
        for key in KEYS:
            folder, fname = files[key]
            src = os.path.join(SRC, '%s__%s.glb' % (sheet, key))
            if not fname or not os.path.exists(src):
                print('skip', group, key)
                continue
            dst = os.path.join(RANCH, group, folder.rstrip('/').replace('/', os.sep), fname)
            tmp = dst[:-4] + '_rigged.glb'
            r = subprocess.run(['blender', '-b', '-P', os.path.join(ROOT, 'tools', 'auto_rig_quadruped.py'), '--', src, tmp, str(leg_top), '--run', run_id],
                               capture_output=True, text=True)
            ok = os.path.exists(tmp) and 'INFO rigged' in r.stdout
            native = re.search(r'NATIVE (\{.*\})', r.stdout)
            print(group, key, 'ok' if ok else 'FAILED', native.group(1) if native else '')
            log.write('%s %s %s\n' % (group, key, 'ok' if ok else r.stderr[-300:]))
            log.flush()
            if not ok:
                continue
            os.replace(tmp, dst)
            # stage manifest
            mdir = os.path.dirname(dst)
            for mf in os.listdir(mdir):
                if mf.endswith('.json'):
                    m = load(os.path.join(mdir, mf))
                    hit = False
                    for mod in m.get('models', []):
                        if mod.get('file') == fname:
                            mod.update({'rigged': True, 'skeleton': 'auto_rig_quadruped', 'animations': ['Idle', 'Walk', 'Run', 'Eating']})
                            hit = True
                    if hit:
                        dump(os.path.join(mdir, mf), m)
            if key == 'adult_female' and native:
                species_native[ai] = json.loads(native.group(1).replace("'", '"'))
    for ai, n in species_native.items():
        if not ai or ai in SKIP_AI:
            continue
        p = os.path.join(AI, ai + '.json')
        d = load(p)
        mv = d.setdefault('movement', {})
        mv['walk_native_mps'] = n['Walk']
        mv['run_native_mps'] = n['Run']
        dump(p, d)
        print('AI', ai, n)


if __name__ == '__main__':
    main()
