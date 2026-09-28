$ErrorActionPreference = 'SilentlyContinue'
$relay = 'C:\Users\casey\Desktop\Homesteader\Homesteader\Library\PackageCache\com.unity.ai.assistant@8d1e3e89e3a7\RelayApp~\relay_win.exe'
$bytes = [IO.File]::ReadAllBytes($relay)
$text  = [System.Text.Encoding]::UTF8.GetString($bytes)

foreach ($needle in @('stdio transport', '"command"', 'Invalid request', 'Invalid method', 'tools/call', 'tools/list', '"method":"tools', 'callTool', 'method: "tools', 'method:"tools', 'protocolVersion', '"jsonrpc"', 'frame_type')) {
    Write-Host ('===' + $needle + '===')
    $idx = 0
    $hits = 0
    while ($true) {
        $next = $text.IndexOf($needle, $idx)
        if ($next -lt 0) { break }
        $start = [Math]::Max(0, $next - 80)
        $len   = [Math]::Min(220, $text.Length - $start)
        Write-Host ('   @' + $next + ': ' + $text.Substring($start, $len))
        $idx = $next + 1
        $hits += 1
        if ($hits -ge 5) { break }
    }
    Write-Host ''
}
