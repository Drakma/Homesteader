# Session Startup

How a session knows what is working before any real work starts.

## The check

```powershell
C:\Python313\python.exe C:\Users\casey\Desktop\Homesteader\tools\session_start.py
```

```
SESSION START - tool check
============================================================
ok    python interpreter   C:\Python313\python.exe
ok    mcp config           5 server(s) declared
ok    mcp servers          5 ok, 0 failed
ok    unity bridge         pid 27008  project Homesteader
ok    vault                Brain (8756 bytes)
ok    vault priorities     Active Priorities.md present
ok    skill unity-mcp      installed
ok    skill vault-context  installed
all 8 checks passed - tools are working
```

Flags: `--json` (machine readable), `--quick` (skip the slow MCP handshakes),
`--verbose` (print diagnostics on failure). Exit 0 = all working, 1 = something
is down.

It is a **report**, not a fixer. It changes nothing and starts nothing that
outlives the call.

## It runs automatically (the guarantee)

`.vscode/tasks.json` has a task with `runOn: folderOpen`, so the check **runs by
itself when you open the Homesteader folder** — no agent, no remembering, no
manual step. That file is the guarantee; everything else here is the command it
calls.

```json
{
  "label": "Homesteader: session start check",
  "runOptions": { "runOn": "folderOpen" },
  "presentation": { "reveal": "always", "panel": "dedicated", "focus": false }
}
```

Two more tasks in the same file for on-demand use, via
**Terminal → Run Task**: `Homesteader: tool check (on demand)` and
`Homesteader: tool check (quick)` (skips the slow MCP handshakes).

Note `runOn` lives inside `runOptions`, not at the task root — see the
[VS Code tasks documentation](https://code.visualstudio.com/docs/debugtest/tasks).

### The one dependency: workspace trust

A `folderOpen` task **does not run in an untrusted workspace**. This profile has
`security.workspace.trust.startupPrompt: "always"`, so if you open the folder
and decline trust, the banner silently does not appear — which is exactly the
failure mode this whole setup exists to remove.

If the banner is missing on open, check trust first before assuming the check
broke.

## Why a skill could not do this

Skills are text loaded into an agent's context. **Nothing in a `SKILL.md`
executes** — a skill describes a tool, it does not run one. That is observable
in this repo: `browser-automation` describes a browser tool and no browser
launches until something calls it; `game-development` describes running games
and nothing starts on its own.

So a skill can only ever *ask* an agent to run the check, and whether it happens
depends on the agent's judgment at the start of a session. That is a request,
not a guarantee. The task is what makes it a guarantee.

`AGENTS.md` still carries the directive, and both skills still mention it. That
is deliberate redundancy: it costs nothing, and it covers the case where the
banner scrolled past or an agent is running somewhere that has no `tasks.json`.

## The two skills

Both live in `tools/skills-src/<name>/` inside the repo and are **installed** to
`~/.codegpt/skills/<name>/`, because that directory is the only place skills are
read from at startup.

| skill | what it does | ships |
|---|---|---|
| `unity-mcp` | Calls live Unity / Blender / Meshy / asset-kit tools over MCP | `SKILL.md`, `mcp_call.py` |
| `vault-context` | Reads Casey's vault index and preferences | `SKILL.md`, `read_vault.py` |

Install or re-install:

```powershell
C:\Python313\python.exe C:\Users\casey\Desktop\Homesteader\tools\install_skill.py
C:\Python313\python.exe C:\Users\casey\Desktop\Homesteader\tools\install_skill.py --check
C:\Python313\python.exe C:\Users\casey\Desktop\Homesteader\tools\install_skill.py --list
C:\Python313\python.exe C:\Users\casey\Desktop\Homesteader\tools\install_skill.py unity-mcp
```

**Run the installer after editing anything in `tools/skills-src/`.** The repo
copy is the source; the installed copy is what a session reads. Editing only one
of them is the same class of mistake as the two divergent `mcp_config.json`
files this project already tripped over. `--check` reports drift; `session_start.py`
reports stale skills as a FAIL.

### Why the installer exists at all

`~/.codegpt/skills/` is **outside the Homesteader workspace**. An agent editing
files with workspace-scoped tools cannot write there — it gets
`PATH_OUTSIDE_WORKSPACE`, or a `403` from the host's file service. The source
therefore lives in the repo, where it can be edited, and a script performs the
copy. That is a workaround for a real constraint, not a preference.

## The vault

`C:\Users\casey\Brain` — the vault's own capitalisation. Note `C:\Users\casey\brain`
(lowercase) also resolves on Windows; do not "fix" one spelling into the other.

```powershell
C:\Python313\python.exe C:\Users\casey\.codegpt\skills\vault-context\read_vault.py
C:\Python313\python.exe C:\Users\casey\.codegpt\skills\vault-context\read_vault.py --list
C:\Python313\python.exe C:\Users\casey\.codegpt\skills\vault-context\read_vault.py --rules
C:\Python313\python.exe C:\Users\casey\.codegpt\skills\vault-context\read_vault.py --priorities
```

**The vault's rules are inside `VAULT-INDEX.md`**, in its "Vault Rules for AI"
section. There is no separate `RULES.md` or `CLAUDE.md` in the vault — a
recursive search of `Brain` turns up exactly one rules-bearing file, the index
itself. `--rules` extracts that section with its `###` children intact.

A workspace-scoped file read of the vault **fails** (403 / outside workspace),
which is why the skill ships a script rather than telling an agent to read the
path directly.

## Related

- `docs/MCP_HOST.md` — the MCP host the `unity-mcp` skill wraps.
- `tools/session_start.py`, `tools/install_skill.py` — the implementations.
- `AGENTS.md` — the session-start directive, stated as a rule.