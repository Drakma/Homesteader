# Unity MCP Wrapper (`tools/unity_mcp.py`)

A thin Python wrapper that lets a script or AI shell talk to the running
Unity Editor through the MCP relay that ships with `com.unity.ai.assistant`.

This is *not* a Unity tool itself - it is a client for the existing relay
binary. The Editor stays unchanged; we spawn our own `relay_win.exe --mcp`
subprocess and pipe standard MCP JSON-RPC into its stdin/stdout.

## When to use it

- When you (or an AI agent) need to read editor state: console logs, project
  metadata, scene captures.
- When you need to make changes inside the Editor from a non-Unity-context:
  use `Unity_RunCommand` to compile and execute a `CommandScript` against the
  Editor API - it can do anything `using UnityEditor;` can do, but only while
  the editor is unlocked and in focus on the main thread.

It is **not** a substitute for the asset-generation pipeline - tools like
`Unity_AssetGeneration_GenerateAsset` are paid (consume credits) and the
Homesteader pipeline uses `tools/free_generator.py` + paid opt-ins explicitly.

## Quick start

```bash
# Tools python shim handles the absolute interpreter for you.
tools\unity_mcp.cmd                              health
tools\unity_mcp.cmd                              list-tools-table
tools\unity_mcp.cmd call Unity_GetConsoleLogs ^
    --args-file tools\.scratch\args_just_max.json
```

A note on Windows shell quoting: PowerShell 5.1 strips double-quoted JSON
fragments when they are mixed with single-quoted args. Use `--args-file` to
sidestep that, or write a tiny JSON file in `tools/.scratch/` first.

## What it does under the hood

```
[shell / AI agent]
  |
  | JSON-RPC over stdio (init, tools/list, tools/call)
  v
tools/unity_mcp.py
  |
  | spawn -> stdin/stdout JSON-RPC
  v
Library/PackageCache/com.unity.ai.assistant@<hash>/RelayApp~/relay_win.exe  --mcp
  |
  | named pipe  (\.\pipe\unity-mcp-<instance>)
  v
Unity Editor (MCP Bridge)  --> live editor state and APIs
```

- **stdio side**: standard Model Context Protocol. Newline-delimited JSON-RPC
  frames. Our wrapper speaks `initialize`, `tools/list`, `tools/call`.
- **pipe side**: relay's own private protocol to Unity. We never touch it
  directly; the relay does. Earlier probe scripts in `tools/.scratch/` did
  try, and the bridge returned `Command type cannot be empty`.

## Tools exposed by your current editor

`list-tools-table` reports these as of 2026-09-20:

| Tool                                | Notes                                                   |
|-------------------------------------|---------------------------------------------------------|
| `Unity_AssetGeneration_GenerateAsset` | Paid. Triggers consent dialog. Avoid for routine work. |
| `Unity_AssetGeneration_GetModels` | List available generation models (free).                |
| `Unity_Camera_Capture`             | Render from a specific camera instance id.              |
| `Unity_GetConsoleLogs`             | Read console logs (always safe, no approval needed).    |
| `Unity_RunCommand`                 | Compile + execute an `IRunCommand` C# block. **Swiss army knife.** |
| `Unity_SceneView_Capture2DScene`   | Capture a rectangular world-space region of a 2D scene. |
| `Unity_SceneView_CaptureMultiAngleSceneView` | Capture scene view from 4 angles (3D layout QA). |

## The consent flow

The relay noted in its own log `[MCP Approval] Tool call: Unity_GetConsoleLogs,
mcpApprovalRequired: false`. Tools that only need read access appear to be
auto-approved. State-changing tools - notably `Unity_RunCommand`,
`Unity_AssetGeneration_*`, anything that modifies assets or the scene - may
trigger an approval dialog inside the Editor the first time they are used
in a session. The dialog appears in **Edit > Project Settings > AI > Unity
MCP**; click "Approve" to grant the relay permission for that tool.

Once approved, the choice is persisted in
`Homesteader/Library/AI.MCP/connections-v2.asset`. New relays started with the
same binary will be auto-approved.

## Programmatic use from Python

```python
from tools import unity_mcp  # if you import by path; or use PYTHONPATH

client = unity_mcp.UnityMCPClient()  # auto-starts a relay subprocess
client.start()
print(client.health())
tools = client.list_tools_table()   # {name: one-liner description}
print(json.dumps(tools, indent=2))
result = client.call("Unity_GetConsoleLogs", {"maxEntries": 5})
print(result["content_blocks"][0]["text"])
client.stop()
```

For a long-lived process, the module exposes `get_client()` which lazily
creates and reuses a single `UnityMCPClient` per interpreter.

## Troubleshooting

- **` not find relay_win.exe`**: the package cache hash changes per
  release. Either update `DEFAULT_RELAY` in `tools/unity_mcp.py` or set
  the env var `UNITY_RELAY` to the absolute path.
- **Handshake refused**: confirm the Editor is running and the same project
  (`C:\Users\casey\Desktop\Homesteader\Homesteader`) is open. Inspect
  `Homesteader/Logs/Editor.log` for `[INFO ] [Unity Mcp Server]` lines.
- **Approval dialog blocks forever**: switch focus to the Editor window;
  the dialog sits in `Edit > Project Settings > AI > Unity MCP`. Approval
  state persists across sessions but not across Unity Editor restarts if
  Identity trust is reset.
- **`Broken pipe` while calling**: the relay process likely crashed; check
  `client.recent_stderr()` for relay-side diagnostics.

## Files

- `tools/unity_mcp.py` - the wrapper itself.
- `tools/unity_mcp.cmd` - Windows shim that resolves the absolute Python
  interpreter and forwards args.
- `tools/.scratch/pipe_*.py`, `pipe_*_log` - probe scripts used during
  discovery. Safe to delete; kept for now so future regressions are easier
  to diagnose.
- `tools/.scratch/args_*.json`, `runcmd_safe.json` - sample argument files.
