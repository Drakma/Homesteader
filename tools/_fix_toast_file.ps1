Set-Location C:\Users\casey\Desktop\Homesteader
$lines = Get-Content "Homesteader\Assets\Scripts\UI\ToastNotificationSystem.cs"
$first240 = $lines[0..239]
Set-Content -Path "Homesteader\Assets\Scripts\UI\ToastNotificationSystem.cs" -Value $first240
Write-Output "Truncated file to clean 240 lines"
