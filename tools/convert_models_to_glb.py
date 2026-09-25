"""
Batch-converts the catalog's FBX / OBJ(+MTL) models to GLB (the project's default model format).

  python tools/convert_models_to_glb.py --list                   # what would be converted
  python tools/convert_models_to_glb.py --only farming logging   # test a few categories
  python tools/convert_models_to_glb.py --run                    # convert everything (resumable)
  python tools/convert_models_to_glb.py --run --force            # redo models that already have a .glb

Writes <stem>.glb beside each source model, keeps the originals, and appends a line per model to
tools/glb_conversion_log.jsonl. Rigged/animated FBX are skipped (Unity needs FBX for Humanoid/Generic
animation). Manifests are NOT touched here: run tools/apply_glb_to_manifests.py afterwards.
"""
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'assets')
BLENDER = r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
LOG = os.path.join(ROOT, 'tools', 'glb_conversion_log.jsonl')
BATCH = 20
SKIP_DIRS = {'_asset_requests', 'hud_kit', '_docs', '_schemas', '_gamerules', 'textures', 'models_legacy'}


def manifest_dims(model_path):
    """[w, d, h] in metres from the manifest that owns this model (same folder), or None."""
    folder = os.path.dirname(model_path)
    fname = os.path.basename(model_path)
    stem = os.path.splitext(fname)[0]
    best = None
    for f in os.listdir(folder):
        if not f.endswith('.json'):
            continue
        try:
            d = json.load(open(os.path.join(folder, f), encoding='utf-8'))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        dims = ((d.get('category_fields') or {}).get('dimensions_m')) or d.get('dimensions_m')
        if not isinstance(dims, dict):
            continue
        listed = [m.get('file') if isinstance(m, dict) else m for m in (d.get('models') or [])]
        w, dp, h = dims.get('width'), dims.get('depth'), dims.get('height')
        if not all(isinstance(v, (int, float)) for v in (w, dp, h)):
            continue
        if fname in listed or os.path.splitext(f)[0] == stem:
            return [w, dp, h]
        best = best or [w, dp, h]
    return best


def gather(only=None, force=False):
    jobs = []
    for root, dirs, files in os.walk(ASSETS):
        rel = os.path.relpath(root, ASSETS).replace('\\', '/')
        parts = rel.split('/')
        if any(p in SKIP_DIRS for p in parts):
            continue
        if only and parts[0] not in only:
            continue
        names = {f.lower() for f in files}
        for f in sorted(files):
            stem, ext = os.path.splitext(f)
            if ext.lower() not in ('.fbx', '.obj'):
                continue
            out = os.path.join(root, stem + '.glb')
            if not force and os.path.isfile(out):
                continue
            # A folder holding both <stem>.fbx and <stem>.obj: prefer the FBX, skip the OBJ twin.
            if ext.lower() == '.obj' and (stem + '.fbx').lower() in names:
                continue
            jobs.append({'src': os.path.join(root, f), 'out': out, 'dims': manifest_dims(os.path.join(root, f))})
    return jobs


def run(jobs):
    work = os.path.join(ROOT, 'tools', '.glb_work')
    os.makedirs(work, exist_ok=True)
    done = ok = skipped = err = 0
    for i in range(0, len(jobs), BATCH):
        chunk = jobs[i:i + BATCH]
        jp = os.path.join(work, 'jobs.json')
        rp = os.path.join(work, 'results.json')
        json.dump(chunk, open(jp, 'w', encoding='utf-8'))
        if os.path.exists(rp):
            os.remove(rp)
        subprocess.run([BLENDER, '-b', '--python', os.path.join(ROOT, 'tools', 'blender_to_glb.py'), '--', jp, rp],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3600)
        results = json.load(open(rp, encoding='utf-8')) if os.path.exists(rp) else [
            {'src': j['src'], 'status': 'error', 'reason': 'blender produced no results'} for j in chunk]
        with open(LOG, 'a', encoding='utf-8') as log:
            for r in results:
                log.write(json.dumps(r) + '\n')
                done += 1
                ok += r['status'] == 'ok'
                skipped += r['status'] == 'skipped'
                err += r['status'] == 'error'
        print(f'{done}/{len(jobs)}  ok={ok} skipped={skipped} error={err}', flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--only', nargs='*')
    a = ap.parse_args()
    jobs = gather(set(a.only) if a.only else None, a.force)
    print(f'{len(jobs)} model(s) to convert')
    if a.list:
        for j in jobs[:40]:
            print(' ', os.path.relpath(j['src'], ASSETS), j['dims'])
        sys.exit(0)
    if a.run or a.only:
        run(jobs)
