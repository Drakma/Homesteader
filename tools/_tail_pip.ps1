Start-Sleep -Seconds 60
Write-Host '=== still-running python ==='
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, CPU, WS | Format-Table -AutoSize
Write-Host '=== log tail ==='
$logPath = 'C:\Users\casey\Desktop\Homesteader\tools\_pip_step2.log'
if (Test-Path $logPath) {
    $lines = (Get-Content $logPath).Count
    Write-Host "log line count: $lines"
    Get-Content $logPath -Tail 8
}
