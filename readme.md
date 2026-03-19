
# Markdown to Word/Excel Converter

A professional PyQt6 desktop application designed to bridge the gap between Markdown documentation and office formats. It uses a high-fidelity "Combo" engine to preserve complex table structures that standard converters miss.

## 🚀 Key Features

- 📄 **Word Conversion** – Full document flow using pypandoc_binary (no external Pandoc install required).

- 📊 **Powerhouse Excel Engine** – 
  - **Merged Cell Support**: Full rowspan and colspan mapping.
  - **Rich Formatting**: Preserves bold, italic, and text alignment.
  - **Smart Architecture**: Automatically handles 100+ tables by splitting them into organized Sheets/Tabs.

- 👁️ **Live Preview** – High-speed 50KB buffered preview with three specialized views: Raw, Rendered, and Table Structure.

- 🔗 **Intelligent Fallback** – If no formal tables are detected, it uses pytablewriter to extract lists and key-value pairs.

- 🌓 **Adaptive UI** – Support for System-aware Dark and Light themes.

- 🧵 **Asynchronous Processing** – Entire conversion runs on a worker thread (QThread) to prevent GUI freezing.

## 📖 How the "Combo" Engine Works

Unlike "lightweight" converters, this app uses a multi-stage pipeline to ensure 100% data integrity:

1. **Parsing**: markdown + lxml converts .md into a structured HTML tree.
2. **Mapping**: BeautifulSoup scans the tree for table attributes (rowspan, colspan, style).
3. **Grid Protection**: A custom "Occupied Map" tracks merged cells to prevent data from shifting into the wrong columns.
4. **Styling**: openpyxl applies final font weights, alignments, and auto-adjusts column widths.
5. **Fallback**: If the HTML tree lacks `<table>` tags, the script switches to a regex-based extraction to save lists as spreadsheets.

## 🛠 Installation

### Prerequisites
- Python 3.8 or higher

### Steps

1. Clone or download this repository.

2. Install the verified "Combo Stack" dependencies:

```bash
pip install PyQt6 pypandoc_binary pandas openpyxl beautifulsoup4 markdown "pytablewriter[excel]"
```

## Usage

1. Run the application:
```bash
python main.py
```

2. Click "Browse" to select a Markdown file (.md)
3. Choose conversion type:
   - **Word (.docx)** - Converts entire document
   - **Excel (.xlsx)** - Extracts tables with formatting
4. Toggle syntax highlighting if needed (Word only)
5. Click "Convert Now"
6. Output file saves in the same folder as input

### Preview Feature
- Click "Preview" button to see rendered markdown
- Three tabs: Raw Markdown, Rendered Preview, Detected Tables
- Shows table structure and formatting before conversion

## Excel Conversion Details

When converting to Excel, the application:

- ✅ Extracts **all tables** from the markdown file
- ✅ Preserves **bold** (`**text**` or `<strong>` or `<b>`)
- ✅ Preserves *italic* (`*text*` or `<em>` or `<i>`)
- ✅ Handles **text alignment** (left/center/right)
- ✅ Supports **merged cells** (rowspan/colspan)
- ✅ Auto-adjusts column widths using openpyxl.utils.get_column_letter
- ✅ Creates separate sheets for multiple tables
- ✅ Initializes sheets with empty DataFrame to ensure writer.sheets access
- ✅ Removes default blank "Sheet" automatically when multiple sheets exist
- ✅ Falls back to pytablewriter for structured data if no tables found
- ✅ Uses regex-based extraction for lists and key-value pairs as final fallback

## Requirements

```
PyQt6              - GUI framework
pypandoc_binary    - Markdown to Word conversion (bundles Pandoc)
pandas             - Data manipulation for Excel
openpyxl           - Excel file writing with formatting
markdown           - Markdown to HTML conversion
beautifulsoup4     - HTML parsing for table extraction
lxml               - Fast HTML parsing (pandas dependency)
numpy              - Numerical operations (pandas dependency)
pytablewriter      - Excel writing with formatting support
```

## Project Structure

```
md_converter/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── core/                   # Core UI components
│   ├── main_window.py      # Main window logic (radio buttons)
│   ├── menu.py             # Menu bar creation
│   ├── preview_dialog.py   # Preview dialog
│   ├── preview_thread.py   # Preview worker thread
│   └── readme_viewer.py    # README viewer dialog
├── logic/                  # Business logic
│   └── converter_thread.py # Conversion worker with Combo Engine
├── ui/                     # UI design files
│   ├── ui_mainwindow.ui    # Main window UI (radio buttons)
│   └── preview_dialog.ui   # Preview dialog UI
└── theme/                  # Theme stylesheets
    ├── styles.qss.css      # Dark theme
    └── light_styles.qss.css # Light theme
```

## Troubleshooting

### Word conversion fails
```bash
pip install pypandoc_binary
```

### Excel formatting not preserved
The Combo Engine uses multiple methods:
1. pandas + openpyxl with custom formatting and merged cell support
2. pytablewriter for structured data fallback
3. Regex-based extraction for lists and key-value pairs

### "No tables found" error
- Ensure markdown contains properly formatted tables using `|` syntax
- Check for HTML tables with `<table>` tags
- The fallback will try to extract lists and key-value pairs automatically

### Multiple sheets issue
- The app automatically removes the default "Sheet" if multiple sheets exist
- Sheet names are truncated to 31 characters (Excel limit)

## License

Distributed under the MIT License. See LICENSE for more information.

## Author

Arean Narrayan
