Set-Location C:\Users\casey\Desktop\Homesteader
$target = "Homesteader\Assets\AssetCatalog"
if (Test-Path $target) {
    Remove-Item -Path $target -Recurse -Force
    Write-Output "Removed $target"
}
$meta = "Homesteader\Assets\AssetCatalog.meta"
if (Test-Path $meta) {
    Remove-Item -Path $meta -Force
    Write-Output "Removed $meta"
}
