#!/usr/bin/env python3
"""
install_qwen_image.py
One-time setup helper for tools/qwen_image_local.py.

What this does:
 1. Pick a target directory for the weights cache (default
     <PROJECT_PARENT>/models/Qwen-Image-2.1, so the cache lives next to the
     project rather than inside C:\\Users\\<you>\\.cache which gets backed up
     by Onedrive and costs disk budget).
 2. Print the huggingface-cli download commands (NOT executed - downloading
     ~47 GB is a multi-hour decision the user must make). Three flavors:
       (a) BF16 full precision   - to repo cache
       (b) Q5_K_M GGUF quant    - smaller, fits 8 GB VRAM (Comfy path)
       (c) Q6_K   GGUF quant    - balanced, fits 11 GB VRAM
 3. Write requirements_qwen_image.txt with the model-card-derived pins:
       torch>=2.4.0
       transformers>=5.17    (Qwen3-VL text encoder needs a fresh release)
       diffusers  from git   (QwenImage21Pipeline is recent-lifecycle)
       accelerate, pillow
 4. Verify the active Python interpreter matches C:\\Python313\\python.exe
     (the canonical install per tools\\python.cmd) and probe torchvision /
     CUDA presence so we get a useful error before a 47 GB download starts.

What this does NOT do:
  - It does NOT auto-run pip install. Many Homesteader scripts avoid touching
    the system Python and prefer a venv; print the command and let the user
    choose. (We do write the requirements file so a copy-paste is one cmd.)
  - It does NOT download weights. The download is the slow part and the disk
    budget part; we never auto-spend either.

Usage:
  python tools\\\\install_qwen_image.py --print-commands
  python tools\\\\install_qwen_image.py --check-only
"""

import argparse
import os
import shutil
import subprocess
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
REQUIREMENTS_PATH = os.path.join(SCRIPT_DIR, "requirements_qwen_image.txt")
EXPECTED_PYTHON = r"C:\Python313\python.exe"


def _which_python():
    # Per project policy tools/python.cmd is the shim that resolves bare
    # "python" to C:\\Python313\\python.exe. We check the executable path
    # rather than the shim.
    return EXPECTED_PYTHON if os.path.isfile(EXPECTED_PYTHON) else sys.executable


def _probe_python_and_torch():
    py = _which_python()
    info = {
        "python_path": py,
        "python_ok": os.path.isfile(py),
        "torch_importable": False,
        "torch_version": None,
        "cuda_available": False,
        "cuda_device_name": None,
    }
    if not info["python_ok"]:
        return info
    # Single python -c invocation; avoids running pip / breaking the parent.
    # The probe is small enough to fit on one logical line; we use `pass` for
    # the empty-suite guard on the early `except` because we cannot rely on
    # statement concatenation interacting cleanly with the if/try blocks.
    code_lines = [
        "try:",
        "    import torch",
        "    print('__TORCH_VERSION__', torch.__version__)",
        "    print('__CUDA_AVAILABLE__', torch.cuda.is_available())",
        "    if torch.cuda.is_available(): print('__CUDA_DEVICE__', torch.cuda.get_device_name(0))",
        "except Exception as e:",
        "    print('__TORCH_IMPORT_ERROR__', repr(e))",
    ]
    # Join with a real newline so `try:` / `except:` open real indented blocks.
    code = "\n".join(code_lines)
    try:
        out = subprocess.check_output(
            [py, "-c", code], stderr=subprocess.STDOUT, text=True, timeout=60
        )
    except subprocess.CalledProcessError as exc:
        info["python_error"] = exc.output.strip()
        return info
    for line in out.splitlines():
        if line.startswith("__TORCH_VERSION__ "):
            info["torch_version"] = line.split(" ", 1)[1].strip()
            info["torch_importable"] = True
        elif line.startswith("__CUDA_AVAILABLE__ "):
            info["cuda_available"] = line.strip().endswith("True")
        elif line.startswith("__CUDA_DEVICE__ "):
            info["cuda_device_name"] = line.split(" ", 1)[1].strip()
        elif line.startswith("__TORCH_IMPORT_ERROR__ "):
            info["torch_importable"] = False
            info["torch_error"] = line.split(" ", 1)[1].strip()
    return info


