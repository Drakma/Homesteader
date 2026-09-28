Set-Location C:\Users\casey\Desktop\Homesteader
Select-String -Path "Homesteader\Assets\Scripts\UI\*.cs", "Homesteader\Assets\UI\Scripts\*.cs" -Pattern "PhoneController" | Select-Object Path, LineNumber, Line
