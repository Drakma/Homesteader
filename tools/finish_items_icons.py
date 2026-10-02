"""Renders the icons of the finish items from their models (the icon is always rendered FROM the model).
    python tools/finish_items_icons.py
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ids = json.load(open(os.path.join(ROOT, 'tools', '_finish_items.json')))
for i in ids:
    for cat in ('building', 'materials'):
        folder = os.path.join(ROOT, 'assets', cat, i)
        glb = os.path.join(folder, i + '.glb')
        if os.path.exists(glb):
            r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'render_icon_from_model.py'), glb, os.path.join(folder, i + '.png')],
                               capture_output=True, text=True)
            print(i, 'ok' if r.returncode == 0 else 'FAILED ' + r.stderr[-200:])
            break
