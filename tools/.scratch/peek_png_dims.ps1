$files = @(
    'vital_atlas_kit',
    'resource_atlas_kit',
    'slot_atlas_kit',
    'decor_atlas_kit',
    'button_atlas_kit'
)
foreach ($f in $files) {
    $path = "C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\HUDTree\Atlases\Kit\$f.png"
    $bytes = [System.IO.File]::ReadAllBytes($path)
    $wB = $bytes[16..19] | ForEach-Object { '{0:X2}' -f $_ }
    $hB = $bytes[20..23] | ForEach-Object { '{0:X2}' -f $_ }
    Write-Output "$f : width=$($wB -join '') height=$($hB -join '')"
}
