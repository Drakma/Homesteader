import os, sys, time, json, urllib.request

def load_env(path):
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env

ENV = load_env(os.path.join(os.path.dirname(__file__), "..", ".env"))
API_KEY = ENV["TRIPO_API_KEY"]
BASE = "https://openapi.tripo3d.ai/v3"

def call(method, path, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {API_KEY}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"HTTP {e.code} error body: {body}")
        raise

def submit(prompt, face_limit=4000):
    body = {
        "prompt": prompt,
        "model": "v3.1-20260211",
        "face_limit": face_limit,
        "texture": True,
        "pbr": True,
        "texture_quality": "standard",
    }
    r = call("POST", "/generation/text-to-model", body)
    print("submit response:", json.dumps(r)[:500])
    return r["data"]["task_id"]

def poll(task_id, timeout=180):
    start = time.time()
    while time.time() - start < timeout:
        r = call("GET", f"/tasks/{task_id}")
        status = r["data"]["status"]
        print(f"  [{task_id}] status={status} progress={r['data'].get('progress')}")
        if status == "success":
            return r["data"]
        if status in ("failed", "cancelled", "banned"):
            raise RuntimeError(f"task {task_id} ended with status {status}: {r}")
        time.sleep(3)
    raise TimeoutError(f"task {task_id} timed out")

def download(url, out_path):
    urllib.request.urlretrieve(url, out_path)
    print(f"  downloaded -> {out_path} ({os.path.getsize(out_path)} bytes)")

if __name__ == "__main__":
    prompt = sys.argv[1]
    out_path = sys.argv[2]
    face_limit = int(sys.argv[3]) if len(sys.argv) > 3 else 4000
    task_id = submit(prompt, face_limit)
    data = poll(task_id)
    model_url = data["output"]["model"] if "model" in data.get("output", {}) else data["output"].get("pbr_model") or data["output"].get("model_url")
    print("model_url:", model_url)
    download(model_url, out_path)
