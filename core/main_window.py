import sys
import os
from pathlib import Path
from tkinter import dialog

from PyQt6.QtWidgets import (QMainWindow, QFileDialog, QMessageBox, 
                             QCheckBox, QPushButton)
from PyQt6.uic import loadUi
from PyQt6.QtCore import Qt

from logic.converter_thread import ConversionWorker
from core.preview_dialog import PreviewDialog
from core.menu import setup_menu


import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from core.logger import Logger

class MarkdownConverterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        ui_path = Path(__file__).parent.parent / 'ui' / 'ui_mainwindow.ui'
        loadUi(str(ui_path), self)
        
        setup_menu(self)
        
        theme_path = Path(__file__).parent.parent / 'theme' / 'styles.qss.css'
        with open(theme_path, 'r') as f:
            self.setStyleSheet(f.read())
        
        self.input_file = None
        self.output_file = None
        self.worker = None

        self.add_preview_button()
        
        self.selectFileBtn.clicked.connect(self.select_file)
        self.convertBtn.clicked.connect(self.convert_file)

    def show_license(self):
        from core.license_viewer import LicenseViewerDialog
        dialog = LicenseViewerDialog(self)
        dialog.exec()

    def show_readme(self):
        from core.readme_viewer import ReadmeViewerDialog
        dialog = ReadmeViewerDialog(self)
        dialog.exec()

    def change_theme(self, theme):
        if theme == 'dark':
            theme_path = Path(__file__).parent.parent / 'theme' / 'styles.qss.css'
            self.actionDark.setChecked(True)
            self.actionLight.setChecked(False)
        else:
            theme_path = Path(__file__).parent.parent / 'theme' / 'light_styles.qss.css'
            self.actionDark.setChecked(False)
            self.actionLight.setChecked(True)
        
        with open(theme_path, 'r') as f:
            self.setStyleSheet(f.read())

    def view_logs(self):
        from core.log_viewer import LogViewerDialog
        dialog = LogViewerDialog(self)
        dialog.exec()

    def clear_logs(self):
        logger = Logger()
        reply = QMessageBox.question(
            self, 
            "Clear Logs", 
            "Are you sure you want to clear all logs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if logger.clear_logs():
                QMessageBox.information(self, "Success", "Logs cleared")
            else:
                QMessageBox.warning(self, "Error", "Failed to clear logs")
    
    def select_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Markdown File",
            "",
            "Markdown Files (*.md *.markdown);;All Files (*)"
        )

        if file_name:
            self.input_file = file_name
            self.fileLabel.setText(f"📁 {os.path.basename(file_name)}")
            self.convertBtn.setEnabled(True)
            if hasattr(self, 'previewBtn'):
                self.previewBtn.setEnabled(True)

            self.show_preview(file_name)
    
    def show_preview(self, file_name):
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                content = f.read(1000)
                lines = content.split('\n')
                preview = '\n'.join(lines[:15])
                
                if len(content) > 1000:
                    preview += "\n\n... (file truncated for preview)"
                
                self.previewText.setText(preview)
        except Exception as e:
            self.previewText.setText(f"Error loading preview: {str(e)}")
    
    def convert_file(self):
        if not self.input_file:
            QMessageBox.warning(self, "Warning", "Please select a file first!")
            return
        
        # Determine conversion type from radio buttons
        if self.radioWord.isChecked():
            output_ext = ".docx"
            conv_type = "Word"
        else:  # radioExcel.isChecked()
            output_ext = ".xlsx"
            conv_type = "Excel"
        
        input_path = Path(self.input_file)
        self.output_file = str(input_path.with_suffix(output_ext))
        
        use_highlighting = self.syntaxHighlightCheck.isChecked()
        
        self.set_ui_enabled(False)
        self.progressBar.setVisible(True)
        self.progressBar.setValue(0)
        self.statusLabel.setText("Starting conversion...")
        
        self.worker = ConversionWorker(
            self.input_file, 
            self.output_file, 
            conv_type,
            use_highlighting
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.conversion_finished)
        self.worker.start()
    
    def set_ui_enabled(self, enabled):
        self.selectFileBtn.setEnabled(enabled)
        self.radioWord.setEnabled(enabled)
        self.radioExcel.setEnabled(enabled)
        self.syntaxHighlightCheck.setEnabled(enabled)
        self.convertBtn.setEnabled(enabled if self.input_file else False)
    
    def update_progress(self, value):
        self.progressBar.setValue(value)
    
    def update_status(self, message):
        self.statusLabel.setText(message)
    
    def conversion_finished(self, success, message):
        self.progressBar.setVisible(False)
        self.set_ui_enabled(True)
        
        if success:
            self.recentLabel.setText(f"✅ Last conversion: {os.path.basename(self.output_file)}")
            QMessageBox.information(self, "Success", message)
            
            reply = QMessageBox.question(
                self, 
                "Open File",
                "Conversion complete! Do you want to open the file?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.open_file(self.output_file)
        else:
            QMessageBox.critical(self, "Error", f"Conversion failed:\n{message}")
    
    def open_file(self, file_path):
        try:
            if sys.platform == 'win32':
                os.startfile(file_path)
            elif sys.platform == 'darwin':
                os.system(f'open "{file_path}"')
            else:
                os.system(f'xdg-open "{file_path}"')
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not open file: {str(e)}")

    def add_preview_button(self):
        if not hasattr(self, 'previewBtn'):
            self.previewBtn = QPushButton("👁️ Preview")
            self.previewBtn.setFixedWidth(100)
            self.previewBtn.setEnabled(False)
            self.previewBtn.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #5c636a;
                }
                QPushButton:disabled {
                    background-color: #3c4043;
                }
            """)

            if hasattr(self, 'fileRowLayout'):
                self.fileRowLayout.addWidget(self.previewBtn)
                self.previewBtn.clicked.connect(self.show_preview_dialog)

    def show_preview_dialog(self):
        if not self.input_file:
            return

        use_highlighting = self.syntaxHighlightCheck.isChecked()
        self.preview_dialog = PreviewDialog(self.input_file, use_highlighting, self)
        self.preview_dialog.show()