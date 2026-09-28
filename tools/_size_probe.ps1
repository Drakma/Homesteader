# Dry-run: pass --include as repeated flags (CLI accepts multiple --include
# flags combined as OR) so the glob parser sees them individually.
$ErrorActionPreference = 'Continue'
$inc = @('*.json', '*.md', 'LICENSE', 'tokenizer/*', 'scheduler/*', 'processor/*', 'text_encoder/*.safetensors', 'text_encoder/*.json', 'transformer/*.safetensors', 'transformer/*.json', 'vae/*.safetensors', 'vae/*.json', 'model_index.json')
$argList = @('-m', 'huggingface_hub.cli.hf', 'download', 'Qwen/Qwen-Image-2.1', '--local-dir', 'C:\Users\casey\Desktop\models\Qwen-Image-2.1', '--dry-run')
foreach ($p in $inc) { $argList += @('--include', $p) }
& "C:\Python313\python.exe" @argList *>&1 | Out-Host
