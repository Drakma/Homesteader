Set-Location C:\Users\casey\Desktop\Homesteader
Get-ChildItem -Path "C:\Users\casey\Desktop" -File | Where-Object { $_.Extension -match "png|jpg|jpeg|webp" } | Select-Object FullName, LastWriteTime
Get-ChildItem -Path "C:\Users\casey\Downloads" -File | Where-Object { $_.Extension -match "png|jpg|jpeg|webp" } | Sort-Object LastWriteTime -Descending | Select-Object -First 10 FullName, LastWriteTime
