Start-Sleep -Seconds 90
Write-Host '=== curl processes ==='
Get-Process curl -ErrorAction SilentlyContinue | Select-Object Id, CPU, WS, StartTime | Format-Table -AutoSize

$dest = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1'
$targets = @(
    'C:\Users\casey\Desktop\models\Qwen-Image-2.1\text_encoder\model-00003-of-00004.safetensors'
    'C:\Users\casey\Desktop\models\Qwen-Image-2.1\transformer\diffusion_pytorch_model-00001-of-00002.safetensors'
)
foreach ($t in $targets) {
    if (Test-Path $t) {
        $sz = (Get-Item $t).Length
        Write-Host ("{0}: {1:N2} GB / ~9.97 GB target" -f (Split-Path $t -Leaf), ($sz / 1GB))
    } else {
        Write-Host ("{0}: not present" -f (Split-Path $t -Leaf))
    }
}
$total = (Get-ChildItem -Recurse -Force $dest 2>$null | Measure-Object -Property Length -Sum).Sum
Write-Host ("local_dir total: {0:N2} GB" -f ($total / 1GB))
