"""Audit what characters live in the HUD runtime / UXML / Python source
so we know what the kit font actually needs to cover."""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PROJECT = r"C:\Users\casey\Desktop\Homesteader"

# 1. UXML/USS file literal strings.
import glob
uxml_files = glob.glob(os.path.join(PROJECT, "Homesteader", "Assets", "**", "*.uxml"), recursive=True)
uss_files  = glob.glob(os.path.join(PROJECT, "Homesteader", "Assets", "**", "*.uss"),  recursive=True)

literal_text_pattern = re.compile(r'text\s*=\s*"([^"]+)"')
uxml_chars = set()
for p in uxml_files:
    try:
        text = open(p, "r", encoding="utf-8").read()
    except Exception:
        continue
    for line in text.splitlines():
        m = literal_text_pattern.search(line)
        if m:
            for c in m.group(1):
                uxml_chars.add(c)

# 2. Python source strings we render to labels.
py_files = [
    r"C:\Users\casey\Desktop\Homesteader\assets\hud_kit\runtime\state.py",
    r"C:\Users\casey\Desktop\Homesteader\assets\hud_kit\runtime\time_system.py",
    r"C:\Users\casey\Desktop\Homesteader\assets\hud_kit\runtime\render.py",
    r"C:\Users\casey\Desktop\Homesteader\assets\hud_kit\runtime\grid_layout.py",
]
py_chars = set()
for p in py_files:
    if not os.path.isfile(p):
        continue
    text = open(p, "r", encoding="utf-8").read()
    for c in text:
        if c.isprintable() and c not in ("\r", "\n", "\t"):
            py_chars.add(c)

# 3. Order catalog: tooltips, item names, etc.
catalog_files = glob.glob(os.path.join(PROJECT, "assets", "**", "*.json"), recursive=True)
cat_chars = set()
for p in catalog_files:
    try:
        data = open(p, "r", encoding="utf-8").read()
    except Exception:
        continue
    for c in data:
        if c.isprintable() and c not in ("\r", "\n", "\t"):
            cat_chars.add(c)

print("UXML literal text chars (" + str(len(uxml_chars)) + "):")
for c in sorted(uxml_chars):
    print("  " + repr(c))

# 4. Compare against current coverage.
from fontTools.ttLib import TTFont
ttf = r"C:\Users\casey\Desktop\Homesteader\assets\hud_kit\font\homesteader_hud.ttf"
cm = TTFont(ttf).getBestCmap()
have = set(chr(c) for c in cm)

# What about the kit changelog, settings, release-notes etc.
extra_pattern = re.compile(r'[ -~]')
uxml_chars_full = uxml_chars | py_chars | cat_chars
print()
print("Combined chars across UXML/Python/JSONs: " + str(len(uxml_chars_full)))
missing = sorted(c for c in uxml_chars_full if c not in have and c.isprintable())
print("Missing from current font: " + str(len(missing)))
for c in missing:
    print("  " + repr(c))
