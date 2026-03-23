# core/mermaid/mermaid_dialog.py
"""
Mermaid Preview and Export Dialog - Using UI File
"""

import os
import re
from pathlib import Path
from PyQt6.QtWidgets import (QDialog, QMessageBox, QApplication, 
                             QFileDialog, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.uic import loadUi

from core.mermaid.mermaid_renderer import MermaidRenderer, MermaidFormat, MermaidBackend

class MermaidRenderThread(QThread):
    """Thread for rendering mermaid diagrams"""
    finished = pyqtSignal(bytes, str)  # data, error
    progress = pyqtSignal(str)
    
    def __init__(self, code, format_type, width=800, height=600, theme="default"):
        super().__init__()
        self.code = code
        self.format_type = format_type
        self.width = width
        self.height = height
        self.theme = theme
    
    def run(self):
        try:
            renderer = MermaidRenderer(backend=MermaidBackend.PLAYWRIGHT)
            data = renderer.render(
                self.code, 
                self.format_type,
                width=self.width,
                height=self.height,
                theme=self.theme
            )
            self.finished.emit(data if isinstance(data, bytes) else data.encode(), "")
        except Exception as e:
            self.finished.emit(b"", str(e))

class MermaidDialog(QDialog):
    """Dialog for viewing and exporting mermaid diagrams"""
    
    def __init__(self, mermaid_code, diagram_info=None, parent=None):
        super().__init__(parent)
        self.mermaid_code = mermaid_code
        self.diagram_info = diagram_info or {}
        self.render_thread = None
        self.current_pixmap = None
        
        # Load UI
        ui_path = Path(__file__).parent.parent.parent / 'ui' / 'mermaid_dialog.ui'
        loadUi(str(ui_path), self)
        
        # Set window title
        diagram_type = self.diagram_info.get('type', 'Diagram')
        self.setWindowTitle(f"Mermaid Viewer - {diagram_type}")
        
        # Set code in text edit
        self.codeTextEdit.setPlainText(mermaid_code)
        
        # Update info tab
        self.typeValue.setText(diagram_type)
        lines = len(mermaid_code.split('\n'))
        chars = len(mermaid_code)
        self.linesValue.setText(str(lines))
        self.charsValue.setText(str(chars))
        
        # Connect buttons
        self.exportBtn.clicked.connect(self.export_diagram)
        self.copyBtn.clicked.connect(self.copy_to_clipboard)
        self.refreshBtn.clicked.connect(self.render_preview)
        self.closeBtn.clicked.connect(self.accept)
        
        # Connect combo boxes
        self.widthCombo.currentTextChanged.connect(self.render_preview)
        self.themeCombo.currentTextChanged.connect(self.render_preview)
        
        # Initial render
        self.render_preview()
    
    def render_preview(self):
        """Render preview as PNG"""
        self.statusLabel.setText("🔄 Rendering diagram...")
        self.progressBar.setVisible(True)
        self.progressBar.setRange(0, 0)  # Indeterminate
        self.exportBtn.setEnabled(False)
        self.copyBtn.setEnabled(False)
        self.refreshBtn.setEnabled(False)
        
        width = int(self.widthCombo.currentText()) if self.widthCombo.currentText() != "Auto" else 1024
        theme = self.themeCombo.currentText()
        
        self.render_thread = MermaidRenderThread(
            self.mermaid_code,
            MermaidFormat.PNG,
            width=width,
            height=600,
            theme=theme
        )
        self.render_thread.finished.connect(self.on_render_finished)
        self.render_thread.start()
    
    def on_render_finished(self, data, error):
        """Handle render completion"""
        self.progressBar.setVisible(False)
        self.exportBtn.setEnabled(True)
        self.copyBtn.setEnabled(True)
        self.refreshBtn.setEnabled(True)
        
        if error:
            self.statusLabel.setText(f"❌ Error: {error}")
            self.previewLabel.setText(f"Failed to render diagram:\n{error}")
            return
        
        # Display PNG preview
        self.current_pixmap = QPixmap()
        self.current_pixmap.loadFromData(data)
        
        # Scale to fit label while maintaining aspect ratio
        label_size = self.previewLabel.size()
        scaled_pixmap = self.current_pixmap.scaled(
            label_size.width() - 20,
            label_size.height() - 20,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.previewLabel.setPixmap(scaled_pixmap)
        self.statusLabel.setText("✅ Preview ready")
    
    def export_diagram(self):
        """Export diagram to file"""
        format_map = {
            "PNG": MermaidFormat.PNG,
            "SVG": MermaidFormat.SVG,
            "PDF": MermaidFormat.PDF,
            "HTML": MermaidFormat.HTML
        }
        
        format_type = format_map[self.formatCombo.currentText()]
        extension = format_type.value
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Diagram",
            f"diagram.{extension}",
            f"{extension.upper()} Files (*.{extension});;All Files (*)"
        )
        
        if not file_path:
            return
        
        self.statusLabel.setText(f"📤 Exporting to {extension.upper()}...")
        
        width = int(self.widthCombo.currentText()) if self.widthCombo.currentText() != "Auto" else 1024
        theme = self.themeCombo.currentText()
        
        renderer = MermaidRenderer(backend=MermaidBackend.PLAYWRIGHT)
        try:
            renderer.render(
                self.mermaid_code,
                format_type,
                output_path=file_path,
                width=width,
                theme=theme
            )
            QMessageBox.information(
                self, 
                "Export Successful",
                f"Diagram saved to:\n{file_path}"
            )
            self.statusLabel.setText("✅ Export complete")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export diagram:\n{str(e)}"
            )
            self.statusLabel.setText("❌ Export failed")
    
    def copy_to_clipboard(self):
        """Copy diagram to clipboard as image"""
        if not self.current_pixmap:
            QMessageBox.warning(self, "No Image", "Please wait for the diagram to render first.")
            return
        
        clipboard = QApplication.clipboard()
        clipboard.setPixmap(self.current_pixmap)
        self.statusLabel.setText("📋 Copied to clipboard")