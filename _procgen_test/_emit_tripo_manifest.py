"""_emit_tripo_manifest.py - emit a `tripo batch run` manifest YAML for
the Homesteader catalog.

Walks the asset catalog and produces a YAML file that the official
tripo-cli's `tripo batch run` consumes for bulk 3D generation with
concurrency, retries, resume. Each catalog item becomes one job with
either a text prompt or an input image path.

Output: assets/_tripo_manifest.yaml

Usage:
    python _procgen_test/_emit_tripo_manifest.py
    python _procgen_test/_emit_tripo_manifest.py --mode image
    python _procgen_test/_emit_tripo_manifest.py --mode both

Then:
    tripo batch run assets/_tripo_manifest.yaml
"""

import argparse
import os
import yaml

PROJ = r"C:\Users\casey\Desktop\Homesteader"
ASSETS = os.path.join(PROJ, "assets")

# Same 12 categorical sweep targets as _sweep_text_to_3d.py.
SWEEP_CATEGORIES = [
    "structures", "farming", "ranching", "fishing", "fuel",
    "electricity", "water", "waste", "internet", "food",
    "appliances", "vehicles",
]

# Natural-language prompt template for text-to-3D. Short - Tripo3D
# preference is < 60 tokens.
PROMPT_TEMPLATE = (
    "a 3D model of {name}, low-poly faceted style, simple geometry, "
    "stylized game asset, single object, no surroundings"
)


def walk_catalog(category, mode):
    """Yield (item_id, name, prompt_or_image, output_relpath) tuples.

    `mode` selects whether we emit text prompts (`mode='text'`),
    image paths (`mode='image'`), or both (`mode='both'` -> one
    entry per item, image preferred when a real icon PNG exists).
    """
    cat_dir = os.path.join(ASSETS, category)
    if not os.path.isdir(cat_dir):
        return
    for entry in sorted(os.listdir(cat_dir)):
        if entry.startswith("_") or entry.startswith("seed_"):
            continue
        group_dir = os.path.join(cat_dir, entry)
        manifest_path = os.path.join(group_dir, f"{entry}.json")
        if not os.path.isfile(manifest_path):
            continue
        try:
            import json
            d = json.load(open(manifest_path, encoding="utf-8"))
        except Exception:
            continue
        name = d.get("name", entry.replace("_", " ").title())
        icon_name = d.get("icon", f"{entry}.png")
        icon_path = os.path.join(group_dir, icon_name)
        prompt = PROMPT_TEMPLATE.format(name=name)
        # Output gets written to ./tripo-out/<task_id>/ by the CLI; we
        # then rename it into place. The manifest just declares intent.
        if mode in ("text", "both"):
            yield (entry, name, prompt, None, category)
        if mode == "image" and os.path.isfile(icon_path):
            yield (entry, name, None, icon_path, category)
        elif mode == "both" and os.path.isfile(icon_path):
            # In 'both' mode we prefer the icon path over text prompt.
            yield (entry, name, None, icon_path, category)


def build_manifest(mode):
    """Build the YAML manifest dict for tripo batch."""
    jobs = []
    seen = set()
    for cat in SWEEP_CATEGORIES:
        for entry, name, prompt, image, _ in walk_catalog(cat, mode):
            # Deduplicate - if we already added this entry as text, but
            # the second pass added it as image (mode='both'), dedupe
            # by item id; keep image variant.
            if entry in seen:
                continue
            seen.add(entry)
            job = {"id": entry, "name": name}
            if image:
                job["input"] = image
            else:
                job["prompt"] = prompt
            # Output naming is the CLI's standard; we map below.
            job["output"] = f"_models/{entry}.glb"
            jobs.append(job)
    return {
        "version": 1,
        "concurrency": 2,        # 2 in-flight to stay polite
        "retries": 3,
        "format": "glb",
        "jobs": jobs,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ASSETS, "_tripo_manifest.yaml"))
    ap.add_argument("--mode", default="text",
                    choices=["text", "image", "both"])
    args = ap.parse_args()

    if not yaml:
        print("[emit] PyYAML not installed; pip install pyyaml.")
        raise SystemExit(1)

    manifest = build_manifest(args.mode)
    with open(args.out, "w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, sort_keys=False, default_flow_style=False)
    n = len(manifest["jobs"])
    print(f"[emit] {args.out}: {n} jobs (mode={args.mode}, "
          f"concurrency={manifest['concurrency']})")
    print(f"[emit] run with: tripo batch run {args.out}")


if __name__ == "__main__":
    main()
