import os
import shutil
import subprocess
import sys

def clean_directory(path):
    """Safely remove a directory if it exists."""
    if os.path.exists(path):
        print(f"Cleaning up '{path}'...")
        shutil.rmtree(path, ignore_errors=True)

def main():
    print("=== MD Converter Build System ===")
    print("What would you like to build?")
    print("  1. OneDir (Faster to launch, produces a folder with many files)")
    print("  2. OneFile (Slower to launch, produces a single clean .exe)")
    print("  3. Both")
    print("  4. Exit")
    
    choice = input("\nEnter your choice (1, 2, 3, or 4): ").strip()
    
    if choice == '4':
        print("Exiting.")
        return
        
    build_onedir = choice in ['1', '3']
    build_onefile = choice in ['2', '3']
    
    if not build_onedir and not build_onefile:
        print("Invalid choice. Exiting.")
        return

    print("\n1. Cleaning previous builds...")
    clean_directory('build')
    if build_onedir:
        clean_directory(os.path.join('dist', 'onedir'))
    if build_onefile:
        clean_directory(os.path.join('dist', 'onefile'))
    
    if build_onedir:
        print("\n2. Building 'onedir' executable...")
        # onedir automatically creates a subfolder based on COLLECT name, so output to 'dist'
        subprocess.run([sys.executable, "-m", "PyInstaller", "md_converter_onedir.spec", "--clean", "--noconfirm", "--distpath", "dist"], check=True)
    
    if build_onefile:
        print("\n3. Building 'onefile' executable...")
        # onefile dumps the .exe directly, so we explicitly force the output into 'dist/onefile'
        subprocess.run([sys.executable, "-m", "PyInstaller", "md_converter_onefile.spec", "--clean", "--noconfirm", "--distpath", "dist/onefile"], check=True)
    
    print("\n=== Build Complete! ===")
    print("Your built applications are located in the 'dist' folder.")

if __name__ == "__main__":
    main()
