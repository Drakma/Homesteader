$url = 'https://i.imgur.com/1kPJVeB.png'
$out = 'C:\Users\casey\Desktop\Homesteader\tools\.scratch\1kPJVeB.png'

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

try {
    $wc = New-Object System.Net.WebClient
    $data = $wc.DownloadData($url)
    [System.IO.File]::WriteAllBytes($out, $data)
    Write-Output ('saved ' + $data.Length + ' bytes -> ' + $out)
} catch {
    Write-Output ('err: ' + $_.Exception.Message)
}
