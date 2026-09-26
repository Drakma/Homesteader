#!/usr/bin/env python
"""Prompt batches for image generation (Nano Banana) -> icons -> Meshy.

Flow
  1. gen     : turn a list of items into image prompts. Every prompt carries a short TAG that the image
               generator must write small in the bottom-left corner. The tag is how a finished picture is
               matched back to its item; it is recorded in a ledger.
  2. (you)   : paste the prompts into Nano and save the pictures into one folder.
  3. ingest  : scan that folder, match pictures to items (tag in the file name, or --assign FILE=TAG after
               reading the tag off the picture), copy them into the batch.
  4. clean   : erase the tag, trim the background to transparent, write a clean picture per item
               (and a 128x128 icon) ready to feed to Meshy image-to-3D.
  5. status  : who is waiting for what.

Files live in assets/_prompt_batches/<batch>/ ; the ledger is assets/_prompt_batches/ledger.json.

Item lines (text file, one per line, '#' comments):   item_id | Display name | description [| category]
    animal_dog_beagle | Beagle | a friendly tricolor beagle standing | ranching

Variants sheet (several DIFFERENT items in one picture, e.g. a set of light poles): '@variants id | Name | shared style [| category]'
with the same indented item lines. One prompt, one sheet, distinct designs on a shared scale; `clean` cuts it into one picture per item.

Groups (stages of a crop, growth of a tree, damage states...): a '@group' line, then one indented line per
stage: 'suffix | name | description [| height%]'. A group is ONE prompt and ONE picture: a single sheet with every
stage in a row, left to right, on a shared ground line and at true relative scale (that is the only way to keep
the stages to scale with each other and the same design). One tag per sheet. `clean` cuts the sheet back into
one picture per stage (item id <group_id>_<suffix>) on a shared canvas so relative size survives.
The optional height% is the stage's height relative to the tallest stage.
    @group crop_tomato | Tomato plant | a tomato plant in a round terracotta pot | farming
      seedling | Seedling | two tiny green leaves just sprouting | 15
      flowering | Flowering | tall vine on a stake with yellow flowers | 70
      ripe | Ripe | heavy with bright red ripe tomatoes | 100
CLI: --group "crop_tomato | Tomato plant | shared desc | farming" --stage "seedling | Seedling | desc | 15" ...

  python tools/prompt_batch.py gen --batch crops --file crops.txt        # with @group blocks
  python tools/prompt_batch.py gen --batch dogs --item "tool_pick | Pickaxe | steel pickaxe with wooden handle | tools"
  python tools/prompt_batch.py ingest --batch dogs --dir C:/Users/me/Downloads/nano [--assign img1.png=K7QF]
  python tools/prompt_batch.py clean --batch dogs
  python tools/prompt_batch.py status [--batch dogs]
"""
import argparse
import hashlib
import json
import os
import random
import re
import shutil
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(BASE, "assets", "_prompt_batches")
LEDGER = os.path.join(ROOT, "ledger.json")
IMG_EXT = (".png", ".jpg", ".jpeg", ".webp")

# no 0/O/1/I/L/5/S/2/Z/8/B: keeps a tag readable on a small, possibly stylised render
ALPHABET = "ACDEFGHJKMNPQRTUVWXY34679"
TAG_LEN = 4

LOWPOLY = ("STYLE: a true low-poly 3D model render, like a low-polygon game asset. The whole object is built from a small number "
           "of large flat triangular and angular polygon facets with hard visible edges between them; every surface is "
           "flat-shaded, each facet a single flat colour with soft simple lighting, so you can count the planes. Chunky "
           "simplified shapes, no fine detail, no smooth curves or gradients, no realistic textures, no fur/leaf/bark "
           "detail, no outlines, not painterly, not photographic, not pixel art, not a cartoon illustration. Limited "
           "natural colour palette. Soft top-left key light.")
STYLE = (LOWPOLY + " Single object, isometric 3/4 front view, centered, full object in frame with generous empty margin, "
         "modern-day item, plain flat solid light-grey background, no shadow on the ground, no other objects, no text except the tag")
TAG_RULE = ("In the bottom-left corner, write the code {tag} in small, plain, dark, sans-serif capital letters "
            "on the flat background, well clear of the object. Write it exactly, nothing else.")


