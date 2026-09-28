Start-Sleep -Seconds 30
Write-Host '=== log tail ==='
$log = 'C:\Users\casey\Desktop\Homesteader\tools\_pip_step2.log'
if (Test-Path $log) { Get-Content $log -Tail 20 }
Write-Host '=== still-alive python ==='
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, CPU, StartTime | Format-Table -AutoSize
