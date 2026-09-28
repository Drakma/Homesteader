Set-Location C:\Users\casey\Desktop\Homesteader
$logPath = "$env:LOCALAPPDATA\Unity\Editor\Editor.log"
Get-Content $logPath -Tail 40
