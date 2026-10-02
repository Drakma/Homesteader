"""
Makes a looping animation clip in a GLB loop without a pop. A clip whose last pose differs from its first (Idle_A_RT: 21 degrees on the
spine, neck and both arms) jumps back every time it wraps, which shows as the upper body wiggling every few seconds. The last 25 percent of
every rotation channel is blended (spherical, smoothstep) into the first pose, so the clip ends where it began.

    python tools/loop_fix.py measure <glb> [clip]       first-to-last pose difference per clip (degrees)
    python tools/loop_fix.py fix <glb> <clip> [...]     rewrites the clips in place (keeps <glb>.loop_backup)

Writes the same file to Homesteader/Assets/StreamingAssets/Peds/<folder>/ when it exists there (the game loads it from there).
"""
import json
import math
import os
import shutil
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path):
    b = bytearray(open(path, 'rb').read())
    jl = struct.unpack_from('<I', b, 12)[0]
    j = json.loads(bytes(b[20:20 + jl]))
    bp = 20 + jl
    bl = struct.unpack_from('<I', b, bp)[0]
    return b, j, bp + 8, bl


def read(b, j, base, i, comps):
    a = j['accessors'][i]
    bv = j['bufferViews'][a['bufferView']]
    off = base + bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride') or comps * 4
    return [list(struct.unpack_from('<' + 'f' * comps, b, off + k * stride)) for k in range(a['count'])], off, stride


def slerp(a, b, t):
    d = sum(x * y for x, y in zip(a, b))
    if d < 0:
        b = [-x for x in b]
        d = -d
    if d > 0.9995:
        r = [x + (y - x) * t for x, y in zip(a, b)]
    else:
        th = math.acos(d)
        s = math.sin(th)
        wa, wb = math.sin((1 - t) * th) / s, math.sin(t * th) / s
        r = [wa * x + wb * y for x, y in zip(a, b)]
    n = math.sqrt(sum(x * x for x in r)) or 1.0
    return [x / n for x in r]


def angle(q0, q1):
    return 2 * math.degrees(math.acos(min(1.0, abs(sum(x * y for x, y in zip(q0, q1))))))


def run(path, clips, fix):
    b, j, base, _ = load(path)
    for anim in j['animations']:
        if clips and anim['name'] not in clips:
            continue
        worst = 0.0
        for ch in anim['channels']:
            if ch['target']['path'] != 'rotation':
                continue
            s = anim['samplers'][ch['sampler']]
            times, _, _ = read(b, j, base, s['input'], 1)
            quats, off, stride = read(b, j, base, s['output'], 4)
            worst = max(worst, angle(quats[0], quats[-1]))
            if not fix:
                continue
            ts = [t[0] for t in times]
            dur = ts[-1] - ts[0]
            start = ts[0] + dur * 0.75
            first = quats[0]
            for k, t in enumerate(ts):
                if t < start:
                    continue
                u = min(1.0, (t - start) / (ts[-1] - start))
                u = u * u * (3 - 2 * u)
                q = slerp(quats[k], first, u)
                struct.pack_into('<ffff', b, off + k * stride, *q)
        print(('fixed ' if fix else 'measured ') + anim['name'], 'worst first-to-last difference %.1f degrees' % worst)
    if fix:
        shutil.copyfile(path, path + '.loop_backup')
        open(path, 'wb').write(bytes(b))
        folder = os.path.basename(os.path.dirname(path))
        dest = os.path.join(ROOT, 'Homesteader', 'Assets', 'StreamingAssets', 'Peds', folder, os.path.basename(path))
        if os.path.exists(dest):
            shutil.copyfile(path, dest)
            print('also written to', os.path.relpath(dest, ROOT))


if __name__ == '__main__':
    mode, path = sys.argv[1], sys.argv[2]
    names = set(sys.argv[3:])
    run(path, names, mode == 'fix')
