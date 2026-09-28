Set-Location C:\Users\casey\Desktop\Homesteader
Get-ChildItem -Path "Homesteader\Assets" -Recurse -File | Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-3) } | ForEach-Object {
    [PSCustomObject]@{
        RelPath = $_.FullName.Replace("C:\Users\casey\Desktop\Homesteader\Homesteader\", "")
        LastWrite = $_.LastWriteTime
        Size = $_.Length
    }
} | Format-Table -AutoSize
