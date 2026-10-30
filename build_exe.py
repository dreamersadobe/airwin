"""Script to build standalone AirWin for Windows using PyInstaller."""

import os
import subprocess
import sys


def build():
    print("Building AirWin for Windows...")
    sep = ";" if sys.platform == "win32" else ":"

    # Build single-file executable
    cmd_onefile = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--onefile",
        "--name=AirWin",
        f"--add-data=airwin{sep}airwin",
        "airwin/main.py",
    ]
    print(f"Running command: {' '.join(cmd_onefile)}")
    subprocess.run(cmd_onefile, check=True)
    print("Build finished! Single executable: dist/AirWin.exe")


if __name__ == "__main__":
    build()
