# Probe whether git is installed anywhere typical on Windows.
$ErrorActionPreference = 'Continue'
$candidates = @(
    'git',
    'C:\Program Files\Git\bin\git.exe',
    'C:\Program Files (x86)\Git\bin\git.exe',
    'C:\Program Files\Git\cmd\git.exe',
    "$env:LOCALAPPDATA\Programs\Git\bin\git.exe"
)
foreach ($c in $candidates) {
    try {
        $ver = & $c --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host ("FOUND: {0} -> {1}" -f $c, ($ver -join ','))
            return
        }
    }
    catch {
        # keep scanning
    }
}
Write-Host "git.exe not found at any standard location"
