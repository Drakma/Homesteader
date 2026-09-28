Set-Location C:\Users\casey\Desktop\Homesteader
Write-Output "--- killing old python 41756 ---"
Stop-Process -Id 41756 -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id,StartTime,@{Name='WS_MB';Expression={[Math]::Round($_.WorkingSet64/1MB,1)}}
