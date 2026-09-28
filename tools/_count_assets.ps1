$assetsDir = "C:\Users\casey\Desktop\Homesteader\assets"
$exclude = @('_ai','_asset_requests','_docs','_gamerules','_ghost_folder_backup','_legacy_from_hud','_pipeline_stats','_prompt_batches','_qwen_local','_schemas','_scratch','_trash','__pycache__','hud_kit','models_legacy','textures','peds','biomes','appliances','vehicles')
$total = 0
Get-ChildItem -Path $assetsDir -Directory | Where-Object { $exclude -notcontains $_.Name -and $_.Name -notmatch '^_' } | ForEach-Object {
    $cat = $_.Name
    $items = Get-ChildItem -Path $_.FullName -Directory | Where-Object { Test-Path (Join-Path $_.FullName ($_.Name + '.json')) }
    $count = $items.Count
    $total += $count
    Write-Output ("{0}: {1}" -f $cat, $count)
}
Write-Output ("TOTAL: {0}" -f $total)
