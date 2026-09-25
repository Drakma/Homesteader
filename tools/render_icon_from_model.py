#!/usr/bin/env python3
"""
render_icon_from_model.py
Renders a game-ready 3D model (.glb, .gltf, .fbx, .obj) directly into a standardized
128x128 32-bit RGBA PNG item icon following Homesteader Icon Standards:
- Headless Blender rendering with transparent film background.
- Automatic center-of-bounds target framing.
- Standard isometric 3/4 front view: ~35 deg pitch, 45 deg yaw (directional items face left).
- Warm key lighting (top-left) + cool fill light (bottom-right) + ambient world light.
- Passes output through regen_icons.standardize_icon_image() to guarantee:
  128x128 canvas, <= 104px max dimension, >= 12px margin, 100% perimeter alpha = 0.
"""

import os
import sys
import subprocess
import shutil
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")

if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

import regen_icons

BLENDER_CANDIDATE_PATHS = [
    r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
    "blender"
]


def find_blender_exe():
    for p in BLENDER_CANDIDATE_PATHS:
        if os.path.isfile(p):
            return p
        found = shutil.which(p)
        if found:
            return found
    return None


BLENDER_RENDER_PY = r"""
import bpy
import math
import sys
import os
from mathutils import Vector

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
if len(argv) < 2:
    print("Usage: blender --background --python render.py -- <model_path> <out_png> [face_left]")
    sys.exit(1)

model_path = os.path.abspath(argv[0])
out_png = os.path.abspath(argv[1])
face_left = argv[2].lower() == "true" if len(argv) > 2 else True

# 1. Clean scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# 2. Configure render settings
scene = bpy.context.scene
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'

# Setup ambient environment lighting
world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.4, 0.45, 0.5, 1.0)
    bg.inputs["Strength"].default_value = 0.9

# 3. Import model
ext = os.path.splitext(model_path)[1].lower()
if ext in ['.glb', '.gltf']:
    bpy.ops.import_scene.gltf(filepath=model_path)
elif ext == '.fbx':
    bpy.ops.import_scene.fbx(filepath=model_path)
elif ext == '.obj':
    try:
        bpy.ops.wm.obj_import(filepath=model_path)
    except AttributeError:
        bpy.ops.import_scene.obj(filepath=model_path)
else:
    print(f"Unsupported format: {ext}")
    sys.exit(1)

# 4. Clean material emission & enable clean shading
for mat in bpy.data.materials:
    if getattr(mat, "use_nodes", False):
        for node in mat.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                for inp in node.inputs:
                    if inp.name.startswith('Emission Color') or inp.name == 'Emission':
                        for link in list(inp.links):
                            mat.node_tree.links.remove(link)
                        inp.default_value = (0, 0, 0, 1)
                    elif inp.name == 'Emission Strength':
                        inp.default_value = 0.0

# 5. Gather imported mesh objects
mesh_objs = [o for o in scene.objects if o.type == 'MESH']
if not mesh_objs:
    print("No mesh objects found after import!")
    sys.exit(1)

# Calculate combined bounding box in world space
bbox_corners = []
for o in mesh_objs:
    mat = o.matrix_world
    for corner in o.bound_box:
        bbox_corners.append(mat @ Vector(corner))

min_x = min(c.x for c in bbox_corners)
max_x = max(c.x for c in bbox_corners)
min_y = min(c.y for c in bbox_corners)
max_y = max(c.y for c in bbox_corners)
min_z = min(c.z for c in bbox_corners)
max_z = max(c.z for c in bbox_corners)

center = Vector(((min_x + max_x) * 0.5, (min_y + max_y) * 0.5, (min_z + max_z) * 0.5))
dimensions = Vector((max_x - min_x, max_y - min_y, max_z - min_z))
max_dim = max(dimensions.x, dimensions.y, dimensions.z)
if max_dim <= 0.0001:
    max_dim = 1.0

# 6. Target Anchor for Camera Tracking
target_empty = bpy.data.objects.new("TargetAnchor", None)
target_empty.location = center
scene.collection.objects.link(target_empty)

# 7. Camera Setup (Isometric 3/4 Front View: pitch ~35 deg, yaw ~45 deg)
cam_data = bpy.data.cameras.new(name="RenderCamera")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = max_dim * 1.35
cam_obj = bpy.data.objects.new(name="RenderCamera", object_data=cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

yaw_deg = -45 if face_left else 45
pitch_deg = 35

dist = max_dim * 2.5
cam_obj.location = center + Vector((
    math.sin(math.radians(yaw_deg)) * math.cos(math.radians(pitch_deg)) * dist,
    -math.cos(math.radians(yaw_deg)) * math.cos(math.radians(pitch_deg)) * dist,
    math.sin(math.radians(pitch_deg)) * dist
))

track = cam_obj.constraints.new(type='TRACK_TO')
track.target = target_empty
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'
bpy.context.view_layer.update()

# Extract camera basis vectors in world space
cam_mat = cam_obj.matrix_world
cam_right = cam_mat.to_3x3() @ Vector((1, 0, 0))
cam_up = cam_mat.to_3x3() @ Vector((0, 1, 0))
cam_dir = -(cam_mat.to_3x3() @ Vector((0, 0, 1)))

# 8. Lighting Setup per ITEM_ICON_STYLE_GUIDE.md
# Primary Key Light: Top-left, warm white (~5500K), 45 deg elevation
key_dir = (cam_dir + (-cam_right * 0.9) + (cam_up * 1.2)).normalized()
key_data = bpy.data.lights.new(name="KeyLight", type='SUN')
key_data.energy = 4.2
key_data.color = (1.0, 0.95, 0.88)  # warm white ~5500K
key_obj = bpy.data.objects.new(name="KeyLight", object_data=key_data)
scene.collection.objects.link(key_obj)
key_obj.location = center + key_dir * dist
key_track = key_obj.constraints.new(type='TRACK_TO')
key_track.target = target_empty
key_track.track_axis = 'TRACK_NEGATIVE_Z'
key_track.up_axis = 'UP_Y'

# Secondary Fill Light: Bottom-right, cool neutral white (~6500K), low intensity (25-30%)
fill_dir = (cam_dir + (cam_right * 0.8) + (-cam_up * 0.3)).normalized()
fill_data = bpy.data.lights.new(name="FillLight", type='SUN')
fill_data.energy = 1.2
fill_data.color = (0.85, 0.92, 1.0)  # cool neutral white ~6500K
fill_obj = bpy.data.objects.new(name="FillLight", object_data=fill_data)
scene.collection.objects.link(fill_obj)
fill_obj.location = center + fill_dir * dist
fill_track = fill_obj.constraints.new(type='TRACK_TO')
fill_track.target = target_empty
fill_track.track_axis = 'TRACK_NEGATIVE_Z'
fill_track.up_axis = 'UP_Y'

# 9. Render and save
scene.render.filepath = out_png
bpy.ops.render.render(write_still=True)
print(f"Render complete -> {out_png}")
"""


