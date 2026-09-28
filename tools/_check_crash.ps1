Set-Location C:\Users\casey\Desktop\Homesteader
Write-Output "=== Windows Event Log Application Errors (last 2 hours) ==="
Get-WinEvent -FilterHashtable @{LogName='Application'; Level=1,2; StartTime=(Get-Date).AddHours(-2)} -ErrorAction SilentlyContinue | Select-Object -First 10 TimeCreated, Id, Message | Format-List

Write-Output "=== Windows Error Reporting (WER) recent files ==="
Get-ChildItem -Path "$env:LOCALAPPDATA\CrashDumps", "C:\ProgramData\Microsoft\Windows\WER\ReportArchive" -Recurse -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 5 FullName, Length, LastWriteTime | Format-List
