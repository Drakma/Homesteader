Set-Location C:\Users\casey\Desktop\Homesteader
$logPath = "Homesteader\Logs\Editor.log"
if (Test-Path $logPath) {
    Get-Content $logPath -Tail 80
}
