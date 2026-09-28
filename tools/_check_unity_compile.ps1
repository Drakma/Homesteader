Set-Location C:\Users\casey\Desktop\Homesteader
$logPath = "Homesteader\Logs\Editor.log"
Start-Sleep -Seconds 3
if (Test-Path $logPath) {
    Get-Content $logPath -Tail 60 | Select-String -Pattern "error|exception|Weather|compiled|Compilation" -CaseSensitive:$false
}