def load_ledger():
    if os.path.isfile(LEDGER):
        with open(LEDGER, encoding="utf-8") as f:
            return json.load(f)
    return {"tags": {}}


def save_ledger(led):
    os.makedirs(ROOT, exist_ok=True)
    with open(LEDGER, "w", encoding="utf-8") as f:
        json.dump(led, f, indent=2)


def new_tag(led):
    for _ in range(1000):
        t = "".join(random.choice(ALPHABET) for _ in range(TAG_LEN))
        if t not in led["tags"]:
            return t
    raise RuntimeError("out of tags")


def parse_item(line):
    parts = [p.strip() for p in line.split("|")]
    if len(parts) < 3:
        raise ValueError(f"need 'item_id | name | description [| category]': {line!r}")
    item_id, name, desc = parts[0], parts[1], parts[2]
    cat = parts[3] if len(parts) > 3 else ""
    if not re.fullmatch(r"[a-z0-9_]+", item_id):
        raise ValueError(f"item_id must be lower snake_case: {item_id!r}")
    return item_id, name, desc, cat


SHEET_STYLE = (LOWPOLY + " Isometric 3/4 front view, modern-day items, plain flat solid light-grey background, "
               "no shadow on the ground, no text except the tag")


def build_prompt(name, desc, tag, group=None):
    if group:
        g = group
        n = len(g["stage_defs"])
        if g.get("kind") == "variants":
            rows = []
            for k, sd in enumerate(g["stage_defs"], 1):
                h = f" (about {sd['height']}% of the tallest one's height)" if sd.get("height") else ""
                rows.append(f"{k}. {sd['name']}: {sd['desc']}{h}")
            return (f"One single image showing {n} different {g['name']} ({g['shared']}), arranged in ONE horizontal row "
                    f"from left to right in this exact order, with a clear empty gap between neighbours so nothing overlaps "
                    f"or touches: " + "; ".join(rows) + ". "
                    f"Each is its own distinct design; they share only the same art style. "
                    f"SCALE: they all stand on one shared ground line and are drawn with the same camera, zoom and angle, each "
                    f"at its true size relative to the others; do not crop any of them. {SHEET_STYLE}. {TAG_RULE.format(tag=tag)}")
        rows = []
        for k, sd in enumerate(g["stage_defs"], 1):
            h = f" (about {sd['height']}% of the tallest one's height)" if sd.get("height") else ""
            rows.append(f"{k}. {sd['name']}: {sd['desc']}{h}")
        return (f"One single image showing {n} stages of the same {g['name']} ({g['shared']}), arranged in ONE "
                f"horizontal row from left to right in this exact order, with a clear empty gap between neighbours so "
                f"nothing overlaps or touches: " + "; ".join(rows) + ". "
                f"All {n} are the SAME object (same design, base, colours and style); only the growth/state changes. "
                f"SCALE: they all stand on one shared ground line and are drawn with the same camera, zoom and angle, "
                f"each at its true size relative to the others, so a small stage stays small and is NOT enlarged to "
                f"match the biggest; do not crop any of them. {SHEET_STYLE}. {TAG_RULE.format(tag=tag)}")
    return f"{name}: {desc}. {STYLE}. {TAG_RULE.format(tag=tag)}"


