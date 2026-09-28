Set-Location C:\Users\casey\Desktop\Homesteader
Get-ChildItem -Path "Homesteader" -Recurse -Filter "*input_file_0.png*" -ErrorAction SilentlyContinue | Select-Object FullName
Get-ChildItem -Path "$env:TEMP" -Recurse -Filter "*input_file_0.png*" -ErrorAction SilentlyContinue | Select-Object FullName
Get-ChildItem -Path "$env:LOCALAPPDATA" -Recurse -Filter "*input_file_0.png*" -ErrorAction SilentlyContinue | Select-Object FullName
