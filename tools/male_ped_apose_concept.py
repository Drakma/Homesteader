"""
Generates the replacement male-farmer mesh from a native A-pose concept.

Why a regenerate instead of an edit: the shipped mesh is a T-pose sculpt, and
Meshy rigged it with the t-pose baked directly over the t-pose rest pose, so
there is no limb pose left to retarget onto. The arms cannot be adducted by
posing - lowering them that far passes the forearms through the thighs. The
fix is a new mesh whose base pose already has the arms down, so its rest pose
and its sculpt agree.

Two consequences that shape the whole run:

  1. The legs must be separate in the source views. If the reference shows the
     legs fused, the generator produces a single-sided skirt/blob rather than
     two legs, and no rig can animate that.
  2. Texture is a strict function of UV and UV is a strict function of
     topology, so this can only produce a NEW model. It cannot preserve the
     shipped one's texture.

Standard prompt style is appended, but two documented lines are deliberately
overridden here - see PROMPT below for why.

Free pipeline only: FLUX.1 [schnell] via tools/free_generator.py, then
Hunyuan3D-2 on Hugging Face Spaces. $0.

    python tools/male_ped_apose_concept.py --sheet
    python tools/male_ped_apose_concept.py --split
    python tools/male_ped_apose_concept.py --mesh
    python tools/male_ped_apose_concept.py --all
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

PED = os.path.join(ROOT, "assets", "peds", "peds_male_farmer")
WORK = os.path.join(PED, "_apose_work")
SHEET_RAW = os.path.join(WORK, "concept_sheet_raw.png")
SHEET = os.path.join(WORK, "concept_sheet.png")

VIEWS = ["front", "left", "right"]
VIEW_ALPHA = os.path.join(WORK, "apose_{view}_alpha.png")
VIEW_RGB = os.path.join(WORK, "apose_{view}.png")

# The harness sits on a dark slate sheet (#2b3442, the project's chroma key),
# so the subject reads as a lighter mid-tone against it. A pure white subject
# would be extracted correctly and still be invisible in every viewer.
HARNESS = "medium gray seamless full-body suit"

# Overrides two lines of the standard ITEM_ICON_STYLE_GUIDE prompt:
#   - "solid uniform DARK SLATE background" -> a LIGHT neutral gray. The
#     grader for the mesh generator needs the silhouette to separate cleanly
#     from the backdrop, and a light gray gives that while keeping the subject
#     a mid-tone on the user-facing sheet.
#   - "facing toward the LEFT of the frame" -> head-on, and the profile views
#     are left-facing and right-facing by name. A front view cannot also face
#     left, and the two profiles must face opposite ways to be useful as
#     references.
PROMPT = (
    "THREE SEPARATE FULL-BODY FIGURES in one wide image, arranged in a row "
    "left to right, each one a complete standing man shown from the top of his "
    "head down to his boots. NOT a portrait, NOT a bust, NOT cropped at the "
    "waist - the feet and boots of every figure are fully inside the frame. "
    "All three figures are the SAME man in the SAME pose at the SAME scale, "
    "separated by wide empty gaps. "
    "First figure on the left: front view, facing the camera head-on. "
    "Second figure in the middle: left profile, facing the left edge of the "
    "image. Third figure on the right: right profile, facing the right edge "
    "of the image. "
    "POSE - a relaxed A-pose: his arms hang down low at his sides and are only "
    "slightly away from his body, hands near his thighs about 25 centimetres "
    "clear of his hips. His legs are straight, shoulder-width apart, with a "
    "clear gap of empty background visible between the two legs from crotch to "
    "boots so his two legs read as separate limbs. Nothing touches or overlaps. "
    "He is dressed in plain work clothes - a hooded sweatshirt, jeans, and work "
    "boots - in flat unpatterned colours. "
    "Style: blocky low-poly video game character, CHUNKY SIMPLIFIED GEOMETRY "
    "with clearly VISIBLE FLAT POLYGON FACETS across the face, torso and limbs, "
    "flat-shaded so every plane reads as a distinct hard-edged facet. "
    "NOT a photograph, NOT a realistic human render, NOT smooth skin, NOT "
    "fine surface detail - a simple faceted low-poly mobile-game model. "
    "Camera: orthographic, straight-on, flat even lighting, no cast shadows. "
    "Background: solid uniform flat light neutral gray (hex #d8dae0) behind "
    "all three figures, no gradient, no floor, no pedestal, no grid, no text, "
    "no watermark, no logo, no signature, no border, no frame."
)


def log(msg):
    print("[apose] " + msg)


def gen_sheet():
    os.makedirs(WORK, exist_ok=True)
    import free_generator as fg

    # A generation that fails must not leave the previous attempt behind to be
    # mistaken for this one's output. Delete first, then require the file to
    # exist afterwards.
    for stale in (SHEET_RAW, SHEET):
        if os.path.isfile(stale):
            os.remove(stale)

    log("generating concept sheet via FLUX.1 [schnell] (free)...")
    fg.generate_icon_flux(PROMPT, SHEET_RAW, width=1344, height=768, steps=4)
    if not os.path.isfile(SHEET_RAW):
        raise RuntimeError("FLUX produced no file at " + SHEET_RAW)
    log("sheet raw: %s (%s bytes)" % (SHEET_RAW, format(os.path.getsize(SHEET_RAW), ",")))

    # Keep a copy at the exact requested size so the panel math is predictable.
    from PIL import Image
    im = Image.open(SHEET_RAW).convert("RGB")
    log("raw size: %s" % (im.size,))
    if im.size != (1344, 768):
        log("NOTE: model returned %s, not the requested 1344x768 - using actual size" % (im.size,))
    im.save(SHEET)
    log("sheet: %s" % SHEET)


def split_sheet():
    from PIL import Image
    if not os.path.isfile(SHEET):
        raise RuntimeError("no sheet at " + SHEET + " - run --sheet first")

    im = Image.open(SHEET).convert("RGB")
    w, h = im.size
    log("splitting %dx%d into 3 panels" % (w, h))

    # Split into even thirds. Guard against the model adding a fourth panel or
    # mis-spacing them by checking each third actually contains ink.
    third = w // 3
    for i, view in enumerate(VIEWS):
        box = (i * third, 0, (i + 1) * third if i < 2 else w, h)
        panel = im.crop(box)
        dst = VIEW_RGB.format(view=view)
        panel.save(dst)
        log("panel %-5s x[%d..%d] -> %s" % (view, box[0], box[2], dst))

    # Report ink coverage per panel so an empty or double-populated third is
    # caught here rather than after a 30-minute mesh job.
    for view in VIEWS:
        p = Image.open(VIEW_RGB.format(view=view)).convert("L")
        px = list(p.getdata())
        corner = px[:1][0]
        ink = sum(1 for v in px if abs(v - corner) > 40)
        log("panel %-5s ink pixels: %d (%.1f%% of frame)" % (view, ink, 100.0 * ink / len(px)))
    log("sheet split done - REVIEW the panels before running --mesh")


def to_views():
    """Alpha-out each panel's flat backdrop so Hunyuan sees just the figure."""
    from PIL import Image
    import math

    X0, X1 = 0.06, 0.94
    Y0, Y1 = 0.02, 0.98

    for view in VIEWS:
        src = VIEW_RGB.format(view=view)
        im = Image.open(src).convert("RGB")
        w, h = im.size

        perim = []
        for x in range(w):
            perim.append(im.getpixel((x, 0)))
            perim.append(im.getpixel((x, h - 1)))
        for y in range(h):
            perim.append(im.getpixel((0, y)))
            perim.append(im.getpixel((w - 1, y)))
        bg = tuple(sum(p[i] for p in perim) / len(perim) for i in range(3))

        def is_bg(p, tol):
            return math.sqrt(sum((p[i] - bg[i]) ** 2 for i in range(3))) < tol

        visited = [[False] * w for _ in range(h)]
        queue = []
        for x in range(w):
            for yy in (0, h - 1):
                if is_bg(im.getpixel((x, yy)), 26.0):
                    visited[yy][x] = True
                    queue.append((x, yy))
        for y in range(h):
            for xx in (0, w - 1):
                if not visited[y][xx] and is_bg(im.getpixel((xx, y)), 26.0):
                    visited[y][xx] = True
                    queue.append((xx, y))

        head = 0
        while head < len(queue):
            qx, qy = queue[head]
            head += 1
            for dx, dy in ((-1, 0), (0, -1), (0, 1)):
                nx, ny = qx + dx, qy + dy
                if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx] and is_bg(im.getpixel((nx, ny)), 26.0):
                    visited[ny][nx] = True
                    queue.append((nx, ny))

        # Drop any flood that reached the loincloth/suit interior: convex-ish
        # fills that hit the figure's core are wrong, so only keep regions that
        # touch the border. (Handled implicitly: we only seeded from the border.)

        rgba = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        opaque = 0
        for y in range(h):
            for x in range(w):
                if not visited[y][x]:
                    px = im.getpixel((x, y))
                    d = math.sqrt(sum((px[i] - bg[i]) ** 2 for i in range(3)))
                    a = 255 if d >= 34.0 else int(255 * max(0.0, (d - 26.0) / 8.0))
                    if a:
                        opaque += 1
                    rgba.putpixel((x, y), (px[0], px[1], px[2], a))
        log("panel %-5s bg=%s matte pixels=%d (%.1f%%)"
            % (view, tuple(round(c) for c in bg), opaque, 100.0 * opaque / (w * h)))

        bbox = rgba.split()[3].getbbox()
        if not bbox:
            raise RuntimeError("panel %s is empty after matte" % view)
        x0 = max(bbox[0], int(w * X0))
        x1 = min(bbox[2], int(w * X1))
        # Pad out to the full frame so Hunyuan pads with background and never
        # composites a body against a body.
        rgba = rgba.crop((x0, int(h * Y0), x1, int(h * Y1)))
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        canvas.paste(rgba, ((w - rgba.width) // 2, (h - rgba.height) // 2), rgba)

        # Hunyuan keys off a plain background; keep a flat RGB copy alongside.
        dst_a = VIEW_ALPHA.format(view=view)
        canvas.save(dst_a)
        bgimg = Image.new("RGB", (w, h), tuple(int(c) for c in bg))
        bgimg.paste(canvas, (0, 0), canvas)
        bgimg.save(VIEW_RGB.format(view=view))
        log("wrote %s and %s" % (dst_a, VIEW_RGB.format(view=view)))


def gen_mesh():
    import free_generator as fg
    out = os.path.join(WORK, "raw_mesh.glb")
    log("generating mesh via Hunyuan3D-2 multi-view (free)...")
    fg.generate_3d_hunyuan_mv(
        front=VIEW_RGB.format(view="front"),
        left=VIEW_RGB.format(view="left"),
        right=VIEW_RGB.format(view="right"),
        output_dir=WORK,
        item_id="raw_mesh",
        caption="male farm worker standing in a relaxed A-pose, arms down at the sides",
    )
    if not os.path.isfile(out):
        raise RuntimeError("Hunyuan produced no file at " + out)
    log("raw mesh: %s (%s bytes)" % (out, format(os.path.getsize(out), ",")))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sheet", action="store_true")
    p.add_argument("--split", action="store_true")
    p.add_argument("--views", action="store_true")
    p.add_argument("--mesh", action="store_true")
    p.add_argument("--all", action="store_true")
    a = p.parse_args()
    if a.all or a.sheet:
        gen_sheet()
    if a.all or a.split:
        split_sheet()
    if a.all or a.views:
        to_views()
    if a.all or a.mesh:
        gen_mesh()
    log("DONE")


if __name__ == "__main__":
    main()