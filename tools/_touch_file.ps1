Set-Location C:\Users\casey\Desktop\Homesteader
$file = "Homesteader\Assets\Scripts\UI\Phone\PhoneController.cs"
(Get-Item $file).LastWriteTime = Get-Date
Write-Output "Touched $file"
