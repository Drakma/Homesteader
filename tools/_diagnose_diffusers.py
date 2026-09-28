"""
Diagnose the current importable diffusers + whether QwenImage21Pipeline is in
it. Used right after a pip install attempt to confirm what's actually
reachable from C:\Python313\python.exe.
"""
import sys

print("interpreter    :", sys.executable)
print("python         :", sys.version.split()[0])
try:
    import torch
    print("torch          :", torch.__version__, "cuda_available=", torch.cuda.is_available())
except Exception as e:
    print("torch          : NOT IMPORTABLE", repr(e))
try:
    import transformers
    print("transformers   :", transformers.__version__)
except Exception as e:
    print("transformers   : NOT IMPORTABLE", repr(e))
try:
    import accelerate
    print("accelerate     :", accelerate.__version__)
except Exception as e:
    print("accelerate     : NOT IMPORTABLE", repr(e))
try:
    import diffusers
    print("diffusers      :", diffusers.__version__)
    print("  path         :", diffusers.__file__)
except Exception as e:
    print("diffusers      : NOT IMPORTABLE", repr(e))
try:
    from diffusers import QwenImage21Pipeline
    print("QwenImage21Pipeline: IMPORTABLE")
except ImportError as e:
    print("QwenImage21Pipeline: NOT IMPORTABLE", repr(e))
try:
    import huggingface_hub
    print("huggingface_hub:", huggingface_hub.__version__)
except Exception as e:
    print("huggingface_hub: NOT IMPORTABLE", repr(e))
try:
    import PIL
    print("pillow         :", PIL.__version__)
except Exception as e:
    print("pillow         : NOT IMPORTABLE", repr(e))
