#!/usr/bin/env python3
"""
Homesteader Unified Assets Catalog Generator (Canonical Wrapper)

DEPRECATION NOTICE:
The legacy behavior of crawling raw HUD/Content directories and generating
duplicate item folders (e.g. sm_*, baby_*, pig_*) has been retired.

C:\\Users\\casey\\Desktop\\Homesteader\\assets\\ is now the single source of truth.
This script delegates to the canonical catalog tools:
1. assets/update_catalog_readme.py (synchronizes master README.md)
2. assets/build_kit.py (synchronizes interactive Asset Kit index.html)
"""

import os
import sys
import subprocess

HOMESTEADER_DIR = r"C:\Users\casey\Desktop\Homesteader"
ASSETS_DIR = os.path.join(HOMESTEADER_DIR, "assets")
# The scripts live in tools/ (moved from assets/ during the HUD teardown), so
# resolve them from this file's own location rather than a hardcoded subdir.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    print("=== SYNCHRONIZING CANONICAL HOMESTEADER ASSETS ===")
    
    # 1. Update Master README
    update_script = os.path.join(ASSETS_DIR, "update_catalog_readme.py")
    if os.path.exists(update_script):
        print("-> Running update_catalog_readme.py...")
        subprocess.run([sys.executable, update_script], check=True)
        
    # 2. Rebuild Asset Kit Single-Page App.
    # NOTE: build_kit.py writes assets/index.html, which is a hand-edited source
    # file the app reads - not a safe-to-overwrite artifact. It now refuses to
    # clobber a file with local edits (exit 1). That refusal must NOT abort the
    # rest of this pipeline, so the return code is reported rather than raised.
    # build_kit.py lives beside index.html in assets/ (it is the tracked
    # generator for that file), not in tools/.
    kit_script = os.path.join(ASSETS_DIR, "build_kit.py")
    if os.path.exists(kit_script):
        print("-> Running build_kit.py...")
        result = subprocess.run([sys.executable, kit_script])
        if result.returncode != 0:
            print("-> build_kit.py declined to write assets/index.html (see above).")
            print("   The rest of the catalog sync completed normally.")
        
    print("\nCanonical assets catalog and Web Asset Kit are fully synchronized!")

if __name__ == "__main__":
    main()
