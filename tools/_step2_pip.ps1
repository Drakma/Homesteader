# Step 2 v3: install everything, but route outputs to a log file via *>
# (NOT a pipe) so SIGPIPE cannot break the install. Already-downloaded
# wheels can be reused; --upgrade overwrites in-progress installs.
$ErrorActionPreference = 'Stop'
$venvDir = 'C:\Users\casey\Desktop\Homesteader\tools\.venv-qwen-image'
$reqPath = 'C:\Users\casey\Desktop\Homesteader\tools\requirements_qwen_image.txt'
$venvPy = Join-Path $venvDir 'Scripts\python.exe'
$logPath = 'C:\Users\casey\Desktop\Homesteader\tools\_pip_step2.log'
$srcDir = 'C:\Users\casey\Desktop\Homesteader\tools\.diffusers-src'

# Inject Git into PATH for this subshell only (no permanent env change).
if (Test-Path 'C:\Program Files\Git\bin\git.exe') {
    $env:Path = 'C:\Program Files\Git\bin;' + $env:Path
}

# Truncate the previous log so only the most recent attempt is in it.
'' | Set-Content -Path $logPath -Encoding utf8

# venv (idempotent).
if (-not (Test-Path $venvPy)) {
    Write-Host '[step2] creating venv...' | Tee-Object -FilePath $logPath -Append | Out-Host
    & "C:\Python313\python.exe" -m venv $venvDir
}

# Pre-clone diffusers (small, fast). Verified ~8s on this host for 61.6 MB.
if (Test-Path (Join-Path $srcDir '.git')) {
    Write-Host "[step2] .diffusers-src already cloned; skipping git clone" | Tee-Object -FilePath $logPath -Append | Out-Host
}
else {
    if (Test-Path $srcDir) { Remove-Item -Recurse -Force $srcDir }
    Write-Host "[step2] cloning diffusers to $srcDir ..." | Tee-Object -FilePath $logPath -Append | Out-Host
    & git clone --filter=blob:none --depth=1 https://github.com/huggingface/diffusers $srcDir 2>&1 |
    Tee-Object -FilePath $logPath -Append | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Host '[step2] FAILED to clone diffusers. See log.' | Tee-Object -FilePath $logPath -Append | Out-Host
        exit 1
    }
}

# Ensure pip is fresh.
"[step2] upgrading pip" | Add-Content $logPath
& $venvPy -m pip install --upgrade pip *>>$logPath
if ($LASTEXITCODE -ne 0) {
    '[step2] pip upgrade failed' | Add-Content $logPath
    exit 1
}

# Build a no-diffusers requirements file so pip does not silently swap to
# the PyPI release of diffusers (which lacks QwenImage21Pipeline).
$noDiffReq = 'C:\Users\casey\Desktop\Homesteader\tools\_requirements_no_diffusers.txt'
$pyProg = @"
lines = open(r'$reqPath','r',encoding='utf-8').read().splitlines()
kept  = []
for ln in lines:
    if 'diffusers' in ln:
        kept.append('# diffusers line omitted; installed from local clone')
    else:
        kept.append(ln)
open(r'$noDiffReq','w',encoding='utf-8').write('\n'.join(kept)+'\n')
print('wrote',r'$noDiffReq')
"@
"[step2] writing no-diffusers requirements" | Add-Content $logPath
& $venvPy -c $pyProg *>>$logPath
if ($LASTEXITCODE -ne 0) {
    '[step2] failed to write no-diffusers requirements' | Add-Content $logPath
    exit 1
}

'[pip-install ' + (Get-Date -Format 'o') + ' start]' | Add-Content $logPath
& $venvPy -m pip install --upgrade -r $noDiffReq *>>$logPath
$p1 = $LASTEXITCODE
'[pip-install ' + (Get-Date -Format 'o') + ' end exit=' + $p1 + ']' | Add-Content $logPath
if ($p1 -ne 0) {
    '[step2] pip install non-diffusers failed' | Add-Content $logPath
    exit 1
}

"[step2] installing diffusers from $srcDir --no-deps --force-reinstall" | Add-Content $logPath
& $venvPy -m pip install --no-deps --force-reinstall "$srcDir" *>>$logPath
$p2 = $LASTEXITCODE
"[step2] diffusers install exit=$p2" | Add-Content $logPath
if ($p2 -ne 0) {
    '[step2] diffusers install failed' | Add-Content $logPath
    exit 1
}

& $venvPy -m pip show transformers diffusers accelerate pillow huggingface_hub *>>$logPath

& $venvPy -c "from diffusers import QwenImage21Pipeline; print('QwenImage21Pipeline: IMPORTABLE')" *>>$logPath
'[step2] done' | Add-Content $logPath
