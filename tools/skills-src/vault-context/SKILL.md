orkin---
name: vault-context
description: "Read Casey's vault index before doing anything else, so you know who he is, how he works, and what is active. Use at the START OF EVERY CONVERSATION, and whenever a task touches his preferences, his memory, his notes, the daily log, or 'remember this'. Triggers on: start of session, who am I, my preferences, what's active, remember this, save this, daily note, vault, Obsidian, my brain, working style, priorities."
allowed-tools: Bash(C:/Python313/python.exe *skills/vault-context/read_vault.py:*)
---

# vault-context

Casey's vault is his memory and it lives outside this workspace, so nothing here
loads it for you automatically. **Read it at the start of every conversation.**

```bash
C:/Python313/python.exe <this-skill-dir>/read_vault.py
```

`<this-skill-dir>` is the folder you just read this file from — `read_vault.py`
sits beside it. Use that path literally rather than guessing at a home
directory.

**Use the absolute interpreter** (`C:/Python313/python.exe`). Bare `python` is
not on `PATH` in a bare shell — see `AGENTS.md` §4.

## Read it first, every session

The index says this about itself, in its own header:

> Read this file at the start of every conversation to understand who I am, how
> I work, and how this vault is organized.

That is not a suggestion you can weigh against the cost of the call. It is one
file, ~8.7 KB, and it is the whole difference between working the way Casey
works and inventing a working style he has not asked for.

```bash
C:/Python313/python.exe <this-skill-dir>/read_vault.py            # whole index
C:/Python313/python.exe <this-skill-dir>/read_vault.py --section prefs
C:/Python313/python.exe <this-skill-dir>/read_vault.py --list     # headings only
```

## Locations

| what | path |
|---|---|
| the index | `C:\Users\casey\brain\VAULT-INDEX.md` |
| the vault | `C:\Users\casey\Brain` (the vault's own capitalisation) |
| daily notes | `01 - Daily Notes/NN - Month YYYY/YYYY-MM-DD.md` |
| active work | `Active Priorities` note |

Both spellings of the vault path resolve to the same folder on Windows. Use the
path exactly as given above; do not "correct" the case.

`read_vault.py` finds the vault in this order: `VAULT_ROOT` env var, then
`C:\Users\casey\Brain`, then `C:\Users\casey\brain`, then a walk upward from the
script. If none resolve it says so plainly and exits 2 — an empty index is never
reported as "no preferences".

## What is in there, and why it matters

- **Who I Am** — Casey, game developer, building Homesteader in Unity 6.
- **Key People** — Jarvis (AI chief of staff).
- **What's Active Right Now** — all open work lives in one note; check it, and
  **verify an item's real state before acting on it. A listed item may already
  be done.**
- **My Preferences for Working with AI** — the working style, below.
- **How My Memory Works** — the vault IS the memory; do not try to hold it all,
  hold what the task needs and search for the rest.
- **Vault Rules for AI** — frontmatter, wikilinks, folder indexes, archiving,
  daily notes.
- **Checkpoint Persistence** — persist anything a future session would need,
  without being asked.

## The preferences, in brief

Read the real thing — this is a pointer, not a substitute. But the shape of it:

- **Plain language, no jargon, be direct.** Don't hedge or over-qualify.
- **Don't settle for half-finished work.** "v2 later" is not a place to park a
  known flaw.
- **Be a partner, not a yes-man.** Argue your position. When he pushes back,
  don't just cave — half the time he's testing your reasoning.
- **Take it straight.** Don't deflect thanks or pile on flattery.
- **"Why do you need that?" is a spec-check, not confusion.** Re-examine the
  plan, then fix it or defend it.
- **Recommend for his actual setup**, not a generic beginner.
- **Don't sandbag timelines.** His bottleneck is planning, not doing.
- **Pull him back from rabbit holes.** Flag tangents; be the closer.
- **Offer to draft his copy**, unprompted, once direction is clear.
- **Don't push him toward shipping.** Show what changed and stop.
- **Restating isn't approving.** Iteration is not sign-off. Wait for "lock it".
- **"Remember this" means save it in two places** — your memory AND the vault.
- **He drives the trust-and-access ramp.** Never propose expanding your own
  access; default to scoping down.

## Vault rules if you write there

Only relevant when a task actually touches the vault, but then it matters:

- **Every note needs YAML frontmatter.** Infer the values; never ask.
  `status: active|completed|parked|idea|archived`,
  `project: homesteader|personal|meta`,
  `type: index|reference|guide|plan|log`.
- **Append before you create.** Fewer, fuller notes beat many thin ones.
- **Wikilink** people, businesses/products/platforms, and notes this one
  references. Never link generic words, the same target twice, or the note's own
  title.
- **Keep folder indexes in sync** in the same pass as the change.
- **Daily notes** come from the template, and append a `## Session N` section if
  one already exists for today.
- **Never archive on your own initiative**, and always confirm first.
- **No frontmatter or wikilinks in code files.**

## Gotchas found by using this

- **Read it at the START, not on demand.** The point is that you know the
  working style before you make a first decision, not after Casey corrects you
  for the third time.
- **The index is not the vault.** It is 8.7 KB; the vault is much larger. Read
  the index, then follow wikilinks or search — do not try to load everything.
- **"What's Active" can be stale.** The index itself warns that a listed item
  may already be done. Verify before acting on it.
- **The vault path is CASE-INCONSISTENT between its own index and the filesystem
  as quoted.** `Brain` vs `brain`. Harmless on Windows; do not "fix" it into a
  single spelling, and do not assume a rewrite is needed.
- **Reading the index does not mean you may write to the vault.** Access is
  Casey's call, not yours — see the trust-and-access preference above.
- **A read of this file through a workspace-scoped file tool can fail with 403
  or PATH_OUTSIDE_WORKSPACE**, because it lives outside the Homesteader
  workspace. That is why this skill ships a script: run it in the terminal and
  the read works.