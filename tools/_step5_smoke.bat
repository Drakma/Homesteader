@echo off
rem Step 5 smoke-test launcher. Uses .bat so all powershell wildcard breaks
rem are gone.
set "HF_HUB_OFFLINE=1"
set "TRANSFORMERS_OFFLINE=1"
set "PYTHONUNBUFFERED=1"

"C:\Python313\python.exe" -u "C:\Users\casey\Desktop\Homesteader\tools\qwen_image_local.py" ^
    --model "C:\Users\casey\Desktop\models\Qwen-Image-2.1" ^
    --prompt "A small wooden barn exterior under a clear winter sky, sunlight, low angle view, photorealistic" ^
    --steps 4 ^
    --width 1024 ^
    --height 1024 ^
    --cpu-offload ^
    --out "C:\Users\casey\Desktop\Homesteader\assets\_qwen_local\smoke.png"
