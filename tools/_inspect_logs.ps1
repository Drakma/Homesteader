Set-Location C:\Users\casey\Desktop\Homesteader
Write-Output "=== Assets _qwen_local contents ==="
if (Test-Path assets\_qwen_local) {
    Get-ChildItem assets\_qwen_local | Format-List FullName, Length, LastWriteTime
} else {
    Write-Output "assets\_qwen_local does not exist"
}

Write-Output "=== Log lengths and tails ==="
Get-ChildItem tools\_smoke* | Format-Table Name, Length, LastWriteTime

Write-Output "=== _smoke_v7b_stdout.log ==="
if (Test-Path tools\_smoke_v7b_stdout.log) { Get-Content tools\_smoke_v7b_stdout.log }

Write-Output "=== _smoke_v7b_stderr.log (last 20 lines) ==="
if (Test-Path tools\_smoke_v7b_stderr.log) { Get-Content tools\_smoke_v7b_stderr.log -Tail 20 }
