#!/usr/bin/env python3
"""
cpu3d_client.py
Client for the cpu3d MCP server: one image of a creature in, a low-poly rigged,
animated model out (.glb/.fbx/.blend). FREE - it runs on a CPU-only LAN PC, no
credits and no approval needed. Pure standard library (speaks MCP streamable HTTP
JSON-RPC directly, so it works whichever `mcp` package version is installed).

Connection: tools/cpu3d_connection.json (gitignored, holds the bearer token):
  {"base_url": "http://192.168.1.35:8765", "fallback_base_url": "http://HOST:8765", "token": "..."}
or the env vars CPU3D_URL / CPU3D_TOKEN.

CLI:  python tools/cpu3d_client.py info
      python tools/cpu3d_client.py generate pic.png --name animal_horse --kind quadruped --out result_dir
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CONN_FILE = os.path.join(HERE, "cpu3d_connection.json")
KINDS = ("auto", "human", "quadruped", "bird", "fish", "vehicle")


class Cpu3dError(RuntimeError):
    pass


def load_connection():
    conn = {}
    if os.path.isfile(CONN_FILE):
        with open(CONN_FILE, "r", encoding="utf-8-sig") as f:
            conn = json.load(f)
    url = os.environ.get("CPU3D_URL") or conn.get("base_url")
    token = os.environ.get("CPU3D_TOKEN") or conn.get("token")
    if not url or not token:
        raise Cpu3dError("cpu3d is not configured: put base_url and token in tools/cpu3d_connection.json")
    bases = [url.rstrip("/")]
    fb = conn.get("fallback_base_url")
    if fb and fb.rstrip("/") not in bases:
        bases.append(fb.rstrip("/"))
    return bases, token


def is_configured():
    try:
        load_connection()
        return True
    except Exception:
        return False


def _parse_rpc(body, content_type):
    """The server answers with JSON or an SSE stream; return the last JSON-RPC message with an id."""
    if "text/event-stream" in (content_type or ""):
        msg = None
        for line in body.decode("utf-8", "replace").splitlines():
            if line.startswith("data:"):
                try:
                    msg = json.loads(line[5:].strip())
                except ValueError:
                    pass
        return msg
    return json.loads(body.decode("utf-8")) if body.strip() else None


class Session:
    def __init__(self, timeout=90):
        self.bases, self.token = load_connection()
        self.timeout = timeout
        self.base = None
        self.sid = None
        self._id = 0
        self._connect()

    def _post(self, base, payload, timeout=None):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.sid:
            headers["Mcp-Session-Id"] = self.sid
        req = urllib.request.Request(base + "/mcp", data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout or self.timeout) as r:
                sid = r.headers.get("Mcp-Session-Id")
                return _parse_rpc(r.read(), r.headers.get("Content-Type")), sid
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise Cpu3dError("cpu3d rejected the token (HTTP 401)")
            raise Cpu3dError(f"cpu3d HTTP {e.code}: {e.read()[:300]!r}")

    def _connect(self):
        last = None
        for base in self.bases:
            try:
                self._id += 1
                msg, sid = self._post(base, {
                    "jsonrpc": "2.0", "id": self._id, "method": "initialize",
                    "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                               "clientInfo": {"name": "homesteader-asset-kit", "version": "1"}}}, timeout=10)
                self.base, self.sid = base, sid
                self._post(base, {"jsonrpc": "2.0", "method": "notifications/initialized"}, timeout=10)
                return
            except (urllib.error.URLError, OSError, Cpu3dError) as e:
                last = e
        raise Cpu3dError(f"cannot reach the cpu3d server ({last}). Is the PC on and awake?")

    def call(self, tool, args=None, timeout=None):
        self._id += 1
        msg, _ = self._post(self.base, {"jsonrpc": "2.0", "id": self._id, "method": "tools/call",
                                        "params": {"name": tool, "arguments": args or {}}}, timeout=timeout)
        if not msg:
            raise Cpu3dError(f"empty reply from {tool}")
        if "error" in msg:
            raise Cpu3dError(f"{tool}: {msg['error'].get('message')}")
        res = msg.get("result", {})
        if res.get("isError"):
            raise Cpu3dError(f"{tool}: " + " ".join(c.get("text", "") for c in res.get("content", [])))
        sc = res.get("structuredContent")
        if sc is not None:
            return sc.get("result", sc) if isinstance(sc, dict) else sc
        return json.loads(res["content"][0]["text"])

    def download(self, url, dest):
        """url comes from get_job (built from the server's own host); re-root it on the base that worked."""
        path = "/jobs/" + url.split("/jobs/", 1)[1]
        req = urllib.request.Request(self.base + path, headers={"Authorization": f"Bearer {self.token}"})
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
            f.write(r.read())


def server_info():
    return Session(timeout=15).call("server_info")


def submit(sess, image_path, name, kind="auto", faces=1500, flat=False, flip=False, mc_resolution=192, previews=False, size_m=0, width_m=0, height_m=0):
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return sess.call("submit_creature", {
        "image_base64": b64, "kind": kind, "faces": int(faces), "name": name, "flat": bool(flat),
        "flip": bool(flip), "mc_resolution": int(mc_resolution), "previews": bool(previews),
        "size_m": float(size_m), "width_m": float(width_m), "height_m": float(height_m)}, timeout=120)["job_id"]


def wait(sess, job_id, on_stage=None, max_seconds=1800):
    t0, last = time.time(), None
    while time.time() - t0 < max_seconds:
        job = sess.call("get_job", {"job_id": job_id, "wait_seconds": 50}, timeout=120)
        if on_stage and job.get("stage") != last:
            last = job.get("stage")
            on_stage(job)
        if job["status"] in ("done", "failed", "cancelled"):
            return job
    raise Cpu3dError("cpu3d job timed out")


def generate(image_path, name, out_dir, kind="auto", faces=1500, flat=False, flip=False,
             mc_resolution=192, previews=False, on_stage=None, size_m=0, width_m=0, height_m=0):
    """Whole workflow. Downloads every result file into out_dir; returns the finished job dict."""
    sess = Session()
    jid = submit(sess, image_path, name, kind, faces, flat, flip, mc_resolution, previews, size_m, width_m, height_m)
    if on_stage:
        on_stage({"status": "queued", "stage": "queued", "job_id": jid})
    job = wait(sess, jid, on_stage)
    if job["status"] != "done":
        raise Cpu3dError(f"cpu3d job {job['status']}: {job.get('error')} " + " | ".join(job.get("log_tail", [])[-3:]))
    for f in job["files"]:
        sess.download(f["url"], os.path.join(out_dir, f["path"]))
    return job


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("info")
    g = sub.add_parser("generate")
    g.add_argument("image")
    g.add_argument("--name", default="creature")
    g.add_argument("--kind", default="auto", choices=KINDS)
    g.add_argument("--faces", type=int, default=1500)
    g.add_argument("--flat", action="store_true")
    g.add_argument("--flip", action="store_true")
    g.add_argument("--mc-resolution", type=int, default=192)
    g.add_argument("--previews", action="store_true")
    g.add_argument("--size-m", type=float, default=0, help="real length in m (height for a human)")
    g.add_argument("--width-m", type=float, default=0)
    g.add_argument("--height-m", type=float, default=0)
    g.add_argument("--out", default="cpu3d_result")
    a = p.parse_args()
    if a.cmd == "info":
        print(json.dumps(server_info(), indent=2))
        return
    job = generate(a.image, a.name, a.out, a.kind, a.faces, a.flat, a.flip, a.mc_resolution, a.previews,
                   on_stage=lambda j: print(f"  {j['status']}: {j.get('stage')}"),
                   size_m=a.size_m, width_m=a.width_m, height_m=a.height_m)
    print("done:", json.dumps({k: job["report"].get(k) for k in ("triangles", "bones", "clips")}), "->", os.path.abspath(a.out))


if __name__ == "__main__":
    try:
        main()
    except Cpu3dError as e:
        sys.exit(str(e))
