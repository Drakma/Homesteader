# Background curl 4.99 GB download.
$ErrorActionPreference = 'Continue'
$curlPath = 'C:\Windows\System32\curl.exe'
$url = 'https://huggingface.co/Qwen/Qwen-Image-2.1/resolve/main/text_encoder/model-00001-of-00004.safetensors'
$path = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1\text_encoder\model-00001-of-00004.safetensors'
New-Item -ItemType Directory -Path (Split-Path $path -Parent) -Force | Out-Null

# Delete any partial shard left over.
if (Test-Path $path) { Remove-Item -Force $path }

$t0 = Get-Date
& $curlPath --location --output $path --connect-timeout 30 --max-time 7200 --retry 5 --retry-delay 10 $url *>&1 | Out-Host
$elapsed = (Get-Date) - $t0
Write-Host ("elapsed: {0:N1}s  curl-exit: {1}" -f $elapsed.TotalSeconds, $LASTEXITCODE)
if (Test-Path $path) {
    $sz = (Get-Item $path).Length
    $mbpers = $sz / 1MB / [math]::Max(1, $elapsed.TotalSeconds)
    Write-Host ("size: {0:N2} GB ({1:N1} MB/s avg)" -f ($sz / 1GB), $mbpers)
}
else {
    Write-Host 'no file produced'
}
