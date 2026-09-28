Start-Sleep -Seconds 60
$dest = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1'
$logPath = 'C:\Users\casey\Desktop\Homesteader\tools\_download_step4.log'

Write-Host '=== python state ==='
Get-Process python -ErrorAction SilentlyContinue |
    Where-Object { $_.StartTime -gt (Get-Date).AddMinutes(-30) } |
    Select-Object Id, CPU, WS |
    Format-Table -AutoSize

Write-Host '=== local_dir size + recent files ==='
$total = (Get-ChildItem -Recurse -Force $dest 2>$null | Measure-Object -Property Length -Sum).Sum
Write-Host ("total: {0:N2} GB" -f ($total / 1GB))
$now = Get-Date
Get-ChildItem -Recurse -Force $dest 2>$null |
    Where-Object { -not $_.PSIsContainer -and -not ($_.FullName -like '*\cache\*') -and $_.Extension -notin '.lock','.incomplete','.metadata' } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 8 |
    ForEach-Object {
        $sec = [int](($now - $_.LastWriteTime).TotalSeconds)
        Write-Host ("+{0,4}s  {1,8:N2} GB  {2}" -f $sec, ($_.Length / 1GB), $_.FullName.Replace($dest, ''))
    }

Write-Host '=== log tail ==='
if (Test-Path $logPath) { Get-Content $logPath -Tail 14 }
