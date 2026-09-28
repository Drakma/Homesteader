Set-Location C:\Users\casey\Desktop\Homesteader
Get-ChildItem -Path "Homesteader\Assets" -Recurse -Filter "*HudUIBuilder*.cs" | Select-Object FullName
Get-ChildItem -Path "Homesteader\Assets" -Recurse -Filter "*Phone*.cs" | Select-Object FullName
