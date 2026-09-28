Set-Location C:\Users\casey\Desktop\Homesteader
$lines = Get-Content "Homesteader\Assets\Scripts\UI\ToastNotificationSystem.cs"
Write-Output "Lines count: $($lines.Count)"
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match "public static void Show") {
        Write-Output "Found 'public static void Show' at line $($i + 1)"
    }
}
