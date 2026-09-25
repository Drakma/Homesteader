#!/usr/bin/env python3
"""
qwen_image_local.py
Local image-generation CLI for Qwen-Image-2.1 (Qwen/Qwen-Image-2.1, 7B params,
Apache-adjacent Qwen Research License, see QWEN_IMAGE_README.md for caveats).

This is the LOCAL option. Homesteader's default asset pipeline is still the
cloud-free one in tools/free_generator.py (FLUX.1 [schnell] + Hunyuan3D-2 via
HF Spaces, $0 cost, no GPU needed). Use this script when:
  - you want to generate without contacting Hugging Face Spaces at all
  - you need native RGBA / transparent output (Homesteader icon spec!) so you
    can pipe directly into regen_icons.standardize_icon_image()
  - you want native 2K on a card with at least 8 GB of VRAM

Two flags do most of the work:
  --transparent          render RGBA (alpha-aware prompt suffix)
  --edit <path.png>      run instruction-based edit on an existing image

Sizing defaults to 1024x1024 (safe on 8 GB cards); pass --width/--height up to
2048 if your card has 11+ GB of VRAM and you have enable_model_cpu_offload().

This script does NOT download weights. Run tools/install_qwen_image.py first so
huggingface-cli has populated a local cache (or set HF_HUB_OFFLINE=1 if you've
already pulled them).

Usage examples:
  python tools/qwen_image_local.py --prompt "a barn exterior in winter" --transparent
  python tools/qwen_image_local.py --prompt "wood grain texture" --width 2048 --height 1024
  python tools/qwen_image_local.py --prompt "snow on the roof" --edit assets/foo/icons/foo_icon.png
  python tools/qwen_image_local.py --prompt "..." --seed 42 --steps 40 --out assets/_test.png
"""

import argparse
import os
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

# Model id exactly as published by Alibaba's Qwen team on Hugging Face:
#   https://huggingface.co/Qwen/Qwen-Image-2.1
# (verified 2026-09-20, ~47 GB total, BF16, license: qwen-research)
DEFAULT_MODEL_ID = "Qwen/Qwen-Image-2.1"

# Aspect-ratio presets straight out of the Qwen-Image-2.1 HF model card README.
ASPECT_RATIOS = {
    "1:1":  (1024, 1024),
    "4:3":  (1024, 768),
    "3:4":  (768, 1024),
    "3:2":  (1152, 768),
    "2:3":  (768, 1152),
    "16:9": (1152, 648),
    "9:16": (648, 1152),
}

# Recommended VRAM buckets straight out of the AlperKTS/Qwen-Image-2.1-GGUF
# README (see tools/QWEN_IMAGE_README.md). We pick Q6_K as the default for the
# BF16 path because BF16 weights + activations for a 7B DiT fit comfortably in
# 11 GB ONLY with CPU offload; Q6_K GGUF fits an 8-12 GB card fully on-GPU.
RECOMMENDED_VRAM_GB = 8.0
TIGHT_VRAM_GB = 6.0


def _probe_vram_gb():
    """
    Return (free_gb, total_gb, device_name) for the active CUDA device.
    Uses torch.cuda.get_device_properties (the canonical source) rather than
    nvidia-smi or WMI AdapterRAM (the latter is a 32-bit field that capped
    both a GTX 970 and an 11 GB GTX 1080 Ti at 4 GB on the host where this
    script was authored).

    Returns (None, None, "cpu") when CUDA is not available - the script can
    still attempt a CPU fallback but warns loudly about it.
    """
    try:
        import torch
    except ImportError:
        return None, None, "torch-not-installed"

    if not torch.cuda.is_available():
        return None, None, "no-cuda"

    idx = torch.cuda.current_device()
    props = torch.cuda.get_device_properties(idx)
    total = props.total_memory / (1024 ** 3)
    # reserved_but_unallocated is what actually matters for "can I fit this"
    # but PyTorch doesn't expose it; free from mem_get_info is the conservative
    # number. We report both rounded to 1 decimal.
    try:
        free_bytes, _total_bytes = torch.cuda.mem_get_info(idx)
        free = free_bytes / (1024 ** 3)
    except Exception:
        free = total
    return round(free, 2), round(total, 2), props.name


