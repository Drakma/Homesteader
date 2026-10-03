"""Fetch the Steadify radio voice runtime: sherpa-onnx native libraries and the Kokoro voice model.

Neither is checked in (the model alone is ~100 MB). Run once per machine:

    python tools/fetch_tts_runtime.py            # download + install
    python tools/fetch_tts_runtime.py --check    # report what is installed

Installs:
  Homesteader/Assets/Plugins/x86_64/sherpa-onnx-c-api.dll, onnxruntime.dll (+ their .meta files)
  Homesteader/Assets/StreamingAssets/Tts/<model>/  (model.onnx, voices.bin, tokens.txt, lexicon-*.txt, dict/, espeak-ng-data/)
  default model: kokoro-multi-lang-v1_0; see KNOWN_MODELS and --model

Sources (GitHub releases of k2-fsa/sherpa-onnx):
  sherpa-onnx-v{SHERPA_VERSION}-win-x64-shared-MD-Release-lib.tar.bz2   (~7 MB)
  tts-models/<model>.tar.bz2                                             (~350 MB for v1_0)

Code that consumes this: Assets/Scripts/Radio/Tts/KokoroTtsEngine.cs (SherpaOnnxNative.cs mirrors the v{SHERPA_VERSION}
C API struct layout, so keep SHERPA_VERSION in step with that file).
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tarfile
import tempfile
import urllib.request

SHERPA_VERSION = "1.13.8"
KNOWN_MODELS = (
    "kokoro-multi-lang-v1_0",   # Kokoro 1.0 fp32, 53 voices, 28 English (recommended, ~350 MB)
    "kokoro-multi-lang-v1_1",   # Kokoro 1.1-zh fp32, 103 voices, 3 English female (~365 MB)
    "kokoro-en-v0_19",          # Kokoro 0.19 fp32, 11 English (~320 MB)
    "kokoro-int8-en-v0_19",     # Kokoro 0.19 int8, 11 English, thin sound (~103 MB)
)
MODEL_NAME = KNOWN_MODELS[0]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_DIR = os.path.join(ROOT, "Homesteader", "Assets", "Plugins", "x86_64")
MODEL_ROOT = os.path.join(ROOT, "Homesteader", "Assets", "StreamingAssets", "Tts")
MODEL_DIR = os.path.join(MODEL_ROOT, MODEL_NAME)

LIB_URL = (f"https://github.com/k2-fsa/sherpa-onnx/releases/download/v{SHERPA_VERSION}/"
           f"sherpa-onnx-v{SHERPA_VERSION}-win-x64-shared-MD-Release-lib.tar.bz2")
MODEL_URL = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/{MODEL_NAME}.tar.bz2"

WANTED_DLLS = ("sherpa-onnx-c-api.dll", "onnxruntime.dll")

# A Unity plugin importer meta so the DLL is marked as a Windows x86_64 native plugin without opening the editor.
DLL_META = """fileFormatVersion: 2
guid: {guid}
PluginImporter:
  externalObjects: {{}}
  serializedVersion: 2
  iconMap: {{}}
  executionOrder: {{}}
  defineConstraints: []
  isPreloaded: 0
  isOverridable: 0
  isExplicitlyReferenced: 0
  validateReferences: 1
  platformData:
  - first:
      : Any
    second:
      enabled: 0
      settings:
        Exclude Editor: 0
        Exclude Linux64: 1
        Exclude OSXUniversal: 1
        Exclude Win: 1
        Exclude Win64: 0
  - first:
      Any:
    second:
      enabled: 0
      settings: {{}}
  - first:
      Editor: Editor
    second:
      enabled: 1
      settings:
        CPU: x86_64
        DefaultValueInitialized: true
        OS: Windows
  - first:
      Standalone: Win64
    second:
      enabled: 1
      settings:
        CPU: x86_64
  userData:
  assetBundleName:
  assetBundleVariant:
