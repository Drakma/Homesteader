#!/usr/bin/env python3
"""Install the unity-mcp skill into ~/.codegpt/skills/.

Why this script exists
---------------------
The skill has to live at ~/.codegpt/skills/unity-mcp/ for an agent session to
load it at startup - that directory is the only place skills are read from.
But that path is OUTSIDE the Homesteader workspace, so an agent editing files
with workspace-scoped tools cannot write there (it gets PATH_OUTSIDE_WORKSPACE,
or a 403 from the host's file service). The skill source therefore lives in the
repo at tools/skills-src/unity-mcp/, and this script performs the copy.

Run it after changing anything in tools/skills-src/unity-mcp/.

Usage
-----
    python tools/install_skill.py            # install / update
    python tools/install_skill.py --check    # report drift, change nothing
    python tools/install_skill.py --uninstall

Exit codes: 0 = ok, 1 = drift found (with --check) or a write failed, 2 = usage.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_SRC = os.path.join(REPO_ROOT, "tools", "skills-src")
TARGET_ROOT = os.path.join(os.path.expanduser("~"), ".codegpt", "skills")

# Every skill this repo owns, with the files that ship for each. SKILL.md is
# the frontmatter + instructions the agent reads; the rest are the scripts it
# invokes. Keeping this a table rather than a single hardcoded skill means
# adding a skill is one line here, not a rewrite.
SKILLS = {
    "unity-mcp": ["SKILL.md", "mcp_call.py"],
    "vault-context": ["SKILL.md", "read_vault.py"],
}

# Retained for the single-skill code paths below.
SOURCE_DIR = os.path.join(SKILLS_SRC, "unity-mcp")
TARGET_DIR = os.path.join(TARGET_ROOT, "unity-mcp")
SHIPPED = SKILLS["unity-mcp"]

# The seed manifest other skills carry: name -> a short content hash. Written
# for consistency with browser-automation and game-development so this skill
# does not look structurally different from the ones that already work.
SEED_NAME = ".codegpt-seed.json"


def digest(path):
    """Short content hash, matching the shape of the existing seed files."""
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def build_seed(source_dir, shipped):
    files = {}
    for name in shipped:
        source = os.path.join(source_dir, name)
        if os.path.isfile(source):
            files[name] = digest(source)
    return {"files": files}


def status(source_dir, target_dir, shipped):
    """Return a list of (file, state) describing source vs installed."""
    rows = []
    for name in shipped:
        source = os.path.join(source_dir, name)
        target = os.path.join(target_dir, name)
        if not os.path.isfile(source):
            rows.append((name, "MISSING IN SOURCE"))
        elif not os.path.isfile(target):
            rows.append((name, "not installed"))
        elif digest(source) != digest(target):
            rows.append((name, "differs"))
        else:
            rows.append((name, "up to date"))
    return rows


def install_one(skill, verbose=True):
    """Install one skill. Returns 0 on success, 1 or 2 on failure."""
    shipped = SKILLS[skill]
    source_dir = os.path.join(SKILLS_SRC, skill)
    target_dir = os.path.join(TARGET_ROOT, skill)
    if not os.path.isdir(source_dir):
        sys.stderr.write("source not found: %s\n" % source_dir)
        return 2
    try:
        os.makedirs(target_dir, exist_ok=True)
    except OSError as exc:
        sys.stderr.write("cannot create %s: %s\n" % (target_dir, exc))
        return 1

    copied = []
    for name in shipped:
        source = os.path.join(source_dir, name)
        if not os.path.isfile(source):
            sys.stderr.write("skipping missing source file: %s\n" % name)
            continue
        shutil.copy2(source, os.path.join(target_dir, name))
        copied.append(name)

    seed_path = os.path.join(target_dir, SEED_NAME)
    with open(seed_path, "w", encoding="utf-8") as fh:
        json.dump(build_seed(source_dir, shipped), fh, indent=2)
        fh.write("\n")
    copied.append(SEED_NAME)

    if verbose:
        print("  %-16s %d file(s) -> %s" % (skill, len(copied), target_dir))
        for name in copied:
            print("      %s" % name)
    return 0


def install(skills=None, verbose=True):
    names = skills or sorted(SKILLS)
    if verbose:
        print("installing %d skill(s) to %s" % (len(names), TARGET_ROOT))
    worst = 0
    for skill in names:
        worst = max(worst, install_one(skill, verbose))
    return worst


def uninstall(skills=None):
    names = skills or sorted(SKILLS)
    removed = 0
    for skill in names:
        target_dir = os.path.join(TARGET_ROOT, skill)
        if not os.path.isdir(target_dir):
            print("nothing to remove: %s" % target_dir)
            continue
        shutil.rmtree(target_dir)
        print("removed %s" % target_dir)
        removed += 1
    return 0 if removed or names else 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="install_skill.py",
        description="Install the repo's skills into ~/.codegpt/skills/.")
    parser.add_argument("skill", nargs="?",
                        help="one skill to act on (default: all)")
    parser.add_argument("--check", action="store_true",
                        help="report drift and change nothing")
    parser.add_argument("--uninstall", action="store_true",
                        help="remove the installed skill(s)")
    parser.add_argument("--list", action="store_true",
                        help="show which skills this repo owns")
    args = parser.parse_args(argv)

    if args.list:
        print("skills-source: %s" % SKILLS_SRC)
        for name in sorted(SKILLS):
            print("  %-16s %s" % (name, ", ".join(SKILLS[name])))
        return 0

    if args.skill and args.skill not in SKILLS:
        sys.stderr.write("unknown skill: %s\nknown: %s\n"
                         % (args.skill, ", ".join(sorted(SKILLS))))
        return 2

    names = [args.skill] if args.skill else sorted(SKILLS)

    if args.uninstall:
        return uninstall(names)

    if args.check:
        drift = False
        print("target: %s" % TARGET_ROOT)
        for skill in names:
            source_dir = os.path.join(SKILLS_SRC, skill)
            target_dir = os.path.join(TARGET_ROOT, skill)
            print("\n%s" % skill)
            for name, state in status(source_dir, target_dir, SKILLS[skill]):
                flag = "ok  " if state == "up to date" else "DIFF"
                if state != "up to date":
                    drift = True
                print("  %s  %-16s %s" % (flag, name, state))
            if not os.path.isdir(target_dir):
                print("  DIFF  (skill directory does not exist)")
                drift = True
        return 1 if drift else 0

    return install(names)


if __name__ == "__main__":
    sys.exit(main())