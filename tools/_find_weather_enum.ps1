Set-Location C:\Users\casey\Desktop\Homesteader
Select-String -Path "Homesteader\Assets\Scripts\UI\*.cs", "Homesteader\Assets\Scripts\UI\**\*.cs" -Pattern "enum HomesteaderWeather" -Context 0, 12
