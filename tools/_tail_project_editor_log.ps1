Set-Location C:\Users\casey\Desktop\Homesteader
$logPath = "Homesteader\Logs\Editor.log"
if (Test-Path $logPath) {
    Get-Content $logPath -Tail 50
} else {
    Write-Output "No logs in Homesteader\Logs\Editor.log"
}
