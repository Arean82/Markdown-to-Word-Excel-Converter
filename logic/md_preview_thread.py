# logic/md_preview_thread.py
# Markdown Preview Thread - Worker thread for generating markdown preview

from PyQt6.QtCore import QThread, pyqtSignal
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from bs4 import BeautifulSoup
import pandas as pd
import re

from core.logger import Logger


class MarkdownPreviewThread(QThread):
    """Worker thread for markdown preview to keep UI responsive"""
    
    preview_ready = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, file_path: str, use_highlighting: bool = True):
        super().__init__()
        self.file_path = file_path
        self.use_highlighting = use_highlighting
        self.logger = Logger()
    
    def run(self):
        """Generate preview in background thread"""
        try:
            # Read file
            with open(self.file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            
            # Parse markdown to HTML
            extensions = [
                'tables',
                'fenced_code',
                'nl2br',
                'sane_lists'
            ]
            
            if self.use_highlighting:
                extensions.append(
                    CodeHiliteExtension(
                        css_class='highlight',
                        use_pygments=True,
                        pygments_style='monokai'
                    )
                )
            
            html_content = markdown.markdown(raw_content, extensions=extensions)
            
            # Check for mermaid diagrams
            mermaid_pattern = r'```mermaid\s*\n.*?\n```'
            has_mermaid = bool(re.search(mermaid_pattern, raw_content, re.DOTALL))
            mermaid_count = len(re.findall(mermaid_pattern, raw_content, re.DOTALL))
            
            # Extract tables info
            soup = BeautifulSoup(html_content, 'html.parser')
            tables = soup.find_all('table')
            table_info = []
            
            for i, table in enumerate(tables, 1):
                try:
                    df = pd.read_html(str(table))[0]
                    table_info.append(f"Table {i}: {df.shape[0]} rows × {df.shape[1]} columns")
                except Exception as e:
                    self.logger.warning(f"Failed to parse table {i}: {str(e)}")
                    table_info.append(f"Table {i}: (unable to parse)")
            
            # Prepare preview data
            preview_data = {
                'raw': raw_content,
                'html': html_content,
                'tables': table_info,
                'has_mermaid': has_mermaid,
                'mermaid_count': mermaid_count,
                'stats': {
                    'lines': len(raw_content.split('\n')),
                    'chars': len(raw_content),
                    'tables': len(tables)
                }
            }
            
            self.preview_ready.emit(preview_data)
            self.logger.info(f"Markdown preview generated for: {self.file_path}")
            
        except Exception as e:
            self.logger.error(f"Markdown preview error: {str(e)}")
            self.error.emit(str(e))