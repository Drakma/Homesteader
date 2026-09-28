Set-Location C:\Users\casey\Desktop\Homesteader
Get-ChildItem -Path "." -Recurse -Filter "*.png" | Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-30) } | Select-Object FullName, Length, LastWriteTime
