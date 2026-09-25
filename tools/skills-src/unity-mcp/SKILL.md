---
name: unity-mcp
description: "Call live Unity, Blender, Meshy, and asset-kit tools over MCP instead of guessing about the editor. Use when you need the Unity console logs, need to run C# in the Editor, need a screenshot from a Unity camera or Scene View, need Meshy credit cost before spending, or need the asset kit's guides and catalog. Triggers on: check Unity, console errors, Unity crashed, run this in Unity, take a screenshot in Unity, how much will this cost, Meshy balance, look at the scene, verify in the editor, call the MCP tool."
allowed-tools: Bash(C:/Python313/python.exe *skills/unity-mcp/mcp_call.py:*)
---

# unity-mcp

Reaches the live Unity Editor, Blender, Meshy and the Homesteader asset kit over
MCP, so you can read the real console, run real C#, and look at the actual scene
instead of asking the user what happened on their screen.

```bash
C:/Python313/python.exe <this-skill-dir>/mcp_call.py <subcommand> [args]
```

`<this-skill-dir>` is the folder you just read this file from — `mcp_call.py`
sits beside it. Use that path literally rather than guessing at a home
directory.

**Use the absolute interpreter** (`C:/Python313/python.exe`). Bare `python` is
not on `PATH` in a bare shell — see `AGENTS.md` §4.

## Why the tools go through this and not through CodeGPT

CodeGPT has no MCP client. Verified, not assumed: grepping its source *and* its
1.5 MB `dist/extension.js` bundle returns zero hits for `ModelContextProtocol`,
`jsonrpc`, `tool_call`, `function_call`, or `vscode.lm`, and there is no MCP SDK
in its `dependencies`. Its model calls and tool decisions happen on CodeGPT
Plus's servers, so there is no local seam to register a tool at. The tools are
reachable **by running this script**, from the terminal, which is what makes
them usable rather than theoretical.

## Start here: `doctor`

```bash
C:/Python313/python.exe <this-skill-dir>/mcp_call.py doctor
```

Handshakes every server and prints tool counts. Run it **before** concluding a
tool is unavailable — it distinguishes "the server is down" from "you called it
wrong", which are otherwise both silent failures.

```
ok    blender                   32 tool(s)   BlenderMCP
ok    homesteader-asset-kit     11 tool(s)   homesteader-asset-kit
ok    mesh2motion                5 tool(s)   mesh2motion
ok    meshy                     24 tool(s)   @meshy-ai/meshy-mcp-server
ok    unity-mcp                  7 tool(s)   unity-mcp-server
5 ok, 0 failed
```

## The loop

```bash
# 1. What can I actually call?
C:/Python313/python.exe <this-skill-dir>/mcp_call.py tools
C:/Python313/python.exe <this-skill-dir>/mcp_call.py tools unity-mcp

# 2. What arguments does it take? (do this before a call you are unsure of)
C:/Python313/python.exe <this-skill-dir>/mcp_call.py schema unity-mcp Unity_RunCommand

# 3. Call it
C:/Python313/python.exe <this-skill-dir>/mcp_call.py call unity-mcp Unity_GetConsoleLogs

# 4. Look at the result, then decide
```

## Unity: the seven tools

| tool | does |
|---|---|
| `Unity_GetConsoleLogs` | console messages, warnings, errors **with stack traces** |
| `Unity_RunCommand` | **compile and execute C# in the Editor** — the big one |
| `Unity_Camera_Capture` | render from a camera, by GameObject instance ID |
| `Unity_SceneView_Capture2DScene` | orthographic top-down region capture |
| `Unity_SceneView_CaptureMultiAngleSceneView` | 4-angle 2x2 grid of the Scene View |
| `Unity_AssetGeneration_GenerateAsset` | generate or modify a Unity asset |
| `Unity_AssetGeneration_GetModels` | list available generation models |

`Unity_RunCommand` is how you inspect the live scene, because it can evaluate
any expression and return the result:

