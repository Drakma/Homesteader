Set-Location C:\Users\casey\Desktop\Homesteader
$lines = Get-Content "Homesteader\Assets\Scripts\UI\ToastNotificationSystem.cs"
Write-Output "Total lines: $($lines.Count)"
$lines[230..($lines.Count - 1)]
