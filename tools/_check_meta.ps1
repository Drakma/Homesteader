Set-Location C:\Users\casey\Desktop\Homesteader
Get-ChildItem -Path "Homesteader\Assets\Resources\WeatherFX" | Select-Object Name, Length, LastWriteTime
Get-Content "Homesteader\Assets\Resources\WeatherFX\tex_snowflake.png.meta" -ErrorAction SilentlyContinue
