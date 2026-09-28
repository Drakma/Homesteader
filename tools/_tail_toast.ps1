Set-Location C:\Users\casey\Desktop\Homesteader
$lines = Get-Content "Homesteader\Assets\Scripts\UI\ToastNotificationSystem.cs"
$lines[225..($lines.Count - 1)] | ForEach-Object { "$_" }
