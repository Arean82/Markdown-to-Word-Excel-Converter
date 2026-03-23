# core/mermaid/mermaid_extractor.py
"""
Extract and process mermaid diagrams from markdown
"""

import re
from typing import List, Dict, Tuple
from pathlib import Path

class MermaidExtractor:
    """Extract mermaid diagrams from markdown files"""
    
    def __init__(self):
        self.mermaid_pattern = r'```mermaid\s*\n(.*?)\n```'
        self.diagram_types = [
            'flowchart', 'sequenceDiagram', 'classDiagram', 
            'stateDiagram', 'erDiagram', 'journey', 'gantt',
            'pie', 'quadrantChart', 'requirementDiagram', 'gitGraph'
        ]
    
    def extract(self, content: str) -> List[Dict[str, str]]:
        """
        Extract all mermaid diagrams from markdown content
        
        Returns:
            List of dicts with keys: 'code', 'type', 'index'
        """
        matches = re.findall(self.mermaid_pattern, content, re.DOTALL)
        diagrams = []
        
        for idx, code in enumerate(matches):
            code = code.strip()
            diagram_type = self._detect_diagram_type(code)
            diagrams.append({
                'index': idx,
                'code': code,
                'type': diagram_type,
                'preview': code[:200] + ('...' if len(code) > 200 else '')
            })
        
        return diagrams
    
    def _detect_diagram_type(self, code: str) -> str:
        """Detect the type of mermaid diagram"""
        first_line = code.split('\n')[0].strip().lower()
        for diagram_type in self.diagram_types:
            if diagram_type.lower() in first_line:
                return diagram_type
        return 'unknown'
    
    def extract_from_file(self, file_path: str) -> List[Dict[str, str]]:
        """Extract diagrams from a markdown file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.extract(content)
    
    def replace_with_images(self, content: str, renderer, output_format='png') -> str:
        """
        Replace mermaid code blocks with embedded images
        Useful for Word/PDF export
        """
        def replace_match(match):
            code = match.group(1).strip()
            try:
                # Render diagram
                image_data = renderer.render(code, MermaidFormat.PNG)
                import base64
                img_b64 = base64.b64encode(image_data).decode('utf-8')
                return f'<img src="data:image/png;base64,{img_b64}" alt="Mermaid Diagram">'
            except Exception as e:
                return f'<div class="mermaid-error">Failed to render: {str(e)}</div>'
        
        return re.sub(self.mermaid_pattern, replace_match, content, flags=re.DOTALL)