Set-Location C:\Users\casey\Desktop\Homesteader
Get-ChildItem -Path "C:\Users\casey\Downloads" -Filter "*app*" | Select-Object FullName, Length, LastWriteTime
