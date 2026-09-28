$log = "C:\Users\casey\Desktop\Homesteader\_procgen_test\_hunyuandit_smoke.log"
$err = "C:\Users\casey\Desktop\Homesteader\_procgen_test\_hunyuandit_smoke.log.err"
$job = Start-Process -FilePath "C:\Python313\python.exe" -ArgumentList @("-u", "C:\Users\casey\Desktop\Homesteader\_procgen_test\_smoke_hunyuandit.py") -RedirectStandardOutput $log -RedirectStandardError $err -WindowStyle Hidden -PassThru
Set-Location "C:\Users\casey\Desktop\Homesteader\_procgen_test"
Write-Output ("PID=" + $job.Id)
