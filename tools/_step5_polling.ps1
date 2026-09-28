# Quick stateless poll, doesn't sleep.
$proc = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -gt (Get-Date).AddMinutes(-15) }
if ($proc) {
    Write-Host ("Python PID {0} CPU {1:N2}s WS {2:N1}MB elapsed {3:N0}s" -f $proc.Id, $proc.CPU, ($proc.WS/1MB), ((Get-Date) - $proc.StartTime).TotalSeconds)
} else {
    Write-Host 'No python in flight.'
}
Write-Host '--- stdout ---'
$std = 'C:\Users\casey\Desktop\Homesteader\tools\_smoke_stdout.log'
if (Test-Path $std) { Get-Content $std -Tail 30 }
Write-Host '--- stderr ---'
$se = 'C:\Users\casey\Desktop\Homesteader\tools\_smoke_stderr.log'
if (Test-Path $se) { Get-Content $se -Tail 30 }
$outFile = 'C:\Users\casey\Desktop\Homesteader\assets\_qwen_local\smoke.png'
if (Test-Path $outFile) {
    Write-Host ("smoke.png EXISTS: {0:N2} MB" -f ((Get-Item $outFile).Length / 1MB))
} else {
    Write-Host 'smoke.png not yet produced'
}
