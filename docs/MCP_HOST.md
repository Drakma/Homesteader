# Standalone MCP Host (`tools/mcp_host.py`)

A single-file, standard-library MCP host that spawns every server in
`.mcp.json` over stdio and lets you list and call their tools for real.

This exists because **the CodeGPT extension cannot do it**. CodeGPT 3.24.73
contains no MCP client and no agent/tool loop at all — verified by grepping its
source *and* its 1.5 MB `dist/extension.js` bundle, which returns zero hits for
`ModelContextProtocol`, `jsonrpc`, `readOnly`/`tool_call`/`function_call`, or
`vscode.lm`. Its model calls and tool decisions happen on CodeGPT Plus's
servers. There is no local seam to add a tool at, so no patch to that extension
can ever expose Unity tools inside its sidebar chat. This host is the
alternative: a real MCP client you drive directly.

## Usage

Run it with the project's standard absolute interpreter — `python` is not on
`PATH` in a bare shell (see `AGENTS.md` §4):

```powershell
# handshake every server, print tool counts
C:\Python313\python.exe tools\mcp_host.py selftest

# list tools (all servers, or one)
C:\Python313\python.exe tools\mcp_host.py list
C:\Python313\python.exe tools\mcp_host.py list unity-mcp

# a tool's full input schema
C:\Python313\python.exe tools\mcp_host.py schema unity-mcp Unity_RunCommand

# call a tool
C:\Python313\python.exe tools\mcp_host.py call unity-mcp Unity_GetConsoleLogs --json '{}'
C:\Python313\python.exe tools\mcp_host.py call unity-mcp Unity_RunCommand --args code="Debug.Log(1);"

# interactive REPL: `server tool {json}` per line
C:\Python313\python.exe tools\mcp_host.py shell
```

`--timeout <seconds>` and `--debug` work **before or after** the subcommand.
`--debug` prints the JSON-RPC traffic and the child's stderr live, which is the
first thing to reach for when a server will not start.

Add `--strict` to `list` to make it exit non-zero if any server fails.

## Which config it reads

`tools/mcp_host.py` reads, in order:

1. `C:\Users\casey\Desktop\Homesteader\.mcp.json`  (project root — **the source of truth**)
2. `C:\Users\casey\.codegpt\mcp_config.json`  (legacy fallback)

Both currently define the same five servers, but only the project file is
canonical. The `~/.codegpt` copy is a hand-maintained duplicate that already
caused one detour: editing it has no effect on anything, because nothing reads
it. Prefer `.mcp.json`. Override with `--config <path>`.

## Servers and current tool counts

| server | tools | notes |
|---|---:|---|
| `blender` | 32 | `uvx blender-mcp` — needs Blender running with the addon |
| `meshy` | 24 | npm package, 3-20s to boot (validates the API key live) |
| `homesteader-asset-kit` | 11 | project catalog tooling |
| `unity-mcp` | 7 | `relay_win.exe --mcp` → Unity editor bridge |
| `mesh2motion` | 5te dev server |
| **total** | **79** | |

Verify any time with `selftest`.

## Windows quirks this file handles

These cost real debugging time; they are documented so nobody re-derives them.

- **Bare `npx` does not resolve.** Node is not on `PATH` on this machine. The
  host falls back to `KNOWN_TOOL_DIRS` and tries `.exe`, `.cmd`, `.bat`, then
  the extensionless name — order matters, because nodejs ships both `npx` (a
  POSIX shell script Windows cannot run: `WinError 193`) and `npx.cmd`.
- **`npx` servers are re-pointed at the installed package.** `npx.cmd`'s shim
  calls bare `node` internally, which fails when Node is off `PATH`, even when
  the shim itself was launched by absolute path. `rewrite_npx_server()` turns
  `npx -y @scope/pkg` into `node <global node_modules>/@scope/pkg/dist/index.js`,
  removing the shim from the path entirely.
- **`cmd.exe` is launched by absolute path.** Never the bare name — this module
  edits the child's `PATH`, so a `PATH` without System32 would make `cmd.exe`
  itself unresolvable. `ComSpec` supplies the path.
- **`.cmd` arguments are passed as one command-line string.** A list like
  `["cmd.exe", "/c", '"C:\\path with spaces\\x.cmd"']` does not survive
  `subprocess` re-quoting; cmd sees literal `\"` and reports the quoted path as
  an unrecognized command.
- **The child's `PATH` gets the tool dirs prepended**, so a shim can find its
  own siblings.

## Statement on Unity tool coverage

Verifying that a call actually reaches the editor matters, so this was tested
rather than assumed:

```
call unity-mcp Unity_GetConsoleLogs --json '{}'
```

returns genuine Unity console output with `Unity.AI.MCP.Editor.Bridge`
stack frames from `com.unity.ai.assistant`, proving relay → named pipe →
editor → response. The bridge registration lives at
`C:\Users\casey\.unity\mcp\connections\bridge-*.json` (named pipe,
`protocol_version 2.0`, `editor_pid`).

The seven Unity tools are:

- `Unity_GetConsoleLogs` — console messages, warnings, errors + stack traces
- `Unity_RunCommand` — compile and execute C# in the Editor
- `Unity_Camera_Capture` — render from a camera, by GameObject instance ID
- `Unity_SceneView_Capture2DScene` — orthographic top-down region capture
- `Unity_SceneView_CaptureMultiAngleSceneView` — 4-angle 2×2 grid
- `Unity_AssetGeneration_GenerateAsset`, `Unity_AssetGeneration_GetModels`

## Scope, honestly stated

This gives **you** a working Unity/Blender/Meshy/asset-kit tool surface from the
command line. It does **not** put those tools inside the CodeGPT sidebar chat,
and nothing can, for the reason in the first section. If you need the tools
available to an agent's own reasoning loop, an agent hosted by something that
implements MCP has to be the one calling them.