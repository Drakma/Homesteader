Set-Location C:\Users\casey\Desktop\Homesteader
$mcpLog = (Get-Item "C:\Users\casey\Desktop\Homesteader\tools\.scratch\*" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 10)
$mcpLog | Select-Object Name, LastWriteTime, Length | Format-Table -AutoSize
