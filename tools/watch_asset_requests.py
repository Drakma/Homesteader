#!/usr/bin/env python3
"""
watch_asset_requests.py
Polls assets/_asset_requests/batches/ and prints one notification per new
finalized batch it finds. Meant to be run in the background with a live
output monitor (e.g. Claude Code's Monitor tool) so a Claude session gets
notified as soon as someone hits "Finalize" on the asset kit's Request
Asset queue.

Individual requests land in pending/ as soon as they're submitted but are
NOT reported here - EVERY request now charges Meshy credits per generation
call, so a Claude session should not act on requests
one at a time as they trickle in. Only once the user explicitly finalizes
(grouping N pending requests into one batch, see
/api/finalize-asset-requests in server.py) does this script say anything,
and it reports the whole batch at once so the total credit cost of the
whole batch can be presented and approved before anything is generated.

This script never moves files itself and never acts on requests - a Claude
session decides what to do (read the batch, propose a plan + total cost,
wait for approval, generate, then move each request file into
in_progress/ and finally done/ once finished).
"""

import os
import sys
import time
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
BASE_DIR = os.path.join(PROJECT_DIR, "assets")
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
    "PIPELINE REQUIRED for a finalized batch (ONLY PIPELINE: REFERENCE IMAGE + MESHY IMAGE-TO-3D - PAID, UNITY 6 TARGET): "
    "(1) ENGINE TARGET: Unity 6 (6000.6.0f1) - 1 Unit = 1 Meter, Y-Up, +Z-Forward (Left-handed). "
    "(2) THERE IS NO FREE PIPELINE ANY MORE. EVERYTHING COSTS MONEY. Hunyuan3D-2.0, FLUX.1 [schnell], "
    "free_generator.py and Creative Claw concept images are ALL RETIRED - do not call them, do not offer them. "
    "Plain Meshy TEXT-to-3D is also no longer the default route. The generation route is: (a) generate a "
    "reference image with the gemini_generate MCP tool (batch multiple items into one contact sheet where "
    "possible), (b) crop to one image per item, (c) feed each crop to Meshy IMAGE-TO-3D "
    "(tools/meshy_client.py create_image_to_3d()) with ai_model='meshy-t2', model_type='smart-topology', "
    "should_texture=True - a single task that produces the model AND its texture. "
    "(3) THE USER'S PROMPT IS THE INPUT: the request carries a PROMPT='...' marker written by the user. Fold that "
    "prompt into the Gemini reference-image prompt AS-IS - it is explicit direction on what to make, do NOT "
    "rewrite, replace, or paraphrase it. Then APPEND the standing technical rules below so it generates properly. "
    "MODEL_TYPE='SMART-TOPOLOGY' (ai_model='meshy-t2') IS MANDATORY, ALWAYS, NO EXCEPTIONS on every image-to-3D "
    "call. Never 'lowpoly' or 'standard' (this reverses the old lowpoly-only rule). "
    "(3b) SCALE + GROUND: after downloading the GLB, scale it to a realistic real-world height and drop its "
    "pivot to the ground (Y_min=0) via a headless Blender script (import -> uniform-scale under an empty parent "
    "to the target height -> recenter XY and drop to Y=0 -> transform_apply -> re-export GLB) before rendering "
    "the icon. Match realistic sizes already used elsewhere in the same category. "
    "(3c) KNOWN OPEN ISSUE: this method can produce fragmented/jagged-looking shading on curved organic "
    "surfaces (e.g. an animal's face) specifically in Unity/glTFast at runtime, not visible in the raw GLB, its "
    "normals, or Blender's own render. Root cause unconfirmed (leading theory: texture compression across "
    "meshy-t2's small UV islands). Flag this to the user after generating rather than assuming it's fixed. "
    "(4) 2D CONCEPT/ICON GENERATION: the Gemini reference image is NOT the icon and is never shipped directly - "
    "the icon is always rendered FROM the finished 3D model in the next step. "
    "MODERN DAY ONLY: every request is a MODERN-DAY item (current-era design, materials and manufacturing) unless the request explicitly says otherwise - put the word 'modern' in the Meshy prompt (e.g. 'a modern walking plow'), and never produce antique, medieval, or period-styled versions. "
    "Follow docs/ITEM_ICON_STYLE_GUIDE.md: 3D low-poly faceted style, solid neutral background, isometric 3/4 front view. "
    "EXTERNAL VIEW ONLY: Always render an external view of the entire complete object/building from the outside (outer facade, "
    "outer walls, roof) with NO internal structure, no cutaways, no indoor camera perspective, and no internal rooms visible "
    "(unless the external view can naturally see inside through open windows or open doors). "
    "TOOL ICON POSE (reference: assets/tools/tool_shovel_trenching/tool_shovel_trenching.png): a long-handled tool is drawn on a DIAGONAL (about 35-45 degrees) with the HANDLE at the upper-right and the WORKING END (blade / share / head) at the lower-left. State this in the prompt (e.g. 'tilted diagonally, handle at top right, blade at bottom left'). When rendering an icon from a model with tools/render_icon_from_model.py, the model's own front axis is arbitrary, so ALWAYS open the result: if the working end is not lower-left, re-run with the other face_left value (true/false) and keep the one that matches. "
    "DIRECTION IS NOT OPTIONAL: Directional items (animals, vehicles, tools) MUST face toward the LEFT of the frame. "
    "(5) ICON FROM THE MODEL (this is the 2D step - it comes AFTER the 3D step): run "
    "tools/render_icon_from_model.py <model_path> assets/<category>/<item_id>/<item_id>.png to pose the textured model "
    "in Blender (isometric 3/4 front view, top-left key lighting) and render the icon from it. "
    "(6) ICON STANDARDIZATION: Run each rendered icon through assets/regen_icons.py standardize_icon_image(). "
    "This enforces 128x128 32-bit RGBA, <= 104px max dimension, >= 12px margin, "
    "100% perimeter alpha = 0, no borders or drop shadows. "
    "(7) BLENDER & UNITY EXPORT: Scale model to metric (1 Unit = 1 Meter), bottom-aligned pivot (Zmin=0) for structures/crops "
    "or centered for tools. Export GLB with embedded textures (path_mode='COPY', embed_textures=True). "
    "(8) REPORT PROGRESS: Call POST /api/update-asset-request with status='in_progress' and clear 'step' strings "
    "(e.g. 'Generating 3D model via Meshy text-to-3D (lowpoly)', 'Downloading GLB + texture', "
    "'Posing model in Blender to render icon', 'Standardizing icon (128x128 RGBA)'). "
    "The UI polls every 2s while in progress. "
    "(9) MARK DONE & UPDATE CATALOG: Call POST /api/update-asset-request with status='done', item_id=<the real created asset id>, "
    "and credits_used={'creative_claw': 0, 'meshy': <credits actually spent>}. Then run python update_catalog_readme.py to synchronize the master index. "
    "(10) SCHEMA VALIDATION: if the request has a non-empty 'schema' field (set from the Request Asset / Request Growth Group "
    "dialog's Schema dropdown), the assembled item's properties/category_fields MUST include every field required by "
    "assets/_schemas/<schema>.schema.json (plus the always-required assets/_schemas/_base*.schema.json fields) - run "
    "tools/validate_schema.py <schema> after writing the manifest and fix any [FAIL] before marking the request done. "
    "This exists because a real batch (the Large Metal Garage growth group, 2026-09-16) shipped with 10 missing required "
    "fields per stage that nobody caught until an explicit review - don't repeat that. "
    "See docs/MESHY_PIPELINE_GUIDE.md for complete code snippets and documentation."
)

