$projDir = 'C:\Users\casey\Desktop\Homesteader'
$outDir  = Join-Path $projDir 'assets\_qwen_local'
$sout    = Join-Path $projDir 'tools\_smoke_v7b_stdout.log'
$serr    = Join-Path $projDir 'tools\_smoke_v7b_stderr.log'
$pngOut  = Join-Path $outDir    'smoke_v7b.png'
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
'' | Set-Content -Path $sout -Encoding utf8
'' | Set-Content -Path $serr -Encoding utf8
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:PYTHONUNBUFFERED = '1'
$env:QWEN_PROMPT = 'A small wooden barn exterior under a clear winter sky, sunlight, low angle view, photorealistic'
$argList = @('-u', 'C:\Users\casey\Desktop\Homesteader\tools\qwen_image_local.py', '--model', 'C:\Users\casey\Desktop\models\Qwen-Image-2.1', '--aspect', '1:1', '--steps', '4', '--cpu-offload', '--out', $pngOut)
$proc = Start-Process -FilePath 'C:\Python313\python.exe' -ArgumentList $argList -RedirectStandardOutput $sout -RedirectStandardError $serr -WorkingDirectory 'C:\Python313' -NoNewWindow -PassThru
Write-Host "[smoke v7b] spawned python PID=$($proc.Id); wrapper exiting."
exit 0
