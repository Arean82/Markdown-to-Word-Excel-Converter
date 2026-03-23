import sys
import os
from pathlib import Path
from tkinter import dialog

from PyQt6.QtWidgets import (QMainWindow, QFileDialog, QMessageBox, 
                             QCheckBox, QPushButton, QInputDialog)
from PyQt6.uic import loadUi
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from logic.converter_thread import ConversionWorker
from core.preview_dialog import PreviewDialog
from core.menu import setup_menu

from core.mermaid.mermaid_dialog import MermaidDialog
from core.mermaid.mermaid_selector import MermaidSelectorDialog

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

        # Setup mermaid menu after menu bar is created
        self.setup_mermaid_menu()

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

    def setup_mermaid_menu(self):
        """Add mermaid menu to menu bar"""
        # Find or create Mermaid menu
        mermaid_menu = None
        for action in self.menuBar().actions():
            if action.text() == "Mermaid":
                mermaid_menu = action.menu()
                break
        
        if not mermaid_menu:
            mermaid_menu = self.menuBar().addMenu("Mermaid")
        
        # Add actions
        view_diagrams_action = QAction("View Mermaid Diagrams", self)
        view_diagrams_action.triggered.connect(self.view_mermaid_diagrams)
        mermaid_menu.addAction(view_diagrams_action)
        
        extract_all_action = QAction("Extract All Diagrams", self)
        extract_all_action.triggered.connect(self.extract_all_diagrams)
        mermaid_menu.addAction(extract_all_action)
        
        # Add quick preview action
        quick_preview_action = QAction("Quick Preview (First Diagram)", self)
        quick_preview_action.triggered.connect(self.quick_mermaid_preview)
        mermaid_menu.addAction(quick_preview_action)
        
        mermaid_menu.addSeparator()
        
        about_mermaid_action = QAction("About Mermaid Support", self)
        about_mermaid_action.triggered.connect(self.about_mermaid)
        mermaid_menu.addAction(about_mermaid_action)

    def view_mermaid_diagrams(self):
        """Open mermaid diagram selector"""
        if not self.input_file:
            QMessageBox.warning(self, "Warning", "Please select a markdown file first!")
            return
        
        dialog = MermaidSelectorDialog(self.input_file, self)
        dialog.exec()

    def quick_mermaid_preview(self):
        """Quick preview of first mermaid diagram found"""
        if not self.input_file:
            QMessageBox.warning(self, "Warning", "Please select a file first!")
            return

        # Read file and extract mermaid blocks
        with open(self.input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        import re
        pattern = r'```mermaid\s*\n(.*?)\n```'
        mermaid_blocks = re.findall(pattern, content, re.DOTALL)

        if not mermaid_blocks:
            QMessageBox.information(
                self, 
                "No Diagrams Found",
                "No mermaid diagrams found in the selected file."
            )
            return

        # Show first diagram
        dialog = MermaidDialog(mermaid_blocks[0], {
            'index': 0,
            'type': 'diagram',
            'code': mermaid_blocks[0]
        }, self)
        dialog.exec()

    def extract_all_diagrams(self):
        """Extract all diagrams and save to folder"""
        if not self.input_file:
            QMessageBox.warning(self, "Warning", "Please select a markdown file first!")
            return
        
        from core.mermaid.mermaid_extractor import MermaidExtractor
        from core.mermaid.mermaid_renderer import MermaidRenderer, MermaidFormat, MermaidBackend
        
        # Ask for output folder
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder for Diagrams",
            str(Path(self.input_file).parent)
        )
        
        if not folder:
            return
        
        try:
            extractor = MermaidExtractor()
            diagrams = extractor.extract_from_file(self.input_file)
            
            if not diagrams:
                QMessageBox.information(self, "No Diagrams", "No mermaid diagrams found.")
                return
            
            self.statusLabel.setText(f"Extracting {len(diagrams)} diagrams...")
            renderer = MermaidRenderer(backend=MermaidBackend.PLAYWRIGHT)
            success_count = 0
            
            for diagram in diagrams:
                try:
                    output_path = Path(folder) / f"diagram_{diagram['index'] + 1}_{diagram['type']}.png"
                    renderer.render(
                        diagram['code'],
                        MermaidFormat.PNG,
                        output_path=str(output_path),
                        width=1024
                    )
                    success_count += 1
                except Exception as e:
                    print(f"Failed to render diagram {diagram['index']}: {e}")
            
            self.statusLabel.setText("Ready")
            QMessageBox.information(
                self,
                "Extraction Complete",
                f"Successfully extracted {success_count} of {len(diagrams)} diagrams to:\n{folder}"
            )
            
        except Exception as e:
            self.statusLabel.setText("Ready")
            QMessageBox.critical(self, "Error", f"Failed to extract diagrams:\n{str(e)}")

    def about_mermaid(self):
        """Show mermaid support information"""
        QMessageBox.about(
            self,
            "Mermaid Diagram Support",
            "Mermaid Diagram Support\n\n"
            "This application supports rendering mermaid diagrams using:\n"
            "• Playwright (headless Chromium)\n\n"
            "To enable mermaid support, install:\n"
            "pip install playwright\n"
            "playwright install chromium\n\n"
            "Supported formats:\n"
            "• PNG, SVG, PDF, HTML\n\n"
            "Supported diagram types:\n"
            "• Flowcharts, Sequence Diagrams, Class Diagrams\n"
            "• State Diagrams, ER Diagrams, Gantt Charts\n"
            "• Pie Charts, Git Graphs, and more!"
        )

        