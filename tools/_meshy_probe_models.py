#!/usr/bin/env python3
"""Probe Meshy's text-to-3D endpoint to find a model_type/ai_model combo that is accepted."""
import os
import sys
import json
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import meshy_client as mc

BASE = "https://api.meshy.ai"


def post(payload):
    req = urllib.request.Request(
        f"{BASE}/openapi/v2/text-to-3d",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {mc.MESHY_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:
            return 200, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


PROMPT = "a low-poly old male farmer standing in an A-pose"

candidates = [
    {"prompt": PROMPT, "mode": "preview", "ai_model": "meshy-5", "model_type": "lowpoly", "alpha_thumbnail": True, "target_formats": ["glb", "fbx", "obj"]},
    {"prompt": PROMPT, "mode": "preview", "ai_model": "meshy-6", "model_type": "lowpoly"},
    {"prompt": PROMPT, "mode": "preview", "ai_model": "meshy-6-lite", "model_type": "standard"},
    {"prompt": PROMPT, "mode": "preview", "model_type": "lowpoly"},
    {"prompt": PROMPT, "mode": "preview"},
]

for i, payload in enumerate(candidates):
    code, body = post(payload)
    label = f"ai_model={payload.get('ai_model')} model_type={payload.get('model_type')}"
    if code in (200, 201, 202):
        task = body.get("result") if isinstance(body, dict) else body
        print(f"[probe {i}] ACCEPTED  {label}  -> task {task}")
        print(f"[probe {i}] NOTE: this created a real task; cancel it if unused.")
    else:
        print(f"[probe {i}] {code}  {label}")
        print(f"[probe {i}]   {str(body)[:300]}")

print("[probe] balance:", mc.get_balance())
