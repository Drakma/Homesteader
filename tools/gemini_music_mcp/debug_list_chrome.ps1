Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" | ForEach-Object {
  $cl = ""
  if ($_.CommandLine) { $cl = $_.CommandLine }
  Write-Output ("{0}: {1}" -f $_.ProcessId, $cl)
}
