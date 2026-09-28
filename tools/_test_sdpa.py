import torch
import torch.nn.functional as F

print("Testing SDPA on GTX 1080 Ti...")
device = "cuda"

for dt_name, dt in [("float16", torch.float16), ("bfloat16", torch.bfloat16)]:
    print(f"\n--- Testing dtype: {dt_name} ---")
    q = torch.randn(1, 16, 1024, 64, device=device, dtype=dt)
    k = torch.randn(1, 16, 1024, 64, device=device, dtype=dt)
    v = torch.randn(1, 16, 1024, 64, device=device, dtype=dt)

    # Test default SDPA
    try:
        out = F.scaled_dot_product_attention(q, k, v)
        print("Default SDPA success:", out.shape)
    except Exception as e:
        print("Default SDPA failed:", e)

    # Test backends explicitly
    from torch.nn.attention import SDPBackend, sdpa_kernel

    for b in [SDPBackend.FLASH_ATTENTION, SDPBackend.EFFICIENT_ATTENTION, SDPBackend.MATH, SDPBackend.CUDNN_ATTENTION]:
        try:
            with sdpa_kernel(b):
                out = F.scaled_dot_product_attention(q, k, v)
                print(f"Backend {b.name} success")
        except Exception as e:
            print(f"Backend {b.name} error/unsupported: {e}")

print("\nDone SDPA test.")
