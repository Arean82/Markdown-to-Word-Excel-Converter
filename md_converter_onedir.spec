# -*- mode: python ; coding: utf-8 -*-
import pypandoc
import os

pandoc_path = pypandoc.get_pandoc_path()
if os.name == 'nt' and not pandoc_path.endswith('.exe'):
    pandoc_path += '.exe'

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
    ],
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
    name='MD Converter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    upx=True,
    upx_exclude=[],
    name='onedir',
)
