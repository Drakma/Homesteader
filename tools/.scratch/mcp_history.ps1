$Env:GIT_PAGER = 'cat'
Set-Location 'C:\Users\casey\Desktop\Homesteader'
& 'C:\Program Files\Git\bin\git.exe' --no-pager log --oneline -n 20 -- .mcp.json
Write-Output '---'
& 'C:\Program Files\Git\bin\git.exe' --no-pager log -p -n 5 -- .mcp.json
Write-Output '---'
& 'C:\Program Files\Git\bin\git.exe' --no-pager status --short -- .mcp.json
& 'C:\Program Files\Git\bin\git.exe' --no-pager diff -- .mcp.json
