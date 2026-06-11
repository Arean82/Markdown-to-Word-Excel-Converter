# logic/mermaid_preview_thread.py
# Mermaid Preview Thread - Worker thread for rendering mermaid diagrams

from PyQt6.QtCore import QThread, pyqtSignal

from core.logger import Logger
from logic.mermaid_renderer import MermaidRenderer, MermaidFormat, MermaidBackend
from logic.mermaid_extractor import MermaidExtractor


class MermaidPreviewThread(QThread):
    """Worker thread for mermaid preview to keep UI responsive"""
    
    preview_ready = pyqtSignal(bytes)  # Emits image data
    diagram_list = pyqtSignal(list)    # Emits list of diagrams
    error = pyqtSignal(str)
    
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.logger = Logger()
        self.current_diagram_index = 0
        self.diagrams = []
    
    def run(self):
        """Generate mermaid preview in background thread"""
        try:
            # Load file
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract diagrams
            extractor = MermaidExtractor()
            
            if self.file_path.endswith('.mermaid'):
                # Pure mermaid file - treat entire content as one diagram
                self.diagrams = [{
                    'index': 0,
                    'code': content.strip(),
                    'type': extractor._detect_diagram_type(content),
                    'preview': content[:200] + ('...' if len(content) > 200 else '')
                }]
            else:
                # Markdown file - extract mermaid blocks
                self.diagrams = extractor.extract(content)
            
            if not self.diagrams:
                self.error.emit("No mermaid diagrams found in file")
                return
            
            # Send diagram list to UI
            self.diagram_list.emit(self.diagrams)
            self.logger.info(f"Found {len(self.diagrams)} mermaid diagrams")
            
            # Render first diagram
            if self.diagrams:
                self.render_diagram(0)
                
        except Exception as e:
            self.logger.error(f"Mermaid preview error: {str(e)}")
            self.error.emit(str(e))
    
    def render_diagram(self, index: int):
        """Render diagram at given index"""
        if index < 0 or index >= len(self.diagrams):
            return
        
        self.current_diagram_index = index
        diagram = self.diagrams[index]
        
        try:
            # Try Playwright first, fallback to mermaid-py
            renderer = MermaidRenderer(backend=MermaidBackend.PLAYWRIGHT)
            
            # Render as PNG for preview
            image_data = renderer.render(
                diagram['code'],
                MermaidFormat.PNG,
                width=800,
                height=600,
                theme='dark'
            )
            
            self.preview_ready.emit(image_data)
            self.logger.info(f"Rendered diagram {index + 1}: {diagram['type']}")
            
        except Exception as e:
            self.logger.error(f"Failed to render diagram {index}: {str(e)}")
            self.error.emit(f"Failed to render diagram: {str(e)}")
    
    def render_next(self):
        """Render next diagram"""
        if self.current_diagram_index + 1 < len(self.diagrams):
            self.render_diagram(self.current_diagram_index + 1)
    
    def render_previous(self):
        """Render previous diagram"""
        if self.current_diagram_index - 1 >= 0:
            self.render_diagram(self.current_diagram_index - 1)
    
    def get_diagram_count(self) -> int:
        """Get total number of diagrams"""
        return len(self.diagrams)
    
    def get_current_diagram_info(self) -> dict:
        """Get info about current diagram"""
        if self.diagrams and 0 <= self.current_diagram_index < len(self.diagrams):
            return self.diagrams[self.current_diagram_index]
        return {} 
