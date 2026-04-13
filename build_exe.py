#!/usr/bin/env python3
"""
Build a standalone DiagramEditor.exe using PyInstaller.

Usage:
    python build_exe.py

This will:
  1. Install PyInstaller if not already installed.
  2. Build a single-folder distribution in dist/DiagramEditor/
  3. The resulting DiagramEditor.exe can run without Python installed.

Output:
    dist/DiagramEditor/DiagramEditor.exe   <-- double-click to run
"""

import subprocess
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def ensure_pyinstaller():
    try:
        import PyInstaller
        print(f"PyInstaller {PyInstaller.__version__} found.")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("PyInstaller installed.")


def build():
    ensure_pyinstaller()

    run_py = os.path.join(ROOT, "run.py")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "DiagramEditor",
        "--noconsole",                # No terminal window on launch
        "--noconfirm",                # Overwrite previous build
        "--clean",                    # Clean build cache
        "--add-data", f"{os.path.join(ROOT, 'diagram_app.py')}{os.pathsep}.",
        run_py,
    ]

    print()
    print("Building DiagramEditor.exe ...")
    print(f"  Command: {' '.join(cmd)}")
    print()

    subprocess.check_call(cmd, cwd=ROOT)

    exe_path = os.path.join(ROOT, "dist", "DiagramEditor", "DiagramEditor.exe")
    if os.path.isfile(exe_path):
        print()
        print("=" * 50)
        print("  BUILD SUCCESSFUL")
        print(f"  {exe_path}")
        print()
        print("  You can copy the entire dist/DiagramEditor/")
        print("  folder to any Windows machine and run")
        print("  DiagramEditor.exe — no Python needed.")
        print("=" * 50)
    else:
        print()
        print("Build may have failed — exe not found at expected path.")
        print("Check the output above for errors.")


if __name__ == "__main__":
    build()