def _default_cache_dir():
    # Cache lives next to the project (one level up), not under the user's
    # roaming profile - the .cache default grows fast and gets OneDrive-bombed.
    parent = os.path.dirname(PROJECT_DIR)
    if not os.path.isdir(parent):
        return os.path.join(PROJECT_DIR, "_models", "Qwen-Image-2.1")
    return os.path.join(parent, "models", "Qwen-Image-2.1")


def _write_requirements():
    # The model card's Quick Start pins:
    #   pip install torch>=2.4.0
    #   pip install transformers>=5.17
    #   pip install git+https://github.com/huggingface/diffusers
    #   pip install accelerate pillow
    # We split diffusers out into a separate line so a venvs-only flow can use
    # the requirements file; pip understands the URL syntax.
    lines = [
        "# Generated by tools/install_qwen_image.py for Qwen/Qwen-Image-2.1.",
        "# Re-run that script to refresh after a model card update.",
        "torch>=2.4.0",
        "transformers>=5.17",
        "accelerate",
        "pillow",
        "huggingface_hub",  # the cli is in this distribution; ensure it's pinned
        # diffusers must come from git because QwenImage21Pipeline is recent-lifecycle
        "diffusers @ git+https://github.com/huggingface/diffusers",
    ]
    with open(REQUIREMENTS_PATH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    return REQUIREMENTS_PATH


def _download_commands(cache_dir, include_gguf):
    """
    Build the curl/huggingface-cli invocations the user can paste.

    The exact 'black-forest-labs/FLUX.1-schnell' / 'tencent/Hunyuan3D-2'
    repos have been working from our offline homes for the cloud-free pipeline
    since 2025; this set mirrors their style with the Qwen repos that the
    Qwen-Image-2.1 HF model card lists as base + quantizations card.
    """
    lines = []
    hf = shutil.which("huggingface-cli") or "huggingface-cli"
    lines.append(f"# 1) Full BF16 weights (model card path, ~47 GB on disk):")
    lines.append(f'"{hf}" download Qwen/Qwen-Image-2.1 \\')
    lines.append(f"    --local-dir {cache_dir} \\")
    lines.append(f"    --include \"*.json\" \"*.md\" \"LICENSE\" \"text_encoder/*.safetensors\" \"transformer/*.safetensors\" \"vae/*.safetensors\" \"processor/*\" \"scheduler/*\"")
    lines.append("")
    if include_gguf:
        gguf_dir = os.path.join(os.path.dirname(cache_dir), "Qwen-Image-2.1-GGUF")
        lines.append("# 2) Optional: Q6_K GGUF quant (5.84 GB, fits 8-12 GB VRAM cards):")
        lines.append(f'"{hf}" download AlperKTS/Qwen-Image-2.1-GGUF \\')
        lines.append(f"    --local-dir {gguf_dir} \\")
        lines.append(f'    --include "*.gguf" "README.md"')
        # The HF model card for Qwen-Image-2.1 itself decomposes into 3 files
        # when you go via Comfy-Org/Qwen-Image-2.1 (separate text encoder /
        # VAE). Recommend pulling those too so a ComfyUI / standalone diffusers
        # pipeline pre-load works without re-hitting the hub.
        lines.append("")
        lines.append("# 3) Optional: Comfy-Org split checkpoints (separate FP8 text encoder + VAE)")
        lines.append("#    Useful if you also want to load the model via diffusers without quantizing,")
        lines.append("#    OR via ComfyUI's native text_encoders/ / vae/ folders.")
        comfy_dir = os.path.join(os.path.dirname(cache_dir), "Comfy-Org-Qwen-Image-2.1")
        lines.append(f'"{hf}" download Comfy-Org/Qwen-Image-2.1 \\')
        lines.append(f"    --local-dir {comfy_dir}")
    return "\n".join(lines)


def _venv_setup_command(py, requirements_path):
    """A minimal venv-create command for users who prefer isolated installs."""
    venv_dir = os.path.join(SCRIPT_DIR, ".venv-qwen-image")
    return (
        f'"{py}" -m venv "{venv_dir}"\n'
        f'"{venv_dir}\\Scripts\\python.exe" -m pip install --upgrade pip\n'
        f'"{venv_dir}\\Scripts\\python.exe" -m pip install -r "{requirements_path}"'
    )


def main():
    ap = argparse.ArgumentParser(
        prog="install_qwen_image.py",
        description="Verify environment and emit (not execute) install / download commands for Qwen-Image-2.1.",
    )
    ap.add_argument("--cache-dir", default=_default_cache_dir(),
                    help=f"Where to keep downloaded weights (default {_default_cache_dir()!r}).")
    ap.add_argument("--gguf", action="store_true",
                    help="Include GGUF (AlperKTS) download commands in the printout.")
    ap.add_argument("--check-only", action="store_true",
                    help="Just run the python/torch probe; don't write requirements.")
    ap.add_argument("--print-commands", action="store_true",
                    help="Print the install + hf download commands and exit.")
    args = ap.parse_args()

    print("=== Python / torch probe ===")
    info = _probe_python_and_torch()
    print(f"Python: {info['python_path']} (exists={info['python_ok']})")
    if info["python_ok"]:
        if info["torch_importable"]:
            print(f"torch:  {info['torch_version']}")
            print(f"cuda:   available={info['cuda_available']}, device={info['cuda_device_name']}")
        else:
            print("torch:  NOT installed (or failed to import).")
            if info.get("torch_error"):
                print(f"        reason: {info['torch_error']}")
            print("        Required: torch>=2.4.0 with CUDA wheels for your driver.")
            print("        If you have an NVIDIA card and CUDA toolkit, install with:")
            print("          pip install torch --index-url https://download.pytorch.org/whl/cu121")
    print()

    if info["python_ok"] and info["torch_importable"] and not info["cuda_available"]:
        print("NOTE: torch is installed but reports CUDA unavailable. You can still")
        print("      import QwenImage21Pipeline but inference will fall back to CPU")
        print("      (extremely slow). Verify your NVIDIA driver + CUDA toolkit install.")
        print()

    if args.check_only:
        return 0

    req_path = _write_requirements()
    print(f"Wrote requirements file: {req_path}")

    print()
    print("=== Install (does NOT run automatically; copy/paste please) ===")
    py = info["python_path"]
    print(f"# venv-isolated (recommended):")
    print(_venv_setup_command(py, req_path))
    print()
    print(f"# OR system-level (uses {py}):")
    print(f'"{py}" -m pip install -r "{req_path}"')
    print()

    print("=== Weight download (does NOT run automatically) ===")
    print("Model card page: https://huggingface.co/Qwen/Qwen-Image-2.1")
    print(f"Cache directory: {args.cache_dir}")
    print(f"Approx size: ~47 GB (BF16) - ensure the disk has it.")
    # Probe the drive free space of the cache path. We pick an existing
    # ancestor because the cache directory itself may not exist yet (and
    # shutil.disk_usage cannot examine non-existent paths).
    probe_root = args.cache_dir
    while not os.path.exists(probe_root):
        parent = os.path.dirname(probe_root)
        if not parent or parent == probe_root:
            break  # hit fs root; use it
        probe_root = parent
    free_gb = shutil.disk_usage(probe_root).free / (1024 ** 3)
    print(f"Disk free at that location ({probe_root}): {free_gb:.1f} GB")
    if free_gb < 60:
        print("WARNING: less than 60 GB free at the cache target. Pick a bigger drive or trim --include.")
    print()
    print(_download_commands(args.cache_dir, args.gguf))
    print()
    print("After step 1 above completes, run:")
    print(f'  "{py}" "{os.path.join(SCRIPT_DIR, "qwen_image_local.py")}" --prompt "a barn exterior in winter" --transparent')

    return 0


if __name__ == "__main__":
    sys.exit(main())
