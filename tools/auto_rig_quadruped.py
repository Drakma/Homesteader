"""
Rigs a static quadruped GLB in headless Blender with NO manual fitting: builds a skeleton from the mesh itself (named like the Animal Animator
Horse profile), computes weights, bakes Animal Animator walk / trot / run / idle / eat clips and exports a rigged GLB.

    blender --background --python tools/auto_rig_quadruped.py -- <in.glb> <out.glb> [leg_top_frac] [--blend <debug.blend>]

The model must stand on z = 0, face -Y (what tools/finish_animal_model.py produces). leg_top_frac is where the legs meet the body, as a fraction
of the model height (horse / cow 0.58, goat / sheep 0.5, pig / dog 0.42).
"""
import math
import sys

import addon_utils
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
src, dst = argv[0], argv[1]
leg_top = float(argv[2]) if len(argv) > 2 and not argv[2].startswith('--') else 0.58
blend_out = argv[argv.index('--blend') + 1] if '--blend' in argv else None
run_id = argv[argv.index('--run') + 1] if '--run' in argv else 'gallop'       # which library gait becomes the Run clip (trot | gallop)

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable('bl_ext.blender_org.animal_animator', default_set=False)
bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
body = [o for o in sc.objects if o.type == 'MESH'][0]
for o in list(sc.objects):
    if o.type not in ('MESH',):
        bpy.data.objects.remove(o, do_unlink=True)
body.parent = None
bpy.context.view_layer.update()
mw = body.matrix_world
P = [mw @ v.co for v in body.data.vertices]
xs, ys, zs = [p.x for p in P], [p.y for p in P], [p.z for p in P]
x0, x1, y0, y1, z0, z1 = min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)
H, L, Wd = z1 - z0, y1 - y0, x1 - x0
cx = (x0 + x1) / 2


def slab_center(ya, yb, zmin):
    """Vertical middle of the upper body between two y values."""
    sel = [p for p in P if ya <= p.y <= yb and p.z >= zmin and abs(p.x - cx) < 0.25 * Wd]
    if not sel:
        return (z0 + z1) / 2
    return (min(p.z for p in sel) + max(p.z for p in sel)) / 2


# ---- feet: the four clusters of the lowest vertices
low = [p for p in P if p.z < z0 + 0.08 * H]
ymid = (y0 + y1) / 2


def cluster(sign, front):
    sel = [p for p in low if (p.x - cx) * sign > 0.0 and ((p.y < ymid) == front)]
    if not sel:
        return Vector((cx + sign * 0.15 * Wd, y0 + (0.25 if front else 0.78) * L, z0))
    return Vector((sum(p.x for p in sel) / len(sel), sum(p.y for p in sel) / len(sel), z0))


feet = {('L', True): cluster(+1, True), ('R', True): cluster(-1, True), ('L', False): cluster(+1, False), ('R', False): cluster(-1, False)}
# Blender: +X is the character's left when it faces -Y

# ---- spine / neck / head from the upper body
back_z = slab_center(y0 + 0.40 * L, y0 + 0.75 * L, z0 + 0.45 * H)
hip = Vector((cx, y0 + 0.74 * L, slab_center(y0 + 0.64 * L, y0 + 0.84 * L, z0 + 0.4 * H)))
shoulder_pt = Vector((cx, y0 + 0.33 * L, slab_center(y0 + 0.26 * L, y0 + 0.40 * L, z0 + 0.4 * H)))
head_front = min(P, key=lambda p: p.y if p.z > z0 + 0.5 * H else 1e9)
head_top = max(P, key=lambda p: p.z)
neck_base = Vector((cx, y0 + 0.24 * L, slab_center(y0 + 0.2 * L, y0 + 0.28 * L, z0 + 0.45 * H)))
head_base = Vector((cx, min(neck_base.y - 0.04 * L, y0 + 0.14 * L), (neck_base.z + head_top.z) / 2))
head_tip = Vector((cx, head_front.y + 0.01 * L, head_front.z))
tail_base = Vector((cx, y1 - 0.06 * L, hip.z + 0.03 * H))
tail_tip = Vector((cx, y1 + 0.05 * L, hip.z - 0.30 * H))


def lerp(a, b, t):
    return a + (b - a) * t


