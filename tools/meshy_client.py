#!/usr/bin/env python3
"""
meshy_client.py
Direct client interface for Meshy AI (meshy.ai) 3D Generation Platform.
Supports:
- Checking balance / credits
- Text-to-3D generation (preview & refine)
- Image-to-3D generation
- Polling task status
- Downloading 3D models (GLB, FBX, OBJ, USDZ)
"""

import os
import time
import json
import urllib.request
import urllib.error

MESHY_API_KEY = os.environ.get("MESHY_API_KEY", "msy_mUvsQRtfvX2levWkmugKy3nFHSp3Yyf0Y4Cx")
BASE_URL = "https://api.meshy.ai"

def _request(endpoint, method="GET", data=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {MESHY_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    req_data = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        raise RuntimeError(f"Meshy API Error {e.code}: {err_body}")

def get_balance():
    """Returns current credit balance."""
    res = _request("/openapi/v1/balance")
    return res.get("balance", 0)

def create_text_to_3d(prompt, ai_model="meshy-5", model_type="lowpoly", target_formats=None, alpha_thumbnail=True):
    """
    Initiates a Text-to-3D preview task using Meshy v2 API.
    Returns: task_id (string)
    """
    payload = {
        "mode": "preview",
        "prompt": prompt,
        "ai_model": ai_model,
        "model_type": model_type,
        "alpha_thumbnail": alpha_thumbnail,
        "target_formats": target_formats or ["glb", "obj", "fbx"]
    }
    res = _request("/openapi/v2/text-to-3d", method="POST", data=payload)
    return res.get("result")

def create_text_to_3d_refine(preview_task_id):
    """
    Refines a completed preview task into a textured mesh.
    Returns: task_id (string)
    """
    payload = {
        "mode": "refine",
        "preview_task_id": preview_task_id
    }
    res = _request("/openapi/v2/text-to-3d", method="POST", data=payload)
    return res.get("result")

def create_image_to_3d(image_url, ai_model="meshy-t2", model_type="smart-topology", should_texture=True, enable_pbr=False, topology="triangle"):
    """
    Initiates an Image-to-3D task. This is now the default generation route
    (reference image -> image-to-3D), superseding create_text_to_3d(). Always
    ai_model='meshy-t2' / model_type='smart-topology' per project policy -
    never 'lowpoly' or 'standard'.
    Returns: task_id (string)
    """
    payload = {
        "image_url": image_url,
        "ai_model": ai_model,
        "model_type": model_type,
        "should_texture": should_texture,
        "enable_pbr": enable_pbr,
        "topology": topology
    }
    res = _request("/openapi/v1/image-to-3d", method="POST", data=payload)
    return res.get("result")

def get_task(task_type, task_id):
    """
    Gets task status.
    task_type: 'text-to-3d' or 'image-to-3d'
    """
    if task_type == "text-to-3d":
        endpoint = f"/openapi/v2/text-to-3d/{task_id}"
    else:
        endpoint = f"/openapi/v1/{task_type}/{task_id}"
    return _request(endpoint)

def wait_for_task(task_type, task_id, timeout_sec=300, poll_interval=5):
    """
    Polls task until SUCCEEDED or FAILED.
    """
    start = time.time()
    print(f"Waiting for {task_type} task {task_id}...")
    while time.time() - start < timeout_sec:
        task = get_task(task_type, task_id)
        status = task.get("status")
        progress = task.get("progress", 0)
        print(f"  Status: {status} ({progress}%)")
        if status == "SUCCEEDED":
            return task
        elif status in ["FAILED", "CANCELED"]:
            raise RuntimeError(f"Task {task_id} {status}: {task.get('task_error', {}).get('message', 'Unknown error')}")
        time.sleep(poll_interval)
    raise TimeoutError(f"Task {task_id} timed out after {timeout_sec}s")

def download_model_files(task_result, output_dir, file_prefix="model"):
    """
    Downloads model outputs (GLB, FBX, OBJ, textures) into output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    model_urls = task_result.get("model_urls", {})
    downloaded = []
    
    for fmt, url in model_urls.items():
        if not url:
            continue
        ext = f".{fmt}" if not fmt.startswith(".") else fmt
        out_filename = f"{file_prefix}{ext}"
        out_path = os.path.join(output_dir, out_filename)
        print(f"  Downloading {fmt} to {out_path}...")
        urllib.request.urlretrieve(url, out_path)
        downloaded.append(out_path)
        
    return downloaded

if __name__ == "__main__":
    b = get_balance()
    print(f"Meshy AI connected successfully. Available balance: {b} credits.")

