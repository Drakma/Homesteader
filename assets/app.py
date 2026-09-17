#!/usr/bin/env python3
"""
Homesteader Master Asset Kit - Standalone Desktop Application
Wraps server.py and index.html in a native Edge WebView2 desktop window.
"""

import os
import sys

# Ensure assets directory is in sys.path even when launched from shortcut or outside CWD
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import time
import socket
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import webview
from server import AssetKitHandler, BASE_DIR

DEFAULT_PORT = 8088
ICON_PATH = os.path.join(BASE_DIR, "app_icon.ico")


class ReusableThreadingServer(ThreadingHTTPServer):
    allow_reuse_address = True


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def check_existing_server(port):
    try:
        url = f"http://127.0.0.1:{port}/api/ping"
        req = urllib.request.Request(url, headers={"User-Agent": "AssetKitApp"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            return resp.status == 200
    except Exception:
        return False


def start_server_thread(port):
    httpd = ReusableThreadingServer(("", port), AssetKitHandler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    return httpd


def main():
    target_port = DEFAULT_PORT
    server_instance = None

    # Check if a compatible server is already running on 8088
    if is_port_in_use(target_port):
        if check_existing_server(target_port):
            print(f"[AssetKit] Reusing active Asset Kit server on port {target_port}")
        else:
            # Port 8088 occupied by something else, allocate a free ephemeral port
            target_port = find_free_port()
            print(f"[AssetKit] Starting embedded server on dynamic port {target_port}...")
            server_instance = start_server_thread(target_port)
    else:
        print(f"[AssetKit] Starting embedded server on port {target_port}...")
        server_instance = start_server_thread(target_port)

    # Wait briefly for server readiness
    for _ in range(20):
        if check_existing_server(target_port):
            break
        time.sleep(0.1)

    app_url = f"http://127.0.0.1:{target_port}/index.html"
    print(f"[AssetKit] Launching desktop UI -> {app_url}")

    # Create native WebView2 desktop window
    window = webview.create_window(
        title="Homesteader // Master Asset Kit",
        url=app_url,
        width=1540,
        height=900,
        min_size=(1024, 700),
        background_color="#090d13",
        text_select=True,
        zoomable=True
    )

    def on_closed():
        print("[AssetKit] Desktop window closed.")
        if server_instance:
            try:
                server_instance.shutdown()
                server_instance.server_close()
                print("[AssetKit] Embedded server stopped.")
            except Exception:
                pass

    window.events.closed += on_closed

    # Start native window loop
    start_kwargs = {
        "debug": False,
        "private_mode": False,
        "storage_path": os.path.join(os.path.expanduser("~"), ".homesteader", "asset_kit_app_data")
    }
    if os.path.exists(ICON_PATH):
        start_kwargs["icon"] = ICON_PATH

    webview.start(**start_kwargs)


if __name__ == "__main__":
    main()

