"""_smoke_tripo_text.py - one-shot text-to-3D smoke test (1 mesh).

Confirms the API key works and the .glb file is decodable.

Usage:
    python _smoke_tripo_text.py <percentage> <subject>
    python _smoke_tripo_text.py <percentage> "Wooden Log Cabin"

But the script will also accept a single subject without a percentage
of budget. Without arg, it uses 'small wooden log cabin'.
"""

import os
import sys
import time
import requests
import base64

PROJ = r"C:\Users\casey\Desktop\Homesteader"
TIPO_BASE = "https://openapi.tripo3d.ai/v3"

api_key = os.environ.get("TRIPO_API_KEY", "")
if not api_key:
    print("[smoke] TRIPO_API_KEY env var not set; aborting.")
    print("[smoke] Sign up at https://www.tripo3d.ai/ and export "
          "TRIPO_API_KEY=<key> before running.")
    sys.exit(1)

subject = (sys.argv[1] if len(sys.argv) > 1
           else "small wooden log cabin, low-poly faceted, single object, "
                "no surroundings")

prompt = f"a 3D model of {subject}"

print(f"[smoke] subject: {subject!r}")
print(f"[smoke] prompt: {prompt!r}")
print(f"[smoke] posting to {TIPO_BASE}/generation/text-to-model...")

t0 = time.time()
r = requests.post(
    f"{TIPO_BASE}/generation/text-to-model",
    headers={"Authorization": f"Bearer {api_key}",
             "Content-Type": "application/json"},
    json={"prompt": prompt, "model_version": "v3.0-20250101"},
    timeout=60,
)
r.raise_for_status()
task = r.json()
task_id = task["task_id"]
print(f"[smoke] task_id: {task_id}")

print(f"[smoke] polling for completion...")
deadline = time.time() + 240
while time.time() < deadline:
    time.sleep(4)
    rr = requests.get(
        f"{TIPO_BASE}/generation/task/{task_id}",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    rr.raise_for_status()
    j = rr.json()
    status = j.get("data", {}).get("status",
             j.get("status", "unknown"))
    print(f"  status={status}")
    if status == "success":
        data = j.get("data", j)
        url = data.get("model_url") or data.get("output_url") or j.get("model_url")
        if not url:
            print("[smoke] success but no model_url in response")
            print(j)
            sys.exit(2)
        out = os.path.join(PROJ, "_procgen_test", "_tripo_smoke", f"{task_id}.glb")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with requests.get(url, stream=True, timeout=120) as dl:
            dl.raise_for_status()
            with open(out, "wb") as f:
                f.write(dl.content)
        sz = os.path.getsize(out)
        print(f"[smoke] -> {out} ({sz / 1024:.1f} KB) "
              f"({time.time() - t0:.1f}s)")
        print(f"[smoke] mesh provider URL (if you want to inspect): {url}")
        sys.exit(0)
    if status in ("failed", "error", "cancelled"):
        print("[smoke] task failed:")
        print(j)
        sys.exit(2)
print("[smoke] poll timeout")
sys.exit(2)
