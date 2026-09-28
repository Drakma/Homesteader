Set-Location C:\Users\casey\Desktop\Homesteader
Select-String -Path "Homesteader\Assets\Scripts\*.cs", "Homesteader\Assets\Scripts\**\*.cs" -Pattern "WeatherEffectsManager" | Select-Object Path, LineNumber, Line
Select-String -Path "Homesteader\Assets\Scripts\*.cs", "Homesteader\Assets\Scripts\**\*.cs" -Pattern "HomesteaderWeather" | Select-Object Path, LineNumber, Line
