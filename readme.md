
# Markdown to Word/Excel Converter

A professional PyQt6 desktop application designed to bridge the gap between Markdown documentation and office formats. It uses a high-fidelity "Combo" engine to preserve complex table structures that standard converters miss.

## 🚀 Key Features

- 📦 **Batch Conversion** – Select multiple Markdown files and convert them all simultaneously to your target format.
- 📄 **Word Conversion** – Full document flow using pypandoc_binary, enhanced with `python-docx` for customizable page formatting (Size, Orientation, Margins).
- 📑 **PDF Conversion** – Generates beautiful, styled PDFs instantly using WeasyPrint, preserving your selected page formatting and gracefully breaking complex tables across pages.
- 📊 **Powerhouse Excel Engine** – 
  - **Merged Cell Support**: Full rowspan and colspan mapping.
  - **Rich Formatting**: Preserves bold, italic, and text alignment.
  - **Smart Architecture**: Automatically handles 100+ tables by splitting them into organized Sheets/Tabs without relying on `pandas`.
- 👁️ **Interactive Preview Navigation** – Dedicated preview dialog allowing you to seamlessly flip through multiple files (◀ / ▶) in Raw, HTML Rendered, or Table Structure view.
- 🔗 **Intelligent Fallback** – If no formal tables are detected, it uses `pytablewriter` to automatically extract lists and key-value pairs.
- 🌓 **Adaptive UI** – Support for System-aware Dark and Light modes (Auto), alongside dozens of beautiful `qt-material` themes.
- 🧵 **Asynchronous Processing** – Entire batch runs on worker threads to keep the UI perfectly smooth.

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
pip install -r requirements.txt
```

*(Note: For the PDF feature on Windows, WeasyPrint requires the GTK3 runtime. If you encounter missing DLL errors, please install the [GTK3 Runtime for Windows](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases) and ensure it is added to your PATH.)*

## Usage

1. Run the application:
```bash
python main.py
```

2. Click "Select Files" to grab one or more Markdown/Mermaid files.
3. Your selected files will neatly populate the **Selected Files** list.
4. Choose conversion type:
   - **Word (.docx)** - Converts entire document with page formatting
   - **Excel (.xlsx)** - Extracts tables with formatting
   - **PDF (.pdf)** - Converts document into a styled PDF
5. Customize page format: Select your preferred Paper Size, Orientation, and Margins.
6. Toggle syntax highlighting if needed.
7. Click "Convert" – the app will automatically batch-process every file in your list!

### Interactive Preview
- Highlight any file in your list and click "👁️ Preview Selected"
- A dedicated Preview Window opens showing the Raw, HTML, and extracted Tables.
- Use the **◀ Previous File** and **Next File ▶** buttons at the bottom of the dialog to instantly flip through previews of all your selected files without closing the window.

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
qt-material        - Beautiful modern UI themes
pypandoc_binary    - Markdown to Word conversion
python-docx        - Word document formatting (Margins, Size, Orientation)
weasyprint         - Markdown to PDF conversion engine (handles print CSS natively)
openpyxl           - Excel file writing with high-fidelity formatting
markdown           - Markdown to HTML conversion
beautifulsoup4     - HTML parsing for table extraction
pytablewriter      - Excel fallback extraction
```

## Project Structure

```
md_converter/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── assets/                 # Static assets
│   ├── icon.png            # Application icon
│   └── theme/              # Theme stylesheets
│       ├── dark.qss        # Dark theme
│       └── light.qss       # Light theme
├── core/                   # Core UI components
│   ├── main_window.py      # Main window logic (radio buttons)
│   ├── menu.py             # Menu bar creation
│   ├── preview_dialog.py   # Preview dialog
│   ├── preview_thread.py   # Preview worker thread
│   └── readme_viewer.py    # README viewer dialog
├── logic/                  # Business logic
│   └── converter_thread.py # Conversion worker with Combo Engine
└── ui/                     # UI design files
    ├── ui_mainwindow.ui    # Main window UI (radio buttons)
    └── preview_dialog.ui   # Preview dialog UI
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
