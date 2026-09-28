# Step 4 v4: raw HTTP download via requests (bypass huggingface_hub's stalled
# higher-level helpers). Clean stale local_dir cache state first.
$ErrorActionPreference = 'Stop'
$logPath = 'C:\Users\casey\Desktop\Homesteader\tools\_download_step4.log'
$dest    = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1'

'' | Set-Content -Path $logPath -Encoding utf8
"[step4v4 $(Get-Date -Format 'o') starting]" | Add-Content $logPath

$staleCache = Join-Path $dest '.cache'
if (Test-Path $staleCache) {
    "[step4v4 removing $staleCache]" | Add-Content $logPath
    Remove-Item -Recurse -Force $staleCache
}
Get-ChildItem -Path $dest -Recurse -Include '*.lock','*.incomplete','*.metadata' -ErrorAction SilentlyContinue |
    ForEach-Object { Remove-Item -Force -ErrorAction SilentlyContinue }

# Use python.exe -u for unbuffered output so the progress lines flush.
& "C:\Python313\python.exe" -u "C:\Users\casey\Desktop\Homesteader\tools\_step4_raw.py" *>> $logPath
$rc = $LASTEXITCODE
"[step4v4 $(Get-Date -Format 'o') exit=$rc]" | Add-Content $logPath
exit $rc
