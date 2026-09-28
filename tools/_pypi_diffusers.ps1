# What does PyPI say about diffusers? Use the simple JSON API and only emit
# fields we care about, no parsing the full long description.
$ErrorActionPreference = 'Continue'
try {
    $resp = Invoke-RestMethod -Uri 'https://pypi.org/pypi/diffusers/json' -TimeoutSec 30
    $info = $resp.info
    Write-Host ("name = {0}" -f $info.name)
    Write-Host ("version = {0}" -f $info.version)
    Write-Host ("requires_python = {0}" -f $info.requires_python)
    Write-Host ("release_count = {0}" -f $resp.releases.Count)
    # Most-recent 5 release dates
    $releases = $resp.releases.PSObject.Properties | ForEach-Object {
        [pscustomobject]@{
            ver = $_.Name
            upload = ($_.Value | Select-Object -First 1).upload_time
        }
    } | Sort-Object upload -Descending | Select-Object -First 5
    $releases | Format-Table -AutoSize
} catch {
    Write-Host ("PyPI fetch failed: " + $_.Exception.Message)
}
