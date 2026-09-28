# Show recent file writes across BOTH local_dir AND global cache, with
# time-relative-since-now so we can see what's actively downloading.
$now = Get-Date
$globalCache = "$env:USERPROFILE\.cache\huggingface"
$dest = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1'

Write-Host '=== local_dir (most-recently written) ==='
Get-ChildItem -Recurse -Force $dest 2>$null |
    Where-Object { -not $_.PSIsContainer } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 8 |
    ForEach-Object {
        $sec = [int](($now - $_.LastWriteTime).TotalSeconds)
        Write-Host ("{0,-10}  {1,8:N2} GB  {2}" -f ("$sec`s", $_.Length/1GB, $_.FullName.Replace($dest, '')))
    }
Write-Host '=== global cache (most-recently written, last 60s) ==='
Get-ChildItem -Recurse -Force $globalCache -Filter '*.incomplete' -ErrorAction SilentlyContinue 2>$null |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 5 |
    ForEach-Object {
        $sec = [int](($now - $_.LastWriteTime).TotalSeconds)
        Write-Host ("{0,-10}  {1,8:N2} GB  {2}" -f ("$sec`s", $_.Length/1GB, $_.FullName.Replace($globalCache, '')))
    }
