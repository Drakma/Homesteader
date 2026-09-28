Set-Location C:\Users\casey\Desktop\Homesteader
$recents = Get-ChildItem -Path "$env:USERPROFILE" -Include "*.jpg","*.png","*.webp" -File -Recurse -Depth 2 -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 15 FullName, LastWriteTime
$recents | Format-Table -AutoSize
