Set-Location C:\Users\casey\Desktop\Homesteader
Get-ChildItem -Path "." -Recurse -Filter "*weather*" -ErrorAction SilentlyContinue | Select-Object FullName, LastWriteTime, Length | Format-Table -AutoSize
Get-ChildItem -Path "." -Recurse -Filter "*Weather*" -ErrorAction SilentlyContinue | Select-Object FullName, LastWriteTime, Length | Format-Table -AutoSize
