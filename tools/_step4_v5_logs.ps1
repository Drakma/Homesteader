# What's in the curl verbose logs?
$logs = @(
    'C:\Users\casey\Desktop\Homesteader\tools\_curl_text3.log',
    'C:\Users\casey\Desktop\Homesteader\tools\_curl_text3.log.out',
    'C:\Users\casey\Desktop\Homesteader\tools\_curl_text3.log.err',
    'C:\Users\casey\Desktop\Homesteader\tools\_curl_transformer1.log',
    'C:\Users\casey\Desktop\Homesteader\tools\_curl_transformer1.log.out',
    'C:\Users\casey\Desktop\Homesteader\tools\_curl_transformer1.log.err',
    'C:\Users\casey\Desktop\Homesteader\tools\_curl_text3.log.out',
    'C:\Users\casey\Desktop\Homesteader\tools\_download_step4.log'
)
foreach ($l in $logs) {
    if (Test-Path $l) {
        $sz = (Get-Item $l).Length
        Write-Host ("{0} ({1} B)" -f (Split-Path $l -Leaf), $sz)
    } else {
        Write-Host ("{0}: (missing)" -f (Split-Path $l -Leaf))
    }
}
