Set-Location C:\Users\casey\Desktop\Homesteader
$lines = Get-Content "Homesteader\Logs\Editor.log"
$lines[($lines.Count - 60)..($lines.Count - 1)]
