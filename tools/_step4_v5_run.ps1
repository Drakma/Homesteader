# Step 4 v5: kick off remaining 2 downloads with curl.exe in background.
# Each download writes to a separate log file; we start parallel curl processes.

$ErrorActionPreference = 'Continue'
$curl = 'C:\Windows\System32\curl.exe'
$jobs = @(
    @{
        url  = 'https://huggingface.co/Qwen/Qwen-Image-2.1/resolve/main/text_encoder/model-00003-of-00004.safetensors'
        path = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1\text_encoder\model-00003-of-00004.safetensors'
        log  = 'C:\Users\casey\Desktop\Homesteader\tools\_curl_text3.log'
    }
    @{
        url  = 'https://huggingface.co/Qwen/Qwen-Image-2.1/resolve/main/transformer/diffusion_pytorch_model-00001-of-00002.safetensors'
        path = 'C:\Users\casey\Desktop\models\Qwen-Image-2.1\transformer\diffusion_pytorch_model-00001-of-00002.safetensors'
        log  = 'C:\Users\casey\Desktop\Homesteader\tools\_curl_transformer1.log'
    }
)
foreach ($j in $jobs) {
    $dir = Split-Path $j.path -Parent
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    Write-Host ("Starting curl for {0} -> {1}" -f $j.url, $j.path)
    $argList = @(
        $curl, '--location', '--continue-at', '-', '--output', $j.path,
        '--connect-timeout', '30', '--max-time', '7200',
        '--retry', '5', '--retry-delay', '10',
        $j.url, '*>>', $j.log
    )
    Start-Process -FilePath $curl -ArgumentList (
        @('--location','--continue-at','-','--output', $j.path,
          '--connect-timeout','30','--max-time','7200',
          '--retry','5','--retry-delay','10', $j.url)
    ) -RedirectStandardOutput ($j.log + '.out') -RedirectStandardError ($j.log + '.err') `
        -WindowStyle Hidden -PassThru | ForEach-Object {
            Write-Host ("  PID {0} for {1}" -f $_.Id, $j.path)
        }
}
Write-Host 'Started. Poll tools\_step4_v5_poll.ps1 in 60s.'
