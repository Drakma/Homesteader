Get-WinEvent -FilterHashtable @{LogName='Application'; Level=1,2; StartTime=(Get-Date).AddMinutes(-10)} -ErrorAction SilentlyContinue | Select-Object -First 5 TimeCreated, Id, Message | Format-List
Get-ChildItem -Path "$env:LOCALAPPDATA\CrashDumps" -Recurse -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 3 FullName, Length, LastWriteTime | Format-List
