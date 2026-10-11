#!/usr/bin/env python3
# Homesteader cpu3d MCP server (stdio). Wraps tools/cpu3d_client.py so an agent can call the free
# rigged-creature pipeline as real tools: one clear full-body image of a human, quadruped, bird or
# fish in, a low-poly rigged and animated GLB out. The work runs on the cpu3d LAN PC (config in the
# gitignored tools/cpu3d_connection.json), so there are no credits and no approval to ask for.
# A job takes seconds to minutes: every generate/submit tool returns a job id at once, cpu3d_status waits (up to 50 s a call),
# cpu3d_download saves the finished files. After downloading, still run gait_fix.py and loop_fix.py.
# Edit rule: no triple-quoted strings; run python tools/check_syntax.py tools/cpu3d_mcp.py after editing.

from __future__ import annotations

import os
import sys
from typing import Any, Dict, Optional

from mcp.server.mcpserver import MCPServer

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)
import cpu3d_client as c3  # noqa: E402

mcp = MCPServer(
    "cpu3d",
    instructions=(
        "cpu3d runs on a LAN PC: FREE, no credits, no approval. It makes pictures (cpu3d_generate_image), music "
        "(cpu3d_generate_music, MP3), rigged animated low-poly models of animals and people from a text description "
        "(cpu3d_generate_creature, recommended) or of animals, people and vehicles from one image (cpu3d_submit), plus extra "
        "animation clips and vehicle recolours. All jobs share one queue: every tool returns a job_id, poll cpu3d_status "
        "until done, then cpu3d_download. Models then still need tools/gait_fix.py and tools/loop_fix.py."
    ),
)


def _err(e: Exception) -> Dict[str, Any]:
    return {"ok": False, "error": str(e)}


