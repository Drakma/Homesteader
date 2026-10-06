#!/usr/bin/env python3
"""
Carries the asset kit's changes into the game: regenerates Assets/Resources/AssetCatalog.json and the packaged mod (Homesteader/mods/homesteader), and
brings the icon copies in Assets/Resources/Icons up to date (the game loads an icon from there FIRST, so a stale copy hid every re-rendered icon).
The kit server starts this in the background after a rename so the game follows (each step is retried: Unity can hold a file open for a moment).

    python tools/refresh_game_content.py
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def run(script):
    for attempt in range(4):
        r = subprocess.run([sys.executable, os.path.join(HERE, script)], capture_output=True, text=True)
        if r.returncode == 0 and 'Error' not in r.stdout[-400:] and 'Errno' not in (r.stdout + r.stderr):
            print('ok', script)
            return True
        time.sleep(2.5)
    print('FAILED', script, (r.stdout + r.stderr)[-300:])
    return False


def sync_icons():
    """Every icon already copied into Assets/Resources/Icons is replaced by the kit's current one when they differ (by content). Its .meta is kept."""
    import glob
    import hashlib
    import shutil
    root = os.path.dirname(HERE)
    res = os.path.join(root, 'Homesteader', 'Assets', 'Resources', 'Icons')
    if not os.path.isdir(res):
        return
    kit = {}
    for p in glob.glob(os.path.join(root, 'assets', '*', '*', '*.png')) + glob.glob(os.path.join(root, 'assets', '*', '*', 'stages', '*', '*.png')):
        kit.setdefault(os.path.basename(p), p)
    md5 = lambda p: hashlib.md5(open(p, 'rb').read()).hexdigest()
    n = 0
    for f in os.listdir(res):
        src = kit.get(f)
        if not f.endswith('.png') or src is None:
            continue
        dst = os.path.join(res, f)
        if md5(src) != md5(dst):
            for _ in range(5):
                try:
                    shutil.copyfile(src, dst)
                    n += 1
                    break
                except OSError:
                    time.sleep(0.5)
    print('ok icons (%d updated)' % n)


if __name__ == '__main__':
    ok = run('generate_unity_asset_catalog.py') and run('package_catalog_as_mods.py')
    sync_icons()
    sys.exit(0 if ok else 1)