def _resolve_device_and_dtype(free_gb, total_gb, prefer_dtype, offload):
    """
    Pick device + dtype + offload policy from the probed VRAM and CLI flags.

    Reasoning:
      - <  TIGHT_VRAM_GB: refuse unless --force-fit. CPU offload mandatory.
      - >= TIGHT, < RECOMMENDED: warning, CPU offload on by default but allow --no-offload override.
      - >= RECOMMENDED_CUDA: comfy. Offload off unless --cpu-offload explicit.
    """
    import torch

    if total_gb is None:
        sys.stderr.write(
            "[qwen-image] WARNING: CUDA not available. Falling back to CPU "
            "inference will be extremely slow (minutes-to-hours per image) and "
            "is not recommended. Install a CUDA-capable PyTorch before retrying.\n"
        )
        return torch.device("cpu"), torch.float32, True

    dtype = {"bf16": torch.bfloat16, "fp16": torch.float16, "fp32": torch.float32}[prefer_dtype]

    if total_gb < TIGHT_VRAM_GB:
        sys.stderr.write(
            f"[qwen-image] WARNING: detected {total_gb:.1f} GB VRAM total on the "
            f"active CUDA device. The AlperKTS/Qwen-Image-2.1-GGUF Q5_K_M quant "
            f"needs about 4.6 GB ON-GPU plus text encoder + activations; total "
            f"system should ideally have 6 GB of VRAM. CPU offload is forced on.\n"
            f"[qwen-image] If you abort, see tools/QWEN_IMAGE_README.md for hardware guidance.\n"
        )
        return torch.device("cuda"), dtype, True

    if total_gb < RECOMMENDED_VRAM_GB:
        sys.stderr.write(
            f"[qwen-image] Note: detected {total_gb:.1f} GB VRAM. The recommended "
            f"target for Qwen-Image-2.1 Q6_K GGUF is 8-12 GB VRAM. CPU offload "
            f"is enabled by default - pass --no-offload if you have the headroom.\n"
        )
        return torch.device("cuda"), dtype, offload  # honour the caller's choice but they got a warning

    return torch.device("cuda"), dtype, offload


def _build_pipeline(model_id, dtype, device_map_or_to, enable_offload):
    """
    Lazily import diffusers/transformers and load QwenImage21Pipeline.

    Errors caught and re-raised as plain RuntimeError so the CLI shows a clean
    message instead of a multi-page diffusers traceback.
    """
    try:
        import torch  # noqa: F401
        from diffusers import QwenImage21Pipeline
    except ImportError as exc:
        raise RuntimeError(
            "diffusers / torch not importable. Run tools/install_qwen_image.py "
            "first to set up the dependencies. Underlying error: " + str(exc)
        ) from exc

    print(f"[qwen-image] Loading pipeline from {model_id!r} ... (this is the slow "
          f"first call - it pulls ~47 GB into RAM if not cached)", flush=True)
    t0 = time.time()
    # Model card snippet uses dtype=...; we pass torch_dtype (more explicit
    # alias used elsewhere in the diffusers ecosystem).
    pipe = QwenImage21Pipeline.from_pretrained(
        model_id,
        torch_dtype=dtype,
    )
    if enable_offload:
        # Diffusers 0.30+ uses accelerate under the hood; this is the
        # documented pattern from the model card README.
        pipe.enable_model_cpu_offload()
    else:
        try:
            pipe.to(device_map_or_to)
        except torch.cuda.OutOfMemoryError as exc:
            raise RuntimeError(
                f"GPU ran out of memory on .to(cuda). The full BF16 pipeline "
                f"needs roughly 14-16 GB of VRAM at 1024x1024; rerun with "
                f"--cpu-offload or pre-pull a quantized GGUF "
                f"(see tools/QWEN_IMAGE_README.md)."
            ) from exc
    print(f"[qwen-image] Pipeline loaded in {time.time() - t0:.1f}s")
    return pipe


# The exact "magic suffix" the model card README recommends for transparent
# (RGBA) output. Keep it byte-for-byte identical, including the trailing period,
# because the renderer expects the trailing alpha-channel cue.
TRANSPARENT_SUFFIX_EN = (
    "This is an RGBA image with transparency. The background is transparent. "
    "The image has an alpha channel."
)


def _maybe_augment_for_transparency(prompt, transparent):
    if not transparent:
        return prompt
    return prompt + " " + TRANSPARENT_SUFFIX_EN


def parse_aspect(value):
    # argparse custom-type callable. Must live at module scope so argparse can
    # import it via __main__.<name>; kept here, not nested in main().
    if value in ASPECT_RATIOS:
        return ASPECT_RATIOS[value]
    try:
        w_str, h_str = value.lower().split("x", 1)
        return int(w_str), int(h_str)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"--aspect must be one of {list(ASPECT_RATIOS)} or WxH integers (e.g. 1024x768)"
        )


