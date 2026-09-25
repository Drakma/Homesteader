#!/usr/bin/env python3
"""Read Casey's vault (C:\\Users\\casey\\Brain).

The vault is his memory and it lives outside the Homesteader workspace, so a
workspace-scoped file read of it fails (403 / PATH_OUTSIDE_WORKSPACE). This
script is the way in.

The RULES live in the vault itself, in the "Vault Rules for AI" section of
VAULT-INDEX.md - there is no separate RULES.md or CLAUDE.md inside the vault.
`--rules` extracts that section verbatim so it can be followed without pulling
the whole index.

Usage
-----
    python read_vault.py                 # the whole index
    python read_vault.py --list          # headings only
    python read_vault.py --section prefs # one section, by fuzzy name
    python read_vault.py --rules         # just the AI rules section
    python read_vault.py --index-only    # path + size only (cheap check)
    python read_vault.py --priorities    # the Active Priorities note too
    python read_vault.py --tree          # folder structure

Exit codes: 0 = ok, 2 = vault or index not found.
"""

import argparse
import os
import re
import sys

# Find order is deliberate: an explicit override, then the vault's own
# capitalisation, then the lowercase spelling Casey used. Both resolve to the
# same folder on Windows, but a case-sensitive mount or a future move would
# break a single hardcoded guess.
CANDIDATE_ROOTS = [
    os.environ.get("VAULT_ROOT"),
    r"C:\Users\casey\Brain",
    r"C:\Users\casey\brain",
]

INDEX_NAME = "VAULT-INDEX.md"
PRIORITIES_NAME = "Active Priorities.md"

# Section headings we want to be able to fetch by a short alias.
SECTION_ALIASES = {
    "prefs": ("preferences", "working with ai"),
    "preferences": ("preferences", "working with ai"),
    "rules": ("vault rules",),
    "memory": ("how my memory works",),
    "active": ("active right now",),
    "who": ("who i am",),
    "people": ("key people",),
    "structure": ("vault structure",),
    "checkpoint": ("checkpoint persistence",),
}


def find_vault():
    """Return the vault root, or None."""
    for root in CANDIDATE_ROOTS:
        if root and os.path.isdir(root):
            return root
    # Last resort: walk up from this script, in case it is ever copied
    # somewhere beneath the vault.
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        if os.path.isfile(os.path.join(current, INDEX_NAME)):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def read_text(path):
    """Read a file, tolerating the BOM Obsidian sometimes leaves behind."""
    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
        return fh.read()


def split_frontmatter(text):
    """Return (frontmatter_lines, body) - frontmatter may be empty."""
    if not text.startswith("---"):
        return [], text
    lines = text.splitlines()
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        return [], text
    return lines[1:end], "\n".join(lines[end + 1:])


def parse_sections(body):
    """Return [(level, title, content), ...] for every markdown heading.

    Handles ATX headings (#, ##) which is what the vault uses. Content runs to
    the next heading of the SAME OR HIGHER level, so a ## section includes its
    ### children.
    """
    lines = body.splitlines()
    headings = []
    for index, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.*?)\s*$", line)
        if match:
            headings.append((index, len(match.group(1)), match.group(2)))
    sections = []
    for position, (line_no, level, title) in enumerate(headings):
        end = len(lines)
        for next_line, next_level, _ in headings[position + 1:]:
            if next_level <= level:
                end = next_line
                break
        content = "\n".join(lines[line_no:end]).rstrip()
        sections.append((level, title, content))
    return sections


def match_section(sections, query):
    """Fuzzy-match a section by title, returning all candidates."""
    needles = [query.lower()]
    needles.extend(SECTION_ALIASES.get(query.lower(), ()))
    hits = []
    for level, title, content in sections:
        low = title.lower()
        if any(needle in low for needle in needles):
            hits.append((level, title, content))
    return hits


def show_sections(sections, stream=sys.stdout):
    for level, title, _ in sections:
        stream.write("%s%s\n" % ("  " * max(0, level - 1), title))


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="read_vault.py",
        description="Read Casey's vault index and notes.")
    parser.add_argument("--list", action="store_true",
                        help="print section headings only")
    parser.add_argument("--section", metavar="NAME",
                        help="print one section (fuzzy match, e.g. prefs, rules)")
    parser.add_argument("--rules", action="store_true",
                        help="print the vault rules for AI")
    parser.add_argument("--priorities", action="store_true",
                        help="also print Active Priorities.md")
    parser.add_argument("--tree", action="store_true",
                        help="print the vault folder structure")
    parser.add_argument("--index-only", action="store_true",
                        help="print the index path and size, nothing else")
    args = parser.parse_args(argv)

    vault = find_vault()
    if not vault:
        looked = [r for r in CANDIDATE_ROOTS if r]
        sys.stderr.write(
            "read_vault.py: could not find the vault.\n"
            "Looked for a directory in:\n"
            + "".join("  %s\n" % r for r in looked)
            + "Set VAULT_ROOT to the vault path to override.\n")
        return 2

    index_path = os.path.join(vault, INDEX_NAME)
    if not os.path.isfile(index_path):
        sys.stderr.write(
            "read_vault.py: found the vault at %s but no %s in it.\n"
            % (vault, INDEX_NAME))
        return 2

    if args.index_only:
        print("vault: %s" % vault)
        print("index: %s" % index_path)
        print("size:  %d bytes" % os.path.getsize(index_path))
        return 0

    if args.tree:
        print("vault: %s" % vault)
        for entry in sorted(os.listdir(vault)):
            full = os.path.join(vault, entry)
            if os.path.isdir(full):
                count = sum(len(files) for _, _, files in os.walk(full))
                print("  %-22s (%d file%s)" % (entry, count,
                                               "" if count == 1 else "s"))
            else:
                print("  %s" % entry)
        return 0

    text = read_text(index_path)
    _, body = split_frontmatter(text)
    sections = parse_sections(body)

    if args.list:
        show_sections(sections)
        return 0

    wanted = None
    if args.rules:
        wanted = "rules"
    elif args.section:
        wanted = args.section

    if wanted:
        hits = match_section(sections, wanted)
        if not hits:
            sys.stderr.write("no section matching %r. Available:\n" % wanted)
            show_sections(sections, sys.stderr)
            return 2
        for _, _, content in hits:
            print(content)
            print()
        return 0

    # Default: the whole index, minus the frontmatter (which is metadata for
    # Obsidian, not instructions).
    print(body.strip())
    print()

    if args.priorities:
        priorities = os.path.join(vault, PRIORITIES_NAME)
        if os.path.isfile(priorities):
            print("=" * 70)
            print("# %s" % PRIORITIES_NAME)
            print("=" * 70)
            _, pbody = split_frontmatter(read_text(priorities))
            print(pbody.strip())
        else:
            print("(no %s in the vault)" % PRIORITIES_NAME)
    return 0


if __name__ == "__main__":
    sys.exit(main())