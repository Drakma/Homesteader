$sout = 'C:\Users\casey\Desktop\Homesteader\tools\_test_mem_stdout.log'
$serr = 'C:\Users\casey\Desktop\Homesteader\tools\_test_mem_stderr.log'
'' | Set-Content $sout -Encoding utf8
'' | Set-Content $serr -Encoding utf8

$proc = Start-Process -FilePath 'C:\Python313\python.exe' -ArgumentList @('-u', 'C:\Users\casey\Desktop\Homesteader\tools\_test_mem.py') -RedirectStandardOutput $sout -RedirectStandardError $serr -WorkingDirectory 'C:\Python313' -NoNewWindow -PassThru
Write-Host "Started PID $($proc.Id)"
$proc.WaitForExit()
Write-Host "Exit Code: $($proc.ExitCode)"
Get-Content $sout
Get-Content $serr
