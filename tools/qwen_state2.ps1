Set-Location C:\Users\casey\Desktop\Homesteader
Write-Output "--- src layout of diffusers-src ---"
$srcDiff = "tools\.diffusers-src\src\diffusers"
if (Test-Path $srcDiff) {
    Get-ChildItem $srcDiff | Select-Object Name
    Write-Output "--- pipelines folder ---"
    Get-ChildItem "$srcDiff\pipelines" -Directory | Select-Object Name
    Write-Output "--- qwen pipeline files ---"
    Get-ChildItem "$srcDiff\pipelines" -Filter "*qwen*" -Recurse -ErrorAction SilentlyContinue | Select-Object FullName
    Get-ChildItem "$srcDiff\pipelines" -Directory | Where-Object { $_.Name -like "*qwen*" } | Select-Object FullName
}
Write-Output ""
Write-Output "--- _download_step4.log tail ---"
Get-Content tools\_download_step4.log -Tail 30 -ErrorAction SilentlyContinue
Write-Output ""
Write-Output "--- _smoke_step5.log tail ---"
Get-Content tools\_smoke_step5.log -Tail 30 -ErrorAction SilentlyContinue
Write-Output ""
Write-Output "--- _smoke_stderr.log tail ---"
Get-Content tools\_smoke_stderr.log -Tail 30 -ErrorAction SilentlyContinue
Write-Output ""
Write-Output "--- _smoke_stdout.log tail ---"
Get-Content tools\_smoke_stdout.log -Tail 30 -ErrorAction SilentlyContinue
Write-Output ""
Write-Output "--- _system_install.log tail ---"
Get-Content tools\_system_install.log -Tail 30 -ErrorAction SilentlyContinue
Write-Output ""
Write-Output "--- C:\Users\casey\Desktop\models dir ---"
if (Test-Path "C:\Users\casey\Desktop\models") { Get-ChildItem "C:\Users\casey\Desktop\models" | Select-Object Name } else { Write-Output "no models dir" }
