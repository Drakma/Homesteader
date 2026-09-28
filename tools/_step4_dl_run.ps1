# Step 4 v2: clean stale download state, then re-run snapshot_download.
# Lessons from v1: stuck silently after writing 11 GB of partial text_encoder
# shards. We will:
#   1. delete the .cache subdir entirely so the next snapshot doesn't fight
#      the .incomplete files from the failed run
#   2. delete any leftover .lock / .incomplete / .metadata files (these are
#      coordinator state; if a run was killed, they need to be cleared)
#   3. restart with output redirected via *> (no pipe -> no SIGPIPE)

$ErrorActionPreference = 'Stop'
$logPath = 'C:\Users\casey\Desktop\Homesteader\tools\_download_step4.log'
$dest = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1'

'' | Set-Content -Path $logPath -Encoding utf8
"[step4v2 $(Get-Date -Format 'o') starting]" | Add-Content $logPath

$staleCache = Join-Path $dest '.cache'
if (Test-Path $staleCache) {
  "[step4v2 removing $staleCache]" | Add-Content $logPath
  Remove-Item -Recurse -Force $staleCache
}

Get-ChildItem -Path $dest -Recurse -Include '*.lock', '*.incomplete', '*.metadata' -ErrorAction SilentlyContinue |
ForEach-Object { Remove-Item -Force -ErrorAction SilentlyContinue }

& "C:\Python313\python.exe" -u "C:\Users\casey\Desktop\Homesteader\tools\_step4_download.py" *>> $logPath
$rc = $LASTEXITCODE
"[step4v2 $(Get-Date -Format 'o') exit=$rc]" | Add-Content $logPath
exit $rc
