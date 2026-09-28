#!/usr/bin/env python3
# Remove all AnimationMixer usage from the headless auto-rig driver.
#
# WHY: calling mixer.clipAction(clip, mesh) BINDS the clip to the mesh via
# three.js PropertyBinding, which mutates the clip's tracks in place. The
# exporter then serialised those mutated tracks, and every clip came out
# flattened to 2 STEP keyframes (start/end only) with correct duration but no
# motion - so the model rendered as a frozen pose in the asset kit.
#
# The app only uses the mixer for INTERACTIVE preview. Export needs pristine
# clips handed straight to GLTFExporter, which is what StepExportToFile.export
# does. So drop the mixer entirely.

import io
import sys

PATH = r"C:\Users\casey\Desktop\Homesteader\tools\mesh2motion\src\autorig_anims.test.ts"

with io.open(PATH, "r", encoding="utf-8") as fh:
    lines = fh.read().splitlines()

start = None
end = None
for i, line in enumerate(lines):
    if "clips animate" in line and start is None:
        # back up to the comment banner line above
        start = i
        while start > 0 and not lines[start].lstrip().startswith("// ---"):
            start -= 1
    if "root default rot" in line:
        end = i
        # include the continuation line of that console.log
        while end + 1 < len(lines) and not lines[end].rstrip().endswith(")"):
            end += 1

if start is None or end is None:
    print("ERROR: could not locate the mixer block (start=%s end=%s)" % (start, end))
    sys.exit(1)

removed = lines[start:end + 1]
replacement = [
    "    // --- 6. Clips are handed to the exporter PRISTINE -------------------",
    "    // Do NOT create an AnimationMixer here.",
    "    //",
    "    // mixer.clipAction(clip, mesh) BINDS the clip to the mesh through",
    "    // three.js PropertyBinding, which mutates clip.tracks in place. The",
    "    // exporter then wrote those mutated tracks and every clip came out",
    "    // flattened to 2 STEP keyframes (start/end only): correct duration,",
    "    // zero motion, and a model frozen in its default pose in the viewer.",
    "    //",
    "    // The mixer is for the app's INTERACTIVE preview only. StepExportToFile",
    "    // hands pristine clips straight to GLTFExporter, so do the same.",
    "    console.log('  clips are pristine:', clips.map((c: any) => c.name).join(', '))",
]

new_lines = lines[:start] + replacement + lines[end + 1:]

with io.open(PATH, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(new_lines) + "\n")

print("removed %d lines, inserted %d" % (len(removed), len(replacement)))
print()
for l in removed[:6]:
    print("  -", l)
