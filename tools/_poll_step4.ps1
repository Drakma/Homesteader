Start-Sleep -Seconds 60
$logPath = 'C:\Users\casey\Desktop\Homesteader\tools\_download_step4.log'
$dest = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1'

Write-Host '=== python process ==='
Get-Process python -ErrorAction SilentlyContinue |
    Where-Object { $_.StartTime -gt (Get-Date).AddMinutes(-10) } |
    Select-Object Id, CPU, WS, StartTime |
    Format-Table -AutoSize

if (Test-Path $logPath) {
    Write-Host '=== log tail ==='
    Get-Content $logPath -Tail 20
}
if (Test-Path $dest) {
    $size = (Get-ChildItem -Recurse -Force $dest 2>$null | Measure-Object -Property Length -Sum).Sum
    $cnt  = (Get-ChildItem -Recurse -Force $dest 2>$null | Measure-Object).Count
    Write-Host ("=== on-disk state ===")
    Write-Host ("files : {0}" -f $cnt)
    Write-Host ("bytes : {0:N2} GB  ({1:N0} B)" -f ($size / 1GB), $size)
}
