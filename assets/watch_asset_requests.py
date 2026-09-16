#!/usr/bin/env python3
"""
watch_asset_requests.py
Polls assets/_asset_requests/batches/ and prints one notification per new
finalized batch it finds. Meant to be run in the background with a live
output monitor (e.g. Claude Code's Monitor tool) so a Claude session gets
notified as soon as someone hits "Finalize" on the asset kit's Request
Asset queue.

Individual requests land in pending/ as soon as they're submitted but are
NOT reported here - Creative Claw charges per generation call, so a Claude
session should not act on them one at a time as they trickle in. Only once
the user explicitly finalizes (grouping N pending requests into one batch,
see /api/finalize-asset-requests in server.py) does this script say
anything, and it reports the whole batch at once so all of that batch's
icons can be generated together as a single contact-sheet image instead of
N separate paid calls.

This script never moves files itself and never acts on requests - a Claude
session decides what to do (read the batch, propose a plan + total cost,
wait for approval, generate, then move each request file into
in_progress/ and finally done/ once finished).
"""

import os
import sys
import time
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REQUESTS_DIR = os.path.join(BASE_DIR, "_asset_requests")
BATCHES_DIR = os.path.join(REQUESTS_DIR, "batches")
PENDING_DIR = os.path.join(REQUESTS_DIR, "pending")
IN_PROGRESS_DIR = os.path.join(REQUESTS_DIR, "in_progress")
DONE_DIR = os.path.join(REQUESTS_DIR, "done")
HEARTBEAT_PATH = os.path.join(REQUESTS_DIR, "watcher_heartbeat.json")

POLL_SECONDS = 4

# Printed with every batch notification so ANY Claude session that picks
# this up - not just the one that built this feature - knows the required
# pipeline, even with zero prior conversational context.
REQUIRED_PIPELINE = (
    "PIPELINE REQUIRED for a finalized batch (100% FREE PIPELINE - $0 COST, UNITY 6 TARGET): "
    "(1) ENGINE TARGET: Unity 6 (6000.6.0f1) - 1 Unit = 1 Meter, Y-Up, +Z-Forward (Left-handed). "
    "(2) STRICT ZERO-CREDIT POLICY: DO NOT USE PAID SERVICES (No Creative Claw, No Meshy.ai). "
    "All tools in assets/free_generator.py are 100% FREE ($0 cost). No user spending approval is needed. "
    "(3) 2D ICON GENERATION: Generate individual 2D icons using free_generator.generate_icon_flux() "
    "(or FLUX.1 [schnell] via gradio_client 'black-forest-labs/FLUX.1-schnell' / Pollinations.ai / Google AI Studio). "
    "Follow HUD/ITEM_ICON_STYLE_GUIDE.md: 3D low-poly faceted style, solid neutral background, isometric 3/4 front view. "
    "DIRECTION IS NOT OPTIONAL: Directional items (animals, vehicles, tools) MUST face toward the LEFT of the frame. "
    "(4) ICON STANDARDIZATION: Run each icon through assets/regen_icons.py standardize_icon_image() "
    "(or free_generator.standardize_icon()). This enforces 128x128 32-bit RGBA, <= 104px max dimension, >= 12px margin, "
    "100% perimeter alpha = 0, no borders or drop shadows. "
    "(5) 3D MODEL GENERATION: Feed the standardized icon to Tencent Hunyuan3D-2.0 via free_generator.generate_3d_hunyuan() "
    "(or gradio_client 'tencent/Hunyuan3D-2' on Hugging Face Spaces). Exports low-poly textured GLB/OBJ with target_face_num=8000. "
    "If the item has NO_MODEL=true or is icon-only, skip 3D generation. "
    "(6) BLENDER & UNITY EXPORT: Scale model to metric (1 Unit = 1 Meter), bottom-aligned pivot (Zmin=0) for structures/crops "
    "or centered for tools. Run free_generator.convert_glb_to_unity_fbx(glb_path, fbx_path) with path_mode='COPY' and embed_textures=True. "
    "(7) REPORT PROGRESS: Call POST /api/update-asset-request with status='in_progress' and clear 'step' strings "
    "(e.g. 'Generating 2D icon via FLUX (Free)', 'Standardizing icon (128x128 RGBA)', 'Generating 3D mesh via Hunyuan3D-2 (Free)'). "
    "The UI polls every 2s while in progress. "
    "(8) MARK DONE & UPDATE CATALOG: Call POST /api/update-asset-request with status='done', item_id=<the real created asset id>, "
    "and credits_used={'creative_claw': 0, 'meshy': 0}. Then run python update_catalog_readme.py to synchronize the master index. "
    "See assets/FREE_PIPELINE_GUIDE.md and HUD/FREE_PIPELINE_GUIDE.md for complete code snippets and documentation."
)

