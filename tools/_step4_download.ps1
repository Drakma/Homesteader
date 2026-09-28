# Step 4: huggingface-cli download Qwen/Qwen-Image-2.1 -> ~47 GB to
# C:\Users\casey\Desktop\models\Qwen-Image-2.1\. This is the multi-minute
# big download. We:
#  - invoke huggingface-cli via `python -m` so we don't depend on a missing Scripts/
#  - route output to a log via *> (the same SIGPIPE workaround as step 2)
#  - exclude downloads that are duplicate or auxiliary (tokenizer, README,
#    config, etc) - we still keep LICENSE per legal record-keeping
#  - include the heavy weights: text_encoder/*.safetensors, transformer/*.safetensors,
#    vae/*.safetensors, scheduler, processor

$ErrorActionPreference = 'Stop'
$cacheDir = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1'
$logPath = 'C:\Users\casey\Desktop\Homesteader\tools\_download_step4.log'

# Make sure cache dir parent exists.
$parent = Split-Path $cacheDir -Parent
if (-not (Test-Path $parent)) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
}
if (-not (Test-Path $cacheDir)) {
    New-Item -ItemType Directory -Path $cacheDir -Force | Out-Null
}

# Empty the previous run's log.
'' | Set-Content -Path $logPath -Encoding utf8

"[step4-start $(Get-Date -Format 'o')]" | Add-Content $logPath
Write-Host "[$(Get-Date -Format 'o')] huggingface-cli starting (sse-free progress estimate via size-deltas)" | Tee-Object Variable firstLine | Out-Host
"[firstLine] $firstLine" | Add-Content $logPath

# The --include list is what the model card README effectively does; we mirror it
# but drop processor/ tokenizer variants we won't need for inference. We use
# include globs so we don't accidentally pull extras.
$include = @(
    '*.json'
    '*.md'
    'LICENSE'
    'tokenizer/*'
    'scheduler/*'
    'processor/*'
    'text_encoder/*.safetensors'
    'text_encoder/*.json'
    'transformer/*.safetensors'
    'transformer/*.json'
    'vae/*.safetensors'
    'vae/*.json'
    'model_index.json'
)

# Build the include list as a comma-separated string for the CLI.
$includeArg = ($include -join ',')

# Use `hf` CLI via `python -m huggingface_hub.cli.hf` so we don't depend on a
# missing Scripts/ entry point. The `huggingface-cli` alias still works but
# `hf` is the canonical one (confirmed via entry-point probe).
"[step4 invoking hf CLI via python -m huggingface_hub.cli.hf]" | Add-Content $logPath
& "C:\Python313\python.exe" -m huggingface_hub.cli.hf download Qwen/Qwen-Image-2.1 `
    --local-dir "C:\Users\casey\Desktop\models\Qwen-Image-2.1" `
    --include $includeArg `
    *>> $logPath
$rc = $LASTEXITCODE
"[step4-end $(Get-Date -Format 'o') exit=$rc]" | Add-Content $logPath
exit $rc
