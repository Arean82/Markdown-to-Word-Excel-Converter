# preview_thread.py - Worker thread for generating markdown preview to keep UI responsive
# This thread reads the markdown file, parses it to HTML, extracts tables info, and sends the data back to the preview dialog for display. It uses markdown extensions for better parsing and can optionally include syntax highlighting for code blocks.   

from PyQt6.QtCore import QThread, pyqtSignal
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from bs4 import BeautifulSoup
import pandas as pd

class PreviewWorker(QThread):
    """Worker thread for preview to keep UI responsive"""
    preview_ready = pyqtSignal(dict)  # Emits preview data
    error = pyqtSignal(str)
    
    def __init__(self, file_path, use_highlighting=True):
        super().__init__()
        self.file_path = file_path
        self.use_highlighting = use_highlighting
    
    def run(self):
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
            
            # Extract tables info
            soup = BeautifulSoup(html_content, 'html.parser')
            tables = soup.find_all('table')
            table_info = []
            
            for i, table in enumerate(tables, 1):
                try:
                    df = pd.read_html(str(table))[0]
                    table_info.append(f"Table {i}: {df.shape[0]} rows × {df.shape[1]} columns")
                except:
                    table_info.append(f"Table {i}: (unable to parse)")
            
            # Prepare preview data
            preview_data = {
                'raw': raw_content,
                'html': html_content,
                'tables': table_info,
                'stats': {
                    'lines': len(raw_content.split('\n')),
                    'chars': len(raw_content),
                    'tables': len(tables)
                }
            }
            
            self.preview_ready.emit(preview_data)
            
        except Exception as e:
            self.error.emit(str(e))