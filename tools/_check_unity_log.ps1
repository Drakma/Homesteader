Set-Location C:\Users\casey\Desktop\Homesteader
$logPath = "Homesteader\Editor.log"
if (-not (Test-Path $logPath)) {
    $logPath = "$env:LOCALAPPDATA\Unity\Editor\Editor.log"
}
if (Test-Path $logPath) {
    Write-Output "Found Unity Editor.log at $logPath"
    Get-Content $logPath -Tail 60 | Select-String -Pattern "error|exception|Weather|Almanac|compiled" -CaseSensitive:$false
} else {
    Write-Output "Editor.log not found"
}
