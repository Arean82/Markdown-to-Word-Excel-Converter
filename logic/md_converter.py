# logic/md_converter.py
# Markdown Converter - Worker thread for Word/Excel conversion

import os
import tempfile
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from core.logger import Logger


class ConversionWorker(QThread):
    """Worker thread for markdown conversion to keep UI responsive"""
    
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, input_file: str, output_file: str, conversion_type: str, use_highlighting: bool = True):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.conversion_type = conversion_type
        self.use_highlighting = use_highlighting
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
            else:
                self.finished.emit(False, f"Unknown conversion type: {self.conversion_type}")
                
        except Exception as e:
            self.logger.error(f"Conversion error: {str(e)}")
            self.finished.emit(False, str(e))
    
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
                f.write(content)
            
            # Convert the temporary file
            pypandoc.convert_file(
                str(temp_md),
                'docx',
                outputfile=self.output_file,
                extra_args=['--standalone']
            )
            
            # Clean up temp file
            os.unlink(str(temp_md))
            
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
            import pandas as pd
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
                
                with pd.ExcelWriter(self.output_file, engine='openpyxl') as writer:
                    for table_idx, table in enumerate(tables, 1):
                        self.status.emit(f"Processing table {table_idx}...")
                        self.logger.info(f"Processing table {table_idx}")
                        
                        # Create sheet
                        sheet_name = f'Table_{table_idx}' if len(tables) > 1 else 'Sheet1'
                        # Initialize sheet with empty DataFrame
                        df_placeholder = pd.DataFrame()
                        df_placeholder.to_excel(writer, sheet_name=sheet_name[:31], index=False)
                        
                        # Get the worksheet
                        workbook = writer.book
                        worksheet = writer.sheets[sheet_name[:31]]
                        
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
                                cell_obj = worksheet.cell(row=r_idx, column=c_idx, value=cell_text)
                                
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
                                
                                # Get alignment from style attribute
                                alignment_style = td.get('style', '')
                                if 'text-align: center' in alignment_style:
                                    cell_obj.alignment = Alignment(horizontal="center")
                                elif 'text-align: right' in alignment_style:
                                    cell_obj.alignment = Alignment(horizontal="right")
                                elif 'text-align: left' in alignment_style:
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
                        
                        # Remove default blank sheet if it exists and we have multiple sheets
                        if "Sheet" in workbook.sheetnames and len(workbook.sheetnames) > 1:
                            workbook.remove(workbook["Sheet"])
                
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
                        data.append([parts[0].strip(), parts[1].strip()])
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