#!/usr/bin/env python3
# Apply the no-bake fix to the headless auto-rig driver.
#
# WHY: every Mesh2Motion clip keyframes root's rotation at a constant
# [-0.7071, 0, 0, 0.7071] (the -90deg axis conversion). Baking that same value
# into root's default node transform applied it TWICE - once from the exported
# node, once from the clip on playback - which produced the splayed/stretched
# figure in the asset kit. The app's own export never bakes a frame; it moves
# the objects and lets the clips drive. Match that.

import io
import os
import sys

PATH = r"C:\Users\casey\Desktop\Homesteader\tools\mesh2motion\src\autorig_anims.test.ts"

with io.open(PATH, "r", encoding="utf-8") as fh:
    text = fh.read()

OLD_START = "    // Overwrite node defaults with the sampled pose"
OLD_END = "      sampled['pelvis'] ? sampled['pelvis'].q.map((v: number) => +v.toFixed(4)) : '(absent)')"

i = text.find(OLD_START)
j = text.find(OLD_END)
if i == -1 or j == -1:
    print("ERROR: could not locate the baking block")
    print("  start found:", i != -1, " end found:", j != -1)
    sys.exit(1)

j_end = text.find("\n", j) + 1
old_block = text[i:j_end]

new_block = (
    "    // DO NOT bake a sampled pose into the exported node transforms.\n"
    "    //\n"
    "    // Every Mesh2Motion clip keyframes root's rotation at a CONSTANT\n"
    "    // [-0.7071, 0, 0, 0.7071] (the -90 degree axis conversion). Writing that\n"
    "    // same value into root's default transform as well applied it TWICE: once\n"
    "    // from the exported node, and again from the clip on playback. The visible\n"
    "    // results were a splayed/stretched figure and legs that did not mirror.\n"
    "    //\n"
    "    // The app's own export (StepExportToFile.export) moves the objects into the\n"
    "    // export scene and lets the clips drive the pose - it never bakes a frame.\n"
    "    const sampledBones = skinned![0].skeleton.bones.length\n"
    "    console.log('  bones bound       :', sampledBones, '(pose NOT baked)')\n"
    "    console.log('  root default rot  :',\n"
    "      skinned![0].skeleton.bones[0].quaternion.toArray().map((v: number) => +v.toFixed(4)))\n"
)

text = text[:i] + new_block + text[j_end:]

with io.open(PATH, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)

print("replaced", len(old_block.splitlines()), "lines with", len(new_block.splitlines()))
print("new file line count:", len(text.splitlines()))
