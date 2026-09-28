# Final check: verify the Qwen/Qwen-Image-2.1 repo weights are complete on disk.
$dest = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1'
$rel = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1'
Get-ChildItem -Recurse -File $dest -ErrorAction SilentlyContinue |
Where-Object { $_.FullName -notlike '*\cache*' -and $_.Extension -notin '.lock', '.incomplete', '.metadata' } |
Sort-Object FullName |
ForEach-Object {
    $szGB = [math]::Round($_.Length / 1GB, 2)
    Write-Host ("{0,7:N2} GB  {1}" -f $szGB, $_.FullName.Replace($rel, ''))
}
Write-Host '---'
$total = (Get-ChildItem -Recurse -File $dest -ErrorAction SilentlyContinue | Where-Object { $_.Extension -notin '.lock', '.incomplete', '.metadata' } | Measure-Object -Property Length -Sum).Sum
Write-Host ("local_dir total: {0:N2} GB" -f ($total / 1GB))
Write-Host '---'
Write-Host 'curl processes still running:'
Get-Process curl -ErrorAction SilentlyContinue | Select-Object Id, CPU | Format-Table -AutoSize
Write-Host '<<<done>>>'
