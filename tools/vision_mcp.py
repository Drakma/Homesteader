#!/usr/bin/env python3
"""
Homesteader Vision MCP Server

Gives an AI agent the ability to actually SEE image files, which the host's
native image reading does not provide on this machine: a PNG comes back to the
agent as an opaque binary blob with no pixels in it. This server closes that gap
by asking a vision model (Gemini, via the same GEMINI_API_KEY the rest of the
free pipeline already uses) to describe an image in text - and text the agent
can read.

Tools:
  - describe_image      : what is in this image? (art direction, composition)
  - examine_render      : is this 3D render visually correct? (asset QA)
  - compare_images      : how do these two images differ? (before/after a change)
  - analyze_silhouette  : measured geometry of the shape, not an opinion -
                          coverage, aspect ratio, bounding box. This is the one
                          to reach for when the question is "is this a plausible
                          tuft or a spiky ball", because it is arithmetic against
                          the pixels rather than a model's impression.

Why a vision model is the right tool and not a dodge: it genuinely sees the
pixels. What it is NOT is ground truth - treat its description as a reliable
second opinion, strongest on composition, colour, and "is anything obviously
broken", weakest on fine detail and on whether something is artistically GOOD.

Setup: GEMINI_API_KEY must be in assets/.env (same file the icon pipeline uses).
Requires: pip install google-genai Pillow   (both already present in this repo)
"""

import os
import io
from typing import Optional, List, Dict, Any

from PIL import Image

from mcp.server.mcpserver import MCPServer

# ---------------------------------------------------------------------------
# Paths & credentials
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PROJECT_ROOT, "assets", ".env")

# Model choice: a current multimodal Gemini. Overridable by env var so this
# does not silently rot when Google retires a model name - which already
# happened once: gemini-2.5-flash returned 404 "no longer available to new
# users", directing here.
DEFAULT_MODEL = os.environ.get("HOMESTEADER_VISION_MODEL", "gemini-3.6-flash")

_client = None
_model_name = DEFAULT_MODEL


def _load_api_key() -> Optional[str]:
    """Reads GEMINI_API_KEY from assets/.env, matching the existing pipeline."""
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    if not os.path.isfile(ENV_PATH):
        return None
    try:
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        return None
    return None


def _get_client():
    global _client
    if _client is not None:
        return _client
    key = _load_api_key()
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to assets/.env (the same file the "
            "icon pipeline reads) or export it in the environment."
        )
    try:
        from google import genai
    except ImportError:
        raise RuntimeError("google-genai is required. Run: pip install google-genai")
    _client = genai.Client(api_key=key)
    return _client


def _resolve(path: str) -> str:
    """Accepts an absolute path, or one relative to the project root."""
    if not path:
        raise ValueError("Empty image path")
    p = path if os.path.isabs(path) else os.path.join(PROJECT_ROOT, path)
    p = os.path.normpath(p)
    if not os.path.isfile(p):
        raise FileNotFoundError(f"No such image: {p}")
    return p


