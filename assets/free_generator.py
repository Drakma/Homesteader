#!/usr/bin/env python3
"""
free_generator.py
100% FREE Asset Generation Pipeline for Homesteader (Unity Target):
- 2D Icons: FLUX.1 [schnell] via Hugging Face Space (or Pollinations.ai fallback) -> $0 cost (replaces CreativeClaw)
- Icon Standardization: regen_icons.py outside-in flood fill -> 128x128 32-bit RGBA, 12px margin, 0 outer perimeter alpha
- 3D Models: Tencent Hunyuan3D-2.0 via Hugging Face Space -> $0 cost (replaces Meshy.ai)
- Engine: Unity (1 Unit = 1 Meter, Y-Up, +Z-Forward, Mecanim Humanoid / Generic)
- Rigging: Mixamo Blender Addon (Humanoid) & Blender Armature (Quadruped / Vehicle / Bird)
"""

import os
import sys
import time
import json
import urllib.request
import urllib.parse
from PIL import Image

try:
    from gradio_client import Client, handle_file
except ImportError:
    Client = None
    handle_file = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

import regen_icons

FLUX_SPACE = "black-forest-labs/FLUX.1-schnell"
HUNYUAN_SPACE = "tencent/Hunyuan3D-2.1"


def _load_env_file(path):
    """Minimal KEY=VALUE .env parser (no python-dotenv dependency needed for
    one file). Ignores blank lines and #-comments; does not override a
    variable that's already set in the real environment."""
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_env_file(os.path.join(BASE_DIR, ".env"))

HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    raise RuntimeError(
        "HF_TOKEN not set. Add it to assets/.env (HF_TOKEN=hf_...) or export it as an "
        "environment variable before importing free_generator."
    )


def generate_icon_flux(prompt, output_path, width=1024, height=1024, steps=4):
    """
    Generates a high-quality 2D concept render using FLUX.1 [schnell] on Hugging Face Spaces ($0 cost).
    Falls back to Pollinations.ai (Flux) if the Hugging Face Space is busy or unreachable.
    """
    print(f"[FREE 2D] Generating icon with FLUX.1 [schnell]...")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Try Hugging Face FLUX.1 Space first
    if Client is not None:
        try:
            client = Client(FLUX_SPACE, token=HF_TOKEN)
            result = client.predict(
                prompt=prompt,
                seed=0,
                randomize_seed=True,
                width=width,
                height=height,
                num_inference_steps=steps,
                api_name="/infer"
            )
            # result is (filepath, seed)
            img_path = result[0] if isinstance(result, (list, tuple)) else result
            if isinstance(img_path, dict) and "path" in img_path:
                img_path = img_path["path"]
            
            if img_path and os.path.exists(img_path):
                img = Image.open(img_path)
                img.save(output_path, "PNG")
                print(f"[FREE 2D] FLUX.1 generation succeeded: {output_path}")
                return True
        except Exception as e:
            print(f"[FREE 2D] Hugging Face FLUX.1 error ({e}), falling back to Pollinations.ai...")

    # Fallback to Pollinations.ai (Free Flux routing, no auth needed)
    try:
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true&seed={int(time.time())}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Homesteader/1.0)"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            with open(output_path, "wb") as f:
                f.write(data)
        print(f"[FREE 2D] Pollinations generation succeeded: {output_path}")
        return True
    except Exception as e:
        print(f"[FREE 2D] Pollinations generation error: {e}")
        return False


def standardize_icon(raw_image_path, target_icon_path):
    """
    Applies the Homesteader Icon Standards:
    - Outside-in perimeter flood fill (handles solid magenta #FF00FF or dark slate #2b3442)
    - 128x128 px 32-bit RGBA
    - <= 104px max dimension (>= 12px clean margin on all borders)
    - 100% outer perimeter alpha = 0 (no borders, no frames)
    """
    print(f"[STANDARDIZE] Processing icon via outside-in flood fill...")
    ok, msg = regen_icons.standardize_icon_image(raw_image_path, target_icon_path)
    if ok:
        print(f"[STANDARDIZE] Success: {msg} -> {target_icon_path}")
    else:
        print(f"[STANDARDIZE] Warning: {msg}")
    return ok


def generate_3d_hunyuan(image_path, output_dir, item_id, caption="", steps=30, octree_res=256):
    """
    Generates a TEXTURED 3D mesh using Tencent's Hunyuan3D-2 Hugging Face Space ($0 cost).

    Uses /generation_all, not /shape_generation - shape_generation only produces bare
    untextured geometry (confirmed empirically 2026-09-16: the resulting GLB had zero
    images/textures/materials). /generation_all runs the same shape step plus texture
    baking and returns two files - a textured GLB and a simplified/untextured one - so
    this picks whichever of the two file outputs is actually the larger, textured one.
    """
    print(f"[FREE 3D] Generating textured 3D mesh via Hunyuan3D-2 on Hugging Face...")
    if Client is None or handle_file is None:
        raise RuntimeError("gradio_client is required. Run: pip install gradio_client")

    os.makedirs(output_dir, exist_ok=True)
    client = Client("tencent/Hunyuan3D-2", token=HF_TOKEN)

    print(f"  Sending image to Hunyuan3D-2 /generation_all endpoint (shape + texture)...")
    res = client.predict(
        caption=caption or item_id.replace("_", " "),
        image=handle_file(image_path),
        mv_image_front=None,
        mv_image_back=None,
        mv_image_left=None,
        mv_image_right=None,
        steps=steps,
        guidance_scale=5.0,
        seed=1234,
        octree_resolution=octree_res,
        check_box_rembg=True,
        num_chunks=8000,
        randomize_seed=True,
        api_name="/generation_all"
    )

    # res = [File (textured/white glb), File (second variant), Output html, Mesh Stats, Seed]
    # Pick the textured one by file size - the untextured variant is reliably much smaller
    # since it carries no image data.
    candidates = []
    for file_val in (res[0], res[1]):
        raw_path = file_val.get("value") or file_val.get("path") if isinstance(file_val, dict) else file_val
        if raw_path and os.path.exists(raw_path):
            candidates.append(raw_path)

    if not candidates:
        raise RuntimeError(f"Could not locate output 3D file from Hunyuan3D: {res}")

    best_path = max(candidates, key=os.path.getsize)
    dest_glb = os.path.join(output_dir, f"{item_id}.glb")
    import shutil
    shutil.copyfile(best_path, dest_glb)
    print(f"[FREE 3D] Successfully deployed textured GLB: {dest_glb} ({os.path.getsize(dest_glb):,} bytes)")
    return dest_glb


