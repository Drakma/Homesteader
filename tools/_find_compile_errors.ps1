Set-Location C:\Users\casey\Desktop\Homesteader
$logPath = "Homesteader\Logs\Editor.log"
Select-String -Path $logPath -Pattern "PhoneController.cs\([0-9]+,[0-9]+\): error" -Context 0, 1 | Select-Object -Last 10
