Set-Location C:\Users\casey\Desktop\Homesteader
Write-Output "=== Assets/Scripts files by LastWriteTime ==="
Get-ChildItem -Path "Homesteader\Assets\Scripts" -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 25 FullName, LastWriteTime, Length | Format-Table -AutoSize
