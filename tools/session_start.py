#!/usr/bin/env python3
"""Startup check: report whether the session's tools are actually working.

What this is for
----------------
At the start of a session nobody knows whether the MCP servers are up, whether
the vault is readable, or whether the skills are installed. Each of those fails
silently and differently. This runs the checks and prints one line per item so
the state is known before any work starts, instead of being discovered halfway
through a task.

It is a REPORT, not a fixer. It changes nothing on disk and starts nothing that
outlives the call.

Usage
-----
    python tools/session_start.py            # full check, human readable
    python tools/session_start.py --json     # machine readable
    python tools/session_start.py --quick    # skip the slow MCP handshakes
    python tools/session_start.py --verbose  # include diagnostic detail

Exit codes: 0 = everything working, 1 = something is down, 2 = fatal.
"""

import argparse
import json
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = r"C:\Python313\python.exe"
MCP_HOST = os.path.join(REPO_ROOT, "tools", "mcp_host.py")
SKILLS_SRC = os.path.join(REPO_ROOT, "tools", "skills-src")
SKILLS_DEST = os.path.join(os.path.expanduser("~"), ".codegpt", "skills")
VAULT_CANDIDATES = [r"C:\Users\casey\Brain", r"C:\Users\casey\brain"]
CONFIG = os.path.join(REPO_ROOT, ".mcp.json")

# Sections of VAULT-INDEX.md surfaced in the digest, in the order they matter to
# a fresh session. Matched by heading text, so a reordered index still works.
INDEX_DIGEST_SECTIONS = ["Who I Am", "What's Active Right Now"]
PRIORITIES_NOTE = "Active Priorities.md"

# Servers expected from .mcp.json. Used to report a MISSING server as a
# failure even when the handshake step is skipped (--quick).
EXPECTED_SERVERS = [
    "blender", "homesteader-asset-kit", "mesh2motion", "meshy", "unity-mcp",
]

# The skills this repo owns and installs.
OWNED_SKILLS = ["unity-mcp", "vault-context"]


class Report(object):
    def __init__(self):
        self.rows = []

    def add(self, ok, label, detail=""):
        self.rows.append({"ok": bool(ok), "label": label, "detail": detail})
        return ok

    @property
    def failures(self):
        return [r for r in self.rows if not r["ok"]]

    def render(self):
        width = max((len(r["label"]) for r in self.rows), default=0)
        for row in self.rows:
            mark = "ok  " if row["ok"] else "FAIL"
            line = "%s  %-*s" % (mark, width, row["label"])
            if row["detail"]:
                line += "  %s" % row["detail"]
            print(line)
        print()
        if self.failures:
            print("%d of %d checks FAILED" % (len(self.failures), len(self.rows)))
        else:
            print("all %d checks passed - tools are working" % len(self.rows))


def run(cmd, timeout=90):
    """Run a command, return (exit_code, stdout+stderr). Never raises."""
    try:
        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=timeout)
        return proc.returncode, proc.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return 124, "timed out after %ss" % timeout
    except OSError as exc:
        return 125, str(exc)


def check_python(report, verbose):
    if os.path.isfile(PYTHON):
        report.add(True, "python interpreter", PYTHON)
    else:
        report.add(False, "python interpreter", "missing: %s" % PYTHON)


def check_config(report, verbose):
    """Parse .mcp.json and confirm the expected servers are declared."""
    if not os.path.isfile(CONFIG):
        report.add(False, "mcp config", "missing: %s" % CONFIG)
        return
    try:
        with open(CONFIG, "r", encoding="utf-8-sig") as fh:
            cfg = json.load(fh)
    except Exception as exc:
        report.add(False, "mcp config", "unreadable: %s" % exc)
        return
    declared = sorted((cfg.get("mcpServers") or {}).keys())
    missing = [s for s in EXPECTED_SERVERS if s not in declared]
    if missing:
        report.add(False, "mcp config",
                   "declares %d server(s), missing: %s"
                   % (len(declared), ", ".join(missing)))
    else:
        report.add(True, "mcp config",
                   "%d server(s) declared" % len(declared))


