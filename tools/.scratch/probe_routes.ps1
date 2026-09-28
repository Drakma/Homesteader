# Probe relay :9002 routes with varied bodies to find the correct wire format.

$base = 'http://127.0.0.1:9002'

function Probe($label, $method, $path, $body) {
    $parms = @{
        Uri             = "$base$path"
        Method          = $method
        UseBasicParsing = $true
        TimeoutSec      = 6
        ContentType     = 'application/json'
    }
    if ($null -ne $body) { $parms.Body = $body }
    Write-Host "--- $label ---"
    try {
        $r = Invoke-WebRequest @parms -ErrorAction Stop
        Write-Host ("HTTP " + $r.StatusCode + " ct=" + $r.Headers['Content-Type'])
        Write-Host ($r.Content.Substring(0, [Math]::Min(600, $r.Content.Length)))
    } catch {
        Write-Host ("$method $path -> " + $_.Exception.Message)
        if ($_.Exception.Response) {
            try {
                $sr = New-Object IO.StreamReader($_.Exception.Response.GetResponseStream())
                $txt = $sr.ReadToEnd()
                Write-Host ('resp-body: ' + $txt.Substring(0, [Math]::Min(600, $txt.Length)))
            } catch { }
        }
    }
    Write-Host ''
}

# Probe /mcp/server-status with many plausible body shapes.
$statusCandidates = @(
    '{}',
    '{"action":"status"}',
    '{"serverName":"unity-mcp"}',
    '{"name":"unity-mcp"}',
    '{"server":"unity-mcp"}',
    '{"serverName":"unity-mcp","action":"status"}',
    '{"serverName":"unity-mcp","name":"unity-mcp"}',
    '{"serverName":"unity-mcp","details":true}',
    '{"server":"unity-mcp","action":"status"}',
    '{"id":"unity-mcp"}'
)
foreach ($b in $statusCandidates) {
    Probe ("status body=" + $b.Substring(0, [Math]::Min(60, $b.Length))) POST '/mcp/server-status' $b
}

# Probe /mcp/call-tool with several envelope shapes for the same tool call.
$callCandidates = @(
    '{"tool":"Unity_ReadConsole","arguments":{}}',
    '{"name":"Unity_ReadConsole","arguments":{}}',
    '{"serverName":"unity-mcp","tool":"Unity_ReadConsole","arguments":{}}',
    '{"serverName":"unity-mcp","name":"Unity_ReadConsole","arguments":{}}',
    '{"server":"unity-mcp","tool":"Unity_ReadConsole","arguments":{}}',
    '{"server":"unity-mcp","name":"Unity_ReadConsole","arguments":{}}',
    '{"id":"unity-mcp","name":"Unity_ReadConsole","arguments":{}}',
    '{"method":"tools/call","params":{"name":"Unity_ReadConsole","arguments":{}},"id":1,"jsonrpc":"2.0"}',
    '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"Unity_ReadConsole","arguments":{}}}'
)
foreach ($b in $callCandidates) {
    Probe ("call body=" + $b.Substring(0, [Math]::Min(60, $b.Length))) POST '/mcp/call-tool' $b
}

# Probe /mcp/tools/list and similar inventory endpoints.
foreach ($p in @('/mcp/tools/list','/mcp/list-tools','/mcp/tools','/mcp/capabilities')) {
    Probe "get $p" GET $p $null
}
