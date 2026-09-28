Start-Sleep -Seconds 60
Get-Process python -ErrorAction SilentlyContinue |
    Where-Object { $_.StartTime -gt (Get-Date).AddMinutes(-30) } |
    Select-Object Id, CPU, WS |
    Format-Table -AutoSize
$log = 'C:\Users\casey\Desktop\Homesteader\tools\_smoke_step5.log'
if (Test-Path $log) { Get-Content $log -Tail 25 }
Write-Host '---'
$gcDir = "$env:USERPROFILE\.cache\huggingface\hub\models--Qwen--Qwen-Image-2.1"
if (Test-Path $gcDir) {
    $blobs = Join-Path $gcDir 'blobs'
    if (Test-Path $blobs) {
        $sz = (Get-ChildItem -Recurse -Force $blobs | Measure-Object -Property Length -Sum).Sum / 1GB
        Write-Host ("global hub cache blobs: {0:N2} GB" -f $sz)
    }
}
$out = 'C:\Users\casey\Desktop\Homesteader\assets\_qwen_local\smoke.png'
if (Test-Path $out) {
    Write-Host ("smoke.png size: {0:N2} GB" -f ((Get-Item $out).Length / 1GB))
}
