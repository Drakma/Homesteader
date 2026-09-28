Set-Location C:\Users\casey\Desktop\Homesteader
Write-Output "--- python processes ---"
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,StartTime,@{Name='CPU_s';Expression={[Math]::Round($_.CPU,1)}},@{Name='WS_MB';Expression={[Math]::Round($_.WorkingSet64/1MB,1)}}
Write-Output ""
Write-Output "--- nvidia-smi (brief) ---"
$nvidia = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($nvidia) { & nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv | Select-Object -First 8 } else { Write-Output "(no nvidia-smi)" }
Write-Output ""
Write-Output "--- _smoke_v6 stdout tail 40 ---"
Get-Content tools\_smoke_v6_stdout.log -Tail 40 -ErrorAction SilentlyContinue
Write-Output ""
Write-Output "--- _smoke_v6 stderr tail 40 ---"
Get-Content tools\_smoke_v6_stderr.log -Tail 40 -ErrorAction SilentlyContinue
Write-Output ""
Write-Output "--- output PNG check ---"
if (Test-Path assets\_qwen_local\smoke_v6.png) {
    $p = Get-Item assets\_qwen_local\smoke_v6.png
    Write-Output "PNG: $($p.FullName)  size=$($p.Length) bytes  mtime=$($p.LastWriteTime)"
} else {
    Write-Output "no PNG yet"
}