# A batch can also contain items that aren't "create a new asset" requests at
# all - queued via the modal's Request Rigging / Regenerate Model buttons, or
# the batch-bar's bulk Request Rigging button. These show up with an
# ACTION=... target=category/item_id marker in the item list above. They
# skip steps (1)-(3) of REQUIRED_PIPELINE entirely (no icon needed, nothing
# to standardize - the asset already exists).
ACTION_ITEM_PIPELINE = (
    "FOR ANY ITEM MARKED ACTION=rig, ACTION=regenerate_model, or ACTION=regenerate_icon above, it already "
    "has a folder (target=category/item_id) - no new item is being created, act directly on the existing "
    "asset. ACTION=rig -> rig it in Blender (Mixamo Addon for humanoids, Animal Animator or standard quadruped armature for animals); skip the icon pipeline. "
    "ACTION=regenerate_model -> re-run Tencent Hunyuan3D-2.0 via free_generator.generate_3d_hunyuan() using the item's EXISTING standardized icon (assets/<target>/<id>/<id>.png) as "
    "the reference image ($0 cost), then convert to Unity metric FBX and overwrite the existing model file(s) - do not touch the icon; skip icon generation. "
    "ACTION=regenerate_icon -> run free FLUX.1 [schnell] via free_generator.generate_icon_flux() "
    "(128x128 3D low-poly, flood-fill crop, standardize, mandatory left-facing-direction rule per HUD/ITEM_ICON_STYLE_GUIDE.md) "
    "using the item's existing name/description/category as the prompt basis - then overwrite ONLY "
    "assets/<target>/<id>/<id>.png - do not touch the 3D model or regenerate it. If the item carries a PROMPT='...' marker (user-typed free text from the "
    "Request Icon dialog's Prompt field), that is EXPLICIT direction on what to change (e.g. 'make it darker, "
    "add rust') - honor it as the primary instruction, layered on top of (not replacing) the item's existing "
    "name/description as context. If the item also carries a REFERENCE=category/id marker (see "
    "REFERENCE_ITEM_PIPELINE below), use it as a style anchor for the new icon exactly as with a new-asset "
    "request. In every case, report step-by-step progress via /api/update-asset-request ($0 cost), and finish with status='done' + item_id=<target_item_id>. "
    "A request with also_rig=true (marked ALSO_RIG=true above) is a normal new-asset creation request that "
    "additionally needs rigging (in Blender) called on it AFTER the model is created and reported "
    "done - rig it as a clearly separate step, still reported via /api/update-asset-request. "
    "RIG_TYPE (human / bipedal_animal / quadruped / vehicle / bird / other) tells you what's being rigged and "
    "which skeleton/animation set to build. "
    "STANDING RULE, NO EXCEPTIONS: rig EVERY RIG_TYPE in Blender (Mixamo Addon for humanoids, Animal Animator for quadrupeds/creatures). "
    "Blender rigging is 100% free ($0 credits) and integrates natively with Unity Mecanim. Import the existing model (assets/<target>/"
    "<target_item_id>/*.fbx or .glb), build/apply an appropriate skeleton for that body plan, and export back with path_mode='COPY' and embed_textures=True."
)

# An item marked REFERENCE=category/id above came with an explicit "match
# style to this existing asset" pick from the Request New Asset dialog's
# Reference Asset field.
REFERENCE_ITEM_PIPELINE = (
    "FOR ANY ITEM MARKED REFERENCE=category/id above, the user wants the new asset to visually match an "
    "EXISTING one - open assets/<category>/<id>/<id>.png and use it as a style anchor: match its color "
    "palette, proportions/scale, level of detail, and overall look when writing the FLUX prompt for "
    "the new item (describe the reference's style in words, e.g. 'same weathered wood tone and low-poly "
    "density as the reference'). "
    "After ANY reference-matched generation, open the result and compare it against the reference side-by-side "
    "before shipping - check colors, trim/material choices, and proportions specifically, not just overall silhouette."
)


def get_live_request_status(request_id):
    """Looks up a request's CURRENT status by scanning pending/in_progress/
    done directly, rather than trusting the batch file's own snapshot (which
    is frozen at the moment it was finalized - every item shows 'queued'
    there forever, even long after it's actually done). Returns None if the
    request file can't be found at all (e.g. deleted from the queue)."""
    for folder in (PENDING_DIR, IN_PROGRESS_DIR, DONE_DIR):
        path = os.path.join(folder, f"{request_id}.json")
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f).get("status")
            except Exception:
                return "gone"
    return "gone"  # sentinel: no live file anywhere for this request id


