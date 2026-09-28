Get-WinEvent -ListLog * -ErrorAction SilentlyContinue | Where-Object { $_.RecordCount -gt 0 -and $_.LastWriteTime -gt (Get-Date).AddMinutes(-10) } | Select-Object LogName, LastWriteTime