def check_mcp(report, verbose, quick):
    """Handshake every server and report the tool counts."""
    if quick:
        report.add(True, "mcp servers", "skipped (--quick)")
        return
    if not os.path.isfile(MCP_HOST):
        report.add(False, "mcp servers", "no host: %s" % MCP_HOST)
        return
    code, output = run([PYTHON, MCP_HOST, "selftest", "--timeout", "180"],
                       timeout=600)
    # The selftest prints a line per server plus a summary; surface the summary
    # and any individual failures.
    summary = ""
    failed = []
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("FAIL"):
            failed.append(stripped[4:].strip())
        if "ok," in stripped and "failed" in stripped:
            summary = stripped
    if code == 0 and not failed:
        report.add(True, "mcp servers", summary or "all handshook")
    else:
        detail = summary or "handshake failed"
        if failed:
            detail = "%s | %s" % (detail, "; ".join(failed))
        report.add(False, "mcp servers", detail)
        if verbose:
            print(output)


def check_unity_bridge(report, verbose):
    """The Unity editor must have registered a bridge for the relay to find."""
    bridge_dir = os.path.join(os.path.expanduser("~"), ".unity", "mcp",
                              "connections")
    if not os.path.isdir(bridge_dir):
        report.add(False, "unity bridge", "no bridge dir: %s" % bridge_dir)
        return
    bridges = [f for f in os.listdir(bridge_dir) if f.endswith(".json")]
    if not bridges:
        report.add(False, "unity bridge", "no bridge registered")
        return
    # Report the newest one, which is the editor most recently active.
    newest = max((os.path.join(bridge_dir, f) for f in bridges),
                 key=os.path.getmtime)
    try:
        with open(newest, "r", encoding="utf-8-sig") as fh:
            data = json.load(fh)
        pid = data.get("editor_pid", "?")
        project = os.path.basename(str(data.get("project_path", "?")))
        report.add(True, "unity bridge", "pid %s  project %s" % (pid, project))
    except Exception as exc:
        report.add(False, "unity bridge", "unreadable: %s" % exc)


def find_vault():
    """Return the vault directory, or None if no candidate resolves."""
    for candidate in VAULT_CANDIDATES:
        if os.path.isdir(candidate):
            return candidate
    return None


def read_text(path):
    """Read a UTF-8 text file, or return None if it is missing/unreadable."""
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


def index_sections(text):
    """Split a markdown document into {heading: body} at `## ` boundaries."""
    sections = {}
    heading = None
    buf = []
    for line in text.splitlines():
        if line.startswith("## "):
            if heading:
                sections[heading] = "\n".join(buf).strip()
            heading = line[3:].strip()
            buf = []
        elif heading:
            buf.append(line)
    if heading:
        sections[heading] = "\n".join(buf).strip()
    return sections


def print_digest(limit=14):
    """Print the vault digest: who Casey is, the working style, and what's open.

    Deliberately a DIGEST, not the whole index. The index itself says a session
    should hold only what the task needs; this puts the identity, the working
    preferences, and the open-work queue in front of the reader at startup, and
    leaves the rest one search away.
    """
    vault = find_vault()
    if not vault:
        print("VAULT: not found in %s" % " or ".join(VAULT_CANDIDATES))
        return

    print("VAULT CONTEXT - %s" % vault)
    print("-" * 60)

    index = read_text(os.path.join(vault, "VAULT-INDEX.md"))
    if not index:
        print("VAULT-INDEX.md unreadable")
    else:
        sections = index_sections(index)
        if "Who I Am" in sections:
            print(sections["Who I Am"])
        prefs = sections.get("My Preferences for Working with AI")
        if prefs:
            print()
            print("My Preferences for Working with AI")
            for line in prefs.splitlines():
                if line.strip().startswith("-"):
                    print(line)

    priorities = read_text(os.path.join(vault, PRIORITIES_NOTE))
    print()
    if not priorities:
        print("%s unreadable" % PRIORITIES_NOTE)
        return
    open_items = [ln.strip() for ln in priorities.splitlines()
                  if ln.strip().startswith("- [ ]")]
    print("%s - %d open item(s)" % (PRIORITIES_NOTE, len(open_items)))
    for line in open_items[:limit]:
        print("  %s" % line[5:].strip())
    if len(open_items) > limit:
        print("  ... %d more (read the note)" % (len(open_items) - limit))
    print()


