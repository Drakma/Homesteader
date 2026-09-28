$ports = 37412,9877,8000,3000,5173
foreach ($p in $ports) {
    $c = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
    if ($c) {
        $app = (Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue).ProcessName
        Write-Output ("LISTEN  {0,-6} pid={1,-7} app={2}" -f $p, $c.OwningProcess, $app)
    } else {
        Write-Output ("silent  {0}" -f $p)
    }
}
