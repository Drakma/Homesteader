Set-Location C:\Users\casey\Desktop\Homesteader
$logPath = "Homesteader\Logs\Editor.log"
Start-Sleep -Seconds 5
Get-Content $logPath -Tail 50 | Select-String -Pattern "error", "exception", "AssetCatalog" -CaseSensitive:$false
