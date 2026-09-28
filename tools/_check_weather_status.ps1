Set-Location C:\Users\casey\Desktop\Homesteader
Write-Output "=== Git Status ==="
& git status -s
Write-Output ""
Write-Output "=== Recent Git Commits ==="
& git log -n 10 --oneline --decorate
Write-Output ""
Write-Output "=== Weather Files in Assets/Scripts or elsewhere ==="
Get-ChildItem -Path "Homesteader\Assets" -Recurse -Filter "*Weather*" -ErrorAction SilentlyContinue | Select-Object FullName, LastWriteTime, Length
