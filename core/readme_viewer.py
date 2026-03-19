import os
import markdown
from pathlib import Path
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton
from PyQt6.QtCore import Qt

class ReadmeViewerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("README - Markdown Converter")
        self.resize(800, 600)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Text browser
        self.text_browser = QTextBrowser()
        self.text_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #1a1a1a;
                color: #d4d4d4;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                font-family: Consolas, Menlo, monospace;
                font-size: 12px;
            }
        """)
        
        # Load README
        self.load_readme()
        
        layout.addWidget(self.text_browser)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.setLayout(layout)
    
    def load_readme(self):
        base_dir = Path(__file__).parent.parent
        possible_names = ["README.md", "README", "Readme.md", "readme.md"]
        
        content = "README file not found."
        
        for name in possible_names:
            path = base_dir / name
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        md_content = f.read()
                    
                    html = markdown.markdown(md_content, extensions=["fenced_code", "tables"])
                    
                    # Wrap in styled HTML
                    content = f"""
                    <html>
                    <head>
                        <style>
                            body {{
                                font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial;
                                margin: 40px;
                                background-color: #1a1a1a;
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
                except Exception:
                    pass
        
        self.text_browser.setHtml(content)