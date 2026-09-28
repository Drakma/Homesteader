# Kill the stalled pip + git subprocesses, leave the venv intact for retry.
$ErrorActionPreference = 'SilentlyContinue'
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process git -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1
Get-Process python, git -ErrorAction SilentlyContinue | Select-Object Id, Name
