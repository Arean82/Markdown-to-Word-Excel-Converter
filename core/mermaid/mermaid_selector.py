# core/mermaid/mermaid_selector.py
"""
Mermaid Diagram Selector Dialog - Using UI File
"""

import os
from pathlib import Path
from PyQt6.QtWidgets import (QDialog, QMessageBox, QFileDialog,
                             QListWidgetItem)
from PyQt6.QtCore import Qt
from PyQt6.uic import loadUi

from core.mermaid.mermaid_extractor import MermaidExtractor
from core.mermaid.mermaid_dialog import MermaidDialog
from core.mermaid.mermaid_renderer import MermaidRenderer, MermaidFormat, MermaidBackend

class MermaidSelectorDialog(QDialog):
    """Dialog to select which mermaid diagram to view"""
    
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.diagrams = []
        self.current_diagram = None
        
        # Load UI
        ui_path = Path(__file__).parent.parent.parent / 'ui' / 'mermaid_selector.ui'
        loadUi(str(ui_path), self)
        
        # Connect buttons
        self.viewBtn.clicked.connect(self.view_selected)
        self.viewAllBtn.clicked.connect(self.view_all)
        self.extractAllBtn.clicked.connect(self.extract_all)
        self.closeBtn.clicked.connect(self.reject)
        
        # Connect list selection
        self.diagramList.itemClicked.connect(self.on_diagram_selected)
        
        # Load diagrams
        self.load_diagrams()
    
    def load_diagrams(self):
        """Load and display diagrams from file"""
        try:
            extractor = MermaidExtractor()
            self.diagrams = extractor.extract_from_file(self.file_path)
            
            if not self.diagrams:
                self.infoLabel.setText("No mermaid diagrams found in this file.")
                return
            
            self.infoLabel.setText(f"Found {len(self.diagrams)} diagram(s):")
            
            for diagram in self.diagrams:
                item = QListWidgetItem(f"{diagram['type']} - Diagram {diagram['index'] + 1}")
                item.setData(Qt.ItemDataRole.UserRole, diagram)
                self.diagramList.addItem(item)
                
        except Exception as e:
            self.infoLabel.setText(f"Error loading file: {str(e)}")
    
    def on_diagram_selected(self, item):
        """Show preview of selected diagram"""
        self.current_diagram = item.data(Qt.ItemDataRole.UserRole)
        
        # Update preview
        self.previewTextEdit.setPlainText(self.current_diagram['code'])
        
        # Update stats
        self.typeStatValue.setText(self.current_diagram['type'])
        lines = len(self.current_diagram['code'].split('\n'))
        chars = len(self.current_diagram['code'])
        self.linesStatValue.setText(str(lines))
        self.charsStatValue.setText(str(chars))
        
        self.viewBtn.setEnabled(True)
    
    def view_selected(self):
        """Open selected diagram in viewer"""
        if self.current_diagram:
            dialog = MermaidDialog(
                self.current_diagram['code'],
                self.current_diagram,
                self
            )
            dialog.exec()
    
    def view_all(self):
        """Open all diagrams in separate windows"""
        for diagram in self.diagrams:
            dialog = MermaidDialog(diagram['code'], diagram)
            dialog.show()  # Non-modal, multiple windows
    
    def extract_all(self):
        """Extract all diagrams to folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder for Diagrams",
            str(Path(self.file_path).parent)
        )
        
        if not folder:
            return
        
        try:
            renderer = MermaidRenderer(backend=MermaidBackend.PLAYWRIGHT)
            success_count = 0
            
            self.infoLabel.setText(f"Extracting {len(self.diagrams)} diagrams...")
            
            for diagram in self.diagrams:
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
            
            self.infoLabel.setText(f"Found {len(self.diagrams)} diagram(s):")
            QMessageBox.information(
                self,
                "Extraction Complete",
                f"Successfully extracted {success_count} of {len(self.diagrams)} diagrams to:\n{folder}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to extract diagrams:\n{str(e)}")