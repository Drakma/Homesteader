Set-Location C:\Users\casey\Desktop\Homesteader
Write-Output "--- tools/ ---"
Get-ChildItem tools | Select-Object Name
Write-Output ""
Write-Output "--- files mentioning qwen ---"
Get-ChildItem -Recurse -File -Filter "*qwen*" | Select-Object FullName
Write-Output ""
Write-Output "--- README / docs mentioning qwen ---"
Select-String -Path (Get-ChildItem -Recurse -File -Include *.md,*.py,*.json | Select-Object -ExpandProperty FullName) -Pattern "qwen" -SimpleMatch | Select-Object Path,LineNumber | Select-Object -First 40
