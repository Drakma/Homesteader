# Check whether a diffusers directory already exists in the venv (might be partial).
$cv = 'C:\Users\casey\Desktop\Homesteader\tools\.venv-qwen-image\Lib\site-packages'
$dst = Join-Path $cv 'diffusers'
if (Test-Path $dst) {
    $count = (Get-ChildItem -Recurse -Force $dst 2>$null | Measure-Object).Count
    $size = (Get-ChildItem -Recurse -Force $dst 2>$null | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host ("diffusers dir exists: {0} entries, {1:N1} MB" -f $count, $size)
} else {
    Write-Host 'diffusers dir NOT present'
}
$distInfo = Join-Path $cv 'diffusers-0.41.0.dev0.dist-info'
if (Test-Path $distInfo) {
    Write-Host ("dist-info present: {0}" -f $distInfo)
} else {
    Write-Host 'diffusers-0.41.0.dev0.dist-info NOT present'
}
# The pyproject version file inside diffusers:
$verFile = Join-Path $dst '__init__.py'
if (Test-Path $verFile) {
    Get-Content $verFile -TotalCount 30 | Select-String -Pattern "__version__" | ForEach-Object { $_.Line }
}
