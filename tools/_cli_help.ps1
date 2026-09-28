# Probe what's importable as a CLI entry point and confirm download works.
$ErrorActionPreference = 'Continue'
Write-Host '=== python -m hug ...' 
& "C:\Python313\python.exe" -m huggingface_hub.commands.huggingface_cli --help *>&1 | Out-Host -Paging
Write-Host '=== via python -c importlib ==='
& "C:\Python313\python.exe" -c "import importlib.metadata; eps = importlib.metadata.entry_points(); for ep in eps.select(group='console_scripts'): print(ep.name, ep.value)" *>&1 | Out-Host
