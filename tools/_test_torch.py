import sys
import torch
print("Python version:", sys.version)
print("Torch version:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("Device:", torch.cuda.get_device_name(0))
    print("Capability:", torch.cuda.get_device_capability(0))
    print("CUDA version:", torch.version.cuda)
    print("cuDNN version:", torch.backends.cudnn.version())
    print("bf16 supported:", torch.cuda.is_bf16_supported())

    # Let's test a simple bfloat16 tensor operation on CUDA
    try:
        a = torch.randn(10, 10, dtype=torch.bfloat16, device="cuda")
        b = a @ a
        print("bf16 matmul success:", b.shape)
    except Exception as e:
        print("bf16 matmul failed:", e)

    # Let's test fp16
    try:
        a = torch.randn(10, 10, dtype=torch.float16, device="cuda")
        b = a @ a
        print("fp16 matmul success:", b.shape)
    except Exception as e:
        print("fp16 matmul failed:", e)
