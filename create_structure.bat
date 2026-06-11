@echo off
echo Creating folder structure for Markdown Converter...
echo.

REM Create main folder
mkdir md_converter 2>nul
cd md_converter

REM Create folders
mkdir ui 2>nul
mkdir theme 2>nul
mkdir core 2>nul
mkdir logic 2>nul
mkdir logs 2>nul

REM Create all files
echo. > main.py
echo. > requirements.txt

REM UI files
echo. > ui\main_window.ui
echo. > ui\preview_dialog.ui
echo. > ui\license_viewer.ui
echo. > ui\log_viewer.ui
echo. > ui\readme_viewer.ui

REM Theme files
echo. > theme\dark.qss
echo. > theme\light.qss

REM Core files
echo. > core\__init__.py
echo. > core\main_window.py
echo. > core\preview_dialog.py
echo. > core\logger.py
echo. > core\log_viewer.py
echo. > core\license_viewer.py
echo. > core\readme_viewer.py

REM Logic files
echo. > logic\__init__.py
echo. > logic\md_handler.py
echo. > logic\md_converter.py
echo. > logic\md_preview_thread.py
echo. > logic\mermaid_handler.py
echo. > logic\mermaid_renderer.py
echo. > logic\mermaid_extractor.py
echo. > logic\mermaid_preview_thread.py

echo.
echo ========================================
echo Folder structure created successfully!
echo ========================================
echo.
echo Directory tree:
echo.
tree /f

echo.
echo Done!
pause