"""


def guid_for(name: str) -> str:
    import hashlib
    return hashlib.md5(("homesteader-tts-" + name).encode()).hexdigest()


def download(url: str, dest: str) -> None:
    print(f"  downloading {url}")
    with urllib.request.urlopen(url) as resp, open(dest, "wb") as out:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if total:
                sys.stdout.write(f"\r  {done / 1e6:7.1f} / {total / 1e6:.1f} MB")
                sys.stdout.flush()
    print()


def install_libs(tmp: str) -> None:
    archive = os.path.join(tmp, "libs.tar.bz2")
    download(LIB_URL, archive)
    os.makedirs(PLUGIN_DIR, exist_ok=True)
    found = set()
    with tarfile.open(archive, "r:bz2") as tf:
        for member in tf.getmembers():
            base = os.path.basename(member.name)
            if base in WANTED_DLLS and member.isfile():
                with tf.extractfile(member) as src, open(os.path.join(PLUGIN_DIR, base), "wb") as dst:
                    shutil.copyfileobj(src, dst)
                found.add(base)
                meta = os.path.join(PLUGIN_DIR, base + ".meta")
                if not os.path.exists(meta):
                    with open(meta, "w", encoding="utf-8", newline="\n") as f:
                        f.write(DLL_META.format(guid=guid_for(base)))
                print(f"  installed {base}")
    missing = set(WANTED_DLLS) - found
    if missing:
        raise SystemExit(f"archive did not contain: {', '.join(sorted(missing))}")


def install_model(tmp: str) -> None:
    archive = os.path.join(tmp, "model.tar.bz2")
    download(MODEL_URL, archive)
    name = os.path.basename(MODEL_DIR)
    os.makedirs(MODEL_ROOT, exist_ok=True)
    if os.path.isdir(MODEL_DIR):
        shutil.rmtree(MODEL_DIR)
    with tarfile.open(archive, "r:bz2") as tf:
        # the tarball holds one top-level folder named after the model; extract it in place
        tf.extractall(MODEL_ROOT, filter="data") if hasattr(tarfile, "data_filter") else tf.extractall(MODEL_ROOT)
    if not os.path.isdir(MODEL_DIR):
        raise SystemExit(f"expected {MODEL_DIR} after extraction")
    print(f"  installed {name} -> {MODEL_DIR}")


def check() -> bool:
    ok = True
    for dll in WANTED_DLLS:
        present = os.path.exists(os.path.join(PLUGIN_DIR, dll))
        ok &= present
        print(f"  [{'ok' if present else 'missing'}] Plugins/x86_64/{dll}")
    installed = [m for m in KNOWN_MODELS if os.path.exists(os.path.join(MODEL_ROOT, m, "voices.bin"))]
    print(f"  models installed (the game uses the first): {', '.join(installed) or 'none'}")
    for name in ("model.int8.onnx|model.onnx", "voices.bin", "tokens.txt", "espeak-ng-data"):
        present = any(os.path.exists(os.path.join(MODEL_DIR, n)) for n in name.split("|"))
        ok &= present
        print(f"  [{'ok' if present else 'missing'}] StreamingAssets/Tts/{os.path.basename(MODEL_DIR)}/{name}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="only report what is installed")
    ap.add_argument("--libs-only", action="store_true")
    ap.add_argument("--model-only", action="store_true")
    ap.add_argument("--model", choices=KNOWN_MODELS, default=MODEL_NAME, help="which Kokoro build to install")
    args = ap.parse_args()
    global MODEL_DIR, MODEL_URL
    MODEL_DIR = os.path.join(MODEL_ROOT, args.model)
    MODEL_URL = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/{args.model}.tar.bz2"

    if args.check:
        return 0 if check() else 1

    with tempfile.TemporaryDirectory() as tmp:
        if not args.model_only:
            print("sherpa-onnx native libraries")
            install_libs(tmp)
        if not args.libs_only:
            print("Kokoro voice model")
            install_model(tmp)
    print()
    print("Installed:" if check() else "Something is still missing:")
    print("Restart the Unity editor so it imports the plugins, then tune a station in Steadify > Radio.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
