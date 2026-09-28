# Force-kill any pip/python subprocess hanging behind a closed pipe.
$ErrorActionPreference = 'SilentlyContinue'
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -gt (Get-Date).AddMinutes(-30) } | Stop-Process -Force
Get-Process pip -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1
Write-Host 'still-running python:'
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, StartTime | Format-Table -AutoSize
