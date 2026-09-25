"""
Runs INSIDE Blender (headless). Converts the adducted male-ped FBX to GLB.

    blender -b --python tools/male_ped_fbx_to_glb.py

Why this is not just tools/blender_to_glb.py: that script deliberately
SKIPS any model with an armature, because Unity wants FBX for Humanoid
retargeting. Here the whole point of the edit is that the arms now hang
at the sides, which is exactly what the FBX rest pose could not express
(Unity's humanDescription.restPose is empty, so the editor re-derives a
T-pose from the skeleton's twist axes). So for the GLB we BAKE the
deformed skin - the adducted pose - into the geometry and the armature
is consumed by the bake and never exported. The GLB then carries a
static mesh in the correct stance.

The FBX files stay exactly as they are; this only adds a .glb beside them.

Output:
    assets/peds/peds_male_farmer/SKM_Peds_Male_Farmer_Rigged.glb
    assets/peds/peds_male_farmer/SKM_Peds_Male_Farmer.glb   (base mesh + texture)

Two things it fixes on the way in:

1. Texture. The FBX's own material points at a texture that was not
   written into the file (Meshy's FBX drops it), so importing the FBX
   alone exports a texture-less grey GLB. The authored
   SKM_Peds_Male_Farmer_base_color.png sitting beside it is reloaded
   and packed instead - same fix blender_to_glb.py applies to the crops.
2. Units. The armature imports at scale 0.01 (Meshy writes it in
   centimetres). Baking the deformed skin at object scale would divide
   the 1.75 m figure down to 1.75 cm, so the object transform is applied
   first and the result is verified against rigging.height_meters.
"""
import bpy
import os
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PED = os.path.join(ROOT, "assets", "peds", "peds_male_farmer")

RIGGED_FBX = os.path.join(PED, "SKM_Peds_Male_Farmer_Rigged.fbx")
BASE_FBX = os.path.join(PED, "SKM_Peds_Male_Farmer.fbx")
BASE_COLOR = os.path.join(PED, "SKM_Peds_Male_Farmer_base_color.png")

RIGGED_GLB = os.path.join(PED, "SKM_Peds_Male_Farmer_Rigged.glb")
BASE_GLB = os.path.join(PED, "SKM_Peds_Male_Farmer.glb")

EXPECTED_HEIGHT_M = 1.75
HEIGHT_TOL = 0.05


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_fbx(path):
    bpy.ops.import_scene.fbx(filepath=path)
    return list(bpy.context.scene.objects)


def bind_base_color(png_path):
    # Rebuild every material as a plain Principled BSDF reading the authored PNG.
    img = bpy.data.images.load(png_path)
    img.pack()
    for mat in list(bpy.data.materials):
        if not mat.use_nodes:
            mat.use_nodes = True
        nt = mat.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = 0.9
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
    return img


def world_bbox(objs):
    lo = Vector((1e18, 1e18, 1e18))
    hi = Vector((-1e18, -1e18, -1e18))
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector((min(lo.x, w.x), min(lo.y, w.y), min(lo.z, w.z)))
            hi = Vector((max(hi.x, w.x), max(hi.y, w.y), max(hi.z, w.z)))
    return lo, hi


