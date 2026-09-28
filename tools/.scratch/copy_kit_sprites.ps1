$src = 'C:\Users\casey\Desktop\Homesteader\assets\hud_kit\sprites'
$dst = 'C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\HUDTree\KitSprites'

if (-not (Test-Path $dst)) { New-Item -ItemType Directory -Path $dst -Force | Out-Null }

function Copy-Kit {
    param([string]$Sub)
    $fullSrc = Join-Path $src $Sub
    if (-not (Test-Path $fullSrc)) { return }
    Get-ChildItem $fullSrc -File -Filter '*.png' | Copy-Item -Destination (Join-Path $dst $Sub) -Force
}

Copy-Kit 'vitals'
Copy-Kit 'resources'
Copy-Kit 'panels'
Copy-Kit 'buttons'
Copy-Kit 'speed_controls'
Copy-Kit 'toolbar_slots'
Copy-Kit 'decor'
Copy-Kit 'status_windows'

# header_strip background image (procedural, in source tree baked by python).
$header_png = 'C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\UI\Atlases\header_strip.png'
if (-not (Test-Path $header_png)) {
    # Generate via the existing baker.
    python 'C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\UI\bake_atlases.py' 2>&1 | Out-Null
    Copy-Item -Path 'C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\UI\Atlases\header_strip.png' -Destination (Join-Path $dst 'panels\header_strip.png')
}

# well texture (background for status wells)
if (-not (Test-Path 'C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\UI\Atlases\well.png')) {
    python 'C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\UI\bake_atlases.py' 2>&1 | Out-Null
}
if (Test-Path 'C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\UI\Atlases\well.png') {
    Copy-Item -Path 'C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\UI\Atlases\well.png' -Destination (Join-Path $dst 'header_strip_well.png')
}

Write-Output ('--- contents of ' + $dst + ' ---')
Get-ChildItem $dst -Recurse -File | Select-Object Length, FullName | Format-Table AutoSize
