"""verify_ttf_family.py - smoke-test the 5 emitted TTFs."""
import io
import os
import sys

from fontTools.ttLib import TTFont


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

KERN_SAMPLES = [
    (0x20, "space"),
    (ord(","), "comma"),
    (ord("!"), "excl"),
    (ord("?"), "question"),
    (40, "paren open"),
    (ord(")"), "paren close"),
    (ord("<"), "less"),
    (ord(">"), "greater"),
    (ord("["), "bracket open"),
    (ord("]"), "bracket close"),
    (ord("%"), "percent"),
    (ord("&"), "amp"),
    (ord("_"), "underscore"),
    (ord("="), "equal"),
    (ord("~"), "tilde"),
    (ord("\\"), "backslash"),
    (ord(";"), "semi"),
]

for fname in [
    "homesteader_hud.ttf",
    "homesteader_hud_medium.ttf",
    "homesteader_hud_bold.ttf",
    "homesteader_hud_italic.ttf",
    "homesteader_hud_bold_italic.ttf",
]:
    p = os.path.join(r"C:\Users\casey\Desktop\Homesteader\assets\hud_kit\font", fname)
    f = TTFont(p)
    cm = f.getBestCmap()
    family = f["name"].getDebugName(1)
    style = f["name"].getDebugName(2)
    weight = f["OS/2"].usWeightClass
    italic = f["OS/2"].fsSelection
    print(fname + ": " + str(len(cm)) + " codepoints, family=" +
          str(family) + ", style=" + str(style) + ", weight=" +
          str(weight))
    misses = [(cp, nm) for cp, nm in KERN_SAMPLES if cp not in cm]
    if misses:
        print("  MISSING:", misses)
    else:
        print("  all sample punctuation + space present.")
    f.close()
