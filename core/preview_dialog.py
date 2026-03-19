from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.uic import loadUi
from pathlib import Path
import os

from core.preview_thread import PreviewWorker

class PreviewDialog(QDialog):
    def __init__(self, file_path, use_highlighting=True, parent=None):
        super().__init__(parent)
        
        ui_path = Path(__file__).parent.parent / 'ui' / 'preview_dialog.ui'
        loadUi(str(ui_path), self)

        # Set HTML tab as default (index 1)
        self.tabWidget.setCurrentIndex(1) 
        
        self.file_path = file_path
        self.use_highlighting = use_highlighting
        self.preview_worker = None
        
        self.setWindowTitle(f"Preview: {os.path.basename(file_path)}")
        self.buttonBox.rejected.connect(self.close)
        self.load_preview()
    
    def load_preview(self):
        self.setWindowTitle(f"Preview: {os.path.basename(self.file_path)} (loading...)")
        
        self.preview_worker = PreviewWorker(self.file_path, self.use_highlighting)
        self.preview_worker.preview_ready.connect(self.display_preview)
        self.preview_worker.error.connect(self.show_error)
        self.preview_worker.start()
    
    def display_preview(self, preview_data):
        self.rawTextEdit.setPlainText(preview_data['raw'])
        self.htmlTextEdit.setHtml(preview_data['html'])
        
        self.tablesList.clear()
        if preview_data['tables']:
            self.tablesLabel.setText(f"Found {len(preview_data['tables'])} table(s):")
            self.tablesList.addItems(preview_data['tables'])
        else:
            self.tablesLabel.setText("No tables detected in markdown")
        
        stats = preview_data['stats']
        self.setWindowTitle(
            f"Preview: {os.path.basename(self.file_path)} "
            f"({stats['lines']} lines, {stats['tables']} tables)"
        )
    
    def show_error(self, error_msg):
        QMessageBox.critical(self, "Preview Error", f"Failed to load preview:\n{error_msg}")
        self.close()