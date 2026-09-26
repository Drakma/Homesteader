#!/usr/bin/env python
"""Foot-slide (skating) check and fix for walk / run clips in a GLB.

A clip only looks right when the feet it plants move backwards at the same speed the character moves forwards.
This measures the ground speed a clip's feet actually cover ("native speed"), and can lengthen the stride so a
clip's native speed matches the game's movement speed at a natural playback rate.

  python tools/gait_fix.py measure <file.glb> [--anim N]
  python tools/gait_fix.py stretch <file.glb> --target 2.0 [--anim N] [--out out.glb]
  python tools/gait_fix.py stretch <file.glb> --swing 1.45      (run cycles: fixed scale, no search)
        --target  ground speed (m/s) the clip should cover at playback speed 1 (usually the game's walk / run speed
                  divided by the playback rate you are happy with, e.g. 2.0 / 1.15)

Humanoid rigs (Mixamo bone names: Hips, LeftUpLeg, LeftLeg, LeftFoot, LeftToeBase and the Right* twins). For other
rigs pass --hips / --foot-l / --foot-r / --toe / --upleg-l / --upleg-r / --leg-l / --leg-r.

The game side: GlbClipPlayer plays the gait clip at (real ground speed / native speed), so store the measured
native speed in GlbClipPlayer.walkNativeSpeed / runNativeSpeed (player) or in an animal definition's
movement.walk_native_mps / run_native_mps (docs/ANIMAL_AI.md). Always keep the original clip (--out, or the backup this script writes next to the file).
"""
import argparse
import json
import os
import shutil
import struct
import sys

import numpy as np


def load(path):
    d = open(path, 'rb').read()
    l = struct.unpack('<I', d[12:16])[0]
    j = json.loads(d[20:20 + l])
    off = 20 + l
    bl = struct.unpack('<I', d[off:off + 4])[0]
    return d, j, bytearray(d[off + 8:off + 8 + bl]), l, off


def _rng(j, i):
    a = j['accessors'][i]
    v = j['bufferViews'][a['bufferView']]
    n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a['type']]
    return v.get('byteOffset', 0) + a.get('byteOffset', 0), a['count'], n


def read(j, b, i):
    o, c, n = _rng(j, i)
    return np.frombuffer(bytes(b[o:o + c * n * 4]), dtype='<f4').reshape(c, n).astype(float)


def write(j, b, i, arr):
    o, c, n = _rng(j, i)
    b[o:o + c * n * 4] = np.asarray(arr, dtype='<f4').tobytes()


def qmul(a, b):
    x1, y1, z1, w1 = a
    x2, y2, z2, w2 = b
    return np.array([w1*x2 + x1*w2 + y1*z2 - z1*y2, w1*y2 - x1*z2 + y1*w2 + z1*x2,
                     w1*z2 + x1*y2 - y1*x2 + z1*w2, w1*w2 - x1*x2 - y1*y2 - z1*z2])


def qinv(q):
    return np.array([-q[0], -q[1], -q[2], q[3]]) / np.dot(q, q)


def slerp(a, b, t):
    a, b = np.array(a), np.array(b)
    if np.dot(a, b) < 0:
        b = -b
    d = np.clip(np.dot(a, b), -1, 1)
    if d > 0.9995:
        r = a + t * (b - a)
        return r / np.linalg.norm(r)
    th = np.arccos(d)
    return (np.sin((1 - t) * th) * a + np.sin(t * th) * b) / np.sin(th)


def qmean(qs):
    ref = qs[0]
    acc = np.zeros(4)
    for q in qs:
        acc += q if np.dot(q, ref) >= 0 else -q
    return acc / np.linalg.norm(acc)


