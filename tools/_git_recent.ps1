Set-Location C:\Users\casey\Desktop\Homesteader
$gitCmd = "C:\Program Files\Git\cmd\git.exe"
Write-Output "=== Recent 5 Commits ==="
& $gitCmd log -n 5 --oneline --decorate
Write-Output ""
Write-Output "=== Git commits mentioning weather ==="
& $gitCmd log --grep="weather" -i -n 5 --oneline
& $gitCmd log --grep="Weather" -n 5 --oneline
Write-Output ""
Write-Output "=== WeatherEffectsManager.cs git status ==="
& $gitCmd status Homesteader/Assets/Scripts/WeatherEffectsManager.cs
