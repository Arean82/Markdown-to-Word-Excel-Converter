# main.py
# Entry point for the application Markdown to Word/Excel Converter

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from core.main_window import MainWindow

import urllib.request

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
    # Fix for Windows taskbar icon not showing the custom icon
    if os.name == 'nt':
        import ctypes
        myappid = 'mdconverter.app.1.0' # arbitrary string
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    download_badges()
    
    app = QApplication(sys.argv)
    from PyQt6.QtWidgets import QStyleFactory
    if 'Fusion' in QStyleFactory.keys():
        app.setStyle('Fusion')
    
    # Set application icon (if present)
    icon_path = get_resource_path(Path('assets') / 'icon.png')
    if icon_path.exists():
        app_icon = QIcon(str(icon_path))
        app.setWindowIcon(app_icon)
    
    window = MainWindow()
    if icon_path.exists():
        window.setWindowIcon(app_icon)
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()