```bash
C:/Python313/python.exe <this-skill-dir>/mcp_call.py call unity-mcp Unity_RunCommand \
  --json '{"code": "return UnityEngine.SceneManagement.SceneManager.GetActiveScene().name;"}'
```

Note the `return` — that is how you get a value back rather than just running a
statement for its side effects. Prefer a read-only expression the first time
you touch a tool you have not used: the Editor is the user's live session, and
an edit is not something you can quietly undo.

## Reading a screenshot

`Unity_Camera_Capture` and both Scene View captures return image data. **You can
read the PNG** — write it out, then read the file to actually look at it.

If a read comes back as `[binary file: png ...]`, this host has no image path: say
so and ask the user what is on screen rather than describing a frame you never
saw. A confident description of an unseen screen is the worst failure this
skill has.

The console log is the cheaper answer and the first move — it settles most
"why is Unity broken" questions for a few hundred tokens, where a frame costs
tens of thousands.

## Meshy: check the balance before spending

At the start of this project the account held **168 credits**, which is why the
standing rule in `AGENTS.md` is that cost confirmation is mandatory before any
spend. `meshy_check_balance` is free and always current:

```bash
C:/Python313/python.exe <this-skill-dir>/mcp_call.py call meshy meshy_check_balance
```

Costs, quoted by the tools themselves: `meshy_animate` 3 credits,
`meshy_convert` 1, `meshy_resize` 1, `meshy_process_multicolor` 10,
`meshy_analyze_printability` **free**.

The generation route is `meshy_text_to_image` -> `meshy_image_to_3d` with
smart-topology and an explicit `target_polycount`. **Low poly is mandatory** —
see `AGENTS.md` §2. Never start a paid generation because a prompt arrived;
present the estimate and the resulting balance, and wait for approval.

## Sessions: none, and that is deliberate

Every call spawns the server, does the work, and exits. Server state does not
survive between calls — a Meshy task you started is still running on Meshy's
side (use `meshy_get_task_status` with the task id), but nothing is held open
locally. This is why the script is safe to call repeatedly, and why you should
capture task ids from a result rather than assuming anything persisted.

## Interpreting failures

- **`server X exited during initialize`** — the child died before answering.
  Re-run with `--debug` to see its stderr; MCP servers report their real problem
  there and nowhere else.
- **`did not answer <method> within Ns`** — still running, just slow. Meshy
  validates its API key over the network and takes seconds to boot; raise
  `--timeout`.
- **`no such server` / `no such tool`** — a typo, not an outage. Confirm the
  exact name with `tools`.
- **Unity connects but a call fails** — check the Editor is actually the right
  project and still open. The bridge file at
  `C:\Users\casey\.unity\mcp\connections\bridge-*.json` names the editor PID and
  project path.

## Gotchas found by using this

- **`doctor` first, always.** Most "the MCP tool does not work" is a server that
  is simply not up, and `doctor` says so in one second.
- **Do not use bare `npx` or bare `python`** anywhere in a command you suggest.
  Neither is on `PATH` on this machine. `mcp_call.py` resolves the `npx`-based
  Meshy server itself, by absolute path, so this is handled — but it is the
  reason the config says `npx` and still works.
- **A Unity call is not a sandbox.** `Unity_RunCommand` executes against the
  user's open Editor with unsaved work in it. Read before you write.
- **`meshy` takes seconds to start.** A short `--timeout` produces a failure
  that looks like a broken server and is not.
- **Tool results can be large.** A console-log call can return tens of
  thousands of tokens of stack traces. Ask a narrower question — filter, or
  target a specific tool — rather than pulling the whole console.
- **The asset kit reads the project's own `.mcp.json`.** If a server is missing
  from `doctor`, check `C:\Users\casey\Desktop\Homesteader\.mcp.json` (the
  source of truth), not `~/.codegpt/mcp_config.json`, which nothing reads.

## Related

- `docs/MCP_HOST.md` — the underlying host, its CLI, and the Windows
  quoting/PATH problems it solves.
- `tools/mcp_host.py` — the implementation. `mcp_call.py` is a thin wrapper
  around it that fixes the config path and the interpreter.