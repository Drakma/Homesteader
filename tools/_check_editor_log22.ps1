Set-Location C:\Users\casey\Desktop\Homesteader
$logPath = "Homesteader\Logs\Editor.log"
Start-Sleep -Seconds 3
Get-Content $logPath -Tail 50 | Select-String -Pattern "error", "exception", "failed" -CaseSensitive:$false
