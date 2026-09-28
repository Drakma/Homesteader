Set-Location C:\Users\casey\Desktop\Homesteader
$lines = Get-Content "Homesteader\Logs\Editor.log"
Write-Output "Total log lines: $($lines.Count)"
$lines[($lines.Count - 60)..($lines.Count - 1)] | Select-String -Pattern "error|exception|Reloading|domain" -CaseSensitive:$false