def quat_mat(q):
    x, y, z, w = q
    return np.array([[1 - 2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def sample(times, vals, t, rot):
    if t <= times[0]:
        return vals[0]
    if t >= times[-1]:
        return vals[-1]
    i = np.searchsorted(times, t) - 1
    u = (t - times[i]) / (times[i + 1] - times[i])
    return slerp(vals[i], vals[i + 1], u) if rot else vals[i] + u * (vals[i + 1] - vals[i])


def measure(j, b, anim, bones):
    """Per-side native ground speed (m/s) of the planted foot, plus foot height stats."""
    nodes = j['nodes']
    parent = {}
    for i, n in enumerate(nodes):
        for c in n.get('children', []):
            parent[c] = i
    idx = {n.get('name'): i for i, n in enumerate(nodes)}
    an = j['animations'][anim]
    chans, T = {}, 0
    for c in an['channels']:
        s = an['samplers'][c['sampler']]
        tm = read(j, b, s['input']).reshape(-1)
        chans[(c['target']['node'], c['target']['path'])] = (tm, read(j, b, s['output']))
        T = max(T, tm[-1])

    def local(i, t):
        n = nodes[i]
        tr = np.array(n.get('translation', [0, 0, 0]), float)
        ro = np.array(n.get('rotation', [0, 0, 0, 1]), float)
        sc = np.array(n.get('scale', [1, 1, 1]), float)
        if (i, 'translation') in chans:
            tr = sample(*chans[(i, 'translation')], t, False)
        if (i, 'rotation') in chans:
            ro = sample(*chans[(i, 'rotation')], t, True)
        if (i, 'scale') in chans:
            sc = sample(*chans[(i, 'scale')], t, False)
        m = np.eye(4)
        m[:3, :3] = quat_mat(ro) * sc
        m[:3, 3] = tr
        return m

    def world(i, t):
        m = local(i, t)
        while i in parent:
            i = parent[i]
            m = local(i, t) @ m
        return m

    ts = np.linspace(0, T, 90, endpoint=False)
    keys = {'hips': bones['hips'], 'l': bones['foot_l'], 'r': bones['foot_r'], 'toe': bones['toe']}
    P = {k: np.array([world(idx[v], t)[:3, 3] for t in ts]) for k, v in keys.items()}
    fwd = P['toe'][0] - P['l'][0]
    fwd[1] = 0
    fwd /= np.linalg.norm(fwd)
    dt = T / len(ts)
    out = {'duration': float(T)}
    for side in ('l', 'r'):
        rel = (P[side] - P['hips']) @ fwd
        y = P[side][:, 1]
        contact = y < (y.min() + 0.25 * (y.max() - y.min()))
        v = -np.gradient(rel, dt)
        out[side] = abs(float(np.median(v[contact])))
        out[side + '_lift'] = float(y.max() - y.min())
    out['native'] = (out['l'] + out['r']) / 2
    return out


def stretch(j, b, anim, bones, kl, kr):
    names = [n.get('name') for n in j['nodes']]
    an = j['animations'][anim]
    rot = {names[c['target']['node']]: an['samplers'][c['sampler']]['output']
           for c in an['channels'] if c['target']['path'] == 'rotation'}
    for k, up, leg, foot in ((kl, bones['upleg_l'], bones['leg_l'], bones['foot_l']),
                             (kr, bones['upleg_r'], bones['leg_r'], bones['foot_r'])):
        qt, ql, qf = read(j, b, rot[up]), read(j, b, rot[leg]), read(j, b, rot[foot])
        m = qmean(list(qt))
        qt2 = np.array([slerp(m, q, k) for q in qt])
        # keep the foot's world orientation: qf' = ql^-1 qt'^-1 qt ql qf
        qf2 = np.array([qmul(qmul(qinv(ql[i]), qinv(qt2[i])), qmul(qmul(qt[i], ql[i]), qf[i])) for i in range(len(qt))])
        qf2 = np.array([q / np.linalg.norm(q) for q in qf2])
        write(j, b, rot[up], qt2)
        write(j, b, rot[foot], qf2)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['measure', 'stretch'])
    ap.add_argument('glb')
    ap.add_argument('--anim', type=int, default=0)
    ap.add_argument('--target', type=float)
    ap.add_argument('--swing', type=float, help="skip the search: scale both legs' swing by this factor (use when planted-foot detection is unreliable, e.g. run cycles with a flight phase)")
    ap.add_argument('--out')
    for k, v in (('hips', 'Hips'), ('foot-l', 'LeftFoot'), ('foot-r', 'RightFoot'), ('toe', 'LeftToeBase'),
                 ('upleg-l', 'LeftUpLeg'), ('upleg-r', 'RightUpLeg'), ('leg-l', 'LeftLeg'), ('leg-r', 'RightLeg')):
        ap.add_argument('--' + k, default=v)
    a = ap.parse_args()
    bones = {'hips': a.hips, 'toe': a.toe}
    bones.update({'foot_l': a.foot_l, 'foot_r': a.foot_r, 'upleg_l': a.upleg_l, 'upleg_r': a.upleg_r,
                  'leg_l': a.leg_l, 'leg_r': a.leg_r})

    d, j, b, l, off = load(a.glb)
    name = j['animations'][a.anim].get('name')
    r = measure(j, b, a.anim, bones)
    print(f"{os.path.basename(a.glb)} clip #{a.anim} '{name}': {r['duration']:.3f}s cycle, native ground speed "
          f"{r['native']:.2f} m/s (left {r['l']:.2f}, right {r['r']:.2f}), foot lift {r['l_lift']:.2f}/{r['r_lift']:.2f} m")
    if a.cmd == 'measure':
        return
    if not a.target and not a.swing:
        sys.exit('--target (or --swing) is required for stretch')

    # find per-side swing scale so each foot's native speed hits the target (bisection; robust to left/right differences)
    def side_k(side):
        lo, hi = 1.0, 2.6
        for _ in range(14):
            mid = (lo + hi) / 2
            jj = json.loads(json.dumps(j))
            bb = bytearray(b)
            stretch(jj, bb, a.anim, bones, mid if side == 'l' else 1.0, mid if side == 'r' else 1.0)
            v = measure(jj, bb, a.anim, bones)[side]
            if v < a.target:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    kl, kr = (a.swing, a.swing) if a.swing else (side_k('l'), side_k('r'))
    stretch(j, b, a.anim, bones, kl, kr)
    r2 = measure(j, b, a.anim, bones)
    print(f"stretched swing x{kl:.2f} left / x{kr:.2f} right -> native {r2['native']:.2f} m/s "
          f"(left {r2['l']:.2f}, right {r2['r']:.2f}), foot lift {r2['l_lift']:.2f}/{r2['r_lift']:.2f} m")
    if max(r2['l_lift'], r2['r_lift']) > 2.2 * max(r['l_lift'], r['r_lift']):
        print('WARNING: foot lift more than doubled; the target stride is very long. Check the clip by eye.')
    out = a.out or a.glb
    if out == a.glb:
        bk = os.path.join(os.path.dirname(a.glb), 'backup')
        os.makedirs(bk, exist_ok=True)
        dst = os.path.join(bk, os.path.basename(a.glb).replace('.glb', '_original.glb'))
        if not os.path.exists(dst):
            shutil.copy(a.glb, dst)
    open(out, 'wb').write(d[:20 + l] + struct.pack('<I', len(b)) + d[off + 4:off + 8] + bytes(b))
    print('wrote', out, f"- set the game's native speed for this clip to {r2['native']:.2f} m/s")


if __name__ == '__main__':
    main()
