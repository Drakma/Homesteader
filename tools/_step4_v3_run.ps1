# Step 4 v3 run: clean any stale .lock / .incomplete / .metadata under
# local_dir that v1/v2 stalled writes left behind, then run the sequential
# per-file downloader (no parallel workers).

$ErrorActionPreference = 'Stop'
$logPath = 'C:\Users\casey\Desktop\Homesteader\tools\_download_step4.log'
$dest    = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1'

'' | Set-Content -Path $logPath -Encoding utf8
"[step4v3 $(Get-Date -Format 'o') starting]" | Add-Content $logPath

# Clean stale local_dir cache.
$staleCache = Join-Path $dest '.cache'
if (Test-Path $staleCache) {
    "[step4v3 removing $staleCache]" | Add-Content $logPath
    Remove-Item -Recurse -Force $staleCache
}
Get-ChildItem -Path $dest -Recurse -Include '*.lock','*.incomplete','*.metadata' -ErrorAction SilentlyContinue |
    ForEach-Object { Remove-Item -Force -ErrorAction SilentlyContinue }

& "C:\Python313\python.exe" -u "C:\Users\casey\Desktop\Homesteader\tools\_step4_seq.py" *>> $logPath
$rc = $LASTEXITCODE
"[step4v3 $(Get-Date -Format 'o') exit=$rc]" | Add-Content $logPath
exit $rc
