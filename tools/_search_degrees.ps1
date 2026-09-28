Set-Location C:\Users\casey\Desktop\Homesteader
Select-String -Path "Homesteader\Assets\Scripts\UI\*.cs", "Homesteader\Assets\Scripts\UI\**\*.cs" -Pattern "°" | Select-Object Path, LineNumber, Line
Select-String -Path "Homesteader\Assets\Scripts\UI\*.cs", "Homesteader\Assets\Scripts\UI\**\*.cs" -Pattern "FormatTemperature" | Select-Object Path, LineNumber, Line
