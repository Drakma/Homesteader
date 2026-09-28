Set-Location C:\Users\casey\Desktop\Homesteader
Write-Output "--- diffusers-src exists? ---"
if (Test-Path tools\.diffusers-src) {
    Get-ChildItem tools\.diffusers-src | Select-Object Name
    Write-Output ""
    Write-Output "--- has QwenImage21Pipeline? ---"
    Select-String -Path "tools\.diffusers-src\diffusers\pipelines\__init__.py" -Pattern "QwenImage" | Select-Object LineNumber,Line | Select-Object -First 10
    Write-Output ""
    Get-ChildItem "tools\.diffusers-src\diffusers\pipelines" -Directory | Select-Object Name
} else {
    Write-Output "NO tools\.diffusers-src"
}
Write-Output ""
Write-Output "--- recent log tail of install steps ---"
Get-ChildItem tools\_*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name,LastWriteTime,Length
Write-Output ""
Write-Output "--- _step4_download.py head ---"
Get-Content tools\_step4_download.py -TotalCount 80 -ErrorAction SilentlyContinue
Write-Output ""
Write-Output "--- HF cache dirs ---"
if (Test-Path "$env:USERPROFILE\.cache\huggingface") {
    Get-ChildItem "$env:USERPROFILE\.cache\huggingface" -ErrorAction SilentlyContinue | Select-Object Name
} else {
    Write-Output "no HF cache"
}
