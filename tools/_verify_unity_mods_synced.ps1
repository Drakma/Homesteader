Set-Location C:\Users\casey\Desktop\Homesteader
Get-ChildItem -Path "Homesteader\Assets\Mods" -Directory | Select-Object Name, @{Name="Files"; Expression={(Get-ChildItem $_.FullName -Recurse -File).Count}} | Format-Table -AutoSize
