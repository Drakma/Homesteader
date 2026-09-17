#!/usr/bin/env python3
"""
Homesteader Master Asset Kit - Standalone Executable Builder
Compiles app.py into a single, portable Windows .exe using PyInstaller.

Usage:
    python build_exe.py
"""

import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    print("=" * 60)
    print("  Homesteader Asset Kit - Standalone .exe Builder")
    print("=" * 60)

    # Check for PyInstaller
    try:
        import PyInstaller
        print("[Build] PyInstaller found.")
    except ImportError:
        print("[Build] Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    icon_path = os.path.join(BASE_DIR, "app_icon.ico")
    app_script = os.path.join(BASE_DIR, "app.py")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--name=HomesteaderAssetKit",
        f"--icon={icon_path}",
        f"--add-data={os.path.join(BASE_DIR, 'index.html')};.",
        f"--add-data={icon_path};.",
        "--collect-all=webview",
        "--clean",
        "-y",
        app_script
    ]

    print("[Build] Running PyInstaller command:")
    print(" ", " ".join(cmd))
    subprocess.run(cmd, cwd=BASE_DIR, check=True)
    print("\n" + "=" * 60)
    print("  Build complete!")
    print(f"  Executable location: {os.path.join(BASE_DIR, 'dist', 'HomesteaderAssetKit', 'HomesteaderAssetKit.exe')}")
    print("=" * 60)


if __name__ == "__main__":
    main()

