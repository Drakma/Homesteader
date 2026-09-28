# Check whether diffusers 0.40.0 already includes QwenImage21Pipeline.
# If yes, we can avoid the git+https dependency entirely.
$ErrorActionPreference = 'Continue'
try {
    # Download the wheel metadata for 0.40.0 and grep its modules listing.
    $package = Invoke-RestMethod -Uri 'https://pypi.org/pypi/diffusers/0.40.0/json' -TimeoutSec 30
    # Use the wheel file URL to peek at the package contents.
    $wheel = $package.urls | Where-Object { $_.filename -like '*py3-none-any.whl' } | Select-Object -First 1
    Write-Host ("wheel url: " + $wheel.url)
    $wheelFile = 'C:\Users\casey\Desktop\Homesteader\tools\_diffusers_0.40.0.whl'
    if (Test-Path $wheelFile) { Remove-Item $wheelFile -Force }
    Invoke-WebRequest -Uri $wheel.url -OutFile $wheelFile -TimeoutSec 90
    Write-Host ("wheel size: {0:N1} MB" -f ((Get-Item $wheelFile).Length / 1MB))
    # Confirm the QwenImage21Pipeline symbol is in there.
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead($wheelFile)
    $hit_q21     = $zip.Entries | Where-Object { $_.FullName -match 'qwenimage21' }
    $hit_q_i     = $zip.Entries | Where-Object { $_.FullName -match 'qwen_image' }
    Write-Host ("matches for 'qwenimage21': " + ($hit_q21 | Measure-Object).Count)
    Write-Host ("matches for 'qwen_image'  : " + ($hit_q_i  | Measure-Object).Count)
    if ($hit_q21) { $hit_q21 | Select-Object -First 5 -ExpandProperty FullName }
    if ($hit_q_i) { $hit_q_i  | Select-Object -First 5 -ExpandProperty FullName }
    $zip.Dispose()
    Remove-Item $wheelFile -Force
} catch {
    Write-Host ("PyPI zip probe failed: " + $_.Exception.Message)
}
