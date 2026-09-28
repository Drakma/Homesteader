Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*_debug_qwen.py*" -or $_.ProcessId -eq 5208 } | Select-Object ProcessId, CommandLine, CreationDate
