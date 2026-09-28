Set-Location C:\Users\casey\Desktop\Homesteader
$lines = Get-Content "Homesteader\Logs\Editor.log"
# Search backward for compilation finish
$lines | Select-String -Pattern "Compilation.*finished|Compiling scripts|Domain Reload" -CaseSensitive:$false | Select-Object -Last 10
