$sout = 'C:\Users\casey\Desktop\Homesteader\tools\_debug_stdout.log'
$serr = 'C:\Users\casey\Desktop\Homesteader\tools\_debug_stderr.log'
'' | Set-Content $sout -Encoding utf8
'' | Set-Content $serr -Encoding utf8

$proc = Start-Process -FilePath 'C:\Python313\python.exe' -ArgumentList @('-u', 'C:\Users\casey\Desktop\Homesteader\tools\_debug_qwen.py') -RedirectStandardOutput $sout -RedirectStandardError $serr -WorkingDirectory 'C:\Python313' -NoNewWindow -PassThru
Write-Host "Started PID $($proc.Id)"
$proc.WaitForExit()
Write-Host "Exit Code: $($proc.ExitCode)"
Write-Host "=== stdout ==="
Get-Content $sout
Write-Host "=== stderr ==="
Get-Content $serr
