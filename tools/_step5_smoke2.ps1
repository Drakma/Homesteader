# Step 5 retry: smoke-test using local-dir weights and HF_HUB_OFFLINE=1
# to skip all network activity.
$ErrorActionPreference = 'Stop'
$logPath = 'C:\Users\casey\Desktop\Homesteader\tools\_smoke_step5.log'
$outDir  = 'C:\Users\casey\Desktop\Homesteader\assets\_qwen_local'
$modelDir = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1'

New-Item -ItemType Directory -Path $outDir -Force | Out-Null
'' | Set-Content -Path $logPath -Encoding utf8

'[step5 retry $(Get-Date -Format "o")] starting with local-dir weights; HF_HUB_OFFLINE=1' | Add-Content $logPath

# Run without `2>&1` piping — it's the pipe that was killing us under the
# 120s foreground timeout. Direct stdout/stderr to files we can tail.
$stdOut = 'C:\Users\casey\Desktop\Homesteader\tools\_smoke_stdout.log'
$stdErr = 'C:\Users\casey\Desktop\Homesteader\tools\_smoke_stderr.log'
'' | Set-Content -Path $stdOut -Encoding utf8
'' | Set-Content -Path $stdErr -Encoding utf8

$env:HF_HUB_OFFLINE  = '1'
$env:TRANSFORMERS_OFFLINE = '1'

$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
$env:HF_TOKEN = $null  # we have no token; offline mode

# Write to stdout/stderr files directly.
& "C:\Python313\python.exe" -u "C:\Users\casey\Desktop\Homesteader\tools\qwen_image_local.py" `
    --model $modelDir `
    --prompt "A small wooden barn exterior under a clear winter sky, sunlight, low angle view, photorealistic" `
    --steps 4 `
    --width 1024 --height 1024 `
    --cpu-offload `
    --out "$outDir\smoke.png" `
    1> $stdOut `
    2> $stdErr
$rc = $LASTEXITCODE

# Append logs to combined log.
"`n=== stdout ===" | Add-Content $logPath
Get-Content $stdOut -Tail 40 | Add-Content $logPath
"`n=== stderr ===" | Add-Content $logPath
Get-Content $stdErr -Tail 40 | Add-Content $logPath
"`n[step5 retry $(Get-Date -Format 'o') exit=$rc]" | Add-Content $logPath

# Report file existence.
$outFile = "$outDir\smoke.png"
if (Test-Path $outFile) {
    Write-Host ("smoke.png: {0:N2} MB" -f ((Get-Item $outFile).Length / 1MB))
} else {
    Write-Host 'smoke.png NOT produced'
}
exit $rc
