"""Search the web for reference images, download them, then LOOK at them locally.

The full loop the agent needs, with no paid service anywhere in it:

    search  -> find candidate image URLs (web search)
    fetch   -> download the images to a local cache
    see     -> describe each one with a LOCAL vision model (torch/transformers,
               GPU, no API key, no quota, works offline after first download)
    measure -> objective silhouette numbers (pure Pillow, cannot hallucinate)

Why the pieces are split this way:
  - Finding images is a text problem, and web search already solves it cheaply.
  - Looking at them must be local, because every hosted vision service either
    needs a paid key or rate-limits anonymous use. A local model costs nothing
    per call and cannot be taken away.
  - Measuring is separate from describing on purpose: a vision model can
    misjudge a proportion, but pixel counting cannot. When the two disagree,
    believe the measurement.

Usage:
    # Look at an image you already have
    python tools/reference_images.py see --image path/to/ref.png

    # Download from a URL, then look at it
    python tools/reference_images.py fetch --url https://... --name tuft
    python tools/reference_images.py see --image _refs/tuft.png

    # Measure only (fast, no model load)
    python tools/reference_images.py measure --image _refs/tuft.png

    # Everything for one URL
    python tools/reference_images.py all --url https://... --name tuft
"""
import argparse
import os
import sys
import urllib.parse
import urllib.request

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_DIR = os.path.join(PROJECT_ROOT, "_refs")

# A browser UA: many CDNs (Unity's key-image host among them) 403 a bare urllib
# request, and a rejected download looks identical to a bad URL.
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"

VALID_EXT = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")


def _abs(path):
    p = path if os.path.isabs(path) else os.path.join(PROJECT_ROOT, path)
    return os.path.normpath(p)


def cmd_fetch(url, name, timeout=60):
    """Downloads one image URL into _refs/<name>.<ext>."""
    os.makedirs(REF_DIR, exist_ok=True)
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower()
    if ext not in VALID_EXT:
        ext = ".png"
    dest = os.path.join(REF_DIR, name + ext)

    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
    except Exception as e:
        print("FETCH FAILED %s: %s: %s" % (url, type(e).__name__, str(e)[:160]))
        return None

    # Verify it is actually an image rather than an HTML error page that
    # happened to return 200 - a common trap with CDN links.
    try:
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(data))
        im.verify()
    except Exception as e:
        print("NOT AN IMAGE %s (%d bytes): %s" % (url, len(data), str(e)[:120]))
        return None

    with open(dest, "wb") as f:
        f.write(data)
    print("FETCHED %s (%s bytes) -> %s" % (url, format(len(data), ","), dest))
    return dest


def cmd_measure(path):
    """Objective silhouette stats. No model, no network, cannot hallucinate."""
    import vision_mcp as v
    r = v.analyze_silhouette(path)
    print("MEASURED  %s" % path)
    for k in ("image_size", "coverage_pct", "bbox", "bbox_aspect_w_over_h",
              "bbox_fill_pct", "reads_as"):
        print("   %-22s %s" % (k, r.get(k)))
    print("   %-22s %s" % ("touches_edges", r.get("touches_edges")))
    if r.get("error"):
        print("   ERROR: %s" % r["error"])
    return r


def cmd_see(path, model="blip"):
    """Describe the image using a LOCAL vision model."""
    import see_image
    print("LOOKING AT %s (local model: %s)" % (path, model))
    if model == "blip":
        real, text = see_image.caption_blip(path)
        print("   caption: %s" % text)
    else:
        real, text = see_image.ask_florence(path)
        print("   detail : %s" % text)


def main():
    ap = argparse.ArgumentParser(description="Search/download/see/measure reference images.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("fetch")
    p.add_argument("--url", required=True)
    p.add_argument("--name", required=True)

    p = sub.add_parser("see")
    p.add_argument("--image", required=True)
    p.add_argument("--model", choices=["blip", "florence"], default="blip")

    p = sub.add_parser("measure")
    p.add_argument("--image", required=True)

    p = sub.add_parser("all")
    p.add_argument("--url", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--model", choices=["blip", "florence"], default="blip")

    args = ap.parse_args()
    if args.cmd == "fetch":
        cmd_fetch(args.url, args.name)
    elif args.cmd == "see":
        cmd_see(args.image, args.model)
    elif args.cmd == "measure":
        cmd_measure(args.image)
    elif args.cmd == "all":
        got = cmd_fetch(args.url, args.name)
        if got:
            cmd_see(got, args.model)
            cmd_measure(got)


if __name__ == "__main__":
    # tools/ holds see_image.py and vision_mcp.py; import them by bare name.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
