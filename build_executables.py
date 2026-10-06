# ==================================================================
# File: build_executables.py
# Description: Automated compiler script using PyInstaller to package
#              both MarkdownConverter and MarkdownReader standalone binaries.
# ==================================================================

import os
import sys
import subprocess
from pathlib import Path

def run_pyinstaller(entry_script, exe_name):
    print(f"\n--- Compiling {exe_name} from {entry_script} ---")
    
    # We add UI and Assets folders as data dependencies
    add_ui = f"ui{os.path.pathsep}ui"
    add_assets = f"assets{os.path.pathsep}assets"
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        f"--name={exe_name}",
        f"--add-data={add_ui}",
        f"--add-data={add_assets}",
        entry_script
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"Error: Failed to compile {exe_name}")
        sys.exit(result.returncode)
    print(f"Successfully compiled {exe_name}!")

def main():
    # Ensure pyinstaller is installed in the active virtual environment
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller inside the environment...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
        
    run_pyinstaller("main.py", "MarkdownConverter")
    run_pyinstaller("main_reader.py", "MarkdownReader")
    
    print("\n=== BUILD PROCESS COMPLETE ===")
    print("Both executables can be found inside the 'dist' folder:")
    print(f"1. Converter Suite: {Path('dist/MarkdownConverter/MarkdownConverter.exe').absolute()}")
    print(f"2. Dedicated Reader: {Path('dist/MarkdownReader/MarkdownReader.exe').absolute()}")

if __name__ == "__main__":
    main()
