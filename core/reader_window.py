# ==================================================================
# File: core/reader_window.py
# Description: Advanced Multi-Tab Markdown Reader window incorporating
#              TOC sidebar, Live Editor, KaTeX math rendering, image lightbox,
#              Claude Code plans discovery, Zen Mode, Vim keyboard layouts,
#              scroll memory progress, and copy as rich text.
# ==================================================================

import os
import re
from pathlib import Path

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QSplitter, QTreeWidget, QTreeWidgetItem, QLabel, 
                             QPlainTextEdit, QTabWidget, QMessageBox, QComboBox, 
                             QInputDialog, QMenu, QApplication, QFileDialog)
from PyQt6.QtGui import QAction, QKeySequence, QShortcut
from PyQt6.QtCore import Qt, QUrl, QSettings, pyqtSignal, QTimer, QMimeData, QFileSystemWatcher
from PyQt6.QtWebEngineWidgets import QWebEngineView

import markdown
from markdown.extensions.codehilite import CodeHiliteExtension


class MarkdownTab(QWidget):
    """Represents a single document tab with its own TOC, Editor, and Web View"""
    
    def __init__(self, file_path: str, is_dark_theme: bool, parent_window):
        super().__init__()
        self.file_path = file_path
        self.is_dark_theme = is_dark_theme
        self.parent_window = parent_window
        
        # Setup layouts
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.layout.addWidget(self.splitter)
        
        # 1. Sidebar Widget (TOC + Pinned Claude Plans)
        self.sidebarWidget = QWidget()
        self.sidebarWidget.setMaximumWidth(350)
        self.sidebarLayout = QVBoxLayout(self.sidebarWidget)
        self.sidebarLayout.setContentsMargins(8, 8, 8, 8)
        self.sidebarLayout.setSpacing(8)
        
        self.sidebarTabWidget = QTabWidget()
        
        # TOC Subtab
        self.tocContainer = QWidget()
        self.tocLayout = QVBoxLayout(self.tocContainer)
        self.tocLayout.setContentsMargins(0, 0, 0, 0)
        self.tocLayout.setSpacing(5)
        self.tocLabel = QLabel("Table of Contents")
        self.tocLabel.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.tocTree = QTreeWidget()
        self.tocTree.setHeaderHidden(True)
        self.tocLayout.addWidget(self.tocLabel)
        self.tocLayout.addWidget(self.tocTree)
        self.sidebarTabWidget.addTab(self.tocContainer, "📋 TOC")
        
        # Claude Code Plans Subtab
        self.plansContainer = QWidget()
        self.plansLayout = QVBoxLayout(self.plansContainer)
        self.plansLayout.setContentsMargins(0, 0, 0, 0)
        self.plansLayout.setSpacing(5)
        self.plansLabel = QLabel("Claude Code Plans")
        self.plansLabel.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.plansTree = QTreeWidget()
        self.plansTree.setHeaderHidden(True)
        self.plansLayout.addWidget(self.plansLabel)
        self.plansLayout.addWidget(self.plansTree)
        self.sidebarTabWidget.addTab(self.plansContainer, "🤖 Claude Plans")
        
        self.sidebarLayout.addWidget(self.sidebarTabWidget)
        self.splitter.addWidget(self.sidebarWidget)
        
        # 2. Live Editor Widget
        self.editorWidget = QWidget()
        self.editorLayout = QVBoxLayout(self.editorWidget)
        self.editorLayout.setContentsMargins(5, 5, 5, 5)
        self.editorLayout.setSpacing(5)
        self.editorLabel = QLabel("Monospace PlainText Editor")
        self.editorLabel.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.editorTextEdit = QPlainTextEdit()
        self.editorTextEdit.setFont(parent_window.editor_font)
        self.editorLayout.addWidget(self.editorLabel)
        self.editorLayout.addWidget(self.editorTextEdit)
        self.editorWidget.setVisible(False)
        self.splitter.addWidget(self.editorWidget)
        
        # 3. Web Preview Container
        self.webContainer = QWidget()
        self.webLayout = QVBoxLayout(self.webContainer)
        self.webLayout.setContentsMargins(0, 0, 0, 0)
        self.webLayout.setSpacing(0)
        
        self.web_view = QWebEngineView()
        web_settings = self.web_view.settings()
        web_settings.setAttribute(web_settings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        web_settings.setAttribute(web_settings.WebAttribute.LocalContentCanAccessFileUrls, True)
        self.webLayout.addWidget(self.web_view)
        self.splitter.addWidget(self.webContainer)
        
        # Ratios (TOC: 20%, Edit: 0%, Web: 80% default)
        self.splitter.setSizes([200, 0, 800])
        
        # File Watcher
        self.file_watcher = QFileSystemWatcher([self.file_path], self)
        self.file_watcher.fileChanged.connect(self.on_file_changed_externally)
        
        # State variables
        self.math_placeholders = []
        self.mermaid_placeholders = []
        self.active_heading_index = 0
        self.g_pressed = False
        self.headings_ids_list = []
        
        # Connections
        self.tocTree.itemClicked.connect(self.on_toc_item_clicked)
        self.plansTree.itemClicked.connect(self.on_plan_item_clicked)
        self.editorTextEdit.textChanged.connect(self.on_editor_text_changed)
        
        # Debounce timer for editing preview
        self.render_timer = QTimer(self)
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self.refresh_preview_from_editor)
        
        # Load content and Claude Plans
        self.load_document()
        self.load_claude_plans()
        
        # Restore scroll position
        self.web_view.loadFinished.connect(self.restore_scroll_position)

    def load_document(self):
        try:
            if hasattr(self, 'file_watcher'):
                self.file_watcher.removePath(self.file_path)
                
            with open(self.file_path, 'r', encoding='utf-8') as f:
                raw_markdown = f.read()
                
            self.editorTextEdit.blockSignals(True)
            self.editorTextEdit.setPlainText(raw_markdown)
            self.editorTextEdit.blockSignals(False)
            
            self.render_markdown(raw_markdown)
            
            if hasattr(self, 'file_watcher'):
                self.file_watcher.addPath(self.file_path)
        except Exception as e:
            self.parent_window.statusBar().showMessage(f"Error loading file: {e}", 3000)

    def on_file_changed_externally(self, path):
        if self.editorWidget.isVisible() and self.editorTextEdit.document().isModified():
            return
        self.load_document()

    def on_editor_text_changed(self):
        self.render_timer.start(300)
        # Mark tab as dirty
        tab_idx = self.parent_window.tabWidget.indexOf(self)
        if tab_idx != -1:
            title = os.path.basename(self.file_path)
            self.parent_window.tabWidget.setTabText(tab_idx, f"• {title}")

    def refresh_preview_from_editor(self):
        md_text = self.editorTextEdit.toPlainText()
        try:
            if hasattr(self, 'file_watcher'):
                self.file_watcher.removePath(self.file_path)
                
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(md_text)
                
            if hasattr(self, 'file_watcher'):
                self.file_watcher.addPath(self.file_path)
        except Exception as e:
            self.parent_window.statusBar().showMessage(f"Warning: Failed to save changes back: {e}", 3000)
            
        self.render_markdown(md_text)
        
        # Reset tab dirty title
        tab_idx = self.parent_window.tabWidget.indexOf(self)
        if tab_idx != -1:
            title = os.path.basename(self.file_path)
            self.parent_window.tabWidget.setTabText(tab_idx, title)

    def render_markdown(self, raw_markdown):
        # Extract headings for keyboard jumping
        self.headings_ids_list.clear()
        lines = raw_markdown.split('\n')
        in_code_block = False
        heading_count = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('```'):
                in_code_block = not in_code_block
            if not in_code_block and re.match(r'^(#{1,6})\s+(.+)$', stripped):
                self.headings_ids_list.append(f"heading_{heading_count}")
                heading_count += 1
                
        # Build Table of Contents
        self.build_toc(raw_markdown)
        
        # Stats
        words = len(re.findall(r'\w+', raw_markdown))
        reading_time = max(1, round(words / 200))
        self.parent_window.statusBar().showMessage(f"Words: {words} | Reading Time: {reading_time} min")
        
        # Protect Mermaid blocks
        self.mermaid_placeholders.clear()
        def replace_mermaid(match):
            placeholder = f"<!-- MERMAID_PLACEHOLDER_{len(self.mermaid_placeholders)} -->"
            self.mermaid_placeholders.append(match.group(1))
            return placeholder
        processed_md = re.sub(r'```mermaid\r?\n(.*?)\r?\n```', replace_mermaid, raw_markdown, flags=re.DOTALL)
        
        # Checklists
        processed_md = re.sub(r'-\s+\[\s*\]\s+(.*?)$', r'- <input type="checkbox" disabled /> \1', processed_md, flags=re.MULTILINE)
        processed_md = re.sub(r'-\s+\[\s*x\s*\]\s+(.*?)$', r'- <input type="checkbox" checked disabled /> \1', processed_md, flags=re.MULTILINE)
        
        # Escape dollars in code
        def escape_dollars_in_code(match):
            return match.group(0).replace('$', '<!-- TEMP_DOLLAR_ESC -->')
        processed_md = re.sub(r'(```.*?```|`.*?`)', escape_dollars_in_code, processed_md, flags=re.DOTALL)
        
        # Extract KaTeX display/inline math
        self.math_placeholders.clear()
        def replace_math(match):
            placeholder = f"<!-- MATH_PLACEHOLDER_{len(self.math_placeholders)} -->"
            self.math_placeholders.append(match.group(0))
            return placeholder
        processed_md = re.sub(r'\$\$(.*?)\$\$', replace_math, processed_md, flags=re.DOTALL)
        processed_md = re.sub(r'(?<!\\)\$((?:[^$\\]|\\.)+)\$', replace_math, processed_md)
        processed_md = processed_md.replace('<!-- TEMP_DOLLAR_ESC -->', '$')
        
        # HTML tags markup config
        processed_md = re.sub(r'<div([^>]*)(?<!markdown="1")>', r'<div\1 markdown="1">', processed_md)
        
        # Compiler
        extensions = [
            'tables',
            'footnotes',
            'fenced_code',
            'md_in_html',
            'meta',
            'nl2br',
            'sane_lists',
            CodeHiliteExtension(
                css_class='highlight',
                use_pygments=True,
                pygments_style='monokai'
            )
        ]
        md_compiler = markdown.Markdown(extensions=extensions)
        html_body = md_compiler.convert(processed_md)
        
        # Cover page Formatting
        meta = getattr(md_compiler, 'Meta', {})
        if meta:
            title = meta.get('title', [""])[0]
            author = meta.get('author', [""])[0]
            date = meta.get('date', [""])[0]
            if title or author or date:
                cover_html = f"""
                <div class="document-cover" style="text-align: center; border-bottom: 2px solid var(--border-color); padding-bottom: 2em; margin-bottom: 3em; margin-top: 1em;">
                    {f'<h1 class="cover-title" style="font-size: 2.5em; font-weight: 800; margin-bottom: 0.2em; color: var(--text-color);">{title}</h1>' if title else ''}
                    {f'<p class="cover-author" style="font-size: 1.2em; color: #86868b; margin: 0.5em 0;">By {author}</p>' if author else ''}
                    {f'<p class="cover-date" style="font-size: 1.0em; color: #86868b; margin: 0.2em 0;">{date}</p>' if date else ''}
                </div>
                """
                html_body = cover_html + html_body
                
        # Restore Mermaid
        for i, code_val in enumerate(self.mermaid_placeholders):
            html_body = html_body.replace(
                f"<!-- MERMAID_PLACEHOLDER_{i} -->",
                f'<div class="mermaid">{self.unescape_html(code_val)}</div>'
            )
            
        # Restore math
        for i, math_val in enumerate(self.math_placeholders):
            html_body = html_body.replace(f"<!-- MATH_PLACEHOLDER_{i} -->", math_val)
            
        # Load local template HTML
        template_path = Path(__file__).parent.parent / 'assets' / 'reader_template.html'
        if not template_path.exists():
            return
            
        with open(template_path, 'r', encoding='utf-8') as f:
            template_html = f.read()
            
        final_html = template_html.replace('<!-- MARKDOWN_HTML_CONTENT -->', html_body)
        
        theme_str = 'dark' if self.is_dark_theme else 'light'
        family_css = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" if self.parent_window.font_family == "System Default" else f"'{self.parent_window.font_family}'"
        
        custom_onload = (
            f"window.onload = function() {{ "
            f"  setTheme('{theme_str}'); "
            f"  setFontFamily(\"{family_css}\"); "
            f"  setFontSize(\"{self.parent_window.font_size}\"); "
            f"  setupHeadingsAndRender(); "
            f"}};"
        )
        final_html = final_html.replace('window.onload = setupHeadingsAndRender;', custom_onload)
        
        # Render
        self.web_view.setHtml(final_html, QUrl.fromLocalFile(str(template_path)))

    def restore_scroll_position(self):
        # Read scroll from registry settings
        scroll_y = self.parent_window.settings.value(f"scroll_{self.file_path}", 0)
        if scroll_y:
            self.web_view.page().runJavaScript(f"window.scrollTo(0, {scroll_y});")

    def save_scroll_position(self):
        # Fetch scroll progress
        self.web_view.page().runJavaScript("window.scrollY", lambda val: self.parent_window.settings.setValue(f"scroll_{self.file_path}", val or 0))

    def unescape_html(self, text: str) -> str:
        return (text.replace('&amp;', '&')
                .replace('&lt;', '<')
                .replace('&gt;', '>')
                .replace('&quot;', '"')
                .replace('&#39;', "'"))

    def build_toc(self, markdown_text: str):
        self.tocTree.clear()
        lines = markdown_text.split('\n')
        headings = []
        in_code_block = False
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('```'):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
                
            match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                clean_title = re.sub(r'\*\*|__|\*|_|`|\[.*?\]\(.*?\)', '', title)
                headings.append((level, clean_title))
                
        level_map = {0: self.tocTree.invisibleRootItem()}
        for idx, (level, title) in enumerate(headings):
            item = QTreeWidgetItem([title])
            item.setData(0, Qt.ItemDataRole.UserRole, f"heading_{idx}")
            parent_level = level - 1
            while parent_level not in level_map and parent_level > 0:
                parent_level -= 1
            parent_item = level_map[parent_level]
            parent_item.addChild(item)
            level_map[level] = item
            if level <= 2:
                item.setExpanded(True)

    def on_toc_item_clicked(self, item: QTreeWidgetItem, column: int):
        heading_id = item.data(0, Qt.ItemDataRole.UserRole)
        if heading_id:
            js_code = f"scrollToHeading('{heading_id}');"
            self.web_view.page().runJavaScript(js_code)

    def load_claude_plans(self):
        self.plansTree.clear()
        plans_dir = Path.home() / ".claude" / "plans"
        if not plans_dir.exists():
            item = QTreeWidgetItem(["No Claude plans folder found"])
            self.plansTree.addTopLevelItem(item)
            return
            
        plan_files = list(plans_dir.glob("*.md")) + list(plans_dir.glob("*.markdown"))
        if not plan_files:
            item = QTreeWidgetItem(["No active plans found"])
            self.plansTree.addTopLevelItem(item)
            return
            
        for plan in plan_files:
            item = QTreeWidgetItem([plan.name])
            item.setData(0, Qt.ItemDataRole.UserRole, str(plan))
            item.setToolTip(str(plan))
            self.plansTree.addTopLevelItem(item)

    def on_plan_item_clicked(self, item: QTreeWidgetItem, column: int):
        plan_path = item.data(0, Qt.ItemDataRole.UserRole)
        if plan_path and os.path.exists(plan_path):
            self.parent_window.open_file_in_tab(plan_path)

    def jump_heading(self, direction: int):
        if not self.headings_ids_list:
            return
        self.active_heading_index = max(0, min(len(self.headings_ids_list) - 1, self.active_heading_index + direction))
        heading_id = self.headings_ids_list[self.active_heading_index]
        self.web_view.page().runJavaScript(f"scrollToHeading('{heading_id}');")