def expand_items(lines, group_cli=None, stage_cli=None):
    """Flatten the raw lines into (item_id, name, desc, cat, group_dict|None) entries."""
    entries, cur = [], None

    def flush():
        nonlocal cur
        if cur:
            defs = [{"suffix": st[0], "item_id": cur["id"] + "_" + st[0], "name": st[1], "desc": st[2], "height": st[3]}
                    for st in cur["stages"]]
            g = {"id": cur["id"], "name": cur["name"], "shared": cur["shared"], "stage_defs": defs, "kind": cur["kind"]}
            entries.append((cur["id"], cur["name"], cur["shared"], cur["cat"], g))
        cur = None

    all_lines = list(lines)
    if group_cli:
        all_lines = ["@group " + group_cli] + ["  " + x for x in (stage_cli or [])] + all_lines
    for raw in all_lines:
        line = raw.strip()
        if line.startswith("@group") or line.startswith("@variants"):
            flush()
            kind = "variants" if line.startswith("@variants") else "stages"
            parts = [x.strip() for x in line[len("@variants" if kind == "variants" else "@group"):].split("|")]
            if len(parts) < 3 or not re.fullmatch(r"[a-z0-9_]+", parts[0]):
                raise ValueError("bad @group line (need 'id | name | shared description [| category]'): " + line)
            cur = {"id": parts[0], "name": parts[1], "shared": parts[2], "cat": parts[3] if len(parts) > 3 else "", "stages": [], "kind": kind}
        elif cur is not None and raw[:1] in (" ", chr(9)):
            q = [x.strip() for x in line.split("|")]
            if len(q) < 3 or not re.fullmatch(r"[a-z0-9_]+", q[0]):
                raise ValueError("bad stage line (need 'suffix | name | description [| height%]'): " + line)
            h = None
            if len(q) > 3 and q[3]:
                h = q[3].rstrip("% ")
            cur["stages"].append((q[0], q[1], q[2], h))
        else:
            flush()
            item_id, name, desc, cat = parse_item(line)
            entries.append((item_id, name, desc, cat, None))
    flush()
    return entries


def batch_dir(batch):
    return os.path.join(ROOT, batch)


def cmd_gen(a):
    led = load_ledger()
    lines = list(a.item or [])
    if a.file:
        with open(a.file, encoding="utf-8") as f:
            lines += [l.rstrip("\r\n") for l in f if l.strip() and not l.strip().startswith("#")]
    if not lines and not a.group:
        sys.exit("no items (use --file, --item or --group/--stage)")
    entries = expand_items(lines, a.group, a.stage)
    out = []
    existing = {(e["batch"], e["item_id"]): t for t, e in led["tags"].items()}
    for item_id, name, desc, cat, grp in entries:
        key = (a.batch, item_id)
        if key in existing and not a.redo:
            tag = existing[key]
            print(f"[keep] {item_id} keeps tag {tag} (use --redo for a new one)")
        else:
            if key in existing:
                led["tags"].pop(existing[key], None)
            tag = new_tag(led)
        prompt = build_prompt(name, desc, tag, grp)
        led["tags"][tag] = {"batch": a.batch, "item_id": item_id, "name": name, "category": cat,
                            "description": desc, "prompt": prompt, "status": "prompted",
                            "created": time.strftime("%Y-%m-%d %H:%M:%S")}
        if grp:
            led["tags"][tag].update({"group": grp["id"], "group_name": grp["name"],
                                     "stages": len(grp["stage_defs"]), "stage_defs": grp["stage_defs"]})
        out.append((tag, item_id, prompt))
    save_ledger(led)
    d = batch_dir(a.batch)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "prompts.txt")
    with open(path, "a", encoding="utf-8") as f:
        for tag, item_id, prompt in out:
            e = led["tags"][tag]
            gi = f"  (sheet of {e['stages']} stages)" if e.get("group") else ""
            f.write(f"[{tag}] {item_id}{gi}\n{prompt}\n\n")
    for tag, item_id, prompt in out:
        e = led["tags"][tag]
        gi = f"  (sheet of {e['stages']} stages: " + ", ".join(sd["suffix"] for sd in e["stage_defs"]) + ")" if e.get("group") else ""
        print(f"\n[{tag}] {item_id}{gi}\n{prompt}")
    print(f"\n{len(out)} prompt(s) written to {path}")


def find_tag(filename, led, batch):
    stem = os.path.splitext(os.path.basename(filename))[0].upper()
    for m in re.findall(r"[A-Z0-9]{%d}" % TAG_LEN, stem):
        e = led["tags"].get(m)
        if e and e["batch"] == batch:
            return m
    return None


