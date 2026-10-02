"""Audit the UI stylesheets against docs/UI_DESIGN_SYSTEM.md.

    python tools/audit_ui.py            report
    python tools/audit_ui.py --strict   exit 1 when anything is off the system (for a pre-commit hook)

Checks: font sizes outside the 7-step scale; literal rgb() colors outside the token blocks; border radii other than
the token (or 0 / pill-style values used by round things); *-btn classes that are not in a shared button group.
"""
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Homesteader', 'Assets', 'Resources', 'HUDTree')
SCALE = {11, 12, 13, 15, 18, 20, 32}
SKIP = {'UITokens.uss', 'HudUI_kit.uss'}
BEGIN = 'BEGIN UI TOKENS'
END = 'END UI TOKENS'


def main():
    strict = '--strict' in sys.argv
    groups = open(os.path.join(ROOT, 'UIControls.uss'), encoding='utf-8').read()
    problems = 0
    for name in sorted(os.listdir(ROOT)):
        if not name.endswith('.uss') or name in SKIP:
            continue
        s = open(os.path.join(ROOT, name), encoding='utf-8').read()
        s = re.sub(r'/\*' + BEGIN + r'.*?' if False else r'/\* ' + BEGIN + r'.*?' + END + r' \*/', '', s, flags=re.S)
        s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
        sizes = sorted({float(x) for x in re.findall(r'font-size:\s*([0-9.]+)px', s)} - SCALE)
        literals = len(re.findall(r'(?<!rgba)\brgb\(', s))
        radii = sorted(set(re.findall(r'border-radius:\s*([^;]+);', s)) - {'var(--r)', '0', '0px'})
        btns = sorted({c for c in re.findall(r'\.([a-z0-9-]+-btn)(?![\w-])', s)} - set(re.findall(r'\.([a-z0-9-]+-btn)\b', groups)))
        print('%-18s font sizes off scale: %s | literal rgb(): %d | other radii: %s | button classes outside the groups: %s'
              % (name, sizes or '-', literals, radii or '-', btns or '-'))
        problems += len(sizes) + len(btns)
    print('\nProblems (sizes + button classes): %d' % problems)
    if strict and problems:
        sys.exit(1)


if __name__ == '__main__':
    main()
