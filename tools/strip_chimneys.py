"""
Takes the built-in chimney (the node "Chimney" with its FireboxPoint and SmokePoint) out of the structure stage models: chimneys are built from kits now (docs/CHIMNEYS.md).

    python tools/strip_chimneys.py            # every assets/structures/**/*.glb that has one
    python tools/strip_chimneys.py --check    # only list them

Works on the GLB's JSON chunk only: the nodes are unhooked from the scene (nothing else in the file is touched, so materials, textures, names and part layout stay as they are).
The unused mesh data stays in the file; the next full regeneration of a model (its generator no longer builds a chimney) drops it.
"""
import glob
import json
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMES = {'Chimney', 'FireboxPoint', 'SmokePoint'}


def strip(path, write):
    data = open(path, 'rb').read()
    magic, version, length = struct.unpack('<4sII', data[:12])
    if magic != b'glTF':
        return 0
    off = 12
    chunks = []
    while off < len(data):
        clen, ctype = struct.unpack('<II', data[off:off + 8])
        chunks.append((ctype, data[off + 8:off + 8 + clen]))
        off += 8 + clen
    jtype, jbytes = chunks[0]
    g = json.loads(jbytes.decode('utf-8'))
    nodes = g.get('nodes', [])
    drop = {i for i, n in enumerate(nodes) if n.get('name') in NAMES}
    if not drop:
        return 0
    for n in nodes:
        if 'children' in n:
            n['children'] = [c for c in n['children'] if c not in drop]
            if not n['children']:
                del n['children']
    for sc in g.get('scenes', []):
        sc['nodes'] = [c for c in sc.get('nodes', []) if c not in drop]
    if write:
        out = json.dumps(g, separators=(',', ':')).encode('utf-8')
        out += b' ' * ((4 - len(out) % 4) % 4)
        body = struct.pack('<II', len(out), jtype) + out
        for ctype, cbytes in chunks[1:]:
            body += struct.pack('<II', len(cbytes), ctype) + cbytes
        open(path, 'wb').write(struct.pack('<4sII', b'glTF', 2, 12 + len(body)) + body)
    return len(drop)


def main():
    write = '--check' not in sys.argv
    total = 0
    for p in sorted(glob.glob(os.path.join(ROOT, 'assets', 'structures', '**', '*.glb'), recursive=True)):
        n = strip(p, write)
        if n:
            total += 1
            print(('stripped ' if write else 'has chimney ') + os.path.relpath(p, ROOT), '(%d nodes)' % n)
    print('%d model(s)' % total)


if __name__ == '__main__':
    main()
