# Re-runs bump_playlists.mjs every 30 minutes until every playlist has 10 tracks
# or 24 hours pass. Started detached; progress is in bump_playlists.log.
Set-Location $PSScriptRoot
$deadline = (Get-Date).AddHours(24)
while ((Get-Date) -lt $deadline) {
  $out = node bump_playlists.mjs 2>&1 | Out-String
  # The generator aborts its run and tags the summary when Gemini's quota is hit; anything else means done or a real failure.
  if ($out -notmatch 'quota-limit-reached') { break }
  Start-Sleep -Seconds 1800
}
Add-Content bump_playlists.log "[$(Get-Date -Format o)] retry_bump.ps1 exiting"