def cmd_ingest(a):
    led = load_ledger()
    d = batch_dir(a.batch)
    raw = os.path.join(d, "raw")
    os.makedirs(raw, exist_ok=True)
    assign = {}
    for pair in a.assign or []:
        fn, _, tag = pair.partition("=")
        assign[os.path.basename(fn)] = tag.strip().upper()
    seen = {e.get("sha1") for e in led["tags"].values() if e.get("sha1")}
    matched, unmatched, dup = [], [], []
    for fn in sorted(os.listdir(a.dir)):
        if not fn.lower().endswith(IMG_EXT):
            continue
        src = os.path.join(a.dir, fn)
        with open(src, "rb") as f:
            sha = hashlib.sha1(f.read()).hexdigest()
        if sha in seen:
            dup.append(fn)
            continue
        tag = assign.get(fn) or find_tag(fn, led, a.batch)
        e = led["tags"].get(tag) if tag else None
        if not e or e["batch"] != a.batch:
            unmatched.append(fn)
            continue
        ext = os.path.splitext(fn)[1].lower()
        dst = os.path.join(raw, f"{e['item_id']}{ext}")
        shutil.copy2(src, dst)
        e.update({"status": "ingested", "raw": os.path.relpath(dst, BASE).replace("\\", "/"), "sha1": sha})
        seen.add(sha)
        matched.append((fn, tag, e["item_id"]))
    save_ledger(led)
    for fn, tag, iid in matched:
        print(f"[ok]   {fn} -> {tag} {iid}")
    for fn in dup:
        print(f"[dup]  {fn} (already ingested)")
    for fn in unmatched:
        print(f"[????] {fn}: no tag in the file name. Read the tag off the picture and run: --assign {fn}=TAG")
    print(f"\n{len(matched)} matched, {len(unmatched)} unmatched, {len(dup)} already ingested")


def key_image(src):
    """Full-size RGBA: tag corner wiped, background keyed to transparent."""
    from PIL import Image
    import statistics
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    px = im.load()
    border = [px[x, 0][:3] for x in range(0, w, 4)] + [px[x, h - 1][:3] for x in range(0, w, 4)] + \
             [px[0, y][:3] for y in range(0, h, 4)] + [px[w - 1, y][:3] for y in range(0, h, 4)]
    bg = tuple(int(statistics.median(c[i] for c in border)) for i in range(3))
    tw, th = int(w * 0.16), int(h * 0.12)
    for y in range(h - th, h):
        for x in range(0, tw):
            px[x, y] = bg + (255,)
    lo, hi = 14.0, 44.0
    try:
        import numpy as np
        from scipy import ndimage
    except ImportError:
        np = None
    if np is not None:
        # Only background CONNECTED to the picture edge is removed, so a grey object (a lamp shade, a steel pole)
        # is never punched through where its colour happens to match the backdrop.
        arr = np.array(im)
        dist = np.sqrt(((arr[:, :, :3].astype(float) - np.array(bg, float)) ** 2).sum(axis=2))
        lab, n = ndimage.label(dist < 30)
        edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
        bgconn = np.isin(lab, list(edge))
        alpha = np.full(dist.shape, 255, dtype=float)
        alpha[bgconn] = 0
        # enclosed pockets of pure backdrop (the gap between a bracket and its post) go too; grey OBJECT surfaces
        # differ from the backdrop by more than this, so they stay
        lab2, n2 = ndimage.label(dist < 9)
        if n2:
            sizes = ndimage.sum(np.ones_like(lab2), lab2, range(1, n2 + 1))
            big = [i + 1 for i, sz in enumerate(sizes) if sz >= 60]
            alpha[np.isin(lab2, big)] = 0
        # soft edge: pixels touching the removed area fade in by colour distance
        rim = ndimage.binary_dilation(bgconn, iterations=2) & ~bgconn
        ramp = np.clip((dist - lo) / (hi - lo), 0, 1) * 255
        alpha[rim] = ramp[rim]
        # remove the light halo: shave one pixel of the soft rim, then paint every remaining edge pixel with the colour
        # of the nearest solid pixel (the backdrop colour bleeds into anti-aliased edges otherwise)
        solid = alpha >= 250
        solid = ndimage.binary_erosion(solid, iterations=1) if solid.sum() > 0 else solid
        idx = ndimage.distance_transform_edt(~solid, return_distances=False, return_indices=True)
        fill = arr[idx[0], idx[1], :3]
        edge = (alpha > 0) & ~solid
        arr[edge, :3] = fill[edge]
        alpha[edge] = np.minimum(alpha[edge], 255)
        alpha[(alpha > 0) & (alpha < 128) & ~solid] = 0     # drop the faintest fringe outright
        arr[:, :, 3] = alpha.astype(np.uint8)
        return Image.fromarray(arr)
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            dist = ((r - bg[0]) ** 2 + (g - bg[1]) ** 2 + (b - bg[2]) ** 2) ** 0.5
            al = 0 if dist <= lo else 255 if dist >= hi else int(255 * (dist - lo) / (hi - lo))
            px[x, y] = (r, g, b, al)
    return im


