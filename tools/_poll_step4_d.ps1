Start-Sleep -Seconds 90
$logPath = 'C:\Users\casey\Desktop\Homesteader\tools\_download_step4.log'
$globalCache = "$env:USERPROFILE\.cache\huggingface"
$dest = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1'

Write-Host '=== python process (started in last 30 min) ==='
Get-Process python -ErrorAction SilentlyContinue |
    Where-Object { $_.StartTime -gt (Get-Date).AddMinutes(-30) } |
    Select-Object Id, CPU, WS, StartTime |
    Format-Table -AutoSize

if (Test-Path $logPath) {
    Write-Host '=== step 4 log tail ==='
    Get-Content $logPath -Tail 10
}

if (Test-Path $globalCache) {
    $sz = (Get-ChildItem -Recurse -Force $globalCache 2>$null | Measure-Object -Property Length -Sum).Sum
    Write-Host ("global hf cache: {0:N2} GB" -f ($sz/1GB))
    Get-ChildItem -Recurse -Force $globalCache -Filter '*.incomplete' 2>$null |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 5 |
        ForEach-Object {
            Write-Host ("  in-progress: {0:N2} GB | {1}" -f ($_.Length/1GB), $_.FullName.Replace($globalCache, ''))
        }
}

if (Test-Path $dest) {
    $sz = (Get-ChildItem -Recurse -Force $dest 2>$null | Measure-Object -Property Length -Sum).Sum
    Write-Host ("local_dir: {0:N2} GB" -f ($sz/1GB))
}
