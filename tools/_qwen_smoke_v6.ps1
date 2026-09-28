# Smoke-test the qwen CLI with the fixed default-out-path code, foreground,
# fully buffered to log files. Uses the same offline env the previous run did,
# but with --steps 4 and a smaller 768x768 render to see something on screen
# quickly on a 1080 Ti with CPU offload. The first call ALSO pays the
# "pipeline import + first-time CUDA kernels" cost; expect ~3-5 min total.
$ErrorActionPreference = 'Continue'
$projDir = 'C:\Users\casey\Desktop\Homesteader'
$outDir  = Join-Path $projDir 'assets\_qwen_local'
$sout    = Join-Path $projDir 'tools\_smoke_v6_stdout.log'
$serr    = Join-Path $projDir 'tools\_smoke_v6_stderr.log'

New-Item -ItemType Directory -Path $outDir -Force | Out-Null
'' | Set-Content $sout -Encoding utf8
'' | Set-Content $serr -Encoding utf8

# Mirror the previous offline flags so we don't hit HF over the wire.
$env:HF_HUB_OFFLINE       = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:PYTHONUNBUFFERED     = '1'

$cmd = 'C:\Python313\python.exe'
$args = @(
    '-u'
    (Join-Path $projDir 'tools\qwen_image_local.py')
    '--model', 'C:\Users\casey\Desktop\models\Qwen-Image-2.1'
    '--prompt', 'A small wooden barn exterior under a clear winter sky, sunlight, low angle view, photorealistic'
    '--aspect', '1:1'
    '--steps', '4'
    '--cpu-offload'
    '--out',  (Join-Path $outDir 'smoke_v6.png')
)

Write-Host "[smoke v6 $(Get-Date -Format o)] launching:" $cmd $args
Write-Host "[smoke v6] output: $sout / $serr"

$t0 = Get-Date
& $cmd @args 1>$sout 2>$serr
$rc = $LASTEXITCODE
$elapsed = (Get-Date) - $t0

Write-Host "[smoke v6 $(Get-Date -Format o)] exit=$rc elapsed=$([int]$elapsed.TotalSeconds)s"
Write-Host ""
Write-Host "--- last 25 of stdout ---"
Get-Content $sout -Tail 25
Write-Host ""
Write-Host "--- last 25 of stderr ---"
Get-Content $serr -Tail 25
Write-Host ""
if (Test-Path (Join-Path $outDir 'smoke_v6.png')) {
    $png = Get-Item (Join-Path $outDir 'smoke_v6.png')
    Write-Host "[smoke v6] PNG written: $($png.FullName) ($($png.Length) bytes)"
} else {
    Write-Host "[smoke v6] NO PNG written."
}
exit $rc
