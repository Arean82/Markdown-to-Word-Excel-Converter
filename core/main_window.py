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
from PyQt6.QtCore import Qt, QSettings

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
        
        # Set UI Size
        self.resize(560, 500)
        self.setMinimumSize(560, 500)
        
        # Initialize logger
        self.logger = Logger()
        
        # Initialize variables
        self.current_files = []
        self.current_file = None
        self.current_file_type = None
        self.worker = None
        
        # Setup QSettings for config.ini
        ini_path = Path(__file__).parent.parent / 'config.ini'
        self.settings = QSettings(str(ini_path), QSettings.Format.IniFormat)
        self.last_path = self.settings.value("last_path", str(Path.home()))
        self.current_theme = self.settings.value("theme", "auto")
        
        # Set dynamic property for qt-material to style it as a large primary action button
        self.convertBtn.setProperty("class", "primary")
        
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
        
        self.actionAuto = QAction("Auto (Adaptive)", self)
        self.actionAuto.setCheckable(True)
        self.actionAuto.setChecked(False)
        self.actionAuto.triggered.connect(lambda: self.apply_theme('auto'))
        
        self.actionLight = QAction("Light", self)
        self.actionLight.setCheckable(True)
        self.actionLight.setChecked(True)
        self.actionLight.triggered.connect(lambda: self.apply_theme('light'))
        
        self.material_actions = []
        
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
        self.apply_theme(self.current_theme)
        
        # Connect UI signals
        self.selectFileBtn.clicked.connect(self.select_file)
        self.previewBtn.clicked.connect(self.show_preview_dialog)
        self.convertBtn.clicked.connect(self.convert_file)
        self.exportDiagramBtn.clicked.connect(self.export_diagram)
        self.wordRadio.toggled.connect(self.toggle_word_settings)
        if hasattr(self, 'pdfMarkdownRadio'):
            self.pdfMarkdownRadio.toggled.connect(self.toggle_word_settings)
        
        # Initial state for Word settings
        self.toggle_word_settings()
        
        self.fileListWidget.itemSelectionChanged.connect(self.handle_list_selection)
        
        self.logger.info("Application started")
    
    def setup_menu(self):
        """Create menu bar programmatically"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction(self.actionExit)
        
        # Theme menu
        theme_menu = menubar.addMenu("Theme")
        theme_menu.addAction(self.actionAuto)
        theme_menu.addAction(self.actionDark)
        theme_menu.addAction(self.actionLight)
        
        # Material sub-menu
        material_menu = theme_menu.addMenu("Material Theme")
        try:
            import qt_material
            for theme_name in qt_material.list_themes():
                action = QAction(theme_name, self)
                action.setCheckable(True)
                action.setChecked(False)
                # Capture theme_name in lambda
                action.triggered.connect(lambda checked, t=theme_name: self.apply_theme(f'material:{t}'))
                material_menu.addAction(action)
                self.material_actions.append(action)
        except ImportError:
            material_menu.setEnabled(False)
            material_menu.setToolTip("Please run 'pip install qt-material' to enable Material themes")
        
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
        self.current_theme = theme
        # Uncheck all
        if hasattr(self, 'actionAuto'):
            self.actionAuto.setChecked(False)
        self.actionDark.setChecked(False)
        self.actionLight.setChecked(False)
        for action in self.material_actions:
            action.setChecked(False)
        
        if theme.startswith('material:'):
            material_theme_name = theme.split(':')[1]
            # Check the specific action
            for action in self.material_actions:
                if action.text() == material_theme_name:
                    action.setChecked(True)
                    break
                    
            try:
                from qt_material import apply_stylesheet
                import os
                # Apply the selected material theme
                apply_stylesheet(self, theme=material_theme_name)
                self.logger.info(f"Theme changed to Material: {material_theme_name}")
            except ImportError:
                self.logger.warning("qt-material is not installed")
                self.apply_theme('dark') # fallback
            return
            
        # Reset qt-material styling if switching away from material
        self.setStyleSheet("")
        
        if theme == 'auto':
            if hasattr(self, 'actionAuto'):
                self.actionAuto.setChecked(True)
            import PyQt6.QtWidgets as QtWidgets
            app = QtWidgets.QApplication.instance()
            if app:
                # Use window color lightness to guess system theme
                is_dark = app.palette().window().color().lightness() < 128
            else:
                is_dark = False
            theme_path = Path(__file__).parent.parent / 'assets' / 'theme' / ('dark.qss' if is_dark else 'light.qss')
            theme_name = 'dark' if is_dark else 'light'
        elif theme == 'dark':
            theme_path = Path(__file__).parent.parent / 'assets' / 'theme' / 'dark.qss'
            self.actionDark.setChecked(True)
            theme_name = 'dark'
        else:
            theme_path = Path(__file__).parent.parent / 'assets' / 'theme' / 'light.qss'
            self.actionLight.setChecked(True)
            theme_name = 'light'
        
        if theme_path.exists():
            with open(theme_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
            self.logger.info(f"Theme changed to {theme} (applied {theme_name})")
    
    def select_file(self):
        """Open file selection dialog"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            self.last_path,
            "Supported Files (*.md *.markdown *.mermaid *.mmd);;Markdown Files (*.md *.markdown);;Mermaid Files (*.mermaid *.mmd);;All Files (*)"
        )
        
        if not file_paths:
            return
            
        self.last_path = str(Path(file_paths[0]).parent)
        self.current_files = file_paths
        self.fileListWidget.clear()
        for fp in self.current_files:
            self.fileListWidget.addItem(os.path.basename(fp))
            
        # Select the first file by default
        self.fileListWidget.setCurrentRow(0)
        self.convertBtn.setEnabled(True)
        
        self.logger.info(f"Selected {len(self.current_files)} files.")
        self.show_correct_section()
        
    def handle_list_selection(self):
        """Handle selection change in the list widget"""
        selected_items = self.fileListWidget.selectedItems()
        if not selected_items:
            self.previewBtn.setEnabled(False)
            self.current_file = None
            return
            
        self.previewBtn.setEnabled(True)
        index = self.fileListWidget.currentRow()
        self.current_file = self.current_files[index]
        
        if self.current_file.endswith(('.md', '.markdown')):
            self.current_file_type = 'markdown'
            self.fileTypeLabel.setText(f"📄 File type: Markdown")
        elif self.current_file.endswith('.mermaid'):
            self.current_file_type = 'mermaid'
            self.fileTypeLabel.setText(f"🎨 File type: Mermaid Diagram")
        else:
            self.fileTypeLabel.setText(f"📄 File type: Unknown")
    
    def show_preview_dialog(self):
        """Show full preview dialog"""
        if not self.current_files:
            QMessageBox.warning(self, "Warning", "Please select files first!")
            return
            
        index = self.fileListWidget.currentRow()
        if index < 0:
            index = 0
        
        use_highlighting = self.highlightCheck.isChecked()
        dialog = PreviewDialog(self.current_files, index, use_highlighting, self)
        dialog.exec()

    def convert_file(self):
        """Convert all selected markdown files"""
        if not self.current_files:
            QMessageBox.warning(self, "Warning", "Please select files first!")
            return
            
        # Build queue of markdown files
        self.conversion_queue = [f for f in self.current_files if f.endswith(('.md', '.markdown'))]
        if not self.conversion_queue:
            QMessageBox.warning(self, "Warning", "No markdown files selected for conversion.\nMermaid files are for diagram viewing only.")
            return

        self.set_ui_enabled(False)
        self.progressBar.setVisible(True)
        self.progressBar.setValue(0)
        
        self.conversion_successes = 0
        self.conversion_failures = 0
        self.start_next_conversion()

    def start_next_conversion(self):
        if not self.conversion_queue:
            # Batch finished
            self.set_ui_enabled(True)
            self.progressBar.setValue(100)
            self.statusLabel.setText("Batch conversion complete")
            QMessageBox.information(self, "Batch Complete", f"Successfully converted {self.conversion_successes} file(s). Failed: {self.conversion_failures}")
            return
            
        file_to_convert = self.conversion_queue.pop(0)
        
        if self.wordRadio.isChecked():
            output_ext = ".docx"
            conv_type = "Word"
        elif hasattr(self, 'pdfMarkdownRadio') and self.pdfMarkdownRadio.isChecked():
            output_ext = ".pdf"
            conv_type = "PDF"
        else:
            output_ext = ".xlsx"
            conv_type = "Excel"
            
        input_path = Path(file_to_convert)
        output_file = str(input_path.with_suffix(output_ext))
        use_highlighting = self.highlightCheck.isChecked()
        paper_size = self.paperSizeCombo.currentText() if hasattr(self, 'paperSizeCombo') else "A4"
        orientation = self.orientationCombo.currentText() if hasattr(self, 'orientationCombo') else "Portrait"
        margin = self.marginCombo.currentText() if hasattr(self, 'marginCombo') else "Normal"
        
        self.statusLabel.setText(f"Converting: {os.path.basename(file_to_convert)}...")
        
        self.worker = ConversionWorker(
            file_to_convert,
            output_file,
            conv_type,
            use_highlighting,
            paper_size,
            orientation,
            margin
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.on_batch_conversion_finished)
        self.worker.start()

    def on_batch_conversion_finished(self, success: bool, message: str):
        if success:
            self.conversion_successes += 1
            self.logger.info(f"Batch item successful: {message}")
            self.recentLabel.setText(f"✅ Last: {os.path.basename(message.split(':')[-1].strip())}")
        else:
            self.conversion_failures += 1
            self.logger.error(f"Batch item failed: {message}")
            
        self.start_next_conversion()
    
    def set_ui_enabled(self, enabled: bool):
        """Enable/disable UI elements"""
        self.selectFileBtn.setEnabled(enabled)
        self.previewBtn.setEnabled(enabled and self.current_file is not None)
        self.wordRadio.setEnabled(enabled)
        self.excelRadio.setEnabled(enabled)
        if hasattr(self, 'pdfMarkdownRadio'):
            self.pdfMarkdownRadio.setEnabled(enabled)
        
        format_selected = self.wordRadio.isChecked() or (hasattr(self, 'pdfMarkdownRadio') and self.pdfMarkdownRadio.isChecked())
        word_settings_enabled = enabled and format_selected
        self.highlightCheck.setEnabled(word_settings_enabled)
        
        if hasattr(self, 'paperSizeCombo'):
            self.paperSizeCombo.setEnabled(word_settings_enabled)
            self.orientationCombo.setEnabled(word_settings_enabled)
            self.marginCombo.setEnabled(word_settings_enabled)
            self.paperLabel.setEnabled(word_settings_enabled)
            self.orientationLabel.setEnabled(word_settings_enabled)
            self.marginLabel.setEnabled(word_settings_enabled)
            
        self.convertBtn.setEnabled(enabled and self.current_file is not None)
        if hasattr(self, 'exportDiagramBtn'):
            self.exportDiagramBtn.setEnabled(enabled and self.current_file_type == 'mermaid')
            
    def toggle_word_settings(self, checked: bool = False):
        """Toggle Word/PDF specific settings"""
        format_selected = self.wordRadio.isChecked() or (hasattr(self, 'pdfMarkdownRadio') and self.pdfMarkdownRadio.isChecked())
        self.highlightCheck.setEnabled(format_selected)
        if hasattr(self, 'paperSizeCombo'):
            self.paperSizeCombo.setEnabled(format_selected)
            self.orientationCombo.setEnabled(format_selected)
            self.marginCombo.setEnabled(format_selected)
            self.paperLabel.setEnabled(format_selected)
            self.orientationLabel.setEnabled(format_selected)
            self.marginLabel.setEnabled(format_selected)
    
    def update_progress(self, value: int):
        """Update progress bar"""
        self.progressBar.setValue(value)
    
    def update_status(self, message: str):
        """Update status label"""
        self.statusLabel.setText(message)
    
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

    def closeEvent(self, event):
        """Clean up background threads before closing."""
        try:
            # Save settings
            self.settings.setValue("theme", self.current_theme)
            self.settings.setValue("last_path", self.last_path)
            
            if self.worker and self.worker.isRunning():
                self.worker.quit()
                self.worker.wait(1000)
            
            # Close preview dialog if open to kill any threads inside it
            if hasattr(self, 'preview_dialog') and self.preview_dialog is not None:
                self.preview_dialog.close()
                
        except Exception as e:
            self.logger.error(f"Error during shutdown: {str(e)}")
            
        event.accept()
    
