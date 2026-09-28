Write-Output "=== Process 5208 ==="
Get-Process -Id 5208 -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, CPU, @{Name='WS_MB';Expression={[Math]::Round($_.WorkingSet64/1MB,1)}}
Write-Output "=== stdout ==="
Get-Content tools\_debug_stdout.log -Tail 30
Write-Output "=== stderr ==="
Get-Content tools\_debug_stderr.log -Tail 30
