# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Photo Enhancer Pro."""

import sys
from pathlib import Path

block_cipher = None
root = Path(SPECPATH)

a = Analysis(
    ['main.py'],
    pathex=[str(root)],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('ui/styles/dark.qss', 'ui/styles'),
    ],
    hiddenimports=[
        'PIL',
        'cv2',
        'piexif',
        'pillow_heif',
        'imagehash',
        'PySide6',
        'processing.stages.color',
        'processing.stages.tone',
        'processing.stages.detail',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'gradio', 'tkinter', 'torch', 'tensorflow', 'matplotlib',
        'sklearn', 'scipy', 'pandas', 'nltk', 'tensorboard',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Photo Enhancer Pro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
