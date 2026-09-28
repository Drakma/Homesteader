Set-Location C:\Users\casey\Desktop\Homesteader
Write-Output "=== Python processes before cleanup ==="
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime, @{Name = 'WS_MB'; Expression = { [Math]::Round($_.WorkingSet64 / 1MB, 1) } }, CommandLine | Format-List

# Stop any test python processes (excluding the MCP server tools/asset_kit_mcp.py or blender-mcp if needed, or specific test PIDs)
$testProcs = Get-CimInstance Win32_Process -Filter "name = 'python.exe'" | Where-Object { 
    $_.CommandLine -like "*qwen*" -or 
    $_.CommandLine -like "*_debug*" -or 
    $_.CommandLine -like "*_test*" -or 
    $_.CommandLine -like "*_smoke*" 
}

foreach ($p in $testProcs) {
    Write-Output "Stopping test process PID $($p.ProcessId): $($p.CommandLine)"
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 1

Write-Output "=== Remaining Python processes ==="
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime, @{Name = 'WS_MB'; Expression = { [Math]::Round($_.WorkingSet64 / 1MB, 1) } }
