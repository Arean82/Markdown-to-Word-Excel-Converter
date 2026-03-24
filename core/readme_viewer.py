# core/readme_viewer.py
# README Viewer Dialog for Markdown Converter Application

from PyQt6.QtWidgets import QDialog
from PyQt6.uic import loadUi
from pathlib import Path
import markdown


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
        base_dir = Path(__file__).parent.parent
        possible_names = ["README.md", "README", "Readme.md", "readme.md"]
        
        content = "README file not found."
        
        for name in possible_names:
            path = base_dir / name
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        md_content = f.read()
                    
                    # Convert markdown to HTML
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