# Step 5 with detachable background so the SIGPIPE-killed-pipe-closed
# pattern cannot affect it. We use Start-Process -RedirectStandardOutput/Error
# instead of the &-operator-and-pipe redirection. Then we wait for both
# files to be written and the python process to exit.
$ErrorActionPreference = 'Continue'
$src  = 'C:\Users\casey\Desktop\Homesteader\tools\qwen_image_local.py'
$sout = 'C:\Users\casey\Desktop\Homesteader\tools\_smoke_stdout.log'
$serr = 'C:\Users\casey\Desktop\Homesteader\tools\_smoke_stderr.log'
$modelDir = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1'

'' | Set-Content -Path $sout -Encoding utf8
'' | Set-Content -Path $serr -Encoding utf8

$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:PYTHONUNBUFFERED = '1'

$proc = Start-Process `
    -FilePath 'C:\Python313\python.exe' `
    -ArgumentList @(
        '-u', $src,
        '--model', $modelDir,
        '--prompt', 'A small wooden barn exterior under a clear winter sky, sunlight, low angle view, photorealistic',
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
