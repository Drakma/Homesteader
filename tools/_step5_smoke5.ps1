# Step 5 v5: launch via .bat (no PS escaping problems).
$ErrorActionPreference = 'Continue'

$sout = 'C:\Users\casey\Desktop\Homesteader\tools\_smoke_stdout.log'
$serr = 'C:\Users\casey\Desktop\Homesteader\tools\_smoke_stderr.log'
'' | Set-Content $sout -Encoding utf8
'' | Set-Content $serr -Encoding utf8

$proc = Start-Process `
    -FilePath 'C:\Users\casey\Desktop\Homesteader\tools\_step5_smoke.bat' `
    -WorkingDirectory 'C:\Python313' `
    -NoNewWindow `
    -RedirectStandardOutput $sout `
    -RedirectStandardError  $serr `
    -PassThru
Write-Host ("Spawned batch PID {0}" -f $proc.Id)
exit 0
