Get-CimInstance Win32_VideoController |
    Select-Object Name, DriverVersion, @{Name='VRAM_GB';Expression={[math]::Round($_.AdapterRAM/1GB,2)}} |
    Format-Table -AutoSize

Get-PSDrive -PSProvider FileSystem |
    Where-Object { $_.Used -gt 0 } |
    Select-Object Name, @{N='Free_GB';E={[math]::Round($_.Free/1GB,1)}}, @{N='Total_GB';E={[math]::Round(($_.Used+$_.Free)/1GB,1)}} |
    Format-Table -AutoSize

Get-CimInstance Win32_Processor |
    Select-Object Name, NumberOfCores, NumberOfLogicalProcessors |
    Format-Table -AutoSize

Get-CimInstance Win32_OperatingSystem |
    Select-Object Caption, Version, OSArchitecture, @{N='RAM_GB';E={[math]::Round($_.TotalVisibleMemorySize/1MB,1)}} |
    Format-Table -AutoSize
