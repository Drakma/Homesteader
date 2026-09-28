Get-ChildItem -Path "C:\Users\casey\Desktop\models\Qwen-Image-2.1" -Recurse | Select-Object FullName, @{Name="Size_GB"; Expression={[Math]::Round($_.Length / 1GB, 3)}} | Format-List
