$dest = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1'
$logPath = 'C:\Users\casey\Desktop\Homesteader\tools\_download_step4.log'

# python process
Write-Host '=== python (started in last 15 min) ==='
$proc = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -gt (Get-Date).AddMinutes(-15) } | Select-Object Id, CPU, WS
if ($proc) { $proc | Format-Table -AutoSize }

# disk state
Write-Host '=== on-disk state ==='
$now = Get-Date
Get-ChildItem -Recurse -Force $dest 2>$null |
    Where-Object { -not $_.PSIsContainer -and $_.FullName -notlike '*\cache\*' -and $_.Extension -notin '.lock','.incomplete','.metadata' } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 8 |
    ForEach-Object {
        $bn = $_.Name
        $sz = $_.Length
        $szGB = [math]::Round($sz / 1GB, 2)
        $sec = [int](($now - $_.LastWriteTime).TotalSeconds)
        Write-Host ("+{0,4}s  {1,8:N2} GB  {2}" -f $sec, $szGB, $_.FullName.Replace($dest, ''))
    }

# overall disk size under local_dir
$total = (Get-ChildItem -Recurse -Force $dest 2>$null | Measure-Object -Property Length -Sum).Sum
Write-Host ("total on disk: {0:N2} GB" -f ($total / 1GB))

Write-Host '=== log tail ==='
if (Test-Path $logPath) { Get-Content $logPath -Tail 18 }
