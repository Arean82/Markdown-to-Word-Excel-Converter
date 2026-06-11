# logic/mermaid_extractor.py
# Mermaid Extractor - Extract and process mermaid diagrams from markdown files

import re
from typing import List, Dict, Optional
from pathlib import Path

from core.logger import Logger


class MermaidExtractor:
    """Extract and process mermaid diagrams from markdown files"""
    
    def __init__(self):
        self.logger = Logger()
        self.mermaid_pattern = r'```mermaid\s*\n(.*?)\n```'
        self.diagram_types = [
            'flowchart', 'sequenceDiagram', 'classDiagram', 
            'stateDiagram', 'stateDiagram-v2', 'erDiagram', 
            'journey', 'gantt', 'pie', 'quadrantChart', 
            'requirementDiagram', 'gitGraph', 'mindmap', 'timeline'
        ]
    
    def extract(self, content: str) -> List[Dict[str, str]]:
        """
        Extract all mermaid diagrams from markdown content
        
        Args:
            content: Markdown content as string
            
        Returns:
            List of dicts with keys: 'code', 'type', 'index', 'preview'
        """
        if not content:
            return []
        
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
        
        self.logger.info(f"Extracted {len(diagrams)} mermaid diagrams")
        return diagrams
    
    def extract_from_file(self, file_path: str) -> List[Dict[str, str]]:
        """
        Extract diagrams from a markdown file
        
        Args:
            file_path: Path to markdown file
            
        Returns:
            List of extracted diagrams
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.extract(content)
        except Exception as e:
            self.logger.error(f"Failed to extract from file {file_path}: {str(e)}")
            return []
    
    def _detect_diagram_type(self, code: str) -> str:
        """
        Detect the type of mermaid diagram from code
        
        Args:
            code: Mermaid diagram code
            
        Returns:
            Diagram type string or 'unknown'
        """
        if not code:
            return 'unknown'
        
        first_line = code.split('\n')[0].strip().lower()
        
        # Check against known diagram types
        for diagram_type in self.diagram_types:
            if diagram_type.lower() in first_line:
                return diagram_type
        
        # Check for graph (older syntax)
        if 'graph' in first_line:
            return 'flowchart'
        
        # Check for sequence (alternate syntax)
        if 'sequence' in first_line:
            return 'sequenceDiagram'
        
        return 'unknown'
    
    def get_diagram_info(self, diagram: Dict[str, str]) -> Dict[str, any]:
        """
        Get detailed information about a diagram
        
        Args:
            diagram: Diagram dict from extract()
            
        Returns:
            Dict with detailed info
        """
        if not diagram:
            return {}
        
        code = diagram.get('code', '')
        lines = code.split('\n')
        
        # Count nodes/items based on diagram type
        node_count = 0
        if diagram['type'] == 'flowchart' or diagram['type'] == 'graph':
            # Count arrow patterns
            node_count = len(re.findall(r'-->|->|---', code))
        elif diagram['type'] == 'sequenceDiagram':
            # Count participants and interactions
            node_count = len(re.findall(r'->>|-->>', code))
        elif diagram['type'] == 'classDiagram':
            # Count class definitions
            node_count = len(re.findall(r'class\s+\w+', code))
        
        return {
            'type': diagram['type'],
            'lines': len(lines),
            'characters': len(code),
            'node_count': node_count,
            'has_syntax_errors': self._check_syntax_errors(code)
        }
    
    def _check_syntax_errors(self, code: str) -> bool:
        """
        Basic syntax check for common mermaid errors
        
        Args:
            code: Mermaid diagram code
            
        Returns:
            True if potential errors found
        """
        errors = []
        
        # Check for unmatched brackets
        if code.count('[') != code.count(']'):
            errors.append('Unmatched brackets')
        
        # Check for unmatched braces
        if code.count('{') != code.count('}'):
            errors.append('Unmatched braces')
        
        # Check for empty lines in critical areas
        lines = code.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith(('graph', 'flowchart', 'sequenceDiagram', 'classDiagram')):
                if stripped.startswith('-->') and i > 0 and not lines[i-1].strip():
                    errors.append('Arrow without source')
        
        return len(errors) > 0
    
    def replace_with_images(self, content: str, renderer, output_format: str = 'png') -> str:
        """
        Replace mermaid code blocks with embedded images
        
        Args:
            content: Markdown content
            renderer: MermaidRenderer instance
            output_format: Output format ('png' or 'svg')
            
        Returns:
            Modified content with image tags
        """
        import base64
        
        def replace_match(match):
            code = match.group(1).strip()
            try:
                from logic.mermaid_renderer import MermaidFormat
                format_type = MermaidFormat.PNG if output_format == 'png' else MermaidFormat.SVG
                
                # Render diagram
                image_data = renderer.render(code, format_type)
                img_b64 = base64.b64encode(image_data).decode('utf-8')
                mime_type = 'image/png' if output_format == 'png' else 'image/svg+xml'
                return f'<img src="data:{mime_type};base64,{img_b64}" alt="Mermaid Diagram">'
            except Exception as e:
                self.logger.error(f"Failed to render diagram: {str(e)}")
                return f'<div class="mermaid-error">Failed to render: {str(e)}</div>'
        
        return re.sub(self.mermaid_pattern, replace_match, content, flags=re.DOTALL)
    
    def get_all_diagram_types(self) -> List[str]:
        """
        Get list of supported diagram types
        
        Returns:
            List of diagram type strings
        """
        return self.diagram_types.copy()
    