def convert_glb_to_unity_fbx(glb_path, fbx_path, target_dimensions_m=None, ground_pivot=True, round_to_whole_meters=False):
    """
    Converts a GLB/OBJ to FBX formatted for Unity:
    - 1 Unit = 1 Meter
    - Decimates to ~8000 faces for game-ready performance
    - Rescaled to target_dimensions_m (dict with width/depth/height, matching the
      item's own catalog manifest) if given - Hunyuan3D-2 generates meshes at its own
      normalized size with zero awareness of the item's real-world dimensions_m, so
      without this every model comes out some arbitrary (usually far too small) size.
      Confirmed empirically 2026-09-16: an ungenerated 9x12x5.2m garage came out as
      1.56x1.96x1.09m with no rescale step at all.
    - Ground-aligned pivot (Z_min = 0) when ground_pivot=True (structures/crops/props),
      centered bounding-box pivot when False (handheld tools). Previously this always
      centered on the full bounding box regardless of the flag - a real bug, since a
      ground-aligned object needs its pivot at the base, not floating at half-height.
    - Y-Up, +Z-Forward
    - Embeds textures directly
    Uses Blender in background mode.
    """
    print(f"[CONVERT] Converting {glb_path} to Unity FBX: {fbx_path}...")
    blender_exe = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
    if not os.path.exists(blender_exe):
        blender_exe = "blender"

    dims = target_dimensions_m or {}
    target_w = dims.get("width")
    target_d = dims.get("depth")
    target_h = dims.get("height")
    if round_to_whole_meters and target_w and target_d and target_h:
        # Structures will eventually snap to a grid - keep their real-world
        # footprint/height at whole meters rather than fractional values.
        target_w = max(1, round(target_w))
        target_d = max(1, round(target_d))
        target_h = max(1, round(target_h))

    rescale_snippet = ""
    if target_w and target_d and target_h:
        rescale_snippet = f"""
    dims = obj.dimensions
    if dims.x > 0.0001 and dims.y > 0.0001 and dims.z > 0.0001:
        obj.scale.x *= {target_w} / dims.x
        obj.scale.y *= {target_d} / dims.y
        obj.scale.z *= {target_h} / dims.z
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
"""

    # Ground-aligned pivot: move the 3D cursor to (center_x, center_y, min_z) of the
    # mesh in world space and snap the origin there, then re-zero the object's
    # location so the origin sits exactly at world (0,0,0). center='BOUNDS' alone
    # (the old behavior) always puts the pivot at the vertical MIDPOINT, which is
    # wrong for anything meant to sit flush on the ground.
    pivot_snippet = """
    verts_world = [obj.matrix_world @ v.co for v in obj.data.vertices]
    if verts_world:
        min_z = min(v.z for v in verts_world)
        max_z = max(v.z for v in verts_world)
        center_x = sum(v.x for v in verts_world) / len(verts_world)
        center_y = sum(v.y for v in verts_world) / len(verts_world)
        pivot_z = min_z if """ + str(ground_pivot) + """ else (min_z + max_z) / 2.0
        bpy.context.scene.cursor.location = (center_x, center_y, pivot_z)
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        obj.location = (0.0, 0.0, 0.0)
"""

    py_cmd = f"""
import bpy, os
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r'{glb_path}')

mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
if mesh_objs:
    obj = mesh_objs[0]
    bpy.context.view_layer.objects.active = obj

    # Decimate if faces > 8000
    if len(obj.data.polygons) > 8000:
        mod = obj.modifiers.new(name='Decimate', type='DECIMATE')
        mod.ratio = min(1.0, 8000.0 / len(obj.data.polygons))
        bpy.ops.object.modifier_apply(modifier=mod.name)
{rescale_snippet}
{pivot_snippet}

bpy.ops.export_scene.fbx(
    filepath=r'{fbx_path}',
    use_selection=False,
    axis_forward='-Z',
    axis_up='Y',
    apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_ALL',
    bake_anim=False,
    path_mode='COPY',
    embed_textures=True
)
"""
    import subprocess
    cmd = [blender_exe, "-b", "--python-expr", py_cmd]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(fbx_path):
        print(f"[CONVERT] FBX export successful: {fbx_path} ({os.path.getsize(fbx_path):,} bytes)")
        return True
    else:
        print(f"[CONVERT] Blender conversion warning: {res.stderr}")
        return False


if __name__ == "__main__":
    print("Homesteader 100% Free Asset Generator ready.")
    print("Usage: import free_generator as fg")
    print("  fg.generate_icon_flux(prompt, output_path)")
    print("  fg.standardize_icon(raw_path, target_path)")
    print("  fg.generate_3d_hunyuan(icon_path, output_dir, item_id)")
    print("  fg.convert_glb_to_unity_fbx(glb_path, fbx_path)")

