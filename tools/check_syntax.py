#!/usr/bin/env python3
"""Syntax gate for the Homesteader tools tree.

Why this exists
---------------
Editing a file that contains triple-quoted docstrings is the single most
common way this repo breaks: the delimiters collapse from three quotes to
two, the file still *looks* fine, and nothing notices until the server
refuses to start several steps later. This script catches that in one
second, with a file path and a line number, instead of a stack trace.

Usage
-----
    python tools/check_syntax.py                  # check the default tree
    python tools/check_syntax.py path [path ...]  # check specific files/dirs
    python tools/check_syntax.py --staged         # only files staged in git

Exit codes: 0 = all clean, 1 = at least one file failed to parse,
2 = a path could not be read.

Standard library only, so it runs under any Python 3 on this machine.
"""

import ast
import os
import subprocess
import sys
import warnings

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directories that are never worth parsing. Kept deliberately short - the
# point of the gate is coverage, so we only skip things that are certainly
# not hand-written source.
SKIP_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "env", "node_modules",
    "Library", "Temp", "obj", "Build", "build", "dist", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "packages", "Logs", "UserSettings",
    "models_legacy",
    # Throwaway diagnostic one-liners. They are never imported and never run
    # as part of the build, so gating them would only add noise. The gate is
    # for code that actually has to execute.
    "scratch",
}

BOM_FIX_HINT = (
    "re-save them as UTF-8 without a BOM; Python 3 will not run a script "
    "whose first byte is a BOM"
)


def _discover_python_files(root):
    """Yield every .py file under root, skipping SKIP_DIRS."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(".py"):
                yield os.path.join(dirpath, name)


def _expand_targets(targets):
    """Turn a mix of files and directories into a flat list of .py files."""
    files = []
    for target in targets:
        target = os.path.abspath(target)
        if os.path.isdir(target):
            files.extend(sorted(_discover_python_files(target)))
        elif os.path.isfile(target):
            if target.endswith(".py"):
                files.append(target)
        else:
            print("check_syntax: no such path: %s" % target, file=sys.stderr)
            sys.exit(2)
    return files


def _staged_python_files():
    """Return .py files currently staged in git.

    Used by the pre-commit hook so the gate only ever has to look at what is
    about to be committed, which keeps large commits fast.
    """
    try:
        out = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        print("check_syntax: could not ask git for staged files: %s" % exc,
              file=sys.stderr)
        return None
    result = []
    for rel in out.splitlines():
        rel = rel.strip()
        if not rel.endswith(".py"):
            continue
        full = os.path.join(REPO_ROOT, rel)
        if os.path.isfile(full):
            result.append(full)
    return result


def _describe_failure(path, exc):
    """Format a SyntaxError as 'path:line:col: message' plus a source line."""
    rel = os.path.relpath(path, REPO_ROOT)
    message = getattr(exc, "msg", None) or str(exc)
    lineno = getattr(exc, "lineno", None)
    offset = getattr(exc, "offset", None)

    location = rel
    if lineno is not None:
        location += ":%d" % lineno
        if offset is not None:
            location += ":%d" % offset

    lines = ["%s: %s" % (location, message)]

    # Quote the offending line and point at the column. For the collapsed
    # docstring case this makes the bug obvious at a glance, which is the
    # whole reason the gate exists.
    source_line = getattr(exc, "text", None)
    if source_line is None and lineno is not None:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                source_line = f.readlines()[lineno - 1]
        except (OSError, IndexError):
            source_line = None

    if source_line is not None:
        # Strip a UTF-8 BOM and any other non-printable characters before
        # echoing the line: some scratch files have a BOM inside them, and a
        # raw U+FEFF crashes the Windows console encoder mid-report.
        stripped = source_line.rstrip("\r\n").replace("\ufeff", "")
        stripped = "".join(ch if ch.isprintable() or ch == "\t" else "?"
                           for ch in stripped)
        lines.append("    %s" % stripped.rstrip())
        if offset:
            caret_pad = (" " * 4) + (" " * max(0, offset - 1))
            lines.append("%s^" % caret_pad)

    # A nudge toward the actual cause when it is the classic one.
    if source_line is not None:
        body = source_line.rstrip("\r\n")
        collapsed_open = body.lstrip().startswith('""') and not body.lstrip().startswith('"""')
        collapsed_close = body.rstrip().endswith('""') and not body.rstrip().endswith('"""')
        if collapsed_open or collapsed_close:
            lines.append("    hint: a triple-quoted delimiter looks collapsed "
                         "to two quotes here")
    return "\n".join(lines)


def _safe_print(text, stream=None):
    # Print without ever dying on an unencodable character.
    # The Windows console defaults to cp1252, so echoing a source line that
    # contains something outside that range would raise UnicodeEncodeError
    # and replace a useful report with a traceback - which is exactly the
    # kind of failure this script is meant to eliminate.
    stream = stream or sys.stdout
    try:
        print(text, file=stream)
    except UnicodeEncodeError:
        encoding = getattr(stream, "encoding", None) or "ascii"
        safe = text.encode(encoding, errors="replace").decode(
            encoding, errors="replace")
        print(safe, file=stream)


def check(files):
    """Parse each file; print a report. Returns the number of failures."""
    if not files:
        print("check_syntax: nothing to check")
        return 0

    failures = 0
    bom_failures = 0
    for path in files:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()
        except OSError as exc:
            print("check_syntax: cannot read %s: %s" % (path, exc), file=sys.stderr)
            failures += 1
            continue

        try:
            # Escape-sequence notices (e.g. a docstring containing \H) are
            # warnings, not parse failures, and would otherwise spam the
            # report for files that are perfectly valid.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ast.parse(source, filename=path)
        except SyntaxError as exc:
            # A file carrying a UTF-8 BOM cannot be run as a script at all on
            # Python 3 ("invalid non-printable character U+FEFF"). Report it,
            # but as a warning: it only matters for files the hook sees, and
            # the hook is what turns this into a blocking failure.
            bom = source.startswith("\ufeff")
            message = _describe_failure(path, exc)
            if bom:
                _safe_print("WARN %s\n    fix: re-save the file as UTF-8 "
                            "without a BOM" % message)
                bom_failures += 1
            else:
                failures += 1
                _safe_print("FAIL %s" % message)
        except ValueError as exc:
            # e.g. null bytes in source - still a real problem worth reporting
            failures += 1
            _safe_print("FAIL %s: %s" % (os.path.relpath(path, REPO_ROOT), exc))

    checked = len(files)
    if failures:
        _safe_print("\ncheck_syntax: %d of %d file(s) failed to parse"
                    % (failures, checked))
    if bom_failures:
        _safe_print("check_syntax: %d file(s) have a UTF-8 BOM (%s)"
                    % (bom_failures, BOM_FIX_HINT))
    if not failures and not bom_failures:
        print("check_syntax: %d file(s) OK" % checked)

    # Only real parse errors fail the gate. BOM files are reported but do not
    # block a commit, so an unrelated pre-existing file cannot stop work.
    return failures


def main(argv):
    args = argv[1:]

    if args and args[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0

    if args and args[0] == "--staged":
        staged = _staged_python_files()
        if staged is None:
            # Not a git checkout, or git is unavailable. Fall back to the
            # full tree rather than silently passing - a gate that passes
            # when it cannot see anything is worse than no gate.
            print("check_syntax: --staged unavailable, checking full tree",
                  file=sys.stderr)
            staged = _expand_targets([REPO_ROOT])
        return 1 if check(staged) else 0

    targets = args if args else [REPO_ROOT]
    return 1 if check(_expand_targets(targets)) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
