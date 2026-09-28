Set-Location C:\Users\casey\Desktop\Homesteader
$lines = Get-Content "Homesteader\Assets\Scripts\UI\Phone\PhoneController.cs"
Write-Output "Lines 210 to 235:"
for ($i = 209; $i -lt 235; $i++) {
    Write-Output "$($i+1): $($lines[$i])"
}
