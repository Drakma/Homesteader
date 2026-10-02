# Homesteader ChatGPT MCP bridge

This service proxies the MCP tools in the project's `.mcp.json` through one
local `stdio` server. It starts local `stdio` servers only when ChatGPT asks for
their tools and connects to configured HTTP servers directly. Tool names are
prefixed with the server name, for example `homesteader-asset-kit__...` and
`unity-mcp__...`.

The bridge has no network listener: it communicates over standard input/output
and is intended to run as the local MCP command for OpenAI Secure MCP Tunnel.
The tunnel client authenticates to OpenAI and forwards calls to this private
process, so no public endpoint or extra bridge token is needed.

## Run

Create a tunnel in OpenAI Platform tunnel settings, then run the current
`tunnel-client` release in a PowerShell session. Set its runtime API key and
initialize a stdio profile that starts the bridge:

```powershell
$env:CONTROL_PLANE_API_KEY = '<your runtime API key>'
& 'C:\path\to\tunnel-client.exe' init --sample sample_mcp_stdio_local --profile homesteader --tunnel-id '<your tunnel id>' --mcp-command "C:\Python313\python.exe C:\Users\casey\Desktop\Homesteader\tools\chatgpt_mcp_bridge\bridge.py"
& 'C:\path\to\tunnel-client.exe' doctor --profile homesteader --explain
& 'C:\path\to\tunnel-client.exe' run --profile homesteader
```

The bridge reads `C:\Users\casey\Desktop\Homesteader\.mcp.json` by default.
Set `HOMESTEADER_MCP_CONFIG` if the config is elsewhere.

In ChatGPT, create a developer-mode app and select **Tunnel** under Connection.
Select the tunnel used by this profile. OpenAI Secure MCP Tunnel keeps the
bridge private and does not require opening an inbound port.

## Meshy tool restrictions

The `.mcp.json` Meshy entry runs the generic `@meshy-ai/meshy-mcp-server`.
Its generation tools can create previews, use other generation routes, and do
not implement Homesteader's required single-task textured low-poly pipeline.
The bridge therefore exposes Meshy's balance and read-only tools only; it hides
generation and other write-capable Meshy tools. Use the approved project
`tools/meshy_client.py` path for generation, including checking the balance,
showing the estimated and resulting balance, and obtaining explicit approval.

## Configuration

The bridge only reads server commands, arguments, URLs, and environment values
from `.mcp.json`; it does not print environment values. Environment references
in the form `${NAME}` and `${NAME:-default}` are expanded at runtime.

Required Python packages are listed in `requirements.txt`.
