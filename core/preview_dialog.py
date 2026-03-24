# core/preview_dialog.py
# This module defines the PreviewDialog class, which provides a user interface for showing a full preview of markdown or mermaid files. It uses worker threads to generate previews without blocking the UI and supports error handling and logging. 
# Preview Dialog - Shows full preview of markdown or mermaid files

import os
from pathlib import Path

from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.uic import loadUi
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from core.logger import Logger

# Logic imports
from logic.md_preview_thread import MarkdownPreviewThread
from logic.mermaid_preview_thread import MermaidPreviewThread


class PreviewDialog(QDialog):
    """Dialog to show full preview of file content"""
    
    def __init__(self, file_path: str, use_highlighting: bool = True, parent=None):
        super().__init__(parent)
        
        # Load UI
        ui_path = Path(__file__).parent.parent / 'ui' / 'preview_dialog.ui'
        loadUi(str(ui_path), self)
        
        self.file_path = file_path
        self.use_highlighting = use_highlighting
        self.logger = Logger()
        
        # Detect file type by extension
        if file_path.endswith(('.md', '.markdown')):
            self.file_type = 'markdown'
            self.setWindowTitle(f"Preview: {os.path.basename(file_path)}")
            self.load_markdown_preview()
        elif file_path.endswith('.mermaid'):
            self.file_type = 'mermaid'
            self.setWindowTitle(f"Mermaid Diagram Preview: {os.path.basename(file_path)}")
            self.load_mermaid_preview()
        else:
            # Try to detect by content
            self.detect_file_type()
        
        # Connect close button
        self.buttonBox.rejected.connect(self.close)
    
    def detect_file_type(self):
        """Detect file type by reading content"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read(500)
            
            if '```mermaid' in content:
                self.file_type = 'markdown_with_mermaid'
                self.setWindowTitle(f"Preview: {os.path.basename(self.file_path)} (with Mermaid)")
                self.load_markdown_preview()
            else:
                self.file_type = 'markdown'
                self.setWindowTitle(f"Preview: {os.path.basename(self.file_path)}")
                self.load_markdown_preview()
        except Exception as e:
            self.logger.error(f"Error detecting file type: {str(e)}")
            self.show_error(str(e))
    
    def load_markdown_preview(self):
        """Load markdown preview using worker thread"""
        self.setWindowTitle(f"Preview: {os.path.basename(self.file_path)} (loading...)")
        
        # Show markdown tabs
        self.tabWidget.setTabVisible(0, True)   # Raw tab
        self.tabWidget.setTabVisible(1, True)   # HTML tab
        self.tabWidget.setTabVisible(2, True)   # Tables tab
        self.tabWidget.setTabVisible(3, False)  # Mermaid tab (hidden)

        # SET HTML TAB AS DEFAULT
        self.tabWidget.setCurrentIndex(1) 
        
        # Start worker thread
        self.preview_worker = MarkdownPreviewThread(self.file_path, self.use_highlighting)
        self.preview_worker.preview_ready.connect(self.display_markdown_preview)
        self.preview_worker.error.connect(self.show_error)
        self.preview_worker.start()
    
    def display_markdown_preview(self, preview_data: dict):
        """Display markdown preview data"""
        self.rawTextEdit.setPlainText(preview_data['raw'])
        self.htmlTextEdit.setHtml(preview_data['html'])
        
        # Display tables
        self.tablesList.clear()
        if preview_data['tables']:
            self.tablesLabel.setText(f"Found {len(preview_data['tables'])} table(s):")
            self.tablesList.addItems(preview_data['tables'])
        else:
            self.tablesLabel.setText("No tables detected in markdown")
        
        # Update window title with stats
        stats = preview_data['stats']
        self.setWindowTitle(
            f"Preview: {os.path.basename(self.file_path)} "
            f"({stats['lines']} lines, {stats['tables']} tables)"
        )
        
        # Check if markdown contains mermaid diagrams
        if preview_data.get('has_mermaid', False):
            self.tabWidget.setTabVisible(3, True)  # Show mermaid tab
            self.mermaidInfoLabel.setText(f"🎨 Found {preview_data.get('mermaid_count', 0)} mermaid diagram(s) in this markdown file")
    
    def load_mermaid_preview(self):
        """Load mermaid preview using worker thread"""
        self.setWindowTitle(f"Preview: {os.path.basename(self.file_path)} (rendering...)")
        
        # Show only mermaid tab
        self.tabWidget.setTabVisible(0, False)  # Raw tab hidden
        self.tabWidget.setTabVisible(1, False)  # HTML tab hidden
        self.tabWidget.setTabVisible(2, False)  # Tables tab hidden
        self.tabWidget.setTabVisible(3, True)   # Mermaid tab visible
        
        # Set mermaid tab as current
        self.tabWidget.setCurrentIndex(3)
        
        # Start worker thread
        self.mermaid_worker = MermaidPreviewThread(self.file_path)
        self.mermaid_worker.preview_ready.connect(self.display_mermaid_preview)
        self.mermaid_worker.diagram_list.connect(self.update_diagram_selector)
        self.mermaid_worker.error.connect(self.show_error)
        self.mermaid_worker.start()
    
    def display_mermaid_preview(self, image_data: bytes):
        """Display mermaid diagram preview"""
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        
        # Scale to fit label
        label_size = self.mermaidPreviewLabel.size()
        scaled_pixmap = pixmap.scaled(
            label_size.width() - 20,
            label_size.height() - 20,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.mermaidPreviewLabel.setPixmap(scaled_pixmap)
        self.mermaidStatusLabel.setText("✅ Preview ready")
    
    def update_diagram_selector(self, diagrams: list):
        """Update diagram selector with available diagrams"""
        self.diagramSelector.clear()
        for idx, diagram in enumerate(diagrams):
            self.diagramSelector.addItem(f"Diagram {idx + 1} - {diagram.get('type', 'unknown')}")
        
        if diagrams:
            self.diagramSelector.setEnabled(True)
            self.exportBtn.setEnabled(True)
            self.mermaidInfoLabel.setText(f"🎨 Found {len(diagrams)} diagram(s)")
    
    def show_error(self, error_msg: str):
        """Show error message"""
        self.logger.error(f"Preview error: {error_msg}")
        QMessageBox.critical(self, "Preview Error", f"Failed to load preview:\n{error_msg}")
        self.close()