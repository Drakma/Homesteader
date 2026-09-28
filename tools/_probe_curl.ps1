# Probe for curl-like binaries.
foreach ($tool in 'curl', 'curl.exe', 'wget', 'C:\Windows\System32\curl.exe', 'C:\Program Files\Git\bin\curl.exe') {
    try {
        $out = & $tool --version 2>&1 | Select-Object -First 1
        if ($out) { Write-Host ("FOUND {0}: {1}" -f $tool, $out) }
    } catch {
        # not found
    }
}
Write-Host 'done'
