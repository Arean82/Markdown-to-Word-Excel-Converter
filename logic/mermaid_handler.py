# logic/mermaid_handler.py
# Mermaid Handler - Handles mermaid file operations and diagram management

import os
import re
from pathlib import Path
from typing import Optional, Dict, Any, List

from core.logger import Logger


class MermaidHandler:
    """Handler for mermaid file operations"""
    
    def __init__(self):
        self.logger = Logger()
        self.current_file = None
        self.content = None
        self.diagrams = []
    
    def load_file(self, file_path: str) -> bool:
        """Load mermaid file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
            self.current_file = file_path
            self.logger.info(f"Loaded mermaid file: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load mermaid file: {str(e)}")
            return False
    
    def get_preview(self, file_path: str, max_chars: int = 1000, max_lines: int = 30) -> str:
        """Get preview of mermaid file"""
        if not self.load_file(file_path):
            return f"Error loading file: {file_path}"
        
        lines = self.content.split('\n')
        preview_lines = lines[:max_lines]
        preview = '\n'.join(preview_lines)
        
        if len(self.content) > max_chars:
            preview += "\n\n... (file truncated for preview)"
        
        return preview
    
    def extract_diagrams(self, content: str = None) -> List[Dict[str, Any]]:
        """Extract mermaid diagrams from content"""
        if content is None:
            content = self.content
        
        if not content:
            return []
        
        # For pure mermaid file, treat entire content as one diagram
        if self.current_file and self.current_file.endswith('.mermaid'):
            diagram_type = self._detect_diagram_type(content)
            return [{
                'index': 0,
                'code': content.strip(),
                'type': diagram_type,
                'preview': content[:200] + ('...' if len(content) > 200 else '')
            }]
        
        # For markdown with mermaid blocks
        pattern = r'```mermaid\s*\n(.*?)\n```'
        matches = re.findall(pattern, content, re.DOTALL)
        
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
        
        self.diagrams = diagrams
        return diagrams
    
    def _detect_diagram_type(self, code: str) -> str:
        """Detect diagram type from mermaid code"""
        first_line = code.split('\n')[0].strip().lower()
        
        diagram_types = [
            'flowchart', 'sequenceDiagram', 'classDiagram', 
            'stateDiagram', 'erDiagram', 'gantt', 'pie', 
            'gitGraph', 'journey', 'quadrantChart', 'requirementDiagram'
        ]
        
        for dt in diagram_types:
            if dt.lower() in first_line:
                return dt
        
        # Check for common keywords
        if 'graph' in first_line:
            return 'flowchart'
        elif 'sequence' in first_line:
            return 'sequenceDiagram'
        elif 'class' in first_line:
            return 'classDiagram'
        
        return 'unknown'
    
    def get_diagram(self, index: int) -> Optional[Dict[str, Any]]:
        """Get diagram by index"""
        if 0 <= index < len(self.diagrams):
            return self.diagrams[index]
        return None
    
    def get_diagram_count(self) -> int:
        """Get number of diagrams"""
        return len(self.diagrams)
    
    def get_file_info(self) -> Dict[str, Any]:
        """Get information about loaded file"""
        if not self.current_file or not self.content:
            return {}
        
        lines = self.content.split('\n')
        
        return {
            'path': self.current_file,
            'name': os.path.basename(self.current_file),
            'size': os.path.getsize(self.current_file),
            'lines': len(lines),
            'chars': len(self.content),
            'diagram_count': len(self.diagrams)
        }
    
    def validate_mermaid_syntax(self, code: str) -> tuple:
        """Basic validation of mermaid syntax"""
        if not code or not code.strip():
            return False, "Empty diagram code"
        
        first_line = code.split('\n')[0].strip().lower()
        
        valid_starts = [
            'graph', 'flowchart', 'sequenceDiagram', 'classDiagram',
            'stateDiagram', 'erDiagram', 'gantt', 'pie', 'gitGraph',
            'journey', 'quadrantChart', 'requirementDiagram'
        ]
        
        is_valid = any(first_line.startswith(vs) for vs in valid_starts)
        
        if not is_valid:
            return False, f"Unknown diagram type. Expected one of: {', '.join(valid_starts[:5])}..."
        
        return True, "Valid mermaid syntax"