"""_smoke_hunyuandit_distilled.py - tiny test to load + run HunyuanDiT-Distilled."""

import os, time
os.environ.setdefault("HF_HOME", r"C:\Users\casey\.cache\huggingface")

# Standard diffusers pipeline + safety checker off.
import torch
from diffusers import HunyuanDiTPipeline

t0 = time.time()
print("[smoke-distill] loading HunyuanDiT-Distilled (fp16)...")
pipe = HunyuanDiTPipeline.from_pretrained(
    "Tencent-Hunyuan/HunyuanDiT-v1.2-Diffusers-Distilled",
    torch_dtype=torch.float16,
    safety_checker=None,
    feature_extractor=None,
)
pipe.to("cuda")
print(f"[smoke-distill] pipe loaded in {time.time()-t0:.1f}s; "
      f"max mem: {torch.cuda.max_memory_allocated()/1e9:.2f} GB")

prompt = ("a clean iso icon of a small log cabin, orthographic projection, "
         "parallel projection, no perspective foreshortening, no vanishing "
         "points, eye-level camera, single subject centered in empty space, "
         "floating, low-poly faceted style with visible flat-shaded polygon "
         "planes, solid flat dark slate background (#2b3442), no horizon "
         "line, no ground plane, no scenery, no props")
neg = ("trees, forest, grass, ground plane, sky, sun, sunlight, environment, "
       "scene, landscape, watermark, text, logo, signature, frame, border, "
       "photorealistic, smooth gradient, hyper-detailed, person, character, "
       "perspective camera, vanishing point, horizon line")

t1 = time.time()
gen = torch.Generator(device="cuda").manual_seed(0)
img = pipe(
    prompt=prompt,
    negative_prompt=neg,
    num_inference_steps=20,    # distilled uses ~20 steps usually
    width=768, height=768,
    guidance_scale=3.0,
    generator=gen,
).images[0]
dt = time.time() - t1
out = r"C:\Users\casey\Desktop\Homesteader\_procgen_test\_distilled_smoke\cabin.png"
os.makedirs(os.path.dirname(out), exist_ok=True)
img.save(out, "PNG")
print(f"[smoke-distill] cabin in {dt:.1f}s -> {out}")
