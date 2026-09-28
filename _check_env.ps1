$root = "C:\Users\casey\Desktop\Homesteader"
foreach ($p in @("$root\.env", "$root\assets\.env")) {
    Write-Output "=== $p"
    if (Test-Path $p) {
        foreach ($line in Get-Content $p) {
            if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
                $name = $Matches[1]
                $val = $Matches[2].Trim().Trim('"').Trim("'")
                Write-Output ("   {0} = <set, {1} chars>" -f $name, $val.Length)
            }
        }
    } else {
        Write-Output "   (not found)"
    }
}
