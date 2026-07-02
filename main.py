# ==================================================================
# File: main.py
# Description: Entry point for the application Markdown to Word/Excel Converter
# ==================================================================

import urllib.request
import traceback
import sys
import os

def exception_hook(exctype, value, tb):
    # with open("FATAL_CRASH.txt", "w") as f:
    #     traceback.print_exception(exctype, value, tb, file=f)
    sys.__excepthook__(exctype, value, tb)
sys.excepthook = exception_hook

from pathlib import Path

# Fix for Windows taskbar icon not showing the custom icon
if os.name == 'nt':
    import ctypes
    myappid = u'mdconverter.app.1.0' # arbitrary string
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from core.main_window import MainWindow

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).parent / relative_path

def download_badges():
    """Download shields.io badges to assets folder if they don't exist"""
    assets_dir = get_resource_path('assets')
    assets_dir.mkdir(exist_ok=True)
    
    badges = {
        'badge_python.svg': 'https://img.shields.io/badge/python-3.8+-blue.svg',
        'badge_pyqt6.svg': 'https://img.shields.io/badge/UI-PyQt6-brightgreen.svg',
        'badge_platform.svg': 'https://img.shields.io/badge/platform-Windows-lightgrey.svg',
        'badge_license.svg': 'https://img.shields.io/badge/license-MIT-green.svg'
    }
    
    for filename, url in badges.items():
        filepath = assets_dir / filename
        if not filepath.exists():
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    filepath.write_bytes(response.read())
            except Exception as e:
                print(f"Failed to download {filename}: {e}")

def main():
    """Application entry point"""
    download_badges()
    
    app = QApplication(sys.argv)
    from PyQt6.QtWidgets import QStyleFactory
    if 'Fusion' in QStyleFactory.keys():
        app.setStyle('Fusion')
    
    # Set application icon (if present)
    png_icon_path = get_resource_path(Path('assets') / 'icon.png')
    ico_icon_path = get_resource_path(Path('assets') / 'icon.ico')
    
    # On Windows, use .ico to ensure taskbar icon displays correctly
    if os.name == 'nt' and png_icon_path.exists() and not ico_icon_path.exists():
        try:
            from PIL import Image
            img = Image.open(png_icon_path)
            img.save(ico_icon_path)
        except Exception as e:
            print(f"Failed to convert icon to ico: {e}")
            
    icon_path = ico_icon_path if (os.name == 'nt' and ico_icon_path.exists()) else png_icon_path
    
    if icon_path.exists():
        app_icon = QIcon(str(icon_path))
        app.setWindowIcon(app_icon)
    
    window = MainWindow()
    if icon_path.exists():
        window.setWindowIcon(app_icon)
    window.show()
    
    print("Starting app.exec()")
    with open("APP_DEBUG.txt", "w") as f:
        f.write("Starting event loop\n")
    try:
        ret = app.exec()
        with open("APP_DEBUG.txt", "a") as f:
            f.write(f"Event loop exited with code: {ret}\n")
        sys.exit(ret)
    except SystemExit as e:
        with open("APP_DEBUG.txt", "a") as f:
            f.write(f"SystemExit caught: {e}\n")
        sys.exit(e.code)


if __name__ == '__main__':
    main()