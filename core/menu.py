from PyQt6.QtWidgets import QMenuBar, QMenu
from PyQt6.QtGui import QAction

def setup_menu(main_window):
    """Create and setup menu bar programmatically"""
    # Create menu bar
    menubar = QMenuBar(main_window)
    main_window.setMenuBar(menubar)
    
    # File menu
    file_menu = QMenu("File", main_window)
    menubar.addMenu(file_menu)
    
    # Create actions
    main_window.actionLicense = QAction("License", main_window)
    main_window.actionReadme = QAction("Readme", main_window)
    main_window.actionExit = QAction("Exit", main_window)
    
    # Add actions to file menu
    file_menu.addAction(main_window.actionLicense)
    file_menu.addAction(main_window.actionReadme)
    file_menu.addSeparator()
    file_menu.addAction(main_window.actionExit)
    
    # Theme menu
    theme_menu = QMenu("Theme", main_window)
    menubar.addMenu(theme_menu)
    
    main_window.actionDark = QAction("Dark", main_window)
    main_window.actionDark.setCheckable(True)
    main_window.actionDark.setChecked(True)
    
    main_window.actionLight = QAction("Light", main_window)
    main_window.actionLight.setCheckable(True)
    
    theme_menu.addAction(main_window.actionDark)
    theme_menu.addAction(main_window.actionLight)
    
    # Logs menu
    logs_menu = QMenu("Logs", main_window)
    menubar.addMenu(logs_menu)
    
    main_window.actionViewLogs = QAction("View Logs", main_window)
    main_window.actionClearLogs = QAction("Clear Logs", main_window)
    
    logs_menu.addAction(main_window.actionViewLogs)
    logs_menu.addAction(main_window.actionClearLogs)
    
    # Connect menu actions
    main_window.actionExit.triggered.connect(main_window.close)
    main_window.actionDark.triggered.connect(lambda: main_window.change_theme('dark'))
    main_window.actionLight.triggered.connect(lambda: main_window.change_theme('light'))
    main_window.actionViewLogs.triggered.connect(main_window.view_logs)
    main_window.actionClearLogs.triggered.connect(main_window.clear_logs)
    main_window.actionLicense.triggered.connect(main_window.show_license)
    main_window.actionReadme.triggered.connect(main_window.show_readme)