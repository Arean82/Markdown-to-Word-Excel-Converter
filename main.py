# ==================================================================
# File: main.py
# Description: Main entry point for the Markdown Studio Reader App
# ==================================================================

import sys
import os
from pathlib import Path

# Add project root to python load path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication, QStyleFactory
from core.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Try Fusion style as a beautiful base theme
    if 'Fusion' in QStyleFactory.keys():
        app.setStyle('Fusion')
        
    # Attempt to apply qt-material theme if available
    try:
        from qt_material import apply_stylesheet
        # Use dark_teal.xml or similar clean modern design
        apply_stylesheet(app, theme='dark_teal.xml')
    except ImportError:
        # Fallback to default styling
        pass
        
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
