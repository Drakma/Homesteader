Set-Location C:\Users\casey\Desktop\Homesteader
Get-ChildItem -Path "Homesteader\Assets" -Recurse -File | Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-3) } | Select-Object FullName, LastWriteTime, Length | Format-Table -AutoSize
