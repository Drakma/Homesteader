# Inspect first 16 bytes of venv Scripts/python.exe
$path = 'C:\Users\casey\Desktop\Homesteader\tools\.venv-qwen-image\Scripts\python.exe'
$bytes = [System.IO.File]::ReadAllBytes($path)[0..15]
$hex = ($bytes | ForEach-Object { $_.ToString('X2') }) -join ' '
Write-Host ("first 16 bytes: {0}" -f $hex)
Write-Host ("file length: {0}" -f (Get-Item $path).Length)
