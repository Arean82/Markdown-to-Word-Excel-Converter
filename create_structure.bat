@echo off
echo Creating folder structure...

REM Create main folders
mkdir md_converter 2>nul
cd md_converter

mkdir ui 2>nul
mkdir theme 2>nul
mkdir core 2>nul
mkdir core\md 2>nul
mkdir core\mermaid 2>nul
mkdir logs 2>nul

REM Create empty files

REM Root files
echo. > main.py
echo. > requirements.txt
echo. > LICENSE
echo. > README.md

REM UI files
echo. > ui\main_window.ui
echo. > ui\preview_dialog.ui
echo. > ui\license_viewer.ui
echo. > ui\log_viewer.ui
echo. > ui\readme_viewer.ui

REM Theme files
echo. > theme\dark.qss
echo. > theme\light.qss

REM Core root files
echo. > core\__init__.py
echo. > core\main_window.py
echo. > core\logger.py
echo. > core\log_viewer.py
echo. > core\license_viewer.py
echo. > core\readme_viewer.py

REM Core/md files
echo. > core\md\__init__.py
echo. > core\md\handler.py
echo. > core\md\converter.py
echo. > core\md\preview_dialog.py
echo. > core\md\preview_thread.py

REM Core/mermaid files
echo. > core\mermaid\__init__.py
echo. > core\mermaid\handler.py
echo. > core\mermaid\renderer.py
echo. > core\mermaid\extractor.py
echo. > core\mermaid\dialog.py

echo.
echo Folder structure created successfully!
echo.
echo Verifying structure...
echo.

REM Show tree structure
tree /f

echo.
echo Done! Press any key to exit...
pause >nul