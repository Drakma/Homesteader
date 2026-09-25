#!/usr/bin/env python3
"""
Validate a Unity .meta file the way UNITY parses it, not the way PyYAML does.

WHY THIS EXISTS
    A .meta was written with '#' comment lines. PyYAML accepted it happily, so
    the file looked fine - but Unity's YAML parser rejects comments outright:
        "Parser Failure at line 18: Expect ':' between key and value"
        "does not have a valid GUID ... will be ignored"
    PyYAML is therefore NOT a valid check for a Unity .meta. This validator
    enforces the rules Unity actually applies:

      1. No comment lines ('#' anywhere at line start, after indentation).
      2. No tab characters (Unity writes spaces only).
      3. A 'guid:' line that is exactly 32 lowercase hex characters.
      4. 'fileFormatVersion: 2' present.
      5. Indentation is a multiple of 2 spaces (Unity's convention).

USAGE
    python tools/check_unity_meta.py <file.meta> [more.meta ...]
    Exits 1 if any file fails, so it can gate a commit.
"""

from __future__ import annotations

import os
import re
import sys

GUID_RE = re.compile(r"^guid:\s*([0-9a-f]{32})\s*$")


def check(path):
    """Return (ok, [problems])."""
    problems = []

    if not os.path.isfile(path):
        return False, ["file does not exist"]

    try:
        with open(path, "r", encoding="utf-8", newline="") as fh:
            raw = fh.read()
    except Exception as exc:
        return False, ["cannot read: " + str(exc)]

    if raw.startswith("\ufeff"):
        problems.append("starts with a UTF-8 BOM (Unity may reject this)")

    lines = raw.split("\n")
    guid_found = False

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        # 1. comments - Unity's parser errors on these
        if stripped.startswith("#"):
            problems.append("line %d: comment line, Unity's YAML parser rejects these: %r"
                            % (i, stripped[:60]))

        # 2. tabs
        if "\t" in line:
            problems.append("line %d: contains a TAB character" % i)

        # 3. guid
        m = GUID_RE.match(line)
        if m:
            guid_found = True
        elif line.startswith("guid:"):
            problems.append("line %d: malformed guid (need 32 lowercase hex chars): %r"
                            % (i, line[:60]))

        # 4. fileFormatVersion
        if line.startswith("fileFormatVersion:") and line.strip() != "fileFormatVersion: 2":
            problems.append("line %d: expected 'fileFormatVersion: 2', got %r"
                            % (i, line.strip()))

        # 5. indentation multiple of 2 (skip blank lines and top-level keys)
        if stripped and not stripped.startswith("---"):
            indent = len(line) - len(line.lstrip(" "))
            if indent % 2 != 0:
                problems.append("line %d: indent %d is not a multiple of 2" % (i, indent))

    if not guid_found:
        problems.append("no valid 'guid:' line found (Unity will ignore the asset)")

    if not any(l.startswith("fileFormatVersion: 2") for l in lines):
        problems.append("missing 'fileFormatVersion: 2'")

    return (len(problems) == 0), problems


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2

    failed = 0
    for path in argv[1:]:
        ok, problems = check(path)
        print(("PASS  " if ok else "FAIL  ") + path)
        for p in problems:
            print("        " + p)
        if not ok:
            failed += 1

    if failed:
        print("\n%d file(s) would be rejected by Unity." % failed)
        return 1
    print("\nall %d file(s) valid for Unity." % (len(argv) - 1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