def trim(im, pad_frac=0.06):
    bbox = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    if not bbox:
        return im
    pad = int(max(bbox[2] - bbox[0], bbox[3] - bbox[1]) * pad_frac)
    return im.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                    min(im.width, bbox[2] + pad), min(im.height, bbox[3] + pad)))


def clean_image(src, dst_clean, dst_icon):
    save_pair(trim(key_image(src)), dst_clean, dst_icon)


def split_columns(im, n):
    """Find the n objects of a left-to-right sheet. Returns (list of (x0, x1), note)."""
    a = im.getchannel("A").point(lambda v: 255 if v > 8 else 0)
    w, h = im.size
    col = [a.crop((x, 0, x + 1, h)).getbbox() is not None for x in range(w)]
    runs, x = [], 0
    while x < w:
        if col[x]:
            x0 = x
            while x < w and col[x]:
                x += 1
            runs.append([x0, x])
        else:
            x += 1
    gap = max(2, int(w * 0.015))
    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] < gap:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    merged = [r for r in merged if r[1] - r[0] >= max(3, int(w * 0.02))]
    if len(merged) == n:
        return [tuple(r) for r in merged], ""
    if len(merged) > n:
        keep = sorted(sorted(merged, key=lambda r: r[0] - r[1])[:n])
        return [tuple(r) for r in keep], f"found {len(merged)} blobs for {n} stages; kept the {n} widest (check them)"
    # objects touch or overlap: cut at the emptiest columns near where each boundary should be
    lo = min(r[0] for r in merged) if merged else 0
    hi = max(r[1] for r in merged) if merged else w
    occ = [sum(1 for y in range(0, h, 2) if a.getpixel((x, y)) > 8) for x in range(w)]
    sm = [sum(occ[max(0, x - 4):x + 5]) / 9.0 for x in range(w)]
    step = (hi - lo) / n
    # the n-1 deepest valleys of the occupancy profile, at least half a step apart
    cand = sorted((x for x in range(lo + int(0.3 * step), hi - int(0.3 * step))
                   if sm[x] <= min(sm[max(0, x - 12):x + 13])), key=lambda x: sm[x])
    picked = []
    for x in cand:
        if all(abs(x - q) >= 0.5 * step for q in picked):
            picked.append(x)
        if len(picked) == n - 1:
            break
    if len(picked) < n - 1:
        picked = [int(lo + k * step) for k in range(1, n)]
    cuts = [lo] + sorted(picked)
    cuts.append(hi)
    why = f"found {len(merged)} separate blobs for {n} stages (they touch/overlap); cut at the emptiest columns (check them)"
    return [(cuts[k], cuts[k + 1]) for k in range(n)], why


def drop_specks(part, frac=0.04):
    """Remove fragments of a neighbouring stage cut off by the split: small connected pieces."""
    try:
        import numpy as np
        from scipy import ndimage
    except ImportError:
        return part
    arr = np.array(part)
    lab, n = ndimage.label(arr[:, :, 3] > 8)
    if n < 2:
        return part
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    keep = [i + 1 for i, sz in enumerate(sizes) if sz >= frac * sizes.max()]
    mask = np.isin(lab, keep)
    arr[~mask, 3] = 0
    from PIL import Image
    return Image.fromarray(arr)


