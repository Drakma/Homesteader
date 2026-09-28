Set-Location C:\Users\casey\Desktop\Homesteader
$recents = Get-ChildItem -Path "$env:TEMP", "$env:USERPROFILE\AppData\Local", "$env:USERPROFILE\Desktop", "$env:USERPROFILE\Downloads" -Recurse -Filter "*.png" -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-60) } | Select-Object -First 30 FullName, LastWriteTime
$recents | Format-Table -AutoSize