def batch_is_fully_done(batch):
    """True if every item in the batch is settled - either its live request
    file says status='done', or the file no longer exists at all anywhere
    (pending/in_progress/done). The latter matters because deleting a
    request from the queue - individually or via "delete all" - is a
    supported, intentional action (see /api/delete-asset-request), and it
    happens AFTER completion just as often as it clears out abandoned
    ones; a missing file must never be treated as "still stuck", or every
    watcher restart re-reports and re-processes every batch whose requests
    were ever cleared from the queue, regardless of whether the real work
    was already done and the assets already exist on disk. Only a request
    whose file still exists with a non-done status (queued/pending/
    in_progress) counts as genuinely unfinished. An empty item list counts
    as done (there was nothing to process)."""
    items = batch.get("items", [])
    if not items:
        return True
    return all(get_live_request_status(it.get("id")) in ("done", "gone") for it in items)


def write_heartbeat():
    """Lets server.py report a genuinely live 'Monitor' status in the asset
    kit's status bar - it just checks how fresh this timestamp is, rather
    than trusting a self-reported value."""
    try:
        with open(HEARTBEAT_PATH, "w", encoding="utf-8") as f:
            json.dump({"ts": time.time()}, f)
    except Exception:
        pass


def main():
    os.makedirs(BATCHES_DIR, exist_ok=True)
    os.makedirs(PENDING_DIR, exist_ok=True)
    os.makedirs(IN_PROGRESS_DIR, exist_ok=True)
    os.makedirs(DONE_DIR, exist_ok=True)

    # A batch file that already existed before this run started is only
    # "seen" (skipped) if it's actually fully done - otherwise a restart
    # (watcher crash, session drop, manual stop) silently swallows any
    # batch that was finalized while nothing was listening, with no way to
    # "resend" it short of editing files by hand. Un-seen ones fall through
    # to the normal new-file path below and get reported on the first loop.
    all_batch_files = set(f for f in os.listdir(BATCHES_DIR) if f.endswith(".json"))
    seen = set()
    stuck_count = 0
    for fname in all_batch_files:
        try:
            with open(os.path.join(BATCHES_DIR, fname), "r", encoding="utf-8") as f:
                batch = json.load(f)
            if batch_is_fully_done(batch):
                seen.add(fname)
            else:
                stuck_count += 1
        except Exception:
            seen.add(fname)  # unparseable - don't get stuck retrying it forever

    write_heartbeat()
    if stuck_count:
        print(f"Found {stuck_count} previously-finalized batch(es) not fully done yet (e.g. this watcher wasn't running when they were being processed) - reporting them now.", flush=True)
    print(f"Watching {BATCHES_DIR} for finalized asset-request batches (polling every {POLL_SECONDS}s)...", flush=True)

    while True:
        try:
            current = set(f for f in os.listdir(BATCHES_DIR) if f.endswith(".json"))
        except FileNotFoundError:
            current = set()

        new_files = sorted(current - seen)
        for fname in new_files:
            path = os.path.join(BATCHES_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    batch = json.load(f)
                items = batch.get("items", [])
                item_lines = "\n".join(
                    f"  - id={it.get('id')} name={it.get('name')!r} category={it.get('category')} "
                    f"description={it.get('description')!r}"
                    + (f" ACTION={it.get('action')} target={it.get('target_category')}/{it.get('target_item_id')}" if it.get("action") else "")
                    + (f" RIG_TYPE={it.get('rig_type')}" if it.get("action") == "rig" else "")
                    + (f" ALSO_RIG=true RIG_TYPE={it.get('rig_type')}" if it.get("also_rig") else "")
                    + (f" EXTRA_ANIMATIONS={','.join(it.get('extra_animations'))}" if it.get("extra_animations") else "")
                    + (" NO_MODEL=true" if it.get("no_model") else "")
                    + (f" PROMPT={it.get('prompt')!r}" if it.get("prompt") else "")
                    + (f" REFERENCE={it.get('reference_category')}/{it.get('reference_item_id')}" if it.get("reference_item_id") else "")
                    for it in items
                )
                has_action_items = any(it.get("action") or it.get("also_rig") for it in items)
                has_reference_items = any(it.get("reference_item_id") for it in items)
                print(
                    f"ASSET_REQUEST_BATCH_READY batch_id={batch.get('batch_id')} count={len(items)}\n"
                    f"{item_lines}\n"
                    f"{REQUIRED_PIPELINE}"
                    + (f"\n{ACTION_ITEM_PIPELINE}" if has_action_items else "")
                    + (f"\n{REFERENCE_ITEM_PIPELINE}" if has_reference_items else ""),
                    flush=True
                )
            except Exception as e:
                print(f"ASSET_REQUEST_BATCH_READY (failed to parse {fname}): {e}", flush=True)

        seen = current
        write_heartbeat()
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