def clean_sheet(e, src, out_dir):
    im = key_image(src)
    defs = e["stage_defs"]
    cols, note = split_columns(im, len(defs))
    pieces = []
    for (x0, x1), sd in zip(cols, defs):
        part = drop_specks(im.crop((x0, 0, x1, im.height)))
        bb = part.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
        if bb:
            part = part.crop(bb)
        pieces.append((sd, part))
    # one shared scale: every stage keeps the size it had on the sheet, bottom-centre on a common canvas
    W, H = max(p.width for _, p in pieces), max(p.height for _, p in pieces)
    from PIL import Image
    outs = []
    for sd, part in pieces:
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        canvas.paste(part, ((W - part.width) // 2, H - part.height), part)
        c = os.path.join(out_dir, sd["item_id"] + ".png")
        ic = os.path.join(out_dir, sd["item_id"] + "_icon.png")
        save_pair(canvas, c, ic)
        outs.append(os.path.relpath(c, BASE).replace("\\", "/"))
    return outs, note


def save_pair(im, dst_clean, dst_icon):
    from PIL import Image
    im.save(dst_clean)
    # 128x128 icon: fit into 104px, centred (icon standard: >=12px margin)
    icon = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    fit = im.copy()
    fit.thumbnail((104, 104), Image.LANCZOS)
    icon.paste(fit, ((128 - fit.width) // 2, (128 - fit.height) // 2), fit)
    icon.save(dst_icon)


def unify_group(paths):
    """Stages of one group share a canvas (bottom-centre anchored) so their relative size survives."""
    from PIL import Image
    ims = [Image.open(c).convert("RGBA") for c, _ in paths]
    W, H = max(i.width for i in ims), max(i.height for i in ims)
    for (c, ic), im in zip(paths, ims):
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        canvas.paste(im, ((W - im.width) // 2, H - im.height), im)
        save_pair(canvas, c, ic)


def cmd_clean(a):
    led = load_ledger()
    d = batch_dir(a.batch)
    out_dir = os.path.join(d, "clean")
    os.makedirs(out_dir, exist_ok=True)
    n = 0
    for tag, e in led["tags"].items():
        if e["batch"] != a.batch or e.get("status") not in ("ingested", "cleaned") or not e.get("raw"):
            continue
        if e["status"] == "cleaned" and not a.redo:
            continue
        src = os.path.join(BASE, e["raw"])
        if e.get("group"):
            outs, note = clean_sheet(e, src, out_dir)
            e.update({"status": "cleaned", "clean_items": outs})
            print(f"[clean] {tag} {e['item_id']}: {len(outs)} stages" + (f"  WARNING: {note}" if note else ""))
        else:
            dst = os.path.join(out_dir, e["item_id"] + ".png")
            ico = os.path.join(out_dir, e["item_id"] + "_icon.png")
            clean_image(src, dst, ico)
            e.update({"status": "cleaned", "clean": os.path.relpath(dst, BASE).replace("\\", "/"),
                      "icon": os.path.relpath(ico, BASE).replace("\\", "/")})
            print(f"[clean] {tag} {e['item_id']}")
        n += 1
    save_ledger(led)
    print(f"{n} cleaned -> {out_dir}  (check them, then feed the *.png to Meshy image-to-3D)")


def cmd_status(a):
    led = load_ledger()
    rows = [(t, e) for t, e in led["tags"].items() if not a.batch or e["batch"] == a.batch]
    if not rows:
        print("nothing tracked")
        return
    for t, e in sorted(rows, key=lambda r: (r[1]["batch"], r[1]["item_id"])):
        gi = f"  [sheet of {e['stages']}]" if e.get("group") else ""
        print(f"{e['batch']:<14} {t}  {e['status']:<9} {e['item_id']}{gi}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen"); g.add_argument("--batch", required=True); g.add_argument("--file")
    g.add_argument("--item", action="append"); g.add_argument("--redo", action="store_true")
    g.add_argument("--group", help="'id | name | shared description [| category]'; add stages with --stage")
    g.add_argument("--stage", action="append", help="'suffix | name | description [| height%]' (repeat, in order)")
    i = sub.add_parser("ingest"); i.add_argument("--batch", required=True); i.add_argument("--dir", required=True)
    i.add_argument("--assign", action="append", help="FILE=TAG for pictures whose file name has no tag")
    c = sub.add_parser("clean"); c.add_argument("--batch", required=True); c.add_argument("--redo", action="store_true")
    s = sub.add_parser("status"); s.add_argument("--batch")
    a = ap.parse_args()
    {"gen": cmd_gen, "ingest": cmd_ingest, "clean": cmd_clean, "status": cmd_status}[a.cmd](a)


if __name__ == "__main__":
    main()
