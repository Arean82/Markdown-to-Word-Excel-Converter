# -*- mode: python ; coding: utf-8 -*-
# Updated: Ensured assets bundle supports the updated README viewer SVGs
import pypandoc
import os
from PyInstaller.utils.hooks import collect_data_files

pandoc_path = pypandoc.get_pandoc_path()
if os.name == 'nt' and not pandoc_path.endswith('.exe'):
    pandoc_path += '.exe'

jaraco_data = collect_data_files('jaraco.text')

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (pandoc_path, 'pypandoc/files'),
        ('assets', 'assets'),
        ('ui', 'ui'),
        ('readme.md', '.'),
        ('LICENSE', '.'),
        ('config.ini', '.')
    ] + jaraco_data,
    hiddenimports=[
        'pypandoc',
        'docx',
        'weasyprint',
        'markdown',
        'bs4',
        'openpyxl',
        'pytablewriter',
        'qt_material',
        'jaraco.text'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide6', 'PyQt5', 'torch', 'scipy', 'matplotlib', 'pandas', 'numpy', 'tensorboard'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Synora Document Studio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='onedir',
)
