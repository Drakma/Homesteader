# Step 5: smoke test the qwen_image_local.py CLI on the freshly downloaded
# weights. Output routed to a log via *> so SIGPIPE cannot break it.
$ErrorActionPreference = 'Continue'
$logPath = 'C:\Users\casey\Desktop\Homesteader\tools\_smoke_step5.log'
$outDir  = 'C:\Users\casey\Desktop\Homesteader\assets\_qwen_local'

New-Item -ItemType Directory -Path $outDir -Force | Out-Null

'' | Set-Content -Path $logPath -Encoding utf8
"[step5 $(Get-Date -Format 'o')]" | Add-Content $logPath

& "C:\Python313\python.exe" -u "C:\Users\casey\Desktop\Homesteader\tools\qwen_image_local.py" `
    --prompt "A small wooden barn exterior under a clear winter sky, sunlight, low angle view, photorealistic" `
    --steps 4 `
    --width 1024 --height 1024 `
    --cpu-offload `
    --out "$outDir\smoke.png"  `
    2>&1 | ForEach-Object { $line = $_; Write-Host $line; Add-Content -Path $logPath -Value $line }
$rc = $LASTEXITCODE
"[step5 $(Get-Date -Format 'o') exit=$rc]" | Add-Content $logPath
exit $rc
