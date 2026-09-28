Set-Location C:\Users\casey\Desktop\Homesteader
$logPath = "Homesteader\Logs\Editor.log"
if (-not (Test-Path $logPath)) {
    $logPath = "$env:LOCALAPPDATA\Unity\Editor\Editor.log"
}

Write-Output "Checking $logPath for errors and exceptions..."
# Check for compiler errors, exceptions, and fatal issues
Get-Content $logPath -Tail 300 | Select-String -Pattern "error", "exception", "failed" -CaseSensitive:$false | Select-Object -Last 20
