Set-Location C:\Users\casey\Desktop\Homesteader
$metaFiles = @(
    "Homesteader\Assets\Resources\WeatherFX\tex_raindrop.png.meta",
    "Homesteader\Assets\Resources\WeatherFX\tex_snowflake.png.meta",
    "Homesteader\Assets\Resources\WeatherFX\tex_splash.png.meta"
)

foreach ($mf in $metaFiles) {
    if (Test-Path $mf) {
        $c = Get-Content $mf -Raw
        $c = $c -replace 'alphaIsTransparency: 0', 'alphaIsTransparency: 1'
        $c = $c -replace 'wrapU: 0', 'wrapU: 1' # Clamp
        $c = $c -replace 'wrapV: 0', 'wrapV: 1' # Clamp
        $c = $c -replace 'wrapW: 0', 'wrapW: 1' # Clamp
        Set-Content -Path $mf -Value $c -NoNewline
        Write-Output "Updated $mf"
    }
}
