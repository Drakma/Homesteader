# Step 2 final: drop the venv strategy. The system Python at C:\Python313\python.exe
# already has torch 2.6.0+cu124, transformers 5.17.0, accelerate, huggingface_hub,
# pillow, numpy - everything we need except the right diffusers. We'll uninstall
# the PyPI 0.40.0 diffusers (pulled in by hy3dgen), then install the local clone
# from tools/.diffusers-src --user. This sidesteps:
#   - venv/relauncher weirdness on Windows
#   - resolving torch without CUDA wheels (system already has cu124 torch)
#   - missing 'requests' dep (already on system via hy3dgen / gradio chains)

$ErrorActionPreference = 'Stop'
$src = 'C:\Users\casey\Desktop\Homesteader\tools\.diffusers-src'
$logPath = 'C:\Users\casey\Desktop\Homesteader\tools\_system_install.log'
'' | Set-Content -Path $logPath -Encoding utf8

# Drop the unused venv (it's about 1 GB; we don't need it). This affects only
# tools\.venv-qwen-image\, leaves system Python untouched.
$venv = 'C:\Users\casey\Desktop\Homesteader\tools\.venv-qwen-image'
if (Test-Path $venv) {
    "[step2-system] removing venv at $venv" | Add-Content $logPath
    Remove-Item -Recurse -Force $venv
}

# Confirm prerequisites on system Python.
"[step2-system] pre-check" | Add-Content $logPath
& "C:\Python313\python.exe" -c "import sys,torch,transformers,accelerate,huggingface_hub,PIL,requests,filelock,numpy,safetensors; print('torch', torch.__version__, 'cuda', torch.cuda.is_available()); print('transformers', transformers.__version__); print('OK')" *>>$logPath
if ($LASTEXITCODE -ne 0) {
    "[step2-system] prerequisites missing" | Add-Content $logPath
    exit 1
}

# Uninstall the PyPI diffusers so the local clone doesn't conflict on import.
# hy3dgen forces a reinstall of 0.40.0 but that's OK; we'll force-install on top.
"[step2-system] uninstall PyPI diffusers" | Add-Content $logPath
& "C:\Python313\python.exe" -m pip uninstall -y diffusers *>>$logPath 2>&1
# (We'll force-install the dev version on top; if hy3dgen re-asserts, we re-fix.)

# Install local diffusers over the hole we just made. --no-deps because we know
# the deps are already installed (numpy, huggingface_hub, etc).
"[step2-system] pip install --no-deps --force-reinstall -U $src" | Add-Content $logPath
& "C:\Python313\python.exe" -m pip install --no-deps --force-reinstall -U "$src" *>>$logPath 2>&1

# Sanity: re-install diffusers WITH deps so hy3dgen doesn't fight back too hard.
"[step2-system] pip install (without --no-deps) to satisfy possible dep downgrades" | Add-Content $logPath
& "C:\Python313\python.exe" -m pip install --force-reinstall -U "$src" *>>$logPath 2>&1

# Probe imports.
"[step2-system] probe imports" | Add-Content $logPath
& "C:\Python313\python.exe" "C:\Users\casey\Desktop\Homesteader\tools\_diagnose_diffusers.py" *>>$logPath 2>&1

'[step2-system] done' | Add-Content $logPath
