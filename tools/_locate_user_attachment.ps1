Set-Location C:\Users\casey\Desktop\Homesteader
Get-ChildItem -Path "." -Recurse -Filter "*input_file_*" -ErrorAction SilentlyContinue | Select-Object FullName
Get-ChildItem -Path "$env:TEMP", "$env:USERPROFILE\AppData\Local\Temp" -Recurse -Filter "*input_file_*" -ErrorAction SilentlyContinue | Select-Object FullName
Get-ChildItem -Path "$env:USERPROFILE" -Filter "*.jpg", "*.png", "*.webp" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 10 FullName, LastWriteTime
