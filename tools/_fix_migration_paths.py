#!/usr/bin/env python3
"""One-shot migration repair: retarget path anchors left over from HUD/scripts/.

The scripts moved from HUD/scripts/ to tools/. Both directories sit one level
below the repo root, so the correct anchor is unchanged - but two idioms in the
old code encode the FOLDER NAME or the OLD DEPTH, and both now resolve wrong.

Idiom A (folder-name guard): the ternary checked whether the script's own
folder was literally named "scripts"; now it is "tools", so the guard is False
and BASE_DIR collapses to tools/ itself.

Idiom B (two levels up): "..", ".." reached the repo root from HUD/scripts/,
but from tools/ it overshoots to Desktop/.

This script rewrites both to the single correct form. Idempotent.
"""
import glob
import os
import re

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))

CHR_SCRIPTS = "chr(115)+chr(99)+chr(114)+chr(105)+chr(112)+chr(116)+chr(115)"

# Idiom A -> one level up from tools/ is the repo root.
NEW_A = 'os.path.dirname(_this_dir)  # tools/ sits at the repo root (one level up)'

PATTERN_A = re.compile(
    r'os\.path\.dirname\(_this_dir\) if os\.path\.basename\(_this_dir\) == '
    r'(?:' + re.escape(CHR_SCRIPTS) + r'|"scripts"|\'scripts\') else _this_dir'
)

# Idiom B -> also one level up, not two.
NEW_B = 'os.path.abspath(os.path.join(SCRIPT_DIR, ".."))'
PATTERN_B = re.compile(
    r'os\.path\.abspath\(os\.path\.join\(SCRIPT_DIR,\s*"\.\.",\s*"\.\."\)\)'
)


def main():
    changed = []
    for path in sorted(glob.glob(os.path.join(TOOLS_DIR, "*.py"))):
        if os.path.basename(path) == os.path.basename(__file__):
            continue
        with open(path, "r", encoding="utf-8") as f:
            original = f.read()
        text = original
        tags = []

        new_text, n_a = PATTERN_A.subn(NEW_A, text)
        if n_a:
            text = new_text
            tags.append(f"A x{n_a}")

        new_text, n_b = PATTERN_B.subn(NEW_B, text)
        if n_b:
            text = new_text
            tags.append(f"B x{n_b}")

        if text != original:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(text)
            changed.append((os.path.basename(path), ", ".join(tags)))

    if not changed:
        print("No leftover migration path idioms found - nothing to do.")
        return
    print(f"Repaired {len(changed)} file(s):")
    for name, tag in changed:
        print(f"  {name:42s} {tag}")


if __name__ == "__main__":
    main()
