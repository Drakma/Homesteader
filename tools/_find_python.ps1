Get-CimInstance Win32_Process -Filter "name = 'python.exe'" | Select-Object ProcessId, CommandLine, CreationDate, WorkingSetSize, UserModeTime, KernelModeTime | Format-List