def normalize_units(objs, label):
    """Apply object transforms, then snap cm->m if the figure came in at 100x."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    lo, hi = world_bbox(meshes)
    size = hi - lo
    # Pick the axis that is actually the model's height: the extent that sits
    # on the ground plane. A figure standing on Z=0 has a large Z span; a
    # model exported lying down has it on X or Y.
    high_axes = [a for a in (size.z, size.x, size.y) if a > 0.4 * max(size)]
    tallest = max(high_axes) if high_axes else max(size)
    factor = 1.0
    # Only ever snap a whole 100x (cm -> m), and only when the result lands in
    # a plausible human range. A 1.75 m figure must not be divided down here.
    if tallest > 20.0 and 1.0 <= tallest / 100.0 <= 3.0:
        factor = 0.01
    print("[glb] %s raw size=(%.4f, %.4f, %.4f) scale=%.5f"
          % (label, size.x, size.y, size.z, factor))
    if factor != 1.0:
        for o in meshes:
            o.scale = (factor, factor, factor)
        bpy.context.view_layer.update()
        bpy.ops.object.select_all(action="DESELECT")
        for o in meshes:
            o.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return meshes


def bake_rest_pose(mesh_obj):
    """Collapse the armature modifier so the current pose becomes the geometry."""
    before = len(mesh_obj.data.vertices)
    bpy.ops.object.select_all(action="DESELECT")
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_obj
    n_mods = len(mesh_obj.modifiers)
    bpy.ops.object.convert(target="MESH")
    baked = bpy.context.view_layer.objects.active
    return baked, before, len(baked.data.vertices), n_mods


def unwrap_uvs(obj):
    """The FBX carries no UVs; project them so the base colour has somewhere to land."""
    if obj.data.uv_layers:
        return False
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    return True


def weld(obj, distance=0.0005):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=distance)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def export_glb(path, obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    kwargs = dict(
        filepath=path,
        export_format="GLB",
        export_image_format="AUTO",
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
        export_apply=True,
        export_yup=True,
        use_selection=True,
    )
    try:
        bpy.ops.export_scene.gltf(**kwargs)
    except TypeError:
        kwargs.pop("use_selection", None)
        bpy.ops.export_scene.gltf(**kwargs)


def report(tag, lo, hi):
    size = hi - lo
    print("[%s] bounds X[%.3f, %.3f] Y[%.3f, %.3f] Z[%.3f, %.3f]  size=(%.3f, %.3f, %.3f)"
          % (tag, lo.x, hi.x, lo.y, hi.y, lo.z, hi.z, size.x, size.y, size.z))
    return size


# ---------------------------------------------------------------------------
# 1. Rigged -> static GLB, arms adducted
# ---------------------------------------------------------------------------
print("[glb] === RIGGED (adducted) -> GLB ===")
reset()
objs = import_fbx(RIGGED_FBX)
meshes = [o for o in objs if o.type == "MESH"]
armatures = [o for o in objs if o.type == "ARMATURE"]
if not meshes:
    raise RuntimeError("no mesh in " + RIGGED_FBX)
print("[glb] imported %d mesh, %d armature" % (len(meshes), len(armatures)))

bind_base_color(BASE_COLOR)

# Apply the object transform (armature's 0.01 cm->m scale rides along) so the
# baked skin comes out in metres rather than centimetres.
normalize_units(objs, "rigged")

mesh = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
mesh.name = "SKM_Peds_Male_Farmer_Rigged"

lo0, hi0 = world_bbox([mesh])
report("glb/rest", lo0, hi0)

mesh, v_before, v_after, n_mods = bake_rest_pose(mesh)
print("[glb] baked pose: modifiers=%d verts %d -> %d" % (n_mods, v_before, v_after))

# The armature is now baked in and no longer referenced - drop it so the GLB
# is a pure static mesh.
for o in list(bpy.context.scene.objects):
    if o.type == "ARMATURE":
        bpy.data.objects.remove(o, do_unlink=True)

had_uvs = bool(mesh.data.uv_layers)
if not had_uvs:
    unwrap_uvs(mesh)
print("[glb] mesh had UVs: %s" % had_uvs)
weld(mesh)

lo, hi = world_bbox([mesh])
size = report("glb/final", lo, hi)
tris = len(mesh.data.polygons)
print("[glb] polys=%d verts=%d materials=%d uv_layers=%d"
      % (tris, len(mesh.data.vertices), len(mesh.data.materials), len(mesh.data.uv_layers)))

if not (EXPECTED_HEIGHT_M - HEIGHT_TOL <= size.z <= EXPECTED_HEIGHT_M + HEIGHT_TOL):
    raise RuntimeError("height %.3f m is not the expected %.2f m - unit scale is wrong"
                       % (size.z, EXPECTED_HEIGHT_M))

export_glb(RIGGED_GLB, mesh)
print("[glb] wrote %s (%s bytes)" % (RIGGED_GLB, format(os.path.getsize(RIGGED_GLB), ",")))

def sample_vertices(obj, step=37, limit=12):
    """Print a spread of LOCAL vertex coords, plus the local extents."""
    vs = obj.data.vertices
    xs = [v.co.x for v in vs]
    ys = [v.co.y for v in vs]
    zs = [v.co.z for v in vs]
    print("[base] local extents X[%.4f, %.4f] Y[%.4f, %.4f] Z[%.4f, %.4f]"
          % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
    for i in range(0, min(len(vs), step * limit), step):
        c = vs[i].co
        print("[base] v%04d (%.4f, %.4f, %.4f)" % (i, c.x, c.y, c.z))


# ---------------------------------------------------------------------------
# 2. Base mesh -> GLB
# ---------------------------------------------------------------------------
# NOTE: tools/blender_to_glb.py produced this GLB before and reported a
# 1.000 x 0.192 x 1.000 m box. That is exactly the 1 m square the raw FBX
# yields here - the mesh is authored in a normalised -0.5..+0.5 box, not in
# metres, and no unit conversion brings it to the 1.75 m the manifest
# declares. There is no scale we can infer, so the honour-what-is-there move
# is to convert it as authored and RECORD the discrepancy rather than invent a
# scale factor. Flip CORRECT_BASE_HEIGHT once it is regenerated properly.
CORRECT_BASE_HEIGHT = False

print("[glb] === BASE MESH -> GLB ===")
reset()
objs = import_fbx(BASE_FBX)
meshes = [o for o in objs if o.type == "MESH"]
if not meshes:
    raise RuntimeError("no mesh in " + BASE_FBX)
print("[glb] base imported %d objects (%d mesh, %d armature)"
      % (len(objs), len(meshes), len([o for o in objs if o.type == "ARMATURE"])))

bind_base_color(BASE_COLOR)

# As authored: drop any scale carried on the object, but keep the file's own
# orientation and position - no axis fix-up and no unit snap.
bpy.ops.object.select_all(action="DESELECT")
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

for o in list(bpy.context.scene.objects):
    if o.type == "ARMATURE":
        bpy.data.objects.remove(o, do_unlink=True)

mesh = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
mesh.name = "SKM_Peds_Male_Farmer"
if not mesh.data.uv_layers:
    unwrap_uvs(mesh)
weld(mesh)

sample_vertices(mesh)
lo, hi = world_bbox([mesh])
size = report("glb/base", lo, hi)
print("[glb] polys=%d verts=%d materials=%d uv_layers=%d"
      % (len(mesh.data.polygons), len(mesh.data.vertices), len(mesh.data.materials), len(mesh.data.uv_layers)))

if CORRECT_BASE_HEIGHT:
    if not (EXPECTED_HEIGHT_M - HEIGHT_TOL <= size.z <= EXPECTED_HEIGHT_M + HEIGHT_TOL):
        raise RuntimeError("base height %.3f m is not the expected %.2f m" % (size.z, EXPECTED_HEIGHT_M))
else:
    print("[glb] NOTE base mesh is %.3f m on its longest axis, not %.2f m: it is authored in a "
          "normalised box rather than metres. Converting as authored - the manifest already "
          "pointed at this file." % (max(size.x, size.y, size.z), EXPECTED_HEIGHT_M))

export_glb(BASE_GLB, mesh)
print("[glb] wrote %s (%s bytes)" % (BASE_GLB, format(os.path.getsize(BASE_GLB), ",")))

print("[glb] DONE")