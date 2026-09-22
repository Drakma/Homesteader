# Local Qwen-Image-2.1 generation for Homesteader

> **TL;DR.** Two scripts — one runs the model, one verifies the environment and
> emits (does NOT auto-run) install + weight-download commands. The Homesteader
> asset pipeline is **Meshy text-to-3D only** (`tools/meshy_client.py`);
> `tools/free_generator.py` and the old FLUX + Hunyuan3D-2 stack are **retired —
> everything costs money**. This local option is a **supplemental** route for
> local experimentation, not part of the asset pipeline.

## What this is

`tools/qwen_image_local.py` is a thin CLI around Alibaba's
[Qwen-Image-2.1](https://huggingface.co/Qwen/Qwen-Image-2.1) image model,
loaded via `diffusers.QwenImage21Pipeline` from the snippets in the model's
Hugging Face model card.

| Property | Value |
|---|---|
| HF repo | `Qwen/Qwen-Image-2.1` |
| Pipeline class | `diffusers.QwenImage21Pipeline` |
| Params | 7.1 B (visual generation component) |
| On-disk size (BF16) | ~47 GB |
| License | **Qwen Research License Agreement** — research-only, **NOT Apache 2.0**, no commercial use without a separate agreement. See `LICENSE` inside the model repo. |
| Created | 2026-09-14 (HF last-modified 2026-09-20) |
| Architecture | 32 Single-Stream DiT layers, mixed-granularity attention, prefix KV cache reuse |

`tools/install_qwen_image.py` is a one-time environment helper. It probes the
active Python (`C:\Python313\python.exe`) for a CUDA-enabled torch, writes a
pin file (`requirements_qwen_image.txt`), and **prints** the install + weight
download commands. It does not run pip; it does not download weights. Disk
spend and install choices are yours.

## Why this script *does not* replace the existing free pipeline

Per project policy:

> The pipeline is **Meshy text-to-3D only** — there is no free stack. See
> `docs/MESHY_PIPELINE_GUIDE.md`.

This script sits **next to** `free_generator.py`, not in front of it. It's
useful when:

- The HF Spaces / Pollinations API is rate-limiting.
- You want **native RGBA / transparency output** (the model card documents
  this and `--transparent` flips it on). This is genuinely valuable for the
  Homesteader icon spec — you can pipe directly into
  `regen_icons.standardize_icon_image()`.
- You want **higher-quality base renders** than FLUX.1 [schnell]'s 4-step
  pipeline.

It is **not** useful for:

- Bulk asset runs (each image takes minutes; HF Spaces cost nothing and
  parallelize better).
- Anything where the model card's license is incompatible with your
  downstream use — the Qwen Research License is research-only.

## Hardware you'll actually need

The installer's probe on the host where this was authored reports:

```
torch: 2.6.0+cu124
cuda:  available=True, device=NVIDIA GeForce GTX 1080 Ti
total_GB: 11.0
```

That 1080 Ti sits exactly in the sweet spot the model was designed for.
Numbers worth knowing:

| Mode | VRAM (on-GPU, no offload) | Resolution | Time per image (1080 Ti, fp16/bf16) |
|---|---|---|---|
| BF16 full weights (`Qwen/Qwen-Image-2.1`) | ~14-16 GB | 1024² | falls back to CPU offload on 11 GB cards |
| BF16 + `enable_model_cpu_offload()` | ~7-8 GB on-GPU; rest on CPU | 1024² | **30-90 s** |
| `AlperKTS/Qwen-Image-2.1-GGUF` `Q8_0` (7.62 GB) | ~9 GB | 1024² | **20-45 s** |
| `AlperKTS/Qwen-Image-2.1-GGUF` `Q6_K` (5.84 GB) | ~7 GB | 2048² | **30-60 s** |
| `AlperKTS/Qwen-Image-2.1-GGUF` `Q5_K_M` (4.89 GB) | ~5.5 GB | 1024² | **20-40 s** |

The numbers above are *estimates*, not benchmarks — drop a `--steps
8 --seed 0` smoke-test into `assets/_qwen_local/` and time it on your own
hardware before committing to a long batch. The script will log actual
elapsed seconds.

A few ProTips:

- **Pascal tip (your 1080 Ti, CC 6.1).** bf16 is supported but falls back to
  fp16 numerics on tensor cores at this compute capability. If you see weird
  NaN losses, fall back to `--dtype fp16`. Genuine bf16 acceleration starts at
  Ampere (CC 8.0+).
- **WMI lied about your VRAM.** A previous probe of
  `Get-CimInstance Win32_VideoController` reported both your 970 and 1080 Ti
  at 4 GB; that's because `AdapterRAM` is a 32-bit unsigned field that caps at
  ~4 GB. This script reads `torch.cuda.get_device_properties(...).total_memory`
  instead, which is correct.
- **Memory growth during the first call.** The first invocation after cache
  populates the diffusers pipeline gets a slow first step (CaMeL-case model
  load into pinned memory). Subsequent calls are much faster.

## Install — manual, on purpose

```
# Probe only (no writes):
python tools\install_qwen_image.py --check-only

# Print commands (also writes requirements_qwen_image.txt):
python tools\install_qwen_image.py --print-commands

# Print commands plus GGUF quantization paths:
python tools\install_qwen_image.py --print-commands --gguf
```

After the printed commands complete, smoke-test:

```
python tools\qwen_image_local.py --prompt "a barn exterior in winter" --transparent
```

Defaults in the CLI:

- `--aspect 1:1`, i.e. `1024 x 1024` (safe on 8 GB cards; safe-er on 11 GB)
- `--steps 40` (matches the model card)
- `--seed 42` (for reproducibility)
- `--dtype bf16`
- `--cpu-offload` enabled automatically when total VRAM < 8 GB; explicit on
  request above that

Useful flags:

- `--width 2048 --height 2048` to attempt native 2K (need 11 GB VRAM + CPU
  offload; or switch to the Q6_K GGUF).
- `--transparent` flips RGBA α on. The model needs a magic suffix on the
  prompt — the script appends the exact phrase the model card documents.
- `--edit path\to\foo.png` runs instruction-based edit on an existing image.
- `--no-offload` to skip CPU offload (only sensible on 11+ GB cards).
- `--force-fit` to bypass the `< 6 GB VRAM` refusal (will OOM, probably).

## Where this sits in the project

- Untouched: `tools/free_generator.py`, `tools/check_syntax.py`, `tools/server.py`,
  the asset-request watcher, `assets/index.html` (the hand-edited source).
- Added:
  - `tools/qwen_image_local.py` — inference CLI.
  - `tools/install_qwen_image.py` — environment helper.
  - `tools/requirements_qwen_image.txt` — written by the installer; pin file.
  - `tools/QWEN_IMAGE_README.md` — this file.
- Future: a small bridge in `free_generator.py` that calls
  `qwen_image_local.py` when the user opts in via the "Generation Pipeline"
  dropdown — but that is a separate task and must not break the free default.

## License reminder

The Qwen team dropped Apache 2.0 for the 2.x line in favor of the **Qwen
Research License Agreement** — research-use-only, no commercial deployment
without a separate agreement. This is documented in the model repo's
`LICENSE` file and was called out by both the [Qwen 2.1 blog post](https://qwen.ai/blog?id=qwen-image-2.1)
and the [AI Weekly writeup](https://aiweekly.co/alerts/alibaba-ships-qwen-image-21-7b-dit-with-native-2048x2048-and-rgba-drops-apache).
If you're shipping a commercial game and the rendered images end up in the
shipped product, **read** that license before integrating this pipeline.

## Sources

- Model card / weights: <https://huggingface.co/Qwen/Qwen-Image-2.1>
- Pipeline PR / class: <https://huggingface.co/docs/diffusers/main/en/api/pipelines/qwenimage>
- Comfy tutorial: <https://docs.comfy.org/tutorials/image/qwen/qwen-image>
- ComfyUI 2.1 announcement: <https://blog.comfy.org/p/qwen-image-21-in-comfyui-open-weight>
- GGUF quantization (community): <https://huggingface.co/AlperKTS/Qwen-Image-2.1-GGUF>
- Comfy-Org split checkpoints: <https://huggingface.co/Comfy-Org/Qwen-Image-2.1>
- Original Qwen-Image (Aug 2025, Apache 2.0): <https://huggingface.co/Qwen/Qwen-Image>
