$names = @(
    'cursor', 'code', 'codegpt', 'claude', 'codex',
    'antigravity', 'cody', 'windsurf', 'roo', 'trae',
    'relay_win', 'mcrelay', 'Unity', 'unity-mcp'
)
$procs = Get-Process | Where-Object { $names -contains $_.ProcessName.ToLower() } |
    Select-Object ProcessName, Id, StartTime, MainWindowTitle |
    Sort-Object ProcessName
if ($procs) {
    $procs | Format-Table -AutoSize | Out-String
} else {
    Write-Output "(no host processes match)"
}
