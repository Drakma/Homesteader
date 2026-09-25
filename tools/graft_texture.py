#!/usr/bin/env python3
"""
Graft the base-colour texture from a source GLB into an exported GLB.

WHY THIS EXISTS
    The headless rigging pipeline strips image references before loading,
    because GLTFLoader stalls indefinitely under jsdom on an embedded raster
    texture (image decode is not implemented there). That is unavoidable for
    the LOAD, but it leaves the exported model untextured - it renders white.

    The fix does not need an image decoder at all. A GLB texture is just bytes
    in a bufferView plus three small JSON tables (images/textures/samplers).
    So: take the source GLB's JPEG bytes verbatim, append them as a new
    bufferView in the export, and wire the material's baseColorTexture to it.
    No decoding, so it works in Node.

USAGE
    python tools/graft_texture.py <textured_source.glb> <untextured_export.glb> [out.glb]

    If out.glb is omitted the export is rewritten in place.
"""

from __future__ import annotations

import json
import os
import struct
import sys

GLB_MAGIC = b"glTF"
JSON_CHUNK = b"JSON"
BIN_CHUNK = b"BIN\x00"


def parse_glb(path):
    """Return (doc, bin_bytes) for a GLB. Raises ValueError on bad input."""
    with open(path, "rb") as fh:
        header = fh.read(12)
        if len(header) < 12 or header[0:4] != GLB_MAGIC:
            raise ValueError("not a binary GLB: " + path)
        # chunk: length(4) type(4) data[N]. Chunk 0 header spans offsets 12..19.
        chunk_header = fh.read(8)
        if len(chunk_header) < 8:
            raise ValueError("truncated GLB header: " + path)
        json_len = struct.unpack("<I", chunk_header[0:4])[0]
        if chunk_header[4:8] != JSON_CHUNK:
            raise ValueError("first chunk is not JSON: " + path)
        doc = json.loads(fh.read(json_len).decode("utf-8"))

        bin_bytes = b""
        chunk_header = fh.read(8)
        if len(chunk_header) == 8 and chunk_header[4:8] == BIN_CHUNK:
            bin_len = struct.unpack("<I", chunk_header[0:4])[0]
            bin_bytes = fh.read(bin_len)
    return doc, bin_bytes


def build_glb(doc, bin_bytes):
    """Serialise (doc, bin) back to GLB bytes with correct padding."""
    text = json.dumps(doc, separators=(",", ":"))
    while len(text) % 4 != 0:
        text += " "
    json_bytes = text.encode("utf-8")

    bin_pad = bin_bytes
    while len(bin_pad) % 4 != 0:
        bin_pad += b"\x00"

    has_bin = len(bin_pad) > 0
    total = 12 + 8 + len(json_bytes) + (8 + len(bin_pad) if has_bin else 0)

    out = bytearray()
    out += GLB_MAGIC
    out += struct.pack("<I", 2)
    out += struct.pack("<I", total)
    out += struct.pack("<I", len(json_bytes))
    out += JSON_CHUNK
    out += json_bytes
    if has_bin:
        out += struct.pack("<I", len(bin_pad))
        out += BIN_CHUNK
        out += bin_pad
    return bytes(out)


def read_buffer_view(doc, blob, index):
    bv = doc["bufferViews"][index]
    start = bv.get("byteOffset", 0)
    return blob[start:start + bv["byteLength"]]


def graft(source_path, export_path, out_path=None):
    src_doc, src_bin = parse_glb(source_path)
    exp_doc, exp_bin = parse_glb(export_path)

    src_images = src_doc.get("images") or []
    if not src_images:
        raise ValueError("source GLB has no embedded images: " + source_path)

    # Take the FIRST image and its bufferView bytes verbatim.
    img = src_images[0]
    if "bufferView" not in img:
        raise ValueError("source image is not embedded (uri form not supported)")
    jpeg = read_buffer_view(src_doc, src_bin, img["bufferView"])
    mime = img.get("mimeType", "image/jpeg")
    print("  source image      :", mime, len(jpeg), "bytes")

    # Which bufferView in the SOURCE material used it (for the sampler/texCoord)?
    src_materials = src_doc.get("materials") or []
    src_pbr = (src_materials[0].get("pbrMetallicRoughness") if src_materials else {}) or {}
    src_bct = src_pbr.get("baseColorTexture") or {}
    tex_coord = src_bct.get("texCoord", 0)

    # --- append the JPEG to the export's BIN -----------------------------
    exp_bin = bytearray(exp_bin)
    while len(exp_bin) % 4 != 0:
        exp_bin += b"\x00"
    image_offset = len(exp_bin)
    exp_bin += jpeg
    while len(exp_bin) % 4 != 0:
        exp_bin += b"\x00"

    doc = json.loads(json.dumps(exp_doc))  # deep copy
    doc.setdefault("bufferViews", [])
    doc.setdefault("buffers", [])

    # Single-buffer assumption holds for GLTFExporter output.
    if not doc["buffers"]:
        doc["buffers"] = [{"byteLength": 0}]

    doc["bufferViews"].append({
        "buffer": 0,
        "byteOffset": image_offset,
        "byteLength": len(jpeg),
    })
    image_bv = len(doc["bufferViews"]) - 1

    doc["images"] = [{"mimeType": mime, "bufferView": image_bv}]
    doc["samplers"] = [{"magFilter": 9729, "minFilter": 9987,
                        "wrapS": 10497, "wrapT": 10497}]
    doc["textures"] = [{"sampler": 0, "source": 0}]
    doc["buffers"][0]["byteLength"] = len(exp_bin)

    # --- point every material at the texture -----------------------------
    materials = doc.get("materials") or []
    if not materials:
        materials = [{}]
        doc["materials"] = materials
    for mat in materials:
        pbr = mat.setdefault("pbrMetallicRoughness", {})
        pbr["baseColorTexture"] = {"index": 0, "texCoord": tex_coord}
        # GLTFExporter leaves metallicFactor at its glTF default of 1.0, which
        # renders a cloth/flesh texture as dark metal. Force non-metal so the
        # base colour reads correctly.
        pbr["metallicFactor"] = 0.0
        pbr.setdefault("roughnessFactor", 0.85)
        # These source textures carry their colour; do not let a viewer tint them.
        mat.setdefault("pbrMetallicRoughness", pbr)

    out_bytes = build_glb(doc, bytes(exp_bin))

    target = out_path or export_path
    with open(target, "wb") as fh:
        fh.write(out_bytes)
    print("  wrote             :", target, len(out_bytes), "bytes")
    print("  images/textures   :", len(doc["images"]), "/", len(doc["textures"]))
    return target


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    src, exp = argv[1], argv[2]
    out = argv[3] if len(argv) > 3 else None
    for p in (src, exp):
        if not os.path.isfile(p):
            print("error: no such file: " + p, file=sys.stderr)
            return 2
    try:
        graft(src, exp, out)
    except Exception as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
