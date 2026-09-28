Set-Location C:\Users\casey\Desktop\Homesteader
$logPath = "Homesteader\Logs\Editor.log"
Select-String -Path $logPath -Pattern "error CS" -Context 0, 1 | Select-Object -Last 10