# A batch can also contain items that aren't "create a new asset" requests at
# all - queued via the modal's Request Rigging / Regenerate Model buttons, or
# the batch-bar's bulk Request Rigging button. These show up with an
# ACTION=... target=category/item_id marker in the item list above. They
# skip the generation/icon-render steps of REQUIRED_PIPELINE entirely (the
# asset already exists on disk).
ACTION_ITEM_PIPELINE = (
    "FOR ANY ITEM MARKED ACTION=rig, ACTION=regenerate_model, or ACTION=regenerate_icon above, it already "
    "has a folder (target=category/item_id) - no new item is being created, act directly on the existing "
    "asset. ACTION=rig -> rig it in Blender (Mixamo Addon for humanoids, Animal Animator or standard quadruped armature for animals); skip the icon pipeline. "
    "ACTION=regenerate_model -> re-run the reference-image + Meshy IMAGE-TO-3D pipeline "
    "(tools/meshy_client.py create_image_to_3d() with ai_model='meshy-t2', model_type='smart-topology') using "
    "the item's existing name/description (plus any PROMPT='...' marker) as the reference-image prompt basis, "
    "then overwrite the existing model file(s) - do not touch the icon unless the user "
    "asked for it. This COSTS MONEY: confirm the credit cost with the user before spending. "
    "ACTION=regenerate_icon -> do NOT call any 2D generator (there is no 2D generator any more). The icon is "
    "always rendered FROM the 3D model: run tools/render_icon_from_model.py <existing_model_path> "
    "assets/<target>/<id>/<id>.png (isometric 3/4 front view, top-left key lighting), then standardize via "
    "assets/regen_icons.py standardize_icon_image() (128x128 RGBA, <= 104px max, >= 12px margin, perimeter "
    "alpha=0), and overwrite ONLY assets/<target>/<id>/<id>.png - do not regenerate the 3D model. "
    "This is FREE (local Blender render, no credits). "
    "If the item carries a PROMPT='...' marker (user-typed free text from the "
    "Request Icon dialog's Prompt field), that is EXPLICIT direction - for regenerate_icon, if the request "
    "requires geometry/texture changes it cannot get from an existing model, regenerate the model through "
    "Meshy first (with cost confirmation) and then render the icon from the new model. If the item also carries a REFERENCE=category/id marker (see "
    "REFERENCE_ITEM_PIPELINE below), use it as a style anchor exactly as with a new-asset "
    "request. In every case, report step-by-step progress via /api/update-asset-request, and finish with status='done' + item_id=<target_item_id>. "
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
    "palette, proportions/scale, level of detail, and overall look when writing the Meshy prompt for "
    "the new item (describe the reference's style in words, e.g. 'same weathered wood tone and low-poly "
    "density as the reference'). "
    "After ANY reference-matched generation, open the result and compare it against the reference side-by-side "
    "before shipping - check colors, trim/material choices, and proportions specifically, not just overall silhouette."
)

