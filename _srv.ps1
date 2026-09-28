$p = Start-Process -FilePath "C:\Python313\python.exe" `
    -ArgumentList "server.py", "8088" `
    -WorkingDirectory "C:\Users\casey\Desktop\Homesteader\tools" `
    -WindowStyle Hidden -PassThru
Write-Output "PID $($p.Id)"
Start-Sleep -Seconds 3
try {
    $r = Invoke-WebRequest -Uri "http://localhost:8088/api/ping" -UseBasicParsing -TimeoutSec 5
    Write-Output "PING OK: $($r.StatusCode)"
} catch { Write-Output "PING FAILED: $($_.Exception.Message)" }
