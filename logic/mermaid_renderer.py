# logic/mermaid_renderer.py
# Mermaid Renderer - Renders mermaid diagrams using Playwright

import os
import tempfile
from pathlib import Path
from enum import Enum
from typing import Optional, Union

from core.logger import Logger


class MermaidFormat(Enum):
    """Output formats for mermaid diagrams"""
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    HTML = "html"


class MermaidBackend(Enum):
    """Available rendering backends"""
    MERMAID_PY = "mermaid_py"    # Fast, primary
    PLAYWRIGHT = "playwright"     # Slower, fallback


class MermaidRenderer:
    """Render mermaid diagrams using mermaid-py (fast) with Playwright fallback"""
    
    def __init__(self, backend: MermaidBackend = MermaidBackend.MERMAID_PY):
        self.backend = backend
        self.logger = Logger()
        self._playwright_available = None
        self._mermaid_py_available = None
    
    def _check_mermaid_py(self) -> bool:
        """Check if mermaid-py is available"""
        if self._mermaid_py_available is not None:
            return self._mermaid_py_available
        
        try:
            import mermaid
            self._mermaid_py_available = True
            self.logger.info("mermaid-py backend available (fast)")
            return True
        except ImportError:
            self._mermaid_py_available = False
            self.logger.warning("mermaid-py not installed")
            return False
    
    def _check_playwright(self) -> bool:
        """Check if playwright is available (slower fallback)"""
        if self._playwright_available is not None:
            return self._playwright_available
        
        try:
            from playwright.sync_api import sync_playwright
            self._playwright_available = True
            self.logger.info("Playwright backend available (fallback)")
            return True
        except ImportError:
            self._playwright_available = False
            self.logger.warning("Playwright not installed")
            return False
    
    def render(self, 
               mermaid_code: str,
               output_format: MermaidFormat = MermaidFormat.PNG,
               output_path: Optional[str] = None,
               width: int = 800,
               height: int = 600,
               theme: str = "default") -> Union[bytes, str]:
        """
        Render mermaid diagram using mermaid-py (fast) with Playwright fallback
        """
        # Try mermaid-py first (faster)
        if self.backend == MermaidBackend.MERMAID_PY and self._check_mermaid_py():
            try:
                return self._render_with_mermaid_py(
                    mermaid_code, output_format, output_path, width, height, theme
                )
            except Exception as e:
                self.logger.warning(f"mermaid-py render failed: {e}")
                # Fallback to Playwright
                if self._check_playwright():
                    self.logger.info("Falling back to Playwright")
                    return self._render_with_playwright(
                        mermaid_code, output_format, output_path, width, height, theme
                    )
                raise
        
        # Try Playwright
        if self._check_playwright():
            return self._render_with_playwright(
                mermaid_code, output_format, output_path, width, height, theme
            )
        
        raise Exception(
            "No mermaid renderer available. Install mermaid-py (fast):\n"
            "pip install mermaid-py\n\n"
            "Or install playwright (fallback):\n"
            "pip install playwright\n"
            "playwright install chromium"
        )
    
    def _render_with_mermaid_py(self, code, output_format, output_path, width, height, theme):
        """Render using mermaid-py (fast)"""
        import mermaid
        
        # Map theme
        theme_map = {
            'default': 'default',
            'dark': 'dark',
            'forest': 'forest',
            'neutral': 'neutral'
        }
        mermaid_theme = theme_map.get(theme, 'default')
        
        if output_format == MermaidFormat.PNG:
            img_data = mermaid.render(code, theme=mermaid_theme)
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(img_data)
                return output_path
            return img_data
        
        elif output_format == MermaidFormat.SVG:
            svg_data = mermaid.render(code, theme=mermaid_theme, format='svg')
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(svg_data)
                return output_path
            return svg_data.encode('utf-8')
        
        else:
            # For PDF/HTML, fallback to playwright
            raise Exception(f"Format {output_format.value} not supported by mermaid-py, use Playwright")
    
    def _render_with_playwright(self, code, output_format, output_path, width, height, theme):
        """Render using Playwright (slower fallback)"""
        from playwright.sync_api import sync_playwright
        
        html_content = self._generate_mermaid_html(code, width, height, theme)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': width, 'height': height})
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                temp_html = f.name
            
            try:
                page.goto(f'file://{temp_html}')
                page.wait_for_selector('.mermaid svg', timeout=10000)
                
                if output_format == MermaidFormat.SVG:
                    svg_content = page.locator('.mermaid').inner_html()
                    if output_path:
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(svg_content)
                        return output_path
                    return svg_content.encode('utf-8')
                
                elif output_format == MermaidFormat.PNG:
                    element = page.locator('.mermaid')
                    screenshot = element.screenshot()
                    if output_path:
                        with open(output_path, 'wb') as f:
                            f.write(screenshot)
                        return output_path
                    return screenshot
                
                elif output_format == MermaidFormat.PDF:
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
        bg_color = '#1e1e1e' if theme == 'dark' else '#ffffff'
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background-color: {bg_color};
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        .mermaid {{
            width: {width}px;
            min-height: {height}px;
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
    
    