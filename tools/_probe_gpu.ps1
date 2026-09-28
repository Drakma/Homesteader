# Probe nvidia-smi and Win32_PnPEntity to ground-truth VRAM and card identity.
# The earlier WMI Win32_VideoController reading returns AdapterRAM, which on
# NVIDIA cards is rounded to 4 GB due to a 32-bit field quirk - this script
# reads driver-reported memory.total directly via nvidia-smi.

$ErrorActionPreference = 'Continue'

Write-Host "=== nvidia-smi ==="
try {
    & nvidia-smi --query-gpu=index,name,memory.total,memory.used,memory.free,driver_version --format=csv 2>&1
} catch {
    Write-Host ("nvidia-smi failed: " + $_.Exception.Message)
}

Write-Host ""
Write-Host "=== Win32_PnPEntity (Display adapters) ==="
try {
    Get-CimInstance Win32_PnPEntity |
        Where-Object { $_.PNPClass -eq 'Display' -or $_.PNPClass -eq 'Monitor' } |
        Select-Object Name, DeviceID, Manufacturer |
        Format-Table -AutoSize
} catch {
    Write-Host ("PnPEntity query failed: " + $_.Exception.Message)
}