def _prepare(path: str, max_dim: int = 1024) -> bytes:
    """Loads an image as PNG bytes, downscaling to keep the request small.

    Downscaling matters for cost and latency, but NOT for judging a low-poly
    render: detail below ~1024px is facet noise, and the silhouette/shading
    questions this server answers survive it easily.
    """
    p = _resolve(path)
    im = Image.open(p)
    # Flatten alpha onto mid-grey: a render often has a transparent or dark
    # background, and a vision model judges an unreadable silhouette poorly
    # against flat black.
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (110, 110, 118, 255))
        im = Image.alpha_composite(bg, im).convert("RGB")
    else:
        im = im.convert("RGB")
    if max(im.size) > max_dim:
        im.thumbnail((max_dim, max_dim), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def _describe(paths: List[str], prompt: str, max_dim: int = 1024) -> str:
    client = _get_client()
    from google.genai import types

    parts = [prompt]
    for p in paths:
        parts.append(types.Part.from_bytes(data=_prepare(p, max_dim), mime_type="image/png"))
    resp = client.models.generate_content(model=_model_name, contents=parts)
    return (getattr(resp, "text", None) or "").strip()


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------
mcp = MCPServer(
    "homesteader-vision",
    instructions=(
        "Use these tools to SEE image files when the host cannot show you their "
        "pixels. describe_image answers 'what is in this'; examine_render answers "
        "'is this 3D preview broken'; compare_images answers 'what changed'; "
        "analyze_silhouette returns MEASURED shape numbers rather than an opinion, "
        "and should be preferred whenever the question is about proportion or "
        "coverage. Descriptions come from a vision model: trustworthy on "
        "composition and obvious breakage, not authoritative on fine detail or "
        "on subjective artistic quality."
    ),
)


@mcp.tool()
def describe_image(path: str, question: Optional[str] = None) -> Dict[str, Any]:
    """
    Describes what an image actually contains, for when you cannot view it.

    Args:
        path: Image file - absolute, or relative to the project root.
        question: Optional specific question to answer about the image.

    Returns:
        Dict with 'description' (the model's answer) and 'path'.
    """
    prompt = question or (
        "Describe this image precisely and concretely for someone who cannot see "
        "it. Cover: what the subject is; its shape and silhouette; colours; the "
        "background; roughly how much of the frame the subject occupies; and "
        "anything that looks broken, missing, or visually wrong. Be specific and "
        "avoid vague praise - state plainly if it looks bad or incomplete."
    )
    return {"path": path, "description": _describe([path], prompt)}


@mcp.tool()
def examine_render(path: str, asset_type: str = "3D model render") -> Dict[str, Any]:
    """
    QA a 3D asset render: reports whether the preview looks correct.

    Args:
        path: Render/image file - absolute, or relative to the project root.
        asset_type: What this is meant to be, e.g. 'low-poly grass tuft',
                    'log cabin model', 'item icon'.

    Returns:
        Dict with 'verdict', 'issues' (list) and 'raw'.
    """
    prompt = (
        f"This is a render of a {asset_type}. Judge it as a game artist would. "
        "Report, as short bullet lines:\n"
        "1. VERDICT: does it read as the intended asset? yes / partly / no.\n"
        "2. SILHOUETTE: is the outline believable, or too spiky/blocky/flat?\n"
        "3. PROPORTION: does it look the right shape, or too tall/wide/squat?\n"
        "4. FRAMING: is any part cut off by the frame, or is the subject tiny in it?\n"
        "5. DEFECTS: anything obviously broken - clipping, floating parts, holes, "
        "black or unlit faces, visible seams, z-fighting.\n"
        "Be blunt. If it does not look like the intended asset, say so first."
    )
    raw = _describe([path], prompt)
    issues = [ln.strip("-* ").strip() for ln in raw.splitlines()
              if ln.strip().startswith(("-", "*")) and ln.strip("* -")]
    verdict = ""
    for ln in raw.splitlines():
        if "VERDICT" in ln.upper():
            verdict = ln.split(":", 1)[-1].strip()
            break
    return {"path": path, "asset_type": asset_type,
            "verdict": verdict or "unstated", "issues": issues, "raw": raw}


@mcp.tool()
def compare_images(before: str, after: str, question: Optional[str] = None) -> Dict[str, Any]:
    """
    Describes how two images differ - for checking whether a change helped.

    Args:
        before: The earlier image.
        after: The later image.
        question: Optional specific question, e.g. 'is the grass now more upright?'

    Returns:
        Dict with 'comparison' and both paths.
    """
    prompt = question or (
        "These are two versions of the same asset, BEFORE then AFTER. Describe "
        "concretely what changed: silhouette, proportions, density, orientation, "
        "colours, anything appearing or disappearing. Then state plainly whether "
        "the AFTER version looks better, worse, or about the same, and why. Do "
        "not be encouraging - report what is actually visible."
    )
    return {"before": before, "after": after,
            "comparison": _describe([before, after], prompt)}


@mcp.tool()
def analyze_silhouette(path: str, bg_tolerance: int = 28) -> Dict[str, Any]:
    """
    Measured shape statistics for an image - arithmetic on the pixels, not an opinion.

    Prefer this over a description when the question is about PROPORTION or
    COVERAGE, because it cannot hallucinate: it counts pixels. Answers things
    like "is the silhouette wider than it is tall" or "is the subject a thin
    vertical sliver or a sprawling ball" with hard numbers.

    Args:
        path: Image file - absolute, or relative to the project root.
        bg_tolerance: How close to the corner colour a pixel must be to count as
                      background (0-255 per channel, summed).

    Returns:
        Dict of measured stats: coverage, aspect ratio, bounding box, edge contact.
    """
    p = _resolve(path)
    im = Image.open(p).convert("RGBA")
    w, h = im.size
    px = im.load()

    # Background is sampled from all four corners and treated as "whatever the
    # renderer used", rather than assuming a specific colour.
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    opaque_corners = [c for c in corners if c[3] > 200]
    if opaque_corners:
        bg = tuple(sum(c[i] for c in opaque_corners) // len(opaque_corners) for i in range(3))
    else:
        bg = (0, 0, 0)

    min_x, min_y, max_x, max_y = w, h, -1, -1
    subject = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a <= 16:
                continue
            if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) <= bg_tolerance:
                continue
            subject += 1
            if x < min_x:
                min_x = x
            if x > max_x:
                max_x = x
            if y < min_y:
                min_y = y
            if y > max_y:
                max_y = y

    if max_x < 0:
        return {"path": path, "error": "no subject pixels found - image may be "
                                       "blank, fully transparent, or a flat colour"}

    bw = max_x - min_x + 1
    bh = max_y - min_y + 1
    return {
        "path": path,
        "image_size": [w, h],
        "background_rgb": list(bg),
        "subject_pixels": subject,
        "coverage_pct": round(100.0 * subject / float(w * h), 2),
        "bbox": {"x": min_x, "y": min_y, "w": bw, "h": bh},
        "bbox_aspect_w_over_h": round(bw / float(bh), 3),
        "bbox_fill_pct": round(100.0 * subject / float(bw * bh), 2),
        "touches_edges": {
            "left": min_x <= 1, "right": max_x >= w - 2,
            "top": min_y <= 1, "bottom": max_y >= h - 2,
        },
        "reads_as": (
            "tall/narrow" if bh > bw * 1.3 else
            "wide/flat" if bw > bh * 1.3 else
            "roughly square"
        ),
    }


def main():
    mcp.run()


if __name__ == "__main__":
    main()
