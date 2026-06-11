# logic/md_converter.py
# Markdown Converter - Worker thread for Word/Excel conversion

import os
import tempfile
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from core.logger import Logger


class ConversionWorker(QThread):
    """Worker thread for markdown conversion to keep UI responsive"""
    
    @staticmethod
    def fix_markdown_tables(content: str) -> str:
        """Ensure tables have a preceding blank line so strict parsers recognize them."""
        lines = content.split('\n')
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
            
        return '\n'.join(fixed_lines)

    
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, input_file: str, output_file: str, conversion_type: str, use_highlighting: bool = True, paper_size: str = "A4", orientation: str = "Portrait", margin: str = "Normal", custom_margins: dict = None):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.conversion_type = conversion_type
        self.use_highlighting = use_highlighting
        self.paper_size = paper_size
        self.orientation = orientation
        self.margin = margin
        self.custom_margins = custom_margins if custom_margins else {"top": 2.54, "bottom": 2.54, "left": 2.54, "right": 2.54}
        self.logger = Logger()
    
    def run(self):
        """Run conversion in background thread"""
        try:
            self.status.emit("Loading file...")
            self.progress.emit(20)
            
            if self.conversion_type == "Word":
                self.convert_to_word()
            elif self.conversion_type == "Excel":
                self.convert_to_excel()
            elif self.conversion_type == "PDF":
                self.convert_to_pdf()
            else:
                self.finished.emit(False, f"Unknown conversion type: {self.conversion_type}")
                
        except Exception as e:
            self.logger.error(f"Conversion error: {str(e)}")
            self.finished.emit(False, str(e))
    
    def convert_to_pdf(self):
        """Convert markdown to PDF using Pandoc (HTML) + Playwright"""
        try:
            import pypandoc
            from playwright.sync_api import sync_playwright
            
            self.logger.info(f"Starting PDF conversion: {self.input_file}")
            self.status.emit("Converting Markdown to HTML...")
            self.progress.emit(30)
            
            extra_args = ['--standalone']
            if not self.use_highlighting:
                extra_args.append('--no-highlight')
                
            # Read the markdown file
            with open(self.input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Write to a temporary file
            temp_md = Path(tempfile.gettempdir()) / f"temp_{Path(self.input_file).stem}.md"
            with open(temp_md, 'w', encoding='utf-8') as f:
                f.write(self.fix_markdown_tables(content))
            
            try:
                html_content = pypandoc.convert_file(str(temp_md), 'html', format='gfm', extra_args=extra_args)
            finally:
                # Clean up temp file
                if os.path.exists(temp_md):
                    os.unlink(str(temp_md))
                    
            # Inject CSS to remove unwanted spacing at the top of the document and fix tables
            css_fix = """<style>
            body { margin-top: 0 !important; padding-top: 0 !important; }
            body > *:first-child { margin-top: 0 !important; padding-top: 0 !important; }
            table { width: 100% !important; max-width: 100% !important; table-layout: fixed !important; word-wrap: break-word !important; overflow-wrap: break-word !important; }
            th, td { word-break: break-word !important; white-space: normal !important; overflow: hidden !important; }
            </style></head>"""
            html_content = html_content.replace("</head>", css_fix)
            
            self.status.emit("Rendering PDF with Playwright...")
            self.progress.emit(60)
            
            # Map margins
            if self.margin == "Custom":
                unit = "in" if self.custom_margins.get("is_inch", False) else "cm"
                margin_dict = {
                    "top": f"{self.custom_margins.get('top', 2.54)}{unit}",
                    "right": f"{self.custom_margins.get('right', 2.54)}{unit}",
                    "bottom": f"{self.custom_margins.get('bottom', 2.54)}{unit}",
                    "left": f"{self.custom_margins.get('left', 2.54)}{unit}"
                }
            else:
                margin_px = "1in"
                if self.margin == "Narrow": margin_px = "0.5in"
                elif self.margin == "Wide": margin_px = "2in"
                
                margin_dict = {
                    "top": margin_px, "right": margin_px, "bottom": margin_px, "left": margin_px
                }
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_content(html_content)
                # Ensure the page formatting applies correctly
                page.pdf(
                    path=self.output_file,
                    format=self.paper_size,
                    landscape=(self.orientation == "Landscape"),
                    margin=margin_dict,
                    print_background=True
                )
                browser.close()
                
            self.progress.emit(100)
            status = "with syntax highlighting" if self.use_highlighting else ""
            self.logger.info(f"PDF conversion successful: {self.output_file}")
            self.finished.emit(True, f"Successfully converted to PDF {status}:\n{self.output_file}")
            
        except Exception as e:
            self.logger.error(f"PDF conversion failed: {str(e)}")
            self.finished.emit(False, f"PDF conversion failed: {str(e)}\n\n(If it says browser executable doesn't exist, try running 'playwright install chromium' in your terminal)")

    def convert_to_word(self):
        """Convert markdown to Word using pypandoc_binary"""
        try:
            import pypandoc
            
            self.logger.info(f"Starting Word conversion: {self.input_file}")
            self.status.emit("Converting to Word using Pandoc...")
            self.progress.emit(30)
            
            self.status.emit("Running Pandoc conversion...")
            self.progress.emit(50)
            
            # Read the markdown file
            with open(self.input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Write to a temporary file
            temp_md = Path(tempfile.gettempdir()) / f"temp_{Path(self.input_file).stem}.md"
            with open(temp_md, 'w', encoding='utf-8') as f:
                f.write(self.fix_markdown_tables(content))
            
            try:
                extra_args = ['--standalone']
                if not self.use_highlighting:
                    extra_args.append('--no-highlight')
                    
                # Convert the temporary file
                pypandoc.convert_file(
                    str(temp_md),
                    'docx',
                    format='gfm',
                    outputfile=self.output_file,
                    extra_args=extra_args
                )
            finally:
                # Clean up temp file
                if os.path.exists(temp_md):
                    os.unlink(str(temp_md))
            
            self.status.emit("Applying page formatting...")
            self.progress.emit(80)
            
            try:
                import docx
                from docx.shared import Inches, Mm
                from docx.enum.section import WD_ORIENT
                
                doc = docx.Document(self.output_file)
                for section in doc.sections:
                    # Apply Paper Size
                    if self.paper_size == "A4":
                        page_width = Mm(210)
                        page_height = Mm(297)
                    elif self.paper_size == "Legal":
                        page_width = Inches(8.5)
                        page_height = Inches(14)
                    else: # Letter
                        page_width = Inches(8.5)
                        page_height = Inches(11)
                    
                    # Apply Orientation
                    if self.orientation == "Landscape":
                        section.orientation = WD_ORIENT.LANDSCAPE
                        section.page_width = page_height
                        section.page_height = page_width
                    else:
                        section.orientation = WD_ORIENT.PORTRAIT
                        section.page_width = page_width
                        section.page_height = page_height
                    
                    # Apply Margins
                    if self.margin == "Narrow":
                        m = Inches(0.5)
                        section.top_margin = m
                        section.bottom_margin = m
                        section.left_margin = m
                        section.right_margin = m
                    elif self.margin == "Wide":
                        section.top_margin = Inches(1)
                        section.bottom_margin = Inches(1)
                        section.left_margin = Inches(2)
                        section.right_margin = Inches(2)
                    elif self.margin == "Custom":
                        from docx.shared import Cm, Inches
                        is_inch = self.custom_margins.get("is_inch", False)
                        unit_func = Inches if is_inch else Cm
                        section.top_margin = unit_func(self.custom_margins.get("top", 2.54))
                        section.bottom_margin = unit_func(self.custom_margins.get("bottom", 2.54))
                        section.left_margin = unit_func(self.custom_margins.get("left", 2.54))
                        section.right_margin = unit_func(self.custom_margins.get("right", 2.54))
                    else: # Normal
                        section.top_margin = Inches(1)
                        section.bottom_margin = Inches(1)
                        section.left_margin = Inches(1)
                        section.right_margin = Inches(1)
                        
                # Fix tables being cut off: Auto resize and word wrap
                from docx.enum.table import WD_TABLE_ALIGNMENT
                from docx.oxml.shared import OxmlElement
                from docx.oxml.ns import qn
                
                for table in doc.tables:
                    table.alignment = WD_TABLE_ALIGNMENT.CENTER
                    table.autofit = False
                    table.allow_autofit = False
                    
                    # Explicitly calculate column widths so it never cuts off
                    page_width = section.page_width - section.left_margin - section.right_margin
                    if table.columns and len(table.columns) > 0:
                        col_width = int(page_width / len(table.columns))
                        
                        tblGrid = table._tbl.find(qn('w:tblGrid'))
                        if tblGrid is not None:
                            for gridCol in tblGrid.findall(qn('w:gridCol')):
                                gridCol.set(qn('w:w'), str(col_width))
                        
                        from docx.shared import Pt
                        for row in table.rows:
                            for cell in row.cells:
                                cell.width = col_width
                                tcPr = cell._tc.get_or_add_tcPr()
                                tcW = tcPr.find(qn('w:tcW'))
                                if tcW is not None:
                                    tcW.set(qn('w:type'), 'dxa')
                                    tcW.set(qn('w:w'), str(col_width))
                                    
                                # Reduce font size of all text in the cell to fit better
                                for paragraph in cell.paragraphs:
                                    for run in paragraph.runs:
                                        current_size_pt = run.font.size.pt if run.font.size else 11.0
                                        new_size_pt = min(9.0, current_size_pt - 2.0)
                                        run.font.size = Pt(new_size_pt)

                # Remove empty paragraphs at the beginning of the document
                while doc.paragraphs and not doc.paragraphs[0].text.strip():
                    p = doc.paragraphs[0]._element
                    p.getparent().remove(p)
                    # p._p = p._element = None (This causes AttributeError sometimes, so just remove the XML element)
                    
                doc.save(self.output_file)
            except ImportError:
                self.logger.warning("python-docx not installed, skipping page formatting")
            except Exception as format_err:
                self.logger.warning(f"Error applying page formatting: {format_err}")
            
            self.progress.emit(100)
            status = "with syntax highlighting" if self.use_highlighting else ""
            self.logger.info(f"Word conversion successful: {self.output_file}")
            self.finished.emit(True, f"Successfully converted to Word {status}:\n{self.output_file}")
            
        except Exception as e:
            self.logger.error(f"Word conversion failed: {str(e)}")
            self.finished.emit(False, f"Word conversion failed: {str(e)}")
    
    def convert_to_excel(self):
        """Convert markdown to Excel using pandas + openpyxl + BeautifulSoup + pytablewriter"""
        try:
            import markdown
            from bs4 import BeautifulSoup
            import openpyxl
            from openpyxl.styles import Font, Alignment
            from openpyxl.utils import get_column_letter
            
            try:
                import pytablewriter
                PYTABLEWRITER_AVAILABLE = True
            except ImportError:
                PYTABLEWRITER_AVAILABLE = False
                self.logger.warning("pytablewriter not available")
            
            self.logger.info(f"Starting Excel conversion: {self.input_file}")
            self.status.emit("Converting to Excel...")
            self.progress.emit(30)
            
            # Read markdown
            with open(self.input_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Convert to HTML
            md_content = self.fix_markdown_tables(md_content)
            html = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
            self.logger.info("Converted markdown to HTML, looking for tables")
            
            # Parse HTML and find tables
            soup = BeautifulSoup(html, 'html.parser')
            tables = soup.find_all('table')
            self.logger.info(f"Found {len(tables)} table(s)")
            
            if tables:
                # Process tables with formatting and merged cells
                self.status.emit(f"Found {len(tables)} tables, converting with formatting...")
                self.progress.emit(50)
                
                workbook = openpyxl.Workbook()
                
                for table_idx, table in enumerate(tables, 1):
                    self.status.emit(f"Processing table {table_idx}...")
                    self.logger.info(f"Processing table {table_idx}")
                    
                    # Create sheet
                    sheet_name = f'Table_{table_idx}' if len(tables) > 1 else 'Sheet1'
                    sheet_name = sheet_name[:31]
                    
                    if table_idx == 1:
                        worksheet = workbook.active
                        worksheet.title = sheet_name
                    else:
                        worksheet = workbook.create_sheet(title=sheet_name)
                    
                    # Track occupied cells for rowspan/colspan
                    occupied = {}
                    
                    # Process rows
                    rows = table.find_all('tr')
                    for r_idx, tr in enumerate(rows, 1):
                        c_idx = 1
                        for td in tr.find_all(['td', 'th']):
                            # Skip cells already covered by previous rowspan
                            while (r_idx, c_idx) in occupied:
                                c_idx += 1
                            
                            # Get cell properties
                            rowspan = int(td.get('rowspan', 1))
                            colspan = int(td.get('colspan', 1))
                            cell_html = str(td)
                            cell_text = td.get_text().strip()
                            
                            # Write value to cell
                            val = cell_text
                            if val.isdigit():
                                val = int(val)
                            else:
                                try:
                                    val = float(val)
                                except ValueError:
                                    pass
                            
                            cell_obj = worksheet.cell(row=r_idx, column=c_idx, value=val)
                            
                            # Handle merged cells
                            if rowspan > 1 or colspan > 1:
                                last_row = r_idx + rowspan - 1
                                last_col = c_idx + colspan - 1
                                worksheet.merge_cells(
                                    start_row=r_idx, start_column=c_idx,
                                    end_row=last_row, end_column=last_col
                                )
                                
                                # Mark all cells in merge range as occupied
                                for r in range(r_idx, last_row + 1):
                                    for c in range(c_idx, last_col + 1):
                                        occupied[(r, c)] = True
                            
                            # Check for bold formatting
                            is_bold = (
                                '**' in cell_html or 
                                '<strong>' in cell_html or 
                                '<b>' in cell_html or 
                                td.name == 'th'
                            )
                            
                            # Check for italic formatting
                            is_italic = (
                                ('*' in cell_html and '**' not in cell_html) or
                                '<em>' in cell_html or
                                '<i>' in cell_html
                            )
                            
                            # Apply bold/italic
                            if is_bold and is_italic:
                                cell_obj.font = Font(bold=True, italic=True)
                            elif is_bold:
                                cell_obj.font = Font(bold=True)
                            elif is_italic:
                                cell_obj.font = Font(italic=True)
                            
                            # Get alignment from style or align attribute
                            align_attr = td.get('align', '').lower()
                            style_attr = td.get('style', '').lower()
                            
                            if align_attr == 'center' or 'text-align: center' in style_attr:
                                cell_obj.alignment = Alignment(horizontal="center")
                            elif align_attr == 'right' or 'text-align: right' in style_attr:
                                cell_obj.alignment = Alignment(horizontal="right")
                            elif align_attr == 'left' or 'text-align: left' in style_attr:
                                cell_obj.alignment = Alignment(horizontal="left")
                            
                            # Auto-adjust column width
                            if len(cell_text) > 0:
                                col_letter = get_column_letter(c_idx)
                                if col_letter in worksheet.column_dimensions:
                                    current_width = worksheet.column_dimensions[col_letter].width or 0
                                else:
                                    current_width = 0
                                new_width = max(current_width, len(cell_text) + 2)
                                worksheet.column_dimensions[col_letter].width = min(new_width, 50)
                            
                            # Move to next column
                            c_idx += colspan
                workbook.save(self.output_file)
                
                self.progress.emit(100)
                self.logger.info(f"Excel conversion successful: {len(tables)} tables to {self.output_file}")
                self.finished.emit(True, f"Successfully converted {len(tables)} table(s) to Excel:\n{self.output_file}")
                return
            
            # No tables found, try pytablewriter for structured data
            if PYTABLEWRITER_AVAILABLE:
                self.status.emit("No tables found, trying pytablewriter for structured data...")
                self.logger.info("No tables found, trying pytablewriter")
                
                # Parse markdown for lists and key-value pairs
                lines = md_content.split('\n')
                data = []
                for line in lines[:200]:
                    if ':' in line and not line.startswith('#'):
                        parts = line.split(':', 1)
                        key = parts[0].strip()
                        # Strict check: key must not be too long, and should not be a normal sentence with spaces
                        if len(key) < 40 and not ' ' in key.strip('-* '):
                            data.append([key.strip('-* '), parts[1].strip()])
                    elif line.startswith('- ') or line.startswith('* '):
                        data.append(['List Item', line[2:].strip()])
                
                if data:
                    writer = pytablewriter.ExcelXlsxTableWriter()
                    writer.open(self.output_file)
                    writer.headers = ['Key', 'Value']
                    writer.value_matrix = data
                    writer.write_table()
                    writer.close()
                    
                    self.progress.emit(100)
                    self.logger.info(f"Pytablewriter conversion successful: {self.output_file}")
                    self.finished.emit(True, f"Converted structured data to Excel using pytablewriter:\n{self.output_file}")
                    return
            
            self.logger.warning("No tables or structured data found")
            self.finished.emit(False, "No tables or structured data found in markdown file")
            
        except Exception as e:
            self.logger.error(f"Excel conversion failed: {str(e)}")
            self.finished.emit(False, f"Excel conversion failed: {str(e)}")