param([int]$InitialDelaySeconds = 0)   # wait this long before the first attempt (used when restarting mid-quota)
# Re-runs bump_playlists.mjs every hour until every playlist has 10 tracks
# or 24 hours pass. Started detached; progress is in bump_playlists.log.
Set-Location $PSScriptRoot
if ($InitialDelaySeconds -gt 0) { Start-Sleep -Seconds $InitialDelaySeconds }
$deadline = (Get-Date).AddHours(24)
while ((Get-Date) -lt $deadline) {
  $out = node bump_playlists.mjs 2>&1 | Out-String
  # The generator tags its summary "quota-limit-reached" when Gemini's quota is hit and "incomplete" when any
  # playlist is still short for another reason (a failed send, a Gemini error). Either way, come back later.
  if ($out -notmatch 'quota-limit-reached' -and $out -notmatch ' incomplete') { break }
  Start-Sleep -Seconds 3600
}
Add-Content bump_playlists.log "[$(Get-Date -Format o)] retry_bump.ps1 exiting"
