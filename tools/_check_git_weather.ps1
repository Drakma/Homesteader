Set-Location C:\Users\casey\Desktop\Homesteader
$gitCmd = (Get-Command git.exe -ErrorAction SilentlyContinue).Source
if (-not $gitCmd) {
    # Check common install locations
    $candidates = @(
        "C:\Program Files\Git\cmd\git.exe",
        "C:\Program Files\Git\bin\git.exe",
        "C:\Users\casey\AppData\Local\Programs\Git\cmd\git.exe",
        "C:\Program Files (x86)\Git\cmd\git.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { $gitCmd = $c; break }
    }
}

Write-Output "Git executable: $gitCmd"
if ($gitCmd) {
    Write-Output "=== Git Status ==="
    & $gitCmd status -s
    Write-Output ""
    Write-Output "=== Recent Git Commits ==="
    & $gitCmd log -n 15 --oneline --decorate
    Write-Output ""
    Write-Output "=== Git Diff of Modified Files ==="
    & $gitCmd diff --name-only
}

Write-Output ""
Write-Output "=== WeatherEffectsManager.cs Info ==="
$wem = "Homesteader\Assets\Scripts\WeatherEffectsManager.cs"
if (Test-Path $wem) {
    Get-Item $wem | Select-Object FullName, LastWriteTime, Length
}