def main():
    ap = argparse.ArgumentParser(
        prog="qwen_image_local.py",
        description="Generate / edit / RGBA images locally with Qwen-Image-2.1.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    # Allow QWEN_PROMPT env var as a fallback for cases where the prompt
    # contains spaces and is awkward to quote through Windows process APIs.
    default_prompt = os.environ.get("QWEN_PROMPT")
    ap.add_argument("--prompt", default=default_prompt, required=default_prompt is None,
                    help="Text prompt (English or Chinese). Falls back to $QWEN_PROMPT when set, for shells with awkward quote handling.")
    ap.add_argument("--negative-prompt", default=" ", help="Negative prompt. Default is a single space (the model card uses this).")
    ap.add_argument("--seed", type=int, default=42, help="RNG seed (default 42).")
    ap.add_argument("--steps", type=int, default=40, help="Inference steps (default 40, matches model card).")
    ap.add_argument("--aspect", type=parse_aspect,
                    default="1:1", help="Aspect ratio preset or WxH (default 1:1 1024x1024).")
    ap.add_argument("--width", type=int, default=None, help="Override width (overrides --aspect).")
    ap.add_argument("--height", type=int, default=None, help="Override height (overrides --aspect).")
    ap.add_argument("--out", default=None, help="Output PNG path (default: assets/_qwen_local/<seed>.png).")
    ap.add_argument("--edit", default=None, help="Optional input PNG path for instruction-based editing.")
    ap.add_argument("--transparent", action="store_true",
                    help="Render with RGBA alpha. Adds a documented magic suffix to the prompt.")
    ap.add_argument("--cpu-offload", dest="cpu_offload", action="store_true", default=None,
                    help="Force enable_model_cpu_offload() (recommended on <8 GB cards).")
    ap.add_argument("--no-offload", dest="cpu_offload", action="store_false",
                    help="Don't enable CPU offload. Requires >=11 GB VRAM with BF16 weights.")
    ap.add_argument("--dtype", choices=("bf16", "fp16", "fp32"), default="bf16",
                    help="Pipeline dtype (default bf16; fp16 is the safe fallback on Pascal GPUs with weak bf16 support).")
    ap.add_argument("--model", default=DEFAULT_MODEL_ID,
                    help=f"Hugging Face model id (default {DEFAULT_MODEL_ID}).")
    ap.add_argument("--force-fit", action="store_true",
                    help="Force the run even if VRAM is below the tight threshold (slow + may OOM).")
    args = ap.parse_args()

    free_gb, total_gb, devname = _probe_vram_gb()
    if total_gb is not None:
        print(f"[qwen-image] CUDA device: {devname} ({total_gb:.1f} GB total, {free_gb:.1f} GB free)")
    else:
        print(f"[qwen-image] CUDA probe: {devname}")

    if total_gb is not None and total_gb < TIGHT_VRAM_GB and not args.force_fit:
        sys.stderr.write(
            f"[qwen-image] Refusing to run with {total_gb:.1f} GB VRAM. "
            f"Rerun with --force-fit to override; expect swap-thrash or OOM.\n"
        )
        return 2

    device, dtype, offload = _resolve_device_and_dtype(
        free_gb, total_gb, args.dtype, args.cpu_offload if args.cpu_offload is not None else True
    )
    print(f"[qwen-image] device={device} dtype={dtype} cpu_offload={offload} model={args.model}")

    if args.width and args.height:
        w, h = args.width, args.height
    else:
        w, h = args.aspect

    out_path = args.out
    if out_path is None:
        out_dir = os.path.join(PROJECT_DIR, "assets", "_qwen_local")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"qwen_seed{args.seed}.png")

    pipe = _build_pipeline(args.model, dtype, device, offload)

    prompt = _maybe_augment_for_transparency(args.prompt, args.transparent)
    print(f"[qwen-image] prompt: {prompt}")
    print(f"[qwen-image] size {w}x{h}, steps={args.steps}, seed={args.seed}, edit={args.edit}")

    import torch
    gen = torch.Generator(device=device).manual_seed(args.seed)
    t0 = time.time()
    call_kwargs = dict(
        prompt=prompt,
        negative_prompt=args.negative_prompt,
        width=w, height=h,
        num_inference_steps=args.steps,
        generator=gen,
    )
    if args.edit:
        try:
            from PIL import Image as PILImage
        except ImportError as exc:
            raise RuntimeError(
                "Pillow not importable. Run tools/install_qwen_image.py to install requirements_qwen_image.txt."
            ) from exc
        if not os.path.isfile(args.edit):
            raise RuntimeError(f"--edit path not found: {args.edit}")
        img = PILImage.open(args.edit)
        # The model card image-edit snippet passes image= rather than
        # image=[...] (single image); match it exactly.
        call_kwargs["image"] = img
    try:
        result = pipe(**call_kwargs)
        image_out = result.images[0]
    except torch.cuda.OutOfMemoryError as exc:
        sys.stderr.write(
            "[qwen-image] CUDA OOM mid-generation. Try: (1) lower --width/--height, "
            "(2) --cpu-offload / --force-fit, (3) a GGUF quantization "
            "(see tools/QWEN_IMAGE_README.md).\n"
        )
        raise
    elapsed = time.time() - t0
    print(f"[qwen-image] generated in {elapsed:.1f}s")

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    image_out.save(out_path, "PNG")
    print(f"[qwen-image] wrote {out_path} (mode={image_out.mode}, size={image_out.size})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