# ---- build the armature
arm_data = bpy.data.armatures.new('Rig')
arm = bpy.data.objects.new('Rig', arm_data)
sc.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones


def bone(name, head, tail, parent=None, connect=False):
    b = eb.new(name)
    b.head, b.tail = Vector(head), Vector(tail)
    if (b.tail - b.head).length < 1e-4:
        b.tail = b.head + Vector((0, 0, 0.01))
    if parent:
        b.parent = eb[parent]
        b.use_connect = connect
    return b


# spine: hips -> 5 segments to the shoulders, neck 4, head, tail 5
spine_pts = [lerp(hip, shoulder_pt, i / 5) for i in range(6)]
bone('spine.001', hip + Vector((0, 0.04 * L, 0)), spine_pts[1])
for i in range(2, 6):
    bone('spine.%03d' % i, spine_pts[i - 1], spine_pts[i], 'spine.%03d' % (i - 1), True)
neck_pts = [lerp(shoulder_pt, neck_base, 0.5), neck_base, lerp(neck_base, head_base, 0.5), head_base]
bone('neck.001', spine_pts[5], neck_pts[0], 'spine.005', True)
bone('neck.002', neck_pts[0], neck_pts[1], 'neck.001', True)
bone('neck.003', neck_pts[1], neck_pts[2], 'neck.002', True)
bone('neck.004', neck_pts[2], neck_pts[3], 'neck.003', True)
bone('head', neck_pts[3], head_tip, 'neck.004', True)
tp = [lerp(tail_base, tail_tip, i / 5) for i in range(6)]
bone('tail.001', tp[0], tp[1], 'spine.001')
for i in range(2, 6):
    bone('tail.%03d' % i, tp[i - 1], tp[i], 'tail.%03d' % (i - 1), True)


def leg(side, front):
    foot = feet[(side, front)]
    top_z = z0 + leg_top * H
    top = Vector((foot.x, (shoulder_pt.y + 0.02 * L) if front else (hip.y + 0.02 * L), top_z))
    mid_z = z0 + (0.58 if front else 0.50) * leg_top * H
    # knee of the foreleg sits straight below, the hock of the hind leg is behind the line
    knee = Vector((foot.x, lerp(top.y, foot.y, 0.5) + (0 if front else 0.05 * L), mid_z))
    low_z = z0 + 0.16 * leg_top * H
    fet = Vector((foot.x, foot.y + (0 if front else 0.01 * L), low_z))
    hoof = Vector((foot.x, foot.y - 0.03 * L, z0))
    attach = 'spine.005' if front else 'spine.001'
    if front:
        n = ('upper_arm.' + side, 'forearm.' + side, 'forefoot.' + side, 'f_hoof.' + side)
    else:
        n = ('thigh.' + side, 'lower_leg.' + side, 'hind_foot.' + side, 'r_hoof.' + side)
        bone('pelvis.' + side, hip, top, 'spine.001')
        attach = 'pelvis.' + side
    bone(n[0], top, knee, attach)
    bone(n[1], knee, fet, n[0], True)
    bone(n[2], fet, hoof, n[1], True)
    bone(n[3], hoof, hoof + Vector((0, -0.04 * L, 0)), n[2], True)


for s in 'LR':
    leg(s, True)
    leg(s, False)
bone('jaw', head_tip, head_tip + Vector((0, 0, -0.03 * H)), 'head')
bpy.ops.object.mode_set(mode='OBJECT')

# ---- skin
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
mesh = body.data
nv = len(mesh.vertices)
names = {vg.index: vg.name for vg in body.vertex_groups}
W = [dict((g.group, g.weight) for g in v.groups) for v in mesh.vertices]
empty = [i for i in range(nv) if not W[i]]
print('INFO bone heat left', len(empty), 'of', nv, 'vertices without weights')
# own weights (bone heat fails on these meshes): inverse distance to the nearest few bone segments. The legs' distance counts sideways
# 2.5x as much, so a chest or belly vertex between the legs does not follow either leg.
LEG = ('upper_arm', 'forearm', 'forefoot', 'f_hoof', 'thigh', 'lower_leg', 'hind_foot', 'r_hoof')
segs = [(b.name, arm.matrix_world @ b.head_local, arm.matrix_world @ b.tail_local, b.name.split('.')[0] in LEG or b.name.startswith('pelvis'))
        for b in arm.data.bones if b.name in body.vertex_groups]
