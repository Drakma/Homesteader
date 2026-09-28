#!/usr/bin/env python3
# Throwaway inspector: print animation clip names, skins and joints for GLB files.
# Used to confirm which clips Mesh2Motion offers before promising a clip name.

import json
import os
import struct
import sys


def read_glb_json(path):
    with open(path, "rb") as handle:
        header = handle.read(12)
        if len(header) < 12 or header[0:4] != b"glTF":
            raise ValueError("not a GLB (bad magic)")
        # GLB layout: magic(4) version(4) totalLength(4), then per chunk:
        # chunkLength(4) chunkType(4) data[N]. Chunk 0 header spans offsets
        # 12..19, so the length is at 12 and the type at 16, then data at 20.
        # Read the chunk header as its own 8 bytes rather than reusing
        # header[8:12], which is the file's total length, not the chunk's.
        chunk_header = handle.read(8)
        chunk_len = struct.unpack("<I", chunk_header[0:4])[0]
        chunk_type = chunk_header[4:8]
        if chunk_type != b"JSON":
            raise ValueError("first chunk is not JSON: " + repr(chunk_type))
        payload = handle.read(chunk_len)
    return json.loads(payload.decode("utf-8"))


def summarize(path):
    print("=" * 78)
    print("FILE: " + path)
    if not os.path.isfile(path):
        print("  MISSING")
        return
    print("  bytes: " + str(os.path.getsize(path)))
    try:
        doc = read_glb_json(path)
    except Exception as exc:
        print("  ERROR: " + str(exc))
        return
    anims = doc.get("animations", []) or []
    skins = doc.get("skins", []) or []
    nodes = doc.get("nodes", []) or []
    print("  animations: " + str(len(anims)))
    for i, a in enumerate(anims):
        print("    [" + str(i) + "] " + repr(a.get("name", "?")))
    print("  skins: " + str(len(skins)))
    for s in skins:
        print("    joints: " + str(len(s.get("joints", []) or [])))
    print("  meshes: " + str(len(doc.get("meshes", []) or [])))
    print("  nodes: " + str(len(nodes)))
    # First 40 node names help identify bone naming convention.
    names = [n.get("name", "?") for n in nodes][:40]
    print("  node names (first 40): " + ", ".join(names))


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        summarize(arg)
