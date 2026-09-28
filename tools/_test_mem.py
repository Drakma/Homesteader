import os
import sys
import psutil

def get_mem():
    p = psutil.Process()
    vm = psutil.virtual_memory()
    print(f"Process RSS: {p.memory_info().rss / 1024**3:.2f} GB | Sys RAM Free: {vm.available / 1024**3:.2f} GB / {vm.total / 1024**3:.2f} GB")

print("Stage 0: start")
get_mem()

import torch
print("Stage 1: imported torch")
get_mem()

from diffusers import QwenImage21Pipeline
print("Stage 2: imported pipeline")
get_mem()

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
model_path = r"C:\Users\casey\Desktop\models\Qwen-Image-2.1"

print("Stage 3: from_pretrained...")
pipe = QwenImage21Pipeline.from_pretrained(
    model_path,
    torch_dtype=torch.bfloat16,
)
print("Stage 4: loaded pipeline")
get_mem()

print("Stage 5: enable_model_cpu_offload...")
pipe.enable_model_cpu_offload()
print("Stage 6: offloaded")
get_mem()