def render_icon_from_model(model_path: str, output_icon_path: str, face_left: bool = True) -> tuple[bool, str]:
    """
    Renders a 3D model into an icon PNG and runs standardizing flood fill.
    Returns (success: bool, message: str).
    """
    if not os.path.isfile(model_path):
        return False, f"Model file not found: {model_path}"

    blender_exe = find_blender_exe()
    if not blender_exe:
        return False, "Blender executable not found on system."

    os.makedirs(os.path.dirname(os.path.abspath(output_icon_path)), exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        blend_script = os.path.join(tmpdir, "render_script.py")
        raw_png = os.path.join(tmpdir, "raw_render.png")

        with open(blend_script, "w", encoding="utf-8") as f:
            f.write(BLENDER_RENDER_PY)

        cmd = [
            blender_exe,
            "--background",
            "--python", blend_script,
            "--",
            os.path.abspath(model_path),
            raw_png,
            str(face_left)
        ]

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            return False, f"Blender render failed (exit code {e.returncode}):\n{e.stderr or e.stdout}"

        if not os.path.isfile(raw_png):
            return False, "Blender exited cleanly but raw_render.png was not created."

        ok, msg = regen_icons.standardize_icon_image(raw_png, output_icon_path)
        if not ok:
            return False, f"Icon standardization failed: {msg}"

    return True, f"Successfully rendered and standardized icon: {output_icon_path}"


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python render_icon_from_model.py <model_path> <output_icon_path> [face_left:true|false]")
        sys.exit(1)

    mpath = sys.argv[1]
    out_icon = sys.argv[2]
    f_left = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else True

    success, message = render_icon_from_model(mpath, out_icon, face_left=f_left)
    print(message)
    sys.exit(0 if success else 1)

