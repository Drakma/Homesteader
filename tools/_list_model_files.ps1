Get-ChildItem -Path "C:\Users\casey\Desktop\models\Qwen-Image-2.1" -Recurse | Select-Object FullName, Length | Format-Table -AutoSize
