# What's in the global HF cache?
$gc = "$env:USERPROFILE\.cache\huggingface"
if (-not (Test-Path $gc)) {
    Write-Host 'global cache not present'
    return
}
Write-Host '=== hub/models--Qwen--Qwen-Image-2.1 ==='
$repoCache = Join-Path $gc 'hub\models--Qwen--Qwen-Image-2.1'
if (Test-Path $repoCache) {
    $blobs = Join-Path $repoCache 'blobs'
    if (Test-Path $blobs) {
        $n = (Get-ChildItem -Recurse -Force $blobs | Measure-Object).Count
        $sz = (Get-ChildItem -Recurse -Force $blobs | Measure-Object -Property Length -Sum).Sum / 1GB
        Write-Host ("blobs: {0} files, {1:N2} GB" -f $n, $sz)
    }
    $snap = Join-Path $repoCache 'refs'
    if (Test-Path $snap) {
        $refNames = (Get-ChildItem $snap).Name -join ','
        Write-Host ("refs: {0}" -f $refNames)
    }
    $locks = Join-Path $repoCache '.locks'
    if (Test-Path $locks) { Write-Host "locks present" }
}
