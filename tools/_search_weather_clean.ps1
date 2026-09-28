Set-Location C:\Users\casey\Desktop\Homesteader
Get-ChildItem -Path "." -Recurse -Filter "*weather*" -ErrorAction SilentlyContinue | ForEach-Object {
    [PSCustomObject]@{
        RelPath = $_.FullName.Replace("C:\Users\casey\Desktop\Homesteader\", "")
        LastWrite = $_.LastWriteTime
        Size = $_.Length
    }
} | Format-Table -AutoSize
Get-ChildItem -Path "." -Recurse -Filter "*Weather*" -ErrorAction SilentlyContinue | ForEach-Object {
    [PSCustomObject]@{
        RelPath = $_.FullName.Replace("C:\Users\casey\Desktop\Homesteader\", "")
        LastWrite = $_.LastWriteTime
        Size = $_.Length
    }
} | Format-Table -AutoSize
