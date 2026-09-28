Start-Sleep -Seconds 30
# Move to background to avoid 120s foreground budget entirely.
$sout = 'C:\Users\casey\Desktop\Homesteader\tools\_smoke_stdout.log'
$serr = 'C:\Users\casey\Desktop\Homesteader\tools\_smoke_stderr.log'
$std = Get-Content $sout -Tail 20
Write-Host '=== stdout ==='
$std
Write-Host '=== stderr ==='
Get-Content $serr -Tail 10
$proc = Get-Process -Name 'python','conhost','cmd' -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -gt (Get-Date).AddMinutes(-15) }
Write-Host '=== process ==='
$proc | Select-Object Id, Name, CPU, WS | Format-Table -AutoSize
$outFile = 'C:\Users\casey\Desktop\Homesteader\assets\_qwen_local\smoke.png'
if (Test-Path $outFile) {
    Write-Host ("smoke.png already exists: {0} B" -f (Get-Item $outFile).Length)
}
