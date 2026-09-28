Get-ChildItem -Path "C:\Users\casey\Desktop\models\Qwen-Image-2.1" -Recurse | Where-Object { -not $_.PSIsContainer } | ForEach-Object {
    [PSCustomObject]@{
        Name = $_.FullName.Replace("C:\Users\casey\Desktop\models\Qwen-Image-2.1\", "")
        Size_MB = [Math]::Round($_.Length / 1MB, 2)
    }
} | Format-Table -AutoSize
