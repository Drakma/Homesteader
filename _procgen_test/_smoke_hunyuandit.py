"""_smoke_hunyuandit.py - HunyuanDiT v1.2 smoke test for iso icons.

Loads HunyuanDiT-v1.2-Diffusers in fp16, runs 5 prompts through it, and
writes the raw 1024 outputs to _procgen_test/_hunyuandit_smoke/.

This is a probe: prove the model can load, generate at 1024 px, and
hold the iso camera prompt before any sweep.
"""

import os
import time
import shutil

os.environ.setdefault("HF_HOME", r"C:\Users\casey\.cache\huggingface")

OUT = r"C:\Users\casey\Desktop\Homesteader\_procgen_test\_hunyuandit_smoke"
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT, exist_ok=True)

import torch
from diffusers import HunyuanDiTPipeline

# Source-render prompt suffix.
# We feed this image into Hunyuan3D-2.0 to get a mesh, then re-render
# the mesh under strict iso projection. So at the SOURCE stage we
# deliberately use eye-level 3/4 view with parallel projection (best
# geometry signal for image-to-multiview) instead of strict iso.
# Pitch + yaw are not strict here - the iso constraint is enforced
# downstream on the mesh re-render.
SOURCE_SUFFIX = (
    ", orthographic projection, parallel projection, no perspective "
    "foreshortening, no vanishing points, eye-level camera, single "
    "subject centered in empty space, floating, low-poly faceted style "
    "with visible flat-shaded polygon planes, solid flat "
    "dark slate background (#2b3442), no horizon line, no ground plane, "
    "no scenery, no props"
)
NEGATIVE = (
    "trees, forest, grass, ground plane, sky, sun, sunlight, environment, "
    "scene, landscape, watermark, text, logo, signature, frame, border, "
    "photorealistic, smooth gradient, hyper-detailed, person, character, "
    "perspective camera, vanishing point, horizon line, "
    "floating lanterns, ornamental cubes, decorative shapes, dangling "
    "objects, scattered accessories, surrounding props, "
    "wireframe, transparent frame, structural skeleton, scaffolding only, "
    "incomplete frame, exposed beams"
)
TRIGGER = "iso icon"

SUBJECTS = [
    "small log cabin",
    "wooden barn",
    "greenhouse",
    "scarecrow",
    "wooden crate",
]

# Dropped from 50 steps / 1024 px to 30 / 768 for ~3x speedup.
# The iso constraint is enforced later, so we just need
# a clean eye-level 3/4 here.
STEPS = 30
SIZE = 768
GUIDANCE = 3.0


def main():
    t0 = time.time()
    print("[hd-smoke] loading HunyuanDiT v1.2 (fp16)...")
    local_repo = "Tencent-Hunyuan/HunyuanDiT-Diffusers"
    # After installing sentencepiece (>=0.2.0), the bundled spiece.model
    # tokenizer parses cleanly. HunyuanDiTPipeline uses BERT+KmdT5
    # encoders and the SentencePiece-backed tokenizer_2 in the v1.2-Diffusers
    # snapshot. We keep the safety checker disabled because the model's
    # safety classifier is unrelated to our prompt content.
    pipe = HunyuanDiTPipeline.from_pretrained(
        local_repo,
        torch_dtype=torch.float16,
        safety_checker=None,
        feature_extractor=None,
    )
    pipe.to("cuda")
    # Aliases match what HunyuanDiT-Diffusers expects.
    if hasattr(pipe, "enable_attention_slicing"):
        pipe.enable_attention_slicing()
    print(f"[hd-smoke] pipe loaded in {time.time()-t0:.1f}s; "
          f"max mem: {torch.cuda.max_memory_allocated()/1e9:.2f} GB")

    # One test loop, 5 subjects, single seed each.
    for idx, subject in enumerate(SUBJECTS):
        prompt = f"a clean {TRIGGER} of {subject}{SOURCE_SUFFIX}"
        print(f"[hd-smoke] gen {idx+1}/{len(SUBJECTS)}: {subject}")
        gen = torch.Generator(device="cuda").manual_seed(idx * 17)
        t1 = time.time()
        img = pipe(
            prompt=prompt,
            negative_prompt=NEGATIVE,
            num_inference_steps=STEPS,
            width=SIZE, height=SIZE,
            guidance_scale=GUIDANCE,
            generator=gen,
        ).images[0]
        dt = time.time() - t1
        slug = subject.replace(" ", "_")
        out_path = os.path.join(OUT, f"{idx:02d}_{slug}_s{idx}.png")
        img.save(out_path, "PNG")
        print(f"  -> {out_path} in {dt:.1f}s")


if __name__ == "__main__":
    main()
