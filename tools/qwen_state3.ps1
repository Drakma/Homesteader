Set-Location C:\Users\casey\Desktop\Homesteader
Write-Output "--- _smoke_stderr.log full size + last 60 ---"
$err = Get-Item tools\_smoke_stderr.log
Write-Output "size: $($err.Length)"
Get-Content tools\_smoke_stderr.log -Tail 60
Write-Output ""
Write-Output "--- _smoke_stdout.log full size + last 60 ---"
$out = Get-Item tools\_smoke_stdout.log
Write-Output "size: $($out.Length)"
Get-Content tools\_smoke_stdout.log -Tail 60
Write-Output ""
Write-Output "--- _smoke_step5.log full ---"
$st = Get-Item tools\_smoke_step5.log
Write-Output "size: $($st.Length)"
Get-Content tools\_smoke_step5.log -Tail 40
Write-Output ""
Write-Output "--- ls of assets/_qwen_local ---"
if (Test-Path assets\_qwen_local) {
    Get-ChildItem assets\_qwen_local | Select-Object Name,Length,LastWriteTime
} else {
    Write-Output "no _qwen_local dir yet"
}
Write-Output ""
Write-Output "--- _step4_download.py bottom ---"
Get-Content tools\_step4_download.py -Tail 30
Write-Output ""
Write-Output "--- which _step5_*.ps1 the smoke uses ---"
Get-ChildItem tools\_step5_*.ps1 | Select-Object Name,LastWriteTime
Write-Output ""
Write-Output "--- diffusers git rev inside the cloned source ---"
& git -C "C:\Users\casey\Desktop\Homesteader\tools\.diffusers-src" rev-parse --short HEAD
& git -C "C:\Users\casey\Desktop\Homesteader\tools\.diffusers-src" log -1 --pretty="%h %s %ad" --date=iso
