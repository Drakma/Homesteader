"""
Authors the CHAINSAW clip `Saw_Sideways` for the farmer ped (docs/CHAINSAW.md): a real chainsaw is not chopped, it is swept: the saw is held in both hands at waist height with
the bar level, and the whole saw moves cleanly from side to side across the front of the body while the player leans into it. Hands are IK-posed on moving targets, baked to the
bones, and exported with the mesh like the other work clips (peds_farmer_winter_work_anims.glb): the new file is peds_farmer_winter_saw_anims.glb (loaded by HudSceneBootstrap).

    blender --background --python tools/make_saw_clip.py [-- preview]
A `preview` argument renders a few frames to assets/_scratch/saw/ instead of exporting.
"""
import math
import os
import sys

import bpy
from mathutils import Euler, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, 'assets', 'peds', 'peds_farmer_winter')
RIGGED = os.path.join(DIR, 'peds_farmer_winter_rigged.glb')
OUT = os.path.join(DIR, 'peds_farmer_winter_saw_anims.glb')
PREVIEW = 'preview' in sys.argv
CLIP = 'Saw_Sideways'
FPS = 24
LOOP = 30                      # frames a full left-right-left sweep takes (1.25 s)
SWEEP = 0.25                   # m each side of centre
FRONT = -1.0                   # the character faces -y in Blender


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = FPS
    bpy.ops.import_scene.gltf(filepath=RIGGED)
    arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    bpy.context.view_layer.objects.active = arm
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)

    def empty(name, loc):
        e = bpy.data.objects.new(name, None)
        bpy.context.scene.collection.objects.link(e)
        e.location = loc
        return e

    # the saw is held at the right hip: rear handle in the right hand, front handle in the left; they stay a fixed distance apart as the saw sweeps across
    rh = empty('RH', (-0.10, -0.40, 0.98))
    lh = empty('LH', (0.12, -0.62, 0.98))
    rp = empty('RP', (-0.65, 0.25, 1.05))
    lp = empty('LP', (0.65, 0.05, 1.05))
    bpy.ops.object.mode_set(mode='POSE')
    for bone, tgt, pole in (('RightHand', rh, rp), ('LeftHand', lh, lp)):
        pb = arm.pose.bones[bone]
        c = pb.constraints.new('IK')
        c.target, c.pole_target, c.chain_count, c.use_tail = tgt, pole, 3, True
        c.pole_angle = 0.0
    bpy.ops.object.mode_set(mode='OBJECT')

    # the sweep: left and right along x, a little forward push at each end of the stroke
    for f in range(1, LOOP + 2):
        ph = (f - 1) / LOOP * 2 * math.pi
        dx = SWEEP * math.sin(ph)
        push = 0.03 * (0.5 - 0.5 * math.cos(2 * ph))
        for e, base in ((rh, (-0.10, -0.40, 0.98)), (lh, (0.12, -0.62, 0.98))):
            e.location = (base[0] + dx, base[1] + FRONT * -1 * 0 - push, base[2])
            e.keyframe_insert('location', frame=f)
        for e, base in ((rp, (-0.65, 0.25, 1.05)), (lp, (0.65, 0.05, 1.05))):
            e.location = (base[0] + dx * 0.5, base[1], base[2])
            e.keyframe_insert('location', frame=f)

    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, LOOP + 1
    if PREVIEW:
        render_preview(arm)
        return
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.nla.bake(frame_start=1, frame_end=LOOP + 1, only_selected=False, visual_keying=True, clear_constraints=True, use_current_action=False, bake_types={'POSE'})
    act = arm.animation_data.action
    act.name = CLIP
    for o in (rh, lh, rp, lp):
        bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_animations=True, export_animation_mode='ACTIONS', export_nla_strips=False, export_yup=True)
    print('wrote', OUT, 'clip', CLIP)


def render_preview(arm):
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in dir(bpy.types) else scene.render.engine
    scene.render.resolution_x, scene.render.resolution_y = 480, 480
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    scene.collection.objects.link(cam)
    scene.camera = cam
    light = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
    scene.collection.objects.link(light)
    light.rotation_euler = (0.8, 0.2, 0.6)
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 2.4
    views = {'top': ((0, 0, 4), (0, 0, 0)), 'front': ((0, -4, 1.0), (math.pi / 2, 0, 0))}
    os.makedirs(os.path.join(ROOT, 'assets', '_scratch', 'saw'), exist_ok=True)
    for name, (loc, rot) in views.items():
        cam.location, cam.rotation_euler = loc, rot
        for f in (1, 8, 16, 23):
            scene.frame_set(f)
            scene.render.filepath = os.path.join(ROOT, 'assets', '_scratch', 'saw', '%s_%02d.png' % (name, f))
            bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    main()
