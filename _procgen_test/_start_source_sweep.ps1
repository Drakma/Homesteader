$log = "C:\Users\casey\Desktop\Homesteader\_procgen_test\_sweep_source.log"
$err = "C:\Users\casey\Desktop\Homesteader\_procgen_test\_sweep_source.log.err"
$job = Start-Process -FilePath "C:\Python313\python.exe" -ArgumentList @("-u", "C:\Users\casey\Desktop\Homesteader\_procgen_test\_sweep_source.py") -RedirectStandardOutput $log -RedirectStandardError $err -WindowStyle Hidden -PassThru
Set-Location "C:\Users\casey\Desktop\Homesteader\_procgen_test"
Write-Output ("PID=" + $job.Id)
