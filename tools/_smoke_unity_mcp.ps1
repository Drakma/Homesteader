# smoke-test the unity-mcp stdio entry
$logPath = 'C:\Users\casey\Desktop\Homesteader\Homesteader\Logs\_mcp_smoke.log'
$errPath = "$logPath.err"
if (Test-Path $logPath) { Remove-Item $logPath -Force }
if (Test-Path $errPath) { Remove-Item $errPath -Force }

$argList = @(
    '--mcp',
    '--name', 'unity-mcp',
    '--instance-id', '37412',
    '--project-path', 'C:\Users\casey\Desktop\Homesteader\Homesteader'
)

$proc = Start-Process -FilePath 'C:\Users\casey\.unity\relay\relay_win.exe' `
    -ArgumentList $argList `
    -RedirectStandardOutput $logPath `
    -RedirectStandardError $errPath `
    -PassThru -WindowStyle Hidden

Write-Host ("started PID " + $proc.Id + " logging to " + $logPath)
Start-Sleep -Seconds 5

Write-Host '--- stdout (first 80 lines) ---'
if (Test-Path $logPath) {
    Get-Content $logPath -TotalCount 80 | ForEach-Object { Write-Host $_ }
} else {
    Write-Host 'no stdout file'
}

Write-Host ''
Write-Host '--- stderr (first 80 lines) ---'
if (Test-Path $errPath) {
    Get-Content $errPath -TotalCount 80 | ForEach-Object { Write-Host $_ }
} else {
    Write-Host 'no stderr file'
}

Write-Host ''
Write-Host '--- proc state ---'
$p = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
if ($p) {
    $up = [int]((Get-Date) - $p.StartTime).TotalSeconds
    Write-Host ("PID " + $p.Id + " uptime=" + $up + "s")
} else {
    Write-Host 'process exited'
}

Write-Host '--- post-launch relay listeners owned by smoke pid ---'
$conns = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -eq $proc.Id }
if ($conns) {
    $conns | Select-Object LocalAddress, LocalPort, OwningProcess | Format-Table -AutoSize
} else {
    Write-Host 'no listeners (relay may have exited or is not listening)'
}

Write-Host '--- all relay_win.exe pids ---'
Get-Process -Name relay_win -ErrorAction SilentlyContinue | Format-Table Id, StartTime -AutoSize

Write-Host '--- killing smoke process ---'
$killTarget = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
if ($killTarget) {
    Stop-Process -Id $proc.Id -Force
    Write-Host 'killed'
} else {
    Write-Host 'already gone'
}
