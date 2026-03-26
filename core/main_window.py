# core/main_window.py
# This module defines the MainWindow class, which is the main application window for the Markdown Converter application. It provides the user interface for selecting files, previewing content, and converting markdown files to Word or Excel formats. It also includes menu options for theme selection, log viewing, and license information    
# Main Window - Main application window

import sys
import os
from pathlib import Path

from PyQt6.QtWidgets import (QMainWindow, QFileDialog, QMessageBox, 
                             QPushButton, QProgressBar, QLabel)
from PyQt6.QtGui import QAction
from PyQt6.uic import loadUi
from PyQt6.QtCore import Qt

from core.logger import Logger
from core.preview_dialog import PreviewDialog
from core.license_viewer import LicenseViewerDialog
from core.log_viewer import LogViewerDialog
from core.readme_viewer import ReadmeViewerDialog

# Logic imports
from logic.md_handler import MarkdownHandler
from logic.mermaid_handler import MermaidHandler
from logic.md_converter import ConversionWorker


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Load UI
        ui_path = Path(__file__).parent.parent / 'ui' / 'main_window.ui'
        loadUi(str(ui_path), self)
        
        # Initialize logger
        self.logger = Logger()
        
        # Initialize variables
        self.current_file = None
        self.current_file_type = None
        self.worker = None
        
        # Initialize handlers
        self.md_handler = MarkdownHandler()
        self.mermaid_handler = MermaidHandler()
        
        # Create menu actions
        self.actionExit = QAction("Exit", self)
        self.actionExit.triggered.connect(self.close)
        
        self.actionDark = QAction("Dark", self)
        self.actionDark.setCheckable(True)
        self.actionDark.setChecked(False)
        self.actionDark.triggered.connect(lambda: self.apply_theme('dark'))
        
        self.actionLight = QAction("Light", self)
        self.actionLight.setCheckable(True)
        self.actionLight.setChecked(True)
        self.actionLight.triggered.connect(lambda: self.apply_theme('light'))
        
        self.actionViewLogs = QAction("View Logs", self)
        self.actionViewLogs.triggered.connect(self.show_logs)
        
        self.actionClearLogs = QAction("Clear Logs", self)
        self.actionClearLogs.triggered.connect(self.clear_logs)
        
        self.actionLicense = QAction("License", self)
        self.actionLicense.triggered.connect(self.show_license)
        
        self.actionReadme = QAction("Readme", self)
        self.actionReadme.triggered.connect(self.show_readme)
        
        # Initially hide mermaid section
        self.mermaidGroup.setVisible(False)

        # Setup menu
        self.setup_menu()
        
        # Apply theme
        self.apply_theme('light')
        
        # Connect UI signals
        self.selectFileBtn.clicked.connect(self.select_file)
        self.previewBtn.clicked.connect(self.show_preview_dialog)
        self.convertBtn.clicked.connect(self.convert_file)
        self.exportDiagramBtn.clicked.connect(self.export_diagram)
        
        self.logger.info("Application started")
    
    def setup_menu(self):
        """Create menu bar programmatically"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction(self.actionExit)
        
        # Theme menu
        theme_menu = menubar.addMenu("Theme")
        theme_menu.addAction(self.actionDark)
        theme_menu.addAction(self.actionLight)
        
        # Logs menu
        logs_menu = menubar.addMenu("Logs")
        logs_menu.addAction(self.actionViewLogs)
        logs_menu.addAction(self.actionClearLogs)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        help_menu.addAction(self.actionLicense)
        help_menu.addAction(self.actionReadme)
    
    def apply_theme(self, theme: str):
        """Apply theme stylesheet"""
        if theme == 'dark':
            theme_path = Path(__file__).parent.parent / 'theme' / 'dark.qss'
            self.actionDark.setChecked(True)
            self.actionLight.setChecked(False)
        else:
            theme_path = Path(__file__).parent.parent / 'theme' / 'light.qss'
            self.actionDark.setChecked(False)
            self.actionLight.setChecked(True)
        
        if theme_path.exists():
            with open(theme_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
            self.logger.info(f"Theme changed to {theme}")
    
    def select_file(self):
        """Open file selection dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "Supported Files (*.md *.markdown *.mermaid *.mmd);;Markdown Files (*.md *.markdown);;Mermaid Files (*.mermaid *.mmd);;All Files (*)"
        )
        
        if not file_path:
            return
        
        self.current_file = file_path
        self.fileLabel.setText(f"📁 {os.path.basename(file_path)}")
        self.convertBtn.setEnabled(True)
        self.previewBtn.setEnabled(True)
        
        # Detect file type by extension
        if file_path.endswith(('.md', '.markdown')):
            self.current_file_type = 'markdown'
            self.fileTypeLabel.setText("📄 File type: Markdown")
            self.load_markdown_preview()
        elif file_path.endswith('.mermaid'):
            self.current_file_type = 'mermaid'
            self.fileTypeLabel.setText("🎨 File type: Mermaid Diagram")
            self.load_mermaid_preview()
        else:
            self.detect_file_type_by_content()
        
        self.logger.info(f"File selected: {file_path} (type: {self.current_file_type})")
        self.show_correct_section()
    
    def detect_file_type_by_content(self):
        """Detect file type by reading content"""
        try:
            with open(self.current_file, 'r', encoding='utf-8') as f:
                content = f.read(500)
            
            if '```mermaid' in content:
                self.current_file_type = 'markdown'
                self.fileTypeLabel.setText("📄 File type: Markdown (with Mermaid diagrams)")
                self.load_markdown_preview()
            else:
                self.current_file_type = 'markdown'
                self.fileTypeLabel.setText("📄 File type: Markdown")
                self.load_markdown_preview()
        except Exception as e:
            self.logger.error(f"Error detecting file type: {str(e)}")
            self.statusLabel.setText(f"Error: {str(e)}")
    
    def load_markdown_preview(self):
        """Load and display markdown preview"""
        try:
            preview_text = self.md_handler.get_preview(self.current_file)
            self.previewText.setPlainText(preview_text)
        except Exception as e:
            self.logger.error(f"Error loading markdown preview: {str(e)}")
            self.previewText.setPlainText(f"Error loading preview: {str(e)}")
    
    def load_mermaid_preview(self):
        """Load and display mermaid preview"""
        try:
            preview_text = self.mermaid_handler.get_preview(self.current_file)
            self.previewText.setPlainText(preview_text)
        except Exception as e:
            self.logger.error(f"Error loading mermaid preview: {str(e)}")
            self.previewText.setPlainText(f"Error loading preview: {str(e)}")
    
    def show_preview_dialog(self):
        """Show full preview dialog"""
        if not self.current_file:
            QMessageBox.warning(self, "Warning", "Please select a file first!")
            return
        
        use_highlighting = self.highlightCheck.isChecked()
        dialog = PreviewDialog(self.current_file, use_highlighting, self)
        dialog.exec()
    
    def convert_file(self):
        """Convert file based on type"""
        if not self.current_file:
            QMessageBox.warning(self, "Warning", "Please select a file first!")
            return
        
        if self.wordRadio.isChecked():
            output_ext = ".docx"
            conv_type = "Word"
        else:
            output_ext = ".xlsx"
            conv_type = "Excel"
        
        if self.current_file_type != 'markdown':
            QMessageBox.warning(
                self, 
                "Warning", 
                "Only markdown files (.md, .markdown) can be converted to Word/Excel.\nMermaid files are for diagram viewing only."
            )
            return
        
        input_path = Path(self.current_file)
        output_file = str(input_path.with_suffix(output_ext))
        use_highlighting = self.highlightCheck.isChecked()
        
        self.set_ui_enabled(False)
        self.progressBar.setVisible(True)
        self.progressBar.setValue(0)
        self.statusLabel.setText("Starting conversion...")
        
        self.worker = ConversionWorker(
            self.current_file,
            output_file,
            conv_type,
            use_highlighting
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.conversion_finished)
        self.worker.start()
        
        self.logger.info(f"Started conversion: {self.current_file} -> {conv_type}")
    
    def set_ui_enabled(self, enabled: bool):
        """Enable/disable UI elements"""
        self.selectFileBtn.setEnabled(enabled)
        self.previewBtn.setEnabled(enabled and self.current_file is not None)
        self.wordRadio.setEnabled(enabled)
        self.excelRadio.setEnabled(enabled)
        self.highlightCheck.setEnabled(enabled)
        self.convertBtn.setEnabled(enabled and self.current_file is not None)
        if hasattr(self, 'exportDiagramBtn'):
            self.exportDiagramBtn.setEnabled(enabled and self.current_file_type == 'mermaid')
    
    def update_progress(self, value: int):
        """Update progress bar"""
        self.progressBar.setValue(value)
    
    def update_status(self, message: str):
        """Update status label"""
        self.statusLabel.setText(message)
    
    def conversion_finished(self, success: bool, message: str):
        """Handle conversion completion"""
        self.progressBar.setVisible(False)
        self.set_ui_enabled(True)
        
        if success:
            self.statusLabel.setText("Conversion complete")
            self.recentLabel.setText(f"✅ Last conversion: {os.path.basename(message.split(':')[-1].strip())}")
            QMessageBox.information(self, "Success", message)
            self.logger.info(f"Conversion successful: {message}")
        else:
            self.statusLabel.setText("Conversion failed")
            self.logger.error(f"Conversion failed: {message}")
            QMessageBox.critical(self, "Error", f"Conversion failed:\n{message}")
    
    def show_license(self):
        """Show license dialog"""
        dialog = LicenseViewerDialog(self)
        dialog.exec()
    
    def show_readme(self):
        """Show README dialog"""
        dialog = ReadmeViewerDialog(self)
        dialog.exec()
    
    def show_logs(self):
        """Show log viewer dialog"""
        dialog = LogViewerDialog(self)
        dialog.exec()
    
    def clear_logs(self):
        """Clear logs with confirmation"""
        reply = QMessageBox.question(
            self,
            "Clear Logs",
            "Are you sure you want to clear all logs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.logger.clear_logs():
                QMessageBox.information(self, "Success", "Logs cleared")
                self.logger.info("Logs cleared by user")
            else:
                QMessageBox.warning(self, "Error", "Failed to clear logs")

    def show_correct_section(self):
        """Show appropriate section based on file type"""
        if self.current_file_type == 'markdown':
            self.mdGroup.setVisible(True)
            self.mermaidGroup.setVisible(False)
            self.convertBtn.setEnabled(True)
        elif self.current_file_type == 'mermaid':
            self.mdGroup.setVisible(False)
            self.mermaidGroup.setVisible(True)
            self.convertBtn.setEnabled(False)
            if hasattr(self, 'exportDiagramBtn'):
                self.exportDiagramBtn.setEnabled(True)

    def get_export_format(self):
        """Get selected export format from radio buttons"""
        if self.pngRadio.isChecked():
            return "PNG"
        elif self.svgRadio.isChecked():
            return "SVG"
        else:
            return "PDF"
        
    def export_diagram(self):
        """Export mermaid diagram to selected format"""
        if not self.current_file or self.current_file_type != 'mermaid':
            QMessageBox.warning(self, "Warning", "Please select a mermaid file first!")
            return

        export_format = self.get_export_format()

        # Get save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Diagram",
            f"diagram.{export_format.lower()}",
            f"{export_format} Files (*.{export_format.lower()});;All Files (*)"
        )

        if not file_path:
            return

        try:
            # Load mermaid content
            with open(self.current_file, 'r', encoding='utf-8') as f:
                code = f.read()

            # Render using mermaid renderer
            from logic.mermaid_renderer import MermaidRenderer, MermaidFormat, MermaidBackend

            # Map format
            format_map = {
                "PNG": MermaidFormat.PNG,
                "SVG": MermaidFormat.SVG,
                "PDF": MermaidFormat.PDF
            }

            renderer = MermaidRenderer(backend=MermaidBackend.MERMAID_PY)
            renderer.render(
                code,
                format_map[export_format],
                output_path=file_path,
                width=1024,
                theme='light'
            )

            QMessageBox.information(self, "Success", f"Diagram exported to:\n{file_path}")
            self.logger.info(f"Diagram exported: {file_path}")

        except Exception as e:
            self.logger.error(f"Export failed: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to export diagram:\n{str(e)}")
    
