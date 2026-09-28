# Step 4 v5: use curl.exe directly (one Windows-native binary that handles
# TLS/HTTPS keepalives robustly). One file per invocation; we log per-file
# progress via the on-file size before/after.

$ErrorActionPreference = 'Stop'
$logPath = 'C:\Users\casey\Desktop\Homesteader\tools\_download_step4.log'
$dest    = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1'

'' | Set-Content -Path $logPath -Encoding utf8
"[step4v5 $(Get-Date -Format 'o') starting]" | Add-Content $logPath

# Files left to download (URL, target path).
$downloads = @(
    @{ url = 'https://huggingface.co/Qwen/Qwen-Image-2.1/resolve/main/text_encoder/model-00001-of-00004.safetensors'
       path = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1\text_encoder\model-00001-of-00004.safetensors' }
    @{ url = 'https://huggingface.co/Qwen/Qwen-Image-2.1/resolve/main/text_encoder/model-00003-of-00004.safetensors'
       path = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1\text_encoder\model-00003-of-00004.safetensors' }
    @{ url = 'https://huggingface.co/Qwen/Qwen-Image-2.1/resolve/main/transformer/diffusion_pytorch_model-00001-of-00002.safetensors'
       path = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1\transformer\diffusion_pytorch_model-00001-of-00002.safetensors' }
)

foreach ($d in $downloads) {
    $url  = $d.url
    $path = $d.path
    $dir  = Split-Path $path -Parent
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    $have = if (Test-Path $path) { (Get-Item $path).Length } else { 0 }
    $t0   = Get-Date
    "[{0:HH:mm:ss}] START {1} (have={2:N2} GB)" -f (Get-Date), $path, ($have/1GB) | Add-Content $logPath
    Write-Host "==> $path (have $('{0:N2}' -f ($have/1GB)) GB)"
    # curl --continue-at - : resume from current local bytes (HTTP Range GET)
    # -L follow redirects (HF returns 302 to cloud storage)
    # -sS silent but show errors
    # --connect-timeout 30 --max-time 7200 (2-hour per-file limit)
    # --retry 5 --retry-delay 10
    # --output precise destination
    & curl.exe `
        --continue-at - `
        --location `
        --output $path `
        --connect-timeout 30 `
        --max-time 7200 `
        --retry 5 `
        --retry-delay 10 `
        $url *>> $logPath
    if ($LASTEXITCODE -ne 0) {
        "[{0:HH:mm:ss}] FAIL {1} (curl exit={2})" -f (Get-Date), $path, $LASTEXITCODE | Add-Content $logPath
        Write-Host "    FAIL: curl exit $LASTEXITCODE"
    } else {
        $after = if (Test-Path $path) { (Get-Item $path).Length } else { 0 }
        $elapsed = (Get-Date) - $t0
        $mb_s = ($after - $have) / 1MB / [math]::Max(1, $elapsed.TotalSeconds)
        "[{0:HH:mm:ss}] DONE {1} in {2:N1}s ({3:N1} MB/s, {4:N2} GB total)" -f `
            (Get-Date), $path, $elapsed.TotalSeconds, $mb_s, ($after/1GB) | Add-Content $logPath
        Write-Host ("    DONE in {0:N1}s ({1:N1} MB/s, {2:N2} GB)" -f $elapsed.TotalSeconds, $mb_s, ($after/1GB))
    }
}

"[step4v5 $(Get-Date -Format 'o') done]" | Add-Content $logPath
