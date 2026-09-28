Get-WinEvent -FilterHashtable @{LogName='System'; Level=1,2,3; StartTime=(Get-Date).AddMinutes(-10)} -ErrorAction SilentlyContinue | Select-Object -First 5 TimeCreated, Id, ProviderName, Message | Format-List
Get-WinEvent -LogName "Microsoft-Windows-Resource-Exhaustion-Detector/Operational" -MaxEvents 5 -ErrorAction SilentlyContinue | Select-Object TimeCreated, Id, Message | Format-List
