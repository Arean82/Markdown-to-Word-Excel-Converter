# ==================================================================
# File: core/readme_viewer.py
# Description: README Viewer Dialog for Markdown Converter Application
# ==================================================================

from PyQt6.QtWidgets import QDialog
from PyQt6.uic import loadUi
from pathlib import Path
import markdown
import sys


class ReadmeViewerDialog(QDialog):
    """Dialog to display README documentation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Load UI
        ui_path = Path(__file__).parent.parent / 'ui' / 'readme_viewer.ui'
        loadUi(str(ui_path), self)
        
        # Connect close button
        self.closeBtn.clicked.connect(self.accept)
        
        # Load README
        self.load_readme()
    
    def load_readme(self):
        """Load and render README file"""
        if hasattr(sys, '_MEIPASS'):
            base_dir = Path(sys._MEIPASS)
        else:
            base_dir = Path(__file__).parent.parent
            
        # Tell the text browser where to look for local assets (like SVG badges)
        self.textBrowser.setSearchPaths([str(base_dir)])
        
        possible_names = ["README.md", "README", "Readme.md", "readme.md"]
        
        content = "README file not found."
        
        for name in possible_names:
            path = base_dir / name
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        md_content = f.read()
                    
                    # FAIL-SAFE: Encode SVGs to Base64 to bypass PyQt6 QTextBrowser caching bugs
                    import base64
                    import re
                    
                    def replace_svg_with_base64(match):
                        img_path = base_dir / match.group(1)
                        if img_path.exists():
                            try:
                                with open(img_path, "rb") as svg_file:
                                    b64_data = base64.b64encode(svg_file.read()).decode('utf-8')
                                return f'](data:image/svg+xml;base64,{b64_data})'
                            except Exception:
                                pass
                        return match.group(0)
                        
                    md_content = re.sub(r'\]\((assets/[^)]+\.svg)\)', replace_svg_with_base64, md_content)
                    
                    # Fix markdown tables without preceding blank lines
                    lines = md_content.split('\n')
                    fixed_lines = []
                    in_code_block = False
                    for i, line in enumerate(lines):
                        if line.strip().startswith('```'):
                            in_code_block = not in_code_block
                        if not in_code_block and line.strip().startswith('|'):
                            if i > 0:
                                prev_line = lines[i-1].strip()
                                if prev_line and not prev_line.startswith('|') and not prev_line.startswith('```'):
                                    fixed_lines.append('')
                        fixed_lines.append(line)
                    md_content = '\n'.join(fixed_lines)
                    html = markdown.markdown(md_content, extensions=["fenced_code", "tables"])
                    
                    # Wrap in styled HTML
                    content = f"""
                    <html>
                    <head>
                        <style>
                            body {{
                                font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial;
                                margin: 40px;
                                background-color: #1e1e1e;
                                color: #ffffff;
                                line-height: 1.6;
                            }}
                            h1, h2, h3 {{ border-bottom: 1px solid #333; padding-bottom: 10px; color: #ffffff; margin-top: 30px; }}
                            pre {{ background: #2d2d2d; padding: 15px; border-radius: 6px; overflow-x: auto; border: 1px solid #444; }}
                            code {{ background: #2d2d2d; padding: 3px 6px; border-radius: 4px; color: #ce9178; }}
                            table {{ border-collapse: collapse; width: 100%; color: #ffffff; margin: 20px 0; }}
                            th, td {{ border: 1px solid #444; padding: 10px; text-align: left; }}
                            th {{ background-color: #252525; }}
                            a {{ color: #40a9ff; text-decoration: none; }}
                            a:hover {{ text-decoration: underline; }}
                        </style>
                    </head>
                    <body>
                        {html}
                    </body>
                    </html>
                    """
                    break
                except Exception as e:
                    content = f"Error loading README: {str(e)}"
        
        self.textBrowser.setHtml(content)