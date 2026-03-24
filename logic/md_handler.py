# logic/md_handler.py
# Markdown Handler - Handles markdown file operations

import os
import re
from pathlib import Path
from typing import Optional, Dict, Any

from core.logger import Logger


class MarkdownHandler:
    """Handler for markdown file operations"""
    
    def __init__(self):
        self.logger = Logger()
        self.current_file = None
        self.content = None
    
    def load_file(self, file_path: str) -> bool:
        """Load markdown file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
            self.current_file = file_path
            self.logger.info(f"Loaded markdown file: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load markdown file: {str(e)}")
            return False
    
    def get_preview(self, file_path: str, max_chars: int = 5000, max_lines: int = 50) -> str:
        """Get preview of markdown file"""
        if not self.load_file(file_path):
            return f"Error loading file: {file_path}"
        
        lines = self.content.split('\n')
        preview_lines = lines[:max_lines]
        preview = '\n'.join(preview_lines)
        
        if len(self.content) > max_chars:
            preview += "\n\n... (file truncated for preview)"
        
        return preview
    
    def has_mermaid_diagrams(self) -> bool:
        """Check if markdown contains mermaid diagrams"""
        if not self.content:
            return False
        
        pattern = r'```mermaid\s*\n.*?\n```'
        return bool(re.search(pattern, self.content, re.DOTALL))
    
    def extract_mermaid_diagrams(self) -> list:
        """Extract mermaid diagrams from markdown content"""
        if not self.content:
            return []
        
        pattern = r'```mermaid\s*\n(.*?)\n```'
        matches = re.findall(pattern, self.content, re.DOTALL)
        
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
        
        return 'unknown'
    
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
            'has_mermaid': self.has_mermaid_diagrams(),
            'mermaid_count': len(self.extract_mermaid_diagrams())
        }