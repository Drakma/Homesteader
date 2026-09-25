#!/usr/bin/env python3
"""
Retarget a Mesh2Motion-rigged GLB to Unity Mecanim Humanoid.

Mesh2Motion exports a valid, skinned GLB, but a GLB alone is not a Mecanim
avatar. Unity needs an .fbx (or .glb) plus a .meta that tells the ModelImporter
the animation type is Humanoid and maps each rig bone to a Unity human bone
name. Without that mapping the model imports as a static prop: it has a
skeleton and clips, but no avatar, so nothing animates.

WHAT THIS DOES
    1. Reads the rig bone names out of a rigged GLB.
    2. Maps Mesh2Motion's bone names onto Unity's Mecanim humanoid names.
    3. Writes a ModelImporter .meta next to the model with:
         animationType: 2   (Humanoid)
         avatarSetup:   1   (Create From This Model)
       plus the human[] bone table, so Unity builds the avatar on import.

WHAT THIS DOES NOT DO
    It does not convert GLB to FBX. Unity imports .glb natively, and the
    project's existing peds use .fbx. Pass --format to choose which model file
    the .meta describes; if the model is FBX you must produce that FBX first
    (Blender or an exporter), and this script will write the .meta for it.

    It does not verify the mapping inside Unity. A wrong mapping shows up as
    red bones in the Avatar Configure window. The script prints which Unity
    bones it could NOT map so those are known up front rather than discovered
    in the editor.

USAGE
    python tools/retarget_to_mecanim.py <rigged.glb> [--out-dir DIR]
                                              [--model-file NAME.fbx]
                                              [--guid HEX32]
                                              [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import struct
import sys
import uuid

# -----------------------------------------------------------------------------
# Mesh2Motion bone name -> Unity Mecanim humanoid bone name.
#
# Mesh2Motion uses an Unreal-style rig (pelvis, spine_01, clavicle_l,
# upperarm_l, thigh_l, calf_l, ball_l). Unity's humanoid taxonomy uses its own
# names (Hips, Spine, LeftUpperArm, LeftUpperLeg, LeftLowerLeg, LeftToes).
# This table is the translation, and it is the actual substance of retargeting.
# -----------------------------------------------------------------------------
BONE_MAP = {
    # spine chain
    "pelvis": "Hips",
    "spine_01": "Spine",
    "spine_02": "Chest",
    "spine_03": "UpperChest",
    "neck_01": "Neck",
    "head": "Head",
    # arms
    "clavicle_l": "LeftShoulder",
    "upperarm_l": "LeftUpperArm",
    "lowerarm_l": "LeftLowerArm",
    "hand_l": "LeftHand",
    "clavicle_r": "RightShoulder",
    "upperarm_r": "RightUpperArm",
    "lowerarm_r": "RightLowerArm",
    "hand_r": "RightHand",
    # legs
    "thigh_l": "LeftUpperLeg",
    "calf_l": "LeftLowerLeg",
    "foot_l": "LeftFoot",
    "ball_l": "LeftToes",
    "thigh_r": "RightUpperLeg",
    "calf_r": "RightLowerLeg",
    "foot_r": "RightFoot",
    "ball_r": "RightToes",
}

# Fingers are optional for a valid Mecanim avatar, but mapping them lets Unity
# drive hand poses. Mesh2Motion's *_01..*_04_leaf_l/r scheme maps onto Unity's
# 1..4 naming directly.
FINGER_STEMS = ["index", "middle", "pinky", "ring", "thumb"]
FINGER_UNITY = {
    "index": "Index",
    "middle": "Middle",
    "pinky": "Pinky",
    "ring": "Ring",
    "thumb": "Thumb",
}

# Unity humanoid bones that must be present for an avatar to be valid. Missing
# required bones are what produce a red/broken avatar.
REQUIRED = [
    "Hips", "Spine", "Chest", "Neck", "Head",
    "LeftUpperArm", "LeftLowerArm", "LeftHand",
    "RightUpperArm", "RightLowerArm", "RightHand",
    "LeftUpperLeg", "LeftLowerLeg", "LeftFoot",
    "RightUpperLeg", "RightLowerLeg", "RightFoot",
]

GLB_HEADER_BYTES = 12
CHUNK_HEADER_BYTES = 8


def read_glb_json(path: str) -> dict:
    """Return the parsed JSON chunk of a GLB.

    GLB layout: magic(4) version(4) totalLength(4), then per chunk
    chunkLength(4) chunkType(4) data[N]. The chunk length sits at file offset
    12 and the type at 16 - reading them in the other order silently compares
    the length against the b'JSON' literal and rejects valid files.
    """
    with open(path, "rb") as handle:
        header = handle.read(GLB_HEADER_BYTES)
        if len(header) < GLB_HEADER_BYTES or header[0:4] != b"glTF":
            raise ValueError("not a binary GLB: " + path)
        chunk_header = handle.read(CHUNK_HEADER_BYTES)
        if len(chunk_header) < CHUNK_HEADER_BYTES:
            raise ValueError("truncated GLB chunk header: " + path)
        chunk_len = struct.unpack("<I", chunk_header[0:4])[0]
        chunk_type = chunk_header[4:8]
        if chunk_type != b"JSON":
            raise ValueError("first GLB chunk is not JSON: " + repr(chunk_type))
        return json.loads(handle.read(chunk_len).decode("utf-8"))


def rig_bone_names(doc: dict) -> list:
    """Joint names of the first skin, in the order the skin declares them."""
    skins = doc.get("skins") or []
    if not skins:
        raise ValueError("no skins in this GLB - it is not rigged")
    nodes = doc.get("nodes") or []
    return [nodes[j].get("name", "") for j in skins[0].get("joints", [])]


def build_human_table(bone_names: list) -> tuple:
    """Map rig bones to Unity humanoid names.

    Returns (mapped, unmapped) where mapped is a list of (bone_name, human_name)
    pairs in Unity's expected order, and unmapped is the rig bones with no Unity
    counterpart (leaf/helper bones are expected there).
    """
    lookup = set(bone_names)
    mapped = []

    for rig_name, unity_name in BONE_MAP.items():
        if rig_name in lookup:
            mapped.append((rig_name, unity_name))

    # Fingers: Mesh2Motion index_02_l == Unity LeftIndex2, etc. The *_04_leaf_*
    # bones are tips with no Unity slot, so they are intentionally skipped.
    for stem in FINGER_STEMS:
        for side_short, side_unity in (("l", "Left"), ("r", "Right")):
            for digit in range(1, 5):
                rig_name = stem + "_0" + str(digit) + "_" + side_short
                if rig_name in lookup:
                    mapped.append(
                        (rig_name, side_unity + FINGER_UNITY[stem] + str(digit))
                    )

    mapped_names = {m[1] for m in mapped}
    unmapped = [b for b in bone_names if b not in BONE_MAP
                and not any(b == m[0] for m in mapped)]
    return mapped, unmapped


def meta_text(guid: str, human_table: list, model_leaf: str) -> str:
    """Build a ModelImporter .meta with Humanoid + Create From This Model."""
    lines = []
    add = lines.append

    add("fileFormatVersion: 2")
    add("guid: " + guid)
    add("ModelImporter:")
    add("  serializedVersion: 24600")
    add("  internalIDToNameTable: []")
    add("  externalObjects: {}")
    add("  materials:")
    add("    materialImportMode: 1")
    add("    materialName: 0")
    add("    materialSearch: 1")
    add("    materialLocation: 0")
    add("    searchTexturesGlobally: 0")
    add("  animations:")
    add("    legacyGenerateAnimations: 4")
    add("    bakeSimulation: 0")
    add("    resampleCurves: 1")
    add("    optimizeGameObjects: 0")
    add("    removeConstantScaleCurves: 0")
    add("    motionNodeName: ")
    add("    animationImportErrors: ")
    add("    animationImportWarnings: ")
    add("    animationRetargetingWarnings: ")
    add("    animationDoRetargetingWarnings: 0")
    add("    importAnimatedCustomProperties: 0")
    add("    importConstraints: 0")
    add("    animationCompression: 1")
    add("    animationRotationError: 0.5")
    add("    animationPositionError: 0.5")
    add("    animationScaleError: 0.5")
    add("    animationWrapMode: 0")
    add("    extraExposedTransformPaths: []")
    add("    extraUserProperties: []")
    add("    clipAnimations: []")
    add("    isReadable: 0")
    add("  meshes:")
    add("    lODScreenPercentages: []")
    add("    globalScale: 1")
    add("    meshCompression: 0")
    add("    addColliders: 0")
    add("    useSRGBMaterialColor: 1")
    add("    sortHierarchyByName: 1")
    add("    preBakeConvexCollisionMesh: 0")
    add("    preBakeTriangleCollisionMesh: 0")
    add("    importPhysicalCameras: 1")
    add("    importVisibility: 1")
    add("    importBlendShapes: 1")
    add("    importCameras: 1")
    add("    importLights: 1")
    add("    nodeNameCollisionStrategy: 1")
    add("    fileIdsGeneration: 2")
    add("    swapUVChannels: 0")
    add("    generateSecondaryUV: 0")
    add("    useFileUnits: 1")
    add("    keepQuads: 0")
    add("    weldVertices: 1")
    add("    bakeAxisConversion: 0")
    add("    preserveHierarchy: 0")
    add("    skinWeightsMode: 0")
    add("    maxBonesPerVertex: 4")
    add("    minBoneWeight: 0.001")
    add("    optimizeBones: 1")
    add("    generateMeshLods: 0")
    add("    meshLodGenerationFlags: 0")
    add("    maximumMeshLod: -1")
    add("    importUVs: -1")
    add("    importVertexColors: 1")
    add("    meshOptimizationFlags: -1")
    add("    indexFormat: 0")
    add("    secondaryUVAngleDistortion: 8")
    add("    secondaryUVAreaDistortion: 15.000001")
    add("    secondaryUVHardAngle: 88")
    add("    secondaryUVMarginMethod: 1")
    add("    secondaryUVMinLightmapResolution: 40")
    add("    secondaryUVMinObjectScale: 1")
    add("    secondaryUVPackMargin: 4")
    add("    useFileScale: 1")
    add("    strictVertexDataChecks: 0")
    add("  tangentSpace:")
    add("    normalSmoothAngle: 60")
    add("    normalImportMode: 0")
    add("    tangentImportMode: 3")
    add("    normalCalculationMode: 4")
    add("    legacyComputeAllNormalsFromSmoothingGroupsWhenMeshHasBlendShapes: 0")
    add("    blendShapeNormalImportMode: 1")
    add("    normalSmoothingSource: 0")
    add("    calculateBlendshapeNormalsDeltaFromImportedNormals: 0")
    add("  referencedClips: []")
    add("  importAnimation: 1")
    add("  humanDescription:")
    add("    serializedVersion: 3")
    add("    human:")
    for rig_name, unity_name in human_table:
        add("    - boneName: " + rig_name)
        add("      humanName: " + unity_name)
        add("      limit:")
        add("        min: {x: 0, y: 0, z: 0}")
        add("        max: {x: 0, y: 0, z: 0}")
        add("        value: {x: 0, y: 0, z: 0}")
        add("        length: 0")
        add("        modified: 0")
    # skeleton[] is normally populated by Unity on import; leaving it empty with
    # autoGenerateAvatarMappingIfUnspecified lets Unity build it from this file.
    add("    skeleton: []")
    add("    armTwist: 0.5")
    add("    foreArmTwist: 0.5")
    add("    upperLegTwist: 0.5")
    add("    legTwist: 0.5")
    add("    armStretch: 0.05")
    add("    legStretch: 0.05")
    add("    feetSpacing: 0")
    add("    globalScale: 1")
    add("    rootMotionBoneName: ")
    add("    hasTranslationDoF: 0")
    add("    hasExtraRoot: 0")
    add("    skeletonHasParents: 1")
    add("  lastHumanDescriptionAvatarSource: {instanceID: 0}")
    add("  autoGenerateAvatarMappingIfUnspecified: 1")
    add("  animationType: 2")
    add("  humanoidOversampling: 1")
    add("  avatarSetup: 1")
    add("  addHumanoidExtraRootOnlyWhenUsingAvatar: 1")
    add("  importBlendShapeDeformPercent: 1")
    add("  remapMaterialsIfMaterialImportModeIsNone: 0")
    add("  additionalBone: 0")
    add("  userData: ")
    add("  assetBundleName: ")
    add("  assetBundleVariant: ")
    return "\n".join(lines) + "\n"


def write_text(path: str, text: str) -> None:
    # No UTF-8 BOM: Unity tolerates one but the project forbids BOMs in files
    # tooling reads, and it costs nothing to be consistent.
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Write a Unity Mecanim Humanoid .meta for a rigged GLB."
    )
    parser.add_argument("glb", help="path to the rigged GLB")
    parser.add_argument("--out-dir", default="",
                        help="where to write the .meta (default: alongside the GLB)")
    parser.add_argument("--model-file", default="",
                        help="model filename the .meta describes (default: the GLB name)")
    parser.add_argument("--guid", default="",
                        help="32-char hex guid (default: derived from the model name)")
    parser.add_argument("--dry-run", action="store_true",
                        help="report the mapping without writing anything")
    args = parser.parse_args(argv)

    if not os.path.isfile(args.glb):
        print("error: no such file: " + args.glb, file=sys.stderr)
        return 2

    try:
        doc = read_glb_json(args.glb)
        bones = rig_bone_names(doc)
    except Exception as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 2

    print("rig bones found :", len(bones))
    anims = doc.get("animations") or []
    print("animations      :", [a.get("name") for a in anims])
    if not anims:
        print("warning: this GLB has no animation clips")

    human_table, unmapped = build_human_table(bones)
    mapped_unity = {u for _, u in human_table}

    print("mapped bones    :", len(human_table))
    missing_required = [b for b in REQUIRED if b not in mapped_unity]
    if missing_required:
        print("MISSING REQUIRED:", ", ".join(missing_required))
        print("  -> Unity will show these as unmapped/red bones in Configure.")
    else:
        print("required bones  : all " + str(len(REQUIRED)) + " present")

    print("unmapped rig bones (expected for leaf/helper bones):")
    for name in unmapped:
        print("   ", name)

    model_leaf = args.model_file or os.path.basename(args.glb)
    if args.guid:
        guid = args.guid.strip()
        if len(guid) != 32:
            print("error: --guid must be 32 hex chars, got "
                  + str(len(guid)), file=sys.stderr)
            return 2
    else:
        guid = uuid.uuid5(uuid.NAMESPACE_URL,
                          "homesteader/mecanim/" + model_leaf).hex

    out_dir = args.out_dir or os.path.dirname(os.path.abspath(args.glb))
    meta_path = os.path.join(out_dir, model_leaf + ".meta")

    print("guid            :", guid)
    print("meta path       :", meta_path)

    if args.dry_run:
        print("dry run: nothing written")
        return 0

    if not os.path.isdir(out_dir):
        print("error: output directory does not exist: " + out_dir, file=sys.stderr)
        return 2

    write_text(meta_path, meta_text(guid, human_table, model_leaf))
    print("WROTE           :", meta_path)
    print("")
    print("Next: open Unity and confirm the avatar. Select the model, set")
    print("Rig > Animation Type = Humanoid, Avatar Definition = Create From")
    print("This Model, then Configure and check for red bones. The clips")
    print("should appear in the Rig tab's animation list.")
    return 0


if __name__ == "__main__":
    sys.exit(main())