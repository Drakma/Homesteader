Start-Sleep -Seconds 60
Write-Host '=== still-running python ==='
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, CPU, StartTime | Format-Table -AutoSize
Write-Host '=== log tail ==='
$log = 'C:\Users\casey\Desktop\Homesteader\tools\_system_install.log'
if (Test-Path $log) { Get-Content $log -Tail 15 }
Write-Host '=== diffusers dir state ==='
$dst = 'C:\Users\casey\Desktop\Homesteader\tools\.venv-qwen-image\Lib\site-packages'  # won't exist
$dst = 'C:\Users\casey\AppData\Roaming\Python\Python313\site-packages\diffusers'
if (Test-Path $dst) {
    $n = (Get-ChildItem -Recurse -Force $dst 2>$null | Measure-Object).Count
    $b = (Get-ChildItem -Recurse -Force $dst 2>$null | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host ("diffusers: {0} entries, {1:N1} MB" -f $n, $b)
} else {
    Write-Host 'diffusers dir not present'
}
