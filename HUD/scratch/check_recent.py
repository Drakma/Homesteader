import os
import time

now = time.time()
hud_root = r"c:\Users\casey\Desktop\Homesteader\HUD"
ue5_root = r"c:\Users\casey\Desktop\Homesteader\Homesteader"

for base in [hud_root, ue5_root]:
    recent = []
    for root, dirs, files in os.walk(base):
        for f in files:
            p = os.path.join(root, f)
            try:
                mtime = os.path.getmtime(p)
                if (now - mtime) < 14400:  # 4 hours
                    recent.append((mtime, p))
            except Exception:
                pass
    recent.sort(reverse=True)
    print(f"{base}: {len(recent)} files modified in last 4 hours.")
    for m, p in recent[:30]:
        t_str = time.strftime("%H:%M:%S", time.localtime(m))
        print(f"  [{t_str}] {os.path.relpath(p, base)}")

