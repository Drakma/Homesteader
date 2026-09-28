$src = 'C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\UI\Atlases'
$dst = 'C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\HUDTree\KitSprites\panels'

if (-not (Test-Path $dst)) { New-Item -ItemType Directory -Path $dst -Force | Out-Null }

Copy-Item -Path (Join-Path $src 'header_strip.png') -Destination (Join-Path $dst 'header_strip.png')
Copy-Item -Path (Join-Path $src 'well.png')           -Destination (Join-Path $dst 'well.png')
Copy-Item -Path (Join-Path $src 'window_frame.png')   -Destination (Join-Path $dst 'window_frame.png')

Get-Item (Join-Path $dst 'header_strip.png') | Select-Object Length
