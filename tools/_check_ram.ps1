Write-Output "=== System RAM and Pagefile ==="
Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory, TotalVirtualMemorySize, FreeVirtualMemory | Format-List
Get-CimInstance Win32_PageFileUsage | Format-List
Get-CimInstance Win32_PageFileSetting | Format-List
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | Select-Object DeviceId, FreeSpace, Size | Format-Table -AutoSize
