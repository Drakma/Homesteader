Set-Location C:\Users\casey\Desktop\Homesteader
$lines = Get-Content "Homesteader\Assets\Scripts\UI\Phone\PhoneController.cs"
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match "_bankBackBtn|_marketBackBtn") {
        Write-Output "Line $($i+1): $($lines[$i])"
    }
}
