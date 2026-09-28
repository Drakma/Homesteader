import os
import torch
from diffusers import QwenImage21Pipeline

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

model_path = r"C:\Users\casey\Desktop\models\Qwen-Image-2.1"
print("Loading pipeline...")
pipe = QwenImage21Pipeline.from_pretrained(
    model_path,
    torch_dtype=torch.bfloat16,
)
print("Enabling model cpu offload...")
pipe.enable_model_cpu_offload()

print("Checking transformer modules...")
print("Transformer processor:", type(pipe.transformer.transformer_blocks[0].attn.processor))
print("Transformer dtype:", pipe.transformer.dtype)

prompt = "A red apple on a wooden table"
print("Starting generation with steps=1...")
try:
    res = pipe(prompt, num_inference_steps=1, width=256, height=256)
    print("Success! Generated image:", res.images[0].size)
except Exception as e:
    import traceback
    traceback.print_exc()
