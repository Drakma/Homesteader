# Show the most-recently modified files in the cache to track which one is
# actively being downloaded, and the time it was last touched.
$dest = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1'
Get-ChildItem -Recurse -Force $dest 2>$null |
    Where-Object { -not $_.PSIsContainer } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 5 |
    ForEach-Object {
        $bn = $_.BaseName
        $ext = $_.Extension
        Write-Host ("{0} | {1:N2} GB | {2}" -f $_.LastWriteTime, ($_.Length / 1GB), $_.FullName.Replace($dest, ''))
    }
Write-Host '---'
Get-ChildItem -Recurse -Force $dest -Filter '*.incomplete' 2>$null |
    ForEach-Object {
        Write-Host ("INCOMPLETE: {0:N2} GB | {1}" -f ($_.Length / 1GB), $_.FullName.Replace($dest, ''))
    }
Write-Host '---'
Get-ChildItem -Recurse -Force $dest -Filter '*.lock' 2>$null |
    ForEach-Object {
        Write-Host ("LOCK: {0}" -f $_.FullName.Replace($dest, ''))
    }
