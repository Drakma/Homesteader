Set-Location C:\Users\casey\Desktop\Homesteader
$dirs = @(
    "$env:USERPROFILE\.codegpt",
    "$env:APPDATA\CodeGPT",
    "$env:LOCALAPPDATA\CodeGPT",
    "$env:USERPROFILE\.cursor",
    "$env:USERPROFILE\.vscode"
)
foreach ($d in $dirs) {
    if (Test-Path $d) {
        Get-ChildItem -Path $d -Recurse -Filter "*input_file_0*" -ErrorAction SilentlyContinue | Select-Object FullName
        Get-ChildItem -Path $d -Recurse -Filter "*.png" -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-30) } | Select-Object FullName, LastWriteTime
    }
}
