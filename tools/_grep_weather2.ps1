Set-Location C:\Users\casey\Desktop\Homesteader
Select-String -Path "Homesteader\Assets\Scripts\*.cs", "Homesteader\Assets\Scripts\**\*.cs" -Pattern "WeatherEffectsManager" | ForEach-Object { "$($_.Filename):$($_.LineNumber)  $($_.Line)" }
Write-Output "---"
Select-String -Path "Homesteader\Assets\Scripts\*.cs", "Homesteader\Assets\Scripts\**\*.cs" -Pattern "HomesteaderWeather" | ForEach-Object { "$($_.Filename):$($_.LineNumber)  $($_.Line)" }
