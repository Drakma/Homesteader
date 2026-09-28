Set-Location C:\Users\casey\Desktop\Homesteader
$template = Get-Content "Homesteader\Assets\Resources\HUDTree\KitSprites\weather\weather_snow.png.meta" -Raw
$newGuid = [System.Guid]::NewGuid().ToString("N")
$newMeta = $template -replace 'guid: [a-f0-9]+', "guid: $newGuid"
Set-Content -Path "Homesteader\Assets\Resources\HUDTree\KitSprites\weather\weather_blizzard.png.meta" -Value $newMeta -NoNewline
Write-Output "Created weather_blizzard.png.meta with guid $newGuid"
