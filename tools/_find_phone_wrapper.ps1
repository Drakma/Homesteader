Set-Location C:\Users\casey\Desktop\Homesteader
Get-ChildItem -Path "Homesteader\Assets" -Recurse -Filter "*.uxml" | Select-String -Pattern "PhoneWrapper" | Select-Object Path, LineNumber
