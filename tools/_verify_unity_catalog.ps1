Set-Location C:\Users\casey\Desktop\Homesteader
Get-ChildItem -Path "Homesteader\Assets\AssetCatalog" -Directory | Select-Object Name, @{Name="Items"; Expression={(Get-ChildItem $_.FullName -Directory).Count}} | Format-Table -AutoSize
