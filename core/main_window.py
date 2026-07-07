# ==================================================================
# File: core/main_window.py
# Description: Main application window for Markdown Converter Application   
# ==================================================================


import sys
import os
from pathlib import Path

from PyQt6.QtWidgets import (QMainWindow, QFileDialog, QMessageBox, 
                             QPushButton, QProgressBar, QLabel, QMenu)
from PyQt6.QtGui import QAction, QShortcut, QKeySequence
from PyQt6.uic import loadUi
from PyQt6.QtCore import Qt, QSettings

from core.logger import Logger
from core.preview_dialog import PreviewDialog
from core.license_viewer import LicenseViewerDialog
from core.log_viewer import LogViewerDialog
from core.readme_viewer import ReadmeViewerDialog

# Logic imports
from logic.md_handler import MarkdownHandler
from logic.mermaid_handler import MermaidHandler
from logic.md_converter import ConversionWorker


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Load UI
        ui_path = Path(__file__).parent.parent / 'ui' / 'main_window.ui'
        loadUi(str(ui_path), self)
        
        # Set UI Size
        self.resize(560, 600)
        self.setMinimumSize(660, 600)
        self.setAcceptDrops(True)
        
        # Initialize logger
        self.logger = Logger()
        
        # Initialize variables
        self.current_files = []
        self.current_file = None
        self.current_file_type = None
        self.worker = None
        
        # Setup QSettings for config.ini
        ini_path = Path(__file__).parent.parent / 'config.ini'
        self.settings = QSettings(str(ini_path), QSettings.Format.IniFormat)
        self.last_path = self.settings.value("last_path", str(Path.home()))
        self.current_theme = self.settings.value("theme", "auto")
        
        # Load saved margin settings
        if hasattr(self, 'doubleSpinBox'):
            self.doubleSpinBox.setValue(float(self.settings.value("margin_top", 2.54)))
        if hasattr(self, 'doubleSpinBox_4'):
            self.doubleSpinBox_4.setValue(float(self.settings.value("margin_bottom", 2.54)))
        if hasattr(self, 'doubleSpinBox_3'):
            self.doubleSpinBox_3.setValue(float(self.settings.value("margin_left", 2.54)))
        if hasattr(self, 'doubleSpinBox_2'):
            self.doubleSpinBox_2.setValue(float(self.settings.value("margin_right", 2.54)))
        if hasattr(self, 'checkBox'):
            self.checkBox.setChecked(str(self.settings.value("margin_is_inch", "false")).lower() == "true")
            
        saved_margin_preset = self.settings.value("margin_preset", "Normal")
        if hasattr(self, 'marginCombo'):
            index = self.marginCombo.findText(saved_margin_preset)
            if index >= 0:
                self.marginCombo.setCurrentIndex(index)
                
        # Load paper size, orientation, format radio, and highlight
        saved_paper_size = self.settings.value("paper_size", "A4")
        if hasattr(self, 'paperSizeCombo'):
            index = self.paperSizeCombo.findText(saved_paper_size)
            if index >= 0: self.paperSizeCombo.setCurrentIndex(index)
            
        saved_orientation = self.settings.value("orientation", "Portrait")
        if hasattr(self, 'orientationCombo'):
            index = self.orientationCombo.findText(saved_orientation)
            if index >= 0: self.orientationCombo.setCurrentIndex(index)
            
        if hasattr(self, 'highlightCheck'):
            self.highlightCheck.setChecked(str(self.settings.value("highlight", "true")).lower() == "true")
            
        if hasattr(self, 'nativeEngineCheck'):
            self.nativeEngineCheck.setChecked(str(self.settings.value("native_engine", "false")).lower() == "true")
            
        saved_format = self.settings.value("format", "Word")
        if saved_format == "Word" and hasattr(self, 'wordRadio'):
            self.wordRadio.setChecked(True)
        elif saved_format == "Excel" and hasattr(self, 'excelRadio'):
            self.excelRadio.setChecked(True)
        elif saved_format == "PDF" and hasattr(self, 'pdfMarkdownRadio'):
            self.pdfMarkdownRadio.setChecked(True)
            
        if hasattr(self, 'excelSheetModeCombo'):
            saved_excel_mode = self.settings.value("excel_sheet_mode", "📊 One table per sheet")
            index = self.excelSheetModeCombo.findText(saved_excel_mode)
            if index >= 0:
                self.excelSheetModeCombo.setCurrentIndex(index)
        
        # Set dynamic property for qt-material to style it as a large primary action button
        self.convertBtn.setProperty("class", "primary")
        
        # Initialize handlers
        self.md_handler = MarkdownHandler()
        self.mermaid_handler = MermaidHandler()
        
        # Create menu actions
        self.actionExit = QAction("Exit", self)
        self.actionExit.triggered.connect(self.close)
        
        self.actionDark = QAction("Dark", self)
        self.actionDark.setCheckable(True)
        self.actionDark.setChecked(False)
        self.actionDark.triggered.connect(lambda: self.apply_theme('dark'))
        
        self.actionAuto = QAction("Auto (Adaptive)", self)
        self.actionAuto.setCheckable(True)
        self.actionAuto.setChecked(False)
        self.actionAuto.triggered.connect(lambda: self.apply_theme('auto'))
        
        self.actionLight = QAction("Light", self)
        self.actionLight.setCheckable(True)
        self.actionLight.setChecked(True)
        self.actionLight.triggered.connect(lambda: self.apply_theme('light'))
        
        self.material_actions = []
        
        self.actionViewLogs = QAction("View Logs", self)
        self.actionViewLogs.triggered.connect(self.show_logs)
        
        self.actionClearLogs = QAction("Clear Logs", self)
        self.actionClearLogs.triggered.connect(self.clear_logs)
        
        self.actionLicense = QAction("License", self)
        self.actionLicense.triggered.connect(self.show_license)
        
        self.actionReadme = QAction("Readme", self)
        self.actionReadme.triggered.connect(self.show_readme)
        
        # Initially show markdown section in stacked widget
        if hasattr(self, 'stackedWidget'):
            self.stackedWidget.setCurrentIndex(0)
        else:
            self.mermaidGroup.setVisible(False)

        # Setup menu
        self.setup_menu()
        
        # Apply theme
        self.apply_theme(self.current_theme)
        
        # Connect UI signals
        self.selectFileBtn.clicked.connect(self.select_file)
        self.previewBtn.clicked.connect(self.show_preview_dialog)
        self.convertBtn.clicked.connect(self.convert_file)
        self.exportDiagramBtn.clicked.connect(self.export_diagram)
        if hasattr(self, 'openOutputFolderBtn'):
            self.openOutputFolderBtn.clicked.connect(self.open_output_folder)
            self.openOutputFolderBtn.setEnabled(False)
            
        if hasattr(self, 'checkBox_2'):
            self.checkBox_2.toggled.connect(self.toggle_conversion_direction)
            
        if hasattr(self, 'reverseConvertBtn'):
            self.reverseConvertBtn.clicked.connect(self.convert_office_to_md)
        self.wordRadio.toggled.connect(self.toggle_word_settings)
        if hasattr(self, 'excelRadio'):
            self.excelRadio.toggled.connect(self.toggle_word_settings)
        if hasattr(self, 'pdfMarkdownRadio'):
            self.pdfMarkdownRadio.toggled.connect(self.toggle_word_settings)
            
        if hasattr(self, 'marginCombo'):
            self.marginCombo.currentTextChanged.connect(self.on_margin_changed)
            self.on_margin_changed(self.marginCombo.currentText())
        
        # Initial state for Word settings
        self.toggle_word_settings()
        
        self.fileListWidget.itemSelectionChanged.connect(self.handle_list_selection)
        
        if hasattr(self, 'actionAIFeatures'):
            self.actionAIFeatures.triggered.connect(self.show_ai_settings)
            
        self.logger.info("Application started")
        
    def on_margin_changed(self, text: str):
        if text == "Normal":
            if hasattr(self, 'doubleSpinBox'): self.doubleSpinBox.setValue(2.54)
            if hasattr(self, 'doubleSpinBox_4'): self.doubleSpinBox_4.setValue(2.54)
            if hasattr(self, 'doubleSpinBox_3'): self.doubleSpinBox_3.setValue(2.54)
            if hasattr(self, 'doubleSpinBox_2'): self.doubleSpinBox_2.setValue(2.54)
            if hasattr(self, 'checkBox'): self.checkBox.setChecked(False)
        elif text == "Narrow":
            if hasattr(self, 'doubleSpinBox'): self.doubleSpinBox.setValue(1.27)
            if hasattr(self, 'doubleSpinBox_4'): self.doubleSpinBox_4.setValue(1.27)
            if hasattr(self, 'doubleSpinBox_3'): self.doubleSpinBox_3.setValue(1.27)
            if hasattr(self, 'doubleSpinBox_2'): self.doubleSpinBox_2.setValue(1.27)
            if hasattr(self, 'checkBox'): self.checkBox.setChecked(False)
        elif text == "Wide":
            if hasattr(self, 'doubleSpinBox'): self.doubleSpinBox.setValue(2.54)
            if hasattr(self, 'doubleSpinBox_4'): self.doubleSpinBox_4.setValue(2.54)
            if hasattr(self, 'doubleSpinBox_3'): self.doubleSpinBox_3.setValue(5.08)
            if hasattr(self, 'doubleSpinBox_2'): self.doubleSpinBox_2.setValue(5.08)
            if hasattr(self, 'checkBox'): self.checkBox.setChecked(False)
            
        # Optional: enable/disable them depending on Custom
        custom_enabled = (text == "Custom")
        if hasattr(self, 'doubleSpinBox'): self.doubleSpinBox.setEnabled(custom_enabled)
        if hasattr(self, 'doubleSpinBox_4'): self.doubleSpinBox_4.setEnabled(custom_enabled)
        if hasattr(self, 'doubleSpinBox_3'): self.doubleSpinBox_3.setEnabled(custom_enabled)
        if hasattr(self, 'doubleSpinBox_2'): self.doubleSpinBox_2.setEnabled(custom_enabled)
        if hasattr(self, 'checkBox'): self.checkBox.setEnabled(custom_enabled)

    def _finish_init(self):
        self.delete_shortcut = QShortcut(QKeySequence("Delete"), self.fileListWidget)
        self.delete_shortcut.activated.connect(self.remove_selected_files)
        self.backspace_shortcut = QShortcut(QKeySequence("Backspace"), self.fileListWidget)
        self.backspace_shortcut.activated.connect(self.remove_selected_files)
        
        self.fileListWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.fileListWidget.customContextMenuRequested.connect(self.show_list_context_menu)
        
        if hasattr(self, 'btnDeleteSelected'):
            self.btnDeleteSelected.clicked.connect(self.remove_selected_files)
    
    def setup_menu(self):
        """Create menu bar programmatically"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction(self.actionExit)
        
        # Theme menu
        theme_menu = menubar.addMenu("Theme")
        theme_menu.addAction(self.actionAuto)
        theme_menu.addAction(self.actionDark)
        theme_menu.addAction(self.actionLight)
        
        # Material sub-menu
        material_menu = theme_menu.addMenu("Material Theme")
        try:
            import qt_material
            for theme_name in qt_material.list_themes():
                action = QAction(theme_name, self)
                action.setCheckable(True)
                action.setChecked(False)
                # Capture theme_name in lambda
                action.triggered.connect(lambda checked, t=theme_name: self.apply_theme(f'material:{t}'))
                material_menu.addAction(action)
                self.material_actions.append(action)
        except ImportError:
            material_menu.setEnabled(False)
            material_menu.setToolTip("Please run 'pip install qt-material' to enable Material themes")
        
        # Logs menu
        logs_menu = menubar.addMenu("Logs")
        logs_menu.addAction(self.actionViewLogs)
        logs_menu.addAction(self.actionClearLogs)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        help_menu.addAction(self.actionLicense)
        help_menu.addAction(self.actionReadme)
    
    def apply_theme(self, theme: str):
        """Apply theme stylesheet"""
        self.current_theme = theme
        # Uncheck all
        if hasattr(self, 'actionAuto'):
            self.actionAuto.setChecked(False)
        self.actionDark.setChecked(False)
        self.actionLight.setChecked(False)
        for action in self.material_actions:
            action.setChecked(False)
        
        if theme.startswith('material:'):
            material_theme_name = theme.split(':')[1]
            # Check the specific action
            for action in self.material_actions:
                if action.text() == material_theme_name:
                    action.setChecked(True)
                    break
                    
            try:
                from qt_material import apply_stylesheet
                import os
                # Apply the selected material theme
                apply_stylesheet(self, theme=material_theme_name)
                self.logger.info(f"Theme changed to Material: {material_theme_name}")
            except ImportError:
                self.logger.warning("qt-material is not installed")
                self.apply_theme('dark') # fallback
            return
            
        # Reset qt-material styling if switching away from material
        self.setStyleSheet("")
        
        if theme == 'auto':
            if hasattr(self, 'actionAuto'):
                self.actionAuto.setChecked(True)
            import PyQt6.QtWidgets as QtWidgets
            app = QtWidgets.QApplication.instance()
            if app:
                # Use window color lightness to guess system theme
                is_dark = app.palette().window().color().lightness() < 128
            else:
                is_dark = False
            theme_path = Path(__file__).parent.parent / 'assets' / 'theme' / ('dark.qss' if is_dark else 'light.qss')
            theme_name = 'dark' if is_dark else 'light'
        elif theme == 'dark':
            theme_path = Path(__file__).parent.parent / 'assets' / 'theme' / 'dark.qss'
            self.actionDark.setChecked(True)
            theme_name = 'dark'
        else:
            theme_path = Path(__file__).parent.parent / 'assets' / 'theme' / 'light.qss'
            self.actionLight.setChecked(True)
            theme_name = 'light'
        
        if theme_path.exists():
            with open(theme_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
            self.logger.info(f"Theme changed to {theme} (applied {theme_name})")
    
    def select_file(self):
        """Open file selection dialog"""
        
        is_reverse = hasattr(self, 'checkBox_2') and self.checkBox_2.isChecked()
        
        if is_reverse:
            filter_str = "Supported Files (*.pdf *.pptx *.docx *.xlsx *.html *.csv *.json *.xml *.jpg *.jpeg *.png *.mp3 *.wav);;All Files (*)"
        else:
            filter_str = "Supported Files (*.md *.markdown *.mermaid *.mmd);;Markdown Files (*.md *.markdown);;Mermaid Files (*.mermaid *.mmd);;All Files (*)"
            
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            self.last_path,
            filter_str
        )
        
        if not file_paths:
            return
            
        # Validate that the user didn't select a mix of Markdown and Mermaid files
        has_md = False
        has_mermaid = False
        for fp in file_paths:
            ext = Path(fp).suffix.lower()
            if ext in {'.md', '.markdown'}:
                has_md = True
            elif ext in {'.mermaid', '.mmd'}:
                has_mermaid = True
                
        if has_md and has_mermaid:
            QMessageBox.warning(self, "Invalid Selection", "You cannot mix Markdown and Mermaid files in the same batch. Please select only one file type.")
            return
            
        self.last_path = str(Path(file_paths[0]).parent)
        self.current_files = file_paths
        self.fileListWidget.clear()
        for fp in self.current_files:
            self.fileListWidget.addItem(os.path.basename(fp))
            
        # Select the first file by default
        self.fileListWidget.setCurrentRow(0)
        self.convertBtn.setEnabled(True)
        if hasattr(self, 'openOutputFolderBtn'):
            self.openOutputFolderBtn.setEnabled(True)
        
        self.logger.info(f"Selected {len(self.current_files)} files.")
        self.show_correct_section()
        
    def remove_selected_files(self):
        selected_items = self.fileListWidget.selectedItems()
        if not selected_items: return
        
        rows = [self.fileListWidget.row(item) for item in selected_items]
        rows.sort(reverse=True)
        
        for row in rows:
            if row < len(self.input_files):
                self.input_files.pop(row)
            self.fileListWidget.takeItem(row)
            
        if self.fileListWidget.count() > 0:
            if not self.fileListWidget.selectedItems():
                self.fileListWidget.setCurrentRow(0)
        else:
            self.previewWidget.setHtml("")
            self.fileTypeLabel.setText("File type: Not selected")

    def show_list_context_menu(self, pos):
        menu = QMenu(self)
        remove_action = menu.addAction("Remove Selected")
        clear_action = menu.addAction("Clear All")
        
        action = menu.exec(self.fileListWidget.mapToGlobal(pos))
        if action == remove_action:
            self.remove_selected_files()
        elif action == clear_action:
            self.input_files.clear()
            self.fileListWidget.clear()
            self.previewWidget.setHtml("")
            self.fileTypeLabel.setText("File type: Not selected")

    def handle_list_selection(self):
        """Handle selection change in the list widget"""
        selected_items = self.fileListWidget.selectedItems()
        if not selected_items:
            self.previewBtn.setEnabled(False)
            self.current_file = None
            return
            
        self.previewBtn.setEnabled(True)
        index = self.fileListWidget.currentRow()
        self.current_file = self.current_files[index]
        
        if self.current_file.endswith(('.md', '.markdown')):
            self.current_file_type = 'markdown'
            self.fileTypeLabel.setText(f"📄 File type: Markdown")
        elif self.current_file.endswith('.mermaid'):
            self.current_file_type = 'mermaid'
            self.fileTypeLabel.setText(f"🎨 File type: Mermaid Diagram")
        elif self.current_file.endswith('.docx'):
            self.current_file_type = 'word'
            self.fileTypeLabel.setText(f"📄 File type: Word Document")
        elif self.current_file.endswith('.xlsx'):
            self.current_file_type = 'excel'
            self.fileTypeLabel.setText(f"📊 File type: Excel Document")
        else:
            self.fileTypeLabel.setText(f"📄 File type: Unknown")
    
    def show_preview_dialog(self):
        """Show full preview dialog"""
        if not self.current_files:
            QMessageBox.warning(self, "Warning", "Please select files first!")
            return
            
        is_reverse = hasattr(self, 'checkBox_2') and self.checkBox_2.isChecked()
        if is_reverse:
            QMessageBox.information(self, "Preview", "Previewing Office files is not currently supported.")
            return
            
        index = self.fileListWidget.currentRow()
        if index < 0:
            index = 0
        
        use_highlighting = self.highlightCheck.isChecked()
        dialog = PreviewDialog(self.current_files, index, use_highlighting, self)
        dialog.exec()

    def convert_file(self):
        """Convert all selected markdown files"""
        if not self.current_files:
            QMessageBox.warning(self, "Warning", "Please select files first!")
            return
            
        # Build queue of markdown files
        self.conversion_queue = [f for f in self.current_files if f.endswith(('.md', '.markdown'))]
        if not self.conversion_queue:
            QMessageBox.warning(self, "Warning", "No markdown files selected for conversion.\nMermaid files are for diagram viewing only.")
            return

        self.set_ui_enabled(False)
        self.progressBar.setVisible(True)
        self.progressBar.setValue(0)
        
        self.conversion_successes = 0
        self.conversion_failures = 0
        self.start_next_conversion()

    def start_next_conversion(self):
        if not self.conversion_queue:
            # Batch finished
            self.set_ui_enabled(True)
            self.progressBar.setValue(100)
            self.statusLabel.setText("Batch conversion complete")
            QMessageBox.information(self, "Batch Complete", f"Successfully converted {self.conversion_successes} file(s). Failed: {self.conversion_failures}")
            return
            
        file_to_convert = self.conversion_queue.pop(0)
        
        if self.wordRadio.isChecked():
            output_ext = ".docx"
            conv_type = "Word"
        elif hasattr(self, 'pdfMarkdownRadio') and self.pdfMarkdownRadio.isChecked():
            output_ext = ".pdf"
            conv_type = "PDF"
        else:
            output_ext = ".xlsx"
            conv_type = "Excel"
            
        input_path = Path(file_to_convert)
        output_file = str(input_path.with_suffix(output_ext))
        use_highlighting = self.highlightCheck.isChecked()
        use_native_engine = self.nativeEngineCheck.isChecked() if hasattr(self, 'nativeEngineCheck') else False
        paper_size = self.paperSizeCombo.currentText() if hasattr(self, 'paperSizeCombo') else "A4"
        orientation = self.orientationCombo.currentText() if hasattr(self, 'orientationCombo') else "Portrait"
        margin = self.marginCombo.currentText() if hasattr(self, 'marginCombo') else "Normal"
        
        custom_margins = {
            "top": self.doubleSpinBox.value() if hasattr(self, 'doubleSpinBox') else 2.54,
            "bottom": self.doubleSpinBox_4.value() if hasattr(self, 'doubleSpinBox_4') else 2.54,
            "left": self.doubleSpinBox_3.value() if hasattr(self, 'doubleSpinBox_3') else 2.54,
            "right": self.doubleSpinBox_2.value() if hasattr(self, 'doubleSpinBox_2') else 2.54,
            "is_inch": self.checkBox.isChecked() if hasattr(self, 'checkBox') else False
        }
        
        self.statusLabel.setText(f"Converting: {os.path.basename(file_to_convert)}...")
        
        excel_sheet_mode = self.excelSheetModeCombo.currentText() if hasattr(self, 'excelSheetModeCombo') else "📊 One table per sheet"
        
        self.worker = ConversionWorker(
            file_to_convert,
            output_file,
            conv_type,
            use_highlighting,
            paper_size,
            orientation,
            margin,
            custom_margins,
            excel_sheet_mode=excel_sheet_mode,
            use_native_engine=use_native_engine
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.on_batch_conversion_finished)
        self.worker.start()

    def on_batch_conversion_finished(self, success: bool, message: str):
        if success:
            self.conversion_successes += 1
            self.logger.info(f"Batch item successful: {message}")
            self.recentLabel.setText(f"✅ Last: {os.path.basename(message.split(':')[-1].strip())}")
        else:
            self.conversion_failures += 1
            self.logger.error(f"Batch item failed: {message}")
            
        is_reverse = hasattr(self, 'checkBox_2') and self.checkBox_2.isChecked()
        if is_reverse:
            self.start_next_reverse_conversion()
        else:
            self.start_next_conversion()
            
    def toggle_conversion_direction(self, checked: bool):
        """Toggle UI state for MD to Office vs Office to MD"""
        if checked:
            self.checkBox_2.setText("Convert to MD File")
            if hasattr(self, 'stackedWidget'):
                self.stackedWidget.setCurrentIndex(2) # Page 3
        else:
            self.checkBox_2.setText("Convert to PDF/Office")
            if hasattr(self, 'stackedWidget'):
                if self.current_file_type == 'mermaid':
                    self.stackedWidget.setCurrentIndex(1)
                else:
                    self.stackedWidget.setCurrentIndex(0)
                    
        # Clear currently selected files since types no longer match the intent
        self.current_files = []
        self.current_file = None
        self.current_file_type = None
        self.fileListWidget.clear()
        self.fileTypeLabel.setText("📄 File type: Not selected")
        self.set_ui_enabled(False)
        self.selectFileBtn.setEnabled(True)

    def convert_office_to_md(self):
        """Convert selected files to Markdown"""
        if not self.current_files:
            QMessageBox.warning(self, "Warning", "Please select files first!")
            return
            
        self.conversion_queue = [f for f in self.current_files if not f.endswith(('.md', '.markdown', '.mermaid', '.mmd'))]
        if not self.conversion_queue:
            QMessageBox.warning(self, "Warning", "No valid files selected for conversion.")
            return

        self.set_ui_enabled(False)
        self.progressBar.setVisible(True)
        self.progressBar.setValue(0)
        
        self.conversion_successes = 0
        self.conversion_failures = 0
        self.start_next_reverse_conversion()

    def start_next_reverse_conversion(self):
        if not hasattr(self, 'conversion_queue') or not self.conversion_queue:
            self.set_ui_enabled(True)
            self.progressBar.setValue(100)
            self.statusLabel.setText("Batch conversion complete")
            QMessageBox.information(self, "Batch Complete", f"Successfully converted {self.conversion_successes} file(s). Failed: {self.conversion_failures}")
            return
            
        file_to_convert = self.conversion_queue.pop(0)
        
        input_path = Path(file_to_convert)
        output_file = str(input_path.with_suffix('.md'))
        
        self.statusLabel.setText(f"Converting: {os.path.basename(file_to_convert)}...")
        
        from logic.markitdown_converter import MarkItDownConverterThread
        openai_key = self.settings.value("openai_api_key", "")
        use_native_engine = self.nativeEngineCheck.isChecked() if hasattr(self, 'nativeEngineCheck') else False
        
        self.worker = MarkItDownConverterThread(
            file_to_convert,
            output_file,
            openai_key,
            use_native_engine
        )
        
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.on_batch_conversion_finished)
        self.worker.start()
    
    def set_ui_enabled(self, enabled: bool):
        """Enable/disable UI elements"""
        self.selectFileBtn.setEnabled(enabled)
        self.previewBtn.setEnabled(enabled and self.current_file is not None)
        self.wordRadio.setEnabled(enabled)
        self.excelRadio.setEnabled(enabled)
        if hasattr(self, 'pdfMarkdownRadio'):
            self.pdfMarkdownRadio.setEnabled(enabled)
        
        format_selected = self.wordRadio.isChecked() or (hasattr(self, 'pdfMarkdownRadio') and self.pdfMarkdownRadio.isChecked())
        word_settings_enabled = enabled and format_selected
        self.highlightCheck.setEnabled(word_settings_enabled)
        
        if hasattr(self, 'excelSheetModeCombo'):
            self.excelSheetModeCombo.setEnabled(enabled and hasattr(self, 'excelRadio') and self.excelRadio.isChecked())
        
        if hasattr(self, 'paperSizeCombo'):
            self.paperSizeCombo.setEnabled(word_settings_enabled)
            self.orientationCombo.setEnabled(word_settings_enabled)
            self.marginCombo.setEnabled(word_settings_enabled)
            self.paperLabel.setEnabled(word_settings_enabled)
            self.orientationLabel.setEnabled(word_settings_enabled)
            self.marginLabel.setEnabled(word_settings_enabled)
            if hasattr(self, 'nativeEngineCheck'):
                self.nativeEngineCheck.setEnabled(word_settings_enabled)
            
        self.convertBtn.setEnabled(enabled and self.current_file is not None)
        if hasattr(self, 'reverseConvertBtn'):
            self.reverseConvertBtn.setEnabled(enabled and self.current_file is not None)
        if hasattr(self, 'exportDiagramBtn'):
            self.exportDiagramBtn.setEnabled(enabled and self.current_file_type == 'mermaid')
        if hasattr(self, 'openOutputFolderBtn'):
            self.openOutputFolderBtn.setEnabled(enabled and self.current_file is not None)
            
    def toggle_word_settings(self, checked: bool = False):
        """Toggle Word/PDF specific settings vs Excel specific settings"""
        format_selected = self.wordRadio.isChecked() or (hasattr(self, 'pdfMarkdownRadio') and self.pdfMarkdownRadio.isChecked())
        self.highlightCheck.setEnabled(format_selected)
        self.highlightCheck.setVisible(format_selected)
        if hasattr(self, 'nativeEngineCheck'):
            self.nativeEngineCheck.setEnabled(format_selected)
            self.nativeEngineCheck.setVisible(format_selected)
        
        if hasattr(self, 'excelSheetModeCombo'):
            excel_selected = hasattr(self, 'excelRadio') and self.excelRadio.isChecked()
            self.excelSheetModeCombo.setEnabled(excel_selected)
            self.excelSheetModeCombo.setVisible(excel_selected)
            
        if hasattr(self, 'paperSizeCombo'):
            self.paperSizeCombo.setEnabled(format_selected)
            self.orientationCombo.setEnabled(format_selected)
            self.marginCombo.setEnabled(format_selected)
            self.paperLabel.setEnabled(format_selected)
            self.orientationLabel.setEnabled(format_selected)
            self.marginLabel.setEnabled(format_selected)
    
    def update_progress(self, value: int):
        """Update progress bar"""
        self.progressBar.setValue(value)
    
    def update_status(self, message: str):
        """Update status label"""
        self.statusLabel.setText(message)
    
    def show_license(self):
        """Show license dialog"""
        dialog = LicenseViewerDialog(self)
        dialog.exec()
    
    def show_readme(self):
        """Show README dialog"""
        dialog = ReadmeViewerDialog(self)
        dialog.exec()
    
    def show_logs(self):
        """Show log viewer dialog"""
        dialog = LogViewerDialog(self)
        dialog.exec()
    
    def clear_logs(self):
        """Clear logs with confirmation"""
        reply = QMessageBox.question(
            self,
            "Clear Logs",
            "Are you sure you want to clear all logs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.logger.clear_logs():
                QMessageBox.information(self, "Success", "Logs cleared")
                self.logger.info("Logs cleared by user")
            else:
                QMessageBox.warning(self, "Error", "Failed to clear logs")

    def show_ai_settings(self):
        """Show AI Settings dialog"""
        from PyQt6.QtWidgets import QInputDialog
        current_key = self.settings.value("openai_api_key", "")
        text, ok = QInputDialog.getText(self, "AI Features Settings", "Enter OpenAI API Key (for OCR/Vision):", text=current_key)
        if ok:
            self.settings.setValue("openai_api_key", text)
            self.logger.info("OpenAI API Key updated")

    def show_correct_section(self):
        """Show appropriate section based on file type"""
        if self.current_file_type == 'markdown':
            if hasattr(self, 'stackedWidget'):
                self.stackedWidget.setCurrentIndex(0)
            else:
                self.mdGroup.setVisible(True)
                self.mermaidGroup.setVisible(False)
            self.convertBtn.setEnabled(True)
        elif self.current_file_type == 'mermaid':
            if hasattr(self, 'stackedWidget'):
                self.stackedWidget.setCurrentIndex(1)
            else:
                self.mdGroup.setVisible(False)
                self.mermaidGroup.setVisible(True)
            self.convertBtn.setEnabled(False)
            if hasattr(self, 'exportDiagramBtn'):
                self.exportDiagramBtn.setEnabled(True)

    def get_export_format(self):
        """Get selected export format from radio buttons"""
        if self.pngRadio.isChecked():
            return "PNG"
        elif self.svgRadio.isChecked():
            return "SVG"
        else:
            return "PDF"
        
    def export_diagram(self):
        """Export mermaid diagram to selected format"""
        if not self.current_file or self.current_file_type != 'mermaid':
            QMessageBox.warning(self, "Warning", "Please select a mermaid file first!")
            return

        export_format = self.get_export_format()

        # Get save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Diagram",
            f"diagram.{export_format.lower()}",
            f"{export_format} Files (*.{export_format.lower()});;All Files (*)"
        )

        if not file_path:
            return

        try:
            # Load mermaid content
            with open(self.current_file, 'r', encoding='utf-8') as f:
                code = f.read()

            # Render using mermaid renderer
            from logic.mermaid_renderer import MermaidRenderer, MermaidFormat, MermaidBackend

            # Map format
            format_map = {
                "PNG": MermaidFormat.PNG,
                "SVG": MermaidFormat.SVG,
                "PDF": MermaidFormat.PDF
            }

            renderer = MermaidRenderer(backend=MermaidBackend.MERMAID_PY)
            renderer.render(
                code,
                format_map[export_format],
                output_path=file_path,
                width=1024,
                theme='light'
            )

            QMessageBox.information(self, "Success", f"Diagram exported to:\n{file_path}")
            self.logger.info(f"Diagram exported: {file_path}")

        except Exception as e:
            self.logger.error(f"Export failed: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to export diagram:\n{str(e)}")

    def open_output_folder(self):
        """Open the folder containing the currently selected file(s)"""
        import platform
        import subprocess
        
        folder_path = self.last_path
        if not folder_path or not os.path.exists(folder_path):
            return
            
        try:
            if platform.system() == "Windows":
                os.startfile(folder_path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", folder_path])
            else:
                subprocess.Popen(["xdg-open", folder_path])
            self.logger.info(f"Opened output folder: {folder_path}")
        except Exception as e:
            self.logger.error(f"Failed to open folder: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to open folder:\n{str(e)}")

    def closeEvent(self, event):
        """Clean up background threads before closing."""
        try:
            # Save settings
            self.settings.setValue("theme", self.current_theme)
            self.settings.setValue("last_path", self.last_path)
            
            # Save margin settings
            if hasattr(self, 'marginCombo'):
                self.settings.setValue("margin_preset", self.marginCombo.currentText())
            if hasattr(self, 'doubleSpinBox'):
                self.settings.setValue("margin_top", self.doubleSpinBox.value())
            if hasattr(self, 'doubleSpinBox_4'):
                self.settings.setValue("margin_bottom", self.doubleSpinBox_4.value())
            if hasattr(self, 'doubleSpinBox_3'):
                self.settings.setValue("margin_left", self.doubleSpinBox_3.value())
            if hasattr(self, 'doubleSpinBox_2'):
                self.settings.setValue("margin_right", self.doubleSpinBox_2.value())
            if hasattr(self, 'checkBox'):
                self.settings.setValue("margin_is_inch", self.checkBox.isChecked())
                
            # Save other format settings
            if hasattr(self, 'paperSizeCombo'):
                self.settings.setValue("paper_size", self.paperSizeCombo.currentText())
            if hasattr(self, 'orientationCombo'):
                self.settings.setValue("orientation", self.orientationCombo.currentText())
            if hasattr(self, 'highlightCheck'):
                self.settings.setValue("highlight", self.highlightCheck.isChecked())
            if hasattr(self, 'nativeEngineCheck'):
                self.settings.setValue("native_engine", self.nativeEngineCheck.isChecked())
                
            if hasattr(self, 'excelSheetModeCombo'):
                self.settings.setValue("excel_sheet_mode", self.excelSheetModeCombo.currentText())
                
            if hasattr(self, 'wordRadio') and self.wordRadio.isChecked():
                self.settings.setValue("format", "Word")
            elif hasattr(self, 'excelRadio') and self.excelRadio.isChecked():
                self.settings.setValue("format", "Excel")
            elif hasattr(self, 'pdfMarkdownRadio') and self.pdfMarkdownRadio.isChecked():
                self.settings.setValue("format", "PDF")
            
            if self.worker and self.worker.isRunning():
                self.worker.quit()
                self.worker.wait(1000)
            
            # Close preview dialog if open to kill any threads inside it
            if hasattr(self, 'preview_dialog') and self.preview_dialog is not None:
                self.preview_dialog.close()
                
        except Exception as e:
            self.logger.error(f"Error during shutdown: {str(e)}")
            
        event.accept()

    def dragEnterEvent(self, event):
        """Accept file drag events"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        """Handle dropped files with auto-routing"""
        urls = event.mimeData().urls()
        if not urls:
            return
            
        file_paths = []
        for url in urls:
            if url.isLocalFile():
                path = url.toLocalFile()
                if os.path.isfile(path):
                    file_paths.append(path)
                    
        if not file_paths:
            return
            
        # Detect extensions
        has_forward = False
        has_reverse = False
        
        forward_exts = {'.md', '.markdown', '.mermaid', '.mmd'}
        
        for fp in file_paths:
            ext = Path(fp).suffix.lower()
            if ext in forward_exts:
                has_forward = True
            else:
                has_reverse = True
                
        if has_forward and has_reverse:
            QMessageBox.warning(self, "Invalid Selection", "You cannot mix Markdown/Mermaid files with Office/Data files in the same batch. Please select only one type of conversion.")
            return
            
        # Auto-route UI mode
        if has_reverse:
            if hasattr(self, 'checkBox_2'):
                self.checkBox_2.setChecked(True)
        else:
            if hasattr(self, 'checkBox_2'):
                self.checkBox_2.setChecked(False)
                
        # Handle mermaid vs markdown mix logic exactly like select_file
        if not has_reverse:
            has_md = False
            has_mermaid = False
            for fp in file_paths:
                ext = Path(fp).suffix.lower()
                if ext in {'.md', '.markdown'}:
                    has_md = True
                elif ext in {'.mermaid', '.mmd'}:
                    has_mermaid = True
                    
            if has_md and has_mermaid:
                QMessageBox.warning(self, "Invalid Selection", "You cannot mix Markdown and Mermaid files in the same batch. Please select only one file type.")
                return
                
        # Populate UI
        self.last_path = str(Path(file_paths[0]).parent)
        self.current_files = file_paths
        self.fileListWidget.clear()
        for fp in self.current_files:
            self.fileListWidget.addItem(os.path.basename(fp))
            
        self.fileListWidget.setCurrentRow(0)
        self.convertBtn.setEnabled(True)
        if hasattr(self, 'openOutputFolderBtn'):
            self.openOutputFolderBtn.setEnabled(True)
        
        self.logger.info(f"Dropped {len(self.current_files)} files.")
        self.show_correct_section()
