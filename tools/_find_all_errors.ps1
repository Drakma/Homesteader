Set-Location C:\Users\casey\Desktop\Homesteader
$logPath = "Homesteader\Logs\Editor.log"
Select-String -Path $logPath -Pattern ": error CS" -Context 1, 2 | Select-Object -Last 10
