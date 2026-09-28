Set-Location C:\Users\casey\Desktop\Homesteader
Get-ChildItem -Path "Homesteader\Assets" -Recurse -Filter "*Bootstrap*.cs" | Select-Object FullName
Get-ChildItem -Path "Homesteader\Assets\Scripts" -Recurse -Filter "*.cs" | Select-String -Pattern "class.*Bootstrap" | Select-Object Path, LineNumber, Line
