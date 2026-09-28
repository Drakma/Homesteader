Start-Sleep -Seconds 10
Write-Host '=== process check ==='
Get-Process powershell, python, git -ErrorAction SilentlyContinue |
    Select-Object Id, ProcessName, CPU |
    Format-Table -AutoSize
Write-Host '=== log tail ==='
$log = 'C:\Users\casey\Desktop\Homesteader\tools\_pip_step2.log'
if (Test-Path $log) {
    Get-Content $log -Tail 8
}
