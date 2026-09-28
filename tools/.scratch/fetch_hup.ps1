$url = 'https://i.imgur.com/hUpS7Ky.png'
$out = 'C:\Users\casey\Desktop\Homesteader\tools\.scratch\hUpS7Ky.png'

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

try {
    $wc = New-Object System.Net.WebClient
    $data = $wc.DownloadData($url)
    [System.IO.File]::WriteAllBytes($out, $data)
    Write-Output ('saved ' + $data.Length + ' bytes -> ' + $out)
} catch {
    Write-Output ('err: ' + $_.Exception.Message)
}
