#!/usr/bin/env python3
"""Load the repo's `.env` into this process's environment.

Why this exists
---------------
Secrets used to be committed in plaintext in `.mcp.json` and as a fallback
default in `tools/meshy_client.py`. `.env` is gitignored, so it is where they
belong. But not every consumer of a secret reads `.env` on its own: `npx
@meshy-ai/meshy-mcp-server` reads `MESHY_API_KEY` from the environment and knows
nothing about dotfiles. This module is the seam that fills that gap.

Two callers use it:
  - `tools/mcp_host.py`, before spawning a server, so a config value of
    `"${MESHY_API_KEY}"` resolves from `.env`.
  - `tools/meshy_client.py`, so a direct-script run picks up the same key.

Format
------
Deliberately minimal and dependency-free (no python-dotenv). Supported inside a
line: comments starting with `#`, blank lines, `KEY=value`, optional `export `
prefix, and single/double quoted values. Values are stripped of surrounding
quotes; no escape processing, because a naive expander that half-implements
escaping is worse than one that plainly does not.

Precedence: a real environment variable always wins. `.env` only fills gaps, so
a shell that already exported the key is never silently overridden.
"""

import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_ENV_PATH = os.path.join(REPO_ROOT, ".env")


def parse_env_file(path):
    """Return {name: value} found in `path`. Missing file returns {}."""
    values = {}
    if not path or not os.path.isfile(path):
        return values
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return values

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[len("export "):].lstrip()
        if "=" not in stripped:
            continue
        name, _, value = stripped.partition("=")
        name = name.strip()
        value = value.strip()
        if not name:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        values[name] = value
    return values


def load_env(path=None):
    """Populate os.environ from `.env`, without overwriting existing values.

    Returns the list of names that were newly set, so a caller can report what
    it picked up (never the values themselves).
    """
    values = parse_env_file(path or DEFAULT_ENV_PATH)
    applied = []
    for name, value in values.items():
        if name in os.environ:
            continue
        os.environ[name] = value
        applied.append(name)
    return applied


ENV_VAR_PREFIX = "${"
ENV_VAR_SUFFIX = "}"


def resolve_env_vars(value, missing=None):
    """Replace whole-string `${NAME}` references with the environment value.

    Only a value that is *entirely* one `${NAME}` reference is substituted. A
    reference embedded mid-string is left alone, so a joining operation that
    mangles punctuation cannot silently corrupt a value. An unresolvable
    reference is left as-is and its name is appended to `missing` (when a list
    is supplied) so the caller can fail loudly rather than pass the literal
    string `${MESHY_API_KEY}` to a server as if it were a key.
    """
    if not isinstance(value, str):
        return value
    if not (value.startswith(ENV_VAR_PREFIX) and value.endswith(ENV_VAR_SUFFIX)):
        return value
    name = value[len(ENV_VAR_PREFIX):-len(ENV_VAR_SUFFIX)].strip()
    if not name:
        return value
    resolved = os.environ.get(name)
    if resolved is None:
        if isinstance(missing, list) and name not in missing:
            missing.append(name)
        return value
    return resolved


def resolve_spec_env(spec, missing=None):
    """Return a copy of a server spec with its `env` block's references resolved.

    The spec dict from `.mcp.json` is not mutated: the caller gets a new dict
    with a new `env` mapping, so a failed resolve cannot leave the loaded config
    holding a half-expanded value.
    """
    if not isinstance(spec, dict):
        return spec
    raw_env = spec.get("env")
    if not isinstance(raw_env, dict):
        return dict(spec)
    resolved_spec = dict(spec)
    resolved_spec["env"] = {
        name: resolve_env_vars(value, missing)
        for name, value in raw_env.items()
    }
    return resolved_spec