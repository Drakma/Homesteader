# Direct test of git clone from GitHub. Bypasses pip's wrapper layer.
$ErrorActionPreference = 'Continue'
$env:Path = 'C:\Program Files\Git\bin;' + $env:Path
$dest = 'C:\Users\casey\Desktop\Homesteader\tools\_git_clone_test'
if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
Write-Host 'Clone start'
$t0 = Get-Date
& git clone --filter=blob:none --depth=1 https://github.com/huggingface/diffusers $dest 2>&1 | Tee-Object -Variable gitOut | Out-Host
$t1 = Get-Date
Write-Host ("Clone elapsed: {0}s" -f [int](($t1 - $t0).TotalSeconds))
Write-Host ("Last line: " + ($gitOut | Select-Object -Last 1))
if (Test-Path $dest) {
    $size = (Get-ChildItem $dest -Recurse -Force | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host ("Size on disk: {0:N1} MB" -f $size)
    Remove-Item -Recurse -Force $dest
}