class MarkdownReaderWindow(QMainWindow):
    """Main Reader Window supporting Multi-tabs, Zen mode, and Vim keys"""
    
    bookmark_toggled = pyqtSignal()
    
    def __init__(self, file_path: str, is_dark_theme: bool = False, parent=None):
        super().__init__(parent)
        self.is_dark_theme = is_dark_theme
        
        # Load registry settings
        self.settings = QSettings("MarkdownStudio", "ReaderSettings")
        self.font_family = self.settings.value("font_family", "System Default")
        self.font_size = self.settings.value("font_size", "16px")
        self.editor_font_family = self.settings.value("editor_font_family", "Consolas")
        
        from PyQt6.QtGui import QFont
        self.editor_font = QFont(self.editor_font_family, 11)
        self.editor_font.setStyleHint(QFont.StyleHint.Monospace)
        
        # Multi-tab Widget as central widget
        self.tabWidget = QTabWidget()
        self.tabWidget.setTabsClosable(True)
        self.tabWidget.setMovable(True)
        self.tabWidget.tabCloseRequested.connect(self.close_tab)
        self.tabWidget.currentChanged.connect(self.on_tab_changed)
        self.setCentralWidget(self.tabWidget)
        
        self.setWindowTitle("Markdown Reader Studio")
        self.resize(1150, 750)
        
        # Setup Status bar
        self.statusBar()
        
        # Setup toolbar
        self.setup_toolbar()
        
        # Add the initially requested file
        if file_path and os.path.exists(file_path):
            self.open_file_in_tab(file_path)
            
        # Shortcuts for Zen Mode, Rich Text, and Tab navigation
        self.setup_reader_shortcuts()

    def setup_reader_shortcuts(self):
        # Zen Mode Shortcut (Ctrl+Shift+F)
        self.zen_shortcut = QShortcut(QKeySequence("Ctrl+Shift+F"), self)
        self.zen_shortcut.activated.connect(self.toggle_zen_mode)
        self.is_zen_active = False
        
        # Copy Rich Text Shortcut (Ctrl+Shift+C)
        self.copy_rich_shortcut = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
        self.copy_rich_shortcut.activated.connect(self.copy_active_tab_rich_text)

    def setup_toolbar(self):
        self.toolBar = self.addToolBar("Reader Options")
        self.toolBar.setMovable(False)
        
        # Tab actions
        self.open_tab_action = QAction("➕ New Tab", self)
        self.open_tab_action.setShortcut(QKeySequence("Ctrl+T"))
        self.open_tab_action.triggered.connect(self.browse_and_open_tab)
        self.toolBar.addAction(self.open_tab_action)
        
        self.toolBar.addSeparator()
        
        # Sidebar toggle action
        self.toggle_sidebar_action = QAction("📋 Toggle TOC", self)
        self.toggle_sidebar_action.setShortcut(QKeySequence("Ctrl+B"))
        self.toggle_sidebar_action.triggered.connect(self.toggle_active_sidebar)
        self.toolBar.addAction(self.toggle_sidebar_action)
        
        # Edit mode action
        self.toggle_edit_action = QAction("✍️ Toggle Editor", self)
        self.toggle_edit_action.setShortcut(QKeySequence("Ctrl+E"))
        self.toggle_edit_action.setCheckable(True)
        self.toggle_edit_action.triggered.connect(self.toggle_active_edit_mode)
        self.toolBar.addAction(self.toggle_edit_action)
        
        # Bookmark action
        self.bookmark_action = QAction("☆ Bookmark", self)
        self.bookmark_action.triggered.connect(self.toggle_active_bookmark)
        self.toolBar.addAction(self.bookmark_action)
        
        self.toolBar.addSeparator()
        
        # Find action
        self.find_action = QAction("🔍 Find", self)
        self.find_action.setShortcut(QKeySequence("Ctrl+F"))
        self.find_action.triggered.connect(self.show_active_find_dialog)
        self.toolBar.addAction(self.find_action)
        
        self.toolBar.addSeparator()
        
        # Zoom actions
        self.zoom_in_action = QAction("🔍➕", self)
        self.zoom_in_action.triggered.connect(lambda: self.adjust_active_zoom(0.1))
        self.toolBar.addAction(self.zoom_in_action)
        
        self.zoom_out_action = QAction("🔍➖", self)
        self.zoom_out_action.triggered.connect(lambda: self.adjust_active_zoom(-0.1))
        self.toolBar.addAction(self.zoom_out_action)
        
        self.toolBar.addSeparator()
        
        # Font Selectors
        font_widget = QWidget()
        font_layout = QHBoxLayout(font_widget)
        font_layout.setContentsMargins(5, 0, 5, 0)
        font_layout.setSpacing(5)
        
        font_lbl = QLabel("Font:")
        self.font_combo = QComboBox()
        self.font_combo.addItems(["System Default", "Arial", "Georgia", "Courier New", "Verdana", "Times New Roman"])
        self.font_combo.setCurrentText(self.font_family)
        self.font_combo.currentTextChanged.connect(self.on_font_family_changed)
        
        size_lbl = QLabel("Size:")
        self.size_combo = QComboBox()
        self.size_combo.addItems(["12px", "14px", "16px", "18px", "20px", "24px", "28px"])
        self.size_combo.setCurrentText(self.font_size)
        self.size_combo.currentTextChanged.connect(self.on_font_size_changed)
        
        font_layout.addWidget(font_lbl)
        font_layout.addWidget(self.font_combo)
        font_layout.addWidget(size_lbl)
        font_layout.addWidget(self.size_combo)
        
        self.toolBar.addWidget(font_widget)

    def open_file_in_tab(self, file_path: str):
        # Prevent opening duplicates
        for idx in range(self.tabWidget.count()):
            tab = self.tabWidget.widget(idx)
            if isinstance(tab, MarkdownTab) and tab.file_path == file_path:
                self.tabWidget.setCurrentIndex(idx)
                return
                
        # Create new tab
        tab = MarkdownTab(file_path, self.is_dark_theme, self)
        title = os.path.basename(file_path)
        idx = self.tabWidget.addTab(tab, title)
        self.tabWidget.setCurrentIndex(idx)
        
        # Set window title
        self.setWindowTitle(f"Markdown Reader - {title}")

    def browse_and_open_tab(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Markdown File",
            "",
            "Markdown Files (*.md *.markdown);;All Files (*)"
        )
        if file_path:
            self.open_file_in_tab(file_path)

    def close_tab(self, idx: int):
        tab = self.tabWidget.widget(idx)
        if isinstance(tab, MarkdownTab):
            # Save scroll memory
            tab.save_scroll_position()
            # Stop watcher
            tab.file_watcher.removePath(tab.file_path)
            
            # Confirm if dirty editor
            if tab.editorWidget.isVisible() and tab.editorTextEdit.document().isModified():
                reply = QMessageBox.question(
                    self, "Unsaved Changes",
                    f"File '{os.path.basename(tab.file_path)}' has unsaved edits. Close anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
                    
        self.tabWidget.removeWidget(tab)
        tab.deleteLater()
        
        if self.tabWidget.count() == 0:
            self.close()

    def get_active_tab(self) -> MarkdownTab:
        return self.tabWidget.currentWidget()

    def on_tab_changed(self, idx: int):
        tab = self.tabWidget.widget(idx)
        if isinstance(tab, MarkdownTab):
            self.setWindowTitle(f"Markdown Reader - {os.path.basename(tab.file_path)}")
            # Sync bookmark button
            self.update_bookmark_button_ui(tab.file_path)
            # Sync editor toggle button
            self.toggle_edit_action.setChecked(tab.editorWidget.isVisible())
            
    def toggle_active_sidebar(self):
        tab = self.get_active_tab()
        if tab:
            tab.sidebarWidget.setVisible(not tab.sidebarWidget.isVisible())

    def toggle_active_edit_mode(self, checked):
        tab = self.get_active_tab()
        if tab:
            tab.editorWidget.setVisible(checked)
            if checked:
                tab.splitter.setSizes([200, 400, 500])
            else:
                tab.splitter.setSizes([200, 0, 800])

    def toggle_active_bookmark(self):
        tab = self.get_active_tab()
        if tab:
            bookmarks = self.settings.value("bookmarks", [])
            if not isinstance(bookmarks, list):
                bookmarks = []
                
            if tab.file_path in bookmarks:
                bookmarks.remove(tab.file_path)
                self.statusBar().showMessage("Bookmark removed.", 2000)
            else:
                bookmarks.append(tab.file_path)
                self.statusBar().showMessage("Bookmark added.", 2000)
                
            self.settings.setValue("bookmarks", bookmarks)
            self.update_bookmark_button_ui(tab.file_path)
            self.bookmark_toggled.emit()

    def update_bookmark_button_ui(self, file_path: str):
        bookmarks = self.settings.value("bookmarks", [])
        if not isinstance(bookmarks, list):
            bookmarks = []
        if file_path in bookmarks:
            self.bookmark_action.setText("⭐ Bookmarked")
        else:
            self.bookmark_action.setText("☆ Bookmark")

    def show_active_find_dialog(self):
        tab = self.get_active_tab()
        if tab:
            text, ok = QInputDialog.getText(self, "Search", "Find text:")
            if ok and text:
                tab.web_view.findText(text)

    def adjust_active_zoom(self, delta: float):
        tab = self.get_active_tab()
        if tab:
            current_zoom = tab.web_view.zoomFactor()
            new_zoom = max(0.25, min(5.0, current_zoom + delta))
            tab.web_view.setZoomFactor(new_zoom)
            self.statusBar().showMessage(f"Zoom level: {int(new_zoom * 100)}%", 2000)

    def on_font_family_changed(self, font_name):
        self.font_family = font_name
        self.settings.setValue("font_family", font_name)
        # Apply fonts to all open tabs
        for idx in range(self.tabWidget.count()):
            tab = self.tabWidget.widget(idx)
            if isinstance(tab, MarkdownTab):
                tab.apply_fonts_in_webview()

    def on_font_size_changed(self, font_size):
        self.font_size = font_size
        self.settings.setValue("font_size", font_size)
        for idx in range(self.tabWidget.count()):
            tab = self.tabWidget.widget(idx)
            if isinstance(tab, MarkdownTab):
                tab.apply_fonts_in_webview()

    def copy_active_tab_rich_text(self):
        tab = self.get_active_tab()
        if not tab: return
        
        # Grab HTML from QWebEngineView dynamically
        tab.web_view.page().toHtml(self.on_html_retrieved_for_clipboard)

    def on_html_retrieved_for_clipboard(self, html_content: str):
        tab = self.get_active_tab()
        if not tab: return
        
        # Strip template tags but keep basic CSS formatting
        mime = QMimeData()
        mime.setHtml(html_content)
        mime.setText(tab.editorTextEdit.toPlainText())
        QApplication.clipboard().setMimeData(mime)
        self.statusBar().showMessage("Copied rendered document as Rich Text!", 3000)

    def toggle_zen_mode(self):
        self.is_zen_active = not self.is_zen_active
        
        # Toggle toolBar and status bar visibility
        self.toolBar.setVisible(not self.is_zen_active)
        self.statusBar().setVisible(not self.is_zen_active)
        
        # Toggle tab widget headers visibility
        self.tabWidget.tabBar().setVisible(not self.is_zen_active)
        
        # Hide sidebars on all open tabs
        for idx in range(self.tabWidget.count()):
            tab = self.tabWidget.widget(idx)
            if isinstance(tab, MarkdownTab):
                tab.sidebarWidget.setVisible(not self.is_zen_active)
                
        if self.is_zen_active:
            self.showFullScreen()
            self.statusBar().showMessage("Zen Mode Active (Press Ctrl+Shift+F to exit)", 4000)
        else:
            self.showNormal()

    def keyPressEvent(self, event):
        # Forward Vim keys to active tab if editor is not focused
        tab = self.get_active_tab()
        if not tab:
            super().keyPressEvent(event)
            return
            
        if tab.editorWidget.isVisible() and tab.editorTextEdit.hasFocus():
            super().keyPressEvent(event)
            return

        key = event.key()
        text = event.text()

        if key == Qt.Key.Key_J:
            tab.web_view.page().runJavaScript("window.scrollBy(0, 80);")
            tab.g_pressed = False
        elif key == Qt.Key.Key_K:
            tab.web_view.page().runJavaScript("window.scrollBy(0, -80);")
            tab.g_pressed = False
        elif text == 'G':
            tab.web_view.page().runJavaScript("window.scrollTo(0, document.body.scrollHeight);")
            tab.g_pressed = False
        elif text == 'g':
            if tab.g_pressed:
                tab.web_view.page().runJavaScript("window.scrollTo(0, 0);")
                tab.g_pressed = False
            else:
                tab.g_pressed = True
        elif text == '[':
            # Jump previous heading
            tab.jump_heading(-1)
            tab.g_pressed = False
        elif text == ']':
            # Jump next heading
            tab.jump_heading(1)
            tab.g_pressed = False
        else:
            tab.g_pressed = False
            super().keyPressEvent(event)

    def closeEvent(self, event):
        # Save scroll progress for all open tabs on exit
        for idx in range(self.tabWidget.count()):
            tab = self.tabWidget.widget(idx)
            if isinstance(tab, MarkdownTab):
                tab.save_scroll_position()
        event.accept()
