Set-Location C:\Users\casey\Desktop\Homesteader
$lines = Get-Content "Homesteader\Logs\Editor.log"
# Search backward for compilation errors
$lines | Select-String -Pattern "\.cs\([0-9]+,[0-9]+\): error" | Select-Object -Last 10
