# probe Unity MCP relay endpoints on :9002 -- round 2, real schemas
$base = 'http://127.0.0.1:9002'

function Show-Resp($label, $method, $path, $body) {
    Write-Host "--- $label ---"
    $parms = @{
        Uri             = "$base$path"
        Method          = $method
        UseBasicParsing = $true
        TimeoutSec      = 8
        ContentType     = 'application/json'
    }
    if ($null -ne $body) { $parms.Body = $body }
    try {
        $r = Invoke-WebRequest @parms -ErrorAction Stop
        Write-Host ("HTTP " + $r.StatusCode + "  ct=" + $r.Headers['Content-Type'])
        Write-Host ($r.Content.Substring(0, [Math]::Min(800, $r.Content.Length)))
    }
    catch {
        Write-Host ("$method $path -> " + $_.Exception.Message)
        if ($_.Exception.Response) {
            try {
                $sr = New-Object IO.StreamReader($_.Exception.Response.GetResponseStream())
                $txt = $sr.ReadToEnd()
                Write-Host ('resp-body: ' + $txt.Substring(0, [Math]::Min(800, $txt.Length)))
            }
            catch { }
        }
    }
    Write-Host ''
}

Write-Host '##### A. server-status with serverName + action #####'
foreach ($name in @('unity-mcp', 'homesteader-asset-kit', 'Unity')) {
    foreach ($action in @('status', 'start', 'list', 'get')) {
        $body = ConvertTo-Json -Compress @{ serverName = $name; action = $action }
        Show-Resp ("server-status name=$name action=$action") POST '/mcp/server-status' $body
    }
}

Write-Host '##### B. call-tool with Unity_X verbs #####'
foreach ($tool in @('Unity_ReadConsole', 'Unity_ListResources', 'Unity_ManageScene', 'Unity_ManageEditor')) {
    $body = ConvertTo-Json -Compress @{ tool = $tool; arguments = @{} }
    Show-Resp ("call-tool $tool") POST '/mcp/call-tool' $body
}

Write-Host '##### C. plain JSON-RPC envelopes #####'
$rpcCalls = @(
    '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe","version":"0.0.0"}}}',
    '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}',
    '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"Unity_ReadConsole","arguments":{}}}'
)
foreach ($rpc in $rpcCalls) {
    Show-Resp ("rpc -> " + ($rpc.Substring(0, [Math]::Min(60, $rpc.Length)))) POST '/mcp/call-tool' $rpc
}
