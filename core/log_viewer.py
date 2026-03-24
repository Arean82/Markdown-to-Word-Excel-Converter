# core/log_viewer.py
# This module defines the LogViewerDialog class, which provides a user interface for viewing and managing application logs. 
# Log Viewer - Dialog to view and manage application logs

from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.uic import loadUi
from pathlib import Path

from core.logger import Logger


class LogViewerDialog(QDialog):
    """Dialog to view and manage application logs"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Load UI
        ui_path = Path(__file__).parent.parent / 'ui' / 'log_viewer.ui'
        loadUi(str(ui_path), self)
        
        # Connect buttons
        self.refreshBtn.clicked.connect(self.refresh_logs)
        self.clearBtn.clicked.connect(self.clear_logs)
        self.closeBtn.clicked.connect(self.accept)
        
        # Load initial logs
        self.refresh_logs()
    
    def refresh_logs(self):
        """Refresh log display"""
        logger = Logger()
        self.logTextEdit.setText(logger.get_log_content())
    
    def clear_logs(self):
        """Clear all logs after confirmation"""
        reply = QMessageBox.question(
            self,
            "Clear Logs",
            "Are you sure you want to clear all logs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            logger = Logger()
            if logger.clear_logs():
                QMessageBox.information(self, "Success", "Logs cleared")
                self.logTextEdit.clear()
            else:
                QMessageBox.warning(self, "Error", "Failed to clear logs")