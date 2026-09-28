# Diagnose the state of the venv after step 2 attempt.
Write-Host '=== venv site-packages ==='
$pkgs = 'torch','transformers','accelerate','diffusers','huggingface_hub','pip','numpy','safetensors'
Get-ChildItem 'C:\Users\casey\Desktop\Homesteader\tools\.venv-qwen-image\Lib\site-packages' -Directory -ErrorAction SilentlyContinue |
    Where-Object { $pkgs -contains $_.Name } |
    Select-Object Name, LastWriteTime |
    Sort-Object Name |
    Format-Table -AutoSize
Write-Host '=== still-running processes ==='
Get-Process powershell, python -ErrorAction SilentlyContinue |
    Where-Object { $_.CPU -gt 0.05 } |
    Select-Object Id, ProcessName, CPU, StartTime |
    Format-Table -AutoSize
Write-Host '=== log tail ==='
$log = 'C:\Users\casey\Desktop\Homesteader\tools\_pip_step2.log'
if (Test-Path $log) {
    Get-Content $log -Tail 12
}
