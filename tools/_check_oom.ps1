Write-Output "=== Resource-Exhaustion-Detector Events ==="
Get-WinEvent -LogName "Microsoft-Windows-Resource-Exhaustion-Detector/Operational" -ErrorAction SilentlyContinue | Select-Object -First 5 TimeCreated, Id, Message | Format-List
Write-Output "=== System Log Errors/Warnings ==="
Get-WinEvent -FilterHashtable @{LogName='System'; Level=1,2,3; StartTime=(Get-Date).AddMinutes(-15)} -ErrorAction SilentlyContinue | Select-Object -First 5 TimeCreated, Id, ProviderName, Message | Format-List
