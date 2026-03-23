# core/mermaid/mermaid_renderer.py
"""
Pure Python Mermaid Renderer
Supports multiple backends with Playwright as primary
"""

import os
import sys
import tempfile
import base64
import subprocess
from pathlib import Path
from enum import Enum
from typing import Optional, Union, List, Tuple

class MermaidFormat(Enum):
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    HTML = "html"

class MermaidBackend(Enum):
    PLAYWRIGHT = "playwright"  # Most reliable, renders full JS
    SELENIUM = "selenium"       # Alternative browser automation
    STATIC = "static"           # Only for simple diagrams

class MermaidRenderer:
    """Pure Python mermaid diagram renderer"""
    
    def __init__(self, backend: MermaidBackend = MermaidBackend.PLAYWRIGHT):
        self.backend = backend
        self._playwright_available = None
        self._selenium_available = None
        
    def _check_playwright(self) -> bool:
        """Check if playwright is available"""
        if self._playwright_available is not None:
            return self._playwright_available
        
        try:
            from playwright.sync_api import sync_playwright
            self._playwright_available = True
            return True
        except ImportError:
            self._playwright_available = False
            return False
    
    def _check_selenium(self) -> bool:
        """Check if selenium is available"""
        if self._selenium_available is not None:
            return self._selenium_available
        
        try:
            import selenium
            self._selenium_available = True
            return True
        except ImportError:
            self._selenium_available = False
            return False
    
    def render(self, mermaid_code: str, 
               output_format: MermaidFormat = MermaidFormat.PNG,
               output_path: Optional[str] = None,
               width: int = 800,
               height: int = 600,
               theme: str = "default") -> Union[bytes, str]:
        """
        Render mermaid diagram to specified format
        
        Args:
            mermaid_code: Mermaid diagram code
            output_format: Output format (PNG, SVG, PDF)
            output_path: Optional output file path
            width: Output width in pixels
            height: Output height in pixels
            theme: Theme (default, dark, forest, neutral)
        
        Returns:
            bytes if output_path not specified, else file path
        """
        if self.backend == MermaidBackend.PLAYWRIGHT and self._check_playwright():
            return self._render_with_playwright(
                mermaid_code, output_format, output_path, width, height, theme
            )
        elif self.backend == MermaidBackend.SELENIUM and self._check_selenium():
            return self._render_with_selenium(
                mermaid_code, output_format, output_path, width, height, theme
            )
        else:
            raise Exception(
                "No render backend available. Install playwright:\n"
                "pip install playwright\n"
                "playwright install chromium"
            )
    
    def _render_with_playwright(self, code, output_format, output_path, width, height, theme):
        """Render using Playwright (headless Chromium)"""
        from playwright.sync_api import sync_playwright
        
        html_content = self._generate_mermaid_html(code, width, height, theme)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': width, 'height': height})
            
            # Create temp HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                f.write(html_content)
                temp_html = f.name
            
            try:
                page.goto(f'file://{temp_html}')
                page.wait_for_selector('.mermaid svg', timeout=5000)
                
                if output_format == MermaidFormat.SVG:
                    # Get SVG content
                    svg_content = page.locator('.mermaid').inner_html()
                    if output_path:
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(svg_content)
                        return output_path
                    return svg_content.encode('utf-8')
                
                elif output_format == MermaidFormat.PNG:
                    # Screenshot
                    element = page.locator('.mermaid')
                    screenshot = element.screenshot()
                    if output_path:
                        with open(output_path, 'wb') as f:
                            f.write(screenshot)
                        return output_path
                    return screenshot
                
                elif output_format == MermaidFormat.PDF:
                    # Generate PDF
                    pdf = page.pdf()
                    if output_path:
                        with open(output_path, 'wb') as f:
                            f.write(pdf)
                        return output_path
                    return pdf
                
                elif output_format == MermaidFormat.HTML:
                    if output_path:
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(html_content)
                        return output_path
                    return html_content.encode('utf-8')
                
            finally:
                browser.close()
                os.unlink(temp_html)
    
    def _generate_mermaid_html(self, code: str, width: int, height: int, theme: str) -> str:
        """Generate HTML wrapper for mermaid diagram"""
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background-color: {'#1e1e1e' if theme == 'dark' else '#ffffff'};
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        .mermaid {{
            width: {width}px;
            height: {height}px;
        }}
    </style>
</head>
<body>
    <pre class="mermaid">
        {code}
    </pre>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: '{theme}',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }},
            securityLevel: 'loose'
        }});
    </script>
</body>
</html>"""
    
    def render_to_base64(self, mermaid_code: str, width: int = 800, height: int = 600) -> str:
        """Render diagram and return as base64 string (for embedding)"""
        image_data = self.render(mermaid_code, MermaidFormat.PNG, width=width, height=height)
        return base64.b64encode(image_data).decode('utf-8')