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

def main():
    print("=== SYNCHRONIZING CANONICAL HOMESTEADER ASSETS ===")
    
    # 1. Update Master README
    update_script = os.path.join(ASSETS_DIR, "update_catalog_readme.py")
    if os.path.exists(update_script):
        print("-> Running update_catalog_readme.py...")
        subprocess.run([sys.executable, update_script], check=True)
        
    # 2. Rebuild Asset Kit Single-Page App
    kit_script = os.path.join(ASSETS_DIR, "build_kit.py")
    if os.path.exists(kit_script):
        print("-> Running build_kit.py...")
        subprocess.run([sys.executable, kit_script], check=True)
        
    print("\nCanonical assets catalog and Web Asset Kit are fully synchronized!")

if __name__ == "__main__":
    main()
