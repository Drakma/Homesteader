Set-Location C:\Users\casey\Desktop\Homesteader
Write-Output "=== Python Processes ==="
Get-CimInstance Win32_Process -Filter "name = 'python.exe'" | Select-Object ProcessId, CommandLine, CreationDate, WorkingSetSize | Format-List
Write-Output "=== GPU state ==="
$nvidia = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($nvidia) { & nvidia-smi }
