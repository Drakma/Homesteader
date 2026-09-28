# Poll the 2 background curl downloads.
$dest = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1'
$targets = @(
    'C:\Users\casey\Desktop\models\Qwen-Image-2.1\text_encoder\model-00003-of-00004.safetensors'
    'C:\Users\casey\Desktop\models\Qwen-Image-2.1\transformer\diffusion_pytorch_model-00001-of-00002.safetensors'
)
foreach ($t in $targets) {
    if (Test-Path $t) {
        $sz = (Get-Item $t).Length
        $mb = [math]::Round($sz / 1MB, 1)
        $gb = [math]::Round($sz / 1GB, 2)
        Write-Host ("{0}: {1:N2} GB ({2:N1} MB)" -f (Split-Path $t -Leaf), $gb, $mb)
    } else {
        Write-Host ("{0}: not present" -f (Split-Path $t -Leaf))
    }
}
Write-Host '---'
Write-Host 'curl processes:'
Get-Process curl -ErrorAction SilentlyContinue | Select-Object Id, CPU, WS, StartTime | Format-Table -AutoSize
Write-Host '---'
Write-Host ("overall local_dir: {0:N2} GB" -f ((Get-ChildItem -Recurse -Force $dest 2>$null | Measure-Object -Property Length -Sum).Sum / 1GB))
