"""_smoke_via_cli.py - smoke test the installed tripo-cli.

After Node.js + tripo-cli are installed, this validates the toolchain
end-to-end with a single 3D generation. Avoids the cost of a fixture
like `Build a wooden cabin` with comprehensive settings.

Usage:
    python _smoke_via_cli.py "small wooden log cabin"
    tripo doctor <-- run separately to verify CLI installation

What it does:
    1. Confirms `tripo` is on PATH.
    2. Runs `tripo make <prompt>` against the API key the user
       configured via `tripo login` or TRIPO_API_KEY.
    3. Parses CLI output for the resulting task_id and the local
       ./tripo-out/<task_id>/ path.
    4. Renames the resulting model.glb into a smoke output folder.
"""

import json
import os
import shutil
import subprocess
import sys

PROJ = r"C:\Users\casey\Desktop\Homesteader"
SMOKE_OUT = os.path.join(PROJ, "_procgen_test", "_tripo_smoke")


def confirm_tripo_on_path():
    r = subprocess.run(["tripo", "--version"], capture_output=True, text=True)
    if r.returncode != 0:
        print("[smoke] `tripo` not on PATH. Verify Node 22 LTS is installed "
              "and `npm install -g tripo-cli` ran cleanly.")
        print(r.stderr)
        sys.exit(2)
    print(f"[smoke] tripo cli version: {r.stdout.strip()}")


def main():
    if len(sys.argv) < 2:
        print("usage: python _smoke_via_cli.py <prompt>")
        sys.exit(2)

    confirm_tripo_on_path()

    prompt = sys.argv[1]
    print(f"[smoke] prompt: {prompt!r}")
    print("[smoke] calling: tripo make {prompt!r}")

    r = subprocess.run(["tripo", "make", prompt], capture_output=True,
                       text=True, timeout=300)
    print(f"[smoke] cli exit: {r.returncode}")
    if r.stdout:
        print("[smoke] stdout (last 30 lines):")
        for line in r.stdout.splitlines()[-30:]:
            print(f"  {line}")
    if r.stderr:
        print("[smoke] stderr (last 10 lines):")
        for line in r.stderr.splitlines()[-10:]:
            print(f"  {line}")

    if r.returncode != 0:
        print("[smoke] tripo make failed; inspect output above.")
        sys.exit(2)

    # The CLI writes ./tripo-out/<task_id> from CWD. We need its path.
    cwd = os.getcwd()
    out_dir = os.path.join(cwd, "tripo-out")
    if not os.path.isdir(out_dir):
        # Some versions deposit under a different relative path.
        out_dir = os.path.expanduser("~/tripo-out")
    if not os.path.isdir(out_dir):
        print(f"[smoke] could not locate {out_dir}; inspect manually")
        sys.exit(3)

    # Find newest task
    task_dirs = [os.path.join(out_dir, d)
                 for d in os.listdir(out_dir)
                 if os.path.isdir(os.path.join(out_dir, d))]
    if not task_dirs:
        print("[smoke] no tasks in tripo-out/")
        sys.exit(3)
    task_dirs.sort(key=os.path.getmtime, reverse=True)
    newest = task_dirs[0]
    task_id = os.path.basename(newest)
    print(f"[smoke] latest task: {task_id}")
    for fname in os.listdir(newest):
        print(f"  {fname}")

    glb = os.path.join(newest, "model.glb")
    if not os.path.isfile(glb):
        print("[smoke] no model.glb in newest task")
        sys.exit(4)

    os.makedirs(SMOKE_OUT, exist_ok=True)
    dest = os.path.join(SMOKE_OUT, f"{task_id}.glb")
    shutil.copy2(glb, dest)
    size = os.path.getsize(dest)
    print(f"[smoke] saved -> {dest} ({size / 1024:.1f} KB)")
    print(f"[smoke] preview at: {newest}/preview.png")


if __name__ == "__main__":
    main()
