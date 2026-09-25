#!/usr/bin/env python3
"""
Homesteader Mesh2Motion MCP Server
==================================

Bridges the locally-hosted Mesh2Motion web app into the Homesteader agent
workflow for FREE, LOCAL character rigging with animal support (biped,
quadruped, bird, dragon, spider, snake, kaiju).

HONEST SCOPE -- read this before using the tools
------------------------------------------------
Mesh2Motion (https://github.com/Mesh2Motion/mesh2motion-app) is a Three.js
browser application, NOT a headless rigging service. Its core value is the
interactive step where you drag skeleton handles onto the mesh. There is no
rigging API, no CLI, and no headless mode in the upstream project.

Therefore these tools do NOT rig a mesh automatically. They automate the
friction AROUND the manual step:

    mesh2motion_start        -> serve the app locally, report the URL
    mesh2motion_open_model   -> stage a model, pick a skeleton type, hand off
    mesh2motion_check_export -> verify the exported animated GLB landed
    mesh2motion_status       -> what is running, what is staged

The human does the ~30 second skeleton fit in the browser; the agent handles
staging, skeleton selection guidance, and export verification.

Stylistic constraints (mirror tools/asset_kit_mcp.py and tools/unity_mcp.py):
- Absolute paths anchored to this file's location, no CWD assumptions.
- No triple-quoted string literals (the editing rules and the docstring
  collapse problem). This module docstring is the single deliberate
  exception, kept at file scope where it cannot be nested inside a literal.
- Always run `python tools/check_syntax.py tools/mesh2motion_mcp.py` after
  editing.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from typing import Any, Dict, List, Optional

from mcp.server.mcpserver import MCPServer

# -----------------------------------------------------------------------------
# Paths and constants
# -----------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

M2M_APP_DIR = os.path.join(SCRIPT_DIR, "mesh2motion")
M2M_ENTRY = os.path.join(M2M_APP_DIR, "package.json")

# Staged models live where the Vite dev server can serve them as static files,
# so a model dropped here is reachable from the browser at /staged/<name>.
STAGE_DIR = os.path.join(M2M_APP_DIR, "static", "staged")

# Exports downloaded from the browser land in the user's Downloads folder.
# We watch for the newest .glb/.gltf there.
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# Project-side landing zone for verified rigged output.
RIGGED_DIR = os.path.join(PROJECT_DIR, "mesh_output", "rigged")

SERVER_PORT = 3000
SERVER_URL = "http://localhost:3000"

LOG_DIR = os.path.join(PROJECT_DIR, "logs")
SERVER_LOG = os.path.join(LOG_DIR, "mesh2motion_server.log")

# Skeleton presets Mesh2Motion ships. The label is what the user picks in the
# browser UI; the hint is Homesteader-specific guidance for that choice.
SKELETON_PRESETS: Dict[str, Dict[str, str]] = {
    "human": {
        "label": "Human",
        "hint": (
            "Biped. Maps to a Unity Mecanim HUMANOID rig after retarget. "
            "Use for farmers, NPCs, and humanoid enemies."
        ),
    },
    "fox": {
        "label": "Fox",
        "hint": (
            "Quadruped. Maps to Unity Mecanim GENERIC. Use for foxes, dogs, "
            "cats, and wolves - also a usable base for cows, pigs and sheep "
            "with leg-length adjustments."
        ),
    },
    "horse": {
        "label": "Horse",
        "hint": (
            "Quadruped. Maps to Unity Mecanim GENERIC. Use for horses, "
            "donkeys, and mules."
        ),
    },
    "bird": {
        "label": "Bird",
        "hint": (
            "Biped avian. Maps to Unity Mecanim GENERIC. Use for chickens, "
            "ducks, and geese."
        ),
    },
    "dragon": {
        "label": "Dragon",
        "hint": "Winged quadruped. Maps to Unity Mecanim GENERIC.",
    },
    "spider": {
        "label": "Spider",
        "hint": "Multi-leg arthropod. Maps to Unity Mecanim GENERIC.",
    },
    "snake": {
        "label": "Snake",
        "hint": "Serpentine. Maps to Unity Mecanim GENERIC.",
    },
    "kaiju": {
        "label": "Kaiju",
        "hint": "Large biped/quadruped hybrid. Maps to Unity Mecanim GENERIC.",
    },
}

VIEWABLE_SUFFIXES = (".glb", ".gltf", ".fbx", ".dae")


mcp = MCPServer(
    "mesh2motion",
    instructions=(
        "Mesh2Motion provides FREE, LOCAL rigging with animal support. It is "
        "a browser app, not a headless service: mesh2motion_open_model stages "
        "a model and the HUMAN fits the skeleton in the browser (the "
        "interactive skeleton positioning is the whole point of the tool). "
        "Do NOT claim a model was rigged automatically - only report rigging "
        "as done once mesh2motion_check_export confirms an exported GLB with "
        "animation clips exists. After export, the result still needs a "
        "Blender retarget pass to become a Unity Mecanim Humanoid or Generic "
        "rig; see docs/MESH2MOTION_SETUP.md."
    ),
)


# -----------------------------------------------------------------------------
# Internal helpers
# -----------------------------------------------------------------------------

def _is_server_up(timeout: float = 1.5) -> bool:
    # Probe the dev server root. Any HTTP response (even an error status)
    # proves something is listening on the port.
    try:
        with urllib.request.urlopen(SERVER_URL, timeout=timeout):
            return True
    except urllib.error.HTTPError:
        return True
    except Exception:
        return False


def _find_node() -> Optional[str]:
    # Node is not on PATH on this machine, so probe the standard install
    # location before giving up.
    found = shutil.which("node")
    if found:
        return found
    candidates = [
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Program Files (x86)\nodejs\node.exe",
    ]
    for cand in candidates:
        if os.path.isfile(cand):
            return cand
    return None


def _find_npm() -> Optional[str]:
    found = shutil.which("npm")
    if found:
        return found
    candidates = [
        r"C:\Program Files\nodejs\npm.cmd",
        r"C:\Program Files (x86)\nodejs\npm.cmd",
    ]
    for cand in candidates:
        if os.path.isfile(cand):
            return cand
    return None


def _node_env() -> Dict[str, str]:
    # npm needs node on PATH; fix it up for the child process only.
    env = dict(os.environ)
    node = _find_node()
    if node:
        node_dir = os.path.dirname(node)
        env["PATH"] = node_dir + os.pathsep + env.get("PATH", "")
    return env


def _resolve_input(model_path: str) -> str:
    # Accept an absolute path or a project-relative one.
    if os.path.isabs(model_path):
        return os.path.normpath(model_path)
    return os.path.normpath(os.path.join(PROJECT_DIR, model_path))


def _newest_export_glb(since: float = 0.0) -> Optional[str]:
    # Newest GLB in Downloads that is newer than the given epoch time.
    if not os.path.isdir(DOWNLOADS_DIR):
        return None
    best: Optional[str] = None
    best_mtime = since
    for name in os.listdir(DOWNLOADS_DIR):
        low = name.lower()
        if not (low.endswith(".glb") or low.endswith(".gltf")):
            continue
        full = os.path.join(DOWNLOADS_DIR, name)
        try:
            mtime = os.path.getmtime(full)
        except OSError:
            continue
        if mtime > best_mtime:
            best_mtime = mtime
            best = full
    return best


def _read_glb_summary(path: str) -> Dict[str, Any]:
    # Parse just the glTF JSON chunk of a GLB to count animations and skins.
    # This is deliberately dependency-free: no pygltflib requirement.
    summary: Dict[str, Any] = {
        "valid_glb": False,
        "byte_size": 0,
        "animation_count": 0,
        "animation_names": [],
        "skin_count": 0,
        "joint_count": 0,
        "mesh_count": 0,
    }
    try:
        summary["byte_size"] = os.path.getsize(path)
    except OSError as exc:
        summary["error"] = "cannot stat file: " + str(exc)
        return summary

    if path.lower().endswith(".gltf"):
        # Plain .gltf is JSON already.
        try:
            with open(path, "r", encoding="utf-8") as handle:
                doc = json.load(handle)
        except Exception as exc:
            summary["error"] = "cannot parse gltf: " + str(exc)
            return summary
    else:
        try:
            with open(path, "rb") as handle:
                header = handle.read(12)
                if len(header) < 12 or header[0:4] != b"glTF":
                    summary["error"] = "not a binary GLB (bad magic)"
                    return summary
                # GLB layout: magic(4) version(4) totalLength(4), then per
                # chunk: chunkLength(4) chunkType(4) data[N]. The 12-byte
                # header above stops at the file's total length, NOT the
                # chunk's, so read the chunk header as its own 8 bytes.
                # (Reading 4 bytes here and comparing them to b"JSON"
                # compared the chunk LENGTH to the literal, which failed on
                # every valid GLB.)
                chunk_header = handle.read(8)
                if len(chunk_header) < 8:
                    summary["error"] = "truncated GLB chunk header"
                    return summary
                chunk_len = int.from_bytes(chunk_header[0:4], "little")
                chunk_type = chunk_header[4:8]
                if chunk_type != b"JSON":
                    summary["error"] = "first GLB chunk is not JSON"
                    return summary
                payload = handle.read(chunk_len)
                doc = json.loads(payload.decode("utf-8"))
        except Exception as exc:
            summary["error"] = "cannot parse GLB: " + str(exc)
            return summary

    summary["valid_glb"] = True
    anims = doc.get("animations", []) or []
    summary["animation_count"] = len(anims)
    summary["animation_names"] = [a.get("name", "?") for a in anims][:40]
    skins = doc.get("skins", []) or []
    summary["skin_count"] = len(skins)
    summary["joint_count"] = max((len(s.get("joints", []) or []) for s in skins), default=0)
    summary["mesh_count"] = len(doc.get("meshes", []) or [])
    return summary


def _server_pid_on_port() -> Optional[int]:
    # Best-effort PID lookup for whatever owns SERVER_PORT.
    try:
        out = subprocess.run(
            ["netstat", "-ano", "-p", "TCP"],
            capture_output=True, text=True, timeout=15,
        ).stdout
    except Exception:
        return None
    needle = ":" + str(SERVER_PORT)
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 5 and needle in parts[1] and parts[3] == "LISTENING":
            try:
                return int(parts[4])
            except ValueError:
                continue
    return None


# -----------------------------------------------------------------------------
# 1. Lifecycle
# -----------------------------------------------------------------------------

@mcp.tool()
def mesh2motion_status() -> Dict[str, Any]:
    # Report server state, staged models, and pending exports in one call.
    staged: List[Dict[str, Any]] = []
    if os.path.isdir(STAGE_DIR):
        for name in sorted(os.listdir(STAGE_DIR)):
            full = os.path.join(STAGE_DIR, name)
            if os.path.isfile(full):
                staged.append({
                    "name": name,
                    "path": full,
                    "bytes": os.path.getsize(full),
                    "url": SERVER_URL + "/staged/" + name,
                })

    newest = _newest_export_glb()
    export_info: Dict[str, Any] = {"found": bool(newest)}
    if newest:
        export_info["path"] = newest
        export_info["summary"] = _read_glb_summary(newest)

    return {
        "success": True,
        "app_dir": M2M_APP_DIR,
        "app_cloned": os.path.isfile(M2M_ENTRY),
        "node_installed": bool(_find_node()),
        "npm_installed": bool(_find_npm()),
        "dependencies_installed": os.path.isdir(os.path.join(M2M_APP_DIR, "node_modules")),
        "server_url": SERVER_URL,
        "server_running": _is_server_up(),
        "server_pid": _server_pid_on_port(),
        "server_log": SERVER_LOG,
        "stage_dir": STAGE_DIR,
        "staged_models": staged,
        "downloads_newest_export": export_info,
        "rigged_output_dir": RIGGED_DIR,
        "skeleton_presets": sorted(SKELETON_PRESETS.keys()),
        "note": (
            "Mesh2Motion has no headless rigging API. The skeleton fit is a "
            "human step in the browser; these tools stage and verify."
        ),
    }


@mcp.tool()
def mesh2motion_start(install: bool = True, open_browser: bool = True) -> Dict[str, Any]:
    # Start the local Mesh2Motion dev server in the background.
    if not os.path.isfile(M2M_ENTRY):
        return {
            "success": False,
            "error": "Mesh2Motion not found at " + M2M_APP_DIR,
            "fix": "git clone https://github.com/Mesh2Motion/mesh2motion-app.git " + M2M_APP_DIR,
        }

    if _is_server_up():
        return {
            "success": True,
            "already_running": True,
            "server_url": SERVER_URL,
            "pid": _server_pid_on_port(),
        }

    npm = _find_npm()
    if not npm:
        return {
            "success": False,
            "error": "node/npm not found.",
            "fix": (
                "Install Node.js LTS, or add C:\\Program Files\\nodejs to PATH. "
                "Node was detected at " + str(_find_node()) + " but npm was not."
            ),
        }

    node_modules = os.path.join(M2M_APP_DIR, "node_modules")
    if install and not os.path.isdir(node_modules):
        inst = subprocess.run(
            [npm, "install"],
            cwd=M2M_APP_DIR,
            capture_output=True,
            text=True,
            env=_node_env(),
            timeout=1800,
            shell=False,
        )
        if inst.returncode != 0:
            return {
                "success": False,
                "error": "npm install failed",
                "returncode": inst.returncode,
                "stdout_tail": inst.stdout[-2000:],
                "stderr_tail": inst.stderr[-2000:],
            }

    os.makedirs(LOG_DIR, exist_ok=True)
    log_handle = open(SERVER_LOG, "a", encoding="utf-8")
    log_handle.write("\n\n=== mesh2motion_start " + time.strftime("%Y-%m-%d %H:%M:%S") + " ===\n")
    log_handle.flush()

    # Launch detached so the server outlives this MCP request.
    creationflags = 0
    if os.name == "nt":
        creationflags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | NEW_PROCESS_GROUP

    proc = subprocess.Popen(
        [npm, "run", "dev", "--", "--port", str(SERVER_PORT), "--strictPort"],
        cwd=M2M_APP_DIR,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        env=_node_env(),
        creationflags=creationflags,
        close_fds=True,
    )

    # Poll until the port answers.
    deadline = time.time() + 90
    while time.time() < deadline:
        if _is_server_up():
            break
        if proc.poll() is not None:
            tail = ""
            try:
                with open(SERVER_LOG, "r", encoding="utf-8", errors="replace") as handle:
                    tail = handle.read()[-2000:]
            except OSError:
                pass
            return {
                "success": False,
                "error": "dev server exited immediately",
                "returncode": proc.returncode,
                "log_tail": tail,
            }
        time.sleep(1.5)

    running = _is_server_up()
    if running and open_browser:
        try:
            webbrowser.open(SERVER_URL)
        except Exception:
            pass

    return {
        "success": running,
        "server_url": SERVER_URL,
        "pid": proc.pid,
        "log": SERVER_LOG,
        "opened_browser": running and open_browser,
        "next": "Call mesh2motion_open_model with a .glb/.gltf/.fbx path.",
        "manual_stop": "Stop-Process -Id " + str(proc.pid),
    }


# -----------------------------------------------------------------------------
# 2. Staging a model for rigging
# -----------------------------------------------------------------------------

@mcp.tool()
def mesh2motion_open_model(
    model_path: str,
    skeleton: str = "human",
    open_browser: bool = True,
) -> Dict[str, Any]:
    # Stage a model into the app's static folder and hand off to the human.
    info = SKELETON_PRESETS.get(skeleton)
    if info is None:
        return {
            "success": False,
            "error": "unknown skeleton preset: " + skeleton,
            "valid_skeletons": sorted(SKELETON_PRESETS.keys()),
        }

    src = _resolve_input(model_path)
    if not os.path.isfile(src):
        return {"success": False, "error": "model not found: " + src}

    ext = os.path.splitext(src)[1].lower()
    if ext not in VIEWABLE_SUFFIXES:
        return {
            "success": False,
            "error": "unsupported format: " + ext,
            "supported": list(VIEWABLE_SUFFIXES),
            "note": "Mesh2Motion imports GLB/GLTF/DAE/FBX.",
        }

    os.makedirs(STAGE_DIR, exist_ok=True)
    dest_name = os.path.basename(src)
    dest = os.path.join(STAGE_DIR, dest_name)
    shutil.copy2(src, dest)

    started = None
    if not _is_server_up():
        started = mesh2motion_start(open_browser=False)
        if not started.get("success"):
            return {
                "success": False,
                "error": "could not start Mesh2Motion server",
                "start_result": started,
            }

    model_url = SERVER_URL + "/staged/" + dest_name
    if open_browser:
        try:
            webbrowser.open(SERVER_URL)
        except Exception:
            pass

    return {
        "success": True,
        "staged_path": dest,
        "staged_url": model_url,
        "skeleton": skeleton,
        "skeleton_label": info["label"],
        "homesteader_hint": info["hint"],
        "steps_for_the_human": [
            "1. In the Mesh2Motion tab, click Import and choose " + dest_name,
            "   (or paste " + model_url + " if the app accepts a URL).",
            "2. Choose the '" + info["label"] + "' skeleton.",
            "3. Drag the joint handles so the skeleton sits inside the mesh. "
            "Check elbows/knees bend the right way.",
            "4. Preview a walk cycle to confirm the deformation looks right.",
            "5. Tick the animations you want, then Export.",
        ],
        "after_export": (
            "The GLB downloads to " + DOWNLOADS_DIR + ". Call "
            "mesh2motion_check_export to verify it, then run the Blender "
            "retarget pass described in docs/MESH2MOTION_SETUP.md."
        ),
        "honesty_note": (
            "Steps 1-5 are manual BY DESIGN. Mesh2Motion has no rigging API; "
            "the skeleton fit is the interactive core of the tool."
        ),
    }


# -----------------------------------------------------------------------------
# 3. Export verification
# -----------------------------------------------------------------------------

@mcp.tool()
def mesh2motion_check_export(
    since_minutes: float = 120.0,
    move_to_project: bool = True,
    expected_name: str = "",
) -> Dict[str, Any]:
    # Verify an exported animated GLB landed in Downloads, optionally move it.
    since = time.time() - (since_minutes * 60.0)
    candidate: Optional[str] = None

    if expected_name:
        guess = os.path.join(DOWNLOADS_DIR, expected_name)
        if os.path.isfile(guess):
            candidate = guess
    if candidate is None:
        candidate = _newest_export_glb(since=since)

    if candidate is None:
        return {
            "success": False,
            "found": False,
            "error": (
                "No GLB/GLTF newer than "
                + str(since_minutes)
                + " minutes in "
                + DOWNLOADS_DIR
            ),
            "hint": (
                "Complete the skeleton fit and press Export in the browser "
                "first. Mesh2Motion exports to your Downloads folder."
            ),
        }

    summary = _read_glb_summary(candidate)
    has_anim = summary.get("animation_count", 0) > 0
    has_skin = summary.get("skin_count", 0) > 0

    result: Dict[str, Any] = {
        "success": True,
        "found": True,
        "export_path": candidate,
        "filename": os.path.basename(candidate),
        "summary": summary,
        "rigged": has_anim and has_skin,
    }

    if not summary.get("valid_glb"):
        result["success"] = False
        result["error"] = summary.get("error", "unreadable GLB")
        return result

    if not has_anim:
        result["warning"] = (
            "GLB has a skin but NO animation clips - you likely exported "
            "before ticking any animations. Re-export with animations selected."
        )
    if not has_skin:
        result["warning"] = (
            "GLB has no skin/joints - the export is an unrigged mesh. The "
            "skeleton fit did not bind; redo step 3 and re-export."
        )

    if move_to_project and result["rigged"]:
        os.makedirs(RIGGED_DIR, exist_ok=True)
        dest = os.path.join(RIGGED_DIR, os.path.basename(candidate))
        try:
            shutil.move(candidate, dest)
            result["moved_to"] = dest
            result["export_path"] = dest
        except Exception as exc:
            result["move_error"] = str(exc)
            result["moved_to"] = None

    result["next_step"] = (
        "Retarget to Unity Mecanim. See docs/MESH2MOTION_SETUP.md - the GLB "
        "skeleton is not a Mecanim Humanoid/Generic avatar yet."
    )
    return result


# -----------------------------------------------------------------------------
# 4. Catalog of available rigs
# -----------------------------------------------------------------------------

@mcp.tool()
def mesh2motion_list_skeletons() -> Dict[str, Any]:
    # List Mesh2Motion rig presets with Homesteader-specific usage guidance.
    return {
        "success": True,
        "count": len(SKELETON_PRESETS),
        "skeletons": [
            {"id": key, "label": val["label"], "hint": val["hint"]}
            for key, val in sorted(SKELETON_PRESETS.items())
        ],
        "source": "https://github.com/Mesh2Motion/mesh2motion-app",
        "note": (
            "Rig availability evolves upstream. Run mesh2motion_status and "
            "check the app's own skeleton dropdown for the authoritative list "
            "on your checked-out version."
        ),
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
