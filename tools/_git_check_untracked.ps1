Set-Location C:\Users\casey\Desktop\Homesteader
$gitCmd = "C:\Program Files\Git\cmd\git.exe"
Write-Output "=== Untracked files mentioning weather or recent ==="
& $gitCmd status --ignored=no -uall | Select-String -Pattern "Weather|weather"
Write-Output "=== Git check-ignore ==="
& $gitCmd check-ignore -v "Homesteader/Assets/Scripts/WeatherEffectsManager.cs"
