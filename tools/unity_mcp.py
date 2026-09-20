"""tools/unity_mcp.py -- thin MCP client wrapper around unity-ai-relay.

Talks to a running Unity Editor through the official
com.unity.ai.assistant package's relay binary. We spawn our own
relay_win.exe in --mcp mode (each process serves one MCP client on
stdio) and pipe JSON-RPC frames through it on demand.

The helper intentionally exposes a small surface:

    list_tools()                            -> list of tool descriptors
    call(tool_name, arguments=None, ...)    -> parsed MCP result
    list_tools_table()                      -> {name: brief} for prompt use
    health()                                -> {running, pid, project}

Persistence: a long-lived relay subprocess sticks to PROJECT_DIR and the
current Unity Editor PID. When the editor changes (PID moves), restart it.

Stylistic constraints (mirror tools/asset_kit_mcp.py):
- Absolute paths anchored to this file's location, no CWD assumptions.
- No triple-quoted string literals (the editing rules and the docstring
  collapse problem).
- Always run `python tools/check_syntax.py tools/unity_mcp.py` after editing.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from typing import Any, Dict, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
HOMESTEADER_PROJECT = os.path.join(PROJECT_DIR, "Homesteader")

DEFAULT_RELAY = os.path.join(
    HOMESTEADER_PROJECT,
    "Library",
    "PackageCache",
    "com.unity.ai.assistant@8d1e3e89e3a7",
    "RelayApp~",
    "relay_win.exe",
)
# Fallback absolute path if the package cache is at a different hash.
FALLBACK_RELAY = r"C:\Users\casey\.unity\relay\relay_win.exe"

PROTOCOL_VERSION = "2024-11-05"
RELAY_NAME = "unity-mcp"

# JSON-RPC plumbing. We read one newline-delimited frame per response.
_EOL = b"\n"
_lock = threading.Lock()


def find_unity_pid(unity_exe_hint: str = "Unity.exe") -> Optional[int]:
    # Resolve the editor PID via tasklist so the relay binds to the right
    # editor instance. Returns the PID of the windowed Unity process
    # (the one with a title), preferring the most recently started one
    # if multiple are running.
    try:
        out = subprocess.check_output(
            ["tasklist", "/FO", "CSV", "/NH", "/FI", f"IMAGENAME eq {unity_exe_hint}"],
            text=True,
            timeout=5,
        )
    except Exception:
        return None
    pids = []
    for line in out.splitlines():
        parts = [p.strip().strip('"') for p in line.split('","')]
        if len(parts) >= 2 and parts[1].isdigit():
            pids.append(int(parts[1]))
    return pids[0] if pids else None


def resolve_relay_path(explicit: Optional[str] = None) -> str:
    candidates = [explicit, os.environ.get("UNITY_RELAY"), DEFAULT_RELAY, FALLBACK_RELAY]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    raise FileNotFoundError(
        "Could not find relay_win.exe. Searched: " + ", ".join(c for c in candidates if c)
    )


class UnityMCPClient:
    # Manages one relay subprocess + its stdio. Strict sequential
    # request/response. The relay is line-buffered; one read per write.
    def __init__(
        self,
        project_path: Optional[str] = None,
        relay_path: Optional[str] = None,
        unity_pid: Optional[int] = None,
        client_name: str = "homesteader-tools",
    ) -> None:
        self.project_path = project_path or HOMESTEADER_PROJECT
        self.relay_path = resolve_relay_path(relay_path)
        self.unity_pid = unity_pid or find_unity_pid() or 0
        self.client_name = client_name
        self.proc: Optional[subprocess.Popen] = None
        self._next_id = 1
        self._stderr_thread: Optional[threading.Thread] = None
        self._stderr_buf: List[str] = []

    def __enter__(self) -> "UnityMCPClient":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    def start(self) -> None:
        if self.proc is not None and self.proc.poll() is None:
            return
        args = [
            self.relay_path,
            "--mcp",
            "--name", RELAY_NAME,
            "--project-path", self.project_path,
        ]
        if self.unity_pid:
            args += ["--instance-id", str(self.unity_pid)]

        # Hide the relay window on Windows; we own its stdio.
        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NO_WINDOW

        self.proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            creationflags=creationflags,
        )

        # Drain stderr in a background thread; relay writes its log there.
        self._stderr_buf = []
        self._stderr_thread = threading.Thread(
            target=self._drain_stderr, daemon=True
        )
        self._stderr_thread.start()

        # MCP initialize handshake.
        init_result = self._round_trip(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": self.client_name, "version": "1.0.0"},
            },
        )
        if not init_result.get("ok"):
            raise RuntimeError(
                "Unity MCP initialize failed: " + json.dumps(init_result)
            )

    def _drain_stderr(self) -> None:
        assert self.proc is not None and self.proc.stderr is not None
        try:
            while True:
                line = self.proc.stderr.readline()
                if not line:
                    return
                self._stderr_buf.append(line.decode("utf-8", errors="replace").rstrip())
        except Exception:
            return

    def recent_stderr(self, n: int = 50) -> List[str]:
        return self._stderr_buf[-n:]

    def stop(self) -> None:
        if self.proc is None:
            return
        try:
            self.proc.stdin.close() if self.proc.stdin else None
        except Exception:
            pass
        try:
            self.proc.terminate()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=3)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass
        self.proc = None

    def _round_trip(self, method: str, params: Optional[dict]) -> Dict[str, Any]:
        # Send one JSON-RPC request, read one JSON-RPC response. We tolerate
        # interspersed notifications (e.g. notifications/tools/list_changed)
        # by reading and discarding any non-id-matched frames until our id
        # comes back.
        if self.proc is None or self.proc.stdin is None or self.proc.stdout is None:
            return {"ok": False, "error": "relay not started"}

        with _lock:
            self._next_id += 1
            msg_id = self._next_id
            frame = {"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params or {}}
            self.proc.stdin.write((json.dumps(frame) + "\n").encode("utf-8"))
            self.proc.stdin.flush()

            deadline = time.time() + 30.0
            buf = bytearray()
            while time.time() < deadline:
                ch = self.proc.stdout.read(1)
                if not ch:
                    return {"ok": False, "error": "relay closed stdout"}
                if ch == _EOL:
                    text = buf.decode("utf-8", errors="replace")
                    buf = bytearray()
                    try:
                        payload = json.loads(text)
                    except json.JSONDecodeError as e:
                        continue
                    if payload.get("id") == msg_id:
                        if "error" in payload:
                            return {"ok": False, "error": payload["error"], "raw": payload}
                        return {"ok": True, "result": payload.get("result"), "raw": payload}
                    # else: notification; discard and wait for the matching id.
                else:
                    buf.extend(ch)
            return {"ok": False, "error": "timeout waiting for id=" + str(msg_id)}

    # Public helpers -------------------------------------------------------

    def initialize(self) -> Dict[str, Any]:
        # The handshake already ran in start(); this surfaces what we got.
        return {
            "relay": os.path.basename(self.relay_path),
            "project": self.project_path,
            "unity_pid": self.unity_pid,
            "pid": self.proc.pid if self.proc else None,
        }

    def health(self) -> Dict[str, Any]:
        running = self.proc is not None and self.proc.poll() is None
        return {
            "running": running,
            "pid": self.proc.pid if self.proc else None,
            "project": self.project_path,
            "unity_pid": self.unity_pid,
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        rr = self._round_trip("tools/list", {})
        if not rr.get("ok"):
            raise RuntimeError("tools/list failed: " + json.dumps(rr))
        result = rr.get("result") or {}
        return list(result.get("tools") or [])

    def list_tools_table(self) -> Dict[str, str]:
        # Compact shape: name -> one-line description.
        out: Dict[str, str] = {}
        for t in self.list_tools():
            name = t.get("name") or "?"
            desc = (t.get("description") or "").split("\n", 1)[0].strip()
            if len(desc) > 220:
                desc = desc[:217] + "..."
            out[name] = desc
        return out

    def call(self, name: str, arguments: Optional[dict] = None) -> Dict[str, Any]:
        # Returns {ok, content_blocks, structured, raw}.
        rr = self._round_trip("tools/call", {"name": name, "arguments": arguments or {}})
        if not rr.get("ok"):
            return {"ok": False, "error": rr.get("error")}
        result = rr.get("result") or {}
        content_blocks = result.get("content") or []
        return {
            "ok": not result.get("isError", False),
            "content_blocks": content_blocks,
            "structured": result.get("structuredContent"),
            "raw": result,
        }


# Module-level singleton: lazily created, reused across calls in one process.
_client_lock = threading.Lock()
_client: Optional[UnityMCPClient] = None


def get_client() -> UnityMCPClient:
    global _client
    with _client_lock:
        if _client is None:
            _client = UnityMCPClient()
            _client.start()
        elif _client.proc is None or _client.proc.poll() is not None:
            _client.start()
        return _client


# CLI helpers -------------------------------------------------------------


def _print_json(obj: Any) -> None:
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def _build_cli_parser():
    import argparse
    p = argparse.ArgumentParser(
        prog="unity_mcp",
        description="Talk to the running Unity Editor via the MCP relay.",
    )
    p.add_argument("--project", default=HOMESTEADER_PROJECT, help="Path to the Unity project root.")
    p.add_argument("--relay", default=None, help="Override relay_win.exe location.")
    p.add_argument("--pid", type=int, default=None, help="Override Unity editor PID.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("health", help="Print relay + editor health snapshot.")

    sub.add_parser("list-tools", help="Print the full tool descriptor list.")
    sub.add_parser("list-tools-table", help="Print a compact {name: one-liner} table.")

    p_call = sub.add_parser("call", help="Invoke a single tool by name.")
    p_call.add_argument("tool", help="Tool name, e.g. Unity_GetConsoleLogs.")
    p_call.add_argument(
        "--args-json",
        default=None,
        help="Arguments as a JSON object string. Defaults to {}.",
    )
    p_call.add_argument(
        "--args-file",
        default=None,
        help="Read the JSON arguments object from this file. Overrides --args-json.",
    )

    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_cli_parser().parse_args(argv)
    client = UnityMCPClient(
        project_path=args.project,
        relay_path=args.relay,
        unity_pid=args.pid,
    )
    client.start()
    try:
        if args.cmd == "health":
            _print_json({**client.health(), "initialize": client.initialize()})
            return 0
        if args.cmd == "list-tools":
            _print_json(client.list_tools())
            return 0
        if args.cmd == "list-tools-table":
            _print_json(client.list_tools_table())
            return 0
        if args.cmd == "call":
            if args.args_file:
                with open(args.args_file, "r", encoding="utf-8") as f:
                    raw = f.read()
            else:
                raw = args.args_json or "{}"
            call_args = json.loads(raw) if raw.strip() else {}
            res = client.call(args.tool, call_args)
            _print_json(res)
            return 0 if res.get("ok") else 2
        return 1
    finally:
        client.stop()


if __name__ == "__main__":
    sys.exit(main())
