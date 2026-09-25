#!/usr/bin/env python3
"""Thin wrapper the unity-mcp skill calls.

This exists so the SKILL.md commands are short and stable: the skill knows only
`mcp_call.py <verb> ...`, and everything about *where* the real host lives and
which interpreter runs it is resolved here, in one place.

The real implementation is tools/mcp_host.py in the Homesteader repo. This
wrapper finds it by searching outward from its own location, so the skill folder
can be copied to ~/.codegpt/skills/unity-mcp (or anywhere) without editing.

Usage is identical to mcp_host.py, with two aliases the skill uses:
    doctor  -> selftest
    tools   -> list
"""

import os
import runpy
import subprocess
import sys

# The repo root that holds tools/mcp_host.py, relative to a candidate start dir.
HOST_RELPATH = os.path.join("tools", "mcp_host.py")

# Candidate roots, tried in order. The first is the workspace the project
# actually lives in; the rest cover the skill being copied somewhere else
# (e.g. ~/.codegpt/skills/unity-mcp) from which we walk upward.
EXPLICIT_ROOTS = [
    r"C:\Users\casey\Desktop\Homesteader",
    os.path.expanduser("~"),
]

ALIASES = {"doctor": "selftest", "tools": "list"}


def find_host():
    """Return the path to mcp_host.py, or None.

    Search order is deliberate: an explicit project root first (cheap and
    correct on this machine), then walk up from this file, then a repo-root
    environment variable, so a checkout in a new location still works.
    """
    # 1. Explicit known roots.
    for root in EXPLICIT_ROOTS:
        candidate = os.path.join(root, HOST_RELPATH)
        if os.path.isfile(candidate):
            return candidate

    # 2. Walk up from this file. A copied skill lives at
    #    <something>/skills/unity-mcp/mcp_call.py, so the repo is several
    #    levels up at most; cap the walk so we never scan a whole drive.
    here = os.path.dirname(os.path.abspath(__file__))
    current = here
    for _ in range(6):
        candidate = os.path.join(current, HOST_RELPATH)
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    # 3. An explicit override, for a checkout somewhere unusual.
    override = os.environ.get("HOMESTEADER_ROOT")
    if override:
        candidate = os.path.join(override, HOST_RELPATH)
        if os.path.isfile(candidate):
            return candidate

    return None


def main():
    host = find_host()
    if not host:
        sys.stderr.write(
            "mcp_call.py: could not find %s.\n"
            "Looked in:\n" % HOST_RELPATH
            + "".join("  %s\n" % os.path.join(r, HOST_RELPATH)
                      for r in EXPLICIT_ROOTS)
            + "  ...and up to 6 parent directories of %s\n"
              % os.path.dirname(os.path.abspath(__file__))
            + "Set HOMESTEADER_ROOT to the checkout root to override.\n"
        )
        return 2

    argv = list(sys.argv[1:])
    # Translate the skill-facing aliases to the real verbs. Only the first
    # positional is a verb; flags may precede it.
    for index, token in enumerate(argv):
        if not token.startswith("-"):
            if token in ALIASES:
                argv[index] = ALIASES[token]
            break

    # Default to `selftest` when called with nothing, because the single most
    # common question is "is this working at all?" and an empty invocation
    # answering that is more useful than an argparse usage error.
    if not argv:
        argv = ["selftest"]

    # Run the host in-process rather than as a subprocess: same interpreter,
    # no extra process, and the child servers inherit this environment. The
    # host reads sys.argv, so patch it for the duration of the run.
    saved_argv = sys.argv
    sys.argv = [host] + argv
    try:
        runpy.run_path(host, run_name="__main__")
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    finally:
        sys.argv = saved_argv
    return 0


if __name__ == "__main__":
    sys.exit(main())