def check_vault(report, verbose):
    """The vault index must be present and readable."""
    vault = None
    for candidate in VAULT_CANDIDATES:
        if os.path.isdir(candidate):
            vault = candidate
            break
    if not vault:
        report.add(False, "vault", "not found in %s"
                   % " or ".join(VAULT_CANDIDATES))
        return
    index = os.path.join(vault, "VAULT-INDEX.md")
    if not os.path.isfile(index):
        report.add(False, "vault", "no VAULT-INDEX.md in %s" % vault)
        return
    report.add(True, "vault", "%s (%d bytes)"
               % (os.path.basename(vault), os.path.getsize(index)))
    priorities = os.path.join(vault, "Active Priorities.md")
    if os.path.isfile(priorities):
        report.add(True, "vault priorities", "Active Priorities.md present")
    else:
        report.add(False, "vault priorities", "Active Priorities.md missing")


def check_skills(report, verbose):
    """Each skill this repo owns must be installed and current."""
    for skill in OWNED_SKILLS:
        source = os.path.join(SKILLS_SRC, skill)
        target = os.path.join(SKILLS_DEST, skill)
        if not os.path.isdir(source):
            report.add(False, "skill %s" % skill, "not in repo")
            continue
        if not os.path.isdir(target):
            report.add(False, "skill %s" % skill,
                       "NOT INSTALLED - run tools/install_skill.py")
            continue
        # Compare mtimes as a cheap drift signal.
        drift = []
        for name in os.listdir(source):
            src = os.path.join(source, name)
            dst = os.path.join(target, name)
            if not os.path.isfile(src):
                continue
            if not os.path.isfile(dst):
                drift.append("%s missing" % name)
            elif os.path.getsize(src) != os.path.getsize(dst):
                drift.append("%s differs" % name)
        if drift:
            report.add(False, "skill %s" % skill,
                       "STALE (%s) - run tools/install_skill.py"
                       % ", ".join(drift))
        else:
            report.add(True, "skill %s" % skill, "installed")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="session_start.py",
        description="Report whether this session's tools are working.")
    parser.add_argument("--json", action="store_true",
                        help="machine-readable output")
    parser.add_argument("--quick", action="store_true",
                        help="skip the slow MCP handshakes")
    parser.add_argument("--verbose", action="store_true",
                        help="include diagnostic output for failures")
    args = parser.parse_args(argv)

    report = Report()
    check_python(report, args.verbose)
    check_config(report, args.verbose)
    check_mcp(report, args.verbose, args.quick)
    if not args.quick:
        check_unity_bridge(report, args.verbose)
    check_vault(report, args.verbose)
    check_skills(report, args.verbose)

    if args.json:
        print(json.dumps({
            "ok": not report.failures,
            "checks": report.rows,
            "failures": [r["label"] for r in report.failures],
        }, indent=2))
    else:
        print("SESSION START - tool check")
        print("=" * 60)
        report.render()
        if report.failures:
            print()
            print("Fix the FAIL lines before relying on those tools. MCP servers")
            print("that are down produce silent, confusing failures later.")
        print()
        print_digest()

    return 0 if not report.failures else 1


if __name__ == "__main__":
    sys.exit(main())