# core/license_viewer.py
# License Viewer Dialog for Markdown Converter Application

from PyQt6.QtWidgets import QDialog
from PyQt6.uic import loadUi
from pathlib import Path


class LicenseViewerDialog(QDialog):
    """Dialog to display license information"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Load UI
        ui_path = Path(__file__).parent.parent / 'ui' / 'license_viewer.ui'
        loadUi(str(ui_path), self)
        
        # Connect close button
        self.closeBtn.clicked.connect(self.accept)
        
        # Load license text
        self.load_license()
    
    def load_license(self):
        """Load LICENSE file content"""
        license_path = Path(__file__).parent.parent / 'LICENSE'
        
        if license_path.exists():
            with open(license_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.textBrowser.setPlainText(content)
        else:
            self.textBrowser.setPlainText("LICENSE file not found.")