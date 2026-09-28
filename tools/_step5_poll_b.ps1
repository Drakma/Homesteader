Start-Sleep -Seconds 60
Write-Host '=== python ==='
Get-Process python -ErrorAction SilentlyContinue Where-Object { $_.StartTime -gt (Get-Date).AddMinutes(-15) } | Select-Object Id, CPU, WS, StartTime | Format-Table -AutoSize
Write-Host '=== stdout ==='
if (Test-Path 'C:\Users\casey\Desktop\Homesteader\tools\_smoke_stdout.log') { Get-Content 'C:\Users\casey\Desktop\Homesteader\tools\_smoke_stdout.log' -Tail 25 }
Write-Host '=== stderr ==='
if (Test-Path 'C:\Users\casey\Desktop\Homesteader\tools\_smoke_stderr.log') { Get-Content 'C:\Users\casey\Desktop\Homesteader\tools\_smoke_stderr.log' -Tail 15 }
Write-Host '=== nvidia-smi (no path; skip) ==='
$out = 'C:\Users\casey\Desktop\Homesteader\assets\_qwen_local\smoke.png'
if (Test-Path $out) {
    Write-Host ("smoke.png: {0:N2} MB" -f ((Get-Item $out).Length / 1MB))
}
