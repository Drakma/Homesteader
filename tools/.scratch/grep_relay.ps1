# Dump relocation-relevant strings from the unity-ai-relay binary.
# Goal: find the JSON envelope field names for actual tool calls.
$ErrorActionPreference = 'SilentlyContinue'

$relay = 'C:\Users\casey\Desktop\Homesteader\Homesteader\Library\PackageCache\com.unity.ai.assistant@8d1e3e89e3a7\RelayApp~\relay_win.exe'
$bytes = [IO.File]::ReadAllBytes($relay)
$text  = [System.Text.Encoding]::UTF8.GetString($bytes)

$needles = @(
    'Command type cannot be empty',
    '"type":"call"',
    '"type":"tool"',
    '"type":"handshake"',
    '"type":"response"',
    '"protocol":"unity-mcp"',
    '"version":"2.0"',
    '"toolsHash"',
    '"tools"',
    '"command"',
    '"commandType"',
    '"command_type"',
    '"subcommand"',
    '"client_id"',
    '"clientId"',
    '"session_id"',
    '"sessionId"',
    '"name"',
    '"arguments"',
    '"initialize"',
    'initialize',
    '"id":',
    '"jsonrpc"',
    'STDIN',
    'MCP',
    'ACP'
)

foreach ($n in $needles) {
    Write-Host ('=== ' + $n + ' ===')
    $idx = 0
    $hits = 0
    while ($true) {
        $next = $text.IndexOf($n, $idx)
        if ($next -lt 0) { break }
        $start = [Math]::Max(0, $next - 60)
        $len   = [Math]::Min(160, $text.Length - $start)
        $ctx   = $text.Substring($start, $len)
        Write-Host ('   @' + $next + ': ' + $ctx)
        $idx = $next + 1
        $hits += 1
        if ($hits -ge 5) { break }
    }
    Write-Host ''
}
