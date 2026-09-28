"""_sweep_source.py - production source-render sweep.

For each item in our 30-item sample, generate one source render via
HunyuanDiT-Distilled at 768x768 / 20 steps / batch=8. Output goes to
assets/_source_renders_v1/ as <category>/<item_id>.png.

These source renders are intended to feed Hunyuan3D-2.0 -> Modly ->
mesh -> Blender iso re-render -> catalog icon. Iso enforcement lives
downstream; the source stage is strict orthographic eye-level 3/4.
"""

import argparse
import os
import time
import torch
os.environ.setdefault("HF_HOME", r"C:\Users\casey\.cache\huggingface")

from diffusers import HunyuanDiTPipeline

# Hand-picked 30 representative items across the categories the icon
# catalog actually ships - 1 concept per item folder.
SAMPLE = [
    # structures (10)
    ("structures", "barn", "Barn"),
    ("structures", "chicken_coop", "Chicken Coop"),
    ("structures", "small_cabin", "Small Cabin"),
    ("structures", "large_log_cabin", "Large Log Cabin"),
    ("structures", "greenhouse", "Greenhouse"),
    ("structures", "stable", "Stable"),
    ("structures", "farmhouse", "Farmhouse"),
    ("structures", "starter_house", "Starter House"),
    ("structures", "windmill", "Windmill"),
    ("structures", "silo", "Silo"),
    # farming (5)
    ("farming", "corn", "Corn Crop"),
    ("farming", "wheat", "Wheat Crop"),
    ("farming", "carrot", "Carrot Plant"),
    ("farming", "pumpkin", "Pumpkin Plant"),
    ("farming", "tomato", "Tomato Plant"),
    # ranching (5)
    ("ranching", "cow", "Cow"),
    ("ranching", "pig", "Pig"),
    ("ranching", "chicken", "Chicken"),
    ("ranching", "sheep", "Sheep"),
    ("ranching", "horse", "Horse"),
    # fishing (5)
    ("fishing", "trout", "Trout"),
    ("fishing", "bass", "Bass"),
    ("fishing", "fishing_rod", "Fishing Rod"),
    ("fishing", "lure", "Fishing Lure"),
    ("fishing", "tackle_box", "Tackle Box"),
    # fuel (5)
    ("fuel", "jerry_can", "Jerry Can"),
    ("fuel", "propane_tank", "Propane Tank"),
    ("fuel", "gas_pump", "Gas Pump"),
    ("fuel", "firewood", "Firewood Stack"),
    ("fuel", "camp_stove", "Camp Stove"),
]

# Strict source-render prompt: orthographic 3/4 eye-level, no iso enforcement
# (iso enforcement happens downstream). Low-poly faceted. Single subject.
# Compact source-render prompt. Tight, fits CLIP's 77-token limit.
# Platform-removal language is a POSITIVE bias ("absolutely suspended
# in pure empty space with no surface beneath"), because HunyanDiT
# treats negative-list items as weak signals. Negative list still
# tries to remove common prop coupling (fence, plant, accessories,
# secondary objects).
SOURCE_SUFFIX = (
    "absolutely suspended floating alone in pure empty space, no "
    "surface beneath, no contact with anything below, no ground, "
    "no floor, no platform, orthographic eye-level 3/4 view, "
    "parallel projection, no vanishing points, low-poly faceted "
    "style with visible flat polygons, single subject only, "
    "solid flat dark slate background"
)
NEGATIVE = (
    "platform, pedestal, base, ground, dirt, sand, soil, terrain, "
    "floor, contact surface, trees, forest, grass, sky, scenery, "
    "watermark, text, frame, smooth gradient, photorealistic, "
    "hyper-detailed, perspective camera, vanishing point, horizon "
    "line, person, character, scaffolding, ornamental cubes, "
    "scattered accessories, neighboring objects, secondary object"
)
TRIGGER = "iso icon"

STEPS = 16
SIZE = 768
GUIDANCE = 2.0   # lower CFG so prompt-bleed (fence, plant, etc.) is reduced
BATCH_SIZE = 1   # one prompt per pipeline call; keeps cross-attention fully on GPU


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=r"C:\Users\casey\Desktop\Homesteader\assets\_source_renders_v1")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--start", type=int, default=0)
    args = ap.parse_args()

    items = SAMPLE if args.limit == 0 else SAMPLE[: args.limit]
    os.makedirs(args.out, exist_ok=True)

    # Pre-create category dirs.
    cats = set(c for c, _, _ in items)
    for c in cats:
        os.makedirs(os.path.join(args.out, c), exist_ok=True)

    print(f"[sweep-source] loading HunyuanDiT-Distilled (fp16)...")
    t0 = time.time()
    pipe = HunyuanDiTPipeline.from_pretrained(
        "Tencent-Hunyuan/HunyuanDiT-v1.2-Diffusers-Distilled",
        torch_dtype=torch.float16,
        safety_checker=None,
        feature_extractor=None,
    )
    pipe.to("cuda")
    print(f"[sweep-source] pipe loaded in {time.time()-t0:.1f}s; "
          f"max mem: {torch.cuda.max_memory_allocated()/1e9:.2f} GB")

    # Run sweep in batches of BATCH_SIZE.
    summary = ["# Source renders", "=" * 60]
    n_done = 0
    for batch_start in range(args.start, len(items), BATCH_SIZE):
        batch = items[batch_start: batch_start + BATCH_SIZE]
        prompts = []
        for cat, item_id, subject in batch:
            prompts.append(f"a clean {TRIGGER} of {subject}{SOURCE_SUFFIX}")
        gens = [torch.Generator(device="cuda").manual_seed(batch_start + i)
                for i in range(len(batch))]
        t1 = time.time()
        try:
            images = pipe(
                prompt=prompts,
                negative_prompt=[NEGATIVE] * len(batch),
                num_inference_steps=STEPS,
                width=SIZE, height=SIZE,
                guidance_scale=GUIDANCE,
                generator=gens,
            ).images
        except Exception as e:
            print(f"[sweep-source] batch {batch_start} FAILED: "
                  f"{type(e).__name__}: {e}")
            # Fall back to one-at-a-time for this batch.
            images = []
            for p in prompts:
                try:
                    img = pipe(
                        prompt=p, negative_prompt=NEGATIVE,
                        num_inference_steps=STEPS, width=SIZE, height=SIZE,
                        guidance_scale=GUIDANCE,
                        generator=torch.Generator(device="cuda").manual_seed(0),
                    ).images[0]
                    images.append(img)
                except Exception as e2:
                    print(f"[sweep-source]  one-of-batch FAIL on item "
                          f"{len(images)}: {e2}")
                    break
        dt = time.time() - t1
        # Save images.
        for (cat, item_id, subject), img in zip(batch, images):
            out_path = os.path.join(args.out, cat, f"{item_id}.png")
            img.save(out_path, "PNG")
            n_done += 1
            summary.append(f"  {cat}/{item_id:<24} {subject}")
            print(f"[sweep-source] {n_done:02d}/{len(items)} "
                  f"{cat}/{item_id} <- {dt / max(1, len(batch)):.1f}s "
                  f"(batch wall)")

    with open(os.path.join(args.out, "_summary.txt"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(summary))
    print(f"[sweep-source] wrote {n_done} renders; _summary.txt")


if __name__ == "__main__":
    main()