for i in range(nv):
    p = mw @ mesh.vertices[i].co
    ds = []
    for n, a, b, is_leg in segs:
        ab = b - a
        t = max(0.0, min(1.0, (p - a).dot(ab) / max(1e-9, ab.length_squared)))
        c = a + ab * t
        dx = (p.x - c.x) * (2.5 if is_leg else 1.0)
        ds.append((math.sqrt(dx * dx + (p.y - c.y) ** 2 + (p.z - c.z) ** 2), n))
    ds.sort()
    ws = {body.vertex_groups[n].index: 1.0 / (d + 0.02 * H) ** 3 for d, n in ds[:4]}
    tot = sum(ws.values())
    W[i] = {g: w / tot for g, w in ws.items()}
# smooth over the WELDED mesh: vertices that share a position (UV / normal splits) are one node, so they always get identical weights
# (different weights on the two sides of a seam is what rips the surface open)
pos = {}
for v in mesh.vertices:
    pos.setdefault((round(v.co.x, 4), round(v.co.y, 4), round(v.co.z, 4)), []).append(v.index)
gid = [0] * nv
members = list(pos.values())
for k, grp in enumerate(members):
    for i in grp:
        gid[i] = k
ng = len(members)
nb = [set() for _ in range(ng)]
for e in mesh.edges:
    a_, b_ = gid[e.vertices[0]], gid[e.vertices[1]]
    if a_ != b_:
        nb[a_].add(b_)
        nb[b_].add(a_)
GW = [W[grp[0]] for grp in members]
for _ in range(4):
    new = []
    for k in range(ng):
        if not nb[k]:
            new.append(GW[k])
            continue
        acc = {}
        for j in nb[k]:
            for g, w in GW[j].items():
                acc[g] = acc.get(g, 0.0) + w / len(nb[k])
        cur = GW[k]
        new.append({g: 0.5 * cur.get(g, 0.0) + 0.5 * acc.get(g, 0.0) for g in set(cur) | set(acc)})
    GW = new
W = [GW[gid[i]] for i in range(nv)]
for vg in body.vertex_groups:
    vg.remove(list(range(nv)))
for i in range(nv):
    top = sorted(W[i].items(), key=lambda kv: -kv[1])[:4]
    top = [(g, w) for g, w in top if w > 0.02] or top[:1]
    tot = sum(w for _, w in top) or 1.0
    for g, w in top:
        body.vertex_groups[g].add([i], w / tot, 'REPLACE')

# ---- animations from Animal Animator (Horse profile, bones named to match)
from bl_ext.blender_org.animal_animator.core import profiles
sc.animal_animator.target = arm
sc.animal_animator.profile = 'HORSE'
mapping = profiles.default_mapping('HORSE', arm)
profiles.store_mapping(arm, 'HORSE', mapping)
profiles.sync_collection(arm, mapping)
bpy.ops.aa.refresh_anims()
CLIPS = {'walk': 'Walk', 'idle_breathe': 'Idle', 'eat_ground': 'Eating'}
if run_id == 'trot':
    CLIPS['trot'] = 'Run'
else:
    CLIPS['trot'] = 'Trot'
    CLIPS['gallop'] = 'Run'
# playback speed / stride intensity per clip, so the walk and the run cover ground at the game's speeds (no foot skating)
TUNE = {'walk': (1.65, 1.3), 'trot': (1.5, 1.0), 'gallop': (1.5, 1.95), 'idle_breathe': (1.0, 1.0), 'eat_ground': (1.0, 1.0)}
if run_id == 'trot':
    TUNE['trot'] = (1.6, 1.8)       # the Run clip of a slower animal: a long, quick trot
# tighter gallop: the hind feet land almost together, then the front feet almost together
from bl_ext.blender_org.animal_animator.core import library
gal = library.anim_by_id(['quad_core', 'horse'], 'gallop')
for foot, ph in (('H_FOOT.L', 0.0), ('H_FOOT.R', 0.05), ('F_FOOT.L', 0.5), ('F_FOOT.R', 0.55)):
    gal['gait']['feet'][foot]['phase'] = ph
