# ==================================================================
# File: main_reader.py
# Description: Entry point for the standalone Markdown Reader Studio
# ==================================================================

import sys
import os
from pathlib import Path

# Add project root to python load path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication, QStyleFactory, QFileDialog
from core.reader_window import MarkdownReaderWindow

def main():
    app = QApplication(sys.argv)
    
    if 'Fusion' in QStyleFactory.keys():
        app.setStyle('Fusion')
        
    file_path = ""
    # Check if a file was passed as a command line argument (e.g. via drag-and-drop onto the exe)
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        file_path = sys.argv[1]
    else:
        # Standalone launch: prompt the user to choose a Markdown file to open
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Open Markdown File",
            "",
            "Markdown Files (*.md *.markdown);;All Files (*)"
        )
        if not file_path:
            sys.exit(0)
            
    window = MarkdownReaderWindow(file_path, is_dark_theme=False)
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
