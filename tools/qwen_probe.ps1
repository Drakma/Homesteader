Set-Location C:\Users\casey\Desktop\Homesteader
Write-Output "--- all python processes ---"
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,StartTime,@{Name='CPU_s';Expression={[Math]::Round($_.CPU,1)}},@{Name='WS_MB';Expression={[Math]::Round($_.WorkingSet64/1MB,1)}},Path,CommandLine | Format-Table -AutoSize -Wrap
Write-Output ""
Write-Output "--- more recent stdout (full this time) ---"
Get-Content tools\_smoke_v6_stdout.log
Write-Output ""
Write-Output "--- v6 stderr FULL ---"
$serr = Get-Item tools\_smoke_v6_stderr.log
Write-Output "(size $($serr.Length))"
Get-Content tools\_smoke_v6_stderr.log
