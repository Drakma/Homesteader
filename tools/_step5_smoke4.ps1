# Step 5 fixed: build a single argument-string to bypass the Start-Process
# -ArrayList-with-comma-split problem. We pass the entire cmdline as one
# string; Start-Process handles quoting on Windows.

$ErrorActionPreference = 'Continue'

$prompt = 'A small wooden barn exterior under a clear winter sky, sunlight, low angle view, photorealistic'
$cmdLine = "C:\Python313\python.exe -u C:\Users\casey\Desktop\Homesteader\tools\qwen_image_local.py --model C:\Users\casey\Desktop\models\Qwen-Image-2.1 --prompt `"$prompt`" --steps 4 --width 1024 --height 1024 --cpu-offload --out C:\Users\casey\Desktop\Homesteader\assets\_qwen_local\smoke.png"

$sout = 'C:\Users\casey\Desktop\Homesteader\tools\_smoke_stdout.log'
$serr = 'C:\Users\casey\Desktop\Homesteader\tools\_smoke_stderr.log'
'' | Set-Content -Path $sout -Encoding utf8
'' | Set-Content -Path $serr -Encoding utf8

$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:PYTHONUNBUFFERED = '1'

Write-Host ("cmdline: {0}" -f $cmdLine)
# Use `-RunAsBatch $false` equivalent: just & directly with redirection; the
# power shell is fast enough on background to not break pipes if we don't
# have a *real* (interactive) pipe attached.

$proc = Start-Process `
    -FilePath 'C:\Python313\python.exe' `
    -ArgumentList @(
        '-u',
        'C:\Users\casey\Desktop\Homesteader\tools\qwen_image_local.py',
        '--model', 'C:\Users\casey\Desktop\models\Qwen-Image-2.1',
        '--prompt', $prompt,
        '--steps', '4',
        '--width', '1024',
        '--height', '1024',
        '--cpu-offload',
        '--out', 'C:\Users\casey\Desktop\Homesteader\assets\_qwen_local\smoke.png'
    ) `
    -NoNewWindow `
    -RedirectStandardOutput $sout `
    -RedirectStandardError  $serr `
    -PassThru
Write-Host ("Spawned python PID {0}" -f $proc.Id)
exit 0