def _b64(image_path: str) -> str:
    import base64
    path = image_path if os.path.isabs(image_path) else os.path.join(PROJECT_DIR, image_path)
    if not os.path.isfile(path):
        raise c3.Cpu3dError("no such image: " + path)
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _submit(tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return {"ok": True, "job_id": c3.Session().call(tool, args, timeout=120)["job_id"]}
    except Exception as e:
        return _err(e)


@mcp.tool()
def cpu3d_info() -> Dict[str, Any]:
    # Is the cpu3d PC reachable; its kinds, limits, clips, animation library and vehicle palette.
    try:
        return {"ok": True, "server": c3.server_info()}
    except Exception as e:
        return _err(e)


@mcp.tool()
def cpu3d_generate_image(prompt: str, name: str = "image", cutout: bool = False, pad_square: bool = False) -> Dict[str, Any]:
    # A picture from a text prompt (Gemini on the cpu3d PC). Returns job_id; poll cpu3d_status, then cpu3d_download for <name>.png.
    # cutout also returns <name>_cutout.png (subject on transparency): the prompt must ask for ONE flat key-colour background the subject does not contain, e.g. pure magenta #FF00FF.
    return _submit("generate_image", {"prompt": prompt, "name": name, "cutout": cutout, "pad_square": pad_square})


@mcp.tool()
def cpu3d_generate_music(prompt: str, name: str = "track", max_attempts: int = 4) -> Dict[str, Any]:
    # A music track from a text prompt (Gemini on the cpu3d PC), returned as an MP3 (1-2 minutes). Describe genre, instruments, mood, tempo, instrumental or not. Gemini picks the length. Returns job_id.
    return _submit("generate_music", {"prompt": prompt, "name": name, "max_attempts": max_attempts})


@mcp.tool()
def cpu3d_generate_creature(subject: str, kind: str, size_m: float, name: str = "creature", faces: int = 4000, texture_size: int = 1024,
                            image_path: str = "") -> Dict[str, Any]:
    # RECOMMENDED for animals and people (not vehicles): a rigged, UV-textured low-poly GLB/FBX/Blend from a text description, 3-4 minutes.
    # kind: quadruped, bird, fish or human. size_m: real length in metres (height for a human). faces 500-10000 (project budget: under 5000).
    # image_path: optional picture with one flat background colour instead of the Gemini drawing. Returns job_id.
    try:
        args = {"subject": subject, "kind": kind, "size_m": size_m, "name": name, "faces": faces, "texture_size": texture_size, "image_base64": _b64(image_path) if image_path else ""}
    except Exception as e:
        return _err(e)
    return _submit("generate_creature", args)


@mcp.tool()
def cpu3d_submit(image_path: str, name: str, kind: str = "auto", faces: int = 1500, flat: bool = False, flip: bool = False, mc_resolution: int = 192,
                 previews: bool = False, size_m: float = 0.0, width_m: float = 0.0, height_m: float = 0.0, texture_size: int = 1024, zones: bool = False,
                 palette: Optional[Dict[str, str]] = None, body_color: str = "", cab_u: str = "auto", planar_deg: float = 0.0, smooth_iters: int = 3) -> Dict[str, Any]:
    # One image to a rigged model (TripoSR path). Use this for VEHICLES (kind vehicle: zones and palette repaint it by part; recolor later with cpu3d_recolor); animals and people are better via cpu3d_generate_creature.
    # kind: auto, human, quadruped, bird, fish, vehicle. Pass real size_m (length, height for a human), width_m, height_m when known: one picture cannot tell the depth.
    try:
        if kind not in c3.KINDS:
            return {"ok": False, "error": "kind must be one of " + ", ".join(c3.KINDS)}
        args = {"image_base64": _b64(image_path), "kind": kind, "faces": faces, "name": name, "flat": flat, "flip": flip, "mc_resolution": mc_resolution, "previews": previews,
                "size_m": size_m, "width_m": width_m, "height_m": height_m, "texture_size": texture_size, "zones": zones, "palette": palette, "body_color": body_color,
                "cab_u": cab_u, "planar_deg": planar_deg, "smooth_iters": smooth_iters}
    except Exception as e:
        return _err(e)
    return _submit("submit_creature", args)


@mcp.tool()
def cpu3d_add_animation(job_id: str, clips: Optional[list] = None, custom: Optional[list] = None, label: str = "", extend: str = "") -> Dict[str, Any]:
    # Add clips to a finished rigged animal or person (about 15-30 s). clips: names from cpu3d_info()['animation_library'] (quadruped Run, Trot, Graze, LookAround; human Run, Wave, Jump, Work, LookAround; bird Walk, Peck, Hop, FlapFast).
    # custom: up to 8 {name, frames, tracks} clips (see the server's add_animation description). extend: label of an earlier result to build on. Files land under animations/<label>/ in the job.
    return _submit("add_animation", {"job_id": job_id, "clips": clips, "custom": custom, "label": label, "extend": extend})


@mcp.tool()
def cpu3d_recolor(job_id: str, colors: Dict[str, str], label: str = "") -> Dict[str, Any]:
    # Recolour a finished VEHICLE job (made with zones or palette) by part, about 10 s: colors like {"body": "#1f6f3a"}. Files land under recolors/<label>/.
    return _submit("recolor_job", {"job_id": job_id, "colors": colors, "label": label})


@mcp.tool()
def cpu3d_list_jobs(limit: int = 20) -> Dict[str, Any]:
    # Most recent jobs, newest first.
    try:
        return {"ok": True, "jobs": c3.Session().call("list_jobs", {"limit": limit})}
    except Exception as e:
        return _err(e)


@mcp.tool()
def cpu3d_cancel(job_id: str) -> Dict[str, Any]:
    # Cancel a queued or running job.
    try:
        return {"ok": True, "result": c3.Session().call("cancel_job", {"job_id": job_id})}
    except Exception as e:
        return _err(e)


@mcp.tool()
def cpu3d_status(job_id: str, wait_seconds: int = 50) -> Dict[str, Any]:
    # Job state: status (queued, running, done, failed, cancelled), stage, files when done. Waits up to wait_seconds for a change.
    try:
        sess = c3.Session()
        job = sess.call("get_job", {"job_id": job_id, "wait_seconds": max(0, min(int(wait_seconds), 50))}, timeout=120)
        return {"ok": True, "job": job}
    except Exception as e:
        return _err(e)


@mcp.tool()
def cpu3d_download(job_id: str, out_dir: str = "") -> Dict[str, Any]:
    # Save every result file of a finished job. Default folder: assets/_scratch/cpu3d/<job_id>.
    try:
        sess = c3.Session()
        job = sess.call("get_job", {"job_id": job_id, "wait_seconds": 0}, timeout=60)
        if job.get("status") != "done":
            return {"ok": False, "error": "job is " + str(job.get("status")), "job": job}
        dest = out_dir or os.path.join(PROJECT_DIR, "assets", "_scratch", "cpu3d", job_id)
        if not os.path.isabs(dest):
            dest = os.path.join(PROJECT_DIR, dest)
        saved = []
        for f in job["files"]:
            target = os.path.join(dest, f["path"])
            sess.download(f["url"], target)
            saved.append(target)
        report = job.get("report") or {}
        icon = report.get("icon")   # the clean 128x128 catalog icon the server makes for a creature (model/<name>/<name>.png)
        icon_path = os.path.join(dest, *icon.split("/")) if icon else None
        return {"ok": True, "out_dir": dest, "files": saved, "icon": icon_path if icon_path and os.path.isfile(icon_path) else None, "report": report}
    except Exception as e:
        return _err(e)


if __name__ == "__main__":
    mcp.run(transport="stdio")