# The ONLY generation pipeline. There is no free alternative, so this text is
# always printed with a batch - it is not conditional on a PIPELINE=paid marker
# any more (the marker only survives as a legacy field in old request files).
PAID_ITEM_PIPELINE = (
    "(11) THE ONLY PIPELINE - REFERENCE IMAGE + MESHY IMAGE-TO-3D: (1) take the user's PROMPT='...' text AS-IS, "
    "fold it into a gemini_generate reference-image prompt (batching multiple items into one sheet where "
    "possible), then crop to one image per item - do not rewrite the user's intent; (2) call "
    "tools/meshy_client.py create_image_to_3d(cropped_image_path, ai_model='meshy-t2', "
    "model_type='smart-topology', should_texture=True) - ALWAYS model_type='smart-topology', never "
    "'lowpoly'/'standard'; "
    "(3) this single Meshy task returns the MODEL AND ITS TEXTURE; "
    "(4) download the GLB (GLB is the project's model format); scale it to a realistic real-world height and "
    "ground its pivot (Y_min=0) via a headless Blender script before the icon step; "
    "(5) run tools/render_icon_from_model.py <model_path> assets/<category>/<item_id>/<item_id>.png to pose the "
    "textured model in Blender (isometric 3/4 front view), render with top-left key lighting, and standardize "
    "to 128x128 RGBA. The icon is ALWAYS rendered from the model - never generated as a separate 2D image. "
    "COST CONFIRMATION IS MANDATORY before spending anything: check the current balance "
    "(GET /api/meshy-balance or the meshy_check_balance tool), present the "
    "estimated cost and the resulting balance to the user, and wait for explicit approval before calling any "
    "Meshy generation tool - the user passing a prompt with a request is not the same as approving a specific "
    "spend. After generation, report credits_used in the "
    "POST /api/update-asset-request done payload (e.g. {'creative_claw': 0, 'meshy': 15}) so the status bar "
    "and per-batch cost summary stay accurate."
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
                    + (f" SCHEMA={it.get('schema')}" if it.get("schema") else "")
                    + (f" PIPELINE={it.get('pipeline')}" if it.get("pipeline") else "")
                    for it in items
                )
                has_action_items = any(it.get("action") or it.get("also_rig") for it in items)
                has_reference_items = any(it.get("reference_item_id") for it in items)
                print(
                    f"ASSET_REQUEST_BATCH_READY batch_id={batch.get('batch_id')} count={len(items)}\n"
                    f"{item_lines}\n"
                    f"{REQUIRED_PIPELINE}"
                    + (f"\n{ACTION_ITEM_PIPELINE}" if has_action_items else "")
                    + (f"\n{REFERENCE_ITEM_PIPELINE}" if has_reference_items else "")
                    + f"\n{PAID_ITEM_PIPELINE}",
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