# a horse's back stays nearly straight in the gallop (the library's spine flex is a dog / cat bend)
for ch in gal['gait']['channels']:
    if ch['pose'] == 'SPINE_FLEX':
        ch['amp'] = 0.25
gal['follow']['SPINE'] = 0
# the hock folds FORWARD (the hoof comes up toward the belly), the opposite of the library's knee-style fold
poses = library.poses(['quad_core', 'horse'])
for pid_, lo, ft in (('H_STEP_LIFT', 16, -30), ('H_STEP_REACH', 3, 10), ('H_STEP_PUSH', 2, -22), ('H_STEP_STANCE', 0, 0)):
    sl = poses[pid_]['slots']
    sl['H_LEG_LOWER.L']['fwd'], sl['H_FOOT.L']['fwd'] = lo, ft
for aid, (spd, inten) in [(k, v) for k, v in TUNE.items() if k in CLIPS]:
    for it in sc.aa_anims:
        it.selected = it.anim_id == aid
    sc.animal_animator.speed, sc.animal_animator.intensity = spd, inten
    bpy.ops.aa.build_anims()
if blend_out:
    bpy.ops.wm.save_as_mainfile(filepath=blend_out)


def trim_to_cycle(act, expect):
    """Animal Animator pads a looping action past its cycle (the extra frames are what showed as a hitch). Finds the frame where the pose
    comes back to the first one and limits the action's range to it."""
    arm.animation_data_create()
    arm.animation_data.action = act
    sc.frame_set(int(act.frame_range[0]))
    p0 = {b.name: b.rotation_quaternion.copy() for b in arm.pose.bones}
    best, bf = 1e9, expect
    for f in range(max(2, expect - 3), expect + 4):
        sc.frame_set(int(act.frame_range[0]) + f)
        d = max(math.degrees(b.rotation_quaternion.rotation_difference(p0[b.name]).angle) for b in arm.pose.bones)
        if d < best:
            best, bf = d, f
    act.use_frame_range = True
    act.frame_start = 0
    act.frame_end = bf
    print('INFO cycle', act.name, bf, 'frames, closing difference', round(best, 1), 'degrees')


keep = {}
for a in list(bpy.data.actions):
    key = a.name.split('_', 2)[-1] if a.name.startswith('A_') else a.name
    key = key[len(arm.name):].lstrip('_') if key.startswith(arm.name) else key
    for aid, clip in CLIPS.items():
        if a.name.endswith('_' + aid):
            a.name = clip
            keep[clip] = a
    if a.name not in CLIPS.values():
        bpy.data.actions.remove(a)
arm.animation_data_clear()
for o in sc.objects:
    if o.animation_data:
        o.animation_data_clear()
for aid in [k for k in ('walk', 'trot', 'gallop') if k in CLIPS]:
    spd = TUNE[aid][0]
    fr = next(a for a in (bpy.data.actions) if a.name == CLIPS[aid])
    trim_to_cycle(fr, int(round(next(i.frames for i in sc.aa_anims if i.anim_id == aid) / spd)))
# native ground speed of Walk and Run: how far a hind hoof travels backward per cycle (stance), over the cycle's time
native = {}
for clip in ('Walk', 'Run'):
    act = keep[clip]
    arm.animation_data.action = act
    n = int(act.frame_end)
    ys = []
    for f in range(n + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        ys.append((arm.matrix_world @ arm.pose.bones['r_hoof.L'].head).y)
    native[clip] = round(sum(max(0.0, ys[i + 1] - ys[i]) for i in range(n)) / (n / 30.0), 2)
print('NATIVE', native)
arm.animation_data_create()
arm.animation_data.action = None
for clip, a in keep.items():
    a.use_fake_user = True
    tr = arm.animation_data.nla_tracks.new()
    tr.name = clip
    tr.strips.new(clip, int(a.frame_range[0]), a)
for img in bpy.data.images:
    w_, h_ = img.size
    if max(w_, h_) > 1024:
        img.scale(max(1, w_ // 2), max(1, h_ // 2))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', use_selection=False, export_yup=True, export_animations=True,
                          export_animation_mode='ACTIONS', export_image_format='JPEG', export_jpeg_quality=85)
print('INFO rigged', dst, 'bones', len(arm.data.bones), 'clips', sorted(keep), 'tris', sum(len(p.vertices) - 2 for p in mesh.polygons))
